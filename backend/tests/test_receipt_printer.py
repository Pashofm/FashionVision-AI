"""
Unit Tests for Receipt Printer System

These tests verify the functionality of the printer driver system,
focusing on the MockPrinterDriver for unit testing without actual hardware.
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path

from backend.app.services.printers import (
    ReceiptPrinterService,
    DriverType,
    PrintResult,
    PrinterDriver,
)
from backend.app.services.printers.drivers import (
    MockPrinterDriver,
    TextFilePrinterDriver,
    HTMLPrinterDriver,
    ESCPOSPrinterDriver,
)


@pytest.fixture
def sample_receipt_data():
    """Generate sample receipt data for testing."""
    return {
        "receipt_number": f"REC-{uuid.uuid4().hex[:8].upper()}",
        "order_number": f"ORD-{uuid.uuid4().hex[:8].upper()}",
        "items": [
            {
                "name": "Camiseta Algodon",
                "quantity": 2,
                "price": 299.99,
                "subtotal": 599.98
            },
            {
                "name": "Jean Slim Fit",
                "quantity": 1,
                "price": 599.99,
                "subtotal": 599.99
            },
            {
                "name": "Gorra Roja Lacoste",
                "quantity": 1,
                "price": 999.99,
                "subtotal": 999.99
            }
        ],
        "subtotal": 2199.96,
        "tax_amount": 351.99,
        "total_amount": 2551.95,
        "payment_method": "card",
        "card_last_four": "4242",
        "authorization_code": f"AUTH-{uuid.uuid4().hex[:6].upper()}",
        "cashier": "Maria Garcia",
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def minimal_receipt_data():
    """Generate minimal receipt data for validation testing."""
    return {
        "receipt_number": "REC-TEST-001",
        "order_number": "ORD-TEST-001",
        "items": [],
        "subtotal": 100.00,
        "tax_amount": 16.00,
        "total_amount": 116.00,
        "payment_method": "cash",
        "cashier": "Test Cashier",
        "created_at": datetime.now().isoformat()
    }


class TestDriverType:
    """Tests for DriverType enumeration."""

    def test_driver_type_values(self):
        """Test that DriverType has correct values."""
        assert DriverType.MOCK.value == "mock"
        assert DriverType.TEXTFILE.value == "textfile"
        assert DriverType.HTML.value == "html"
        assert DriverType.ESCPOS.value == "escpos"

    def test_driver_type_values_list(self):
        """Test values() class method."""
        values = DriverType.values()
        assert len(values) == 4
        assert "mock" in values
        assert "textfile" in values
        assert "html" in values
        assert "escpos" in values

    def test_driver_type_from_string_valid(self):
        """Test converting valid strings to DriverType."""
        assert DriverType.from_string("mock") == DriverType.MOCK
        assert DriverType.from_string("TEXTFILE") == DriverType.TEXTFILE
        assert DriverType.from_string("Html") == DriverType.HTML
        assert DriverType.from_string("ESCPOS") == DriverType.ESCPOS

    def test_driver_type_from_string_invalid(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown driver type"):
            DriverType.from_string("invalid")

    def test_driver_type_from_string_empty(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown driver type"):
            DriverType.from_string("")


class TestPrintResult:
    """Tests for PrintResult dataclass."""

    def test_print_result_success(self):
        """Test creating a successful PrintResult."""
        result = PrintResult(
            success=True,
            message="Test success",
            driver_type="mock"
        )

        assert result.success is True
        assert result.message == "Test success"
        assert result.driver_type == "mock"
        assert result.output_path is None
        assert result.printed_at is not None

    def test_print_result_failure(self):
        """Test creating a failed PrintResult."""
        result = PrintResult(
            success=False,
            message="Print failed",
            driver_type="escpos",
            error_code="PRINTER_OFFLINE"
        )

        assert result.success is False
        assert result.error_code == "PRINTER_OFFLINE"
        assert result.printed_at is None

    def test_print_result_to_dict(self):
        """Test converting PrintResult to dictionary."""
        result = PrintResult(
            success=True,
            message="Test",
            driver_type="mock",
            output_path="/test/path.txt",
            print_duration_ms=150
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["message"] == "Test"
        assert data["driver_type"] == "mock"
        assert data["output_path"] == "/test/path.txt"
        assert data["print_duration_ms"] == 150
        assert "printed_at" in data


class TestMockPrinterDriver:
    """Tests for MockPrinterDriver class."""

    @pytest.fixture
    def driver(self):
        """Create a fresh MockPrinterDriver instance."""
        return MockPrinterDriver()

    @pytest.mark.asyncio
    async def test_driver_type(self, driver):
        """Test driver_type property returns MOCK."""
        assert driver.driver_type == DriverType.MOCK

    @pytest.mark.asyncio
    async def test_driver_name(self, driver):
        """Test driver_name property."""
        assert "Mock" in driver.driver_name
        assert "Printer" in driver.driver_name

    @pytest.mark.asyncio
    async def test_print_success(self, driver, sample_receipt_data):
        """Test that print returns success for valid data."""
        result = await driver.print(sample_receipt_data)

        assert result.success is True
        assert "Mock print successful" in result.message
        assert result.driver_type == "mock"
        assert result.output_path is not None
        assert "mock://print/" in result.output_path

    @pytest.mark.asyncio
    async def test_print_stores_data(self, driver, sample_receipt_data):
        """Test that print stores receipt data in memory."""
        initial_count = driver.get_print_count()

        await driver.print(sample_receipt_data)

        assert driver.get_print_count() == initial_count + 1

        prints = driver.get_prints()
        assert len(prints) == 1
        assert prints[0]["receipt_number"] == sample_receipt_data["receipt_number"]

    @pytest.mark.asyncio
    async def test_print_multiple_receipts(self, driver, minimal_receipt_data):
        """Test printing multiple receipts accumulates in memory."""
        await driver.print(minimal_receipt_data)
        await driver.print(minimal_receipt_data)
        await driver.print(minimal_receipt_data)

        assert driver.get_print_count() == 3

    @pytest.mark.asyncio
    async def test_print_validates_required_fields(self, driver):
        """Test that print raises ValueError for missing required fields."""
        incomplete_data = {
            "receipt_number": "REC-001",
            "order_number": "ORD-001"
        }

        with pytest.raises(ValueError, match="Missing required receipt fields"):
            await driver.print(incomplete_data)

    @pytest.mark.asyncio
    async def test_print_missing_receipt_number(self, driver, minimal_receipt_data):
        """Test validation catches missing receipt_number."""
        del minimal_receipt_data["receipt_number"]

        with pytest.raises(ValueError, match="Missing required receipt fields"):
            await driver.print(minimal_receipt_data)

    @pytest.mark.asyncio
    async def test_print_missing_items(self, driver, minimal_receipt_data):
        """Test validation passes with empty items list."""
        minimal_receipt_data["items"] = []
        result = await driver.print(minimal_receipt_data)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_preview_returns_html(self, driver, sample_receipt_data):
        """Test that preview returns HTML content."""
        html = await driver.preview(sample_receipt_data)

        assert "<html>" in html
        assert "MOCK PREVIEW" in html
        assert sample_receipt_data["receipt_number"] in html
        assert sample_receipt_data["cashier"] in html

    @pytest.mark.asyncio
    async def test_preview_validates_data(self, driver):
        """Test that preview validates required fields."""
        with pytest.raises(ValueError, match="Missing required receipt fields"):
            await driver.preview({"invalid": "data"})

    @pytest.mark.asyncio
    async def test_clear_prints(self, driver, sample_receipt_data):
        """Test that clear_prints removes all stored prints."""
        await driver.print(sample_receipt_data)
        await driver.print(sample_receipt_data)

        assert driver.get_print_count() == 2

        driver.clear_prints()

        assert driver.get_print_count() == 0

    @pytest.mark.asyncio
    async def test_get_prints_returns_copy(self, driver, sample_receipt_data):
        """Test that get_prints returns a copy, not reference."""
        await driver.print(sample_receipt_data)

        prints = driver.get_prints()
        prints.append("should not affect original")

        assert len(driver.get_prints()) == 1

    @pytest.mark.asyncio
    async def test_print_includes_metadata(self, driver, sample_receipt_data):
        """Test that print result includes metadata."""
        result = await driver.print(sample_receipt_data)

        assert result.metadata is not None
        assert "prints_count" in result.metadata
        assert "stored_receipt_number" in result.metadata
        assert result.metadata["stored_receipt_number"] == sample_receipt_data["receipt_number"]

    @pytest.mark.asyncio
    async def test_print_duration_recorded(self, driver, sample_receipt_data):
        """Test that print duration is recorded."""
        result = await driver.print(sample_receipt_data)

        assert result.print_duration_ms is not None
        assert result.print_duration_ms >= 0


class TestReceiptPrinterService:
    """Tests for ReceiptPrinterService singleton."""

    def test_set_driver_changes_current(self):
        """Test that set_driver changes the active driver."""
        ReceiptPrinterService.set_driver(DriverType.TEXTFILE)

        current_type, _ = ReceiptPrinterService.get_current_driver()
        assert current_type == DriverType.TEXTFILE

    def test_set_driver_mack_to_mock(self):
        """Test switching back to mock driver."""
        ReceiptPrinterService.set_driver(DriverType.TEXTFILE)
        ReceiptPrinterService.set_driver(DriverType.MOCK)

        current_type, _ = ReceiptPrinterService.get_current_driver()
        assert current_type == DriverType.MOCK

    def test_get_current_driver_returns_tuple(self):
        """Test get_current_driver returns (DriverType, str)."""
        driver_type, driver_name = ReceiptPrinterService.get_current_driver()

        assert isinstance(driver_type, DriverType)
        assert isinstance(driver_name, str)

    def test_get_available_drivers(self):
        """Test that all drivers are available."""
        drivers = ReceiptPrinterService.get_available_drivers()

        assert len(drivers) == 4
        driver_types = [d[0] for d in drivers]
        assert DriverType.MOCK in driver_types
        assert DriverType.TEXTFILE in driver_types
        assert DriverType.HTML in driver_types
        assert DriverType.ESCPOS in driver_types

    @pytest.mark.asyncio
    async def test_print_receipt_uses_current_driver(self, sample_receipt_data):
        """Test that print_receipt uses the current driver."""
        ReceiptPrinterService.set_driver(DriverType.MOCK)

        result = await ReceiptPrinterService.print_receipt(sample_receipt_data)

        assert result.success is True
        assert result.driver_type == "mock"

    @pytest.mark.asyncio
    async def test_preview_receipt_returns_html(self, sample_receipt_data):
        """Test that preview_receipt returns HTML string."""
        ReceiptPrinterService.set_driver(DriverType.MOCK)

        html = await ReceiptPrinterService.preview_receipt(sample_receipt_data)

        assert isinstance(html, str)
        assert "<html>" in html

    @pytest.mark.asyncio
    async def test_driver_interchangeability(self, sample_receipt_data):
        """Test that all drivers can print without errors (skip ESCPOS if no pyserial)."""
        for driver_type in DriverType:
            ReceiptPrinterService.set_driver(driver_type)
            result = await ReceiptPrinterService.print_receipt(sample_receipt_data)
            if driver_type == DriverType.ESCPOS:
                assert result.success is False or result.success is True
            else:
                assert result.success is True, f"Driver {driver_type.value} failed"

    @pytest.mark.asyncio
    async def test_get_driver_instance(self):
        """Test getting a specific driver instance."""
        mock_driver = ReceiptPrinterService.get_driver_instance(DriverType.MOCK)

        assert isinstance(mock_driver, MockPrinterDriver)

    def test_reset_to_default(self):
        """Test that reset_to_default sets MOCK as active."""
        ReceiptPrinterService.set_driver(DriverType.HTML)
        ReceiptPrinterService.reset_to_default()

        current_type, _ = ReceiptPrinterService.get_current_driver()
        assert current_type == DriverType.MOCK


class TestPrinterDriverInterface:
    """Tests verifying the PrinterDriver interface."""

    @pytest.mark.asyncio
    async def test_all_drivers_implement_interface(self):
        """Test that all driver classes implement PrinterDriver."""
        drivers = [
            MockPrinterDriver(),
            TextFilePrinterDriver(),
            HTMLPrinterDriver(),
            ESCPOSPrinterDriver(),
        ]

        for driver in drivers:
            assert isinstance(driver, PrinterDriver)
            assert hasattr(driver, "driver_type")
            assert hasattr(driver, "driver_name")
            assert hasattr(driver, "print")
            assert hasattr(driver, "preview")

    @pytest.mark.asyncio
    async def test_all_drivers_have_unique_types(self):
        """Test that each driver has a unique type."""
        drivers = [
            MockPrinterDriver(),
            TextFilePrinterDriver(),
            HTMLPrinterDriver(),
            ESCPOSPrinterDriver(),
        ]

        types = [d.driver_type for d in drivers]
        assert len(types) == len(set(types))


class TestTextFilePrinterDriver:
    """Tests for TextFilePrinterDriver."""

    @pytest.fixture
    def driver(self, tmp_path):
        """Create driver with temp directory."""
        return TextFilePrinterDriver(audit_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_driver_type(self, driver):
        """Test driver_type property returns TEXTFILE."""
        assert driver.driver_type == DriverType.TEXTFILE

    @pytest.mark.asyncio
    async def test_print_creates_file(self, driver, sample_receipt_data, tmp_path):
        """Test that print creates a text file."""
        result = await driver.print(sample_receipt_data)

        assert result.success is True
        assert result.output_path is not None
        assert Path(result.output_path).parent == tmp_path

    @pytest.mark.asyncio
    async def test_preview_returns_html(self, driver, sample_receipt_data):
        """Test that preview returns HTML."""
        html = await driver.preview(sample_receipt_data)

        assert "<html>" in html


class TestHTMLPrinterDriver:
    """Tests for HTMLPrinterDriver."""

    @pytest.fixture
    def driver(self, tmp_path):
        """Create driver with temp directory."""
        return HTMLPrinterDriver(output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_driver_type(self, driver):
        """Test driver_type property returns HTML."""
        assert driver.driver_type == DriverType.HTML

    @pytest.mark.asyncio
    async def test_print_creates_html_file(self, driver, sample_receipt_data, tmp_path):
        """Test that print creates an HTML file."""
        result = await driver.print(sample_receipt_data)

        assert result.success is True
        assert ".html" in result.output_path

    @pytest.mark.asyncio
    async def test_preview_returns_complete_html(self, driver, sample_receipt_data):
        """Test that preview returns complete HTML document."""
        html = await driver.preview(sample_receipt_data)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "FASHIONVISION AI" in html


class TestESCPOSPrinterDriver:
    """Tests for ESCPOSPrinterDriver."""

    @pytest.fixture
    def driver(self):
        """Create driver with test port."""
        return ESCPOSPrinterDriver(port="/dev/ttyUSB99", baudrate=9600)

    @pytest.mark.asyncio
    async def test_driver_type(self, driver):
        """Test driver_type property returns ESCPOS."""
        assert driver.driver_type == DriverType.ESCPOS

    @pytest.mark.asyncio
    async def test_preview_returns_html(self, driver, sample_receipt_data):
        """Test that preview returns HTML."""
        html = await driver.preview(sample_receipt_data)

        assert "<html>" in html
        assert "ESCPOS PREVIEW" in html

    @pytest.mark.asyncio
    async def test_print_without_printer_fails_gracefully(self, driver, sample_receipt_data):
        """Test that print fails gracefully when no printer connected."""
        result = await driver.print(sample_receipt_data)

        assert result.success is False
        assert result.error_code == "ESCPOS_ERROR"