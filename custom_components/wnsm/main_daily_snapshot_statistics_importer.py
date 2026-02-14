import logging

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import DOMAIN
from .statistics_utils import as_utc, get_last_stats_timestamp

_LOGGER = logging.getLogger(__name__)


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

        start = as_utc(dt_util.parse_datetime(reading_date))
        if start is None:
            _LOGGER.warning("Skipping main snapshot import for %s: invalid reading_date '%s'", self.zaehlpunkt, reading_date)
            return

        last_start = await get_last_stats_timestamp(self.hass, self.id, "start")
        if last_start is not None and start <= last_start:
            return

        metadata = self.get_statistics_metadata()
        stats = [StatisticData(start=start, state=float(meter_reading), sum=None)]
        async_add_external_statistics(self.hass, metadata, stats)
