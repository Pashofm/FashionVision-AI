from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base
import enum


class UserRole(enum.Enum):
    customer = "customer"
    admin = "admin"


class MovementType(enum.Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"


class CartStatus(enum.Enum):
    pending = "pending"
    processed = "processed"


class SaleStatus(enum.Enum):
    completado = "completado"
    cancelado = "cancelado"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer)
    created_at = Column(DateTime, server_default=func.now())

    carts = relationship("Cart", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    cantidad = Column(Integer, default=0)
    precio = Column(DECIMAL(10, 2), nullable=False)
    color = Column(String(50), nullable=True)
    tipo_prenda = Column(String(100), nullable=True)
    imagen_url = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    cantidad = Column(Integer, nullable=False)
    nota = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    product = relationship("Product", back_populates="inventory_movements")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    total = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(String(50), nullable=True)
    estado = Column(Enum(SaleStatus), default=SaleStatus.completado)
    created_at = Column(DateTime, server_default=func.now())

    items = relationship("SaleItem", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(CartStatus), default=CartStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart")
    payment = relationship("Payment", back_populates="cart", uselist=False)


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    cantidad = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    metodo_pago = Column(String(50), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    cart = relationship("Cart", back_populates="payment")
    receipt = relationship("Receipt", back_populates="payment", uselist=False)


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    numero_recibo = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    payment = relationship("Payment", back_populates="receipt")