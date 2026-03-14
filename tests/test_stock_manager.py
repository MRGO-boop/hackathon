"""Unit tests for Stock Manager component."""
import pytest
import uuid
from core_inventory.components.stock_manager import StockManager, StockError, LocationStock
from core_inventory.models.stock import Stock
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing."""
    product = Product(
        id=uuid.uuid4(),
        sku="TEST-SKU-001",
        name="Test Product",
        category="Electronics",
        unit_of_measure="pieces"
    )
    db_session.add(product)
    db_session.commit()
    return product


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
def second_location(db_session):
    """Create a second location for testing."""
    location = Location(
        id=uuid.uuid4(),
        name="Second Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(location)
    db_session.commit()
    return location


class TestGetStock:
    """Tests for get_stock functionality."""
    
    def test_get_stock_existing_record(self, db_session, sample_product, sample_location):
        """Test getting stock for existing stock record."""
        # Create stock record
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        quantity = sm.get_stock(str(sample_product.id), str(sample_location.id))
        
        assert quantity == 100
    
    def test_get_stock_no_record_returns_zero(self, db_session, sample_product, sample_location):
        """Test getting stock when no record exists returns 0."""
        sm = StockManager(db_session)
        quantity = sm.get_stock(str(sample_product.id), str(sample_location.id))
        
        assert quantity == 0
    
    def test_get_stock_invalid_product_id_fails(self, db_session, sample_location):
        """Test getting stock with invalid product ID fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.get_stock("not-a-uuid", str(sample_location.id))
        
        assert exc_info.value.code == "INVALID_ID"
    
    def test_get_stock_invalid_location_id_fails(self, db_session, sample_product):
        """Test getting stock with invalid location ID fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.get_stock(str(sample_product.id), "not-a-uuid")
        
        assert exc_info.value.code == "INVALID_ID"


class TestUpdateStock:
    """Tests for update_stock functionality."""
    
    def test_update_stock_increase_existing(self, db_session, sample_product, sample_location):
        """Test increasing stock for existing record."""
        # Create initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=50
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        sm.update_stock(str(sample_product.id), str(sample_location.id), 30)
        db_session.commit()
        
        # Verify stock updated
        updated_stock = db_session.query(Stock).filter(
            Stock.product_id == sample_product.id,
            Stock.location_id == sample_location.id
        ).first()
        
        assert updated_stock.quantity == 80

    
    def test_update_stock_decrease_existing(self, db_session, sample_product, sample_location):
        """Test decreasing stock for existing record."""
        # Create initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        sm.update_stock(str(sample_product.id), str(sample_location.id), -30)
        db_session.commit()
        
        # Verify stock updated
        updated_stock = db_session.query(Stock).filter(
            Stock.product_id == sample_product.id,
            Stock.location_id == sample_location.id
        ).first()
        
        assert updated_stock.quantity == 70
    
    def test_update_stock_create_new_record(self, db_session, sample_product, sample_location):
        """Test creating new stock record when none exists."""
        sm = StockManager(db_session)
        sm.update_stock(str(sample_product.id), str(sample_location.id), 50)
        db_session.commit()
        
        # Verify stock created
        stock = db_session.query(Stock).filter(
            Stock.product_id == sample_product.id,
            Stock.location_id == sample_location.id
        ).first()
        
        assert stock is not None
        assert stock.quantity == 50
    
    def test_update_stock_insufficient_stock_fails(self, db_session, sample_product, sample_location):
        """Test that decreasing stock below zero fails."""
        # Create initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=50
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.update_stock(str(sample_product.id), str(sample_location.id), -100)
        
        assert exc_info.value.code == "INSUFFICIENT_STOCK"
        
        # Verify stock unchanged
        unchanged_stock = db_session.query(Stock).filter(
            Stock.product_id == sample_product.id,
            Stock.location_id == sample_location.id
        ).first()
        assert unchanged_stock.quantity == 50
    
    def test_update_stock_negative_on_new_record_fails(self, db_session, sample_product, sample_location):
        """Test that creating new record with negative quantity fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.update_stock(str(sample_product.id), str(sample_location.id), -50)
        
        assert exc_info.value.code == "INVALID_QUANTITY"
        
        # Verify no stock record created
        stock = db_session.query(Stock).filter(
            Stock.product_id == sample_product.id,
            Stock.location_id == sample_location.id
        ).first()
        assert stock is None
    
    def test_update_stock_product_not_found_fails(self, db_session, sample_location):
        """Test that updating stock for non-existent product fails."""
        sm = StockManager(db_session)
        fake_product_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(StockError) as exc_info:
            sm.update_stock(fake_product_id, str(sample_location.id), 50)
        
        assert exc_info.value.code == "PRODUCT_NOT_FOUND"
    
    def test_update_stock_location_not_found_fails(self, db_session, sample_product):
        """Test that updating stock for non-existent location fails."""
        sm = StockManager(db_session)
        fake_location_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(StockError) as exc_info:
            sm.update_stock(str(sample_product.id), fake_location_id, 50)
        
        assert exc_info.value.code == "LOCATION_NOT_FOUND"
    
    def test_update_stock_invalid_product_id_fails(self, db_session, sample_location):
        """Test that updating stock with invalid product ID fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.update_stock("not-a-uuid", str(sample_location.id), 50)
        
        assert exc_info.value.code == "INVALID_ID"


class TestCheckAvailability:
    """Tests for check_availability functionality."""
    
    def test_check_availability_sufficient_stock(self, db_session, sample_product, sample_location):
        """Test checking availability when sufficient stock exists."""
        # Create stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        available = sm.check_availability(str(sample_product.id), str(sample_location.id), 50)
        
        assert available is True
    
    def test_check_availability_exact_stock(self, db_session, sample_product, sample_location):
        """Test checking availability when stock exactly matches required."""
        # Create stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        available = sm.check_availability(str(sample_product.id), str(sample_location.id), 100)
        
        assert available is True
    
    def test_check_availability_insufficient_stock(self, db_session, sample_product, sample_location):
        """Test checking availability when insufficient stock exists."""
        # Create stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=50
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        available = sm.check_availability(str(sample_product.id), str(sample_location.id), 100)
        
        assert available is False
    
    def test_check_availability_no_stock(self, db_session, sample_product, sample_location):
        """Test checking availability when no stock exists."""
        sm = StockManager(db_session)
        available = sm.check_availability(str(sample_product.id), str(sample_location.id), 10)
        
        assert available is False
    
    def test_check_availability_zero_required(self, db_session, sample_product, sample_location):
        """Test checking availability with zero required quantity."""
        sm = StockManager(db_session)
        available = sm.check_availability(str(sample_product.id), str(sample_location.id), 0)
        
        assert available is True
    
    def test_check_availability_negative_required_fails(self, db_session, sample_product, sample_location):
        """Test that checking availability with negative required fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.check_availability(str(sample_product.id), str(sample_location.id), -10)
        
        assert exc_info.value.code == "INVALID_QUANTITY"


class TestGetStockByProduct:
    """Tests for get_stock_by_product functionality."""
    
    def test_get_stock_by_product_multiple_locations(self, db_session, sample_product, sample_location, second_location):
        """Test getting stock across multiple locations."""
        # Create stock at multiple locations
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=100
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=second_location.id,
            quantity=50
        )
        db_session.add_all([stock1, stock2])
        db_session.commit()
        
        sm = StockManager(db_session)
        location_stocks = sm.get_stock_by_product(str(sample_product.id))
        
        assert len(location_stocks) == 2
        
        # Verify both locations present
        location_ids = {ls.location_id for ls in location_stocks}
        assert str(sample_location.id) in location_ids
        assert str(second_location.id) in location_ids
        
        # Verify quantities
        for ls in location_stocks:
            if ls.location_id == str(sample_location.id):
                assert ls.quantity == 100
                assert ls.location_name == "Test Warehouse"
            elif ls.location_id == str(second_location.id):
                assert ls.quantity == 50
                assert ls.location_name == "Second Warehouse"
    
    def test_get_stock_by_product_single_location(self, db_session, sample_product, sample_location):
        """Test getting stock for product at single location."""
        # Create stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=sample_product.id,
            location_id=sample_location.id,
            quantity=75
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        location_stocks = sm.get_stock_by_product(str(sample_product.id))
        
        assert len(location_stocks) == 1
        assert location_stocks[0].location_id == str(sample_location.id)
        assert location_stocks[0].quantity == 75
        assert location_stocks[0].location_name == "Test Warehouse"
    
    def test_get_stock_by_product_no_stock(self, db_session, sample_product):
        """Test getting stock for product with no stock records."""
        sm = StockManager(db_session)
        location_stocks = sm.get_stock_by_product(str(sample_product.id))
        
        assert len(location_stocks) == 0
    
    def test_get_stock_by_product_invalid_id_fails(self, db_session):
        """Test getting stock with invalid product ID fails."""
        sm = StockManager(db_session)
        
        with pytest.raises(StockError) as exc_info:
            sm.get_stock_by_product("not-a-uuid")
        
        assert exc_info.value.code == "INVALID_PRODUCT_ID"


class TestGetLowStockProducts:
    """Tests for get_low_stock_products functionality."""
    
    def test_get_low_stock_products_below_threshold(self, db_session, sample_location):
        """Test getting products below their configured threshold."""
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="LOW-STOCK-001",
            name="Low Stock Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=100
        )
        db_session.add(product)
        db_session.commit()
        
        # Create stock below threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=50
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 1
        assert low_stock[0]["sku"] == "LOW-STOCK-001"
        assert low_stock[0]["current_stock"] == 50
        assert low_stock[0]["threshold"] == 100

    
    def test_get_low_stock_products_above_threshold(self, db_session, sample_location):
        """Test that products above threshold are not returned."""
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="GOOD-STOCK-001",
            name="Good Stock Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=50
        )
        db_session.add(product)
        db_session.commit()
        
        # Create stock above threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 0
    
    def test_get_low_stock_products_exact_threshold(self, db_session, sample_location):
        """Test that products at exact threshold are not returned."""
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="EXACT-STOCK-001",
            name="Exact Stock Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=100
        )
        db_session.add(product)
        db_session.commit()
        
        # Create stock at exact threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 0
    
    def test_get_low_stock_products_multiple_locations(self, db_session, sample_location, second_location):
        """Test low stock calculation across multiple locations."""
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="MULTI-LOC-001",
            name="Multi Location Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=150
        )
        db_session.add(product)
        db_session.commit()
        
        # Create stock at multiple locations (total = 120, below threshold of 150)
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=70
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=second_location.id,
            quantity=50
        )
        db_session.add_all([stock1, stock2])
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 1
        assert low_stock[0]["current_stock"] == 120
        assert low_stock[0]["threshold"] == 150
    
    def test_get_low_stock_products_no_threshold_not_returned(self, db_session, sample_location):
        """Test that products without threshold are not returned by default."""
        # Create product without threshold
        product = Product(
            id=uuid.uuid4(),
            sku="NO-THRESHOLD-001",
            name="No Threshold Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=None
        )
        db_session.add(product)
        db_session.commit()
        
        # Create low stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 0
    
    def test_get_low_stock_products_with_global_threshold(self, db_session, sample_location):
        """Test using global threshold for products without configured threshold."""
        # Create product without threshold
        product = Product(
            id=uuid.uuid4(),
            sku="GLOBAL-THRESHOLD-001",
            name="Global Threshold Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=None
        )
        db_session.add(product)
        db_session.commit()
        
        # Create low stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=sample_location.id,
            quantity=30
        )
        db_session.add(stock)
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products(threshold=50)
        
        assert len(low_stock) == 1
        assert low_stock[0]["sku"] == "GLOBAL-THRESHOLD-001"
        assert low_stock[0]["current_stock"] == 30
        assert low_stock[0]["threshold"] == 50
    
    def test_get_low_stock_products_mixed_thresholds(self, db_session, sample_location):
        """Test with both configured and global thresholds."""
        # Create product with configured threshold
        product1 = Product(
            id=uuid.uuid4(),
            sku="CONFIGURED-001",
            name="Configured Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=100
        )
        # Create product without threshold
        product2 = Product(
            id=uuid.uuid4(),
            sku="UNCONFIGURED-001",
            name="Unconfigured Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=None
        )
        db_session.add_all([product1, product2])
        db_session.commit()
        
        # Create low stock for both
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product1.id,
            location_id=sample_location.id,
            quantity=50
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product2.id,
            location_id=sample_location.id,
            quantity=30
        )
        db_session.add_all([stock1, stock2])
        db_session.commit()
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products(threshold=40)
        
        assert len(low_stock) == 2
        skus = {item["sku"] for item in low_stock}
        assert "CONFIGURED-001" in skus
        assert "UNCONFIGURED-001" in skus
    
    def test_get_low_stock_products_zero_stock(self, db_session):
        """Test that products with zero stock are detected."""
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="ZERO-STOCK-001",
            name="Zero Stock Product",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        db_session.add(product)
        db_session.commit()
        
        # No stock records created
        
        sm = StockManager(db_session)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 1
        assert low_stock[0]["current_stock"] == 0
        assert low_stock[0]["threshold"] == 10
