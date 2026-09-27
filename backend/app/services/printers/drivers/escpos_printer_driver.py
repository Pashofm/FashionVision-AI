"""
ESCPOS Printer Driver for Thermal Receipt Printers

This driver communicates with ESC/POS compatible thermal receipt printers
via USB/Serial connection. It converts receipt data to ESC/POS commands
and sends them to the printer.

Use cases:
- Real thermal printer output in production
- Customer receipts at POS stations

Supported printers:
- Epson TM-T88 series
- Epson TM-T20/T-T30 series
- Most ESC/POS compatible thermal printers

Connection:
- USB via pySerial (virtual COM port)
- Serial RS232
"""

import time
from datetime import datetime
from typing import Optional

from ..base_driver import PrinterDriver
from ..driver_type import DriverType
from ..print_result import PrintResult


class ESCPOSPrinterDriver(PrinterDriver):
    """
    Printer driver for ESC/POS thermal receipt printers.

    This driver sends raw ESC/POS commands to a thermal printer connected
    via USB/Serial. It handles text formatting, cutting, and other printer-specific
    operations through ESC/POS command sequences.
    """

    ESC_INITIALIZE = b"\x1b\x40"
    ESC_ALIGN_CENTER = b"\x1b\x61\x01"
    ESC_ALIGN_LEFT = b"\x1b\x61\x00"
    ESC_BOLD_ON = b"\x1b\x45\x01"
    ESC_BOLD_OFF = b"\x1b\x45\x00"
    ESC_DOUBLE_HEIGHT_ON = b"\x1b\x21\x10"
    ESC_DOUBLE_HEIGHT_OFF = b"\x1b\x21\x00"
    ESC_UNDERLINE_ON = b"\x1b\x2d\x01"
    ESC_UNDERLINE_OFF = b"\x1b\x2d\x00"
    ESC_CUT_PAPER = b"\x1d\x56\x00"
    ESC_CUT_PAPER_PARTIAL = b"\x1d\x56\x01"

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        timeout: float = 5.0
    ):
        """
        Initialize the ESCPOS printer driver.

        Args:
            port: Serial port path (e.g., /dev/ttyUSB0, COM3)
            baudrate: Serial baud rate (default: 9600)
            timeout: Serial port timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def _connect(self) -> None:
        """Establish serial connection to the printer."""
        try:
            import serial
            if self._serial is None or not self._serial.is_open:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=False,
                    rtscts=False
                )
                self._serial.open()
        except ImportError:
            raise ImportError(
                "pyserial is required for ESCPOS printing. "
                "Install it with: pip install pyserial"
            )

    def _disconnect(self) -> None:
        """Close the serial connection."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()

    def _send(self, data: bytes) -> None:
        """Send raw bytes to the printer."""
        if self._serial is None or not self._serial.is_open:
            self._connect()
        self._serial.write(data)
        self._serial.flush()

    @property
    def driver_type(self) -> DriverType:
        return DriverType.ESCPOS

    @property
    def driver_name(self) -> str:
        return f"ESCPOS Thermal Printer ({self.port})"

    async def print(self, receipt_data: dict) -> PrintResult:
        """
        Send receipt data to the thermal printer via ESC/POS commands.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            PrintResult with success status
        """
        start_time = time.time()

        try:
            await self._async_print(receipt_data)
            duration_ms = int((time.time() - start_time) * 1000)

            return PrintResult(
                success=True,
                message=f"Receipt printed to thermal printer on {self.port}",
                driver_type=self.driver_type.value,
                output_path=f"serial://{self.port}",
                print_duration_ms=duration_ms,
                metadata={
                    "port": self.port,
                    "baudrate": self.baudrate
                }
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return PrintResult(
                success=False,
                message=f"ESCPOS print failed: {str(e)}",
                driver_type=self.driver_type.value,
                error_code="ESCPOS_ERROR",
                print_duration_ms=duration_ms,
                metadata={
                    "port": self.port,
                    "error_type": type(e).__name__
                }
            )
        finally:
            self._disconnect()

    async def _async_print(self, receipt_data: dict) -> None:
        """Perform the actual print operation asynchronously."""
        await self.validate_receipt_data(receipt_data)

        commands = self._build_escpos_commands(receipt_data)
        self._send(commands)

    def _build_escpos_commands(self, receipt_data: dict) -> bytes:
        """
        Build ESC/POS command sequence for the receipt.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            bytes: Complete ESC/POS command sequence
        """
        cmds = []

        cmds.append(self.ESC_INITIALIZE)

        cmds.append(self.ESC_ALIGN_CENTER)
        cmds.append(self.ESC_DOUBLE_HEIGHT_ON)
        cmds.append(self.ESC_BOLD_ON)
        cmds.append(b"FASHIONVISION AI\r\n")
        cmds.append(self.ESC_BOLD_OFF)
        cmds.append(self.ESC_DOUBLE_HEIGHT_OFF)
        cmds.append(b"Receipt\r\n")
        cmds.append(b"\r\n")

        cmds.append(self.ESC_ALIGN_LEFT)

        cmds.append(self.ESC_BOLD_ON)
        cmds.append(f"Receipt #: {receipt_data.get('receipt_number', 'N/A')}\r\n".encode())
        cmds.append(f"Order #:   {receipt_data.get('order_number', 'N/A')}\r\n".encode())
        cmds.append(f"Date:      {receipt_data.get('created_at', 'N/A')}\r\n".encode())
        cmds.append(f"Cashier:   {receipt_data.get('cashier', 'N/A')}\r\n".encode())
        cmds.append(self.ESC_BOLD_OFF)

        cmds.append(b"- " * 20 + b"\r\n")
        cmds.append(b"ITEMS\r\n")
        cmds.append(b"- " * 20 + b"\r\n")

        for item in receipt_data.get("items", []):
            name = item.get("name", "Unknown")[:18]
            qty = item.get("quantity", 0)
            price = item.get("price", 0.00)
            subtotal = item.get("subtotal", 0.00)

            cmds.append(self.ESC_BOLD_ON)
            cmds.append(f"{name}\r\n".encode())
            cmds.append(self.ESC_BOLD_OFF)

            cmds.append(f"  x{qty}  ${price:.2f}     ${subtotal:.2f}\r\n".encode())

        cmds.append(b"- " * 20 + b"\r\n")

        subtotal = receipt_data.get("subtotal", 0.00)
        tax_amount = receipt_data.get("tax_amount", 0.00)
        total_amount = receipt_data.get("total_amount", 0.00)

        cmds.append(self.ESC_ALIGN_CENTER)
        cmds.append(self.ESC_BOLD_ON)
        cmds.append(f"Subtotal:         ${subtotal:.2f}\r\n".encode())
        cmds.append(f"Tax:              ${tax_amount:.2f}\r\n".encode())
        cmds.append(b"\r\n")
        cmds.append(self.ESC_DOUBLE_HEIGHT_ON)
        cmds.append(f"TOTAL:            ${total_amount:.2f}\r\n".encode())
        cmds.append(self.ESC_DOUBLE_HEIGHT_OFF)
        cmds.append(self.ESC_BOLD_OFF)

        cmds.append(b"\r\n")

        cmds.append(self.ESC_ALIGN_CENTER)
        cmds.append(f"Payment: {receipt_data.get('payment_method', 'N/A')}\r\n".encode())

        card_last_four = receipt_data.get("card_last_four")
        if card_last_four:
            cmds.append(f"Card: **** {card_last_four}\r\n".encode())

        authorization_code = receipt_data.get("authorization_code")
        if authorization_code:
            cmds.append(f"Auth: {authorization_code}\r\n".encode())

        cmds.append(b"\r\n")
        cmds.append(b"* THANK YOU FOR SHOPPING *\r\n")
        cmds.append(b"*   PLEASE COME AGAIN    *\r\n")
        cmds.append(b"\r\n\r\n")

        cmds.append(self.ESC_CUT_PAPER)

        return b"".join(cmds)

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
                <td style="text-align: center;">{item.get('quantity', 0)}</td>
                <td style="text-align: right;">${item.get('price', 0.00):.2f}</td>
                <td style="text-align: right;">${item.get('subtotal', 0.00):.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ESCPOS Preview - {receipt_data.get('receipt_number', 'N/A')}</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    background-color: #f0f0f0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                }}
                .receipt {{
                    background: white;
                    width: 300px;
                    padding: 20px;
                    border: 1px solid #ccc;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 1px dashed #000;
                    padding-bottom: 10px;
                    margin-bottom: 10px;
                }}
                .header h1 {{ font-size: 16px; margin: 0; }}
                .info p {{ margin: 2px 0; font-size: 12px; }}
                .items table {{ width: 100%; font-size: 11px; border-collapse: collapse; }}
                .items th {{ text-align: left; border-bottom: 1px solid #000; padding: 4px 0; }}
                .items td {{ padding: 3px 0; }}
                .totals {{ margin-top: 10px; text-align: right; font-size: 12px; }}
                .total {{ font-weight: bold; font-size: 14px; }}
                .footer {{
                    text-align: center;
                    border-top: 1px dashed #000;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-size: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="receipt">
                <div class="header">
                    <h1>FASHIONVISION AI</h1>
                    <p>[ESCPOS PREVIEW]</p>
                </div>
                <div class="info">
                    <p><strong>Receipt #:</strong> {receipt_data.get('receipt_number', 'N/A')}</p>
                    <p><strong>Order #:</strong> {receipt_data.get('order_number', 'N/A')}</p>
                    <p><strong>Date:</strong> {receipt_data.get('created_at', 'N/A')}</p>
                    <p><strong>Cashier:</strong> {receipt_data.get('cashier', 'N/A')}</p>
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
                    <p class="total">TOTAL: ${receipt_data.get('total_amount', 0.00):.2f}</p>
                </div>
                <div class="footer">
                    <p>Payment: {receipt_data.get('payment_method', 'N/A')}</p>
                    <p>*** THANK YOU ***</p>
                    <p><em>[This is an ESCPOS preview - will print to thermal printer]</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        return html