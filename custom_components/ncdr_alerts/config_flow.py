"""Config flow for NCDR Alerts integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv

from .const import (
    CONFIG_FLOW_VERSION,
    DOMAIN,
    ALERTS_TYPE
)
from .data import NcdrAlertData

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate that the user input allows us to connect to DataPoint.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    alert_name = data[CONF_NAME]

    ncdr_type_data = NcdrAlertData(hass, alert_name)
    await ncdr_type_data.async_update_alerts()
    if ncdr_type_data.alert_name is None:
        raise CannotConnect()

    return {"alert_type": ncdr_type_data.alert_type}


class NcdrAlertsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NCDR Alerts integration."""

    VERSION = CONFIG_FLOW_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """ get option flow """
        return NcdrAlertsOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            alerts_type = "ncdr"
            for i in user_input[CONF_NAME]:
                alerts_type = alerts_type + "-" + i
            await self.async_set_unique_id(
                f"{alerts_type}"
            )
            self._abort_if_unique_id_configured()

            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                title = ""
                for i in user_input[CONF_NAME]:
                    title = title + " " + ALERTS_TYPE[i]
                return self.async_create_entry(
                    title=title, data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): cv.multi_select(
                    ALERTS_TYPE
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class NcdrAlertsOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Optional(
                    CONF_NAME,
                    default=_get_config_value(
                        self.config_entry, CONF_NAME, "5")
                ): cv.multi_select(ALERTS_TYPE)
            }
        )


def _get_config_value(config_entry, key, default):
    if config_entry.options:
        return config_entry.options.get(key, default)
    return config_entry.data.get(key, default)

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
