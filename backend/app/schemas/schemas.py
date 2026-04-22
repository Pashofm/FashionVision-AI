import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


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
    yolo_class_id: Optional[int] = None
    yolo_class_name: Optional[str] = None
    images: List[str] = []


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    base_price: Optional[float] = None
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


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    quantity_available: Optional[int] = None
    quantity_reserved: Optional[int] = None
    low_stock_threshold: Optional[int] = None


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
    unit_price: float
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