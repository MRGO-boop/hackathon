"""Integration tests for Product Manager component."""
import pytest
import uuid
from core_inventory.components.product_manager import ProductManager
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.move_history import MoveHistory, DocumentType
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User


@pytest.fixture
def setup_data(db_session):
    """Setup test data with locations and user."""
    location1 = Location(
        id=uuid.uuid4(),
        name="Warehouse A",
        type=LocationType.warehouse,
        is_archived=False
    )
    location2 = Location(
        id=uuid.uuid4(),
        name="Warehouse B",
        type=LocationType.warehouse,
        is_archived=False
    )
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User"
    )
    db_session.add_all([location1, location2, user])
    db_session.commit()
    
    return {
        "location1": location1,
        "location2": location2,
        "user": user
    }


class TestProductManagerIntegration:
    """Integration tests for complete product management workflows."""
    
    def test_complete_product_lifecycle(self, db_session, setup_data):
        """Test complete product lifecycle: create, update, search, filter."""
        pm = ProductManager(db_session)
        
        # Create product with initial stock
        product = pm.create_product(
            sku="LAPTOP-001",
            name="Dell Laptop",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=5,
            initial_stock_quantity=50,
            initial_stock_location_id=str(setup_data["location1"].id),
            user_id=str(setup_data["user"].id)
        )
        
        # Verify product created
        assert product.sku == "LAPTOP-001"
        assert product.name == "Dell Laptop"
        
        # Verify stock created
        stock = db_session.query(Stock).filter(
            Stock.product_id == product.id
        ).first()
        assert stock.quantity == 50
        
        # Verify history created
        history = db_session.query(MoveHistory).filter(
            MoveHistory.product_id == product.id
        ).first()
        assert history.quantity_change == 50
        assert history.document_type == DocumentType.initial_stock

        
        # Update product
        updated = pm.update_product(
            product_id=str(product.id),
            name="Dell Latitude Laptop",
            low_stock_threshold=10
        )
        assert updated.name == "Dell Latitude Laptop"
        assert updated.sku == "LAPTOP-001"  # SKU preserved
        assert updated.low_stock_threshold == 10
        
        # Search by SKU
        search_results = pm.search_products("LAPTOP-001")
        assert len(search_results) == 1
        assert search_results[0].id == product.id
        
        # Search by name
        search_results = pm.search_products("Latitude")
        assert len(search_results) == 1
        assert search_results[0].id == product.id
        
        # Filter by category
        filter_results = pm.filter_products(category="Electronics")
        assert len(filter_results) == 1
        assert filter_results[0].id == product.id
        
        # Get product
        retrieved = pm.get_product(str(product.id))
        assert retrieved.id == product.id
        assert retrieved.name == "Dell Latitude Laptop"
    
    def test_multiple_products_search_and_filter(self, db_session, setup_data):
        """Test search and filter with multiple products."""
        pm = ProductManager(db_session)
        
        # Create multiple products
        laptop = pm.create_product(
            sku="LAPTOP-001",
            name="Dell Laptop",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        phone = pm.create_product(
            sku="PHONE-001",
            name="iPhone",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        desk = pm.create_product(
            sku="DESK-001",
            name="Office Desk",
            category="Furniture",
            unit_of_measure="pieces"
        )
        
        # Search by partial name
        results = pm.search_products("Laptop")
        assert len(results) == 1
        assert results[0].sku == "LAPTOP-001"
        
        # Filter by Electronics category
        results = pm.filter_products(category="Electronics")
        assert len(results) == 2
        assert all(p.category == "Electronics" for p in results)
        
        # Filter by Furniture category
        results = pm.filter_products(category="Furniture")
        assert len(results) == 1
        assert results[0].sku == "DESK-001"
    
    def test_sku_uniqueness_across_categories(self, db_session):
        """Test that SKU uniqueness is enforced across all categories."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="PROD-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        # Try to create product with same SKU in different category
        with pytest.raises(Exception) as exc_info:
            pm.create_product(
                sku="PROD-001",
                name="Product 2",
                category="Furniture",
                unit_of_measure="pieces"
            )
        
        assert "already exists" in str(exc_info.value).lower() or "SKU_EXISTS" in str(exc_info.value)
