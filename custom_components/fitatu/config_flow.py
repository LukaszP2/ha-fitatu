"""Config flow for Fitatu."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from fitatu_api import FitatuApiClient, FitatuApiError, FitatuAuthError
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback

from .const import CONF_SESSION, CONF_USER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _login(
    hass: HomeAssistant, email: str, password: str
) -> tuple[str, dict[str, Any]]:
    """Authenticate directly with Fitatu and return the account ID and token session."""

    def login() -> tuple[str, dict[str, Any]]:
        client = FitatuApiClient.login(email, password)
        try:
            user_id = client.auth.fitatu_user_id
            if user_id is None:
                raise FitatuAuthError("Fitatu did not return an account identifier")
            return str(user_id), client.auth.to_session_data(include_tokens=True)
        finally:
            client.close()

    return await hass.async_add_executor_job(login)


class FitatuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle user setup and reauthentication for Fitatu."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for Fitatu email and password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                user_id, session = await _login(
                    self.hass, user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except FitatuAuthError:
                errors["base"] = "invalid_auth"
            except (FitatuApiError, OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while connecting to Fitatu")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Fitatu",
                    data={
                        CONF_USER_ID: user_id,
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_SESSION: session,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication for an existing account."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for credentials again and refresh the stored session."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                user_id, session = await _login(
                    self.hass, user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except FitatuAuthError:
                errors["base"] = "invalid_auth"
            except (FitatuApiError, OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                if user_id != entry.data[CONF_USER_ID]:
                    errors["base"] = "different_account"
                else:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            CONF_EMAIL: user_input[CONF_EMAIL],
                            CONF_SESSION: session,
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL, default=entry.data.get(CONF_EMAIL, "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of credentials."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                user_id, session = await _login(
                    self.hass, user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except FitatuAuthError:
                errors["base"] = "invalid_auth"
            except (FitatuApiError, OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reconfiguration")
                errors["base"] = "unknown"
            else:
                if user_id != entry.data[CONF_USER_ID]:
                    errors["base"] = "different_account"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data={
                            **entry.data,
                            CONF_EMAIL: user_input[CONF_EMAIL],
                            CONF_SESSION: session,
                        },
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL, default=entry.data.get(CONF_EMAIL, "")
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FitatuOptionsFlow:
        """Return options flow for selecting monitoring categories."""
        return FitatuOptionsFlow()


class FitatuOptionsFlow(config_entries.OptionsFlowWithReload):
    """Allow users to select groups of monitoring sensors."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Display category switches."""
        from .const import (
            CATEGORY_ACTIVITY,
            CATEGORY_ADVANCED,
            CATEGORY_BODY,
            CATEGORY_CORE,
            CATEGORY_HYDRATION,
            CATEGORY_NUTRITION,
            DEFAULT_MONITORING_CATEGORIES,
        )

        if user_input is not None:
            selected = [key for key, enabled in user_input.items() if enabled]
            return self.async_create_entry(title="", data={"categories": selected})

        current = self.config_entry.options.get(
            "categories", DEFAULT_MONITORING_CATEGORIES
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CATEGORY_CORE, default=CATEGORY_CORE in current): bool,
                    vol.Required(
                        CATEGORY_NUTRITION, default=CATEGORY_NUTRITION in current
                    ): bool,
                    vol.Required(
                        CATEGORY_HYDRATION, default=CATEGORY_HYDRATION in current
                    ): bool,
                    vol.Required(
                        CATEGORY_ACTIVITY, default=CATEGORY_ACTIVITY in current
                    ): bool,
                    vol.Required(CATEGORY_BODY, default=CATEGORY_BODY in current): bool,
                    vol.Required(
                        CATEGORY_ADVANCED, default=CATEGORY_ADVANCED in current
                    ): bool,
                }
            ),
        )
