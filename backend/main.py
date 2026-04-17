from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from decimal import Decimal

from backend.database.connection import get_db, init_db
from backend.database.models import (
    User, Category, Product, InventoryMovement, Sale, SaleItem,
    Cart, CartItem, Payment, Receipt, UserRole, MovementType, CartStatus, SaleStatus
)
from backend.schemas.schemas import (
    UserCreate, UserResponse, CategoryCreate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    InventoryMovementCreate, InventoryMovementResponse,
    SaleCreate, SaleResponse, SaleItemCreate,
    CartCreate, CartResponse, CartItemCreate, CartWithTotal,
    PaymentCreate, PaymentResponse, ReceiptResponse,
    SalesAnalytics, ProductSalesStats, InventoryStats
)

app = FastAPI(title="FashionVision AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).parent / "models" / "best.pt"
model = None


def get_model():
    global model
    if model is None:
        if MODEL_PATH.exists():
            logger.info(f"Loading model from {MODEL_PATH}")
            model = YOLO(str(MODEL_PATH))
        else:
            logger.warning(f"Model not found at {MODEL_PATH}, using YOLOv8n")
            model = YOLO("yolov8n.pt")
    return model


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "FashionVision AI API", "status": "operational"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}


# ==================== USERS ====================

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, password_hash=user.password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ==================== CATEGORIES ====================

@app.post("/api/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(nombre=category.nombre, descripcion=category.descripcion)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


# ==================== PRODUCTS (INVENTORY) ====================

@app.post("/api/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/api/products", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}


# ==================== INVENTORY MOVEMENTS ====================

@app.post("/api/inventory-movements", response_model=InventoryMovementResponse)
def create_inventory_movement(movement: InventoryMovementCreate, db: Session = Depends(get_db)):
    db_movement = InventoryMovement(**movement.model_dump())
    db.add(db_movement)
    
    product = db.query(Product).filter(Product.id == movement.product_id).first()
    if movement.movement_type == MovementType.entrada:
        product.cantidad += movement.cantidad
    elif movement.movement_type == MovementType.salida:
        product.cantidad -= movement.cantidad
    elif movement.movement_type == MovementType.ajuste:
        product.cantidad = movement.cantidad
    
    db.commit()
    db.refresh(db_movement)
    return db_movement


@app.get("/api/inventory-movements", response_model=List[InventoryMovementResponse])
def get_inventory_movements(product_id: int = None, db: Session = Depends(get_db)):
    query = db.query(InventoryMovement)
    if product_id:
        query = query.filter(InventoryMovement.product_id == product_id)
    return query.order_by(InventoryMovement.created_at.desc()).all()


# ==================== SALES ====================

@app.post("/api/sales", response_model=SaleResponse)
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    total = Decimal("0")
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            total += Decimal(str(product.precio)) * item.cantidad
    
    db_sale = Sale(total=total, metodo_pago=sale.metodo_pago)
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            db_item = SaleItem(
                sale_id=db_sale.id,
                product_id=item.product_id,
                cantidad=item.cantidad,
                precio_unitario=product.precio
            )
            db.add(db_item)
            product.cantidad -= item.cantidad
    
    db.commit()
    db.refresh(db_sale)
    return db_sale


@app.get("/api/sales", response_model=List[SaleResponse])
def get_sales(db: Session = Depends(get_db)):
    return db.query(Sale).order_by(Sale.created_at.desc()).all()


# ==================== CARTS ====================

@app.post("/api/carts", response_model=CartResponse)
def create_cart(cart: CartCreate, db: Session = Depends(get_db)):
    db_cart = Cart(user_id=cart.user_id)
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart


@app.get("/api/carts", response_model=List[CartResponse])
def get_carts(user_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Cart)
    if user_id:
        query = query.filter(Cart.user_id == user_id)
    return query.order_by(Cart.created_at.desc()).all()


@app.get("/api/carts/admin", response_model=List[CartWithTotal])
def get_pending_carts_admin(db: Session = Depends(get_db)):
    carts = db.query(Cart).filter(Cart.status == CartStatus.pending).all()
    result = []
    for cart in carts:
        cart_total = Decimal("0")
        for item in cart.items:
            if item.product:
                cart_total += Decimal(str(item.product.precio)) * item.cantidad
        user = db.query(User).filter(User.id == cart.user_id).first()
        result.append(CartWithTotal(
            id=cart.id,
            user_id=cart.user_id,
            status=cart.status,
            created_at=cart.created_at,
            items=[CartItemResponse(id=i.id, cart_id=cart.id, product_id=i.product_id, cantidad=i.cantidad) for i in cart.items],
            total=cart_total,
            customer_username=user.username if user else "Unknown"
        ))
    return result


@app.post("/api/carts/{cart_id}/items", response_model=CartResponse)
def add_cart_item(cart_id: int, item: CartItemCreate, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    db_item = CartItem(cart_id=cart_id, product_id=item.product_id, cantidad=item.cantidad)
    db.add(db_item)
    db.commit()
    db.refresh(cart)
    return cart


@app.delete("/api/carts/{cart_id}/items/{item_id}")
def remove_cart_item(cart_id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item removed"}


# ==================== PAYMENTS ====================

@app.post("/api/payments", response_model=PaymentResponse)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.id == payment.cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    db_payment = Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@app.post("/api/payments/{cart_id}/process", response_model=ReceiptResponse)
def process_payment(cart_id: int, metodo_pago: str, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.status == CartStatus.processed:
        raise HTTPException(status_code=400, detail="Cart already processed")
    
    total = Decimal("0")
    for item in cart.items:
        if item.product:
            total += Decimal(str(item.product.precio)) * item.cantidad
    
    db_payment = Payment(cart_id=cart_id, metodo_pago=metodo_pago, monto=total)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    receipt_count = db.query(Receipt).count() + 1
    numero_recibo = f"REC-{receipt_count:06d}"
    db_receipt = Receipt(payment_id=db_payment.id, cart_id=cart_id, numero_recibo=numero_recibo)
    db.add(db_receipt)
    
    cart.status = CartStatus.processed
    
    for item in cart.items:
        if item.product:
            db_item = SaleItem(
                sale_id=None,
                product_id=item.product_id,
                cantidad=item.cantidad,
                precio_unitario=item.product.precio
            )
            db.add(db_item)
    
    db.commit()
    db.refresh(db_receipt)
    return db_receipt


# ==================== ANALYTICS ====================

@app.get("/api/analytics/sales", response_model=SalesAnalytics)
def get_sales_analytics(db: Session = Depends(get_db)):
    now = func.now()
    
    monthly = db.query(func.sum(Sale.total)).filter(
        func.extract("month", Sale.created_at) == func.extract("month", now),
        func.extract("year", Sale.created_at) == func.extract("year", now)
    ).scalar() or Decimal("0")
    
    weekly = db.query(func.sum(Sale.total)).filter(
        func.extract("week", Sale.created_at) == func.extract("week", now)
    ).scalar() or Decimal("0")
    
    daily = db.query(func.sum(Sale.total)).filter(
        func.date(Sale.created_at) == func.current_date()
    ).scalar() or Decimal("0")
    
    total_transactions = db.query(Sale).count()
    
    return SalesAnalytics(
        monthly_sales=monthly,
        weekly_sales=weekly,
        daily_sales=daily,
        total_transactions=total_transactions
    )


@app.get("/api/analytics/products/most-sold", response_model=List[ProductSalesStats])
def get_most_sold_products(db: Session = Depends(get_db)):
    results = db.query(
        SaleItem.product_id,
        Product.nombre,
        func.sum(SaleItem.cantidad).label("total_sold")
    ).join(Product).group_by(SaleItem.product_id, Product.nombre).order_by(func.sum(SaleItem.cantidad).desc()).limit(10).all()
    return [ProductSalesStats(product_id=r[0], product_nombre=r[1], total_sold=r[2]) for r in results]


@app.get("/api/analytics/products/least-sold", response_model=List[ProductSalesStats])
def get_least_sold_products(db: Session = Depends(get_db)):
    results = db.query(
        SaleItem.product_id,
        Product.nombre,
        func.sum(SaleItem.cantidad).label("total_sold")
    ).join(Product).group_by(SaleItem.product_id, Product.nombre).order_by(func.sum(SaleItem.cantidad).asc()).limit(10).all()
    return [ProductSalesStats(product_id=r[0], product_nombre=r[1], total_sold=r[2]) for r in results]


@app.get("/api/analytics/inventory", response_model=InventoryStats)
def get_inventory_stats(db: Session = Depends(get_db)):
    excess = db.query(Product).filter(Product.cantidad > 50).all()
    out_of_stock = db.query(Product).filter(Product.cantidad == 0).all()
    low_stock = db.query(Product).filter(Product.cantidad > 0, Product.cantidad <= 10).all()
    return InventoryStats(
        excess_stock=[ProductResponse.model_validate(p) for p in excess],
        out_of_stock=[ProductResponse.model_validate(p) for p in out_of_stock],
        low_stock=[ProductResponse.model_validate(p) for p in low_stock]
    )
