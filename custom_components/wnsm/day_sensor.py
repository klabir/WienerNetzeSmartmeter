from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import WnsmDataUpdateCoordinator


class WNSMDailySensor(CoordinatorEntity[WnsmDataUpdateCoordinator], SensorEntity):
    """Representation of a daily consumption sensor."""

    def __init__(
        self,
        coordinator: WnsmDataUpdateCoordinator,
        zaehlpunkt: str,
        scan_interval: timedelta = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    ) -> None:
        super().__init__(coordinator)
        self.zaehlpunkt = zaehlpunkt
        self._attr_name = f"{zaehlpunkt} Day"
        self._attr_icon = "mdi:calendar-today"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_suggested_update_interval = scan_interval

    @property
    def unique_id(self) -> str:
        return f"{self.zaehlpunkt}_day"

    @property
    def available(self) -> bool:
        point = self.coordinator.data.get(self.zaehlpunkt)
        return point is not None and point.available

    @property
    def native_value(self):
        point = self.coordinator.data.get(self.zaehlpunkt)
        return None if point is None else point.day_value_kwh

    @property
    def extra_state_attributes(self):
        point = self.coordinator.data.get(self.zaehlpunkt)
        if point is None:
            return {}
        attrs = dict(point.attributes)
        attrs["reading_date"] = point.day_reading_date
        return attrs
