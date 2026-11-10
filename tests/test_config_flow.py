"""Test the Fitatu config flow."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fitatu_api import FitatuApiError, FitatuAuthError
from homeassistant.data_entry_flow import FlowResultType

from custom_components.fitatu.config_flow import FitatuConfigFlow, FitatuOptionsFlow
from custom_components.fitatu.const import (
    CATEGORY_ACTIVITY,
    CATEGORY_CORE,
    CONF_SESSION,
    CONF_USER_ID,
)


class TestFitatuConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test suite for FitatuConfigFlow."""

    async def test_step_user_show_form(self):
        """Test user step shows the form when input is None."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        result = await flow.async_step_user(user_input=None)

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {})

    async def test_step_user_invalid_auth(self):
        """Test invalid auth populates errors['base'] = 'invalid_auth'."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.fitatu.config_flow._login",
            side_effect=FitatuAuthError("Invalid credentials"),
        ):
            result = await flow.async_step_user(
                {"email": "test@example.com", "password": "wrong"}
            )

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {"base": "invalid_auth"})

    async def test_step_user_cannot_connect(self):
        """Test connection error populates errors['base'] = 'cannot_connect'."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.fitatu.config_flow._login",
            side_effect=FitatuApiError("Timeout"),
        ):
            result = await flow.async_step_user(
                {"email": "test@example.com", "password": "pass"}
            )

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {"base": "cannot_connect"})

    async def test_step_user_unknown_error(self):
        """Test unknown error populates errors['base'] = 'unknown'."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.fitatu.config_flow._login",
            side_effect=RuntimeError("Boom"),
        ):
            result = await flow.async_step_user(
                {"email": "test@example.com", "password": "pass"}
            )

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {"base": "unknown"})

    async def test_step_user_success(self):
        """Test successful user step creates entry."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        fake_session = {"token": "secret"}
        with patch(
            "custom_components.fitatu.config_flow._login",
            return_value=("12345", fake_session),
        ):
            result = await flow.async_step_user(
                {"email": "user@example.com", "password": "password123"}
            )

        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        self.assertEqual(result["title"], "Fitatu")
        self.assertEqual(
            result["data"],
            {
                CONF_USER_ID: "12345",
                "email": "user@example.com",
                CONF_SESSION: fake_session,
            },
        )

    async def test_reauth_flow_success(self):
        """Test reauth flow succeeds with correct account."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries.async_reload = AsyncMock()
        flow.context = {"entry_id": "entry1"}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {
            CONF_USER_ID: "12345",
            "email": "user@example.com",
            CONF_SESSION: {},
        }
        flow._get_reauth_entry = MagicMock(return_value=entry)

        fake_session = {"token": "renewed"}
        with patch(
            "custom_components.fitatu.config_flow._login",
            return_value=("12345", fake_session),
        ):
            result = await flow.async_step_reauth_confirm(
                {"email": "user@example.com", "password": "new_password"}
            )

        self.assertEqual(result["type"], FlowResultType.ABORT)
        self.assertEqual(result["reason"], "reauth_successful")
        flow.hass.config_entries.async_update_entry.assert_called_once()
        flow.hass.config_entries.async_reload.assert_called_once_with("entry1")

    async def test_reauth_flow_different_account(self):
        """Test reauth flow rejects a different user id with base error."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        flow.context = {"entry_id": "entry1"}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {
            CONF_USER_ID: "12345",
            "email": "user@example.com",
            CONF_SESSION: {},
        }
        flow._get_reauth_entry = MagicMock(return_value=entry)

        with patch(
            "custom_components.fitatu.config_flow._login",
            return_value=("99999", {"token": "other"}),
        ):
            result = await flow.async_step_reauth_confirm(
                {"email": "other@example.com", "password": "password"}
            )

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "reauth_confirm")
        self.assertEqual(result["errors"], {"base": "different_account"})

    async def test_options_flow(self):
        """Test options flow enables selected categories."""
        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.options = {"categories": [CATEGORY_CORE]}
        flow = FitatuOptionsFlow()
        flow.hass = MagicMock()
        flow.handler = "entry1"
        flow.hass.config_entries.async_get_known_entry.return_value = entry

        # Show form
        form = await flow.async_step_init(user_input=None)
        self.assertEqual(form["type"], FlowResultType.FORM)
        self.assertEqual(form["step_id"], "init")

        # Submit form
        result = await flow.async_step_init(
            user_input={
                CATEGORY_CORE: True,
                CATEGORY_ACTIVITY: True,
            }
        )
        self.assertEqual(result["type"], FlowResultType.CREATE_ENTRY)
        self.assertEqual(
            sorted(result["data"]["categories"]),
            sorted([CATEGORY_CORE, CATEGORY_ACTIVITY]),
        )

    async def test_reconfigure_flow_success(self):
        """Test reconfigure flow succeeds and updates entry."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        flow.context = {"entry_id": "entry1"}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {
            CONF_USER_ID: "12345",
            "email": "user@example.com",
            CONF_SESSION: {},
        }
        flow._get_reconfigure_entry = MagicMock(return_value=entry)
        flow.async_update_reload_and_abort = MagicMock(
            return_value={"type": FlowResultType.ABORT, "reason": "reconfigure_successful"}
        )

        fake_session = {"token": "reconfigured"}
        with patch(
            "custom_components.fitatu.config_flow._login",
            return_value=("12345", fake_session),
        ):
            result = await flow.async_step_reconfigure(
                {"email": "user@example.com", "password": "new_password"}
            )

        self.assertEqual(result["type"], FlowResultType.ABORT)
        self.assertEqual(result["reason"], "reconfigure_successful")
        flow.async_update_reload_and_abort.assert_called_once()

    async def test_reconfigure_flow_different_account(self):
        """Test reconfigure flow rejects a different user id."""
        flow = FitatuConfigFlow()
        flow.hass = MagicMock()
        flow.context = {"entry_id": "entry1"}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {
            CONF_USER_ID: "12345",
            "email": "user@example.com",
            CONF_SESSION: {},
        }
        flow._get_reconfigure_entry = MagicMock(return_value=entry)

        with patch(
            "custom_components.fitatu.config_flow._login",
            return_value=("99999", {"token": "other"}),
        ):
            result = await flow.async_step_reconfigure(
                {"email": "other@example.com", "password": "password"}
            )

        self.assertEqual(result["type"], FlowResultType.FORM)
        self.assertEqual(result["step_id"], "reconfigure")
        self.assertEqual(result["errors"], {"base": "different_account"})
