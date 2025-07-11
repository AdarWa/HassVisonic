from enum import Enum
import hashlib

class DeviceType(Enum):
    PANEL="Visonic Panel"
    MOTION="Motion Sensor" #TODO
    FLOOD="Flood Sensor" #TODO
    REPEATER="Repeater"
    SMOKE="Smoke Detector"
    MAGNETIC="Magnetic Sensor"
    CURTAIN="Curtain Sensor" #TODO
    SHOCK="Shock Sensor" #TODO
    CAMERA="Motion Camera" #TODO
    KEYPAD="Keypad"
    IGNORE="IGNORE"

types = {
    'VISONIC_PANEL': DeviceType.PANEL,
    'FLAT_PIR_SMART': DeviceType.MOTION,
    'FLOOD': DeviceType.FLOOD,
    'BASIC_REPEATER': DeviceType.REPEATER,
    'PGM_ON_PANEL': DeviceType.IGNORE,
    'S_SMOKE_AND_HEAT': DeviceType.SMOKE,
    'CONTACT_AUX': DeviceType.MAGNETIC,
    'CURTAIN': DeviceType.CURTAIN,
    'HW_ZONE_CONNECTED_DIRECTLY_TO_THE_PANEL': None, #External Siren
    'GENERIC_PROXY_TAG': DeviceType.IGNORE,
    'SHOCK_CONTACT_AUX_ANTIMASK': DeviceType.SHOCK,
    'MOTION_CAMERA': DeviceType.CAMERA,
    'PROXIMITY_KEYPAD': DeviceType.KEYPAD,
    'POWER_LINK': DeviceType.IGNORE
}

class Device:
    name = ""
    device_type = None
    bypass = False
    hasName = True
    visonic_id = None
    
    
    def __init__(self, device_type, name, bypass, warnings, _id):
        self.visonic_id = _id
        if name == "":
            self.name = device_type if types[device_type] is None else types[device_type].value
            self.hasName = False
        else: 
            self.name = name
        self.device_type = types[device_type]
        self.bypass = bypass
        self._warnings = warnings
    
    @property
    def id(self):
        toHash = self.name if self.hasName else self.visonic_id
        digest = hashlib.md5(toHash.encode()).hexdigest()
        return digest[:5]+ digest[-5:]
    
    @property
    def warnings(self):
        if self._warnings is None:
            return []
        return [x["type"] for x in self._warnings]
    
    def isOpen(self):
        if self.device_type != DeviceType.MAGNETIC:
            return None
        
        return "OPENED" in self.warnings
    
    def isWet(self):
        if self.device_type != DeviceType.FLOOD:
            return None
        
        cnt = 0
        for warning in self.warnings:
            if warning.startswith("TAMPER"):
               continue
            cnt += 1
        return cnt > 0 
    
    def __repr__(self):
        dtype = "None"
        if self.device_type is not None:
            dtype = self.device_type.value
        return self.name + ", " + dtype + ", bypass: " + str(self.bypass) + ", warnings: " + str(self.warnings)
    
    def __str__(self):
        return self.__repr__()
    
    