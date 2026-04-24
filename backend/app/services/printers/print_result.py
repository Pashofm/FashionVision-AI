"""
Print Result Data Class

This module defines the result returned by printer driver operations,
containing success status, message, and optional metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PrintResult:
    """
    Result of a print operation from a printer driver.

    Attributes:
        success: Whether the print operation succeeded
        message: Human-readable result message
        driver_type: The driver type that performed the operation
        output_path: File path or identifier of the output (if applicable)
        print_duration_ms: Time taken to complete the print operation
        error_code: Optional error code if success is False
        metadata: Additional driver-specific data
    """
    success: bool
    message: str
    driver_type: str
    output_path: Optional[str] = None
    print_duration_ms: Optional[int] = None
    error_code: Optional[str] = None
    metadata: Optional[dict] = None
    printed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.printed_at is None and self.success:
            self.printed_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert PrintResult to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "driver_type": self.driver_type,
            "output_path": self.output_path,
            "print_duration_ms": self.print_duration_ms,
            "error_code": self.error_code,
            "metadata": self.metadata,
            "printed_at": self.printed_at.isoformat() if self.printed_at else None
        }