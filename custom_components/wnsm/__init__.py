"""Set up the Wiener Netze SmartMeter Integration component."""
from homeassistant import core, config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import DOMAIN

from .const import DEFAULT_SCAN_INTERVAL_MINUTES


async def async_setup_entry(
        hass: core.HomeAssistant,
        entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    config = {**entry.data, **entry.options}
    config.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    hass.data[DOMAIN][entry.entry_id] = config

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Forward the setup to the sensor platform.
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_update_options(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(entry.entry_id)
