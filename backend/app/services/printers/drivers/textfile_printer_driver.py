"""
TextFile Printer Driver for Audit Logging

This driver writes receipt data to plain text files for audit purposes.
Files are stored in the receipts/audit/ directory with a .txt extension.

Use cases:
- Compliance and audit trail requirements
- Archival of all transaction receipts
- Debugging and troubleshooting print issues
"""

import os
import time
from datetime import datetime
from pathlib import Path

from ..base_driver import PrinterDriver
from ..driver_type import DriverType
from ..print_result import PrintResult


class TextFilePrinterDriver(PrinterDriver):
    """
    Printer driver that writes receipts to text files for auditing.

    Files are created in the receipts/audit/ directory with the naming
    convention: REC-{receipt_number}-{timestamp}.txt
    """

    def __init__(self, audit_dir: str = None):
        """
        Initialize the text file printer driver.

        Args:
            audit_dir: Directory path for storing audit files.
                      Defaults to backend/receipts/audit/
        """
        if audit_dir is None:
            backend_dir = Path(__file__).parent.parent.parent.parent
            audit_dir = backend_dir / "receipts" / "audit"

        self.audit_dir = Path(audit_dir)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create audit directory if it doesn't exist."""
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    @property
    def driver_type(self) -> DriverType:
        return DriverType.TEXTFILE

    @property
    def driver_name(self) -> str:
        return "Text File Printer Driver (Audit)"

    async def print(self, receipt_data: dict) -> PrintResult:
        """
        Write receipt data to a text file for audit purposes.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            PrintResult with file path and success status
        """
        start_time = time.time()
        await self.validate_receipt_data(receipt_data)

        receipt_number = receipt_data.get("receipt_number", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"REC-{receipt_number}-{timestamp}.txt"
        filepath = self.audit_dir / filename

        content = self._format_receipt_text(receipt_data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        duration_ms = int((time.time() - start_time) * 1000)

        return PrintResult(
            success=True,
            message=f"Receipt written to audit file: {filename}",
            driver_type=self.driver_type.value,
            output_path=str(filepath),
            print_duration_ms=duration_ms,
            metadata={
                "filename": filename,
                "file_size_bytes": filepath.stat().st_size
            }
        )

    async def preview(self, receipt_data: dict) -> str:
        """
        Generate an HTML preview of the receipt.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            str: HTML representation of the receipt
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
            <title>Receipt - {receipt_data.get('receipt_number', 'N/A')}</title>
            <style>
                body {{ font-family: 'Courier New', monospace; padding: 20px; max-width: 300px; margin: 0 auto; }}
                .header {{ text-align: center; border-bottom: 1px dashed #000; padding-bottom: 10px; margin-bottom: 10px; }}
                .items table {{ width: 100%; border-collapse: collapse; }}
                .items th {{ text-align: left; border-bottom: 1px solid #000; }}
                .items td {{ padding: 4px 0; }}
                .totals {{ margin-top: 10px; border-top: 1px solid #000; padding-top: 10px; }}
                .total-row {{ font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 0.8em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>FASHIONVISION AI</h2>
                <p>Receipt: {receipt_data.get('receipt_number', 'N/A')}</p>
                <p>Order: {receipt_data.get('order_number', 'N/A')}</p>
                <p>Date: {receipt_data.get('created_at', 'N/A')}</p>
                <p>Cashier: {receipt_data.get('cashier', 'N/A')}</p>
            </div>
            <div class="items">
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
            </div>
            <div class="totals">
                <p>Subtotal: ${receipt_data.get('subtotal', 0.00):.2f}</p>
                <p>Tax: ${receipt_data.get('tax_amount', 0.00):.2f}</p>
                <p class="total-row">TOTAL: ${receipt_data.get('total_amount', 0.00):.2f}</p>
            </div>
            <div class="footer">
                <p>Payment Method: {receipt_data.get('payment_method', 'N/A')}</p>
                <p>Thank you for shopping with us!</p>
            </div>
        </body>
        </html>
        """
        return html

    def _format_receipt_text(self, receipt_data: dict) -> str:
        """
        Format receipt data as a plain text receipt.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            str: Formatted plain text receipt
        """
        lines = []
        lines.append("=" * 40)
        lines.append("        FASHIONVISION AI RECEIPT")
        lines.append("=" * 40)
        lines.append("")
        lines.append(f"Receipt #: {receipt_data.get('receipt_number', 'N/A')}")
        lines.append(f"Order #:   {receipt_data.get('order_number', 'N/A')}")
        lines.append(f"Date:      {receipt_data.get('created_at', 'N/A')}")
        lines.append(f"Cashier:   {receipt_data.get('cashier', 'N/A')}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("ITEMS")
        lines.append("-" * 40)

        for item in receipt_data.get("items", []):
            name = item.get("name", "Unknown")[:20]
            qty = item.get("quantity", 0)
            price = item.get("price", 0.00)
            subtotal = item.get("subtotal", 0.00)
            lines.append(f"{name:<20} x{qty}")
            lines.append(f"{"":>22} ${price:.2f}")
            lines.append(f"{"":>22} Sub: ${subtotal:.2f}")

        lines.append("-" * 40)
        lines.append(f"Subtotal:              ${receipt_data.get('subtotal', 0.00):.2f}")
        lines.append(f"Tax:                  ${receipt_data.get('tax_amount', 0.00):.2f}")
        lines.append("-" * 40)
        lines.append(f"TOTAL:                ${receipt_data.get('total_amount', 0.00):.2f}")
        lines.append("=" * 40)
        lines.append("")
        lines.append(f"Payment: {receipt_data.get('payment_method', 'N/A')}")
        lines.append("")
        lines.append("        Thank you for shopping!")
        lines.append("            Please come again")
        lines.append("")
        lines.append(f"[Audit file - {datetime.now().isoformat()}]")

        return "\n".join(lines)