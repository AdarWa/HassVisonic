from homeassistant.components.binary_sensor import BinarySensorEntity # type: ignore
import logging
from .const import DOMAIN
from .device import Device,DeviceType

logger = logging.getLogger(DOMAIN)
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    global _api,sensors
    _api = hass.data[DOMAIN].get(entry.entry_id)
    if not _api:
        logger.fatal("API is none")
        return
    sensors = []
    for device in _api.devices:
        if device.device_type == DeviceType.MAGNETIC:
            sensors.append(MagneticSensor(device))
        elif device.device_type == DeviceType.FLOOD:
            sensors.append(FloodSensor(device))
    
    async_add_entities(sensors, True)
    
def getDevice(id):
    for device in _api.devices:
        if device.id == id:
            return device
    
    logger.fatal(f"Device {id} not found.")
    return None

class MagneticSensor(BinarySensorEntity):

    def __init__(self,device):
        _api.entities.append(self)
        self._device = device
        self._id = device.id
        self._name = device.name
        self._state = device.isOpen()
        self.entity_id = "binary_sensor.visonic_"+device.id
        self._attr_should_poll = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def device_class(self):
        return "door"
    
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
        self._state = temp.isOpen()        

class FloodSensor(BinarySensorEntity):

    def __init__(self,device):
        _api.entities.append(self)
        self._device = device
        self._id = device.id
        self._name = device.name
        self._state = device.isOpen()
        self.entity_id = "binary_sensor.visonic_"+device.id
        self._attr_should_poll = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def device_class(self):
        return "moisture"
    
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
        self._state = temp.isWet()      
