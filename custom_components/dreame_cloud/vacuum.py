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
    PROP_CHARGING_STATUS,
    PROP_STATUS,
    PROP_SUCTION_LEVEL,
    PROP_WATER_VOLUME,
    PROP_FAULTS,
    PROP_TASK_STATUS,
    PROP_LAST_CLEAN_TIME,
    PROP_LAST_CLEAN_AREA,
    PROP_MAIN_BRUSH_LIFE,
    PROP_SIDE_BRUSH_LIFE,
    PROP_FILTER_LIFE,
    PROP_SENSOR_DIRTY,
    PROP_MOP_PAD_LIFE,
    PROP_TOTAL_CLEAN_TIME,
    PROP_TOTAL_CLEAN_AREA,
    PROP_SELF_WASH_BASE_STATUS,
    PROP_MOP_IN_STATION,
    PROP_MOP_PAD_INSTALLED,
    ACTION_START,
    ACTION_PAUSE,
    ACTION_CHARGE,
    ACTION_STOP,
    SUCTION_MAP,
    STATUS_MAP,
    CHARGING_STATUS_MAP,
    TASK_STATUS_MAP,
    ERROR_MAP,
    WATER_MAP,
)

_LOGGER = logging.getLogger(__name__)

# Status → VacuumActivity mapping
CLEANING_STATUSES = {1, 18, 19, 20, 24, 25}   # any active cleaning
PAUSED_STATUSES   = {17}                        # standby after pause
DOCKED_STATUSES   = {3}                         # charging on base
RETURNING_STATUSES = {5}                        # going home
ERROR_STATUSES    = {9}                         # fault
# Everything else (11=sleeping, 14=sleeping, 6=wifi) → idle

FAN_SPEED_LIST = ["quiet", "standard", "strong", "turbo"]
REVERSE_SUCTION_MAP = {v: k for k, v in SUCTION_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreame vacuum entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DreameVacuumEntity(
            coordinator=data["coordinator"],
            client=data["client"],
            session=data["session"],
            device_id=entry.data[CONF_DEVICE_ID],
            device_name=entry.title,
        )]
    )


class DreameVacuumEntity(CoordinatorEntity, StateVacuumEntity):
    """Full vacuum entity compatible with vacuum-card and standard HA vacuum services."""

    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.STATUS
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.STATE
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

    # ── State ────────────────────────────────────────────────────────────────

    @property
    def activity(self) -> VacuumActivity | None:
        """Return current VacuumActivity state (used by HA core + vacuum-card)."""
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
        return VacuumActivity.IDLE

    # ── Attributes read by vacuum-card ────────────────────────────────────────

    @property
    def battery_level(self) -> int | None:
        """Battery % — displayed by vacuum-card battery tip."""
        return self.coordinator.data.get(PROP_BATTERY_LEVEL)

    @property
    def fan_speed(self) -> str | None:
        """Current suction level string — shown in vacuum-card fan speed dropdown."""
        raw = self.coordinator.data.get(PROP_SUCTION_LEVEL)
        return SUCTION_MAP.get(raw) if raw is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Extra attributes exposed on the entity.

        vacuum-card reads:
          - status  (friendly status string shown below name)
          - fan_speed_list (for the fan speed dropdown — we also set _attr_fan_speed_list)
          - battery_level / battery_icon (fallback if battery_entity not set)

        Also exposing all useful Dreame data here so stats in vacuum-card
        can reference them via `attribute:` without needing separate sensor entities.
        """
        data = self.coordinator.data
        attrs: dict[str, Any] = {}

        # ── Status strings (vacuum-card uses 'status' attribute) ──
        raw_status = data.get(PROP_STATUS)
        if raw_status is not None:
            attrs["status"] = STATUS_MAP.get(raw_status, str(raw_status))
            attrs["status_code"] = raw_status

        raw_task = data.get(PROP_TASK_STATUS)
        if raw_task is not None:
            attrs["task_status"] = TASK_STATUS_MAP.get(raw_task, str(raw_task))

        raw_charging = data.get(PROP_CHARGING_STATUS)
        if raw_charging is not None:
            attrs["charging_status"] = CHARGING_STATUS_MAP.get(raw_charging, str(raw_charging))

        # ── Error ──
        fault = data.get(PROP_FAULTS)
        if fault is not None:
            attrs["error"] = ERROR_MAP.get(fault, f"Error {fault}") if fault != 0 else None

        # ── Water volume (for mop control) ──
        raw_water = data.get(PROP_WATER_VOLUME)
        if raw_water is not None:
            attrs["water_volume"] = WATER_MAP.get(raw_water, str(raw_water))

        # ── Last clean session ──
        last_time = data.get(PROP_LAST_CLEAN_TIME)
        if last_time is not None:
            attrs["last_clean_time"] = last_time           # minutes
        last_area = data.get(PROP_LAST_CLEAN_AREA)
        if last_area is not None:
            attrs["last_clean_area"] = last_area           # m²

        # ── Lifetime totals ──
        total_time = data.get(PROP_TOTAL_CLEAN_TIME)
        if total_time is not None:
            attrs["total_clean_time"] = total_time         # minutes
            attrs["total_clean_time_hours"] = round(total_time / 60, 1)
        total_area = data.get(PROP_TOTAL_CLEAN_AREA)
        if total_area is not None:
            attrs["total_clean_area"] = total_area         # m²

        # ── Consumable life (%) — can be referenced in vacuum-card stats ──
        for prop, key in [
            (PROP_MAIN_BRUSH_LIFE,  "main_brush_life"),
            (PROP_SIDE_BRUSH_LIFE,  "side_brush_life"),
            (PROP_FILTER_LIFE,      "filter_life"),
            (PROP_SENSOR_DIRTY,     "sensor_cleanliness"),
            (PROP_MOP_PAD_LIFE,     "mop_pad_life"),
        ]:
            val = data.get(prop)
            if val is not None:
                attrs[key] = val

        # ── Station / mop state ──
        wash_status = data.get(PROP_SELF_WASH_BASE_STATUS)
        if wash_status is not None:
            wash_map = {0: "idle", 1: "washing", 2: "drying", 3: "paused"}
            attrs["self_wash_base_status"] = wash_map.get(wash_status, str(wash_status))

        mop_in_station = data.get(PROP_MOP_IN_STATION)
        if mop_in_station is not None:
            attrs["mop_in_station"] = bool(mop_in_station)

        mop_installed = data.get(PROP_MOP_PAD_INSTALLED)
        if mop_installed is not None:
            attrs["mop_pad_installed"] = bool(mop_installed)

        # ── Battery icon (fallback for vacuum-card if battery_entity not set) ──
        batt = self.coordinator.data.get(PROP_BATTERY_LEVEL)
        if batt is not None:
            if batt >= 90:
                attrs["battery_icon"] = "mdi:battery"
            elif batt >= 70:
                attrs["battery_icon"] = "mdi:battery-70"
            elif batt >= 50:
                attrs["battery_icon"] = "mdi:battery-50"
            elif batt >= 30:
                attrs["battery_icon"] = "mdi:battery-30"
            else:
                attrs["battery_icon"] = "mdi:battery-alert"

        return attrs

    # ── Actions (called by vacuum-card toolbar + HA automations) ─────────────

    async def async_start(self) -> None:
        """Start auto cleaning."""
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
        """Send robot back to dock."""
        await self._client.call_action(self._session, ACTION_CHARGE[0], ACTION_CHARGE[1])
        await self.coordinator.async_request_refresh()

    async def async_locate(self, **kwargs: Any) -> None:
        """Play a sound to locate the robot. Uses the 'find_me' action (siid=4, aiid=9) if available,
        otherwise sends a test sound command."""
        try:
            # siid=4 aiid=9 is TEST_SOUND on most Dreame models
            await self._client.call_action(self._session, 4, 9)
        except Exception:
            _LOGGER.warning("Locate (find me) not supported on this model")
        await self.coordinator.async_request_refresh()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set suction level (quiet/standard/strong/turbo)."""
        level = REVERSE_SUCTION_MAP.get(fan_speed)
        if level is None:
            _LOGGER.error("Invalid fan speed '%s'. Valid: %s", fan_speed, FAN_SPEED_LIST)
            return
        siid, piid = PROP_SUCTION_LEVEL
        await self._client.set_property(self._session, siid, piid, level)
        await self.coordinator.async_request_refresh()

    async def async_send_command(
        self, command: str, params: dict | list | None = None, **kwargs: Any
    ) -> None:
        """
        Send a raw command to the vacuum. Useful for advanced automations.

        Examples:
          - command: "shortcut", params: {"id": 33}  → triggers shortcut by ID
          - command: "set_suction", params: {"level": 2}
        """
        from .const import SHORTCUT_STATUS_VALUE, CLEANING_PROPERTIES_PIID, STATUS_PIID
        params = params or {}

        if command == "shortcut":
            shortcut_id = params.get("id")
            if shortcut_id is None:
                _LOGGER.error("send_command 'shortcut' requires params.id")
                return
            await self._client.call_action(
                self._session,
                siid=4,
                aiid=1,
                params=[
                    {"piid": STATUS_PIID, "value": SHORTCUT_STATUS_VALUE},
                    {"piid": CLEANING_PROPERTIES_PIID, "value": str(shortcut_id)},
                ],
            )
        elif command == "set_water_volume":
            level = params.get("level", 2)
            siid, piid = PROP_WATER_VOLUME
            await self._client.set_property(self._session, siid, piid, level)
        else:
            _LOGGER.warning("Unknown send_command: %s", command)

        await self.coordinator.async_request_refresh()
