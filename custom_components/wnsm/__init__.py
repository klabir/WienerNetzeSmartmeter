"""Set up the Wiener Netze SmartMeter Integration component."""

from dataclasses import dataclass

from homeassistant import config_entries, core
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import (
    CONF_ENABLE_DAY_STATISTICS_IMPORT,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)


@dataclass(slots=True)
class WnsmRuntimeData:
    """Runtime configuration cached per config entry."""

    config: dict


async def async_setup_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
) -> bool:
    """Set up platform from a ConfigEntry."""
    config = {**entry.data, **entry.options}
    config.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    config.setdefault(CONF_ENABLE_DAY_STATISTICS_IMPORT, False)

    # Modern runtime storage for HA integrations.
    entry.runtime_data = WnsmRuntimeData(config=config)

    # Compatibility cache for existing platform setup code paths.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = config

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

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
        entry.runtime_data = None
    return unload_ok


async def async_reload_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
) -> None:
    """Reload config entry when options are updated from UI."""
    await hass.config_entries.async_reload(entry.entry_id)
