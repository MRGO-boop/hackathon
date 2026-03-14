"""Integration tests for LocationManager component."""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.location import Location, LocationType
from core_inventory.models.stock import Stock
from core_inventory.models.product import Product
from core_inventory.components.location_manager import LocationManager, LocationError


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def location_manager(db_session):
    """Create a LocationManager instance."""
    return LocationManager(db_session)


class TestLocationHierarchy:
    """Integration tests for location hierarchy."""
    
    def test_three_level_hierarchy(self, location_manager, db_session):
        """Test creating a three-level location hierarchy."""
        # Create warehouse
        warehouse = location_manager.create_location(
            name="Main Warehouse",
            location_type="warehouse"
        )
        
        # Create rack in warehouse
        rack = location_manager.create_location(
            name="Rack A1",
            location_type="rack",
            parent_id=str(warehouse.id)
        )
        
        # Create floor area in rack
        floor_area = location_manager.create_location(
            name="Position 1",
            location_type="floor_area",
            parent_id=str(rack.id)
        )
        
        # Verify hierarchy
        assert rack.parent_id == warehouse.id
        assert floor_area.parent_id == rack.id
        
        # Verify in database
        db_warehouse = db_session.query(Location).filter(Location.id == warehouse.id).first()
        db_rack = db_session.query(Location).filter(Location.id == rack.id).first()
        db_floor = db_session.query(Location).filter(Location.id == floor_area.id).first()
        
        assert db_rack.parent_id == db_warehouse.id
        assert db_floor.parent_id == db_rack.id
    
    def test_update_hierarchy(self, location_manager):
        """Test updating location hierarchy."""
        # Create two warehouses
        warehouse1 = location_manager.create_location(
            name="Warehouse 1",
            location_type="warehouse"
        )
        warehouse2 = location_manager.create_location(
            name="Warehouse 2",
            location_type="warehouse"
        )
        
        # Create rack in warehouse1
        rack = location_manager.create_location(
            name="Rack A",
            location_type="rack",
            parent_id=str(warehouse1.id)
        )
        
        assert rack.parent_id == warehouse1.id
        
        # Move rack to warehouse2
        updated_rack = location_manager.update_location(
            location_id=str(rack.id),
            parent_id=str(warehouse2.id)
        )
        
        assert updated_rack.parent_id == warehouse2.id


class TestLocationWithStock:
    """Integration tests for location operations with stock."""
    
    def test_archive_location_after_stock_removed(self, location_manager, db_session):
        """Test archiving location after stock is removed."""
        # Create location
        location = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        # Create product
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-SKU",
            name="Test Product",
            category="Test",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        # Add stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location.id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        # Try to archive - should fail
        with pytest.raises(LocationError) as exc_info:
            location_manager.archive_location(str(location.id))
        assert exc_info.value.code == "LOCATION_HAS_STOCK"
        
        # Remove stock
        stock.quantity = 0
        db_session.commit()
        
        # Now archive should succeed
        location_manager.archive_location(str(location.id))
        
        # Verify archived
        archived_location = location_manager.get_location(str(location.id))
        assert archived_location.is_archived is True
    
    def test_multiple_products_at_location(self, location_manager, db_session):
        """Test location with multiple products."""
        # Create location
        location = location_manager.create_location(
            name="Multi-Product Location",
            location_type="warehouse"
        )
        
        # Create multiple products
        products = []
        for i in range(3):
            product = Product(
                id=uuid.uuid4(),
                sku=f"SKU-{i}",
                name=f"Product {i}",
                category="Test",
                unit_of_measure="pieces"
            )
            db_session.add(product)
            products.append(product)
        db_session.commit()
        
        # Add stock for all products
        for product in products:
            stock = Stock(
                id=uuid.uuid4(),
                product_id=product.id,
                location_id=location.id,
                quantity=50
            )
            db_session.add(stock)
        db_session.commit()
        
        # Try to archive - should fail
        with pytest.raises(LocationError) as exc_info:
            location_manager.archive_location(str(location.id))
        assert exc_info.value.code == "LOCATION_HAS_STOCK"
        assert "3" in str(exc_info.value.context["stock_count"])


class TestLocationCRUDWorkflow:
    """Integration tests for complete CRUD workflows."""
    
    def test_complete_location_lifecycle(self, location_manager, db_session):
        """Test complete location lifecycle: create, update, archive."""
        # Create location
        location = location_manager.create_location(
            name="Initial Name",
            location_type="warehouse"
        )
        
        assert location.name == "Initial Name"
        assert location.type == LocationType.warehouse
        assert location.is_archived is False
        
        # Update name
        updated = location_manager.update_location(
            location_id=str(location.id),
            name="Updated Name"
        )
        
        assert updated.name == "Updated Name"
        assert updated.id == location.id
        
        # Update type
        updated = location_manager.update_location(
            location_id=str(location.id),
            location_type="rack"
        )
        
        assert updated.type == LocationType.rack
        
        # Archive
        location_manager.archive_location(str(location.id))
        
        # Verify archived
        archived = location_manager.get_location(str(location.id))
        assert archived.is_archived is True
        
        # Verify not in default list
        locations = location_manager.list_locations()
        assert location.id not in [loc.id for loc in locations]
        
        # Verify in list with archived
        all_locations = location_manager.list_locations(include_archived=True)
        assert location.id in [loc.id for loc in all_locations]
    
    def test_multiple_locations_management(self, location_manager):
        """Test managing multiple locations simultaneously."""
        # Create multiple locations
        locations = []
        for i in range(5):
            loc = location_manager.create_location(
                name=f"Location {i}",
                location_type="warehouse"
            )
            locations.append(loc)
        
        # Verify all created
        all_locations = location_manager.list_locations()
        assert len(all_locations) == 5
        
        # Update some
        location_manager.update_location(
            location_id=str(locations[0].id),
            name="Updated Location 0"
        )
        location_manager.update_location(
            location_id=str(locations[1].id),
            location_type="rack"
        )
        
        # Archive some
        location_manager.archive_location(str(locations[2].id))
        location_manager.archive_location(str(locations[3].id))
        
        # Verify active count
        active_locations = location_manager.list_locations()
        assert len(active_locations) == 3
        
        # Verify total count
        all_locations = location_manager.list_locations(include_archived=True)
        assert len(all_locations) == 5


class TestLocationEdgeCases:
    """Integration tests for edge cases."""
    
    def test_location_with_whitespace_name(self, location_manager):
        """Test location creation with whitespace in name."""
        location = location_manager.create_location(
            name="  Warehouse with spaces  ",
            location_type="warehouse"
        )
        
        # Should trim whitespace
        assert location.name == "Warehouse with spaces"
    
    def test_update_location_remove_parent(self, location_manager):
        """Test removing parent from location."""
        # Create parent and child
        parent = location_manager.create_location(
            name="Parent",
            location_type="warehouse"
        )
        child = location_manager.create_location(
            name="Child",
            location_type="rack",
            parent_id=str(parent.id)
        )
        
        assert child.parent_id == parent.id
        
        # Remove parent
        updated = location_manager.update_location(
            location_id=str(child.id),
            parent_id=""
        )
        
        assert updated.parent_id is None
    
    def test_archive_multiple_times_idempotent(self, location_manager):
        """Test archiving location multiple times is idempotent."""
        location = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        # Archive first time
        location_manager.archive_location(str(location.id))
        
        # Archive second time - should not raise error
        location_manager.archive_location(str(location.id))
        
        # Verify still archived
        archived = location_manager.get_location(str(location.id))
        assert archived.is_archived is True
