"""
HTML Printer Driver for Browser Preview and Email

This driver generates complete HTML receipts that can be:
- Displayed in a browser for preview
- Sent via email to customers
- Stored for digital record keeping

Use cases:
- Customer email receipts
- Browser-based receipt preview
- Digital receipt archival with full formatting
"""

import os
import time
from datetime import datetime
from pathlib import Path

from ..base_driver import PrinterDriver
from ..driver_type import DriverType
from ..print_result import PrintResult


class HTMLPrinterDriver(PrinterDriver):
    """
    Printer driver that generates HTML files for preview and email.

    HTML files are stored in the receipts/previews/ directory with
    a .html extension. These can be served to browsers or attached
    to emails.
    """

    def __init__(self, output_dir: str = None):
        """
        Initialize the HTML printer driver.

        Args:
            output_dir: Directory path for storing HTML files.
                       Defaults to backend/receipts/previews/
        """
        if output_dir is None:
            backend_dir = Path(__file__).parent.parent.parent.parent
            output_dir = backend_dir / "receipts" / "previews"

        self.output_dir = Path(output_dir)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def driver_type(self) -> DriverType:
        return DriverType.HTML

    @property
    def driver_name(self) -> str:
        return "HTML Printer Driver (Preview/Email)"

    async def print(self, receipt_data: dict) -> PrintResult:
        """
        Generate an HTML file with the receipt content.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            PrintResult with HTML file path and success status
        """
        start_time = time.time()
        await self.validate_receipt_data(receipt_data)

        receipt_number = receipt_data.get("receipt_number", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"REC-{receipt_number}-{timestamp}.html"
        filepath = self.output_dir / filename

        html_content = self._generate_html(receipt_data)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        duration_ms = int((time.time() - start_time) * 1000)

        return PrintResult(
            success=True,
            message=f"HTML receipt generated: {filename}",
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
        Return the full HTML content for immediate display.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            str: Complete HTML document string
        """
        await self.validate_receipt_data(receipt_data)
        return self._generate_html(receipt_data)

    def _generate_html(self, receipt_data: dict) -> str:
        """
        Generate a complete HTML receipt document.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            str: Complete HTML document
        """
        items_html = ""
        for item in receipt_data.get("items", []):
            items_html += f"""
            <tr>
                <td>{self._escape_html(item.get('name', 'Unknown'))}</td>
                <td style="text-align: center;">{item.get('quantity', 0)}</td>
                <td style="text-align: right;">${item.get('price', 0.00):.2f}</td>
                <td style="text-align: right;">${item.get('subtotal', 0.00):.2f}</td>
            </tr>
            """

        payment_method = receipt_data.get('payment_method', 'N/A')
        card_last_four = receipt_data.get('card_last_four')
        authorization_code = receipt_data.get('authorization_code')

        payment_info = payment_method.upper()
        if card_last_four:
            payment_info += f" **** {card_last_four}"
        if authorization_code:
            payment_info += f" (Auth: {authorization_code})"

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recibo - {receipt_data.get('receipt_number', 'N/A')}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .receipt-container {{
            max-width: 350px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .receipt-header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 25px 20px;
            text-align: center;
        }}
        .receipt-header h1 {{
            font-size: 1.5em;
            margin-bottom: 5px;
            letter-spacing: 2px;
        }}
        .receipt-header p {{
            font-size: 0.85em;
            opacity: 0.8;
        }}
        .receipt-body {{
            padding: 20px;
        }}
        .info-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #ddd;
        }}
        .info-item label {{
            font-size: 0.7em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .info-item p {{
            font-size: 0.95em;
            color: #333;
            font-weight: 500;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .items-table th {{
            font-size: 0.7em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: left;
            padding: 8px 0;
            border-bottom: 2px solid #1a1a2e;
        }}
        .items-table td {{
            padding: 10px 0;
            font-size: 0.9em;
            color: #333;
        }}
        .items-table .empty-cell {{}}
        .totals-section {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .total-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9em;
            color: #555;
        }}
        .total-row.grand-total {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 2px solid #1a1a2e;
            font-size: 1.2em;
            font-weight: bold;
            color: #1a1a2e;
        }}
        .payment-section {{
            text-align: center;
            padding: 15px;
            background: #1a1a2e;
            color: white;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .payment-section label {{
            font-size: 0.7em;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .payment-section p {{
            font-size: 1.1em;
            margin-top: 5px;
        }}
        .receipt-footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 0.8em;
            border-top: 1px dashed #ddd;
        }}
        .receipt-footer p {{
            margin-bottom: 5px;
        }}
        .qr-placeholder {{
            width: 80px;
            height: 80px;
            background: #f0f0f0;
            margin: 10px auto;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7em;
            color: #aaa;
        }}
    </style>
</head>
<body>
    <div class="receipt-container">
        <div class="receipt-header">
            <h1>FASHIONVISION AI</h1>
            <p>Recibo de Pago</p>
        </div>
        <div class="receipt-body">
            <div class="info-section">
                <div class="info-item">
                    <label>No. Recibo</label>
                    <p>{receipt_data.get('receipt_number', 'N/A')}</p>
                </div>
                <div class="info-item">
                    <label>No. Orden</label>
                    <p>{receipt_data.get('order_number', 'N/A')}</p>
                </div>
                <div class="info-item">
                    <label>Fecha</label>
                    <p>{receipt_data.get('created_at', 'N/A')}</p>
                </div>
                <div class="info-item">
                    <label>Cajero</label>
                    <p>{receipt_data.get('cashier', 'N/A')}</p>
                </div>
            </div>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th style="text-align: center;">Cant.</th>
                        <th style="text-align: right;">Precio</th>
                        <th style="text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            <div class="totals-section">
                <div class="total-row">
                    <span>Subtotal</span>
                    <span>${receipt_data.get('subtotal', 0.00):.2f}</span>
                </div>
                <div class="total-row">
                    <span>Impuesto</span>
                    <span>${receipt_data.get('tax_amount', 0.00):.2f}</span>
                </div>
                <div class="total-row grand-total">
                    <span>TOTAL</span>
                    <span>${receipt_data.get('total_amount', 0.00):.2f}</span>
                </div>
            </div>
            <div class="payment-section">
                <label>Método de Pago</label>
                <p>{payment_info}</p>
            </div>
        </div>
        <div class="receipt-footer">
            <div class="qr-placeholder">QR Code</div>
            <p>Gracias por su compra</p>
            <p>Conserv este recibo para cualquier devolución</p>
        </div>
    </div>
</body>
</html>"""

    def _escape_html(self, text: str) -> str:
        """Escape special HTML characters in text."""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))