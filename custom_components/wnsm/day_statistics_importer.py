import logging
from datetime import datetime, timezone

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics, get_last_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .AsyncSmartmeter import AsyncSmartmeter
from .api.constants import ValueType
from .const import DOMAIN
from .day_processing import extract_day_points

_LOGGER = logging.getLogger(__name__)


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize datetime to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class DayStatisticsImporter:
    """Import DAY readings into long-term statistics with source timestamps."""

    def __init__(self, hass: HomeAssistant, async_smartmeter: AsyncSmartmeter, zaehlpunkt: str):
        self.hass = hass
        self.async_smartmeter = async_smartmeter
        self.zaehlpunkt = zaehlpunkt
        self.id = f"{DOMAIN}:{slugify(zaehlpunkt)}_day"

    def get_statistics_metadata(self) -> StatisticMetaData:
        return StatisticMetaData(
            source=DOMAIN,
            statistic_id=self.id,
            name=f"{self.zaehlpunkt} Day",
            unit_of_measurement="kWh",
            has_mean=False,
            has_sum=False,
        )

    async def async_import(self, date_from: datetime, date_to: datetime) -> None:
        """Import statistics newer than the latest imported sample."""
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

        raw = await self.async_smartmeter.get_historic_data(
            self.zaehlpunkt,
            date_from,
            date_to,
            ValueType.DAY,
        )
        points = extract_day_points(raw)
        metadata = self.get_statistics_metadata()

        stats = []
        for point in sorted(points, key=lambda p: p.source_timestamp):
            ts = _as_utc(point.source_timestamp)
            if last_start is not None and ts <= last_start:
                continue
            stats.append(StatisticData(start=ts, state=float(point.value_kwh), sum=None))

        if stats:
            _LOGGER.debug("Importing %s DAY statistics for %s", len(stats), self.zaehlpunkt)
            async_add_external_statistics(self.hass, metadata, stats)
