from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    customer = "customer"
    admin = "admin"


class MovementType(str, Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"


class CartStatus(str, Enum):
    pending = "pending"
    processed = "processed"


class SaleStatus(str, Enum):
    completado = "completado"
    cancelado = "cancelado"


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.customer


class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    nombre: str
    cantidad: int = 0
    precio: Decimal
    color: Optional[str] = None
    tipo_prenda: Optional[str] = None
    imagen_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    cantidad: Optional[int] = None
    precio: Optional[Decimal] = None
    color: Optional[str] = None
    tipo_prenda: Optional[str] = None
    imagen_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryMovementBase(BaseModel):
    product_id: int
    movement_type: MovementType
    cantidad: int
    nota: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovementResponse(InventoryMovementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SaleItemBase(BaseModel):
    product_id: int
    cantidad: int
    precio_unitario: Decimal


class SaleItemCreate(SaleItemBase):
    pass


class SaleItemResponse(SaleItemBase):
    id: int
    sale_id: int

    class Config:
        from_attributes = True


class SaleBase(BaseModel):
    total: Decimal
    metodo_pago: Optional[str] = None
    estado: SaleStatus = SaleStatus.completado


class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    metodo_pago: str


class SaleResponse(SaleBase):
    id: int
    created_at: datetime
    items: List[SaleItemResponse] = []

    class Config:
        from_attributes = True


class CartItemBase(BaseModel):
    product_id: int
    cantidad: int = 1


class CartItemCreate(CartItemBase):
    pass


class CartItemResponse(CartItemBase):
    id: int
    cart_id: int

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    user_id: int
    status: CartStatus = CartStatus.pending


class CartCreate(BaseModel):
    user_id: int


class CartResponse(CartBase):
    id: int
    created_at: datetime
    items: List[CartItemResponse] = []

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    cart_id: int
    metodo_pago: str
    monto: Decimal


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptBase(BaseModel):
    payment_id: int
    cart_id: int
    numero_recibo: str


class ReceiptResponse(ReceiptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CartWithTotal(BaseModel):
    id: int
    user_id: int
    status: CartStatus
    created_at: datetime
    items: List[CartItemResponse]
    total: Decimal
    customer_username: str

    class Config:
        from_attributes = True


class SalesAnalytics(BaseModel):
    monthly_sales: Decimal
    weekly_sales: Decimal
    daily_sales: Decimal
    total_transactions: int


class ProductSalesStats(BaseModel):
    product_id: int
    product_nombre: str
    total_sold: int

    class Config:
        from_attributes = True


class InventoryStats(BaseModel):
    excess_stock: List[ProductResponse]
    out_of_stock: List[ProductResponse]
    low_stock: List[ProductResponse]