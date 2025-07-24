from homeassistant.components.sensor import SensorEntity,SensorDeviceClass # type: ignore
import logging
from .const import DOMAIN
from .device import Device,DeviceType
from .usr_sensor import AlarmSensor, setup_alarm_sensor_platform

logger = logging.getLogger(__name__)
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    global _api,sensors
    _api = hass.data[DOMAIN].get(entry.entry_id)
    if not _api:
        logger.fatal("API is none")
        return
    sensors = []
    if entry.data.get("uart_to_tcp", False):
        alarm_sensor = AlarmSensor()
        sensors.append(alarm_sensor)
        setup_alarm_sensor_platform(hass, alarm_sensor, entry.data.get("uart_ip"), entry.data.get("uart_port"), entry.data.get("rapid_sensor_id"))
    for device in _api.devices:
        if device.device_type not in [DeviceType.MAGNETIC, DeviceType.PANEL, DeviceType.REPEATER, DeviceType.IGNORE, DeviceType.FLOOD]:
            sensors.append(GenericDevice(device))
    
    async_add_entities(sensors, True)
    
def getDevice(id):
    for device in _api.devices:
        if device.id == id:
            return device
    
    logger.fatal(f"Device {id} not found.")
    return None

class GenericDevice(SensorEntity):
    
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Problem", "Idle", "Tamper"]

    def __init__(self,device):
        _api.entities.append(self)
        self._device = device
        self._id = device.id
        self._name = device.name
        # self._state = device.isOpen()
        self.entity_id = "sensor.visonic_"+device.id
        self._attr_should_poll = False

    @property
    def name(self):
        return self._name
    
    @property
    def extra_state_attributes(self):
        return {
            "Device Type": self._device.device_type,
            "Bypass": self._device.bypass,
            "Warnings": self._device.warnings,
            "Id": self._device.id,
            "Visonic Id": self._device.visonic_id,
                }
        
    @property
    def native_value(self):
        isTamper = len(self._device.warnings) > 0
        for warning in self._device.warnings:
            if not warning.startswith("TAMPER"):
                isTamper = False
        state = "Idle"
        if isTamper:
            state = "Tamper"
        elif len(self._device.warnings) > 0:
            state = "Problem"
        return state
    
    @property
    def unique_id(self):
        return "visonic_" + self._device.id

    def update(self):
        temp = getDevice(self._id)
        if temp is None:
            self._attr_available = False
            return
        self._attr_available = True
        self._device = temp
        self._name = temp.name
