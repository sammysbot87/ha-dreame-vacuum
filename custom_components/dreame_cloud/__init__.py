"""The Dreame Vacuum Cloud integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    DEFAULT_SCAN_INTERVAL,
    PROP_BATTERY_LEVEL,
    PROP_CHARGING_STATUS,
    PROP_STATUS,
    PROP_LAST_CLEAN_TIME,
    PROP_LAST_CLEAN_AREA,
    PROP_SUCTION_LEVEL,
    PROP_WATER_VOLUME,
    PROP_TASK_STATUS,
    PROP_FAULTS,
    PROP_SELF_WASH_BASE_STATUS,
    PROP_MOP_IN_STATION,
    PROP_MOP_PAD_INSTALLED,
    PROP_SHORTCUTS,
    PROP_MAIN_BRUSH_LIFE,
    PROP_SIDE_BRUSH_LIFE,
    PROP_FILTER_LIFE,
    PROP_SENSOR_DIRTY,
    PROP_MOP_PAD_LIFE,
    PROP_TOTAL_CLEAN_TIME,
    PROP_TOTAL_CLEAN_AREA,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.VACUUM, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

ALL_PROPERTIES = [
    PROP_BATTERY_LEVEL,
    PROP_CHARGING_STATUS,
    PROP_STATUS,
    PROP_LAST_CLEAN_TIME,
    PROP_LAST_CLEAN_AREA,
    PROP_SUCTION_LEVEL,
    PROP_WATER_VOLUME,
    PROP_TASK_STATUS,
    PROP_FAULTS,
    PROP_SELF_WASH_BASE_STATUS,
    PROP_MOP_IN_STATION,
    PROP_MOP_PAD_INSTALLED,
    PROP_SHORTCUTS,
    PROP_MAIN_BRUSH_LIFE,
    PROP_SIDE_BRUSH_LIFE,
    PROP_FILTER_LIFE,
    PROP_SENSOR_DIRTY,
    PROP_MOP_PAD_LIFE,
    PROP_TOTAL_CLEAN_TIME,
    PROP_TOTAL_CLEAN_AREA,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Vacuum Cloud from a config entry."""
    auth = DreameCloudAuth(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        region=entry.data[CONF_REGION],
        access_token=entry.data.get(CONF_ACCESS_TOKEN),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
    )
    client = DreameCloudClient(
        auth=auth,
        device_id=entry.data[CONF_DEVICE_ID],
        host_prefix=entry.data[CONF_HOST_PREFIX],
    )

    session = aiohttp.ClientSession()

    async def async_update_data() -> dict:
        """Fetch data from the Dreame cloud API."""
        try:
            data = await client.get_properties(session, ALL_PROPERTIES)
            # Persist updated tokens to config entry
            if auth.access_token != entry.data.get(CONF_ACCESS_TOKEN):
                hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_ACCESS_TOKEN: auth.access_token,
                        CONF_REFRESH_TOKEN: auth.refresh_token,
                    },
                )
            return data
        except AuthenticationError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except (APIError, aiohttp.ClientError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"dreame_cloud_{entry.data[CONF_DEVICE_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "session": session,
        "auth": auth,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        await entry_data["session"].close()
    return unload_ok
