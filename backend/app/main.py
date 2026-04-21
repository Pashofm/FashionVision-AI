import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, List

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from PIL import Image
import io

from backend.app.database import get_db, AsyncSessionLocal, engine, Base
from backend.app.config import settings
from backend.app.models import (
    User, Category, Product, ProductVariant, Inventory, InventoryMovement,
    DbSession, Cart, CartItem, PaymentQueue, Order, OrderItem, Receipt,
    UserRole, CartStatus, OrderStatus, PaymentMethod, QueueStatus, QueuePriority, MovementType
)
from backend.app.schemas import (
    UserCreate, UserResponse, UserUpdate,
    CategoryCreate, CategoryResponse, CategoryUpdate,
    ProductCreate, ProductResponse, ProductUpdate, ProductVariantCreate, ProductVariantResponse,
    ProductWithVariantsResponse,
    InventoryCreate, InventoryResponse, InventoryUpdate,
    InventoryMovementCreate, InventoryMovementResponse,
    SessionCreate, SessionResponse,
    CartCreate, CartResponse, CartUpdate, CartItemCreate, CartItemResponse, CartWithItemsResponse, CartWithTotal,
    PaymentQueueCreate, PaymentQueueResponse,
    OrderCreate, OrderResponse,
    ReceiptCreate, ReceiptResponse,
    DashboardToday, DashboardTopProduct, ActivePaymentQueueItem,
    LoginRequest, LoginResponse,
    CartStatus
)
from backend.app.services.detection import get_model, detect_in_image, get_model_classes

import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="FashionVision AI API",
    description="AI-powered clothing detection and retail management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_dependency = Depends(get_db)


# ==================== HEALTH ====================

@app.get("/")
async def root():
    return {"message": "FashionVision AI API", "status": "operational"}


@app.get("/health")
async def health_check(db: AsyncSession = db_dependency):
    return {"status": "healthy", "database": "connected"}


# ==================== YOLO DETECTION ====================

@app.get("/api/detect/classes")
async def get_detection_classes():
    classes = get_model_classes()
    return {"classes": classes}


@app.post("/api/detect")
async def detect_clothes(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        result = detect_in_image(image)
        return JSONResponse(result)
    except Exception as e:
        import logging
        logging.error(f"Error during detection: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/detect/health")
async def detection_health_check():
    from backend.app.services import detection
    yolo_model = get_model()
    return {
        "status": "healthy" if yolo_model else "model_not_loaded",
        "model_loaded": yolo_model is not None,
        "model_path": str(detection.MODEL_PATH)
    }


# ==================== AUTH ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    
    access_token = f"demo_token_{user.id}"
    return LoginResponse(access_token=access_token, user=UserResponse.model_validate(user))


# ==================== USERS ====================

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=pwd_context.hash(user_data.password),
        role=user_data.role
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


@app.get("/api/users", response_model=List[UserResponse])
async def get_users(db: AsyncSession = db_dependency):
    result = await db.execute(select(User))
    return result.scalars().all()


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: uuid.UUID, user_data: UserUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.name:
        user.name = user_data.name
    if user_data.email:
        user.email = user_data.email
    if user_data.password:
        user.password_hash = pwd_context.hash(user_data.password)
    if user_data.role:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    await db.flush()
    await db.refresh(user)
    return user


# ==================== CATEGORIES ====================

@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = db_dependency):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.flush()
    await db.refresh(db_category)
    return db_category


@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = db_dependency):
    result = await db.execute(select(Category))
    return result.scalars().all()


@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: uuid.UUID, category_data: CategoryUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_data.name:
        category.name = category_data.name
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.icon is not None:
        category.icon = category_data.icon
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    await db.flush()
    await db.refresh(category)
    return category


# ==================== PRODUCTS ====================

@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.sku == product.sku))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.flush()
    await db.refresh(db_product)
    return db_product


@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: uuid.UUID = None,
    search: str = None,
    yolo_class_name: str = None,
    db: AsyncSession = db_dependency
):
    query = select(Product)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if yolo_class_name:
        query = query.where(Product.yolo_class_name == yolo_class_name)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/products/with-variants", response_model=List[ProductWithVariantsResponse])
async def get_products_with_variants(db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).options(selectinload(Product.variants)))
    return result.scalars().all()


@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: uuid.UUID, product_data: ProductUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    await db.flush()
    await db.refresh(product)
    return product


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    return {"message": "Product deleted"}


@app.get("/api/products/by-yolo/{yolo_class_name}", response_model=ProductResponse)
async def get_product_by_yolo(yolo_class_name: str, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.yolo_class_name == yolo_class_name))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"No product found for YOLO class: {yolo_class_name}")
    return product


# ==================== PRODUCT VARIANTS ====================

@app.post("/api/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(product_id: uuid.UUID, variant: ProductVariantCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_variant = ProductVariant(
        product_id=product_id,
        size=variant.size,
        color=variant.color,
        color_hex=variant.color_hex,
        sku_variant=variant.sku_variant,
        price_modifier=variant.price_modifier
    )
    db.add(db_variant)
    await db.flush()
    await db.refresh(db_variant)
    return db_variant


@app.get("/api/products/{product_id}/variants", response_model=List[ProductVariantResponse])
async def get_product_variants(product_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(ProductVariant).where(ProductVariant.product_id == product_id))
    return result.scalars().all()


# ==================== INVENTORY ====================

@app.post("/api/inventory", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory(inventory: InventoryCreate, db: AsyncSession = db_dependency):
    db_inventory = Inventory(**inventory.model_dump())
    db.add(db_inventory)
    await db.flush()
    await db.refresh(db_inventory)
    return db_inventory


@app.get("/api/inventory", response_model=List[InventoryResponse])
async def get_inventory(db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory))
    return result.scalars().all()


@app.get("/api/inventory/{variant_id}", response_model=InventoryResponse)
async def get_inventory_by_variant(variant_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory


@app.put("/api/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(inventory_id: uuid.UUID, inventory_data: InventoryUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    update_data = inventory_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(inventory, key, value)
    
    await db.flush()
    await db.refresh(inventory)
    return inventory


# ==================== INVENTORY MOVEMENTS ====================

@app.post("/api/inventory-movements", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_movement(movement: InventoryMovementCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == movement.product_variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    quantity_before = inventory.quantity_available
    inventory.quantity_available += movement.quantity_change
    quantity_after = inventory.quantity_available
    
    db_movement = InventoryMovement(
        product_variant_id=movement.product_variant_id,
        movement_type=movement.movement_type,
        quantity_change=movement.quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        notes=movement.notes
    )
    db.add(db_movement)
    await db.flush()
    await db.refresh(db_movement)
    return db_movement


@app.get("/api/inventory-movements", response_model=List[InventoryMovementResponse])
async def get_inventory_movements(product_variant_id: uuid.UUID = None, db: AsyncSession = db_dependency):
    query = select(InventoryMovement)
    if product_variant_id:
        query = query.where(InventoryMovement.product_variant_id == product_variant_id)
    query = query.order_by(InventoryMovement.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


# ==================== SESSIONS ====================

@app.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionCreate, db: AsyncSession = db_dependency):
    db_session = DbSession(station_id=session.station_id, client_user_id=session.client_user_id)
    db.add(db_session)
    await db.flush()
    await db.refresh(db_session)
    return db_session


@app.get("/api/sessions", response_model=List[SessionResponse])
async def get_sessions(db: AsyncSession = db_dependency):
    result = await db.execute(select(DbSession))
    return result.scalars().all()


# ==================== CARTS ====================

@app.post("/api/carts", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(cart: CartCreate, db: AsyncSession = db_dependency):
    db_cart = Cart(**cart.model_dump())
    db.add(db_cart)
    await db.flush()
    await db.refresh(db_cart)
    return db_cart


@app.get("/api/carts", response_model=List[CartResponse])
async def get_carts(session_id: uuid.UUID = None, status: CartStatus = None, db: AsyncSession = db_dependency):
    query = select(Cart)
    if session_id:
        query = query.where(Cart.session_id == session_id)
    if status:
        query = query.where(Cart.status == status)
    query = query.order_by(Cart.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/carts/{cart_id}", response_model=CartWithItemsResponse)
async def get_cart(cart_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == cart_id).options(selectinload(Cart.items)))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@app.put("/api/carts/{cart_id}", response_model=CartResponse)
async def update_cart(cart_id: uuid.UUID, cart_data: CartUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    if cart_data.status:
        cart.status = cart_data.status
    if cart_data.notes is not None:
        cart.notes = cart_data.notes
    
    await db.flush()
    await db.refresh(cart)
    return cart


@app.post("/api/carts/{cart_id}/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_cart_item(cart_id: uuid.UUID, item: CartItemCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    db_item = CartItem(
        cart_id=cart_id,
        product_id=item.product_id,
        product_variant_id=item.product_variant_id,
        quantity=item.quantity,
        unit_price=item.unit_price,
        detection_confidence=item.detection_confidence,
        detection_image_path=item.detection_image_path,
        detection_bbox=item.detection_bbox
    )
    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    return db_item


@app.delete("/api/carts/{cart_id}/items/{item_id}")
async def remove_cart_item(cart_id: uuid.UUID, item_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(CartItem).where(and_(CartItem.id == item_id, CartItem.cart_id == cart_id)))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    return {"message": "Item removed"}


@app.get("/api/carts/admin", response_model=List[CartWithTotal])
async def get_pending_carts_admin(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Cart)
        .where(Cart.status == CartStatus.submitted)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    carts = result.scalars().all()
    
    response = []
    for cart in carts:
        cart_total = sum(item.unit_price * item.quantity for item in cart.items)
        response.append(CartWithTotal(
            id=cart.id,
            session_id=cart.session_id,
            status=cart.status,
            created_at=cart.created_at,
            items=[CartItemResponse.model_validate(i) for i in cart.items],
            total=cart_total
        ))
    return response


# ==================== PAYMENT QUEUE ====================

@app.post("/api/payment-queue", response_model=PaymentQueueResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_queue(queue: PaymentQueueCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(PaymentQueue).order_by(PaymentQueue.queue_position.desc()).limit(1))
    last_queue = result.scalar_one_or_none()
    next_position = (last_queue.queue_position + 1) if last_queue else 1
    
    db_queue = PaymentQueue(cart_id=queue.cart_id, queue_position=next_position, priority=queue.priority)
    db.add(db_queue)
    await db.flush()
    await db.refresh(db_queue)
    return db_queue


@app.get("/api/payment-queue", response_model=List[PaymentQueueResponse])
async def get_payment_queue(status: QueueStatus = None, db: AsyncSession = db_dependency):
    query = select(PaymentQueue)
    if status:
        query = query.where(PaymentQueue.status == status)
    query = query.order_by(PaymentQueue.queue_position.asc())
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/payment-queue/active", response_model=List[ActivePaymentQueueItem])
async def get_active_payment_queue(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(PaymentQueue)
        .where(PaymentQueue.status.in_([QueueStatus.waiting, QueueStatus.in_progress]))
        .options(selectinload(PaymentQueue.cart).selectinload(Cart.items))
        .order_by(PaymentQueue.priority.desc(), PaymentQueue.queue_position.asc())
    )
    queues = result.scalars().all()
    
    response = []
    for pq in queues:
        estimated_total = sum(item.unit_price * item.quantity for item in pq.cart.items if item.confirmed)
        response.append(ActivePaymentQueueItem(
            queue_id=pq.id,
            queue_position=pq.queue_position,
            priority=pq.priority,
            status=pq.status,
            submitted_at=pq.created_at,
            cart_id=pq.cart.id,
            cart_notes=pq.cart.notes,
            station_id=pq.cart.session.station_id if pq.cart.session else None,
            item_count=len([i for i in pq.cart.items if i.confirmed]),
            estimated_total=estimated_total
        ))
    return response


# ==================== ORDERS ====================

@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == order.cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5]}"
    
    db_order = Order(
        cart_id=order.cart_id,
        order_number=order_number,
        cashier_id=order.cashier_id,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        cash_received=order.cash_received,
        change_given=order.change_given,
        notes=order.notes
    )
    db.add(db_order)
    await db.flush()
    await db.refresh(db_order)
    return db_order


@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(status: OrderStatus = None, db: AsyncSession = db_dependency):
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    query = query.order_by(Order.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ==================== RECEIPTS ====================

@app.post("/api/receipts", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(receipt: ReceiptCreate, db: AsyncSession = db_dependency):
    receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5]}"
    
    db_receipt = Receipt(
        order_id=receipt.order_id,
        receipt_number=receipt_number,
        receipt_data=receipt.receipt_data,
        pdf_path=receipt.pdf_path,
        emailed_to=receipt.emailed_to
    )
    db.add(db_receipt)
    await db.flush()
    await db.refresh(db_receipt)
    return db_receipt


@app.get("/api/receipts", response_model=List[ReceiptResponse])
async def get_receipts(db: AsyncSession = db_dependency):
    result = await db.execute(select(Receipt).order_by(Receipt.created_at.desc()))
    return result.scalars().all()


# ==================== ANALYTICS ====================

@app.get("/api/analytics/dashboard/today", response_model=DashboardToday)
async def get_dashboard_today(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(Order.status == OrderStatus.completed, func.date(Order.completed_at) == func.current_date()))
    )
    row = result.one()
    
    result_items = await db.execute(
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order)
        .where(and_(Order.status == OrderStatus.completed, func.date(Order.completed_at) == func.current_date()))
    )
    total_items = result_items.scalar()
    
    return DashboardToday(total_orders=row[0], total_revenue=float(row[1]), total_items_sold=total_items)


@app.get("/api/analytics/top-products", response_model=List[DashboardTopProduct])
async def get_top_products(days: int = 30, db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Product.id, Product.name, Category.name, func.sum(OrderItem.quantity), func.sum(OrderItem.subtotal), func.count(func.distinct(Order.id)))
        .select_from(OrderItem)
        .join(Order)
        .join(Product)
        .join(Category)
        .where(and_(Order.status == OrderStatus.completed, Order.completed_at >= datetime.now() - timedelta(days=days)))
        .group_by(Product.id, Product.name, Category.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
    )
    
    response = []
    for row in result:
        response.append(DashboardTopProduct(
            product_id=row[0], product_name=row[1], category_name=row[2],
            total_quantity_sold=row[3], total_revenue=float(row[4]), order_count=row[5]
        ))
    return response


@app.get("/api/analytics/sales")
async def get_sales_analytics(db: AsyncSession = db_dependency):
    now = datetime.now()
    
    monthly = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(Order.status == OrderStatus.completed, func.extract("month", Order.completed_at) == func.extract("month", now)))
    )
    weekly = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(Order.status == OrderStatus.completed, Order.completed_at >= now - timedelta(days=7)))
    )
    daily = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(Order.status == OrderStatus.completed, func.date(Order.completed_at) == func.current_date()))
    )
    total = await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.completed))

    return {
        "monthly_sales": float(monthly.scalar()),
        "weekly_sales": float(weekly.scalar()),
        "daily_sales": float(daily.scalar()),
        "total_transactions": total.scalar()
    }
