import io
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.config import settings, update_session_timeout
from backend.app.database import AsyncSessionLocal, Base, engine, get_db
from backend.app.dependencies import get_current_user, require_role
from backend.app.models import (Cart, CartItem, CartStatus, Category,
                                Session, Inventory, InventoryMovement,
                                MovementType, Order, OrderItem, OrderStatus,
                                PaymentMethod, PaymentQueue, Product,
                                ProductVariant, QueuePriority, QueueStatus,
                                Receipt, SessionStatus, StockStatus, Supplier,
                                AttributeOption, ProductAttribute, PriceHistory,
                                User, UserRole)
from backend.app.schemas import (ActivePaymentQueueItem, CartCreate,
                                 CartItemCreate, CartItemResponse,
                                 CartResponse, CartStatus, CartUpdate,
                                 CartWithItemsResponse, CartWithTotal,
                                 CategoryCreate, CategoryResponse,
                                 CategoryUpdate, DashboardToday,
                                 DashboardTopProduct, DashboardSummary,
                                 ImageUploadResponse, InventoryAdjust,
                                 InventoryAlert, InventoryCreate,
                                 InventoryLowStockResponse,
                                 InventoryMovementCreate,
                                 InventoryMovementResponse, InventoryResponse,
                                 InventoryRestock, InventoryUpdate,
                                 InventoryStatusUpdate,
                                 LoginRequest, LoginResponse,
                                 OrderCreate, OrderResponse,
                                 PaymentQueueCreate, PaymentQueueResponse,
                                 PeriodComparison, POSInitializeRequest,
                                 POSInitializeResponse, POSResultResponse,
                                 POSStatusResponse, PriceBreakdownResponse,
                                 PriceHistoryCreate, PriceHistoryResponse,
                                 ProductCreate, ProductResponse,
                                 ProductUpdate, ProductVariantCreate,
                                 ProductVariantResponse, ProductVariantUpdate,
                                 ProductWithStockResponse,
                                 ProductWithVariantsResponse, ReceiptCreate,
                                 ReceiptResponse, RefreshTokenRequest,
                                 RefreshTokenResponse, SalesByCategory,
                                 SalesByHour, SessionCreate, SessionResponse,
                                 SupplierCreate, SupplierResponse,
                                 SupplierUpdate,
                                 AttributeOptionCreate, AttributeOptionResponse,
                                 AttributeOptionUpdate, AttributeOptionBase,
                                 ProductAttributeCreate, ProductAttributeResponse,
                                 UserCreate, UserResponse, UserUpdate,
                                 VariantWithInventory, PriceType, StockStatus)
from backend.app.services.auth import (create_access_token,
                                       create_refresh_token,
                                       decode_refresh_token, hash_password,
                                       verify_password, get_token_issued_at)
from backend.app.services.timezone_service import (
    get_current_utc_time, get_server_time, utc_to_local, local_to_utc,
    get_timezone_from_request, format_datetime_for_response
)
from backend.app.services.detection import detect_in_image, get_model, get_model_classes
from backend.app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)
_cleanup_lock = asyncio.Lock()
_cleanup_task_handle = None


async def periodic_session_cleanup(app: FastAPI):
    while True:
        try:
            await asyncio.sleep(300)
            if _cleanup_lock.locked():
                continue
            async with _cleanup_lock:
                async with AsyncSessionLocal() as db:
                    expired_count = await SessionManager.expire_inactive_sessions(db)
                    if expired_count > 0:
                        logger.info(f"Session cleanup: expired {expired_count} inactive sessions")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic session cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionManager.set_timeout_minutes(settings.SESSION_TIMEOUT_MINUTES)
    
    global _cleanup_task_handle
    _cleanup_task_handle = asyncio.create_task(periodic_session_cleanup(app))
    
    yield
    
    if _cleanup_task_handle:
        _cleanup_task_handle.cancel()
        try:
            await _cleanup_task_handle
        except asyncio.CancelledError:
            pass


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
    try:
        model = get_model()
        model_loaded = model is not None
    except Exception:
        model_loaded = False
    return {"status": "healthy", "database": "connected", "model_loaded": model_loaded}


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
    model_path = detection.get_model_path()
    return {
        "status": "healthy" if yolo_model else "model_not_loaded",
        "model_loaded": yolo_model is not None,
        "model_path": str(model_path)
    }


# ==================== UPLOAD (Cloudinary) ====================

@app.post("/api/upload/image")
async def upload_product_image(
    file: UploadFile = File(...),
    folder: str = "fashionvision/products"
):
    try:
        contents = await file.read()
        result = upload_image(
            file=contents,
            folder=folder,
            resource_type="image"
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        import logging
        logging.error(f"Error uploading image: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/upload/image/{public_id}")
async def delete_product_image(public_id: str):
    try:
        result = delete_image(public_id)
        return {"success": True, "data": result}
    except Exception as e:
        import logging
        logging.error(f"Error deleting image: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== AUTH ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(user_id=str(user.id))

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@app.post("/api/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = db_dependency):
    payload = decode_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if user.last_logout_at:
        token_iat = get_token_issued_at(payload)
        if token_iat and token_iat.replace(tzinfo=dt_timezone.utc) < user.last_logout_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been invalidated. Please login again.",
            )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    new_refresh_token = create_refresh_token(user_id=str(user.id))

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.post("/api/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    user_id = current_user.id
    result = await db.execute(
        update(User).where(User.id == user_id).values(last_logout_at=datetime.now(dt_timezone.utc))
    )
    await db.commit()
    return {"status": "logged_out", "user_id": str(user_id)}


@app.get("/api/auth/session/extend", status_code=status.HTTP_200_OK)
async def extend_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    session_id_param = None
    try:
        session_id_param = uuid.UUID(current_user.id)
    except Exception:
        pass

    if session_id_param:
        await SessionManager.extend_session(db, session_id_param)

    return {"status": "extended", "timeout_minutes": SessionManager.get_timeout_minutes()}


@app.put("/api/auth/session/timeout")
async def update_session_timeout_config(
    timeout_minutes: int,
    current_user: User = Depends(require_role(UserRole.admin)),
):
    if timeout_minutes < 1 or timeout_minutes > 1440:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeout must be between 1 and 1440 minutes",
        )
    SessionManager.set_timeout_minutes(timeout_minutes)
    return {"status": "updated", "timeout_minutes": timeout_minutes}


@app.get("/api/auth/session/status")
async def get_session_status(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": str(current_user.id),
        "role": current_user.role.value,
        "timeout_minutes": SessionManager.get_timeout_minutes(),
        "is_active": current_user.is_active,
    }


# ==================== USERS ====================

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
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
        user.password_hash = hash_password(user_data.password)
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

def _calculate_price_fields(product: Product) -> dict:
    cost = float(product.cost_price or 0)
    margin = float(product.profit_margin or 0)
    tax_rate = float(product.tax_rate or 0.16)

    selling_price = cost * (1 + margin)
    profit_per_unit = selling_price - cost
    tax_amount_per_unit = selling_price * tax_rate

    return {
        "selling_price": round(selling_price, 2),
        "profit_per_unit": round(profit_per_unit, 2),
        "tax_amount_per_unit": round(tax_amount_per_unit, 2)
    }


@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.sku == product.sku))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="SKU already exists")

    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.flush()
    await db.refresh(db_product)

    price_fields = _calculate_price_fields(db_product)
    response_data = {
        **{k: getattr(db_product, k) for k in ['id', 'category_id', 'name', 'description', 'sku',
          'base_price', 'cost_price', 'tax_rate', 'profit_margin', 'brand', 'supplier',
          'barcode', 'weight', 'width', 'height', 'depth', 'min_stock_level', 'max_stock_level',
          'is_featured', 'tags', 'yolo_class_id', 'yolo_class_name', 'images', 'is_active',
          'created_at', 'updated_at']},
        **price_fields
    }
    return ProductResponse(**response_data)


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

    price_fields = _calculate_price_fields(product)
    response_data = {
        **{k: getattr(product, k) for k in ['id', 'category_id', 'name', 'description', 'sku',
          'base_price', 'cost_price', 'tax_rate', 'profit_margin', 'brand', 'supplier',
          'barcode', 'weight', 'width', 'height', 'depth', 'min_stock_level', 'max_stock_level',
          'is_featured', 'tags', 'yolo_class_id', 'yolo_class_name', 'images', 'is_active',
          'created_at', 'updated_at']},
        **price_fields
    }
    return ProductResponse(**response_data)


@app.get("/api/products/{product_id}/price-breakdown", response_model=PriceBreakdownResponse)
async def get_product_price_breakdown(
    product_id: uuid.UUID,
    variant_id: uuid.UUID = None,
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variant_modifier = 0.0
    if variant_id:
        var_result = await db.execute(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        variant = var_result.scalar_one_or_none()
        if variant:
            variant_modifier = float(variant.price_modifier or 0)

    cost_price = float(product.cost_price or 0)
    profit_margin = float(product.profit_margin or 0)
    tax_rate = float(product.tax_rate or 0.16)
    base_price = float(product.base_price or 0)

    selling_price = cost_price * (1 + profit_margin)
    tax_amount = selling_price * tax_rate
    final_price = selling_price + variant_modifier + tax_amount
    total_profit = selling_price - cost_price

    return PriceBreakdownResponse(
        product_id=product.id,
        cost_price=cost_price,
        profit_margin=profit_margin,
        profit_margin_percent=round(profit_margin * 100, 2),
        base_price=base_price,
        tax_rate=tax_rate,
        tax_amount=round(tax_amount, 2),
        selling_price=round(selling_price, 2),
        total_profit=round(total_profit, 2),
        variant_price_modifier=variant_modifier,
        final_price=round(final_price, 2)
    )


@app.post("/api/products/{product_id}/update-prices")
async def update_product_prices(
    product_id: uuid.UUID,
    cost_price: float = None,
    profit_margin: float = None,
    tax_rate: float = None,
    reason: str = "Actualización de precios",
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if cost_price is not None:
        price_hist = PriceHistory(
            product_id=product.id,
            price_type="cost",
            old_price=float(product.cost_price or 0),
            new_price=cost_price,
            changed_by=current_user.id,
            reason=reason
        )
        db.add(price_hist)
        product.cost_price = cost_price

    if profit_margin is not None:
        price_hist = PriceHistory(
            product_id=product.id,
            price_type="base",
            old_price=float(product.profit_margin or 0),
            new_price=profit_margin,
            changed_by=current_user.id,
            reason=reason
        )
        db.add(price_hist)
        product.profit_margin = profit_margin

    if tax_rate is not None:
        price_hist = PriceHistory(
            product_id=product.id,
            price_type="special",
            old_price=float(product.tax_rate or 0),
            new_price=tax_rate,
            changed_by=current_user.id,
            reason=reason
        )
        db.add(price_hist)
        product.tax_rate = tax_rate

    await db.flush()
    await db.refresh(product)

    return {"message": "Prices updated", "product_id": str(product.id), **(_calculate_price_fields(product))}


@app.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.flush()
    await db.refresh(product)

    price_fields = _calculate_price_fields(product)
    response_data = {
        **{k: getattr(product, k) for k in ['id', 'category_id', 'name', 'description', 'sku',
          'base_price', 'cost_price', 'tax_rate', 'profit_margin', 'brand', 'supplier',
          'barcode', 'weight', 'width', 'height', 'depth', 'min_stock_level', 'max_stock_level',
          'is_featured', 'tags', 'yolo_class_id', 'yolo_class_name', 'images', 'is_active',
          'created_at', 'updated_at']},
        **price_fields
    }
    return ProductResponse(**response_data)


@app.delete("/api/products/{product_id}")
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get all variant IDs for this product
    variant_result = await db.execute(
        select(ProductVariant.id).where(ProductVariant.product_id == product_id)
    )
    variant_ids = [row[0] for row in variant_result.fetchall()]

    # Check for pending orders containing this product or its variants
    if variant_ids:
        order_check = await db.execute(
            select(OrderItem).join(Order).where(
                Order.status == OrderStatus.pending,
                OrderItem.product_variant_id.in_(variant_ids)
            )
        )
        if order_check.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar el producto: tiene variantes en pedidos pendientes"
            )

    # Check for pending orders directly referencing this product
    order_check_direct = await db.execute(
        select(OrderItem).join(Order).where(
            Order.status == OrderStatus.pending,
            OrderItem.product_id == product_id
        )
    )
    if order_check_direct.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el producto: está en pedidos pendientes"
        )

    # Delete cart items referencing this product (they are just shopping cart entries)
    await db.execute(delete(CartItem).where(CartItem.product_id == product_id))

    # Delete cart items referencing this product's variants
    if variant_ids:
        await db.execute(
            delete(CartItem).where(CartItem.product_variant_id.in_(variant_ids))
        )

    # Delete inventory records for this product's variants
    if variant_ids:
        await db.execute(delete(Inventory).where(Inventory.product_variant_id.in_(variant_ids)))

    # Delete the product (variants cascade delete automatically)
    await db.delete(product)
    return {"message": "Producto eliminado"}


@app.get("/api/products/by-yolo/{yolo_class_name}", response_model=ProductWithVariantsResponse)
async def get_product_by_yolo(yolo_class_name: str, db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Product)
        .where(Product.yolo_class_name == yolo_class_name)
        .options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"No product found for YOLO class: {yolo_class_name}")
    return product


# ==================== PRODUCT VARIANTS ====================

@app.post("/api/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    product_id: uuid.UUID,
    variant: ProductVariantCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
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


@app.put("/api/products/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    variant_data: ProductVariantUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(ProductVariant).where(
            and_(ProductVariant.id == variant_id, ProductVariant.product_id == product_id)
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    update_data = variant_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(variant, key, value)

    await db.flush()
    await db.refresh(variant)
    return variant


@app.delete("/api/products/{product_id}/variants/{variant_id}")
async def delete_product_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(ProductVariant).where(
            and_(ProductVariant.id == variant_id, ProductVariant.product_id == product_id)
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    await db.delete(variant)
    return {"message": "Variant deleted"}


@app.get("/api/products/{product_id}/stock", response_model=ProductWithStockResponse)
async def get_product_stock(product_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.variants).selectinload(ProductVariant.inventory))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    total_stock = 0
    has_low_stock = False
    has_out_of_stock = False

    variants_data = []
    for v in product.variants:
        inv = v.inventory
        qty = inv.quantity_available if inv else 0
        total_stock += qty
        threshold = inv.low_stock_threshold if inv else 5

        if qty == 0:
            has_out_of_stock = True
        elif qty <= threshold:
            has_low_stock = True

        variants_data.append(VariantWithInventory(
            id=v.id,
            product_id=v.product_id,
            size=v.size,
            color=v.color,
            color_hex=v.color_hex,
            sku_variant=v.sku_variant,
            price_modifier=float(v.price_modifier) if v.price_modifier else 0,
            is_active=v.is_active,
            created_at=v.created_at,
            inventory=InventoryResponse(
                id=inv.id,
                product_variant_id=inv.product_variant_id,
                quantity_available=inv.quantity_available,
                quantity_reserved=inv.quantity_reserved,
                low_stock_threshold=inv.low_stock_threshold,
                last_updated=inv.last_updated
            ) if inv else None
        ))

    return ProductWithStockResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        base_price=float(product.base_price),
        description=product.description,
        category_id=product.category_id,
        yolo_class_id=product.yolo_class_id,
        yolo_class_name=product.yolo_class_name,
        images=product.images or [],
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        variants=variants_data,
        total_stock=total_stock,
        has_low_stock=has_low_stock,
        has_out_of_stock=has_out_of_stock
    )


@app.get("/api/products/stock/all")
async def get_all_products_with_stock(
    skip: int = 0,
    limit: int = 100,
    category_id: uuid.UUID = None,
    search: str = None,
    db: AsyncSession = db_dependency
):
    query = select(Product).options(
        selectinload(Product.variants).selectinload(ProductVariant.inventory)
    )

    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()

    response = []
    for product in products:
        total_stock = 0
        has_low_stock = False
        has_out_of_stock = False

        for v in product.variants:
            inv = v.inventory
            qty = inv.quantity_available if inv else 0
            total_stock += qty
            threshold = inv.low_stock_threshold if inv else 5

            if qty == 0:
                has_out_of_stock = True
            elif qty <= threshold:
                has_low_stock = True

        response.append({
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "category_id": str(product.category_id),
            "base_price": float(product.base_price),
            "is_active": product.is_active,
            "variants_count": len(product.variants),
            "total_stock": total_stock,
            "has_low_stock": has_low_stock,
            "has_out_of_stock": has_out_of_stock
        })

    return response


@app.post("/api/products/{product_id}/images", response_model=ImageUploadResponse)
async def add_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        contents = await file.read()
        upload_result = upload_image(
            file=contents,
            folder="fashionvision/products",
            resource_type="image"
        )

        current_images = product.images or []
        current_images.append(upload_result.get("secure_url", ""))
        product.images = current_images
        await db.flush()

        return ImageUploadResponse(
            success=True,
            public_id=upload_result.get("public_id", ""),
            url=upload_result.get("secure_url", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@app.delete("/api/products/{product_id}/images")
async def remove_product_image(
    product_id: uuid.UUID,
    image_url: str,
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    current_images = product.images or []
    if image_url in current_images:
        current_images.remove(image_url)
        product.images = current_images
        await db.flush()

    try:
        public_id = image_url.split("/")[-1].split(".")[0]
        delete_image(public_id)
    except Exception:
        pass

    return {"message": "Image removed"}


# ==================== INVENTORY ====================

@app.post("/api/inventory", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory(
    inventory: InventoryCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    db_inventory = Inventory(**inventory.model_dump())
    db.add(db_inventory)
    await db.flush()
    await db.refresh(db_inventory)
    return db_inventory


@app.get("/api/inventory", response_model=List[InventoryResponse])
async def get_inventory(db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory))
    return result.scalars().all()


@app.get("/api/inventory/low-stock", response_model=List[InventoryLowStockResponse])
async def get_low_stock_variants(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(
            ProductVariant.id,
            ProductVariant.product_id,
            Product.name,
            Category.name,
            Product.sku,
            ProductVariant.sku_variant,
            ProductVariant.size,
            ProductVariant.color,
            Inventory.quantity_available,
            Inventory.quantity_reserved,
            Inventory.low_stock_threshold
        )
        .select_from(Inventory)
        .join(ProductVariant)
        .join(Product)
        .join(Category)
        .where(Inventory.quantity_available <= Inventory.low_stock_threshold)
        .order_by(Inventory.quantity_available.asc())
    )

    response = []
    for row in result:
        qty = row[8] or 0
        threshold = row[10] or 5
        status = 'out_of_stock' if qty == 0 else 'low_stock'

        response.append(InventoryLowStockResponse(
            variant_id=row[0],
            product_id=row[1],
            product_name=row[2],
            category_name=row[3],
            sku=row[4],
            sku_variant=row[5],
            size=row[6],
            color=row[7],
            quantity_available=qty,
            quantity_reserved=row[9] or 0,
            low_stock_threshold=threshold,
            status=status
        ))
    return response


@app.get("/api/inventory/{variant_id}", response_model=InventoryResponse)
async def get_inventory_by_variant(variant_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory


@app.put("/api/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: uuid.UUID,
    inventory_data: InventoryUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
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


@app.post("/api/inventory/adjust", response_model=InventoryMovementResponse)
async def adjust_inventory(
    variant_id: uuid.UUID,
    adjust_data: InventoryAdjust,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found for this variant")

    new_quantity = inventory.quantity_available + adjust_data.quantity_change
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Cannot reduce stock below zero")

    quantity_before = inventory.quantity_available
    inventory.quantity_available = new_quantity
    inventory.last_updated = datetime.utcnow()
    inventory.updated_by = current_user.id

    db_movement = InventoryMovement(
        product_variant_id=variant_id,
        movement_type=MovementType.adjustment,
        quantity_change=adjust_data.quantity_change,
        quantity_before=quantity_before,
        quantity_after=new_quantity,
        reference_id=adjust_data.reference_id,
        notes=adjust_data.reason,
        created_by=current_user.id
    )
    db.add(db_movement)
    await db.flush()
    await db.refresh(db_movement)
    return db_movement


@app.post("/api/inventory/restock", response_model=InventoryMovementResponse)
async def restock_inventory(
    variant_id: uuid.UUID,
    restock_data: InventoryRestock,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found for this variant")

    quantity_before = inventory.quantity_available
    inventory.quantity_available += restock_data.quantity
    inventory.last_updated = datetime.utcnow()
    inventory.updated_by = current_user.id

    db_movement = InventoryMovement(
        product_variant_id=variant_id,
        movement_type=MovementType.restock,
        quantity_change=restock_data.quantity,
        quantity_before=quantity_before,
        quantity_after=inventory.quantity_available,
        reference_id=restock_data.reference_id,
        notes=restock_data.notes,
        created_by=current_user.id
    )
    db.add(db_movement)
    await db.flush()
    await db.refresh(db_movement)
    return db_movement


@app.put("/api/inventory/{variant_id}/threshold")
async def update_stock_threshold(
    variant_id: uuid.UUID,
    threshold: int,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    inventory.low_stock_threshold = threshold
    inventory.last_updated = datetime.utcnow()
    inventory.updated_by = current_user.id
    await db.flush()

    return {"message": "Threshold updated", "threshold": threshold}


@app.put("/api/inventory/{variant_id}/status")
async def update_inventory_status(
    variant_id: uuid.UUID,
    status_data: InventoryStatusUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Inventory).where(Inventory.product_variant_id == variant_id))
    inventory = result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    inventory.stock_status = status_data.stock_status
    if status_data.warehouse_location is not None:
        inventory.warehouse_location = status_data.warehouse_location
    inventory.last_updated = datetime.utcnow()
    inventory.updated_by = current_user.id
    await db.flush()

    return {
        "message": "Status updated",
        "variant_id": str(variant_id),
        "stock_status": status_data.stock_status.value,
        "warehouse_location": inventory.warehouse_location
    }


@app.get("/api/inventory/warehouse/{location}", response_model=List[InventoryResponse])
async def get_inventory_by_warehouse(
    location: str,
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(Inventory)
        .where(Inventory.warehouse_location == location)
        .options(selectinload(Inventory.variant).selectinload(ProductVariant.product))
    )
    return result.scalars().all()


@app.get("/api/inventory/by-status", response_model=List[InventoryResponse])
async def get_inventory_by_status(
    status: StockStatus,
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(Inventory)
        .where(Inventory.stock_status == status)
        .options(selectinload(Inventory.variant).selectinload(ProductVariant.product))
    )
    return result.scalars().all()


# ==================== SUPPLIERS ====================

@app.get("/api/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(
    is_active: bool = None,
    db: AsyncSession = db_dependency
):
    query = select(Supplier)
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)
    result = await db.execute(query.order_by(Supplier.name))
    return result.scalars().all()


@app.post("/api/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    await db.flush()
    await db.refresh(db_supplier)
    return db_supplier


@app.put("/api/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(supplier, key, value)

    await db.flush()
    await db.refresh(supplier)
    return supplier


@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_active = False
    await db.flush()
    return {"message": "Supplier deactivated"}


# ==================== ATTRIBUTE OPTIONS ====================

@app.get("/api/attributes", response_model=List[AttributeOptionResponse])
async def get_attributes(
    type: str = None,
    db: AsyncSession = db_dependency
):
    query = select(AttributeOption).where(AttributeOption.is_active == True)
    if type:
        query = query.where(AttributeOption.type == type)
    result = await db.execute(query.order_by(AttributeOption.sort_order, AttributeOption.value))
    return result.scalars().all()


@app.post("/api/attributes", response_model=AttributeOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    attribute: AttributeOptionCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(AttributeOption).where(
            AttributeOption.type == attribute.type,
            AttributeOption.value == attribute.value
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Attribute already exists")

    db_attr = AttributeOption(**attribute.model_dump())
    db.add(db_attr)
    await db.flush()
    await db.refresh(db_attr)
    return db_attr


@app.put("/api/attributes/{attribute_id}", response_model=AttributeOptionResponse)
async def update_attribute(
    attribute_id: uuid.UUID,
    attribute_data: AttributeOptionUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(AttributeOption).where(AttributeOption.id == attribute_id))
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    update_data = attribute_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(attr, key, value)

    await db.flush()
    await db.refresh(attr)
    return attr


@app.delete("/api/attributes/{attribute_id}")
async def delete_attribute(
    attribute_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(AttributeOption).where(AttributeOption.id == attribute_id))
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    attr.is_active = False
    await db.flush()
    return {"message": "Attribute deactivated"}


@app.get("/api/products/{product_id}/attributes", response_model=List[AttributeOptionResponse])
async def get_product_attributes(
    product_id: uuid.UUID,
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(AttributeOption)
        .join(ProductAttribute, ProductAttribute.attribute_option_id == AttributeOption.id)
        .where(ProductAttribute.product_id == product_id)
        .where(AttributeOption.is_active == True)
    )
    return result.scalars().all()


@app.post("/api/products/{product_id}/attributes")
async def add_product_attributes(
    product_id: uuid.UUID,
    attribute_ids: List[uuid.UUID],
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    added = []
    for attr_id in attribute_ids:
        result = await db.execute(select(AttributeOption).where(AttributeOption.id == attr_id))
        attr = result.scalar_one_or_none()
        if not attr:
            continue

        existing = await db.execute(
            select(ProductAttribute).where(
                ProductAttribute.product_id == product_id,
                ProductAttribute.attribute_option_id == attr_id
            )
        )
        if existing.scalar_one_or_none():
            continue

        pa = ProductAttribute(product_id=product_id, attribute_option_id=attr_id)
        db.add(pa)
        added.append(attr_id)

    await db.flush()
    return {"message": f"Added {len(added)} attributes", "added": [str(a) for a in added]}


@app.delete("/api/products/{product_id}/attributes/{attribute_id}")
async def remove_product_attribute(
    product_id: uuid.UUID,
    attribute_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(ProductAttribute).where(
            ProductAttribute.product_id == product_id,
            ProductAttribute.attribute_option_id == attribute_id
        )
    )
    pa = result.scalar_one_or_none()
    if not pa:
        raise HTTPException(status_code=404, detail="Product attribute not found")

    await db.delete(pa)
    await db.flush()
    return {"message": "Attribute removed from product"}


# ==================== PRICE HISTORY ====================

@app.get("/api/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_product_price_history(
    product_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = db_dependency
):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ==================== SESSIONS ====================

@app.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionCreate, db: AsyncSession = db_dependency):
    db_session = Session(station_id=session.station_id, client_user_id=session.client_user_id)
    db.add(db_session)
    await db.flush()
    await db.refresh(db_session)
    return db_session


@app.get("/api/sessions", response_model=List[SessionResponse])
async def get_sessions(db: AsyncSession = db_dependency):
    result = await db.execute(select(Session))
    return result.scalars().all()


@app.post("/api/sessions/cleanup")
async def cleanup_sessions(db: AsyncSession = db_dependency):
    """
    Manually trigger session cleanup and expired cart cancellation.
    Also expires carts belonging to expired sessions.
    """
    try:
        expired_count = await SessionManager.expire_inactive_sessions(db)
        
        await db.execute(
            update(Cart)
            .where(
                Cart.status == CartStatus.building,
                Cart.session_id.in_(
                    select(Session.id).where(Session.status != SessionStatus.active)
                )
            )
            .values(status=CartStatus.cancelled)
        )
        
        await db.commit()
        
        return {
            "success": True,
            "expired_sessions": expired_count,
            "cancelled_carts": expired_count
        }
    except Exception as e:
        logger.error(f"Error in session cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CARTS ====================

@app.post("/api/carts", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(cart: CartCreate, db: AsyncSession = db_dependency):
    existing = await db.execute(
        select(Cart).where(
            and_(
                Cart.session_id == cart.session_id,
                Cart.status == CartStatus.building
            )
        )
    )
    existing_cart = existing.scalar_one_or_none()
    if existing_cart:
        return existing_cart
    
    db_cart = Cart(**cart.model_dump())
    db.add(db_cart)
    await db.flush()
    await db.refresh(db_cart)
    return db_cart


@app.get("/api/carts/by-session/{session_id}", response_model=CartResponse)
async def get_or_create_cart_for_session(session_id: uuid.UUID, db: AsyncSession = db_dependency):
    existing = await db.execute(
        select(Cart).where(
            and_(
                Cart.session_id == session_id,
                Cart.status == CartStatus.building
            )
        )
    )
    existing_cart = existing.scalar_one_or_none()
    if existing_cart:
        return existing_cart
    
    db_cart = Cart(session_id=session_id, status=CartStatus.building)
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
        query = query.where(Cart.status == status.value)
    query = query.order_by(Cart.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


# ==================== CARTS (admin endpoints first - route ordering matters!) ====================

@app.get("/api/carts/admin", response_model=List[CartWithTotal])
async def get_pending_carts_admin(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Cart)
        .where(Cart.status.in_([CartStatus.submitted.value, CartStatus.processing.value]))
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    carts = result.scalars().all()
    
    response = []
    for cart in carts:
        cart_total = sum(float(item.unit_price) * item.quantity for item in cart.items)
        items_response = []
        for i in cart.items:
            item_data = CartItemResponse.model_validate(i)
            if i.product:
                item_data.product = ProductResponse.model_validate(i.product)
            items_response.append(item_data)
        response.append(CartWithTotal(
            id=cart.id,
            session_id=cart.session_id,
            status=cart.status,
            created_at=cart.created_at,
            items=items_response,
            total=cart_total
        ))
    return response


@app.get("/api/carts/{cart_id}", response_model=CartWithItemsResponse)
async def get_cart(cart_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.items).selectinload(CartItem.product),
            selectinload(Cart.items).selectinload(CartItem.product_variant)
        )
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@app.put("/api/carts/{cart_id}")
async def update_cart(cart_id: uuid.UUID, cart_data: CartUpdate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    VALID_TRANSITIONS = {
        CartStatus.building: [CartStatus.submitted, CartStatus.cancelled],
        CartStatus.submitted: [CartStatus.processing, CartStatus.cancelled],
        CartStatus.processing: [CartStatus.paid, CartStatus.cancelled],
        CartStatus.paid: [],
        CartStatus.cancelled: []
    }
    
    if cart_data.status:
        current_status = cart.status
        new_status = cart_data.status
        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{current_status.value}' to '{new_status.value}'. "
                       f"Allowed transitions: {[s.value for s in VALID_TRANSITIONS.get(current_status, [])]}"
            )
        cart.status = new_status
    
    if cart_data.payment_method is not None:
        cart.payment_method = cart_data.payment_method
    if cart_data.notes is not None:
        cart.notes = cart_data.notes
    
    order_data = None
    receipt_data = None
    
    status_value = cart_data.status.value if hasattr(cart_data.status, 'value') else cart_data.status
    if status_value == 'paid' and cart.payment_method:
        items_result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id)
        )
        cart_items = items_result.scalars().all()
        
        subtotal = float(sum(float(item.unit_price) * item.quantity for item in cart_items))
        tax_amount = float(subtotal * 0.16)
        total_amount = float(subtotal + tax_amount)
        
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        
        cashier_result = await db.execute(select(User).where(User.role == UserRole.cashier).limit(1))
        cashier = cashier_result.scalar_one_or_none()
        cashier_id = cashier.id if cashier else None
        cashier_name = cashier.name if cashier else "Cajero"

        db_order = Order(
            cart_id=cart_id,
            order_number=order_number,
            cashier_id=cashier_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_method=cart.payment_method,
            status=OrderStatus.completed,
            completed_at=datetime.now()
        )
        db.add(db_order)
        await db.flush()
        
        order_items_list = []
        for item in cart_items:
            product_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = product_result.scalar_one_or_none()
            product_name = product.name if product else "Producto"
            
            db_order_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                product_variant_id=item.product_variant_id,
                product_name=product_name,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                subtotal=float(item.unit_price) * item.quantity
            )
            db.add(db_order_item)
            order_items_list.append({
                "name": product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "subtotal": float(item.unit_price) * item.quantity
            })
        
        await db.flush()
        
        receipt_number = f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        
        receipt_info = {
            "order_number": order_number,
            "receipt_number": receipt_number,
            "items": order_items_list,
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "payment_method": cart.payment_method.value if hasattr(cart.payment_method, 'value') else cart.payment_method,
            "cashier": cashier_name,
            "created_at": datetime.now().isoformat()
        }
        
        db_receipt = Receipt(
            order_id=db_order.id,
            receipt_number=receipt_number,
            receipt_data=receipt_info
        )
        db.add(db_receipt)
        await db.flush()
        
        order_data = OrderResponse.model_validate(db_order)
        receipt_data = ReceiptResponse.model_validate(db_receipt)
    
    await db.flush()
    await db.refresh(cart)
    
    return {
        "cart": CartResponse.model_validate(cart),
        "order": order_data,
        "receipt": receipt_data
    }


@app.post("/api/carts/{cart_id}/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_cart_item(cart_id: uuid.UUID, item: CartItemCreate, db: AsyncSession = db_dependency):
    result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    variant_id = item.product_variant_id
    unit_price = item.unit_price
    if not variant_id:
        variant_result = await db.execute(
            select(ProductVariant).where(ProductVariant.product_id == item.product_id).limit(1)
        )
        variant = variant_result.scalar_one_or_none()
        if not variant:
            raise HTTPException(status_code=400, detail="No variants available for this product")
        variant_id = variant.id
        if unit_price is None:
            unit_price = float(variant.price_modifier) + 999.99  # base price fallback
    
    if unit_price is None:
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            unit_price = float(product.base_price)
    
    if unit_price is None:
        raise HTTPException(status_code=400, detail="Could not determine unit price")
    
    db_item = CartItem(
        cart_id=cart_id,
        product_id=item.product_id,
        product_variant_id=variant_id,
        quantity=item.quantity,
        unit_price=unit_price,
        detection_confidence=item.detection_confidence,
        detection_image_path=item.detection_image_path,
        detection_bbox=item.detection_bbox
    )
    db.add(db_item)
    await db.flush()
    
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product), selectinload(CartItem.product_variant))
        .where(CartItem.id == db_item.id)
    )
    db_item = result.scalar_one()
    return db_item


@app.delete("/api/carts/{cart_id}/items/{item_id}")
async def remove_cart_item(cart_id: uuid.UUID, item_id: uuid.UUID, db: AsyncSession = db_dependency):
    result = await db.execute(select(CartItem).where(and_(CartItem.id == item_id, CartItem.cart_id == cart_id)))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    return {"message": "Item removed"}


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


@app.get("/api/analytics/sales-by-hour", response_model=List[SalesByHour])
async def get_sales_by_hour(date: str = None, db: AsyncSession = db_dependency):
    if date:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()

    result = await db.execute(
        select(
            func.extract('hour', Order.completed_at).label('hour'),
            func.count(Order.id).label('total_orders'),
            func.coalesce(func.sum(Order.total_amount), 0).label('total_revenue')
        )
        .where(and_(
            Order.status == OrderStatus.completed,
            func.date(Order.completed_at) == target_date
        ))
        .group_by(func.extract('hour', Order.completed_at))
        .order_by(func.extract('hour', Order.completed_at))
    )

    response = []
    for row in result:
        response.append(SalesByHour(
            hour=int(row[0]),
            total_orders=row[1],
            total_revenue=float(row[2])
        ))
    return response


@app.get("/api/analytics/sales-by-category", response_model=List[SalesByCategory])
async def get_sales_by_category(period: str = 'weekly', db: AsyncSession = db_dependency):
    now = datetime.now()
    if period == 'daily':
        start_date = func.current_date()
    elif period == 'weekly':
        start_date = now - timedelta(days=7)
    elif period == 'monthly':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)

    result = await db.execute(
        select(
            Category.id,
            Category.name,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.subtotal).label('total_revenue'),
            func.count(func.distinct(Order.id)).label('order_count')
        )
        .select_from(OrderItem)
        .join(Order)
        .join(Product)
        .join(Category)
        .where(and_(
            Order.status == OrderStatus.completed,
            Order.completed_at >= start_date
        ))
        .group_by(Category.id, Category.name)
        .order_by(func.sum(OrderItem.quantity).desc())
    )

    response = []
    for row in result:
        response.append(SalesByCategory(
            category_id=row[0],
            category_name=row[1],
            total_quantity_sold=row[2] or 0,
            total_revenue=float(row[3] or 0),
            order_count=row[4]
        ))
    return response


@app.get("/api/analytics/inventory-alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(db: AsyncSession = db_dependency):
    result = await db.execute(
        select(
            ProductVariant.id,
            ProductVariant.product_id,
            Product.name,
            func.concat(func.coalesce(ProductVariant.size, ''), ' - ', func.coalesce(ProductVariant.color, '')).label('variant_desc'),
            ProductVariant.sku_variant,
            Inventory.quantity_available,
            Inventory.quantity_reserved,
            Inventory.low_stock_threshold
        )
        .select_from(Inventory)
        .join(ProductVariant)
        .join(Product)
        .where(Inventory.quantity_available <= Inventory.low_stock_threshold)
        .order_by(Inventory.quantity_available.asc())
    )

    response = []
    for row in result:
        qty_available = row[5] or 0
        threshold = row[6] or 5
        status = 'out_of_stock' if qty_available == 0 else 'low_stock'
        response.append(InventoryAlert(
            variant_id=row[0],
            product_id=row[1],
            product_name=row[2],
            variant_description=row[3] or '',
            sku_variant=row[4],
            quantity_available=qty_available,
            quantity_reserved=row[6] or 0,
            low_stock_threshold=threshold,
            status=status
        ))
    return response


@app.get("/api/analytics/comparison", response_model=PeriodComparison)
async def get_period_comparison(period: str = 'weekly', db: AsyncSession = db_dependency):
    now = datetime.now()

    if period == 'weekly':
        current_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        previous_end = current_start
    elif period == 'monthly':
        current_start = now - timedelta(days=30)
        previous_start = now - timedelta(days=60)
        previous_end = current_start
    else:
        current_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)
        previous_end = current_start

    current_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(
            Order.status == OrderStatus.completed,
            Order.completed_at >= current_start
        ))
    )
    current_period = float(current_result.scalar() or 0)

    previous_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(
            Order.status == OrderStatus.completed,
            Order.completed_at >= previous_start,
            Order.completed_at < previous_end
        ))
    )
    previous_period = float(previous_result.scalar() or 0)

    absolute_change = current_period - previous_period
    if previous_period > 0:
        percentage_change = ((current_period - previous_period) / previous_period) * 100
    else:
        percentage_change = 100.0 if current_period > 0 else 0.0

    trend = 'up' if absolute_change > 0 else 'down' if absolute_change < 0 else 'stable'

    return PeriodComparison(
        current_period=current_period,
        previous_period=previous_period,
        absolute_change=absolute_change,
        percentage_change=round(percentage_change, 2),
        trend=trend
    )


@app.get("/api/analytics/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = db_dependency):
    now = datetime.now()
    today_start = func.current_date()

    today_result = await db.execute(
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
            func.coalesce(func.sum(OrderItem.quantity), 0)
        )
        .where(and_(
            Order.status == OrderStatus.completed,
            func.date(Order.completed_at) == today_start
        ))
        .join(OrderItem, Order.id == OrderItem.order_id, isouter=True)
    )
    today_row = today_result.first()
    today_data = DashboardToday(
        total_orders=today_row[0] or 0,
        total_revenue=float(today_row[1] or 0),
        total_items_sold=today_row[2] or 0
    )

    weekly_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(
            Order.status == OrderStatus.completed,
            Order.completed_at >= now - timedelta(days=7)
        ))
    )
    weekly_sales = float(weekly_result.scalar() or 0)

    monthly_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(and_(
            Order.status == OrderStatus.completed,
            Order.completed_at >= now - timedelta(days=30)
        ))
    )
    monthly_sales = float(monthly_result.scalar() or 0)

    comparison = await get_period_comparison('weekly', db)

    sales_by_hour = await get_sales_by_hour(db=db)
    sales_by_category = await get_sales_by_category('weekly', db)
    top_products = await get_top_products(30, db)
    inventory_alerts = await get_inventory_alerts(db)

    return DashboardSummary(
        today=today_data,
        weekly_sales=weekly_sales,
        monthly_sales=monthly_sales,
        comparison=comparison,
        sales_by_hour=sales_by_hour,
        sales_by_category=sales_by_category,
        top_products=top_products,
        inventory_alerts=inventory_alerts
    )


# ==================== POS TERMINAL ====================

pos_transactions = {}


@app.post("/api/payments/pos/init", response_model=POSInitializeResponse)
async def pos_initialize_payment(
    request: POSInitializeRequest,
    db: AsyncSession = db_dependency
):
    from backend.app.services.pos_terminal import terminal

    result = await terminal.initialize_payment(
        amount=request.amount,
        currency=request.currency,
        description=f"Cart payment {request.cart_id}"
    )

    if result["success"]:
        pos_transactions[result["transaction_id"]] = {
            "cart_id": request.cart_id,
            "amount": request.amount,
            "status": result["status"]
        }

    return POSInitializeResponse(
        success=result["success"],
        transaction_id=result["transaction_id"],
        status=result["status"],
        amount=result["amount"],
        message=result.get("message")
    )


@app.post("/api/payments/pos/wait-card")
async def pos_wait_for_card(transaction_id: str):
    from backend.app.services.pos_terminal import terminal

    result = await terminal.wait_for_card_present(transaction_id)

    if transaction_id in pos_transactions:
        pos_transactions[transaction_id]["status"] = result.get("status", "waiting_card")

    return result


@app.post("/api/payments/pos/process")
async def pos_process_payment(transaction_id: str):
    from backend.app.services.pos_terminal import terminal

    result = await terminal.process_payment(transaction_id)

    if transaction_id in pos_transactions:
        pos_transactions[transaction_id]["status"] = result.status.value
        pos_transactions[transaction_id]["result"] = result.to_dict()

    return result.to_dict()


@app.post("/api/payments/pos/cancel")
async def pos_cancel_transaction(transaction_id: str):
    from backend.app.services.pos_terminal import terminal

    result = await terminal.cancel_transaction(transaction_id)

    if transaction_id in pos_transactions:
        pos_transactions[transaction_id]["status"] = "cancelled"

    return result


@app.get("/api/payments/pos/status/{transaction_id}")
async def pos_get_status(transaction_id: str):
    from backend.app.services.pos_terminal import terminal

    return await terminal.get_transaction_status(transaction_id)


@app.get("/api/payments/pos/result/{transaction_id}")
async def pos_get_result(transaction_id: str):
    from backend.app.services.pos_terminal import terminal

    result = terminal.get_transaction_result(transaction_id)
    if result:
        return result.to_dict()
    return {"error": "Transaction not found or not completed"}


@app.post("/api/payments/pos/complete-payment", status_code=status.HTTP_200_OK)
async def pos_complete_payment(
    transaction_id: str,
    cart_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    from backend.app.services.pos_terminal import terminal

    result = terminal.get_transaction_result(transaction_id)

    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if result.status.value != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Payment not approved. Status: {result.status.value}"
        )

    cart_result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .options(selectinload(Cart.items).selectinload(CartItem.product_variant))
        .where(Cart.id == cart_id)
    )
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    subtotal = sum(float(item.unit_price) * item.quantity for item in cart.items)
    tax_amount = subtotal * 0.16
    total_amount = subtotal + tax_amount

    order = Order(
        cart_id=cart_id,
        order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}",
        cashier_id=current_user.id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=PaymentMethod.card,
        cash_received=total_amount,
        change_given=0,
        status=OrderStatus.completed,
        completed_at=datetime.utcnow()
    )
    db.add(order)
    await db.flush()

    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_variant_id=item.product_variant_id,
            product_name=item.product.name if item.product else "Unknown",
            variant_description=f"{item.product_variant.size if item.product_variant else ''} - {item.product_variant.color if item.product_variant else ''}",
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.unit_price) * item.quantity
        )
        db.add(order_item)

        inventory_result = await db.execute(
            select(Inventory).where(Inventory.product_variant_id == item.product_variant_id)
        )
        inventory = inventory_result.scalar_one_or_none()
        if inventory:
            inventory.quantity_available -= item.quantity

            movement = InventoryMovement(
                product_variant_id=item.product_variant_id,
                movement_type=MovementType.sale,
                quantity_change=-item.quantity,
                quantity_before=inventory.quantity_available + item.quantity,
                quantity_after=inventory.quantity_available,
                reference_id=order.id,
                notes=f"Venta orden {order.order_number}",
                created_by=current_user.id
            )
            db.add(movement)

    cart.status = CartStatus.paid
    await db.flush()

    receipt_data = {
        "order_number": order.order_number,
        "receipt_number": f"REC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}",
        "items": [
            {
                "name": item.product.name if item.product else "Unknown",
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "subtotal": float(item.unit_price) * item.quantity
            }
            for item in cart.items
        ],
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "payment_method": "card",
        "card_last_four": result.card_last_four,
        "authorization_code": result.authorization_code,
        "transaction_id": transaction_id,
        "cashier": current_user.name,
        "created_at": datetime.utcnow().isoformat()
    }

    receipt = Receipt(
        order_id=order.id,
        receipt_number=receipt_data["receipt_number"],
        receipt_data=receipt_data
    )
    db.add(receipt)
    await db.flush()

    queue_result = await db.execute(
        select(PaymentQueue).where(PaymentQueue.cart_id == cart_id)
    )
    queue_entry = queue_result.scalar_one_or_none()
    if queue_entry:
        queue_entry.status = QueueStatus.completed

    await db.commit()

    return {
        "success": True,
        "order_id": str(order.id),
        "order_number": order.order_number,
        "receipt": receipt_data,
        "receipt_id": str(receipt.id)
    }


@app.get("/api/printers/drivers")
async def get_printer_drivers():
    """
    Get list of available printer drivers.

    Returns available driver types and their names.
    """
    from backend.app.services.printers import ReceiptPrinterService, DriverType

    drivers = ReceiptPrinterService.get_available_drivers()
    return {
        "drivers": [
            {"type": dt.value, "name": name}
            for dt, name in drivers
        ]
    }


@app.get("/api/printers/driver")
async def get_current_printer_driver():
    """
    Get the currently active printer driver.

    Returns the active driver type and name.
    """
    from backend.app.services.printers import ReceiptPrinterService, DriverType

    driver_type, driver_name = ReceiptPrinterService.get_current_driver()
    return {
        "type": driver_type.value,
        "name": driver_name
    }


@app.post("/api/printers/driver")
async def set_printer_driver(driver_type: str):
    """
    Change the active printer driver.

    Args:
        driver_type: One of 'mock', 'textfile', 'html', 'escpos'

    Returns confirmation message.
    """
    from backend.app.services.printers import ReceiptPrinterService, DriverType

    try:
        driver_enum = DriverType.from_string(driver_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ReceiptPrinterService.set_driver(driver_enum)
    _, driver_name = ReceiptPrinterService.get_current_driver()

    return {
        "message": f"Printer driver changed to {driver_type}",
        "active_driver": driver_name
    }


@app.post("/api/receipts/{receipt_id}/print")
async def print_receipt(
    receipt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = db_dependency
):
    """
    Print a receipt using the current active driver.

    Args:
        receipt_id: UUID of the receipt to print

    Returns:
        PrintResult with success status and output info
    """
    from backend.app.services.printers import ReceiptPrinterService

    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = result.scalar_one_or_none()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    print_result = await ReceiptPrinterService.print_receipt(receipt.receipt_data)

    if print_result.success and not receipt.printed_at:
        from datetime import datetime
        receipt.printed_at = datetime.utcnow()
        await db.commit()

    return print_result.to_dict()


@app.get("/api/receipts/{receipt_id}/preview")
async def preview_receipt(
    receipt_id: uuid.UUID,
    db: AsyncSession = db_dependency
):
    """
    Generate an HTML preview of a receipt.

    Args:
        receipt_id: UUID of the receipt to preview

    Returns:
        HTML string of the receipt preview
    """
    from backend.app.services.printers import ReceiptPrinterService

    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    receipt = result.scalar_one_or_none()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    html = await ReceiptPrinterService.preview_receipt(receipt.receipt_data)

    return {"html": html}
