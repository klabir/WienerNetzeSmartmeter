import logging
from datetime import datetime, timezone

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics, get_last_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize datetime to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MainDailySnapshotStatisticsImporter:
    """Import METER_READ snapshot points into long-term statistics with reading-date timestamps."""

    def __init__(self, hass: HomeAssistant, zaehlpunkt: str):
        self.hass = hass
        self.zaehlpunkt = zaehlpunkt
        self.id = f"{DOMAIN}:{slugify(zaehlpunkt)}_main_daily_snapshot"

    def get_statistics_metadata(self) -> StatisticMetaData:
        return StatisticMetaData(
            source=DOMAIN,
            statistic_id=self.id,
            name=f"{self.zaehlpunkt} Main Daily Snapshot",
            unit_of_measurement="kWh",
            has_mean=False,
            has_sum=False,
        )

    async def async_import(self, reading_date: str | None, meter_reading: int | float) -> None:
        """Import one snapshot point at the provided reading date."""
        if reading_date is None:
            _LOGGER.debug("Skipping main snapshot import for %s: reading_date is missing", self.zaehlpunkt)
            return

        start = dt_util.parse_datetime(reading_date)
        start = _as_utc(start)
        if start is None:
            _LOGGER.warning("Skipping main snapshot import for %s: invalid reading_date '%s'", self.zaehlpunkt, reading_date)
            return

        last = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,
            self.id,
            True,
            {"start"},
        )

        last_start = None
        if self.id in last and len(last[self.id]) == 1:
            last_start = last[self.id][0].get("start")
            if isinstance(last_start, (int, float)):
                last_start = dt_util.utc_from_timestamp(last_start)
            elif isinstance(last_start, str):
                last_start = dt_util.parse_datetime(last_start)
            last_start = _as_utc(last_start)

        if last_start is not None and start <= last_start:
            return

        metadata = self.get_statistics_metadata()
        stats = [StatisticData(start=start, state=float(meter_reading), sum=None)]
        async_add_external_statistics(self.hass, metadata, stats)
