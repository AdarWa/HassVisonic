"""The Visonic Alarm Integration"""
from homeassistant.config_entries import ConfigEntry # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.helpers.typing import ConfigType # type: ignore
from .api import API
from .const import PLATFORMS, DOMAIN
import asyncio
import threading
import logging
from homeassistant.helpers.entity_registry import async_get # type: ignore
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval # type: ignore

_LOGGER = logging.getLogger(__name__)

async def updateHandler(call):
    try:
        _LOGGER.debug("Updating visonic panel from request.")
        
        await _api.fetchDevicesAsync()
        for entity in _api.entities:
            if type(entity).__name__ == "VisonicPanel":
                threading.Thread(target=entity.updateStatus).start()
            else:
                entity.update()
            entity.schedule_update_ha_state()
    except Exception as e:
        _LOGGER.fatal(type(e).__name__ + "occured while updating panel. " + str(e))

async def triggerSirenHandler(call):
    try:
        await _api.triggerAsync()
    except Exception as e:
        _LOGGER.fatal(type(e).__name__ + "occured while updating panel. " + str(e))

async def muteSirenHandler(call):
    try:
        await _api.muteAsync()
    except Exception as e:
        _LOGGER.fatal(type(e).__name__ + "occured while updating panel. " + str(e))

async def updateLater():
    loop = asyncio.get_event_loop()
    for i in range(5):
        loop.call_later(i,loop.create_task, updateHandler(None))

async def updateRepeatHandler(call):
    loop = asyncio.get_event_loop()
    loop.call_later(5,loop.create_task, updateLater())
    
async def continue_action_cb(call):
    if _api.continue_func is not None:
        await asyncio.to_thread(_api.continue_func)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Placeholder for YAML setup. Not used."""
    global _hass
    _hass = hass
    _LOGGER.debug("Setting up visonic alarm integration")
    hass.services.async_register(DOMAIN, "update", updateHandler)
    hass.services.async_register(DOMAIN, "trigger_siren", triggerSirenHandler)
    hass.services.async_register(DOMAIN, "mute_siren", muteSirenHandler)
    hass.services.async_register(DOMAIN, "continue_action", continue_action_cb)
    hass.bus.async_listen("alarm_change_event", updateRepeatHandler)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    global _api
    """Set up the integration from a config entry."""
    # Store config entry data
    try:
        hass.data.setdefault(DOMAIN, {})
        _api = API(entry.data.get("hostname", "visonic.tycomonitor.com"))
        hass.data[DOMAIN][entry.entry_id] = _api
        # forward config entry data to the API
        _api.secrets = {
            "email": entry.data.get("email"),
            "password": entry.data.get("password"),
            "app_id": entry.data.get("app_id"),
            "user_code": entry.data.get("user_code"),
            "panel_serial": entry.data.get("panel_serial")
        }
        await _api.initAsync()
        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        async_track_time_interval(hass, updateHandler, timedelta(minutes=1))

        return True
    except Exception as e:
        _LOGGER.fatal(type(e).__name__ + " occured while setting up the entry. " + str(e))
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok