"""Shared METER_READ retrieval helpers for sensor entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .AsyncSmartmeter import AsyncSmartmeter
from .utils import build_reading_date_attributes


def _set_meter_read_attributes(attributes: dict[str, Any], meter_reads: list[int | float | None]) -> None:
    """Store first two METER_READ values in common attributes."""
    attributes["messwert1"] = meter_reads[0] if len(meter_reads) > 0 else None
    attributes["messwert2"] = meter_reads[1] if len(meter_reads) > 1 else None


async def async_get_latest_meter_read_payload(
    async_smartmeter: AsyncSmartmeter,
    zaehlpunkt: str,
    zaehlpunkt_response: dict[str, Any],
) -> tuple[int | float | None, dict[str, Any]]:
    """Return latest meter read value and normalized attributes for a Zählpunkt."""
    reading_dates, attributes = build_reading_date_attributes(zaehlpunkt_response)
    meter_reads: list[int | float | None] = []

    selected_value: int | float | None = None
    selected_reading_date = None

    for reading_date in reading_dates:
        meter_reading = await async_smartmeter.get_meter_reading_from_historic_data(
            zaehlpunkt, reading_date, datetime.now()
        )
        meter_reads.append(meter_reading)
        if selected_value is None and meter_reading is not None:
            selected_value = meter_reading
            selected_reading_date = reading_date

    _set_meter_read_attributes(attributes, meter_reads)

    if selected_reading_date is not None:
        attributes["reading_date"] = selected_reading_date.isoformat()
    return selected_value, attributes
