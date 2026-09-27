"""Reconcile order item snapshots with the ORM model.

Revision ID: 004_reconcile_order_items
Revises: 003_drop_yolo
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_reconcile_order_items"
down_revision: Union[str, None] = "003_drop_yolo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_name VARCHAR(200)")
    op.execute("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS variant_description VARCHAR(100)")
    op.execute(
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS "
        "discount_applied NUMERIC(10, 2) NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS subtotal NUMERIC(10, 2)")

    op.execute(
        """
        UPDATE order_items
        SET product_name = products.name
        FROM products
        WHERE products.id = order_items.product_id
          AND order_items.product_name IS NULL
        """
    )
    op.execute(
        """
        UPDATE order_items
        SET subtotal = unit_price * quantity
        WHERE subtotal IS NULL
        """
    )

    op.alter_column("order_items", "product_name", nullable=False)
    op.alter_column("order_items", "subtotal", nullable=False)
    op.alter_column("order_items", "discount_applied", server_default=None)


def downgrade() -> None:
    op.drop_column("order_items", "subtotal")
    op.drop_column("order_items", "discount_applied")
    op.drop_column("order_items", "variant_description")
    op.drop_column("order_items", "product_name")
