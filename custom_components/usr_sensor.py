from __future__ import annotations

from homeassistant.components.sensor import ( # type: ignore
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.core import HomeAssistant, callback # type: ignore
from homeassistant.helpers.entity_platform import AddEntitiesCallback # type: ignore
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType # type: ignore
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send # type: ignore
import socket
import threading
import logging
from .parser import parseData, parseDataBlock  # Adjust path as needed

_LOGGER = logging.getLogger(__name__)

SIGNAL_ALARM_UPDATE = "alarm_update_signal"



def setup_alarm_sensor_platform(
    hass: HomeAssistant,
    sensor: AlarmSensor,
    host: str = "",
    port: int = 0,
    id_: int | None = None
) -> None:
    """Set up the alarm sensor platform as part of a custom integration."""

    def socket_loop():
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, port))
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        data_block = parseData(data)
                        state_tuple = parseDataBlock(data_block, id_)
                        if state_tuple:
                            state, rapid = state_tuple
                            if state:
                                sensor.update_state(state)
                            if rapid is not None:
                                hass.states.set("visonic.rapid_sensor", rapid)
                                hass.bus.fire(SIGNAL_ALARM_UPDATE, {})
            except Exception as e:
                _LOGGER.exception("Socket loop crashed: %s", e)

    threading.Thread(target=socket_loop, daemon=True).start()


class AlarmSensor(SensorEntity):
    """Representation of an alarm state sensor."""

    _attr_name = "USR Alarm State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_should_poll = False
    _attr_options = [
        "Entry Delay", "Armed Home", "Armed Away", "Arming Home", "Arming Away",
        "Disarmed - Downloading", "Disarmed - User Test", "Disarmed"
    ]

    def __init__(self) -> None:
        self._attr_native_value = None

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to Home Assistant."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_ALARM_UPDATE, self._handle_update)
        )

    @callback
    def _handle_update(self, state: str) -> None:
        """Handle signal update."""
        self._attr_native_value = state
        self.schedule_update_ha_state()

    def update_state(self, state: str) -> None:
        """External state update from socket thread."""
        dispatcher_send(self.hass, SIGNAL_ALARM_UPDATE, state)
