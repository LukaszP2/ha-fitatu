"""Test Fitatu actions and services."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.exceptions import HomeAssistantError

from custom_components.fitatu.actions import async_setup_actions


class TestFitatuActions(unittest.IsolatedAsyncioTestCase):
    """Test suite for Fitatu actions."""

    async def test_coordinator_client_none_safety(self):
        """Test actions throw HomeAssistantError when entry or runtime_data is None."""
        hass = MagicMock()
        registered_services = {}

        def mock_register(h, domain, name, handler, schema=None):
            registered_services[name] = handler

        with patch(
            "custom_components.fitatu.actions.async_register_admin_service",
            side_effect=mock_register,
        ):
            await async_setup_actions(hass)

        self.assertIn("set_water", registered_services)

        # Call with nonexistent entry
        with patch("custom_components.fitatu.actions.async_get_config_entry", return_value=None):
            call = MagicMock()
            call.data = {"config_entry_id": "invalid_id", "millilitres": 250}
            with self.assertRaises(HomeAssistantError) as ctx:
                await registered_services["set_water"](call)
            self.assertIn("Fitatu entry is not loaded", str(ctx.exception))

    async def test_action_success_triggers_refresh(self):
        """Test action executes API operation and triggers coordinator refresh."""
        hass = MagicMock()
        registered_services = {}

        def mock_register(h, domain, name, handler, schema=None):
            registered_services[name] = handler

        with patch(
            "custom_components.fitatu.actions.async_register_admin_service",
            side_effect=mock_register,
        ):
            await async_setup_actions(hass)

        entry = MagicMock()
        entry.data = {"user_id": "123"}
        coordinator = MagicMock()
        coordinator.account_date.return_value = "2026-11-06"
        coordinator.async_request_refresh = AsyncMock()
        coordinator.client.water.set_day = MagicMock(return_value={"ok": True})
        entry.runtime_data = coordinator

        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

        with patch("custom_components.fitatu.actions.async_get_config_entry", return_value=entry):
            call = MagicMock()
            call.data = {"config_entry_id": "entry1", "millilitres": 500}
            await registered_services["set_water"](call)

            coordinator.client.water.set_day.assert_called_once_with("123", "2026-11-06", 500)
            coordinator.async_request_refresh.assert_called_once()
