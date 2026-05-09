"""Binary sensors for Dreame Vacuum Cloud."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    PROP_MOP_IN_STATION,
    PROP_MOP_PAD_INSTALLED,
    PROP_CHARGING_STATUS,
    PROP_STATUS,
)


@dataclass(frozen=True)
class DreameBinarySensorDescription(BinarySensorEntityDescription):
    prop: tuple[int, int] = (0, 0)
    on_value: any = 1


BINARY_SENSOR_DESCRIPTIONS: tuple[DreameBinarySensorDescription, ...] = (
    DreameBinarySensorDescription(
        key="mop_in_station",
        name="Mop in Station",
        prop=PROP_MOP_IN_STATION,
        icon="mdi:water-sync",
        on_value=1,
    ),
    DreameBinarySensorDescription(
        key="mop_pad_installed",
        name="Mop Pad Installed",
        prop=PROP_MOP_PAD_INSTALLED,
        icon="mdi:water",
        on_value=1,
    ),
    DreameBinarySensorDescription(
        key="charging",
        name="Charging",
        prop=PROP_CHARGING_STATUS,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        on_value=1,
    ),
    DreameBinarySensorDescription(
        key="cleaning",
        name="Cleaning",
        prop=PROP_STATUS,
        device_class=BinarySensorDeviceClass.RUNNING,
        on_value=None,  # custom logic — any active status
    ),
)

CLEANING_STATUSES = {1, 18, 19, 20, 24, 25}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.title

    async_add_entities(
        DreameBinarySensorEntity(coordinator, description, device_id, device_name)
        for description in BINARY_SENSOR_DESCRIPTIONS
        if description.prop in coordinator.data
    )


class DreameBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Dreame binary sensor."""

    entity_description: DreameBinarySensorDescription

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
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self.entity_description.prop)
        if raw is None:
            return None
        if self.entity_description.key == "cleaning":
            return raw in CLEANING_STATUSES
        return raw == self.entity_description.on_value
