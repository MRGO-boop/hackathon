"""Unit tests for Product Manager component."""
import pytest
import uuid
from core_inventory.components.product_manager import ProductManager, ProductError
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.move_history import MoveHistory, DocumentType
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User


@pytest.fixture
def sample_location(db_session):
    """Create a sample location for testing."""
    location = Location(
        id=uuid.uuid4(),
        name="Test Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestCreateProduct:
    """Tests for create_product functionality."""
    
    def test_successful_product_creation(self, db_session):
        """Test successful product creation with valid data."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-001",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        assert product.sku == "SKU-001"
        assert product.name == "Test Product"
        assert product.category == "Electronics"
        assert product.unit_of_measure == "pieces"
        assert product.id is not None
        assert product.low_stock_threshold is None
    
    def test_create_product_with_low_stock_threshold(self, db_session):
        """Test creating product with low stock threshold."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-002",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        
        assert product.low_stock_threshold == 10
    
    def test_create_product_normalizes_sku(self, db_session):
        """Test that product creation normalizes SKU by trimming whitespace."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="  SKU-003  ",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        assert product.sku == "SKU-003"
    
    def test_create_product_duplicate_sku_fails(self, db_session):
        """Test that creating product with duplicate SKU fails."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-001",
            name="First Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-001",
                name="Second Product",
                category="Electronics",
                unit_of_measure="pieces"
            )
        
        assert exc_info.value.code == "SKU_EXISTS"
        assert "already exists" in exc_info.value.message.lower()

    
    def test_create_product_empty_sku_fails(self, db_session):
        """Test that creating product with empty SKU fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="",
                name="Test Product",
                category="Electronics",
                unit_of_measure="pieces"
            )
        
        assert exc_info.value.code == "INVALID_SKU"
    
    def test_create_product_empty_name_fails(self, db_session):
        """Test that creating product with empty name fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-001",
                name="",
                category="Electronics",
                unit_of_measure="pieces"
            )
        
        assert exc_info.value.code == "INVALID_NAME"
    
    def test_create_product_empty_category_fails(self, db_session):
        """Test that creating product with empty category fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-001",
                name="Test Product",
                category="",
                unit_of_measure="pieces"
            )
        
        assert exc_info.value.code == "INVALID_CATEGORY"
    
    def test_create_product_empty_unit_fails(self, db_session):
        """Test that creating product with empty unit of measure fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-001",
                name="Test Product",
                category="Electronics",
                unit_of_measure=""
            )
        
        assert exc_info.value.code == "INVALID_UNIT"

    
    def test_create_product_with_initial_stock(self, db_session, sample_location, sample_user):
        """Test creating product with initial stock creates stock and history."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-004",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces",
            initial_stock_quantity=100,
            initial_stock_location_id=str(sample_location.id),
            user_id=str(sample_user.id)
        )
        
        # Verify product created
        assert product.id is not None
        
        # Verify stock created
        stock = db_session.query(Stock).filter(
            Stock.product_id == product.id,
            Stock.location_id == sample_location.id
        ).first()
        assert stock is not None
        assert stock.quantity == 100
        
        # Verify move history created
        history = db_session.query(MoveHistory).filter(
            MoveHistory.product_id == product.id,
            MoveHistory.document_type == DocumentType.initial_stock
        ).first()
        assert history is not None
        assert history.quantity_change == 100
        assert history.location_id == sample_location.id
        assert history.user_id == sample_user.id
    
    def test_create_product_initial_stock_without_location_fails(self, db_session, sample_user):
        """Test that creating product with initial stock but no location fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-005",
                name="Test Product",
                category="Electronics",
                unit_of_measure="pieces",
                initial_stock_quantity=100,
                user_id=str(sample_user.id)
            )
        
        assert exc_info.value.code == "MISSING_LOCATION"
    
    def test_create_product_initial_stock_without_user_fails(self, db_session, sample_location):
        """Test that creating product with initial stock but no user fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.create_product(
                sku="SKU-006",
                name="Test Product",
                category="Electronics",
                unit_of_measure="pieces",
                initial_stock_quantity=100,
                initial_stock_location_id=str(sample_location.id)
            )
        
        assert exc_info.value.code == "MISSING_USER"



class TestUpdateProduct:
    """Tests for update_product functionality."""
    
    def test_successful_product_update(self, db_session):
        """Test successful product update."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-010",
            name="Original Name",
            category="Original Category",
            unit_of_measure="pieces"
        )
        
        updated = pm.update_product(
            product_id=str(product.id),
            name="Updated Name",
            category="Updated Category",
            unit_of_measure="kg"
        )
        
        assert updated.name == "Updated Name"
        assert updated.category == "Updated Category"
        assert updated.unit_of_measure == "kg"
        assert updated.sku == "SKU-010"  # SKU should not change
    
    def test_update_product_preserves_sku(self, db_session):
        """Test that updating product preserves original SKU."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-011",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        original_sku = product.sku
        
        updated = pm.update_product(
            product_id=str(product.id),
            name="Updated Name"
        )
        
        assert updated.sku == original_sku
    
    def test_update_product_partial_update(self, db_session):
        """Test that partial update only changes specified fields."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-012",
            name="Original Name",
            category="Original Category",
            unit_of_measure="pieces"
        )
        
        updated = pm.update_product(
            product_id=str(product.id),
            name="Updated Name"
        )
        
        assert updated.name == "Updated Name"
        assert updated.category == "Original Category"
        assert updated.unit_of_measure == "pieces"

    
    def test_update_product_low_stock_threshold(self, db_session):
        """Test updating low stock threshold."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-013",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        updated = pm.update_product(
            product_id=str(product.id),
            low_stock_threshold=50
        )
        
        assert updated.low_stock_threshold == 50
    
    def test_update_product_not_found_fails(self, db_session):
        """Test that updating non-existent product fails."""
        pm = ProductManager(db_session)
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(ProductError) as exc_info:
            pm.update_product(
                product_id=fake_id,
                name="Updated Name"
            )
        
        assert exc_info.value.code == "PRODUCT_NOT_FOUND"
    
    def test_update_product_invalid_id_format_fails(self, db_session):
        """Test that updating with invalid ID format fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.update_product(
                product_id="not-a-uuid",
                name="Updated Name"
            )
        
        assert exc_info.value.code == "INVALID_PRODUCT_ID"
    
    def test_update_product_empty_name_fails(self, db_session):
        """Test that updating with empty name fails."""
        pm = ProductManager(db_session)
        
        product = pm.create_product(
            sku="SKU-014",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        with pytest.raises(ProductError) as exc_info:
            pm.update_product(
                product_id=str(product.id),
                name=""
            )
        
        assert exc_info.value.code == "INVALID_NAME"



class TestGetProduct:
    """Tests for get_product functionality."""
    
    def test_successful_get_product(self, db_session):
        """Test successfully retrieving a product."""
        pm = ProductManager(db_session)
        
        created = pm.create_product(
            sku="SKU-020",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        retrieved = pm.get_product(str(created.id))
        
        assert retrieved.id == created.id
        assert retrieved.sku == created.sku
        assert retrieved.name == created.name
    
    def test_get_product_not_found_fails(self, db_session):
        """Test that getting non-existent product fails."""
        pm = ProductManager(db_session)
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(ProductError) as exc_info:
            pm.get_product(fake_id)
        
        assert exc_info.value.code == "PRODUCT_NOT_FOUND"
    
    def test_get_product_invalid_id_format_fails(self, db_session):
        """Test that getting product with invalid ID format fails."""
        pm = ProductManager(db_session)
        
        with pytest.raises(ProductError) as exc_info:
            pm.get_product("not-a-uuid")
        
        assert exc_info.value.code == "INVALID_PRODUCT_ID"


class TestSearchProducts:
    """Tests for search_products functionality."""
    
    def test_search_by_exact_sku(self, db_session):
        """Test searching products by exact SKU match."""
        pm = ProductManager(db_session)
        
        product1 = pm.create_product(
            sku="SKU-100",
            name="Product One",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-200",
            name="Product Two",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.search_products("SKU-100")
        
        assert len(results) == 1
        assert results[0].sku == "SKU-100"

    
    def test_search_by_partial_name(self, db_session):
        """Test searching products by partial name match."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-101",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-102",
            name="Desktop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-103",
            name="Mobile Phone",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.search_products("Computer")
        
        assert len(results) == 2
        assert all("Computer" in p.name for p in results)
    
    def test_search_case_insensitive(self, db_session):
        """Test that search is case insensitive for names."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-104",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.search_products("laptop")
        
        assert len(results) == 1
        assert results[0].name == "Laptop Computer"
    
    def test_search_empty_query_returns_empty(self, db_session):
        """Test that empty search query returns empty list."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-105",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.search_products("")
        
        assert len(results) == 0
    
    def test_search_no_matches_returns_empty(self, db_session):
        """Test that search with no matches returns empty list."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-106",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.search_products("NonExistent")
        
        assert len(results) == 0



class TestFilterProducts:
    """Tests for filter_products functionality."""
    
    def test_filter_by_category(self, db_session):
        """Test filtering products by category."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-200",
            name="Laptop",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-201",
            name="Desk",
            category="Furniture",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-202",
            name="Phone",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(category="Electronics")
        
        assert len(results) == 2
        assert all(p.category == "Electronics" for p in results)
    
    def test_filter_no_category_returns_all(self, db_session):
        """Test that filtering without category returns all products."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-203",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-204",
            name="Product 2",
            category="Furniture",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products()
        
        assert len(results) == 2
    
    def test_filter_empty_category_returns_all(self, db_session):
        """Test that filtering with empty category returns all products."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-205",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-206",
            name="Product 2",
            category="Furniture",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(category="")
        
        assert len(results) == 2
    
    def test_filter_no_matches_returns_empty(self, db_session):
        """Test that filtering with no matches returns empty list."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-207",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(category="NonExistent")
        
        assert len(results) == 0


    def test_filter_by_multiple_criteria(self, db_session):
        """Test filtering products by multiple criteria with AND logic."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-300",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-301",
            name="Desktop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-302",
            name="Office Desk",
            category="Furniture",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-303",
            name="Monitor",
            category="Electronics",
            unit_of_measure="kg"
        )
        
        # Filter by category and unit_of_measure
        results = pm.filter_products(
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        assert len(results) == 2
        assert all(p.category == "Electronics" for p in results)
        assert all(p.unit_of_measure == "pieces" for p in results)
    
    def test_filter_by_sku(self, db_session):
        """Test filtering products by SKU."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-400",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-401",
            name="Product 2",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(sku="SKU-400")
        
        assert len(results) == 1
        assert results[0].sku == "SKU-400"
    
    def test_filter_by_name_partial_match(self, db_session):
        """Test filtering products by name with partial match."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-500",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-501",
            name="Desktop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-502",
            name="Mobile Phone",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(name="Computer")
        
        assert len(results) == 2
        assert all("Computer" in p.name for p in results)
    
    def test_filter_by_category_and_name(self, db_session):
        """Test filtering products by category and name simultaneously."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-600",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-601",
            name="Office Computer Desk",
            category="Furniture",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-602",
            name="Desktop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(
            category="Electronics",
            name="Computer"
        )
        
        assert len(results) == 2
        assert all(p.category == "Electronics" for p in results)
        assert all("Computer" in p.name for p in results)
    
    def test_filter_by_all_criteria(self, db_session):
        """Test filtering products by all available criteria."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-700",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-701",
            name="Desktop Computer",
            category="Electronics",
            unit_of_measure="pieces"
        )
        pm.create_product(
            sku="SKU-702",
            name="Laptop Computer",
            category="Electronics",
            unit_of_measure="kg"
        )
        
        results = pm.filter_products(
            sku="SKU-700",
            category="Electronics",
            name="Laptop",
            unit_of_measure="pieces"
        )
        
        assert len(results) == 1
        assert results[0].sku == "SKU-700"
        assert results[0].category == "Electronics"
        assert "Laptop" in results[0].name
        assert results[0].unit_of_measure == "pieces"
    
    def test_filter_multiple_criteria_no_matches(self, db_session):
        """Test filtering with multiple criteria that match no products."""
        pm = ProductManager(db_session)
        
        pm.create_product(
            sku="SKU-800",
            name="Laptop",
            category="Electronics",
            unit_of_measure="pieces"
        )
        
        results = pm.filter_products(
            category="Electronics",
            name="Desktop"  # No product has "Desktop" in name
        )
        
        assert len(results) == 0
