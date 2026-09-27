"""
Inventory API Integration Tests

Tests for inventory-related API endpoints:
- GET /api/inventory
- POST /api/inventory
- PUT /api/inventory/{id}
- POST /api/inventory/adjust
- POST /api/inventory/restock
- GET /api/inventory/low-stock
- PUT /api/inventory/{variant_id}/threshold
"""
import pytest
import uuid
from decimal import Decimal

from backend.app.models.models import Inventory, InventoryMovement, MovementType
from tests.factories import (
    InventoryFactory, ProductVariantFactory, UserFactory, CategoryFactory,
    ProductFactory
)


pytestmark = pytest.mark.asyncio


class TestInventoryAPIEndpoints:
    """Tests for inventory API endpoints."""

    async def test_get_inventory_empty(self, authenticated_client):
        """Test getting inventory when empty."""
        response = await authenticated_client.get("/api/inventory")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_inventory_with_items(self, authenticated_client, test_inventory):
        """Test getting inventory with items."""
        response = await authenticated_client.get("/api/inventory")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_inventory(self, authenticated_client, test_variant):
        """Test creating inventory via API."""
        response = await authenticated_client.post("/api/inventory", json={
            "product_variant_id": str(test_variant.id),
            "quantity_available": 50,
            "low_stock_threshold": 10
        })
        assert response.status_code == 201
        data = response.json()
        assert data["quantity_available"] == 50

    async def test_create_inventory_without_auth_fails(self, client, test_variant):
        """Test that creating inventory without auth fails."""
        response = await client.post("/api/inventory", json={
            "product_variant_id": str(test_variant.id),
            "quantity_available": 50
        })
        assert response.status_code == 403

    async def test_get_inventory_by_variant_id(
        self, authenticated_client, test_inventory, test_variant
    ):
        """Test getting inventory by variant ID."""
        response = await authenticated_client.get(
            f"/api/inventory/{test_variant.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["product_variant_id"] == str(test_variant.id)

    async def test_get_inventory_not_found(self, authenticated_client):
        """Test getting non-existent inventory."""
        response = await authenticated_client.get(
            f"/api/inventory/{uuid.uuid4()}"
        )
        assert response.status_code == 404

    async def test_update_inventory(
        self, authenticated_client, test_inventory
    ):
        """Test updating inventory quantity."""
        response = await authenticated_client.put(
            f"/api/inventory/{test_inventory.id}",
            json={"quantity_available": 75}
        )
        assert response.status_code == 200
        data = response.json()
        assert int(data["quantity_available"]) == 75

    async def test_adjust_inventory(
        self, authenticated_client, test_variant, admin_user
    ):
        """Test adjusting inventory via API."""
        InventoryFactory.create(
            db_session=None,
            variant=test_variant,
            quantity_available=100
        )

        response = await authenticated_client.post("/api/inventory/adjust", json={
            "variant_id": str(test_variant.id),
            "quantity": 5,
            "reason": "Manual adjustment"
        })
        assert response.status_code == 200

    async def test_adjust_inventory_invalid_variant(
        self, authenticated_client
    ):
        """Test adjusting non-existent variant."""
        response = await authenticated_client.post("/api/inventory/adjust", json={
            "variant_id": str(uuid.uuid4()),
            "quantity": 5,
            "reason": "Test"
        })
        assert response.status_code == 404

    async def test_restock_inventory(
        self, authenticated_client, test_variant
    ):
        """Test restocking inventory via API."""
        response = await authenticated_client.post("/api/inventory/restock", json={
            "variant_id": str(test_variant.id),
            "quantity": 100,
            "notes": "Supplier delivery"
        })
        assert response.status_code == 200

    async def test_get_low_stock(
        self, authenticated_client, db_session
    ):
        """Test getting low stock inventory."""
        await InventoryFactory.create(
            db_session,
            quantity_available=5,
            low_stock_threshold=10
        )
        await InventoryFactory.create(
            db_session,
            quantity_available=20,
            low_stock_threshold=10
        )

        response = await authenticated_client.get("/api/inventory/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_update_threshold(
        self, authenticated_client, test_variant, test_inventory
    ):
        """Test updating low stock threshold."""
        response = await authenticated_client.put(
            f"/api/inventory/{test_variant.id}/threshold",
            json={"threshold": 20}
        )
        assert response.status_code == 200


class TestInventoryMovementAPI:
    """Tests for inventory movement API endpoints."""

    async def test_create_movement(
        self, authenticated_client, test_variant, test_inventory
    ):
        """Test creating an inventory movement."""
        response = await authenticated_client.post("/api/inventory-movements", json={
            "product_variant_id": str(test_variant.id),
            "movement_type": "adjustment",
            "quantity_change": 10,
            "quantity_before": 100,
            "quantity_after": 110,
            "notes": "Test movement"
        })
        assert response.status_code == 201

    async def test_get_movements(
        self, authenticated_client, test_variant
    ):
        """Test getting inventory movements."""
        response = await authenticated_client.get(
            f"/api/inventory-movements?variant_id={test_variant.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_movements_by_type(
        self, authenticated_client, test_variant
    ):
        """Test filtering movements by type."""
        response = await authenticated_client.get(
            f"/api/inventory-movements?variant_id={test_variant.id}&type=sale"
        )
        assert response.status_code == 200
