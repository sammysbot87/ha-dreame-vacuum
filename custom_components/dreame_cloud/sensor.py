"""Sensors for Dreame Vacuum Cloud."""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime, UnitOfArea
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    PROP_BATTERY_LEVEL,
    PROP_CHARGING_STATUS,
    PROP_STATUS,
    PROP_LAST_CLEAN_TIME,
    PROP_LAST_CLEAN_AREA,
    PROP_SUCTION_LEVEL,
    PROP_WATER_VOLUME,
    PROP_TASK_STATUS,
    PROP_FAULTS,
    PROP_MAIN_BRUSH_LIFE,
    PROP_SIDE_BRUSH_LIFE,
    PROP_FILTER_LIFE,
    PROP_SENSOR_DIRTY,
    PROP_MOP_PAD_LIFE,
    PROP_TOTAL_CLEAN_TIME,
    PROP_TOTAL_CLEAN_AREA,
    PROP_SHORTCUTS,
    STATUS_MAP,
    CHARGING_STATUS_MAP,
    SUCTION_MAP,
    WATER_MAP,
    TASK_STATUS_MAP,
    ERROR_MAP,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DreameSensorEntityDescription(SensorEntityDescription):
    """Describes a Dreame sensor."""
    prop: tuple[int, int] = (0, 0)
    value_map: dict | None = None
    transform: Any = None  # callable to transform raw value


SENSOR_DESCRIPTIONS: tuple[DreameSensorEntityDescription, ...] = (
    DreameSensorEntityDescription(
        key="battery",
        name="Battery",
        prop=PROP_BATTERY_LEVEL,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DreameSensorEntityDescription(
        key="charging_status",
        name="Charging Status",
        prop=PROP_CHARGING_STATUS,
        value_map=CHARGING_STATUS_MAP,
    ),
    DreameSensorEntityDescription(
        key="status",
        name="Status",
        prop=PROP_STATUS,
        value_map=STATUS_MAP,
    ),
    DreameSensorEntityDescription(
        key="task_status",
        name="Task Status",
        prop=PROP_TASK_STATUS,
        value_map=TASK_STATUS_MAP,
    ),
    DreameSensorEntityDescription(
        key="suction_level",
        name="Suction Level",
        prop=PROP_SUCTION_LEVEL,
        value_map=SUCTION_MAP,
    ),
    DreameSensorEntityDescription(
        key="water_volume",
        name="Water Volume",
        prop=PROP_WATER_VOLUME,
        value_map=WATER_MAP,
    ),
    DreameSensorEntityDescription(
        key="last_clean_time",
        name="Last Clean Duration",
        prop=PROP_LAST_CLEAN_TIME,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    DreameSensorEntityDescription(
        key="last_clean_area",
        name="Last Clean Area",
        prop=PROP_LAST_CLEAN_AREA,
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:floor-plan",
    ),
    DreameSensorEntityDescription(
        key="total_clean_time",
        name="Total Clean Time",
        prop=PROP_TOTAL_CLEAN_TIME,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-check-outline",
    ),
    DreameSensorEntityDescription(
        key="total_clean_area",
        name="Total Cleaned Area",
        prop=PROP_TOTAL_CLEAN_AREA,
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:map-check-outline",
    ),
    DreameSensorEntityDescription(
        key="error",
        name="Error",
        prop=PROP_FAULTS,
        value_map=ERROR_MAP,
        icon="mdi:alert-circle-outline",
    ),
    DreameSensorEntityDescription(
        key="main_brush_life",
        name="Main Brush Life",
        prop=PROP_MAIN_BRUSH_LIFE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:brush",
    ),
    DreameSensorEntityDescription(
        key="side_brush_life",
        name="Side Brush Life",
        prop=PROP_SIDE_BRUSH_LIFE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:brush-variant",
    ),
    DreameSensorEntityDescription(
        key="filter_life",
        name="Filter Life",
        prop=PROP_FILTER_LIFE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:air-filter",
    ),
    DreameSensorEntityDescription(
        key="sensor_dirty",
        name="Sensor Cleanliness",
        prop=PROP_SENSOR_DIRTY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:radar",
    ),
    DreameSensorEntityDescription(
        key="mop_pad_life",
        name="Mop Pad Life",
        prop=PROP_MOP_PAD_LIFE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-sync",
    ),
    DreameSensorEntityDescription(
        key="shortcuts",
        name="Available Shortcuts",
        prop=PROP_SHORTCUTS,
        icon="mdi:lightning-bolt",
        transform=lambda v: _decode_shortcuts(v),
    ),
)


def _decode_shortcuts(raw: str) -> str:
    """Decode base64 shortcut names from JSON string."""
    try:
        shortcuts = json.loads(raw)
        names = []
        for s in shortcuts:
            try:
                name = base64.b64decode(s["name"] + "==").decode("utf-8").strip()
            except Exception:
                name = s.get("name", "Unknown")
            names.append(f"{name} (ID:{s['id']})")
        return ", ".join(names)
    except Exception:
        return raw


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.title

    async_add_entities(
        DreameSensorEntity(coordinator, description, device_id, device_name)
        for description in SENSOR_DESCRIPTIONS
        if description.prop in coordinator.data
    )


class DreameSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Dreame sensor."""

    entity_description: DreameSensorEntityDescription

    def __init__(self, coordinator, description, device_id, device_name):
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device_name} {description.name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Dreame",
            "model": "L10s Ultra Gen 2",
        }

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self.entity_description.prop)
        if raw is None:
            return None
        if self.entity_description.transform:
            return self.entity_description.transform(raw)
        if self.entity_description.value_map:
            return self.entity_description.value_map.get(raw, str(raw))
        return raw
