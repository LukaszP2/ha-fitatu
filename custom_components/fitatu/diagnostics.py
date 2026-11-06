"""Privacy-safe diagnostics for Fitatu."""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import FitatuConfigEntry
from .const import CONF_SESSION, CONF_USER_ID


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FitatuConfigEntry
) -> dict[str, Any]:
    """Return configuration diagnostics without account or session secrets."""
    return {
        "account_configured": bool(entry.data.get(CONF_USER_ID)),
        "email_configured": bool(entry.data.get(CONF_EMAIL)),
        "session_configured": bool(entry.data.get(CONF_SESSION)),
        "monitoring_categories": entry.options.get("categories", []),
        "device_registered": dr.async_get(hass).async_get_device(
            identifiers={(entry.domain, entry.data.get(CONF_USER_ID, ""))}
        )
        is not None,
    }
