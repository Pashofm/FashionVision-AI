"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-05-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text, nullable=False),
        sa.Column('role', sa.Enum('admin', 'cashier', 'client', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('avatar_path', sa.Text, nullable=True),
        sa.Column('last_logout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])

    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table('store_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_name', sa.String(200), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('default_currency', sa.String(3), nullable=False),
        sa.Column('default_payment_method', sa.Enum('cash', 'card', 'mixed', name='payment_method'), nullable=False),
        sa.Column('receipt_footer', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table('suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('contact_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table('attribute_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('value', sa.String(50), nullable=False),
        sa.Column('hex_code', sa.String(7), nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('type', 'value', name='uq_attribute_type_value'),
    )

    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('sku', sa.String(100), nullable=False, unique=True),
        sa.Column('base_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('cost_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('profit_margin', sa.Numeric(5, 4), nullable=False),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('supplier', sa.String(150), nullable=True),
        sa.Column('barcode', sa.String(50), nullable=True, unique=True),
        sa.Column('weight', sa.Numeric(8, 2), nullable=True),
        sa.Column('width', sa.Numeric(8, 2), nullable=True),
        sa.Column('height', sa.Numeric(8, 2), nullable=True),
        sa.Column('depth', sa.Numeric(8, 2), nullable=True),
        sa.Column('min_stock_level', sa.Integer, nullable=False),
        sa.Column('max_stock_level', sa.Integer, nullable=True),
        sa.Column('is_featured', sa.Boolean, nullable=False, default=False),
        sa.Column('tags', postgresql.JSONB, nullable=False),
        sa.Column('yolo_class_id', sa.Integer, nullable=True, unique=True),
        sa.Column('yolo_class_name', sa.String(100), nullable=True, unique=True),
        sa.Column('images', postgresql.JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
    )
    op.create_index('idx_products_name_trgm', 'products', [sa.text('name gin_trgm_ops)')], postgresql_using='gin')
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_yolo', 'products', ['yolo_class_name'], unique=False, where=sa.text('yolo_class_name IS NOT NULL'))
    op.create_index('idx_products_active', 'products', ['is_active'], unique=False, where=sa.text('is_active = TRUE'))

    op.create_table('product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('size_attribute_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('color_attribute_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('color_hex', sa.String(7), nullable=True),
        sa.Column('sku_variant', sa.String(150), nullable=False, unique=True),
        sa.Column('price_modifier', sa.Numeric(10, 2), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['size_attribute_id'], ['attribute_options.id']),
        sa.ForeignKeyConstraint(['color_attribute_id'], ['attribute_options.id']),
        sa.UniqueConstraint('product_id', 'size_attribute_id', 'color_attribute_id', name='uq_product_size_color'),
    )
    op.create_index('idx_variants_product', 'product_variants', ['product_id'])
    op.create_index('idx_variants_sku', 'product_variants', ['sku_variant'])
    op.create_index('idx_variants_size', 'product_variants', ['size_attribute_id'])
    op.create_index('idx_variants_color', 'product_variants', ['color_attribute_id'])

    op.create_table('product_attributes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribute_option_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['attribute_option_id'], ['attribute_options.id']),
        sa.UniqueConstraint('product_id', 'attribute_option_id', name='uq_product_attribute'),
    )

    op.create_table('price_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('price_type', sa.String(20), nullable=False),
        sa.Column('old_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('new_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )

    op.create_table('inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('quantity_available', sa.Integer, nullable=False),
        sa.Column('quantity_reserved', sa.Integer, nullable=False),
        sa.Column('low_stock_threshold', sa.Integer, nullable=False),
        sa.Column('stock_status', sa.Enum('available', 'reserved', 'damaged', 'in_transit', 'returned', name='stock_status'), nullable=False),
        sa.Column('warehouse_location', sa.String(100), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
    )
    op.create_index('idx_inventory_variant', 'inventory', ['product_variant_id'])
    op.create_index('idx_inventory_status', 'inventory', ['stock_status'])
    op.create_index('idx_inventory_low_stock', 'inventory', [sa.text('low_stock_threshold) WHERE quantity_available <= low_stock_threshold')], postgresql_using='btree')

    op.create_table('inventory_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('movement_type', sa.Enum('sale', 'restock', 'adjustment', 'return', 'reserved', 'released', name='movement_type'), nullable=False),
        sa.Column('quantity_change', sa.Integer, nullable=False),
        sa.Column('quantity_before', sa.Integer, nullable=False),
        sa.Column('quantity_after', sa.Integer, nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
    )
    op.create_index('idx_movements_variant', 'inventory_movements', ['product_variant_id'])
    op.create_index('idx_movements_type', 'inventory_movements', ['movement_type'])
    op.create_index('idx_movements_created_at', 'inventory_movements', [sa.text('created_at DESC')])
    op.create_index('idx_movements_reference', 'inventory_movements', ['reference_id'], unique=False, where=sa.text('reference_id IS NOT NULL'))

    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_token', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('client_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('station_id', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('active', 'completed', 'abandoned', name='session_status'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_user_id'], ['users.id']),
    )
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_client_user', 'sessions', ['client_user_id'])
    op.create_index('idx_sessions_token', 'sessions', ['session_token'])

    op.create_table('carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('building', 'submitted', 'processing', 'paid', 'cancelled', name='cart_status'), nullable=False),
        sa.Column('payment_method', sa.Enum('cash', 'card', 'mixed', name='payment_method'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
    )
    op.create_index('idx_carts_session', 'carts', ['session_id'])
    op.create_index('idx_carts_status', 'carts', ['status'])

    op.create_table('cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('confirmed', sa.Boolean, nullable=False, default=False),
        sa.Column('detected_class', sa.String(100), nullable=True),
        sa.Column('detection_confidence', sa.Float, nullable=True),
        sa.Column('detection_image_path', sa.Text, nullable=True),
        sa.Column('detection_bbox', postgresql.JSONB, nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
    )
    op.create_index('idx_cart_items_cart', 'cart_items', ['cart_id'])
    op.create_index('idx_cart_items_variant', 'cart_items', ['product_variant_id'])
    op.create_index('idx_cart_items_product', 'cart_items', ['product_id'])

    op.create_table('orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cashier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('payment_method', sa.String(20), nullable=False),
        sa.Column('cash_received', sa.Numeric(10, 2), nullable=True),
        sa.Column('change_given', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.Enum('pending', 'completed', 'refunded', 'partially_refunded', name='order_status'), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id']),
        sa.ForeignKeyConstraint(['cashier_id'], ['users.id']),
    )
    op.create_index('idx_orders_number', 'orders', ['order_number'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_cashier', 'orders', ['cashier_id'])
    op.create_index('idx_orders_created_at', 'orders', [sa.text('created_at DESC')])

    op.create_table('order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('variant_description', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('cost_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['product_variant_id'], ['product_variants.id']),
    )
    op.create_index('idx_order_items_order', 'order_items', ['order_id'])
    op.create_index('idx_order_items_variant', 'order_items', ['product_variant_id'])

    op.create_table('receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('receipt_number', sa.String(50), nullable=False, unique=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receipt_data', postgresql.JSONB, nullable=True),
        sa.Column('pdf_path', sa.String(255), nullable=True),
        sa.Column('printed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('printer_name', sa.String(100), nullable=True),
        sa.Column('emailed_to', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
    )
    op.create_index('idx_receipts_order', 'receipts', ['order_id'])

    op.create_table('payment_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('priority', sa.Enum('normal', 'urgent', name='queue_priority'), nullable=False),
        sa.Column('queue_position', sa.Integer, nullable=False),
        sa.Column('status', sa.Enum('waiting', 'in_progress', 'completed', 'skipped', name='queue_status'), nullable=False),
        sa.Column('station_id', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('called_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
    )
    op.create_index('idx_payment_queue_status', 'payment_queue', ['status'])
    op.create_index('idx_payment_queue_priority', 'payment_queue', ['priority'])
    op.create_index('idx_payment_queue_status_position', 'payment_queue', ['status', 'queue_position'], unique=False, where=sa.text("status = 'waiting'"))

    op.create_table('daily_sales_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('summary_date', sa.Date(), nullable=False, unique=True),
        sa.Column('total_orders', sa.Integer, nullable=False),
        sa.Column('total_revenue', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_items_sold', sa.Integer, nullable=False),
        sa.Column('payment_method_breakdown', postgresql.JSONB, nullable=False),
        sa.Column('top_products', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_daily_summary_date', 'daily_sales_summary', [sa.text('summary_date DESC')])

    op.execute('GRANT USAGE ON SCHEMA public TO fashionvision_ai_user')
    op.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashionvision_ai_user')
    op.execute('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fashionvision_ai_user')
    op.execute('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO fashionvision_ai_user')


def downgrade() -> None:
    pass