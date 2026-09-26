"""drop_yolo_and_legacy_columns

Revision ID: 003_drop_yolo
Revises: ce260a16d612
Create Date: 2026-05-27 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_drop_yolo"
down_revision: Union[str, None] = "ce260a16d612"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("DROP INDEX IF EXISTS idx_products_yolo")
    op.execute("DROP INDEX IF EXISTS idx_products_yolo_class_name")
    op.drop_column("products", "yolo_class_id")
    op.drop_column("products", "yolo_class_name")
    op.drop_column("products", "min_stock_level")
    op.drop_column("products", "max_stock_level")


def downgrade():
    op.add_column("products", sa.Column("yolo_class_id", sa.Integer, nullable=True, unique=True))
    op.add_column("products", sa.Column("yolo_class_name", sa.String(100), nullable=True, unique=True))
    op.add_column("products", sa.Column("min_stock_level", sa.Integer, nullable=False, server_default="0"))
    op.add_column("products", sa.Column("max_stock_level", sa.Integer, nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_yolo ON products(yolo_class_name) WHERE yolo_class_name IS NOT NULL")
