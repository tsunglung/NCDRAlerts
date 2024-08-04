"""Support for NCDR alerts service."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTRIBUTION,
    ATTR_LAST_UPDATE,
    ATTR_TITLE,
    ATTR_AUTHOR,
    ATTR_TEXT,
    DOMAIN,
    NCDR_ALERTS_COORDINATOR,
    NCDR_ALERTS_DATA,
    NCDR_ALERTS_NAME,
    ALERTS_TYPE
)
import logging
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities
) -> None:
    """Set up the NCDR alert sensor platform."""
    hass_data = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            NcdrAlertSensor(entry.data, hass_data, alert_type)
            for alert_type in hass_data[NCDR_ALERTS_NAME]
        ],
        False,
    )


class NcdrAlertSensor(SensorEntity):
    """Implementation of a NCDR alert sensor."""

    def __init__(self, entry_data, hass_data, alert_type):
        """Initialize the sensor."""
        self._data = hass_data[NCDR_ALERTS_DATA]
        self._coordinator = hass_data[NCDR_ALERTS_COORDINATOR]

        self._name = f"{ALERTS_TYPE[alert_type]}"
        self._unique_id = f"{ALERTS_TYPE[alert_type]} {alert_type}"

        self.ncdr_alerts_alert_type = alert_type
        self.ncdr_alerts_alert_name = None
        self.ncdr_alerts_now = None
        self._last_update = None
        self._title = None
        self._author = None
        self._text = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        for i in self.ncdr_alerts_now:
            for j, k in i.items():
                if self.ncdr_alerts_alert_type == j:
                    self._last_update = k.get("updated", "")
                    self._title = k.get("title", "")
                    self._author = k.get("author", "")
                    self._text = k.get("text", "")

        return self._last_update

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def icon(self):
        """Return the icon for the entity card."""
        return "mdi:alert"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_LAST_UPDATE: self._last_update if self.ncdr_alerts_now else None,
            ATTR_TITLE: self._title if self.ncdr_alerts_now else None,
            ATTR_AUTHOR: self._author if self.ncdr_alerts_now else None,
            ATTR_TEXT: self._text if self.ncdr_alerts_now else None
        }

    async def async_added_to_hass(self) -> None:
        """Set up a listener and load data."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._update_callback)
        )
        self._update_callback()

    async def async_update(self):
        """Schedule a custom update via the common entity update service."""
        await self._coordinator.async_request_refresh()

    @callback
    def _update_callback(self) -> None:
        """Load data from integration."""
        self.ncdr_alerts_now = self._data.alerts
        self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Entities do not individually poll."""
        return False

    @property
    def available(self):
        """Return if state is available."""
        return self.ncdr_alerts_now is not None
