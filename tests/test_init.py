"""Tests for Fitatu integration."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.fitatu import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.fitatu.const import PLATFORMS


class TestFitatuInit(unittest.IsolatedAsyncioTestCase):
    """Test suite for Fitatu initialization and entry lifecycles."""

    def test_import(self):
        """Test module can be imported."""
        import custom_components.fitatu

        self.assertIsNotNone(custom_components.fitatu)

    async def test_async_setup(self):
        """Test async_setup sets up actions."""
        hass = MagicMock()
        with patch(
            "custom_components.fitatu.async_setup_actions",
            new_callable=AsyncMock,
        ) as mock_actions:
            result = await async_setup(hass, {})
            self.assertTrue(result)
            mock_actions.assert_awaited_once_with(hass)

    async def test_async_setup_entry_success(self):
        """Test successful entry setup."""
        hass = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        entry = MagicMock()

        with patch("custom_components.fitatu.FitatuCoordinator") as mock_coord_cls:
            mock_coordinator = MagicMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coordinator

            result = await async_setup_entry(hass, entry)

            self.assertTrue(result)
            mock_coord_cls.assert_called_once_with(hass, entry)
            mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()
            self.assertEqual(entry.runtime_data, mock_coordinator)
            hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
                entry, PLATFORMS
            )

    async def test_async_unload_entry_success(self):
        """Test entry unload with close call verification."""
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

        entry = MagicMock()
        entry.runtime_data = MagicMock()

        result = await async_unload_entry(hass, entry)

        self.assertTrue(result)
        hass.config_entries.async_unload_platforms.assert_awaited_once_with(
            entry, PLATFORMS
        )
        hass.async_add_executor_job.assert_awaited_once_with(entry.runtime_data.close)
        entry.runtime_data.close.assert_called_once()

    async def test_async_unload_entry_failure(self):
        """Test entry unload failure does not close runtime_data."""
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
        hass.async_add_executor_job = AsyncMock()

        entry = MagicMock()
        entry.runtime_data = MagicMock()

        result = await async_unload_entry(hass, entry)

        self.assertFalse(result)
        hass.config_entries.async_unload_platforms.assert_awaited_once_with(
            entry, PLATFORMS
        )
        hass.async_add_executor_job.assert_not_called()
        entry.runtime_data.close.assert_not_called()
