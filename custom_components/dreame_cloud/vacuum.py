"""Vacuum platform for Dreame Vacuum Cloud."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    VacuumActivity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    PROP_BATTERY_LEVEL,
    PROP_STATUS,
    PROP_CHARGING_STATUS,
    PROP_SUCTION_LEVEL,
    PROP_FAULTS,
    PROP_TASK_STATUS,
    ACTION_START,
    ACTION_PAUSE,
    ACTION_CHARGE,
    ACTION_STOP,
    SUCTION_MAP,
    ERROR_MAP,
)

_LOGGER = logging.getLogger(__name__)

# Status codes that mean the robot is actively cleaning
CLEANING_STATUSES = {1, 18, 19, 20, 24, 25}
# Status codes that mean it's paused
PAUSED_STATUSES = {17}
# Status codes that mean it's docked/charging
DOCKED_STATUSES = {3}
# Status codes that mean it's returning home
RETURNING_STATUSES = {5}
# Status codes that mean error
ERROR_STATUSES = {9}

FAN_SPEED_LIST = ["quiet", "standard", "strong", "turbo"]
REVERSE_SUCTION_MAP = {v: k for k, v in SUCTION_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreame vacuum entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    session = data["session"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.title

    async_add_entities(
        [DreameVacuumEntity(coordinator, client, session, device_id, device_name)]
    )


class DreameVacuumEntity(CoordinatorEntity, StateVacuumEntity):
    """Representation of the Dreame vacuum as a HA vacuum entity."""

    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.STATUS
        | VacuumEntityFeature.FAN_SPEED
    )

    _attr_fan_speed_list = FAN_SPEED_LIST

    def __init__(self, coordinator, client, session, device_id, device_name):
        super().__init__(coordinator)
        self._client = client
        self._session = session
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_vacuum"
        self._attr_name = device_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Dreame",
            "model": "L10s Ultra Gen 2",
        }

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the current vacuum activity/state."""
        status = self.coordinator.data.get(PROP_STATUS)
        if status is None:
            return None
        if status in CLEANING_STATUSES:
            return VacuumActivity.CLEANING
        if status in DOCKED_STATUSES:
            return VacuumActivity.DOCKED
        if status in RETURNING_STATUSES:
            return VacuumActivity.RETURNING
        if status in ERROR_STATUSES:
            return VacuumActivity.ERROR
        if status in PAUSED_STATUSES:
            return VacuumActivity.PAUSED
        # sleeping / standby / etc → idle
        return VacuumActivity.IDLE

    @property
    def battery_level(self) -> int | None:
        return self.coordinator.data.get(PROP_BATTERY_LEVEL)

    @property
    def fan_speed(self) -> str | None:
        raw = self.coordinator.data.get(PROP_SUCTION_LEVEL)
        if raw is None:
            return None
        return SUCTION_MAP.get(raw, str(raw))

    @property
    def error(self) -> str | None:
        fault = self.coordinator.data.get(PROP_FAULTS)
        if fault is None or fault == 0:
            return None
        return ERROR_MAP.get(fault, f"Error {fault}")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        attrs: dict[str, Any] = {}
        status = data.get(PROP_STATUS)
        if status is not None:
            from .const import STATUS_MAP
            attrs["status_code"] = status
            attrs["status"] = STATUS_MAP.get(status, str(status))
        task = data.get(PROP_TASK_STATUS)
        if task is not None:
            from .const import TASK_STATUS_MAP
            attrs["task"] = TASK_STATUS_MAP.get(task, str(task))
        charging = data.get(PROP_CHARGING_STATUS)
        if charging is not None:
            from .const import CHARGING_STATUS_MAP
            attrs["charging_status"] = CHARGING_STATUS_MAP.get(charging, str(charging))
        return attrs

    async def async_start(self) -> None:
        """Start or resume cleaning."""
        await self._client.call_action(self._session, ACTION_START[0], ACTION_START[1])
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause cleaning."""
        await self._client.call_action(self._session, ACTION_PAUSE[0], ACTION_PAUSE[1])
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        await self._client.call_action(self._session, ACTION_STOP[0], ACTION_STOP[1])
        await self.coordinator.async_request_refresh()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return to dock."""
        await self._client.call_action(self._session, ACTION_CHARGE[0], ACTION_CHARGE[1])
        await self.coordinator.async_request_refresh()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set suction level."""
        level = REVERSE_SUCTION_MAP.get(fan_speed)
        if level is None:
            _LOGGER.error("Invalid fan speed: %s", fan_speed)
            return
        siid, piid = PROP_SUCTION_LEVEL
        await self._client.set_property(self._session, siid, piid, level)
        await self.coordinator.async_request_refresh()
