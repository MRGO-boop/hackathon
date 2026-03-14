"""Unit tests for LocationManager component."""
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


class TestCreateLocation:
    """Tests for create_location function."""
    
    def test_create_location_success(self, location_manager, db_session):
        """Test successful location creation."""
        location = location_manager.create_location(
            name="Main Warehouse",
            location_type="warehouse"
        )
        
        assert location.id is not None
        assert location.name == "Main Warehouse"
        assert location.type == LocationType.warehouse
        assert location.parent_id is None
        assert location.is_archived is False
        
        # Verify in database
        db_location = db_session.query(Location).filter(Location.id == location.id).first()
        assert db_location is not None
        assert db_location.name == "Main Warehouse"
    
    def test_create_location_with_parent(self, location_manager, db_session):
        """Test location creation with parent hierarchy."""
        # Create parent location
        parent = location_manager.create_location(
            name="Warehouse A",
            location_type="warehouse"
        )
        
        # Create child location
        child = location_manager.create_location(
            name="Rack 1",
            location_type="rack",
            parent_id=str(parent.id)
        )
        
        assert child.parent_id == parent.id
        
        # Verify hierarchy in database
        db_child = db_session.query(Location).filter(Location.id == child.id).first()
        assert db_child.parent_id == parent.id
    
    def test_create_location_empty_name(self, location_manager):
        """Test location creation with empty name fails."""
        with pytest.raises(LocationError) as exc_info:
            location_manager.create_location(
                name="",
                location_type="warehouse"
            )
        
        assert exc_info.value.code == "INVALID_NAME"
        assert "name is required" in exc_info.value.message.lower()
    
    def test_create_location_invalid_type(self, location_manager):
        """Test location creation with invalid type fails."""
        with pytest.raises(LocationError) as exc_info:
            location_manager.create_location(
                name="Test Location",
                location_type="invalid_type"
            )
        
        assert exc_info.value.code == "INVALID_TYPE"
        assert "invalid location type" in exc_info.value.message.lower()
    
    def test_create_location_nonexistent_parent(self, location_manager):
        """Test location creation with non-existent parent fails."""
        fake_parent_id = str(uuid.uuid4())
        
        with pytest.raises(LocationError) as exc_info:
            location_manager.create_location(
                name="Test Location",
                location_type="rack",
                parent_id=fake_parent_id
            )
        
        assert exc_info.value.code == "PARENT_NOT_FOUND"
    
    def test_create_location_all_types(self, location_manager):
        """Test creating locations with all valid types."""
        warehouse = location_manager.create_location(
            name="Warehouse",
            location_type="warehouse"
        )
        assert warehouse.type == LocationType.warehouse
        
        rack = location_manager.create_location(
            name="Rack",
            location_type="rack"
        )
        assert rack.type == LocationType.rack
        
        floor_area = location_manager.create_location(
            name="Floor Area",
            location_type="floor_area"
        )
        assert floor_area.type == LocationType.floor_area


class TestUpdateLocation:
    """Tests for update_location function."""
    
    def test_update_location_name(self, location_manager, db_session):
        """Test updating location name."""
        location = location_manager.create_location(
            name="Old Name",
            location_type="warehouse"
        )
        
        updated = location_manager.update_location(
            location_id=str(location.id),
            name="New Name"
        )
        
        assert updated.name == "New Name"
        assert updated.id == location.id
        
        # Verify in database
        db_location = db_session.query(Location).filter(Location.id == location.id).first()
        assert db_location.name == "New Name"
    
    def test_update_location_type(self, location_manager):
        """Test updating location type."""
        location = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        updated = location_manager.update_location(
            location_id=str(location.id),
            location_type="rack"
        )
        
        assert updated.type == LocationType.rack
    
    def test_update_location_parent(self, location_manager):
        """Test updating location parent."""
        parent = location_manager.create_location(
            name="Parent",
            location_type="warehouse"
        )
        
        location = location_manager.create_location(
            name="Child",
            location_type="rack"
        )
        
        updated = location_manager.update_location(
            location_id=str(location.id),
            parent_id=str(parent.id)
        )
        
        assert updated.parent_id == parent.id
    
    def test_update_location_not_found(self, location_manager):
        """Test updating non-existent location fails."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(LocationError) as exc_info:
            location_manager.update_location(
                location_id=fake_id,
                name="New Name"
            )
        
        assert exc_info.value.code == "LOCATION_NOT_FOUND"
    
    def test_update_location_empty_name(self, location_manager):
        """Test updating location with empty name fails."""
        location = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        with pytest.raises(LocationError) as exc_info:
            location_manager.update_location(
                location_id=str(location.id),
                name=""
            )
        
        assert exc_info.value.code == "INVALID_NAME"


class TestArchiveLocation:
    """Tests for archive_location function."""
    
    def test_archive_location_success(self, location_manager, db_session):
        """Test successful location archival."""
        location = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        location_manager.archive_location(str(location.id))
        
        # Verify archived in database
        db_location = db_session.query(Location).filter(Location.id == location.id).first()
        assert db_location.is_archived is True
    
    def test_archive_location_with_stock_fails(self, location_manager, db_session):
        """Test archiving location with stock fails."""
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
        
        # Add stock at location
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location.id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        # Try to archive location
        with pytest.raises(LocationError) as exc_info:
            location_manager.archive_location(str(location.id))
        
        assert exc_info.value.code == "LOCATION_HAS_STOCK"
        assert "existing stock" in exc_info.value.message.lower()
    
    def test_archive_location_with_zero_stock_succeeds(self, location_manager, db_session):
        """Test archiving location with zero stock succeeds."""
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
        
        # Add stock with zero quantity
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location.id,
            quantity=0
        )
        db_session.add(stock)
        db_session.commit()
        
        # Archive location should succeed
        location_manager.archive_location(str(location.id))
        
        # Verify archived
        db_location = db_session.query(Location).filter(Location.id == location.id).first()
        assert db_location.is_archived is True
    
    def test_archive_location_not_found(self, location_manager):
        """Test archiving non-existent location fails."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(LocationError) as exc_info:
            location_manager.archive_location(fake_id)
        
        assert exc_info.value.code == "LOCATION_NOT_FOUND"


class TestGetLocation:
    """Tests for get_location function."""
    
    def test_get_location_success(self, location_manager):
        """Test successful location retrieval."""
        created = location_manager.create_location(
            name="Test Location",
            location_type="warehouse"
        )
        
        retrieved = location_manager.get_location(str(created.id))
        
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        assert retrieved.type == created.type
    
    def test_get_location_not_found(self, location_manager):
        """Test retrieving non-existent location fails."""
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(LocationError) as exc_info:
            location_manager.get_location(fake_id)
        
        assert exc_info.value.code == "LOCATION_NOT_FOUND"
    
    def test_get_location_invalid_id(self, location_manager):
        """Test retrieving location with invalid ID fails."""
        with pytest.raises(LocationError) as exc_info:
            location_manager.get_location("invalid-id")
        
        assert exc_info.value.code == "INVALID_LOCATION_ID"


class TestListLocations:
    """Tests for list_locations function."""
    
    def test_list_locations_empty(self, location_manager):
        """Test listing locations when none exist."""
        locations = location_manager.list_locations()
        assert locations == []
    
    def test_list_locations_multiple(self, location_manager):
        """Test listing multiple locations."""
        loc1 = location_manager.create_location(
            name="Location 1",
            location_type="warehouse"
        )
        loc2 = location_manager.create_location(
            name="Location 2",
            location_type="rack"
        )
        loc3 = location_manager.create_location(
            name="Location 3",
            location_type="floor_area"
        )
        
        locations = location_manager.list_locations()
        
        assert len(locations) == 3
        location_ids = [loc.id for loc in locations]
        assert loc1.id in location_ids
        assert loc2.id in location_ids
        assert loc3.id in location_ids
    
    def test_list_locations_excludes_archived(self, location_manager):
        """Test listing locations excludes archived by default."""
        loc1 = location_manager.create_location(
            name="Active Location",
            location_type="warehouse"
        )
        loc2 = location_manager.create_location(
            name="Archived Location",
            location_type="warehouse"
        )
        
        # Archive loc2
        location_manager.archive_location(str(loc2.id))
        
        # List without archived
        locations = location_manager.list_locations()
        
        assert len(locations) == 1
        assert locations[0].id == loc1.id
    
    def test_list_locations_includes_archived(self, location_manager):
        """Test listing locations can include archived."""
        loc1 = location_manager.create_location(
            name="Active Location",
            location_type="warehouse"
        )
        loc2 = location_manager.create_location(
            name="Archived Location",
            location_type="warehouse"
        )
        
        # Archive loc2
        location_manager.archive_location(str(loc2.id))
        
        # List with archived
        locations = location_manager.list_locations(include_archived=True)
        
        assert len(locations) == 2
        location_ids = [loc.id for loc in locations]
        assert loc1.id in location_ids
        assert loc2.id in location_ids
