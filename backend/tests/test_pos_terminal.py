import pytest
import asyncio
from backend.app.services.pos_terminal import (
    MockPOSTerminal, TransactionStatus, TransactionResult
)


class TestMockPOSTerminal:
    @pytest.fixture
    def terminal(self):
        return MockPOSTerminal(approval_rate=0.70, decline_rate=0.20, timeout_rate=0.10)

    @pytest.mark.asyncio
    async def test_initialize_payment_creates_transaction(self, terminal):
        result = await terminal.initialize_payment(amount=100.00, currency="MXN")

        assert result["success"] is True
        assert "transaction_id" in result
        assert result["status"] == TransactionStatus.WAITING_CARD.value
        assert result["amount"] == 100.00
        assert result["currency"] == "MXN"

    @pytest.mark.asyncio
    async def test_initialize_payment_unique_ids(self, terminal):
        result1 = await terminal.initialize_payment(amount=100.00)
        result2 = await terminal.initialize_payment(amount=200.00)

        assert result1["transaction_id"] != result2["transaction_id"]

    @pytest.mark.asyncio
    async def test_wait_for_card_success(self, terminal):
        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        card_result = await terminal.wait_for_card_present(txn_id)

        assert card_result["success"] is True
        assert card_result["status"] == TransactionStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_wait_for_card_invalid_transaction(self, terminal):
        result = await terminal.wait_for_card_present("invalid-txn-id")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_process_payment_completes(self, terminal):
        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        await terminal.wait_for_card_present(txn_id)
        result = await terminal.process_payment(txn_id)

        assert result.status in [
            TransactionStatus.APPROVED,
            TransactionStatus.DECLINED,
            TransactionStatus.TIMEOUT
        ]
        assert result.transaction_id == txn_id
        assert result.amount == 100.00

    @pytest.mark.asyncio
    async def test_process_payment_invalid_transaction(self, terminal):
        result = await terminal.process_payment("invalid-txn-id")

        assert result.status == TransactionStatus.DECLINED

    @pytest.mark.asyncio
    async def test_cancel_transaction(self, terminal):
        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        cancel_result = await terminal.cancel_transaction(txn_id)

        assert cancel_result["success"] is True
        assert cancel_result["status"] == TransactionStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_invalid_transaction(self, terminal):
        result = await terminal.cancel_transaction("invalid-txn-id")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_transaction_status(self, terminal):
        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        status = await terminal.get_transaction_status(txn_id)

        assert status["success"] is True
        assert status["transaction_id"] == txn_id
        assert status["status"] == TransactionStatus.WAITING_CARD.value

    @pytest.mark.asyncio
    async def test_get_transaction_result(self, terminal):
        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        await terminal.wait_for_card_present(txn_id)
        process_result = await terminal.process_payment(txn_id)

        result = terminal.get_transaction_result(txn_id)

        assert result is not None
        assert result.status == process_result.status

    @pytest.mark.asyncio
    async def test_approved_transaction_has_auth_code(self, terminal):
        terminal.approval_rate = 1.0
        terminal.decline_rate = 0.0
        terminal.timeout_rate = 0.0

        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        await terminal.wait_for_card_present(txn_id)
        result = await terminal.process_payment(txn_id)

        assert result.status == TransactionStatus.APPROVED
        assert result.authorization_code is not None
        assert result.provider_reference is not None

    @pytest.mark.asyncio
    async def test_declined_transaction_has_error(self, terminal):
        terminal.approval_rate = 0.0
        terminal.decline_rate = 1.0
        terminal.timeout_rate = 0.0

        init_result = await terminal.initialize_payment(amount=100.00)
        txn_id = init_result["transaction_id"]

        await terminal.wait_for_card_present(txn_id)
        result = await terminal.process_payment(txn_id)

        assert result.status == TransactionStatus.DECLINED
        assert result.error_message is not None


class TestTransactionResult:
    def test_to_dict(self):
        result = TransactionResult(
            status=TransactionStatus.APPROVED,
            transaction_id="TXN-123",
            amount=100.00,
            card_last_four="4242",
            authorization_code="AUTH-123456",
            provider_reference="REF-ABC"
        )

        data = result.to_dict()

        assert data["status"] == "approved"
        assert data["transaction_id"] == "TXN-123"
        assert data["amount"] == 100.00
        assert data["card_last_four"] == "4242"
        assert data["authorization_code"] == "AUTH-123456"
        assert data["provider_reference"] == "REF-ABC"
        assert "timestamp" in data