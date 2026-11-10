"""Home Assistant integration for Fitatu."""

from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .actions import async_setup_actions
from .const import DOMAIN, PLATFORMS
from .coordinator import FitatuCoordinator

FitatuConfigEntry: TypeAlias = ConfigEntry[FitatuCoordinator]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register Fitatu actions independently of loaded config entries."""
    await async_setup_actions(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FitatuConfigEntry) -> bool:
    """Set up Fitatu from a config entry."""
    coordinator = FitatuCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FitatuConfigEntry) -> bool:
    """Unload a Fitatu config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await hass.async_add_executor_job(entry.runtime_data.close)
    return True
