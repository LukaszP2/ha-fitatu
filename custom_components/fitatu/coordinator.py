"""Shared Fitatu API access and normalized monitoring data."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fitatu_api import (
    FitatuApiClient,
    FitatuApiError,
    FitatuAuthContext,
    FitatuAuthError,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CATEGORY_ACTIVITY,
    CATEGORY_ADVANCED,
    CATEGORY_BODY,
    CATEGORY_HYDRATION,
    CATEGORY_NUTRITION,
    CONF_SESSION,
    CONF_USER_ID,
    DEFAULT_MONITORING_CATEGORIES,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
_NUTRIENTS = {
    "energy": ("energy", "kcal", "calories", "energykcal"),
    "protein": ("protein", "proteins"),
    "fat": ("fat", "fats"),
    "carbohydrate": ("carbohydrate", "carbohydrates", "carbs"),
}


def _key(value: Any) -> str:
    """Normalize a response key for resilient matching."""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _number(value: Any) -> float | None:
    """Parse a numeric value without converting missing data to zero."""
    if isinstance(value, Mapping):
        for key in ("value", "amount", "current", "total", "kcal"):
            if key in value:
                return _number(value[key])
        return None
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _find_mapping_value(data: Any, aliases: set[str]) -> Any:
    """Find a named field in nested service data."""
    if isinstance(data, Mapping):
        for key, value in data.items():
            if _key(key) in aliases:
                return value
        for value in data.values():
            found = _find_mapping_value(value, aliases)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_mapping_value(value, aliases)
            if found is not None:
                return found
    return None


def _nutrient_record(summary: Any, nutrient: str) -> dict[str, float | None]:
    """Normalize one nutrient's Fitatu range summary."""
    aliases = set(_NUTRIENTS[nutrient])
    record = None
    if isinstance(summary, Mapping):
        for key, value in summary.items():
            if _key(key) in aliases:
                record = value
                break
    elif isinstance(summary, list):
        for item in summary:
            if (
                isinstance(item, Mapping)
                and _key(item.get("nutrient", item.get("name", item.get("key", ""))))
                in aliases
            ):
                record = item
                break
    if record is None:
        return {field: None for field in ("eaten", "current", "min", "max")}
    if isinstance(record, Mapping):
        return {
            field: _number(record.get(field, record.get(f"target_{field}")))
            for field in ("eaten", "current", "min", "max")
        }
    return {"eaten": _number(record), "current": None, "min": None, "max": None}


def _sum_named_values(data: Any, aliases: set[str]) -> float | None:
    """Sum matching values in an activity response without double-counting."""
    values: list[float] = []

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if _key(key) in aliases:
                    parsed = _number(value)
                    if parsed is not None:
                        values.append(parsed)
                else:
                    visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(data)
    return sum(values) if values else None


def _count_day_rows(day_data: Any, section: str) -> int | None:
    """Count meal items or activity entries without exposing their names."""
    if not isinstance(day_data, Mapping):
        return None
    plan = day_data.get(section)
    if not isinstance(plan, (Mapping, list)):
        return None
    if section == "activityPlan" and isinstance(plan, list):
        return len(plan)
    groups = plan.values() if isinstance(plan, Mapping) else plan
    count = 0
    found = False
    for group in groups:
        if isinstance(group, Mapping):
            rows = group.get("items", group.get("activities"))
            if isinstance(rows, list):
                count += len(rows)
                found = True
        elif isinstance(group, list):
            count += len(group)
            found = True
    return count if found else None


def _water_value(day_data: Any) -> float | None:
    """Read daily water intake in millilitres from the planner response."""
    raw = _find_mapping_value(
        day_data,
        {
            "waterconsumptionml",
            "waterconsumption",
            "waterintakeml",
            "waterintake",
            "water",
        },
    )
    if isinstance(raw, Mapping):
        raw = _find_mapping_value(
            raw,
            {
                "amount",
                "value",
                "consumed",
                "quantity",
                "waterconsumption",
                "waterconsumptionml",
            },
        )
    return _number(raw)


def _latest_weight(history: Any) -> tuple[float | None, str | None, str | None]:
    """Extract the newest weight record, including its source unit if present."""
    rows: Any = history
    if isinstance(history, Mapping):
        rows = history.get(
            "list",
            history.get(
                "items",
                history.get(
                    "measurements",
                    history.get(
                        "entries", history.get("history", history.get("results", []))
                    ),
                ),
            ),
        )
    if not isinstance(rows, list) or not rows:
        return None, None, None
    record = rows[0]
    if not isinstance(record, Mapping):
        return None, None, None
    value = _number(record.get("value", record.get("weight")))
    unit = record.get("unit", record.get("weightUnit", record.get("weight_unit")))
    recorded = record.get("date", record.get("day"))
    unit_text = str(unit).upper() if unit is not None else None
    return value, unit_text, str(recorded) if recorded is not None else None


class FitatuCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch the current diary and normalize supported monitoring values."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.api_lock = asyncio.Lock()
        self.auth = FitatuAuthContext.from_session_data(entry.data[CONF_SESSION])
        self.client = FitatuApiClient(
            self.auth,
            timeout_seconds=25,
            retry_max_attempts=2,
            persist_tokens=False,
        )

    def close(self) -> None:
        """Close the pooled HTTP connection."""
        self.client.close()

    def _account_date(self) -> date:
        """Return today's date in Fitatu's account timezone."""
        from homeassistant.util import dt as dt_util

        timezone_name = getattr(self.auth, "app_timezone", None)
        fallback_timezone = ZoneInfo(self.hass.config.time_zone)
        try:
            timezone = ZoneInfo(timezone_name) if timezone_name else fallback_timezone
        except (ZoneInfoNotFoundError, TypeError):
            timezone = fallback_timezone
        return dt_util.now(timezone).date()

    def _fetch(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Perform the synchronous API calls in a worker thread."""
        today = self._account_date()
        user_id = self.entry.data[CONF_USER_ID]
        categories = set(
            self.entry.options.get("categories", DEFAULT_MONITORING_CATEGORIES)
        )
        needs_nutrition = CATEGORY_NUTRITION in categories or "core" in categories
        needs_day = bool(
            categories & {CATEGORY_HYDRATION, CATEGORY_ACTIVITY, CATEGORY_ADVANCED}
        )
        needs_settings = bool(
            categories & {CATEGORY_HYDRATION, CATEGORY_BODY, CATEGORY_ADVANCED}
        )

        # Each category only makes the requests it needs. All calls remain
        # direct, read-only requests through the Fitatu client.
        nutrition = (
            self.client.summary.get_nutrition(user_id, today, today)
            if needs_nutrition
            else None
        )
        day_data = self.client.planner.get_day(user_id, today) if needs_day else None
        activity_data = (
            self.client.summary.get_activities(user_id, today, today)
            if CATEGORY_ACTIVITY in categories
            else None
        )

        settings = None
        if needs_settings:
            try:
                settings = self.client.user_settings.get_new(user_id, today)
            except FitatuAuthError:
                raise
            except FitatuApiError as err:
                _LOGGER.debug(
                    "Fitatu settings are not available: %s", type(err).__name__
                )

        weight_history = None
        if CATEGORY_BODY in categories:
            try:
                weight_history = self.client.measurements.get_weight_history(
                    user_id,
                    from_date=today - timedelta(days=366),
                    to_date=today,
                    page=1,
                    limit=1,
                )
            except FitatuAuthError:
                raise
            except FitatuApiError as err:
                _LOGGER.debug(
                    "Fitatu weight history is not available: %s", type(err).__name__
                )

        records = {name: _nutrient_record(nutrition, name) for name in _NUTRIENTS}
        weight, weight_unit, weight_date = _latest_weight(weight_history)
        values: dict[str, Any] = {
            "date": today.isoformat(),
            "weight": weight,
            "weight_unit": weight_unit,
            "weight_date": weight_date,
            "water": _water_value(day_data),
            "food_item_count": _count_day_rows(day_data, "dietPlan"),
            "activity_count": _count_day_rows(day_data, "activityPlan"),
            "activity_energy": _sum_named_values(
                activity_data,
                {
                    "burnedenergy",
                    "energyburned",
                    "caloriesburned",
                    "burnedcalories",
                    "totalenergy",
                },
            ),
        }
        for nutrient, fields in records.items():
            for field, value in fields.items():
                values[f"{nutrient}_{field}"] = value

        if settings is not None:
            values["water_target"] = _number(
                _find_mapping_value(
                    settings,
                    {
                        "watertarget",
                        "dailywatertarget",
                        "waterconsumptiontarget",
                        "watergoal",
                    },
                )
            )
            values["weight_unit"] = _find_mapping_value(
                settings, {"weightunit", "weight_unit"}
            )
            values["bmr"] = _number(
                _find_mapping_value(settings, {"bmr", "basalmetabolicrate"})
            )
            values["tmr"] = _number(
                _find_mapping_value(
                    settings, {"tmr", "totalmetabolicrate", "dailyenergyexpenditure"}
                )
            )
        else:
            values["water_target"] = None
            values["weight_unit"] = None
            values["bmr"] = None
            values["tmr"] = None

        session = self.auth.to_session_data(include_tokens=True)
        return values, session

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh all monitoring values and save renewed tokens."""
        try:
            async with self.api_lock:
                data, session = await self.hass.async_add_executor_job(self._fetch)
        except FitatuAuthError as err:
            raise ConfigEntryAuthFailed("Fitatu authentication expired") from err
        except FitatuApiError as err:
            raise UpdateFailed("Fitatu API request failed") from err
        except (OSError, TimeoutError) as err:
            raise UpdateFailed("Could not connect to Fitatu") from err
        except Exception as err:
            _LOGGER.debug("Unexpected Fitatu update error", exc_info=err)
            raise UpdateFailed("Unexpected Fitatu response") from err

        if session != self.entry.data.get(CONF_SESSION):
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={**self.entry.data, CONF_SESSION: session},
            )
        return data
