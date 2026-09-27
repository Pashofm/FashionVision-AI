"""Require positive cart item quantities.

Revision ID: 005_positive_cart_quantity
Revises: 004_reconcile_order_items
Create Date: 2026-09-27
"""

from typing import Sequence, Union

from alembic import op


revision: str = "005_positive_cart_quantity"
down_revision: Union[str, None] = "004_reconcile_order_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM cart_items WHERE quantity <= 0")
    op.create_check_constraint(
        "ck_cart_items_quantity_positive", "cart_items", "quantity > 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_cart_items_quantity_positive", "cart_items", type_="check")
