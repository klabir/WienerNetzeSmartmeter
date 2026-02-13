from datetime import timedelta

from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import WnsmDataUpdateCoordinator
from .reading_date_base import WNSMReadingDateBaseSensor


class WNSMDayReadingDateSensor(WNSMReadingDateBaseSensor):
    """Expose DAY reading_date as dedicated timestamp sensor."""

    def __init__(
        self,
        coordinator: WnsmDataUpdateCoordinator,
        zaehlpunkt: str,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__(coordinator, zaehlpunkt, "Day Reading Date", scan_interval)

    @property
    def unique_id(self) -> str:
        return f"{self.zaehlpunkt}_day_reading_date"

    @property
    def available(self) -> bool:
        point = self.coordinator.data.get(self.zaehlpunkt)
        return point is not None and point.available and point.day_source_timestamp is not None

    @property
    def native_value(self):
        point = self.coordinator.data.get(self.zaehlpunkt)
        return None if point is None else point.day_source_timestamp

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        point = self.coordinator.data.get(self.zaehlpunkt)
        if point is not None:
            attrs["reading_date"] = point.day_reading_date
        return attrs
