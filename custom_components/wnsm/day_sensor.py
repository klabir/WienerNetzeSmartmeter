import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .utils import before, today

_LOGGER = logging.getLogger(__name__)


class WNSMDailySensor(SensorEntity):
    """Representation of a daily consumption sensor."""

    def __init__(self, username: str, password: str, zaehlpunkt: str) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt

        self._attr_native_value: int | float | None = None
        self._attr_name = f"{zaehlpunkt} Day"
        self._attr_icon = "mdi:calendar-today"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_extra_state_attributes = {}

        self._available: bool = True
        self._updatets: str | None = None

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

    def _daily_value(self, messwerte: dict[str, Any]) -> tuple[float | None, str | None]:
        values = messwerte.get("values", [])
        if not values:
            return None, None
        values_with_ts = [
            value
            for value in values
            if value.get("zeitBis") is not None or value.get("zeitVon") is not None
        ]
        if not values_with_ts:
            return None, None
        latest = max(
            values_with_ts,
            key=lambda value: dt_util.parse_datetime(value.get("zeitBis") or value.get("zeitVon"))
            or datetime.min,
        )
        wert = latest.get("messwert")
        if wert is None:
            return None, None
        unit = messwerte.get("unitOfMeasurement")
        if unit is None:
            return None, None
        unit = unit.upper()
        if unit == "WH":
            factor = 1e-3
        elif unit == "KWH":
            factor = 1.0
        else:
            _LOGGER.warning("Unknown unit for daily consumption: %s", unit)
            return None, None

        latest_zeitbis = dt_util.parse_datetime(latest.get("zeitBis") or latest.get("zeitVon"))
        reading_date = (
            (latest_zeitbis - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            if latest_zeitbis is not None
            else None
        )
        return wert * factor, reading_date

    async def async_update(self):
        """Update sensor."""
        try:
            smartmeter = Smartmeter(username=self.username, password=self.password)
            async_smartmeter = AsyncSmartmeter(self.hass, smartmeter)
            await async_smartmeter.login()
            zaehlpunkt_response = await async_smartmeter.get_zaehlpunkt(self.zaehlpunkt)
            reading_dates = [before(today(), 1), before(today(), 2)]
            self._attr_extra_state_attributes = {
                **zaehlpunkt_response,
                "reading_dates": [reading_date.isoformat() for reading_date in reading_dates],
                "reading_date": None,
                "yesterday": reading_dates[0].isoformat(),
                "day_before_yesterday": reading_dates[1].isoformat(),
            }
            if async_smartmeter.is_active(zaehlpunkt_response):
                start = before(today(), 1)
                end = today()
                messwerte = await async_smartmeter.get_historic_data(
                    self.zaehlpunkt,
                    start,
                    end,
                    ValueType.DAY,
                )
                daily_value, reading_date = self._daily_value(messwerte)
                if daily_value is not None:
                    self._attr_native_value = daily_value
                if reading_date is not None:
                    self._attr_extra_state_attributes["reading_date"] = reading_date
            self._available = True
            self._updatets = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving data from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving data from smart meter api - Error: %s", e)
