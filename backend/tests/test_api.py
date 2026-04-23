import pytest
import uuid


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
    async def test_refresh_token_invalid(self, client):
        response = await client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_status_unauthorized(self, client):
        response = await client.get("/api/auth/session/status")
        assert response.status_code == 403


class TestCategoryEndpoints:
    @pytest.mark.asyncio
    async def test_get_categories_empty(self, client):
        response = await client.get("/api/categories")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_category_unauthorized(self, client):
        response = await client.post("/api/categories", json={
            "name": "Test Category"
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_and_get_category(self, authenticated_client):
        category_data = {
            "name": "Test Category",
            "description": "Test description"
        }
        create_response = await authenticated_client.post("/api/categories", json=category_data)
        assert create_response.status_code == 201
        category_id = create_response.json()["id"]

        get_response = await authenticated_client.get(f"/api/categories/{category_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Test Category"


class TestProductEndpoints:
    @pytest.mark.asyncio
    async def test_get_products_empty(self, client):
        response = await client.get("/api/products")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_product_unauthorized(self, client):
        response = await client.post("/api/products", json={
            "name": "Test Product",
            "sku": "TEST-001",
            "base_price": 99.99
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, authenticated_client):
        fake_id = str(uuid.uuid4())
        response = await authenticated_client.get(f"/api/products/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_products_with_filters(self, authenticated_client):
        response = await authenticated_client.get("/api/products?search=test&limit=10")
        assert response.status_code == 200


class TestInventoryEndpoints:
    @pytest.mark.asyncio
    async def test_get_inventory_empty(self, client):
        response = await client.get("/api/inventory")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_low_stock_empty(self, authenticated_client):
        response = await authenticated_client.get("/api/inventory/low-stock")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCartEndpoints:
    @pytest.mark.asyncio
    async def test_get_carts_empty(self, authenticated_client):
        response = await authenticated_client.get("/api/carts")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_pending_carts(self, authenticated_client):
        response = await authenticated_client.get("/api/carts/admin")
        assert response.status_code == 200


class TestPOSTerminalEndpoints:
    @pytest.mark.asyncio
    async def test_pos_initialize_payment(self, authenticated_client):
        response = await authenticated_client.post("/api/payments/pos/init", json={
            "cart_id": str(uuid.uuid4()),
            "amount": 100.00,
            "currency": "MXN"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data

    @pytest.mark.asyncio
    async def test_pos_get_status_invalid(self, authenticated_client):
        response = await authenticated_client.get("/api/payments/pos/status/invalid-txn")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pos_cancel_invalid(self, authenticated_client):
        response = await authenticated_client.post("/api/payments/pos/cancel", json={
            "transaction_id": "invalid-txn"
        })
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    async def test_get_today_analytics(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/dashboard/today")
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "total_items_sold" in data

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
        assert "weekly_sales" in data
        assert "daily_sales" in data

    @pytest.mark.asyncio
    async def test_get_comparison(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/comparison?period=weekly")
        assert response.status_code == 200
        data = response.json()
        assert "current_period" in data
        assert "previous_period" in data
        assert "percentage_change" in data
        assert "trend" in data

    @pytest.mark.asyncio
    async def test_get_dashboard_summary(self, authenticated_client):
        response = await authenticated_client.get("/api/analytics/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "weekly_sales" in data
        assert "monthly_sales" in data
        assert "comparison" in data