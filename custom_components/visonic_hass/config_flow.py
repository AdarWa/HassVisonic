import uuid
from homeassistant import config_entries # type: ignore
import voluptuous as vol # type: ignore
from homeassistant.core import callback # type: ignore
from .api import API
import logging
from .const import DOMAIN
import hashlib

DATA_SCHEMA = vol.Schema({
    vol.Required("hostname"): str,
    vol.Required("email"): str,
    vol.Required("password"): str,
    vol.Required("user_code"): str,
    vol.Required("panel_serial"): str,
    vol.Required("accepted_codes"): str,
    vol.Optional("uart_to_tcp", default=False): bool,
})



class VisonicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._data = {
                "hostname": user_input["hostname"],
                "email": user_input["email"],
                "password": user_input["password"],
                "user_code": user_input["user_code"],
                "panel_serial": user_input["panel_serial"],
                "uart_to_tcp": user_input["uart_to_tcp"],
                "accepted_codes": [hashlib.sha256(code.encode()).hexdigest() for code in user_input["accepted_codes"].replace(" ", "").split(",")],
                "app_id": "aa63eef7-a5a0-4490-8b79-65e840235342",
            }
            try:
                _api = API(user_input["hostname"])
                _api.secrets = self._data
                await _api.initAsync()
            except Exception as e:
                logging.getLogger(__name__).error(f"Error connecting to Visonic API: {e}")
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="user",
                    data_schema=DATA_SCHEMA,
                    errors=errors,
                )

            if self._data.get("uart_to_tcp"):
                return await self.async_step_uart()

            return self.async_create_entry(title=user_input["hostname"], data=self._data)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_uart(self, user_input=None):
        errors = {}
        UART_SCHEMA = vol.Schema({
            vol.Required("uart_ip"): str,
            vol.Required("uart_port"): int,
            vol.Optional("rapid_sensor_id"): int
        })
        if user_input is not None:
            self._data["uart_ip"] = user_input["uart_ip"]
            self._data["uart_port"] = user_input["uart_port"]
            self._data["rapid_sensor_id"] = user_input.get("rapid_sensor_id")
            return self.async_create_entry(
                title=self._data.get("hostname", "Visonic"),
                data=self._data,
            )
        return self.async_show_form(
            step_id="uart",
            data_schema=UART_SCHEMA,
            errors=errors,
        )
