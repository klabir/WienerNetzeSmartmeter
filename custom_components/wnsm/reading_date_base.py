"""Shared base for reading-date timestamp sensors."""

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import WnsmDataUpdateCoordinator


class WNSMReadingDateBaseSensor(CoordinatorEntity[WnsmDataUpdateCoordinator], SensorEntity):
    """Common behaviour for reading-date timestamp sensors."""

    def __init__(
        self,
        coordinator: WnsmDataUpdateCoordinator,
        zaehlpunkt: str,
        name_suffix: str,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__(coordinator)
        self.zaehlpunkt = zaehlpunkt
        self._attr_name = f"{zaehlpunkt} {name_suffix}"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_suggested_update_interval = scan_interval

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        point = self.coordinator.data.get(self.zaehlpunkt)
        return {} if point is None else dict(point.attributes)
