"""Write actions for Fitatu, exposed only to Home Assistant administrators."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service import (
    async_get_config_entry,
    async_register_admin_service,
)

from .const import CONF_USER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)
_DATE = vol.Optional("date")
_MEALS = vol.In(["breakfast", "second_breakfast", "lunch", "dinner", "snack", "supper"])


def _base_schema(fields: dict[Any, Any]) -> vol.Schema:
    return vol.Schema({vol.Required("config_entry_id"): str, **fields})


async def async_setup_actions(hass: HomeAssistant) -> None:
    """Register actions once for the integration; each call targets one entry."""

    async def run(
        call: ServiceCall, operation: Callable[..., Any], args: dict[str, Any]
    ) -> None:
        entry = async_get_config_entry(hass, DOMAIN, call.data["config_entry_id"])
        if entry is None or entry.runtime_data is None:
            raise HomeAssistantError("Fitatu entry is not loaded")
        coordinator = entry.runtime_data
        day = call.data.get("date") or coordinator.account_date()
        user_id = entry.data[CONF_USER_ID]
        try:
            async with coordinator.api_lock:
                result = await hass.async_add_executor_job(
                    lambda: operation(user_id, day, **args)
                )
            if isinstance(result, dict) and result.get("ok") is False:
                raise HomeAssistantError("Fitatu did not confirm the requested change")
            await coordinator.async_request_refresh()
        except HomeAssistantError:
            raise
        except Exception as err:
            _LOGGER.debug("Fitatu write action failed: %s", type(err).__name__)
            raise HomeAssistantError(
                "Fitatu could not apply the requested change"
            ) from err

    async def custom_item(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            entry_method(call, "custom"),
            {
                "meal_type": d["meal"],
                "name": d["name"],
                "calories": d["calories"],
                "protein_g": d.get("protein_g", 0),
                "fat_g": d.get("fat_g", 0),
                "carbs_g": d.get("carbs_g", 0),
                "eaten": d.get("eaten", False),
            },
        )

    async def product(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            entry_method(call, "product"),
            {
                "meal_type": d["meal"],
                "product_id": d["product_id"],
                "measure_id": d["measure_id"],
                "measure_quantity": d.get("quantity", 1),
                "eaten": d.get("eaten", False),
            },
        )

    async def product_unit(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            entry_method(call, "product_unit"),
            {
                "meal_type": d["meal"],
                "product_id": d["product_id"],
                "amount": d["amount"],
                "unit": d["unit"],
                "eaten": d.get("eaten", False),
            },
        )

    async def recipe(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            entry_method(call, "recipe"),
            {
                "meal_type": d["meal"],
                "recipe_id": d["recipe_id"],
                "measure_quantity": d.get("quantity", 1),
                "eaten": d.get("eaten", False),
            },
        )

    async def update_item(call: ServiceCall) -> None:
        d = call.data
        updates = {
            key: d[key]
            for key in ("quantity", "measure_id", "eaten", "name")
            if key in d
        }
        if not updates:
            raise HomeAssistantError("At least one food entry field must be provided")
        if "quantity" in updates:
            updates["measure_quantity"] = updates.pop("quantity")
        await run(
            call,
            entry_method(call, "update"),
            {
                "meal_type": d["meal"],
                "item_id": d["item_id"],
                **updates,
            },
        )

    async def remove_item(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            entry_method(call, "remove"),
            {"meal_type": d["meal"], "item_id": d["item_id"]},
        )

    async def set_water(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).water.set_day(
                uid, day, kw["water_consumption_ml"]
            ),
            {"water_consumption_ml": d["millilitres"]},
        )

    async def set_measurements(call: ServiceCall) -> None:
        d = call.data
        kwargs = {key: d[key] for key in ("weight", "fat_percentage") if key in d}
        if "weight" in kwargs:
            kwargs["weight_unit"] = d.get("weight_unit", "KG")
        kwargs.update(
            {
                key: d[key]
                for key in ("chest", "waist", "hips", "thigh", "arm")
                if key in d
            }
        )
        if not kwargs:
            raise HomeAssistantError("At least one measurement must be provided")
        kwargs["merge"] = True
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).measurements.set_day(
                uid, day, **kw
            ),
            kwargs,
        )

    async def delete_measurements(call: ServiceCall) -> None:
        await run(
            call,
            lambda uid, day: coordinator_client(call).measurements.delete_day(uid, day),
            {},
        )

    async def set_note(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).planner.set_note(
                uid, day, **kw
            ),
            {"note": d["note"]},
        )

    async def add_activity(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).planner.add_activity(
                uid, day, **kw
            ),
            {
                "activity_id": d["activity_id"],
                "minutes": d["minutes"],
                "energy": d["energy_kcal"],
            },
        )

    async def remove_activity(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).planner.remove_activity(
                uid, day, **kw
            ),
            {"item_id": d["activity_id"]},
        )

    async def move_item(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).planner.move_day_item(
                uid, day, from_meal_type=kw.pop("from_meal_type"), **kw
            ),
            {
                "from_meal_type": d["from_meal"],
                "item_id": d["item_id"],
                "to_day": d.get("to_date"),
                "to_meal_type": d.get("to_meal"),
            },
        )

    async def copy_meal(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(call).planner.copy_meal(
                uid, day, from_meal_type=kw.pop("from_meal_type"), **kw
            ),
            {
                "from_meal_type": d["from_meal"],
                "to_day": d["to_date"],
                "to_meal_type": d["to_meal"],
                "eaten": d.get("eaten"),
            },
        )

    async def replace_item(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(
                call
            ).planner.replace_day_item_with_custom_item(uid, day, **kw),
            {
                "meal_type": d["meal"],
                "item_id": d["item_id"],
                "name": d["name"],
                "calories": d["calories"],
                "protein_g": d.get("protein_g", 0),
                "fat_g": d.get("fat_g", 0),
                "carbs_g": d.get("carbs_g", 0),
            },
        )

    async def set_glass_size(call: ServiceCall) -> None:
        d = call.data
        await run(
            call,
            lambda uid, day, **kw: coordinator_client(
                call
            ).user_settings.update_water_settings(uid, **kw),
            {"unit_capacity": d["millilitres"]},
        )

    def coordinator_client(call: ServiceCall) -> Any:
        entry = async_get_config_entry(hass, DOMAIN, call.data["config_entry_id"])
        if entry is None or entry.runtime_data is None:
            raise HomeAssistantError("Fitatu entry is not loaded")
        return entry.runtime_data.client

    def entry_method(call: ServiceCall, kind: str) -> Callable[..., Any]:
        client = coordinator_client(call)
        return {
            "custom": client.planner.add_custom_item_to_day_meal,
            "product": client.planner.add_product_to_day_meal,
            "product_unit": client.planner.add_product_to_day_meal_with_unit,
            "recipe": client.planner.add_recipe_to_day_meal,
            "update": client.planner.update_day_item,
            "remove": client.planner.remove_day_item,
        }[kind]

    services = {
        "add_custom_item": (
            custom_item,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("name"): vol.All(str, vol.Length(min=1, max=200)),
                vol.Required("calories"): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("protein_g", default=0): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("fat_g", default=0): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("carbs_g", default=0): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("eaten", default=False): bool,
                _DATE: str,
            },
        ),
        "add_product": (
            product,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("product_id"): vol.Coerce(int),
                vol.Required("measure_id"): vol.Coerce(int),
                vol.Optional("quantity", default=1): vol.All(
                    vol.Coerce(float), vol.Range(min=0.001)
                ),
                vol.Optional("eaten", default=False): bool,
                _DATE: str,
            },
        ),
        "add_product_unit": (
            product_unit,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("product_id"): vol.Coerce(int),
                vol.Required("amount"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.001)
                ),
                vol.Required("unit"): str,
                vol.Optional("eaten", default=False): bool,
                _DATE: str,
            },
        ),
        "add_recipe": (
            recipe,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("recipe_id"): vol.Coerce(int),
                vol.Optional("quantity", default=1): vol.All(
                    vol.Coerce(float), vol.Range(min=0.001)
                ),
                vol.Optional("eaten", default=False): bool,
                _DATE: str,
            },
        ),
        "update_item": (
            update_item,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("item_id"): str,
                vol.Optional("quantity"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.001)
                ),
                vol.Optional("measure_id"): vol.Coerce(int),
                vol.Optional("eaten"): bool,
                vol.Optional("name"): str,
                _DATE: str,
            },
        ),
        "remove_item": (
            remove_item,
            {vol.Required("meal"): _MEALS, vol.Required("item_id"): str, _DATE: str},
        ),
        "set_water": (
            set_water,
            {
                vol.Required("millilitres"): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=20000)
                ),
                _DATE: str,
            },
        ),
        "set_measurements": (
            set_measurements,
            {
                vol.Optional("weight"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=700)
                ),
                vol.Optional("weight_unit", default="KG"): vol.In(["KG", "LB"]),
                vol.Optional("fat_percentage"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100)
                ),
                vol.Optional("chest"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=300)
                ),
                vol.Optional("waist"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=300)
                ),
                vol.Optional("hips"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=300)
                ),
                vol.Optional("thigh"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=200)
                ),
                vol.Optional("arm"): vol.All(
                    vol.Coerce(float), vol.Range(min=1, max=150)
                ),
                _DATE: str,
            },
        ),
        "delete_measurements": (delete_measurements, {vol.Required("date"): str}),
        "set_note": (set_note, {vol.Required("note"): str, _DATE: str}),
        "add_activity": (
            add_activity,
            {
                vol.Required("activity_id"): vol.Coerce(int),
                vol.Required("minutes"): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=1440)
                ),
                vol.Required("energy_kcal"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=20000)
                ),
                _DATE: str,
            },
        ),
        "remove_activity": (
            remove_activity,
            {vol.Required("activity_id"): str, _DATE: str},
        ),
        "move_item": (
            move_item,
            {
                vol.Required("from_meal"): _MEALS,
                vol.Required("item_id"): str,
                vol.Optional("to_meal"): _MEALS,
                vol.Optional("to_date"): str,
                _DATE: str,
            },
        ),
        "copy_meal": (
            copy_meal,
            {
                vol.Required("from_meal"): _MEALS,
                vol.Required("to_date"): str,
                vol.Optional("to_meal"): _MEALS,
                vol.Optional("eaten"): bool,
                _DATE: str,
            },
        ),
        "replace_item": (
            replace_item,
            {
                vol.Required("meal"): _MEALS,
                vol.Required("item_id"): str,
                vol.Required("name"): str,
                vol.Required("calories"): vol.Coerce(float),
                vol.Optional("protein_g", default=0): vol.Coerce(float),
                vol.Optional("fat_g", default=0): vol.Coerce(float),
                vol.Optional("carbs_g", default=0): vol.Coerce(float),
                _DATE: str,
            },
        ),
        "set_water_glass_size": (
            set_glass_size,
            {
                vol.Required("millilitres"): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=3000)
                )
            },
        ),
    }
    for name, (handler, fields) in services.items():
        async_register_admin_service(
            hass, DOMAIN, name, handler, schema=_base_schema(fields)
        )
