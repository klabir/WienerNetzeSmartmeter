import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .utils import build_reading_date_attributes

_LOGGER = logging.getLogger(__name__)


class WNSMMeterReadReadingDateSensor(SensorEntity):
    """Expose METER_READ reading_date as dedicated timestamp sensor."""

    def __init__(
        self,
        async_smartmeter: AsyncSmartmeter | None,
        username: str,
        password: str,
        zaehlpunkt: str,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt
        self._async_smartmeter = async_smartmeter

        self._attr_name = f"{zaehlpunkt} Meter Read Reading Date"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_native_value: datetime | None = None
        self._attr_extra_state_attributes = {}

        self._available: bool = True
        self._attr_suggested_update_interval = scan_interval

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.zaehlpunkt}_meter_read_reading_date"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    def _get_async_smartmeter(self) -> AsyncSmartmeter:
        """Return shared async smartmeter client, fallback to per-entity one."""
        if self._async_smartmeter is None:
            smartmeter = Smartmeter(username=self.username, password=self.password)
            self._async_smartmeter = AsyncSmartmeter(self.hass, smartmeter)
        return self._async_smartmeter

    async def async_update(self):
        """Update sensor."""
        try:
            async_smartmeter = self._get_async_smartmeter()
            await async_smartmeter.login()
            zaehlpunkt_response = await async_smartmeter.get_zaehlpunkt(self.zaehlpunkt)
            reading_dates, self._attr_extra_state_attributes = build_reading_date_attributes(
                zaehlpunkt_response
            )

            if async_smartmeter.is_active(zaehlpunkt_response):
                for reading_date in reading_dates:
                    meter_reading = await async_smartmeter.get_meter_reading_from_historic_data(
                        self.zaehlpunkt, reading_date, datetime.now()
                    )
                    if meter_reading is not None:
                        self._attr_native_value = reading_date
                        self._attr_extra_state_attributes["reading_date"] = reading_date.isoformat()
                        break
                else:
                    _LOGGER.debug(
                        "No usable METER_READ reading_date returned for %s", self.zaehlpunkt
                    )

            self._available = True
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving meter-read reading date from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving meter-read reading date from smart meter api - Error: %s", e)
