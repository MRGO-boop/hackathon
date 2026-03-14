"""Integration tests for Stock Manager component."""
import pytest
import uuid
from core_inventory.components.stock_manager import StockManager, StockError
from core_inventory.models.stock import Stock
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType


@pytest.fixture
def setup_test_data(db_session):
    """Create test products and locations."""
    # Create locations
    warehouse1 = Location(
        id=uuid.uuid4(),
        name="Warehouse A",
        type=LocationType.warehouse,
        is_archived=False
    )
    warehouse2 = Location(
        id=uuid.uuid4(),
        name="Warehouse B",
        type=LocationType.warehouse,
        is_archived=False
    )
    
    # Create products
    product1 = Product(
        id=uuid.uuid4(),
        sku="PROD-001",
        name="Product One",
        category="Electronics",
        unit_of_measure="pieces",
        low_stock_threshold=50
    )
    product2 = Product(
        id=uuid.uuid4(),
        sku="PROD-002",
        name="Product Two",
        category="Furniture",
        unit_of_measure="pieces",
        low_stock_threshold=20
    )
    
    db_session.add_all([warehouse1, warehouse2, product1, product2])
    db_session.commit()
    
    return {
        "warehouse1": warehouse1,
        "warehouse2": warehouse2,
        "product1": product1,
        "product2": product2
    }



class TestStockTransactions:
    """Tests for stock operations with transaction support."""
    
    def test_update_stock_transaction_commit(self, db_session, setup_test_data):
        """Test that stock updates are committed properly."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Update stock
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        db_session.commit()
        
        # Verify in new session query
        stock = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        
        assert stock.quantity == 100
    
    def test_update_stock_transaction_rollback(self, db_session, setup_test_data):
        """Test that stock updates can be rolled back."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Update stock
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        
        # Rollback
        db_session.rollback()
        
        # Verify no stock record exists
        stock = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        
        assert stock is None
    
    def test_multiple_updates_in_transaction(self, db_session, setup_test_data):
        """Test multiple stock updates in single transaction."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Multiple updates
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        sm.update_stock(str(data["product1"].id), str(data["warehouse2"].id), 50)
        sm.update_stock(str(data["product2"].id), str(data["warehouse1"].id), 75)
        
        db_session.commit()
        
        # Verify all updates
        stock1 = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        stock2 = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse2"].id
        ).first()
        stock3 = db_session.query(Stock).filter(
            Stock.product_id == data["product2"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        
        assert stock1.quantity == 100
        assert stock2.quantity == 50
        assert stock3.quantity == 75



class TestMultiLocationStockTracking:
    """Tests for tracking stock across multiple locations."""
    
    def test_independent_stock_tracking(self, db_session, setup_test_data):
        """Test that stock is tracked independently per location."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Add stock at different locations
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        sm.update_stock(str(data["product1"].id), str(data["warehouse2"].id), 200)
        db_session.commit()
        
        # Verify independent tracking
        stock_w1 = sm.get_stock(str(data["product1"].id), str(data["warehouse1"].id))
        stock_w2 = sm.get_stock(str(data["product1"].id), str(data["warehouse2"].id))
        
        assert stock_w1 == 100
        assert stock_w2 == 200
    
    def test_stock_change_at_one_location_doesnt_affect_other(self, db_session, setup_test_data):
        """Test that changing stock at one location doesn't affect others."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Setup initial stock
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        sm.update_stock(str(data["product1"].id), str(data["warehouse2"].id), 200)
        db_session.commit()
        
        # Change stock at warehouse1
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), -50)
        db_session.commit()
        
        # Verify warehouse2 unchanged
        stock_w1 = sm.get_stock(str(data["product1"].id), str(data["warehouse1"].id))
        stock_w2 = sm.get_stock(str(data["product1"].id), str(data["warehouse2"].id))
        
        assert stock_w1 == 50
        assert stock_w2 == 200
    
    def test_get_stock_by_product_shows_all_locations(self, db_session, setup_test_data):
        """Test getting stock across all locations for a product."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Add stock at multiple locations
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        sm.update_stock(str(data["product1"].id), str(data["warehouse2"].id), 150)
        db_session.commit()
        
        # Get all locations
        location_stocks = sm.get_stock_by_product(str(data["product1"].id))
        
        assert len(location_stocks) == 2
        
        total_stock = sum(ls.quantity for ls in location_stocks)
        assert total_stock == 250


class TestLowStockAlertIntegration:
    """Integration tests for low stock alert functionality."""
    
    def test_low_stock_alert_with_real_data(self, db_session, setup_test_data):
        """Test low stock alerts with realistic scenario."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Product1 has threshold of 50, add stock below threshold
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 30)
        
        # Product2 has threshold of 20, add stock above threshold
        sm.update_stock(str(data["product2"].id), str(data["warehouse1"].id), 50)
        
        db_session.commit()
        
        # Get low stock products
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 1
        assert low_stock[0]["sku"] == "PROD-001"
        assert low_stock[0]["current_stock"] == 30
        assert low_stock[0]["threshold"] == 50

    
    def test_low_stock_aggregates_across_locations(self, db_session, setup_test_data):
        """Test that low stock calculation aggregates across all locations."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Product1 threshold is 50, add stock at two locations totaling 40
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 25)
        sm.update_stock(str(data["product1"].id), str(data["warehouse2"].id), 15)
        
        # Product2 threshold is 20, add stock above threshold
        sm.update_stock(str(data["product2"].id), str(data["warehouse1"].id), 30)
        db_session.commit()
        
        # Should be flagged as low stock (40 < 50)
        low_stock = sm.get_low_stock_products()
        
        assert len(low_stock) == 1
        assert low_stock[0]["sku"] == "PROD-001"
        assert low_stock[0]["current_stock"] == 40


class TestStockAvailabilityChecks:
    """Integration tests for stock availability checking."""
    
    def test_availability_check_realistic_scenario(self, db_session, setup_test_data):
        """Test availability checking in realistic order fulfillment scenario."""
        data = setup_test_data
        sm = StockManager(db_session)
        
        # Setup stock
        sm.update_stock(str(data["product1"].id), str(data["warehouse1"].id), 100)
        db_session.commit()
        
        # Check various order quantities
        assert sm.check_availability(str(data["product1"].id), str(data["warehouse1"].id), 50) is True
        assert sm.check_availability(str(data["product1"].id), str(data["warehouse1"].id), 100) is True
        assert sm.check_availability(str(data["product1"].id), str(data["warehouse1"].id), 101) is False
        
        # Check at different location (no stock)
        assert sm.check_availability(str(data["product1"].id), str(data["warehouse2"].id), 1) is False
