"""
Base Printer Driver Abstract Class

This module defines the interface that all printer drivers must implement.
It provides the contract for receipt printing operations.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .driver_type import DriverType
    from .print_result import PrintResult


class PrinterDriver(ABC):
    """
    Abstract base class for receipt printer drivers.

    All printer drivers must implement this interface to ensure
    consistent behavior across different printing/output methods.

    Methods:
        driver_type: Property returning the driver type enumeration
        driver_name: Property returning a human-readable driver name
        print: Async method to print a receipt
        preview: Async method to generate HTML preview
    """

    @property
    @abstractmethod
    def driver_type(self) -> "DriverType":
        """
        Return the DriverType enumeration value for this driver.

        Returns:
            DriverType: The type of this driver
        """
        pass

    @property
    @abstractmethod
    def driver_name(self) -> str:
        """
        Return a human-readable name for this driver.

        Returns:
            str: Friendly name like "Mock Printer" or "ESCPOS Thermal"
        """
        pass

    @abstractmethod
    async def print(self, receipt_data: dict) -> "PrintResult":
        """
        Print a receipt using the driver's output method.

        Args:
            receipt_data: Dictionary containing receipt information:
                - receipt_number: Unique receipt identifier
                - order_number: Associated order number
                - items: List of items with name, quantity, price
                - subtotal: Subtotal amount
                - tax_amount: Tax amount
                - total_amount: Grand total
                - payment_method: Payment method used
                - cashier: Name of the cashier
                - created_at: ISO timestamp

        Returns:
            PrintResult: Result of the print operation
        """
        pass

    @abstractmethod
    async def preview(self, receipt_data: dict) -> str:
        """
        Generate an HTML preview of the receipt.

        Args:
            receipt_data: Same dictionary as print()

        Returns:
            str: HTML string representing the receipt preview
        """
        pass

    async def validate_receipt_data(self, receipt_data: dict) -> None:
        """
        Validate that required fields are present in receipt_data.

        Args:
            receipt_data: Receipt data dictionary to validate

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "receipt_number", "order_number", "items",
            "subtotal", "tax_amount", "total_amount",
            "payment_method", "cashier", "created_at"
        ]
        missing = [f for f in required_fields if f not in receipt_data]
        if missing:
            raise ValueError(f"Missing required receipt fields: {missing}")