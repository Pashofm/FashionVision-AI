import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


def get_current_datetime() -> datetime:
    from backend.app.services.timezone_service import get_current_utc_time
    return get_current_utc_time()


class UserRole(str, Enum):
    admin = "admin"
    cashier = "cashier"
    client = "client"


class CartStatus(str, Enum):
    building = "building"
    submitted = "submitted"
    processing = "processing"
    paid = "paid"
    cancelled = "cancelled"


class OrderStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    partially_refunded = "partially_refunded"


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    mixed = "mixed"


class QueueStatus(str, Enum):
    waiting = "waiting"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class QueuePriority(str, Enum):
    normal = "normal"
    urgent = "urgent"


class MovementType(str, Enum):
    sale = "sale"
    restock = "restock"
    adjustment = "adjustment"
    return_item = "return"
    reserved = "reserved"
    released = "released"


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class StockStatus(str, Enum):
    available = "available"
    reserved = "reserved"
    damaged = "damaged"
    in_transit = "in_transit"
    returned = "returned"


class PriceType(str, Enum):
    cost = "cost"
    base = "base"
    special = "special"


class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.client


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductVariantBase(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    color_hex: Optional[str] = None
    sku_variant: str
    price_modifier: float = 0


class ProductVariantCreate(ProductVariantBase):
    product_id: uuid.UUID


class ProductVariantResponse(ProductVariantBase):
    id: uuid.UUID
    product_id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    sku: str
    base_price: float
    description: Optional[str] = None
    category_id: uuid.UUID
    cost_price: float = 0
    tax_rate: float = 0.16
    profit_margin: float = 0
    brand: Optional[str] = None
    supplier: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    min_stock_level: int = 0
    max_stock_level: Optional[int] = None
    is_featured: bool = False
    tags: List[str] = []
    yolo_class_id: Optional[int] = None
    yolo_class_name: Optional[str] = None
    images: List[str] = []


class ProductCreate(ProductBase):
    yolo_class_id: Optional[int] = None
    yolo_class_name: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    base_price: Optional[float] = None
    cost_price: Optional[float] = None
    tax_rate: Optional[float] = None
    profit_margin: Optional[float] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    category_id: Optional[uuid.UUID] = None
    yolo_class_id: Optional[int] = None
    yolo_class_name: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    selling_price: Optional[float] = None
    profit_per_unit: Optional[float] = None
    tax_amount_per_unit: Optional[float] = None

    class Config:
        from_attributes = True


class ProductWithVariantsResponse(ProductResponse):
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    product_variant_id: uuid.UUID
    quantity_available: int = 0
    quantity_reserved: int = 0
    low_stock_threshold: int = 5
    stock_status: StockStatus = StockStatus.available
    warehouse_location: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    quantity_available: Optional[int] = None
    quantity_reserved: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    stock_status: Optional[StockStatus] = None
    warehouse_location: Optional[str] = None


class InventoryResponse(InventoryBase):
    id: uuid.UUID
    last_updated: datetime

    class Config:
        from_attributes = True


class InventoryMovementBase(BaseModel):
    product_variant_id: uuid.UUID
    movement_type: MovementType
    quantity_change: int
    notes: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovementResponse(InventoryMovementBase):
    id: uuid.UUID
    quantity_before: int
    quantity_after: int
    reference_id: Optional[uuid.UUID]
    created_by: Optional[uuid.UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryAdjust(BaseModel):
    quantity_change: int
    reason: str
    reference_id: Optional[uuid.UUID] = None


class InventoryRestock(BaseModel):
    quantity: int
    notes: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None


class VariantWithInventory(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    size: Optional[str]
    color: Optional[str]
    color_hex: Optional[str]
    sku_variant: str
    price_modifier: float
    is_active: bool
    created_at: datetime
    inventory: Optional[InventoryResponse] = None

    class Config:
        from_attributes = True


class ProductWithStockResponse(ProductResponse):
    variants: List[VariantWithInventory] = []
    total_stock: int = 0
    has_low_stock: bool = False
    has_out_of_stock: bool = False

    class Config:
        from_attributes = True


class InventoryLowStockResponse(BaseModel):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    category_name: str
    sku: str
    sku_variant: str
    size: Optional[str]
    color: Optional[str]
    quantity_available: int
    quantity_reserved: int
    low_stock_threshold: int
    status: str

    class Config:
        from_attributes = True


class ProductVariantUpdate(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    color_hex: Optional[str] = None
    price_modifier: Optional[float] = None
    is_active: Optional[bool] = None


class ImageUploadResponse(BaseModel):
    success: bool
    public_id: str
    url: str


class SessionBase(BaseModel):
    station_id: Optional[str] = None


class SessionCreate(SessionBase):
    client_user_id: Optional[uuid.UUID] = None


class SessionResponse(SessionBase):
    id: uuid.UUID
    session_token: uuid.UUID
    client_user_id: Optional[uuid.UUID]
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class CartItemBase(BaseModel):
    product_id: uuid.UUID
    product_variant_id: Optional[uuid.UUID] = None
    quantity: int = 1
    unit_price: Optional[float] = None
    detection_confidence: Optional[float] = None
    detection_image_path: Optional[str] = None
    detection_bbox: Optional[dict] = None


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    confirmed: Optional[bool] = None


class CartItemResponse(CartItemBase):
    id: uuid.UUID
    cart_id: uuid.UUID
    confirmed: bool
    added_at: datetime
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    session_id: uuid.UUID
    status: CartStatus = CartStatus.building
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class CartCreate(CartBase):
    pass


class CartUpdate(BaseModel):
    status: Optional[CartStatus] = None
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class CartResponse(CartBase):
    id: uuid.UUID
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartWithItemsResponse(CartResponse):
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True


class CartWithTotal(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    status: CartStatus
    created_at: datetime
    items: List[CartItemResponse]
    total: float
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentQueueBase(BaseModel):
    cart_id: uuid.UUID
    priority: QueuePriority = QueuePriority.normal


class PaymentQueueCreate(PaymentQueueBase):
    pass


class PaymentQueueUpdate(BaseModel):
    priority: Optional[QueuePriority] = None
    status: Optional[QueueStatus] = None
    assigned_to: Optional[uuid.UUID] = None


class PaymentQueueResponse(PaymentQueueBase):
    id: uuid.UUID
    queue_position: int
    status: QueueStatus
    assigned_to: Optional[uuid.UUID]
    called_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    product_id: uuid.UUID
    product_variant_id: Optional[uuid.UUID] = None
    product_name: str
    variant_description: Optional[str] = None
    quantity: int
    unit_price: float
    discount_applied: float = 0
    subtotal: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    cart_id: uuid.UUID
    cashier_id: uuid.UUID
    subtotal: float
    discount_amount: float = 0
    tax_amount: float = 0
    total_amount: float
    payment_method: PaymentMethod
    cash_received: Optional[float] = None
    change_given: Optional[float] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderWithItemsResponse(OrderResponse):
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class ReceiptBase(BaseModel):
    order_id: uuid.UUID
    receipt_data: dict
    pdf_path: Optional[str] = None
    emailed_to: Optional[str] = None


class ReceiptCreate(ReceiptBase):
    pass


class ReceiptResponse(ReceiptBase):
    id: uuid.UUID
    receipt_number: str
    printed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DailySalesSummaryResponse(BaseModel):
    id: uuid.UUID
    summary_date: datetime
    total_orders: int
    total_revenue: float
    total_items_sold: int
    average_order_value: float
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardToday(BaseModel):
    total_orders: int
    total_revenue: float
    total_items_sold: int


class DashboardTopProduct(BaseModel):
    product_id: uuid.UUID
    product_name: str
    category_name: str
    total_quantity_sold: int
    total_revenue: float
    order_count: int


class ActivePaymentQueueItem(BaseModel):
    queue_id: uuid.UUID
    queue_position: int
    priority: QueuePriority
    status: QueueStatus
    submitted_at: datetime
    cart_id: uuid.UUID
    cart_notes: Optional[str]
    station_id: Optional[str]
    item_count: int
    estimated_total: float


class SalesByHour(BaseModel):
    hour: int
    total_orders: int
    total_revenue: float


class SalesByCategory(BaseModel):
    category_id: uuid.UUID
    category_name: str
    total_quantity_sold: int
    total_revenue: float
    order_count: int


class InventoryAlert(BaseModel):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    variant_description: str
    sku_variant: str
    quantity_available: int
    quantity_reserved: int
    low_stock_threshold: int
    status: str


class PeriodComparison(BaseModel):
    current_period: float
    previous_period: float
    absolute_change: float
    percentage_change: float
    trend: str


class DashboardSummary(BaseModel):
    today: DashboardToday
    weekly_sales: float
    monthly_sales: float
    comparison: PeriodComparison
    sales_by_hour: List[SalesByHour]
    sales_by_category: List[SalesByCategory]
    top_products: List[DashboardTopProduct]
    inventory_alerts: List[InventoryAlert]
    sales_trend: List[SalesByHour]


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str = "access"


class POSPaymentStatus(str, Enum):
    PENDING = "pending"
    WAITING_CARD = "waiting_card"
    PROCESSING = "processing"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class POSInitializeRequest(BaseModel):
    cart_id: uuid.UUID
    amount: float
    currency: str = "MXN"


class POSInitializeResponse(BaseModel):
    success: bool
    transaction_id: str
    status: POSPaymentStatus
    amount: float
    message: Optional[str] = None


class POSStatusResponse(BaseModel):
    success: bool
    transaction_id: str
    status: POSPaymentStatus
    amount: Optional[float] = None
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None
    error_message: Optional[str] = None
    provider_reference: Optional[str] = None
    timestamp: Optional[datetime] = None


class POSResultResponse(BaseModel):
    success: bool
    transaction_id: str
    status: POSPaymentStatus
    amount: float
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None
    error_message: Optional[str] = None
    provider_reference: Optional[str] = None
    timestamp: datetime


class SupplierBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AttributeOptionBase(BaseModel):
    type: str
    value: str
    hex_code: Optional[str] = None
    sort_order: int = 0


class AttributeOptionCreate(AttributeOptionBase):
    pass


class AttributeOptionUpdate(BaseModel):
    type: Optional[str] = None
    value: Optional[str] = None
    hex_code: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AttributeOptionResponse(AttributeOptionBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductAttributeBase(BaseModel):
    product_id: uuid.UUID
    attribute_option_id: uuid.UUID


class ProductAttributeCreate(ProductAttributeBase):
    pass


class ProductAttributeResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    attribute_option: AttributeOptionResponse
    created_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    product_id: uuid.UUID
    price_type: PriceType
    old_price: Optional[float] = None
    new_price: float
    reason: Optional[str] = None


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistoryResponse(PriceHistoryBase):
    id: uuid.UUID
    changed_by: Optional[uuid.UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class PriceBreakdownResponse(BaseModel):
    product_id: uuid.UUID
    cost_price: float
    profit_margin: float
    profit_margin_percent: float
    base_price: float
    tax_rate: float
    tax_amount: float
    selling_price: float
    total_profit: float
    variant_price_modifier: float = 0
    final_price: float

    class Config:
        from_attributes = True


class InventoryStatusUpdate(BaseModel):
    stock_status: StockStatus
    warehouse_location: Optional[str] = None