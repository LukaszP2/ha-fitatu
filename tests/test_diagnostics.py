"""Test Fitatu diagnostics."""

import unittest
from unittest.mock import MagicMock, patch

from custom_components.fitatu.const import CONF_SESSION, CONF_USER_ID
from custom_components.fitatu.diagnostics import async_get_config_entry_diagnostics


class TestFitatuDiagnostics(unittest.IsolatedAsyncioTestCase):
    """Test suite for Fitatu diagnostics."""

    async def test_diagnostics_privacy_safe(self):
        """Test that diagnostics does not expose raw session or credentials."""
        hass = MagicMock()
        entry = MagicMock()
        entry.domain = "fitatu"
        entry.data = {
            CONF_USER_ID: "user_secret_123",
            "email": "user@example.com",
            CONF_SESSION: {"jwt": "very_secret_token", "refresh": "another_secret"},
        }
        entry.options = {"categories": ["core", "nutrition"]}

        with patch("homeassistant.helpers.device_registry.async_get") as mock_dr:
            mock_dr.return_value.async_get_device.return_value = MagicMock()
            result = await async_get_config_entry_diagnostics(hass, entry)

        # Check that secret tokens are not in the dictionary
        self.assertNotIn("very_secret_token", str(result))
        self.assertNotIn("another_secret", str(result))
        self.assertTrue(result["account_configured"])
        self.assertTrue(result["email_configured"])
        self.assertTrue(result["session_configured"])
        self.assertTrue(result["device_registered"])
        self.assertEqual(result["monitoring_categories"], ["core", "nutrition"])
