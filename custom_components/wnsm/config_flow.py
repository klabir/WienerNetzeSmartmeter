"""
Setting up config flow for homeassistant
"""
import logging
from typing import Any, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.helpers import selector

from .api import Smartmeter
from .const import (
    ATTRS_ZAEHLPUNKTE_CALL,
    CONF_ENABLE_DAY_STATISTICS_IMPORT,
    CONF_ZAEHLPUNKTE,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .utils import translate_dict

_LOGGER = logging.getLogger(__name__)


def _scan_interval_selector(default_value: int):
    """Return a compatible selector (or fallback) for scan interval."""
    if hasattr(selector, "NumberSelector") and hasattr(selector, "NumberSelectorConfig"):
        return selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=1440,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="min",
            )
        )

    return vol.All(vol.Coerce(int), vol.Range(min=1, max=1440))


def _boolean_selector(default_value: bool):
    """Return a compatible selector (or fallback) for bool options."""
    if hasattr(selector, "BooleanSelector"):
        return selector.BooleanSelector()

    return cv.boolean


def _build_auth_schema() -> vol.Schema:
    """Schema shown during initial setup."""
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_MINUTES): _scan_interval_selector(
                DEFAULT_SCAN_INTERVAL_MINUTES
            ),
            vol.Optional(CONF_ENABLE_DAY_STATISTICS_IMPORT, default=False): _boolean_selector(False),
        }
    )


class WienerNetzeSmartMeterCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wiener Netze Smartmeter config flow"""

    data: Optional[dict[str, Any]]

    async def validate_auth(self, username: str, password: str) -> list[dict]:
        """
        Validates credentials for smartmeter.
        Raises a ValueError if the auth credentials are invalid.
        """
        smartmeter = Smartmeter(username, password)
        await self.hass.async_add_executor_job(smartmeter.login)
        contracts = await self.hass.async_add_executor_job(smartmeter.zaehlpunkte)
        zaehlpunkte = []
        if contracts is not None and isinstance(contracts, list) and len(contracts) > 0:
            for contract in contracts:
                if "zaehlpunkte" in contract:
                    zaehlpunkte.extend(contract["zaehlpunkte"])
        return zaehlpunkte

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        zps = []
        if user_input is not None:
            try:
                zps = await self.validate_auth(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.error("Error validating Wiener Netze auth")
                _LOGGER.exception(exception)
                errors["base"] = "auth"
            if not errors:
                self.data = user_input
                self.data[CONF_ZAEHLPUNKTE] = [
                    translate_dict(zp, ATTRS_ZAEHLPUNKTE_CALL)
                    for zp in zps
                    if zp["isActive"]
                ]
                return self.async_create_entry(
                    title="Wiener Netze Smartmeter", data=self.data
                )

        return self.async_show_form(
            step_id="user", data_schema=_build_auth_schema(), errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return WienerNetzeSmartMeterOptionsFlow(config_entry)


class WienerNetzeSmartMeterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Wiener Netze Smartmeter."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_value = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        current_day_stats_import = self.config_entry.options.get(
            CONF_ENABLE_DAY_STATISTICS_IMPORT,
            self.config_entry.data.get(CONF_ENABLE_DAY_STATISTICS_IMPORT, False),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_value): _scan_interval_selector(
                        current_value
                    ),
                    vol.Required(
                        CONF_ENABLE_DAY_STATISTICS_IMPORT,
                        default=current_day_stats_import,
                    ): _boolean_selector(current_day_stats_import),
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return WienerNetzeSmartMeterOptionsFlow(config_entry)


class WienerNetzeSmartMeterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Wiener Netze Smartmeter."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_value = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        current_day_stats_import = self.config_entry.options.get(
            CONF_ENABLE_DAY_STATISTICS_IMPORT,
            self.config_entry.data.get(CONF_ENABLE_DAY_STATISTICS_IMPORT, False),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_value): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=1440,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                    vol.Required(CONF_ENABLE_DAY_STATISTICS_IMPORT, default=current_day_stats_import): selector.BooleanSelector(),
                }
            ),
        )
