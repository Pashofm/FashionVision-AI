"""
Receipt Printer Module

This module provides a flexible receipt printing system with pluggable
printer drivers. It supports multiple output formats and printer types
through a driver interchangeability pattern.

Usage:
    from backend.app.services.printers import ReceiptPrinterService, DriverType

    # Set the active driver
    ReceiptPrinterService.set_driver(DriverType.HTML)

    # Print a receipt
    result = await ReceiptPrinterService.print_receipt(receipt_data)

    # Get HTML preview
    html = await ReceiptPrinterService.preview_receipt(receipt_data)
"""

from .driver_type import DriverType
from .print_result import PrintResult
from .receipt_printer_service import ReceiptPrinterService
from .base_driver import PrinterDriver

__all__ = [
    "DriverType",
    "PrintResult",
    "ReceiptPrinterService",
    "PrinterDriver",
]