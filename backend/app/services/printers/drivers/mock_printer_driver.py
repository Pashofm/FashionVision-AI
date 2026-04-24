"""
Mock Printer Driver for Unit Testing

This driver is used for testing purposes. It stores print operations
in memory and always returns success, making it ideal for unit tests
without requiring actual printer hardware or file I/O.
"""

import time
from typing import List

from ..base_driver import PrinterDriver
from ..driver_type import DriverType
from ..print_result import PrintResult


class MockPrinterDriver(PrinterDriver):
    """
    Mock printer driver that stores prints in memory.

    This driver is designed for unit testing and development environments
    where no actual printing is desired. All print operations are stored
    in an in-memory list for verification.

    Attributes:
        _prints: Internal list storing all printed receipt data
    """

    def __init__(self):
        self._prints: List[dict] = []

    @property
    def driver_type(self) -> DriverType:
        return DriverType.MOCK

    @property
    def driver_name(self) -> str:
        return "Mock Printer Driver (Testing)"

    async def print(self, receipt_data: dict) -> PrintResult:
        """
        Store receipt data in memory and return success result.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            PrintResult with success=True and mock output path
        """
        start_time = time.time()
        await self.validate_receipt_data(receipt_data)

        self._prints.append(receipt_data.copy())

        duration_ms = int((time.time() - start_time) * 1000)

        return PrintResult(
            success=True,
            message="Mock print successful - receipt stored in memory",
            driver_type=self.driver_type.value,
            output_path=f"mock://print/{receipt_data.get('receipt_number', 'unknown')}",
            print_duration_ms=duration_ms,
            metadata={
                "prints_count": len(self._prints),
                "stored_receipt_number": receipt_data.get("receipt_number")
            }
        )

    async def preview(self, receipt_data: dict) -> str:
        """
        Generate a basic HTML preview of the receipt.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            str: Basic HTML representation of the receipt
        """
        await self.validate_receipt_data(receipt_data)

        items_html = ""
        for item in receipt_data.get("items", []):
            items_html += f"""
            <tr>
                <td>{item.get('name', 'Unknown')}</td>
                <td>{item.get('quantity', 0)}</td>
                <td>${item.get('price', 0.00):.2f}</td>
                <td>${item.get('subtotal', 0.00):.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Receipt Preview - {receipt_data.get('receipt_number', 'N/A')}</title>
            <style>
                body {{ font-family: monospace; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                .total {{ font-weight: bold; font-size: 1.2em; }}
            </style>
        </head>
        <body>
            <h1>[MOCK PREVIEW] Receipt</h1>
            <p><strong>Receipt #:</strong> {receipt_data.get('receipt_number', 'N/A')}</p>
            <p><strong>Order #:</strong> {receipt_data.get('order_number', 'N/A')}</p>
            <p><strong>Date:</strong> {receipt_data.get('created_at', 'N/A')}</p>
            <p><strong>Cashier:</strong> {receipt_data.get('cashier', 'N/A')}</p>
            <hr>
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th>Price</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            <hr>
            <p>Subtotal: ${receipt_data.get('subtotal', 0.00):.2f}</p>
            <p>Tax: ${receipt_data.get('tax_amount', 0.00):.2f}</p>
            <p class="total">Total: ${receipt_data.get('total_amount', 0.00):.2f}</p>
            <p><strong>Payment:</strong> {receipt_data.get('payment_method', 'N/A')}</p>
            <p><em>[This is a mock preview - no actual print occurred]</em></p>
        </body>
        </html>
        """
        return html

    def get_prints(self) -> List[dict]:
        """
        Get all stored print operations.

        Returns:
            List of receipt data dictionaries that have been printed
        """
        return self._prints.copy()

    def clear_prints(self) -> None:
        """Clear all stored print operations."""
        self._prints.clear()

    def get_print_count(self) -> int:
        """Return the number of stored print operations."""
        return len(self._prints)