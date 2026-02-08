import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .AsyncSmartmeter import AsyncSmartmeter
from .api import Smartmeter
from .api.constants import ValueType
from .utils import before, today

_LOGGER = logging.getLogger(__name__)


class WNSMDailySensor(SensorEntity):
    """Representation of a daily consumption sensor."""

    def __init__(
        self,
        username: str,
        password: str,
        zaehlpunkt: str,
        scan_interval: timedelta | None = None,
    ) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt
        self._scan_interval = scan_interval
        self._unsub_timer = None

        self._attr_native_value: int | float | None = None
        self._attr_extra_state_attributes = {"raw_api": {}}
        self._attr_name = f"{zaehlpunkt} Day"
        self._attr_icon = "mdi:calendar-today"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

        self._available: bool = True
        self._updatets: str | None = None
        self._attr_should_poll = self._scan_interval is None

    async def async_added_to_hass(self) -> None:
        if self._scan_interval:
            self._unsub_timer = async_track_time_interval(
                self.hass,
                self._handle_scheduled_update,
                self._scan_interval,
            )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    async def _handle_scheduled_update(self, now) -> None:
        await self.async_update()
        self.async_write_ha_state()

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

    def _daily_value(self, bewegungsdaten: dict[str, Any]) -> float | None:
        values = bewegungsdaten.get("values", [])
        if not values:
            return None
        values_with_ts = [
            value
            for value in values
            if value.get("zeitBis") is not None or value.get("zeitVon") is not None
        ]
        if not values_with_ts:
            return None
        latest = max(
            values_with_ts,
            key=lambda value: dt_util.parse_datetime(value.get("zeitBis") or value.get("zeitVon"))
            or datetime.min,
        )
        wert = latest.get("messwert")
        if wert is None:
            return None
        unit = bewegungsdaten.get("unitOfMeasurement")
        if unit is None:
            return None
        unit = unit.upper()
        if unit == "WH":
            factor = 1e-3
        elif unit == "KWH":
            factor = 1.0
        else:
            _LOGGER.warning("Unknown unit for daily consumption: %s", unit)
            return None
        return wert * factor

    async def async_update(self):
        """Update sensor."""
        try:
            smartmeter = Smartmeter(username=self.username, password=self.password)
            async_smartmeter = AsyncSmartmeter(self.hass, smartmeter)
            await async_smartmeter.login()
            zaehlpunkt_response, zaehlpunkt_raw = await async_smartmeter.get_zaehlpunkt_with_raw(self.zaehlpunkt)
            self._attr_extra_state_attributes = {
                "raw_api": {
                    "zaehlpunkt": zaehlpunkt_raw,
                },
                "reading_date": None,
                "yesterday": None,
                "day_before_yesterday": None,
            }
            self._attr_extra_state_attributes.update(zaehlpunkt_response)

            if async_smartmeter.is_active(zaehlpunkt_response):
                reading_dates = [before(today(), 1), before(today(), 2)]
                self._attr_extra_state_attributes["reading_dates"] = [
                    reading_date.isoformat() for reading_date in reading_dates
                ]
                self._attr_extra_state_attributes["reading_date"] = reading_dates[0].isoformat()
                self._attr_extra_state_attributes["yesterday"] = reading_dates[0].isoformat()
                self._attr_extra_state_attributes["day_before_yesterday"] = reading_dates[1].isoformat()
                start = before(today(), 1)
                end = today()
                messwerte, messwerte_raw = await async_smartmeter.get_historic_data(
                    self.zaehlpunkt,
                    start,
                    end,
                    ValueType.DAY,
                    include_raw=True,
                )
                self._attr_extra_state_attributes["raw_api"]["messwerte_day"] = messwerte_raw
                daily_value = self._daily_value(messwerte)
                if daily_value is not None:
                    self._attr_native_value = daily_value
            self._available = True
            self._updatets = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        except TimeoutError as e:
            self._available = False
            _LOGGER.warning("Error retrieving data from smart meter api - Timeout: %s", e)
        except RuntimeError as e:
            self._available = False
            _LOGGER.exception("Error retrieving data from smart meter api - Error: %s", e)
