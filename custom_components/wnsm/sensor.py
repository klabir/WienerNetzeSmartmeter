"""
WienerNetze Smartmeter sensor platform
"""
import collections.abc
from datetime import timedelta
from typing import Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import core, config_entries
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA
)
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import DOMAIN
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
)
from .const import CONF_ZAEHLPUNKTE, DEFAULT_SCAN_INTERVAL_MINUTES
from .day_sensor import WNSMDailySensor
from .wnsm_sensor import WNSMSensor
# Time between updating data from Wiener Netze (YAML config only)
SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    scan_interval_minutes = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    scan_interval = timedelta(minutes=scan_interval_minutes)
    wnsm_sensors = [
        WNSMSensor(
            config[CONF_USERNAME],
            config[CONF_PASSWORD],
            zp["zaehlpunktnummer"],
            scan_interval=scan_interval,
        )
        for zp in config[CONF_ZAEHLPUNKTE]
    ]
    wnsm_sensors.extend(
        [
            WNSMDailySensor(
                config[CONF_USERNAME],
                config[CONF_PASSWORD],
                zp["zaehlpunktnummer"],
                scan_interval=scan_interval,
            )
            for zp in config[CONF_ZAEHLPUNKTE]
        ]
    )
    async_add_entities(wnsm_sensors, update_before_add=True)


async def async_setup_platform(
    hass: core.HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,
    async_add_entities: collections.abc.Callable,
    discovery_info: Optional[
        DiscoveryInfoType
    ] = None,  # pylint: disable=unused-argument
) -> None:
    """Set up the sensor platform by adding it into configuration.yaml"""
    wnsm_sensor = WNSMSensor(config[CONF_USERNAME], config[CONF_PASSWORD], config[CONF_DEVICE_ID])
    wnsm_daily_sensor = WNSMDailySensor(config[CONF_USERNAME], config[CONF_PASSWORD], config[CONF_DEVICE_ID])
    async_add_entities([wnsm_sensor, wnsm_daily_sensor], update_before_add=True)
