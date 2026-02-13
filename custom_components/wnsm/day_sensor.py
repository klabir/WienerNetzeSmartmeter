import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .day_processing import latest_day_point
from .day_statistics_importer import DayStatisticsImporter
from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .utils import before, today, build_reading_date_attributes

_LOGGER = logging.getLogger(__name__)


class WNSMDailySensor(SensorEntity):
    """Representation of a daily consumption sensor."""

    def __init__(
        self,
        async_smartmeter: AsyncSmartmeter | None,
        username: str,
        password: str,
        zaehlpunkt: str,
        enable_day_statistics_import: bool = False,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt
        self._async_smartmeter = async_smartmeter
        self._enable_day_statistics_import = enable_day_statistics_import

        self._attr_native_value: int | float | None = None
        self._attr_name = f"{zaehlpunkt} Day"
        self._attr_icon = "mdi:calendar-today"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_extra_state_attributes = {}

        self._available: bool = True
        self._updatets: str | None = None
        self._attr_suggested_update_interval = scan_interval

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._attr_name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.zaehlpunkt}_day"

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
                    self._attr_native_value = latest.value_kwh
                    self._attr_extra_state_attributes["reading_date"] = latest.reading_date
                else:
                    _LOGGER.debug("No usable DAY values returned for %s", self.zaehlpunkt)

                if self._enable_day_statistics_import:
                    importer = DayStatisticsImporter(self.hass, async_smartmeter, self.zaehlpunkt)
                    await importer.async_import(start, end)
            self._available = True
            self._updatets = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving data from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving data from smart meter api - Error: %s", e)
