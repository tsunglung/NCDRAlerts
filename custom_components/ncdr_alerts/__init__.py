"""The NCDR Alerts integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NCDR_ALERTS_COORDINATOR,
    NCDR_ALERTS_DATA,
    NCDR_ALERTS_NAME,
    PLATFORMS,
    UPDATE_LISTENER,
)
from .data import NcdrAlertData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up a NCDR alerts entry."""

    alert_name = _get_config_value(config_entry, CONF_NAME, "5")

    ncdr_alerts_data = NcdrAlertData(hass, alert_name)
    await ncdr_alerts_data.async_update_alerts()
    if ncdr_alerts_data.alert_name is None:
        raise ConfigEntryNotReady()

    ncdr_alerts_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"NCDR alerts for {alert_name}",
        update_method=ncdr_alerts_data.async_update,
        update_interval=DEFAULT_SCAN_INTERVAL,
    )

    ncdr_alerts_hass_data = hass.data.setdefault(DOMAIN, {})
    ncdr_alerts_hass_data[config_entry.entry_id] = {
        NCDR_ALERTS_DATA: ncdr_alerts_data,
        NCDR_ALERTS_COORDINATOR: ncdr_alerts_coordinator,
        NCDR_ALERTS_NAME: alert_name,
    }

    # Fetch initial data so we have data when entities subscribe
    await ncdr_alerts_coordinator.async_refresh()
    if ncdr_alerts_data.alert_name is None:
        raise ConfigEntryNotReady()

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    update_listener = config_entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][config_entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        update_listener = hass.data[DOMAIN][config_entry.entry_id][UPDATE_LISTENER]
        update_listener()
        hass.data[DOMAIN].pop(config_entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok


def _get_config_value(config_entry, key, default):
    if config_entry.options:
        return config_entry.options.get(key, default)
    return config_entry.data.get(key, default)
