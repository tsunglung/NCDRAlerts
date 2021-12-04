"""Common NCDR Alerts Data class used by both sensor and entity."""
import logging
import json

from aiohttp.hdrs import USER_AGENT
import requests
import http

from .const import (
    ALERTS_TYPE,
    ALERTS_AREA,
    BASE_URL,
    HA_USER_AGENT,
    REQUEST_TIMEOUT
)

_LOGGER = logging.getLogger(__name__)


class NcdrAlertData:
    """Get alerts data from NCDR. """

    def __init__(self, hass, alerts_type):
        """Initialize the data object."""
        self._hass = hass

        # Holds the current data from the NCDR
        self.data = []
        self.alerts = None
        self.alert_name = None
        self.alerts_type = alerts_type
        self.alert_type = None
        self.uri = None

    async def async_update_alerts(self):
        """Async wrapper for getting alert data."""
        return await self._hass.async_add_executor_job(self._update_alerts)

    def get_data_for_alert(self, alert_type, data):
        """ return data """
        self._update_alerts()
        return self.data

    def _parser_json(self, alert_type, text):
        """ parser json """
        the_dict = json.loads(text)
        data = {}
        value = {}
        if "entry" in the_dict:
            if isinstance(the_dict["entry"], dict):
                value["updated"] = the_dict["updated"]
                value["title"] = the_dict["entry"]["title"]
                value["author"] = the_dict["entry"]["author"]["name"]
                value["text"] = the_dict["entry"]["summary"].get("#text", None)
            else:
                value["updated"] = the_dict["updated"]
                value["title"] = the_dict["entry"][-1]["title"]
                value["author"] = the_dict["entry"][-1]["author"]["name"]
                value["text"] = the_dict["entry"][-1]["summary"].get("#text", None)
        data[alert_type] = value

        return data

    def _update_alerts(self):
        """Return the alert json."""
        headers = {USER_AGENT: HA_USER_AGENT}

        for i in self.alerts_type:
            if i in ALERTS_AREA:
                self.uri = "{}County={}".format(BASE_URL, i)
            else:
                self.uri = "{}AlertType={}".format(BASE_URL, i)

            req = None
            try:
                req = requests.post(
                    self.uri,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT)

            except requests.exceptions.RequestException as err:
                _LOGGER.error("Failed fetching data for %s", ALERTS_TYPE[i])

            if req and req.status_code == http.HTTPStatus.OK:
                self.data.append(self._parser_json(i, req.text))
                if self.alert_name is None:
                    self.alert_name = "ncdr"
                self.alert_name = self.alert_name + "-" + i
            else:
                _LOGGER.error("Received error from NCDR")

        return self.alert_name

    async def async_update(self):
        """Async wrapper for update method."""
        return await self._hass.async_add_executor_job(self._update)

    def _update(self):
        """Get the latest data from NCDR."""
        if self.alerts_type is None:
            _LOGGER.error("No NCDR held, check logs for problems")
            return

        try:
            alerts = self.get_data_for_alert(
                self.alert_type, self.data
            )
            self.alerts = alerts
        except (ValueError) as err:
            _LOGGER.error("Check NCDR connection: %s", err.args)
            self.alert_name = None
