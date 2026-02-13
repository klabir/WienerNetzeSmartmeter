"""Unofficial Python wrapper for the Wiener Netze Smart Meter private API."""
from importlib.metadata import PackageNotFoundError, version

from .client import Smartmeter

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["Smartmeter"]
