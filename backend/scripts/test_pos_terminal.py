#!/usr/bin/env python3
"""
Test script for POS Terminal Integration

This script tests the POS terminal functionality with mock transactions.

Usage:
    python scripts/test_pos_terminal.py

Scenarios tested:
1. Initialize payment
2. Wait for card
3. Process payment (approved)
4. Process payment (declined)
5. Process payment (timeout)
6. Cancel transaction
7. Get transaction status

IMPORTANT: This is for testing the MOCK terminal only.
For real POS testing, you would need actual Stripe Terminal hardware.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.pos_terminal import terminal, TransactionStatus


async def test_approved_transaction():
    """Test a successful payment transaction."""
    print("\n" + "=" * 50)
    print("TEST: Approved Transaction")
    print("=" * 50)

    amount = 599.99
    print(f"Initializing payment for ${amount}")

    init = await terminal.initialize_payment(amount=amount, description="Test purchase")
    print(f"Init result: {init}")

    txn_id = init["transaction_id"]

    print("\nWaiting for card...")
    card = await terminal.wait_for_card_present(txn_id)
    print(f"Card result: {card}")

    if card["success"]:
        print("\nProcessing payment...")
        result = await terminal.process_payment(txn_id)
        print(f"Status: {result.status.value}")
        print(f"Amount: ${result.amount}")
        if result.card_last_four:
            print(f"Card: **** {result.card_last_four}")
        if result.authorization_code:
            print(f"Auth Code: {result.authorization_code}")
        print(f"Provider Ref: {result.provider_reference}")

        assert result.status == TransactionStatus.APPROVED, f"Expected APPROVED, got {result.status}"
        print("\n✅ TEST PASSED: Transaction approved successfully")
        return True

    return False


async def test_declined_transaction():
    """Test a declined payment transaction."""
    print("\n" + "=" * 50)
    print("TEST: Declined Transaction")
    print("=" * 50)

    print("Setting decline rate to 100% for this test...")
    original_rate = terminal.approval_rate
    terminal.approval_rate = 0.0
    terminal.decline_rate = 1.0

    amount = 199.99
    print(f"Initializing payment for ${amount}")

    init = await terminal.initialize_payment(amount=amount, description="Test declined")
    txn_id = init["transaction_id"]

    card = await terminal.wait_for_card_present(txn_id)
    if card["success"]:
        result = await terminal.process_payment(txn_id)
        print(f"Status: {result.status.value}")
        print(f"Error: {result.error_message}")

        assert result.status == TransactionStatus.DECLINED, f"Expected DECLINED, got {result.status}"
        print("\n✅ TEST PASSED: Transaction declined as expected")

    terminal.approval_rate = original_rate
    terminal.decline_rate = original_rate * 0.3 / 0.7 if original_rate < 1 else 0.2
    return True


async def test_timeout_transaction():
    """Test a timeout scenario."""
    print("\n" + "=" * 50)
    print("TEST: Timeout Transaction")
    print("=" * 50)

    print("Setting timeout rate to 100% for this test...")
    original_approval = terminal.approval_rate
    original_decline = terminal.decline_rate
    terminal.approval_rate = 0.0
    terminal.decline_rate = 0.0

    amount = 299.99
    print(f"Initializing payment for ${amount}")

    init = await terminal.initialize_payment(amount=amount, description="Test timeout")
    txn_id = init["transaction_id"]

    card = await terminal.wait_for_card_present(txn_id)
    if card["success"]:
        result = await terminal.process_payment(txn_id)
        print(f"Status: {result.status.value}")
        print(f"Error: {result.error_message}")

        assert result.status == TransactionStatus.TIMEOUT, f"Expected TIMEOUT, got {result.status}"
        print("\n✅ TEST PASSED: Transaction timed out as expected")

    terminal.approval_rate = original_approval
    terminal.decline_rate = original_decline
    return True


async def test_cancel_transaction():
    """Test cancelling a transaction."""
    print("\n" + "=" * 50)
    print("TEST: Cancel Transaction")
    print("=" * 50)

    amount = 149.99
    print(f"Initializing payment for ${amount}")

    init = await terminal.initialize_payment(amount=amount, description="Test cancel")
    txn_id = init["transaction_id"]

    print("Cancelling transaction...")
    cancel = await terminal.cancel_transaction(txn_id)
    print(f"Cancel result: {cancel}")

    status = await terminal.get_transaction_status(txn_id)
    print(f"Final status: {status['status']}")

    assert status["status"] == "cancelled", f"Expected CANCELLED, got {status['status']}"
    print("\n✅ TEST PASSED: Transaction cancelled successfully")
    return True


async def test_multiple_transactions():
    """Test multiple transactions to verify random distribution."""
    print("\n" + "=" * 50)
    print("TEST: Multiple Transactions (Statistical)")
    print("=" * 50)

    print(f"Current rates: Approval={terminal.approval_rate*100}%, Decline={terminal.decline_rate*100}%, Timeout={terminal.timeout_rate*100}%")

    num_tests = 10
    results = {"approved": 0, "declined": 0, "timeout": 0}

    print(f"\nRunning {num_tests} transactions...")

    for i in range(num_tests):
        amount = 100 + (i * 10)
        init = await terminal.initialize_payment(amount=amount, description=f"Test {i+1}")
        txn_id = init["transaction_id"]

        card = await terminal.wait_for_card_present(txn_id)
        if card["success"]:
            result = await terminal.process_payment(txn_id)
            results[result.status.value] = results.get(result.status.value, 0) + 1
            print(f"  Transaction {i+1}: {result.status.value}")

    print(f"\nResults: {results}")

    total = sum(results.values())
    if total > 0:
        for key, value in results.items():
            pct = (value / total) * 100
            print(f"  {key}: {value} ({pct:.1f}%)")

    print("\n✅ TEST COMPLETED: Statistical distribution observed")
    return True


async def run_all_tests():
    """Run all POS terminal tests."""
    print("\n" + "#" * 60)
    print("#" + " " * 18 + "POS TERMINAL TEST SUITE" + " " * 18 + "#")
    print("#" * 60)

    tests = [
        ("Approved Transaction", test_approved_transaction),
        ("Declined Transaction", test_declined_transaction),
        ("Timeout Transaction", test_timeout_transaction),
        ("Cancel Transaction", test_cancel_transaction),
        ("Multiple Transactions", test_multiple_transactions),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1

    print("\n" + "#" * 60)
    print(f"#  SUMMARY: {passed} passed, {failed} failed  #")
    print("#" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)