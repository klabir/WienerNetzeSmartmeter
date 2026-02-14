"""Coordinator for Wiener Netze Smartmeter data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .AsyncSmartmeter import AsyncSmartmeter
from .api.constants import ValueType
from .const import CONF_ENABLE_DAY_STATISTICS_IMPORT, CONF_ZAEHLPUNKTE, DEFAULT_SCAN_INTERVAL_MINUTES
from .day_processing import latest_day_point
from .day_statistics_importer import DayStatisticsImporter
from .importer import Importer
from .utils import before, build_reading_date_attributes, today

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ZaehlpunktData:
    """Cached data for one zaehlpunkt."""

    available: bool
    attributes: dict[str, Any]
    meter_read_value: float | None
    meter_reading_date: datetime | None
    day_value_kwh: float | None
    day_reading_date: str | None
    day_source_timestamp: datetime | None


class WnsmDataUpdateCoordinator(DataUpdateCoordinator[dict[str, ZaehlpunktData]]):
    """Fetch shared data for all WNSM sensors in one update cycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_smartmeter: AsyncSmartmeter,
        config: dict[str, Any],
    ) -> None:
        scan_interval_minutes = int(config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES))
        super().__init__(
            hass,
            _LOGGER,
            name=f"wnsm-{entry.entry_id}",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )
        self._config = config
        self._async_smartmeter = async_smartmeter

    async def _async_update_data(self) -> dict[str, ZaehlpunktData]:
        result: dict[str, ZaehlpunktData] = {}
        now = datetime.now()
        for zp in self._config[CONF_ZAEHLPUNKTE]:
            zaehlpunkt = zp["zaehlpunktnummer"]
            try:
                zaehlpunkt_response = await self._async_smartmeter.get_zaehlpunkt(zaehlpunkt)
                reading_dates, attributes = build_reading_date_attributes(zaehlpunkt_response)

                meter_read_value = None
                meter_reading_date = None
                day_value_kwh = None
                day_reading_date = None
                day_source_timestamp = None

                if self._async_smartmeter.is_active(zaehlpunkt_response):
                    for reading_date in reading_dates:
                        meter_reading = await self._async_smartmeter.get_meter_reading_from_historic_data(
                            zaehlpunkt,
                            reading_date,
                            now,
                        )
                        if meter_reading is not None:
                            meter_read_value = meter_reading
                            meter_reading_date = reading_date
                            attributes["reading_date"] = reading_date.isoformat()
                            break

                    start = before(today(), 1)
                    end = today()
                    messwerte = await self._async_smartmeter.get_historic_data(
                        zaehlpunkt,
                        start,
                        end,
                        granularity=ValueType.DAY,
                    )
                    latest = latest_day_point(messwerte)
                    if latest is not None:
                        day_value_kwh = latest.value_kwh
                        day_reading_date = latest.reading_date
                        day_source_timestamp = latest.source_timestamp

                    importer = Importer(
                        self.hass,
                        self._async_smartmeter,
                        zaehlpunkt,
                        "kWh",
                    )
                    await importer.async_import(zaehlpunkt_response=zaehlpunkt_response)

                    if self._config.get(CONF_ENABLE_DAY_STATISTICS_IMPORT, False):
                        day_importer = DayStatisticsImporter(self.hass, self._async_smartmeter, zaehlpunkt)
                        await day_importer.async_import(start, end)

                result[zaehlpunkt] = ZaehlpunktData(
                    available=True,
                    attributes=attributes,
                    meter_read_value=meter_read_value,
                    meter_reading_date=meter_reading_date,
                    day_value_kwh=day_value_kwh,
                    day_reading_date=day_reading_date,
                    day_source_timestamp=day_source_timestamp,
                )
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Failed update for zaehlpunkt %s", zaehlpunkt)
                prev = self.data.get(zaehlpunkt) if self.data else None
                if prev is not None:
                    result[zaehlpunkt] = ZaehlpunktData(
                        available=False,
                        attributes=prev.attributes,
                        meter_read_value=prev.meter_read_value,
                        meter_reading_date=prev.meter_reading_date,
                        day_value_kwh=prev.day_value_kwh,
                        day_reading_date=prev.day_reading_date,
                        day_source_timestamp=prev.day_source_timestamp,
                    )
                else:
                    result[zaehlpunkt] = ZaehlpunktData(
                        available=False,
                        attributes={"error": str(err)},
                        meter_read_value=None,
                        meter_reading_date=None,
                        day_value_kwh=None,
                        day_reading_date=None,
                        day_source_timestamp=None,
                    )
        return result
