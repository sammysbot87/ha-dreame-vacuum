"""Buttons for Dreame Vacuum Cloud — shortcuts and control actions."""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    PROP_SHORTCUTS,
    ACTION_PAUSE,
    ACTION_CHARGE,
    ACTION_STOP,
    SHORTCUT_STATUS_VALUE,
    CLEANING_PROPERTIES_PIID,
    STATUS_PIID,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DreameButtonDescription(ButtonEntityDescription):
    siid: int = 0
    aiid: int = 0
    params: list = field(default_factory=list)


STATIC_BUTTONS: tuple[DreameButtonDescription, ...] = (
    DreameButtonDescription(
        key="pause",
        name="Pause",
        icon="mdi:pause",
        siid=ACTION_PAUSE[0],
        aiid=ACTION_PAUSE[1],
    ),
    DreameButtonDescription(
        key="return_to_dock",
        name="Return to Dock",
        icon="mdi:home-import-outline",
        siid=ACTION_CHARGE[0],
        aiid=ACTION_CHARGE[1],
    ),
    DreameButtonDescription(
        key="stop",
        name="Stop",
        icon="mdi:stop",
        siid=ACTION_STOP[0],
        aiid=ACTION_STOP[1],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame buttons including dynamic shortcut buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    session = data["session"]
    device_id = entry.data[CONF_DEVICE_ID]
    device_name = entry.title

    entities: list[ButtonEntity] = []

    # Static control buttons
    for description in STATIC_BUTTONS:
        entities.append(
            DreameControlButton(coordinator, description, client, session, device_id, device_name)
        )

    # Dynamic shortcut buttons from the shortcuts property
    shortcuts_raw = coordinator.data.get(PROP_SHORTCUTS)
    if shortcuts_raw:
        try:
            shortcuts = json.loads(shortcuts_raw)
            for shortcut in shortcuts:
                try:
                    name = base64.b64decode(shortcut["name"] + "==").decode("utf-8").strip()
                except Exception:
                    name = shortcut.get("name", f"Shortcut {shortcut['id']}")

                entities.append(
                    DreameShortcutButton(
                        coordinator=coordinator,
                        client=client,
                        session=session,
                        device_id=device_id,
                        device_name=device_name,
                        shortcut_id=shortcut["id"],
                        shortcut_name=name,
                    )
                )
        except Exception as err:
            _LOGGER.warning("Failed to parse shortcuts: %s", err)

    async_add_entities(entities)


class DreameControlButton(CoordinatorEntity, ButtonEntity):
    """A button for static control actions (pause, stop, dock)."""

    entity_description: DreameButtonDescription

    def __init__(self, coordinator, description, client, session, device_id, device_name):
        super().__init__(coordinator)
        self.entity_description = description
        self._client = client
        self._session = session
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device_name} {description.name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Dreame",
            "model": "L10s Ultra Gen 2",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        desc = self.entity_description
        await self._client.call_action(self._session, desc.siid, desc.aiid)
        await self.coordinator.async_request_refresh()


class DreameShortcutButton(CoordinatorEntity, ButtonEntity):
    """A button that triggers a specific Dreame shortcut."""

    def __init__(self, coordinator, client, session, device_id, device_name, shortcut_id, shortcut_name):
        super().__init__(coordinator)
        self._client = client
        self._session = session
        self._shortcut_id = shortcut_id
        self._attr_unique_id = f"{device_id}_shortcut_{shortcut_id}"
        self._attr_name = f"{device_name} Shortcut: {shortcut_name}"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Dreame",
            "model": "L10s Ultra Gen 2",
        }

    async def async_press(self) -> None:
        """Trigger the shortcut."""
        _LOGGER.info("Triggering Dreame shortcut ID %s", self._shortcut_id)
        await self._client.call_action(
            self._session,
            siid=4,
            aiid=1,
            params=[
                {"piid": STATUS_PIID, "value": SHORTCUT_STATUS_VALUE},
                {"piid": CLEANING_PROPERTIES_PIID, "value": str(self._shortcut_id)},
            ],
        )
        await self.coordinator.async_request_refresh()
