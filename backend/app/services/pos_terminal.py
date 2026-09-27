"""
Mock POS Terminal Service for FashionVision AI

This module simulates a Point of Sale (POS) terminal for card payments.
It mimics the behavior of real payment terminals like Stripe Terminal.

IMPORTANT: This is a MOCK implementation for testing purposes.
In production, replace with actual Stripe Terminal SDK or other payment provider.

Flow:
1. POS initializes payment -> returns transaction_id
2. POS waits for card
3. POS processes payment
4. POS returns result (approved/declined)

For testing, the mock returns:
- 70% chance of approval
- 20% chance of decline
- 10% chance of timeout
"""

import uuid
import random
import asyncio
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal


class TransactionStatus(str, Enum):
    PENDING = "pending"
    WAITING_CARD = "waiting_card"
    PROCESSING = "processing"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TransactionResult:
    def __init__(
        self,
        status: TransactionStatus,
        transaction_id: str,
        amount: float,
        card_last_four: Optional[str] = None,
        authorization_code: Optional[str] = None,
        error_message: Optional[str] = None,
        provider_reference: Optional[str] = None
    ):
        self.status = status
        self.transaction_id = transaction_id
        self.amount = amount
        self.card_last_four = card_last_four
        self.authorization_code = authorization_code
        self.error_message = error_message
        self.provider_reference = provider_reference

    def to_dict(self):
        return {
            "status": self.status.value,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "card_last_four": self.card_last_four,
            "authorization_code": self.authorization_code,
            "error_message": self.error_message,
            "provider_reference": self.provider_reference,
            "timestamp": datetime.utcnow().isoformat()
        }


class MockPOSTerminal:
    """
    Mock POS Terminal that simulates card payment processing.

    Configuration:
    - approval_rate: Percentage of transactions that get approved (default: 0.70)
    - decline_rate: Percentage that get declined (default: 0.20)
    - timeout_rate: Percentage that timeout (default: 0.10)
    """

    def __init__(
        self,
        terminal_id: str = "MOCK-POS-001",
        approval_rate: float = 0.70,
        decline_rate: float = 0.20,
        timeout_rate: float = 0.10
    ):
        self.terminal_id = terminal_id
        self.approval_rate = approval_rate
        self.decline_rate = decline_rate
        self.timeout_rate = timeout_rate
        self._active_transactions = {}

    def _generate_transaction_id(self) -> str:
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"

    def _generate_auth_code(self) -> str:
        return f"AUTH-{random.randint(100000, 999999)}"

    def _generate_provider_ref(self) -> str:
        return f"REF-{uuid.uuid4().hex[:8].upper()}"

    def _simulate_card_present(self) -> bool:
        return random.random() < 0.85

    def _simulate_card_read(self) -> Optional[str]:
        if random.random() < 0.95:
            return f"{random.randint(1000, 9999)}"
        return None

    async def initialize_payment(
        self,
        amount: float,
        currency: str = "MXN",
        description: str = ""
    ) -> dict:
        """
        Initialize a new payment transaction.

        Args:
            amount: Amount to charge
            currency: Currency code (default: MXN)
            description: Optional description

        Returns:
            dict with transaction_id and status
        """
        await asyncio.sleep(0.1)

        transaction_id = self._generate_transaction_id()

        self._active_transactions[transaction_id] = {
            "amount": amount,
            "currency": currency,
            "description": description,
            "status": TransactionStatus.WAITING_CARD,
            "created_at": datetime.utcnow()
        }

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": TransactionStatus.WAITING_CARD.value,
            "amount": amount,
            "currency": currency,
            "message": "Waiting for card..."
        }

    async def wait_for_card_present(self, transaction_id: str) -> dict:
        """
        Simulate waiting for card to be presented.

        Returns:
            dict with card status
        """
        if transaction_id not in self._active_transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }

        await asyncio.sleep(0.5)

        if not self._simulate_card_present():
            return {
                "success": False,
                "transaction_id": transaction_id,
                "status": TransactionStatus.TIMEOUT.value,
                "error": "Card not detected. Please present card."
            }

        self._active_transactions[transaction_id]["status"] = TransactionStatus.PROCESSING

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": TransactionStatus.PROCESSING.value,
            "message": "Card detected. Processing..."
        }

    async def process_payment(self, transaction_id: str) -> TransactionResult:
        """
        Process the payment after card is detected.

        Returns:
            TransactionResult with final status
        """
        if transaction_id not in self._active_transactions:
            return TransactionResult(
                status=TransactionStatus.DECLINED,
                transaction_id=transaction_id,
                amount=0,
                error_message="Transaction not found"
            )

        tx = self._active_transactions[transaction_id]
        await asyncio.sleep(1.5)

        random_value = random.random()
        if random_value < self.approval_rate:
            card_last_four = self._simulate_card_read()
            result = TransactionResult(
                status=TransactionStatus.APPROVED,
                transaction_id=transaction_id,
                amount=tx["amount"],
                card_last_four=card_last_four,
                authorization_code=self._generate_auth_code(),
                provider_reference=self._generate_provider_ref()
            )
        elif random_value < self.approval_rate + self.decline_rate:
            result = TransactionResult(
                status=TransactionStatus.DECLINED,
                transaction_id=transaction_id,
                amount=tx["amount"],
                error_message="Transaction declined by issuer"
            )
        else:
            result = TransactionResult(
                status=TransactionStatus.TIMEOUT,
                transaction_id=transaction_id,
                amount=tx["amount"],
                error_message="Transaction timeout"
            )

        self._active_transactions[transaction_id]["status"] = result.status
        self._active_transactions[transaction_id]["result"] = result

        return result

    async def cancel_transaction(self, transaction_id: str) -> dict:
        """
        Cancel an active transaction.
        """
        if transaction_id not in self._active_transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }

        self._active_transactions[transaction_id]["status"] = TransactionStatus.CANCELLED

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": TransactionStatus.CANCELLED.value,
            "message": "Transaction cancelled"
        }

    async def get_transaction_status(self, transaction_id: str) -> dict:
        """
        Get the current status of a transaction.
        """
        if transaction_id not in self._active_transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }

        tx = self._active_transactions[transaction_id]

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": tx["status"].value,
            "amount": tx["amount"],
            "created_at": tx["created_at"].isoformat()
        }

    def get_transaction_result(self, transaction_id: str) -> Optional[TransactionResult]:
        """Get the full result of a completed transaction."""
        if transaction_id in self._active_transactions:
            return self._active_transactions[transaction_id].get("result")
        return None


terminal = MockPOSTerminal()


async def test_pos_terminal():
    """Test script to demonstrate POS terminal functionality."""
    print("=" * 60)
    print("MOCK POS TERMINAL TEST")
    print("=" * 60)

    test_amount = 599.99

    print(f"\n1. Initializing payment for ${test_amount}")
    init_result = await terminal.initialize_payment(
        amount=test_amount,
        description="FashionVision Purchase"
    )
    print(f"   Result: {init_result}")

    txn_id = init_result["transaction_id"]

    print(f"\n2. Waiting for card...")
    card_result = await terminal.wait_for_card_present(txn_id)
    print(f"   Result: {card_result}")

    if card_result["success"]:
        print(f"\n3. Processing payment...")
        final_result = await terminal.process_payment(txn_id)
        print(f"   Status: {final_result.status.value}")
        print(f"   Amount: ${final_result.amount}")
        if final_result.card_last_four:
            print(f"   Card: **** {final_result.card_last_four}")
        if final_result.authorization_code:
            print(f"   Auth Code: {final_result.authorization_code}")
        if final_result.error_message:
            print(f"   Error: {final_result.error_message}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_pos_terminal())