import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .day_processing import extract_day_points, latest_day_point
from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .utils import before, today, build_reading_date_attributes

_LOGGER = logging.getLogger(__name__)


class WNSMDayReadingDateSensor(SensorEntity):
    """Expose DAY reading_date as dedicated timestamp sensor."""

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
            _, self._attr_extra_state_attributes = build_reading_date_attributes(
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
                points = sorted(
                    extract_day_points(messwerte), key=lambda point: point.source_timestamp, reverse=True
                )
                self._attr_extra_state_attributes["messwert1"] = points[0].value_kwh if len(points) > 0 else None
                self._attr_extra_state_attributes["messwert2"] = points[1].value_kwh if len(points) > 1 else None

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
