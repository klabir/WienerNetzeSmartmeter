import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .day_processing import latest_day_point
from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .utils import before, today, build_reading_date_attributes

_LOGGER = logging.getLogger(__name__)


class WNSMDayReadingDateSensor(SensorEntity):
    """Expose DAY reading_date as dedicated timestamp sensor."""

    def __init__(
        self,
        username: str,
        password: str,
        zaehlpunkt: str,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt

        self._attr_name = f"{zaehlpunkt} Day Reading Date"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_native_value: datetime | None = None
        self._attr_extra_state_attributes = {}

        self._available: bool = True
        self._attr_suggested_update_interval = scan_interval

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.zaehlpunkt}_day_reading_date"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    async def async_update(self):
        """Update sensor."""
        try:
            smartmeter = Smartmeter(username=self.username, password=self.password)
            async_smartmeter = AsyncSmartmeter(self.hass, smartmeter)
            await async_smartmeter.login()
            zaehlpunkt_response = await async_smartmeter.get_zaehlpunkt(self.zaehlpunkt)
            reading_dates, self._attr_extra_state_attributes = build_reading_date_attributes(
                zaehlpunkt_response
            )

            if async_smartmeter.is_active(zaehlpunkt_response):
                start = before(today(), 1)
                end = today()
                messwerte = await async_smartmeter.get_historic_data(
                    self.zaehlpunkt,
                    start,
                    end,
                    ValueType.DAY,
                )
                latest = latest_day_point(messwerte)
                if latest is not None:
                    self._attr_native_value = latest.source_timestamp
                    self._attr_extra_state_attributes["reading_date"] = latest.reading_date
                else:
                    _LOGGER.debug("No usable DAY reading_date returned for %s", self.zaehlpunkt)

            self._available = True
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving day reading date from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving day reading date from smart meter api - Error: %s", e)
