"""
Receipt Printer Service

This module provides a singleton service that manages printer drivers
and provides a unified interface for receipt printing operations.

The service maintains:
- A registry of available drivers
- The currently active driver
- Convenience methods for printing and previewing

Usage:
    from backend.app.services.printers import ReceiptPrinterService, DriverType

    # Change the active driver
    ReceiptPrinterService.set_driver(DriverType.ESCPOS)

    # Print a receipt
    result = await ReceiptPrinterService.print_receipt(receipt_data)

    # Get current driver info
    driver_type, driver_name = ReceiptPrinterService.get_current_driver()
"""

from typing import Tuple

from .driver_type import DriverType
from .print_result import PrintResult
from .base_driver import PrinterDriver
from .drivers import (
    MockPrinterDriver,
    TextFilePrinterDriver,
    HTMLPrinterDriver,
    ESCPOSPrinterDriver,
)


class ReceiptPrinterService:
    """
    Singleton service for managing receipt printing operations.

    This class provides a centralized interface for printing receipts
    using interchangable printer drivers. It maintains the currently
    active driver and provides convenience methods.

    Attributes:
        _current_driver: Currently active printer driver instance
        _drivers: Dictionary mapping DriverType to driver instances
    """

    _current_driver: PrinterDriver = None
    _drivers: dict[DriverType, PrinterDriver] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the driver registry and set default driver."""
        if cls._initialized:
            return

        cls._drivers = {
            DriverType.MOCK: MockPrinterDriver(),
            DriverType.TEXTFILE: TextFilePrinterDriver(),
            DriverType.HTML: HTMLPrinterDriver(),
            DriverType.ESCPOS: ESCPOSPrinterDriver(),
        }

        cls._current_driver = cls._drivers[DriverType.MOCK]
        cls._initialized = True

    @classmethod
    def set_driver(cls, driver_type: DriverType) -> None:
        """
        Change the active printer driver.

        Args:
            driver_type: The DriverType to switch to

        Raises:
            ValueError: If driver_type is not registered
        """
        cls._initialize()

        if driver_type not in cls._drivers:
            available = [dt.value for dt in cls._drivers.keys()]
            raise ValueError(
                f"Driver type '{driver_type.value}' not available. "
                f"Available drivers: {available}"
            )

        cls._current_driver = cls._drivers[driver_type]

    @classmethod
    def get_current_driver(cls) -> Tuple[DriverType, str]:
        """
        Get information about the currently active driver.

        Returns:
            Tuple of (DriverType, driver_name)
        """
        cls._initialize()
        return (
            cls._current_driver.driver_type,
            cls._current_driver.driver_name
        )

    @classmethod
    def get_available_drivers(cls) -> list[Tuple[DriverType, str]]:
        """
        Get list of all available drivers.

        Returns:
            List of (DriverType, driver_name) tuples
        """
        cls._initialize()
        return [
            (driver.driver_type, driver.driver_name)
            for driver in cls._drivers.values()
        ]

    @classmethod
    async def print_receipt(cls, receipt_data: dict) -> PrintResult:
        """
        Print a receipt using the current active driver.

        Args:
            receipt_data: Dictionary containing:
                - receipt_number: Unique identifier
                - order_number: Associated order number
                - items: List of items with name, quantity, price, subtotal
                - subtotal: Subtotal amount
                - tax_amount: Tax amount
                - total_amount: Grand total
                - payment_method: Payment method (cash/card)
                - cashier: Name of cashier
                - created_at: ISO timestamp

        Returns:
            PrintResult with success status and output information
        """
        cls._initialize()
        return await cls._current_driver.print(receipt_data)

    @classmethod
    async def preview_receipt(cls, receipt_data: dict) -> str:
        """
        Generate an HTML preview of the receipt.

        Args:
            receipt_data: Same dictionary as print_receipt()

        Returns:
            str: HTML string representing the receipt preview
        """
        cls._initialize()
        return await cls._current_driver.preview(receipt_data)

    @classmethod
    def get_driver_instance(cls, driver_type: DriverType) -> PrinterDriver:
        """
        Get a specific driver instance by type.

        Args:
            driver_type: The DriverType to retrieve

        Returns:
            PrinterDriver instance

        Raises:
            ValueError: If driver_type is not registered
        """
        cls._initialize()

        if driver_type not in cls._drivers:
            raise ValueError(f"Driver type '{driver_type.value}' not registered")

        return cls._drivers[driver_type]

    @classmethod
    def reset_to_default(cls) -> None:
        """Reset to the default (Mock) driver."""
        cls._initialize()
        cls._current_driver = cls._drivers[DriverType.MOCK]