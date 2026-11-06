"""Test the Fitatu coordinator."""

import unittest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from fitatu_api import FitatuApiError, FitatuAuthError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.fitatu.const import CONF_SESSION, CONF_USER_ID
from custom_components.fitatu.coordinator import (
    FitatuCoordinator,
    _count_day_rows,
    _latest_weight,
    _number,
    _nutrient_record,
    _water_value,
)


class TestFitatuCoordinator(unittest.IsolatedAsyncioTestCase):
    """Test suite for FitatuCoordinator."""

    def test_helpers(self):
        """Test coordinator parsing helper functions."""
        # _number helper
        self.assertIsNone(_number(None))
        self.assertIsNone(_number(False))
        self.assertIsNone(_number("invalid"))
        self.assertIsNone(_number(-10))
        self.assertEqual(_number("123.45"), 123.45)
        self.assertEqual(_number("123,45"), 123.45)
        self.assertEqual(_number({"value": "500"}), 500.0)

        # _count_day_rows
        self.assertIsNone(_count_day_rows(None, "dietPlan"))
        self.assertEqual(_count_day_rows({"dietPlan": {"breakfast": {"items": [1, 2]}}}, "dietPlan"), 2)
        self.assertEqual(_count_day_rows({"activityPlan": [1, 2, 3]}, "activityPlan"), 3)

        # _water_value
        self.assertEqual(_water_value({"waterConsumptionMl": 1500}), 1500.0)
        self.assertEqual(_water_value({"water": {"amount": 2000}}), 2000.0)
        self.assertIsNone(_water_value({}))

        # _latest_weight
        self.assertEqual(_latest_weight(None), (None, None, None))
        self.assertEqual(
            _latest_weight({"list": [{"value": "75.5", "unit": "kg", "date": "2026-11-01"}]}),
            (75.5, "KG", "2026-11-01"),
        )

        # _nutrient_record
        res = _nutrient_record({"energy": {"eaten": 1200, "current": 1500}}, "energy")
        self.assertEqual(res["eaten"], 1200.0)
        self.assertEqual(res["current"], 1500.0)

    def test_account_date(self):
        """Test account_date method returns current date in appropriate timezone."""
        hass = MagicMock()
        hass.config.time_zone = "UTC"
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "123", CONF_SESSION: {}}

        with patch("custom_components.fitatu.coordinator.FitatuAuthContext"), patch(
            "custom_components.fitatu.coordinator.FitatuApiClient"
        ):
            coord = FitatuCoordinator(hass, entry)
            coord.auth.app_timezone = "Europe/Warsaw"
            d = coord.account_date()
            self.assertIsInstance(d, date)

    async def test_update_data_auth_failed(self):
        """Test _async_update_data raises ConfigEntryAuthFailed on FitatuAuthError."""
        hass = MagicMock()
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "123", CONF_SESSION: {}}

        with patch("custom_components.fitatu.coordinator.FitatuAuthContext"), patch(
            "custom_components.fitatu.coordinator.FitatuApiClient"
        ):
            coord = FitatuCoordinator(hass, entry)
            hass.async_add_executor_job = AsyncMock(side_effect=FitatuAuthError("Token expired"))

            with self.assertRaises(ConfigEntryAuthFailed):
                await coord._async_update_data()

    async def test_update_data_api_failed(self):
        """Test _async_update_data raises UpdateFailed on FitatuApiError."""
        hass = MagicMock()
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "123", CONF_SESSION: {}}

        with patch("custom_components.fitatu.coordinator.FitatuAuthContext"), patch(
            "custom_components.fitatu.coordinator.FitatuApiClient"
        ):
            coord = FitatuCoordinator(hass, entry)
            hass.async_add_executor_job = AsyncMock(side_effect=FitatuApiError("500 Server error"))

            with self.assertRaises(UpdateFailed):
                await coord._async_update_data()

    async def test_update_data_success_renews_session(self):
        """Test _async_update_data saves renewed session if it changed."""
        hass = MagicMock()
        entry = MagicMock()
        old_session = {"token": "old"}
        new_session = {"token": "new"}
        entry.data = {CONF_USER_ID: "123", CONF_SESSION: old_session}

        with patch("custom_components.fitatu.coordinator.FitatuAuthContext"), patch(
            "custom_components.fitatu.coordinator.FitatuApiClient"
        ):
            coord = FitatuCoordinator(hass, entry)
            coord.hass = hass
            hass.async_add_executor_job = AsyncMock(return_value=({"energy_eaten": 1500}, new_session))

            data = await coord._async_update_data()
            self.assertEqual(data["energy_eaten"], 1500)
            hass.config_entries.async_update_entry.assert_called_once_with(
                entry,
                data={CONF_USER_ID: "123", CONF_SESSION: new_session},
            )
