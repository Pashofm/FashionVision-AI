"""add_product_embeddings_table

Revision ID: ce260a16d612
Revises: 002_seed_data
Create Date: 2026-05-24 19:55:02.180988

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ce260a16d612"
down_revision: Union[str, None] = "002_seed_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "product_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("embedding", postgresql.JSONB, nullable=False),
        sa.Column("images_used", sa.Integer, nullable=False, server_default='0'),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table("product_embeddings")
