from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity,AlarmControlPanelState,AlarmControlPanelEntityFeature,CodeFormat # type: ignore
from homeassistant.helpers.event import async_track_state_change_event # type: ignore
from homeassistant.core import callback # type: ignore
from .const import DOMAIN
import hashlib
import logging
from threading import Timer

class VisonicPanel(AlarmControlPanelEntity):
    _attr_name = "Visonic Panel"
    _attr_code_format = CodeFormat.NUMBER
    _attr_code_arm_required = True
    _attr_unique_id = "alarm_control_panel.visonic_panel"
    current_state = None
    armed_vacation = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_VACATION
        | AlarmControlPanelEntityFeature.TRIGGER
    )
    
    async def async_update(self):
        obj = self.hass.states.get("alarm.changeable_state")
        if obj is not None:
            self.current_state = obj.state
            if self.current_state != "Armed Away":
                self.armed_vacation = False
        else:
            self.current_state = "Unknown"
    
    @callback
    async def callUpdate(self, e):
        await self.async_update()
        
    async def registerListner(self,event):
        async_track_state_change_event(self.hass, "alarm.changeable_state", self.callUpdate)
              
    
    def __init__(self, _hass, _api,_secrets):
        self.secrets = _secrets
        self.api = _api
        self.hass = _hass
        self.logger = logging.getLogger(DOMAIN)
        _hass.bus.async_listen_once("homeassistant_started", self.registerListner)
        Timer(20, self.updateStatus).start()
    
    def fetchStatus(self):
        fetched = self.api.fetchState()
        if fetched is None:
            return
        state = fetched["state"]
        if state == "DISARM":
            self.current_state = "Disarmed"
        elif state == "EXIT":
            self.current_state = "Arming Home"
        elif state == "HOME":
            self.current_state = "Armed Home"
        elif state == "AWAY":
            self.current_state = "Armed Away"
        elif state == "ENTRY_DELAY":
            self.current_state = "Entry Delay"
        self.hass.states.set("alarm.changeable_state", self.current_state)
        self.hass.states.set("alarm.ready", fetched["ready"])
    
    def updateStatus(self):
        self.fetchStatus()
        # self.schedule_update_ha_state()
    
    
    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the device."""
        if self.current_state == "Disarmed":
            return AlarmControlPanelState.DISARMED
        if self.current_state == "Armed Away":
            if self.armed_vacation:
                return AlarmControlPanelState.ARMED_VACATION
            return AlarmControlPanelState.ARMED_AWAY
        if self.current_state == "Armed Home":
            return AlarmControlPanelState.ARMED_HOME
        if self.current_state == "Entry Delay":
            return AlarmControlPanelState.PENDING
        if self.current_state == "Arming Home" or self.current_state == "Arming Away":
            return AlarmControlPanelState.ARMING
        return None
    
    
    

    def alarm_disarm(self, code) -> None:
        if hashlib.sha256(str(code).encode()).hexdigest() in self.secrets:
            self.hass.bus.fire("visonic.disarm")
            def func():
                self.api.arm("DISARM")
                for i in range(1,10):
                    Timer(i,self.updateStatus).start()
                self.armed_vacation = False
            self.api.continue_func = func
        else:
            self.hass.bus.fire("visonic.invalid_code")
            
    def alarm_arm_home(self, code) -> None:
        if hashlib.sha256(str(code).encode()).hexdigest() in self.secrets:
            self.hass.bus.fire("visonic.arm_home")
            def func():
                self.api.arm("HOME")
                for i in range(1,10):
                    Timer(i,self.updateStatus).start()
                Timer(62,self.updateStatus).start()
                self.armed_vacation = False
            self.api.continue_func = func
        else:
            self.hass.bus.fire("visonic.invalid_code")
            
    def alarm_arm_away(self, code) -> None:
        if hashlib.sha256(str(code).encode()).hexdigest() in self.secrets:
            self.hass.bus.fire("visonic.arm_away")
            def func():
                self.api.arm("AWAY")
                for i in range(1,10):
                    Timer(i,self.updateStatus).start()
                Timer(62,self.updateStatus).start()
                self.armed_vacation = False
            self.api.continue_func = func
        else:
            self.hass.bus.fire("visonic.invalid_code")
    
    def alarm_arm_vacation(self, code) -> None:
        if hashlib.sha256(str(code).encode()).hexdigest() in self.secrets:
            self.hass.bus.fire("visonic.arm_vacation")
            def func():
                self.api.arm("AWAY")
                for i in range(1,10):
                    Timer(i,self.updateStatus).start()
                Timer(62,self.updateStatus).start()
                self.armed_vacation = True
            self.api.continue_func = func
        else:
            self.hass.bus.fire("visonic.invalid_code")
    
    def alarm_trigger(self, code) -> None:
        self.api.trigger()

async def async_setup_entry(hass, entry, async_add_entities):
    _api = hass.data[DOMAIN].get(entry.entry_id)
    if not _api:
        return
    hashes = entry.data.get("accepted_codes", [])
    panel = VisonicPanel(hass, _api, hashes)
    _api.entities.append(panel)
    async_add_entities([panel])
