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

    async def test_all_actions_execution(self):
        """Test execution and delegation of all registered services."""
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
        entry.runtime_data = coordinator
        hass.async_add_executor_job = AsyncMock(side_effect=lambda fn: fn())

        with patch("custom_components.fitatu.actions.async_get_config_entry", return_value=entry):
            # 1. add_custom_item
            call = MagicMock()
            call.data = {"config_entry_id": "entry1", "meal": "breakfast", "name": "Apple", "calories": 52}
            await registered_services["add_custom_item"](call)
            coordinator.client.planner.add_custom_item_to_day_meal.assert_called_once()

            # 2. add_product
            call.data = {"config_entry_id": "entry1", "meal": "lunch", "product_id": 10, "measure_id": 2, "quantity": 1.5}
            await registered_services["add_product"](call)
            coordinator.client.planner.add_product_to_day_meal.assert_called_once()

            # 3. add_product_unit
            call.data = {"config_entry_id": "entry1", "meal": "lunch", "product_id": 10, "amount": 100, "unit": "g"}
            await registered_services["add_product_unit"](call)
            coordinator.client.planner.add_product_to_day_meal_with_unit.assert_called_once()

            # 4. add_recipe
            call.data = {"config_entry_id": "entry1", "meal": "dinner", "recipe_id": 99}
            await registered_services["add_recipe"](call)
            coordinator.client.planner.add_recipe_to_day_meal.assert_called_once()

            # 5. update_item
            call.data = {"config_entry_id": "entry1", "meal": "dinner", "item_id": "item1", "quantity": 2.0}
            await registered_services["update_item"](call)
            coordinator.client.planner.update_day_item.assert_called_once()

            # 6. remove_item
            call.data = {"config_entry_id": "entry1", "meal": "dinner", "item_id": "item1"}
            await registered_services["remove_item"](call)
            coordinator.client.planner.remove_day_item.assert_called_once()

            # 7. set_measurements
            call.data = {"config_entry_id": "entry1", "weight": 75.5, "weight_unit": "KG"}
            await registered_services["set_measurements"](call)
            coordinator.client.measurements.set_day.assert_called_once()

            # 8. delete_measurements
            call.data = {"config_entry_id": "entry1", "date": "2026-11-06"}
            await registered_services["delete_measurements"](call)
            coordinator.client.measurements.delete_day.assert_called_once()

            # 9. set_note
            call.data = {"config_entry_id": "entry1", "note": "Great workout"}
            await registered_services["set_note"](call)
            coordinator.client.planner.set_note.assert_called_once()

            # 10. add_activity
            call.data = {"config_entry_id": "entry1", "activity_id": 5, "minutes": 30, "energy_kcal": 200}
            await registered_services["add_activity"](call)
            coordinator.client.planner.add_activity.assert_called_once()

            # 11. remove_activity
            call.data = {"config_entry_id": "entry1", "activity_id": "act1"}
            await registered_services["remove_activity"](call)
            coordinator.client.planner.remove_activity.assert_called_once()

            # 12. move_item
            call.data = {"config_entry_id": "entry1", "from_meal": "breakfast", "item_id": "item1", "to_meal": "lunch"}
            await registered_services["move_item"](call)
            coordinator.client.planner.move_day_item.assert_called_once()

            # 13. copy_meal
            call.data = {"config_entry_id": "entry1", "from_meal": "breakfast", "to_date": "2026-11-07", "to_meal": "breakfast"}
            await registered_services["copy_meal"](call)
            coordinator.client.planner.copy_meal.assert_called_once()

            # 14. replace_item
            call.data = {"config_entry_id": "entry1", "meal": "dinner", "item_id": "item1", "name": "Salad", "calories": 150}
            await registered_services["replace_item"](call)
            coordinator.client.planner.replace_day_item_with_custom_item.assert_called_once()

            # 15. set_water_glass_size
            call.data = {"config_entry_id": "entry1", "millilitres": 250}
            await registered_services["set_water_glass_size"](call)
            coordinator.client.user_settings.update_water_settings.assert_called_once()

    async def test_update_item_and_measurements_validation(self):
        """Test update_item and set_measurements raise error when empty."""
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
        entry.runtime_data = MagicMock()
        with patch("custom_components.fitatu.actions.async_get_config_entry", return_value=entry):
            # update_item without fields
            call = MagicMock()
            call.data = {"config_entry_id": "entry1", "meal": "breakfast", "item_id": "it1"}
            with self.assertRaises(HomeAssistantError) as ctx:
                await registered_services["update_item"](call)
            self.assertIn("At least one food entry field must be provided", str(ctx.exception))

            # set_measurements without measurements
            call.data = {"config_entry_id": "entry1"}
            with self.assertRaises(HomeAssistantError) as ctx:
                await registered_services["set_measurements"](call)
            self.assertIn("At least one measurement must be provided", str(ctx.exception))
