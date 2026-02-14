import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    ENTITY_ID_FORMAT
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import slugify

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .importer import Importer
from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .utils import before, today, build_reading_date_attributes

_LOGGER = logging.getLogger(__name__)


class WNSMSensor(SensorEntity):
    """Representation of Wiener Smartmeter total energy sensor."""

    def _icon(self) -> str:
        return "mdi:flash"

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

        self._attr_native_value: int | float | None = 0
        self._attr_extra_state_attributes = {"raw_api": {}}
        self._attr_name = zaehlpunkt
        self._attr_icon = self._icon()
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        self.attrs: dict[str, Any] = {}
        self._name: str = zaehlpunkt
        self._available: bool = True
        self._updatets: str | None = None
        self._attr_suggested_update_interval = scan_interval

    @property
    def get_state(self) -> Optional[str]:
        return f"{self._attr_native_value:.3f}"

    @property
    def _id(self):
        return ENTITY_ID_FORMAT.format(slugify(self._name).lower())

    @property
    def icon(self) -> str:
        return self._attr_icon

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.zaehlpunkt

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    def granularity(self) -> ValueType:
        return ValueType.from_str(self._attr_extra_state_attributes.get("granularity", "QUARTER_HOUR"))

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
                # Since update is not exactly at midnight, both yesterday and day before are tried.
                for reading_date in reading_dates:
                    meter_reading = await async_smartmeter.get_meter_reading_from_historic_data(
                        self.zaehlpunkt, reading_date, datetime.now()
                    )
                    if meter_reading is not None:
                        self._attr_native_value = meter_reading
                        self._attr_extra_state_attributes["reading_date"] = reading_date.isoformat()
                        break
                importer = Importer(
                    self.hass,
                    async_smartmeter,
                    self.zaehlpunkt,
                    self.unit_of_measurement,
                    self.granularity(),
                )
                await importer.async_import()
            self._available = True
            self._updatets = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving data from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving data from smart meter api - Error: %s", e)
