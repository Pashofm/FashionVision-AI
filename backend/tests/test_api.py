import pytest
import uuid
from decimal import Decimal


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_success(self, client, admin_user):
        response = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "testpassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        response = await client.post("/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, admin_user):
        login_response = await client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "testpassword123"
        })
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client):
        response = await client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_status_authorized(self, authenticated_client):
        response = await authenticated_client.get("/api/auth/session/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_session_status_unauthorized(self, client):
        response = await client.get("/api/auth/session/status")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_session_extend(self, authenticated_client):
        response = await authenticated_client.get("/api/auth/session/extend")
        assert response.status_code == 200


class TestUserEndpoints:
    @pytest.mark.asyncio
    async def test_create_user(self, client):
        response = await client.post("/api/users", json={
            "name": "New User",
            "email": "newuser@test.com",
            "password": "password123",
            "role": "client"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "newuser@test.com"

    @pytest.mark.asyncio
    async def test_list_users(self, authenticated_client, admin_user):
        response = await authenticated_client.get("/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(u["email"] == "admin@test.com" for u in data)

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, authenticated_client, admin_user):
        response = await authenticated_client.get(f"/api/users/{admin_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"

    @pytest.mark.asyncio
    async def test_update_user(self, authenticated_client, admin_user):
        response = await authenticated_client.put(f"/api/users/{admin_user.id}", json={
            "name": "Updated Admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Admin"


class TestCategoryEndpoints:
    @pytest.mark.asyncio
    async def test_get_categories(self, client):
        response = await client.get("/api/categories")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_category(self, authenticated_client):
        response = await authenticated_client.post("/api/categories", json={
            "name": "Test Category",
            "description": "Test description"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Category"

    @pytest.mark.asyncio
    async def test_get_category_by_id(self, authenticated_client, test_category):
        response = await authenticated_client.get(f"/api/categories/{test_category.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_category(self, authenticated_client, test_category):
        response = await authenticated_client.put(f"/api/categories/{test_category.id}", json={
            "name": "Updated Category"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Category"

    @pytest.mark.asyncio
    async def test_create_category_unauthorized(self, client):
        response = await client.post("/api/categories", json={
            "name": "Unauthorized Category"
        })
        assert response.status_code == 403


class TestProductEndpoints:
    @pytest.mark.asyncio
    async def test_get_products(self, client):
        response = await client.get("/api/products")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_products_with_filters(self, authenticated_client):
        response = await authenticated_client.get("/api/products?search=test&limit=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_product(self, authenticated_client, test_category):
        response = await authenticated_client.post("/api/products", json={
            "name": "New Product",
            "category_id": str(test_category.id),
            "sku": "NEW-PROD-001",
            "base_price": 79.99
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, authenticated_client, test_product):
        response = await authenticated_client.get(f"/api/products/{test_product.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_product(self, authenticated_client, test_product):
        response = await authenticated_client.put(f"/api/products/{test_product.id}", json={
            "name": "Updated Product"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Product"

    @pytest.mark.asyncio
    async def test_delete_product(self, authenticated_client, test_product):
        response = await authenticated_client.delete(f"/api/products/{test_product.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_product_by_yolo_class(self, client, test_product):
        response = await client.get(f"/api/products/by-yolo/{test_product.yolo_class_name}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_products_with_variants(self, authenticated_client, test_product):
        response = await authenticated_client.get("/api/products/with-variants")
        assert response.status_code == 200


class TestProductVariantEndpoints:
    @pytest.mark.asyncio
    async def test_create_variant(self, authenticated_client, test_product):
        response = await authenticated_client.post(f"/api/products/{test_product.id}/variants", json={
            "size": "L",
            "color": "Blue",
            "color_hex": "#0000FF",
            "sku_variant": "NEW-VAR-001",
            "price_modifier": 5.00
        })
        assert response.status_code == 201
        data = response.json()
        assert data["size"] == "L"

    @pytest.mark.asyncio
    async def test_get_variants(self, authenticated_client, test_product):
        response = await authenticated_client.get(f"/api/products/{test_product.id}/variants")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_variant(self, authenticated_client, test_product, test_variant):
        response = await authenticated_client.put(
            f"/api/products/{test_product.id}/variants/{test_variant.id}",
            json={"price_modifier": 15.00}
        )
        assert response.status_code == 200
        assert float(response.json()["price_modifier"]) == 15.00

    @pytest.mark.asyncio
    async def test_delete_variant(self, authenticated_client, test_product, test_variant):
        response = await authenticated_client.delete(
            f"/api/products/{test_product.id}/variants/{test_variant.id}"
        )
        assert response.status_code == 200


class TestInventoryEndpoints:
    @pytest.mark.asyncio
    async def test_get_inventory(self, client):
        response = await client.get("/api/inventory")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_inventory(self, authenticated_client, test_variant):
        response = await authenticated_client.post("/api/inventory", json={
            "product_variant_id": str(test_variant.id),
            "quantity_available": 50,
            "low_stock_threshold": 10
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_inventory_by_variant(self, authenticated_client, test_inventory):
        response = await authenticated_client.get(f"/api/inventory/{test_variant.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_inventory(self, authenticated_client, test_inventory):
        response = await authenticated_client.put(f"/api/inventory/{test_inventory.id}", json={
            "quantity_available": 75
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_adjust_inventory(self, authenticated_client, test_variant, test_inventory):
        response = await authenticated_client.post("/api/inventory/adjust", json={
            "variant_id": str(test_variant.id),
            "quantity": 5,
            "reason": "Manual adjustment"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_restock_inventory(self, authenticated_client, test_variant):
        response = await authenticated_client.post("/api/inventory/restock", json={
            "variant_id": str(test_variant.id),
            "quantity": 100,
            "notes": "Supplier delivery"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_low_stock(self, authenticated_client, test_inventory):
        response = await authenticated_client.get("/api/inventory/low-stock")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_update_threshold(self, authenticated_client, test_variant, test_inventory):
        response = await authenticated_client.put(
            f"/api/inventory/{test_variant.id}/threshold",
            json={"threshold": 20}
        )
        assert response.status_code == 200


class TestInventoryMovementEndpoints:
    @pytest.mark.asyncio
    async def test_create_movement(self, authenticated_client, test_variant, test_inventory):
        response = await authenticated_client.post("/api/inventory-movements", json={
            "product_variant_id": str(test_variant.id),
            "movement_type": "adjustment",
            "quantity_change": 10,
            "quantity_before": 100,
            "quantity_after": 110,
            "notes": "Test movement"
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_movements(self, authenticated_client, test_variant):
        response = await authenticated_client.get(
            f"/api/inventory-movements?variant_id={test_variant.id}"
        )
        assert response.status_code == 200


class TestSessionEndpoints:
    @pytest.mark.asyncio
    async def test_create_session(self, client, client_user):
        response = await client.post("/api/sessions", json={
            "client_user_id": str(client_user.id),
            "station_id": "Kiosk-01"
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_sessions(self, client):
        response = await client.get("/api/sessions")
        assert response.status_code == 200


class TestCartEndpoints:
    @pytest.mark.asyncio
    async def test_create_cart(self, client, test_session):
        response = await client.post("/api/carts", json={
            "session_id": str(test_session.id)
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_carts(self, authenticated_client):
        response = await authenticated_client.get("/api/carts")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_pending_carts(self, authenticated_client, test_cart):
        response = await authenticated_client.get("/api/carts/admin")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_cart_by_id(self, authenticated_client, test_cart):
        response = await authenticated_client.get(f"/api/carts/{test_cart.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_cart_status(self, authenticated_client, test_cart):
        response = await authenticated_client.put(f"/api/carts/{test_cart.id}", json={
            "status": "submitted"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_cart_item(self, client, test_cart, test_product, test_variant):
        response = await client.post(f"/api/carts/{test_cart.id}/items", json={
            "product_id": str(test_product.id),
            "product_variant_id": str(test_variant.id),
            "quantity": 2,
            "unit_price": 109.99,
            "detection_confidence": 0.95
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_remove_cart_item(self, client, test_cart, test_cart_item):
        response = await client.delete(f"/api/carts/{test_cart.id}/items/{test_cart_item.id}")
        assert response.status_code == 200


class TestPaymentQueueEndpoints:
    @pytest.mark.asyncio
    async def test_create_payment_queue(self, authenticated_client, test_cart):
        response = await authenticated_client.post("/api/payment-queue", json={
            "cart_id": str(test_cart.id),
            "priority": "normal"
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_payment_queue(self, authenticated_client):
        response = await authenticated_client.get("/api/payment-queue")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_active_payment_queue(self, authenticated_client):
        response = await authenticated_client.get("/api/payment-queue/active")
        assert response.status_code == 200


class TestOrderEndpoints:
    @pytest.mark.asyncio
    async def test_create_order(self, authenticated_client, test_cart, cashier_user):
        response = await authenticated_client.post("/api/orders", json={
            "cart_id": str(test_cart.id),
            "cashier_id": str(cashier_user.id)
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_orders(self, authenticated_client):
        response = await authenticated_client.get("/api/orders")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, authenticated_client, test_order):
        response = await authenticated_client.get(f"/api/orders/{test_order.id}")
        assert response.status_code == 200


class TestReceiptEndpoints:
    @pytest.mark.asyncio
    async def test_create_receipt(self, authenticated_client, test_order):
        response = await authenticated_client.post("/api/receipts", json={
            "order_id": str(test_order.id),
            "receipt_data": {"total": 255.18}
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_receipts(self, authenticated_client):
        response = await authenticated_client.get("/api/receipts")
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_get_today_analytics(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/dashboard/today")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data

    @pytest.mark.asyncio
    async def test_get_top_products(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/top-products?days=30")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_sales_analytics(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/sales")
        assert response.status_code == 200
        data = response.json()
        assert "monthly_sales" in data

    @pytest.mark.asyncio
    async def test_get_sales_by_hour(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/sales-by-hour?date=2024-01-15")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_sales_by_category(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/sales-by-category?period=weekly")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_inventory_alerts(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/inventory-alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_comparison(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/comparison?period=weekly")
        assert response.status_code == 200
        data = response.json()
        assert "current_period" in data
        assert "percentage_change" in data

    @pytest.mark.asyncio
    async def test_get_dashboard_summary(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "today" in data


class TestPOSTerminalEndpoints:
    @pytest.mark.asyncio
    async def test_pos_initialize_payment(self, authenticated_client, test_cart):
        response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(test_cart.id),
            "amount": 100.00,
            "currency": "MXN"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data

    @pytest.mark.asyncio
    async def test_pos_wait_for_card(self, authenticated_client):
        init_response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00
        })
        transaction_id = init_response.json()["transaction_id"]

        response = await authenticated_client.post("/api/payments/pos/wait-card", json={
            "transaction_id": transaction_id
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pos_process_payment(self, authenticated_client):
        init_response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00
        })
        transaction_id = init_response.json()["transaction_id"]

        response = await authenticated_client.post("/api/payments/pos/process", json={
            "transaction_id": transaction_id
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pos_cancel_transaction(self, authenticated_client):
        init_response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00
        })
        transaction_id = init_response.json()["transaction_id"]

        response = await authenticated_client.post("/api/payments/pos/cancel", json={
            "transaction_id": transaction_id
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pos_get_status(self, authenticated_client):
        init_response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00
        })
        transaction_id = init_response.json()["transaction_id"]

        response = await authenticated_client.get(f"/api/payments/pos/status/{transaction_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pos_get_result(self, authenticated_client):
        init_response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00
        })
        transaction_id = init_response.json()["transaction_id"]

        response = await authenticated_client.get(f"/api/payments/pos/result/{transaction_id}")
        assert response.status_code == 200


class TestDetectionEndpoints:
    @pytest.mark.asyncio
    async def test_get_detection_classes(self, client):
        response = await client.get("/api/detect/classes")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_detection_health(self, client):
        response = await client.get("/api/detect/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_detect_no_image(self, client):
        response = await client.post("/api/detect")
        assert response.status_code == 422


class TestUploadEndpoints:
    @pytest.mark.asyncio
    async def test_upload_image_unauthorized(self, client):
        response = await client.post("/api/upload/image")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_image_unauthorized(self, client):
        response = await client.delete("/api/upload/image/test-public-id")
        assert response.status_code == 401
