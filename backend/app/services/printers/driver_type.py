"""
Driver Type Enumeration for Receipt Printer System

This module defines the available printer driver types that can be used
for receipt generation and printing.
"""

from enum import Enum


class DriverType(Enum):
    """
    Enumeration of supported printer driver types.

    Each driver type corresponds to a specific printing/output method:
    - MOCK: For unit testing without actual printing
    - TEXTFILE: For audit logs stored as text files
    - HTML: For browser preview or email HTML
    - ESCPOS: For thermal receipt printers using ESC/POS protocol
    """
    MOCK = "mock"
    TEXTFILE = "textfile"
    HTML = "html"
    ESCPOS = "escpos"

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all driver type values."""
        return [driver.value for driver in cls]

    @classmethod
    def from_string(cls, value: str) -> "DriverType":
        """Convert string to DriverType, case-insensitive."""
        for driver in cls:
            if driver.value.lower() == value.lower():
                return driver
        raise ValueError(f"Unknown driver type: {value}")