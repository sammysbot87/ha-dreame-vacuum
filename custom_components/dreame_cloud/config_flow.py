"""Config flow for Dreame Vacuum Cloud."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import DreameCloudAuth, DreameCloudClient, AuthenticationError, APIError
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_DEVICE_ID,
    CONF_HOST_PREFIX,
    DEFAULT_REGION,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS),
    }
)

STEP_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
    }
)


async def validate_credentials(hass: HomeAssistant, data: dict) -> dict:
    """Validate login credentials and return tokens + devices."""
    auth = DreameCloudAuth(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        region=data[CONF_REGION],
    )
    async with aiohttp.ClientSession() as session:
        if not await auth.login(session):
            raise AuthenticationError("Invalid credentials")

        # Temporarily create a client with no device to list devices
        client = DreameCloudClient(auth, "", "10000")
        devices = await client.get_devices(session)

    return {
        "access_token": auth.access_token,
        "refresh_token": auth.refresh_token,
        "devices": devices,
    }


class DreameCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dreame Vacuum Cloud."""

    VERSION = 1

    def __init__(self) -> None:
        self._username: str = ""
        self._password: str = ""
        self._region: str = DEFAULT_REGION
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._devices: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step — credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                result = await validate_credentials(self.hass, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"
            else:
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._region = user_input[CONF_REGION]
                self._access_token = result["access_token"]
                self._refresh_token = result["refresh_token"]
                self._devices = result["devices"]

                if len(self._devices) == 1:
                    # Auto-select if only one device
                    return await self._create_entry(self._devices[0])
                elif len(self._devices) > 1:
                    return await self.async_step_device()
                else:
                    errors["base"] = "no_devices"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection when multiple devices exist."""
        errors: dict[str, str] = {}

        device_options = {
            d["did"]: f"{d.get('customName', d['model'])} ({d['did']})"
            for d in self._devices
        }

        if user_input is not None:
            did = user_input[CONF_DEVICE_ID]
            device = next((d for d in self._devices if d["did"] == did), None)
            if device:
                return await self._create_entry(device)
            errors["base"] = "invalid_device"

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_ID): vol.In(device_options)}),
            errors=errors,
        )

    async def _create_entry(self, device: dict) -> FlowResult:
        """Create the config entry."""
        bind_domain = device.get("bindDomain", "")
        host_prefix = bind_domain.split(".")[0] if bind_domain else "10000"

        await self.async_set_unique_id(device["did"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=device.get("customName", device["model"]),
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_REGION: self._region,
                CONF_ACCESS_TOKEN: self._access_token,
                CONF_REFRESH_TOKEN: self._refresh_token,
                CONF_DEVICE_ID: device["did"],
                CONF_HOST_PREFIX: host_prefix,
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            data = {
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_REGION: entry.data[CONF_REGION],
            }
            try:
                result = await validate_credentials(self.hass, data)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_ACCESS_TOKEN: result["access_token"],
                        CONF_REFRESH_TOKEN: result["refresh_token"],
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
