import logging
from warnings import deprecated

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy

_LOGGER = logging.getLogger(__name__)


@deprecated("Remove this sensor from your configuration.")
class StatisticsSensor(SensorEntity):
    """Deprecated placeholder sensor kept for backward compatibility."""

    def __init__(self, username: str, password: str, zaehlpunkt: str) -> None:
        self.username = username
        self.password = password
        self.zaehlpunkt = zaehlpunkt
        self._available = False
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @staticmethod
    def statistics(s: str) -> str:
        return f"{s}_statistics"

    @property
    def icon(self) -> str:
        return "mdi:meter-electric-outline"

    @property
    def name(self) -> str:
        return StatisticsSensor.statistics(self.zaehlpunkt)

    @property
    def unique_id(self) -> str:
        return StatisticsSensor.statistics(self.zaehlpunkt)

    @property
    def available(self) -> bool:
        return False

    async def async_update(self):
        self._available = False
        _LOGGER.warning("StatisticsSensor disabled. Please remove it from your configuration.")
