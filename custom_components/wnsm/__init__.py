"""Set up the Wiener Netze SmartMeter Integration component."""
from homeassistant import config_entries, core
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import (
    CONF_ENABLE_DAY_STATISTICS_IMPORT,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)

from .const import DEFAULT_SCAN_INTERVAL_MINUTES


async def async_setup_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    config = {**entry.data, **entry.options}
    config.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    config.setdefault(CONF_ENABLE_DAY_STATISTICS_IMPORT, False)
    hass.data[DOMAIN][entry.entry_id] = config

    # Forward the setup to the sensor platform.
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
