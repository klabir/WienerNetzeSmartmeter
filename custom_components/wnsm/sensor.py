"""WienerNetze Smartmeter sensor platform."""

from datetime import timedelta

from homeassistant import config_entries, core
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers.event import async_track_time_interval

from .const import CONF_ZAEHLPUNKTE, DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import WnsmDataUpdateCoordinator
from .day_reading_date_sensor import WNSMDayReadingDateSensor
from .day_sensor import WNSMDailySensor
from .meter_read_reading_date_sensor import WNSMMeterReadReadingDateSensor
from .wnsm_sensor import WNSMSensor


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    runtime_data = config_entry.runtime_data
    if runtime_data is None:
        raise ConfigEntryNotReady("Runtime data unavailable during sensor setup")

    config = runtime_data.config
    async_smartmeter = runtime_data.async_smartmeter

    scan_interval_minutes = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    scan_interval = timedelta(minutes=scan_interval_minutes)

    coordinator = WnsmDataUpdateCoordinator(hass, config_entry, async_smartmeter, config)
    await coordinator.async_config_entry_first_refresh()


    async def _async_run_imports(_now):
        await coordinator.async_run_imports()

    config_entry.async_on_unload(
        async_track_time_interval(hass, _async_run_imports, timedelta(hours=1))
    )
    hass.async_create_task(coordinator.async_run_imports())

    wnsm_sensors = [
        WNSMSensor(coordinator, zp["zaehlpunktnummer"], scan_interval)
        for zp in config[CONF_ZAEHLPUNKTE]
    ]
    wnsm_sensors.extend(
        [
            WNSMDailySensor(coordinator, zp["zaehlpunktnummer"], scan_interval)
            for zp in config[CONF_ZAEHLPUNKTE]
        ]
    )
    wnsm_sensors.extend(
        [
            WNSMDayReadingDateSensor(coordinator, zp["zaehlpunktnummer"], scan_interval)
            for zp in config[CONF_ZAEHLPUNKTE]
        ]
    )
    wnsm_sensors.extend(
        [
            WNSMMeterReadReadingDateSensor(coordinator, zp["zaehlpunktnummer"], scan_interval)
            for zp in config[CONF_ZAEHLPUNKTE]
        ]
    )
    async_add_entities(wnsm_sensors)
