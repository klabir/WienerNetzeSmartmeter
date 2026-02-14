"""Shared METER_READ retrieval helpers for sensor entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .AsyncSmartmeter import AsyncSmartmeter
from .utils import build_reading_date_attributes


async def async_get_latest_meter_read_payload(
    async_smartmeter: AsyncSmartmeter,
    zaehlpunkt: str,
    zaehlpunkt_response: dict[str, Any],
) -> tuple[int | float | None, dict[str, Any]]:
    """Return latest meter read value and normalized attributes for a Zählpunkt."""
    reading_dates, attributes = build_reading_date_attributes(zaehlpunkt_response)

    for reading_date in reading_dates:
        meter_reading = await async_smartmeter.get_meter_reading_from_historic_data(
            zaehlpunkt, reading_date, datetime.now()
        )
        if meter_reading is not None:
            attributes["reading_date"] = reading_date.isoformat()
            return meter_reading, attributes

    return None, attributes
