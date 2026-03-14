"""Integration tests for DocumentManager component."""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.user import User
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType
from core_inventory.models.stock import Stock
from core_inventory.models.receipt import ReceiptItem
from core_inventory.models.delivery_order import DeliveryOrderItem
from core_inventory.components.document_manager import DocumentManager
from core_inventory.components.stock_manager import StockManager


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
def test_user(db_session):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_product(db_session):
    """Create a test product."""
    product = Product(
        id=uuid.uuid4(),
        sku="TEST-SKU-001",
        name="Test Product",
        category="Test Category",
        unit_of_measure="pcs"
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def test_location(db_session):
    """Create a test location."""
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
def document_manager(db_session):
    """Create a DocumentManager instance."""
    return DocumentManager(db_session)


@pytest.fixture
def stock_manager(db_session):
    """Create a StockManager instance."""
    return StockManager(db_session)


def test_receipt_creation_with_stock_manager(document_manager, stock_manager, test_user, test_product, test_location):
    """Test that receipt creation works with stock manager integration."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    
    receipt = document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=items
    )
    
    # Verify receipt was created
    assert receipt is not None
    
    # Verify stock is still 0 (receipt not validated yet)
    stock = stock_manager.get_stock(str(test_product.id), str(test_location.id))
    assert stock == 0


def test_transfer_validates_stock_availability(document_manager, stock_manager, db_session, test_user, test_product, test_location):
    """Test that transfer creation validates stock availability."""
    # Create destination location
    dest_location = Location(
        id=uuid.uuid4(),
        name="Destination Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(dest_location)
    db_session.commit()
    
    # Add stock at source
    stock_manager.update_stock(str(test_product.id), str(test_location.id), 100)
    
    # Create transfer
    transfer = document_manager.create_transfer(
        source_location_id=str(test_location.id),
        destination_location_id=str(dest_location.id),
        product_id=str(test_product.id),
        quantity=50,
        created_by=str(test_user.id)
    )
    
    assert transfer is not None
    
    # Stock should still be 100 at source (transfer not validated yet)
    stock = stock_manager.get_stock(str(test_product.id), str(test_location.id))
    assert stock == 100


def test_multiple_receipts_same_product_location(document_manager, db_session, test_user, test_product, test_location):
    """Test creating multiple receipts for the same product and location."""
    items1 = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 100
        }
    ]
    
    items2 = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    
    receipt1 = document_manager.create_receipt(
        supplier_name="Supplier 1",
        created_by=str(test_user.id),
        items=items1
    )
    
    receipt2 = document_manager.create_receipt(
        supplier_name="Supplier 2",
        created_by=str(test_user.id),
        items=items2
    )
    
    assert receipt1.id != receipt2.id
    
    # Verify both receipts exist
    receipts = document_manager.list_documents(document_type="receipt")
    assert len(receipts) == 2



def test_delivery_order_with_multiple_locations(document_manager, db_session, test_user, test_product):
    """Test creating delivery order with items from multiple locations."""
    # Create two locations
    location1 = Location(
        id=uuid.uuid4(),
        name="Warehouse 1",
        type=LocationType.warehouse,
        is_archived=False
    )
    location2 = Location(
        id=uuid.uuid4(),
        name="Warehouse 2",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(location1)
    db_session.add(location2)
    db_session.commit()
    
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(location1.id),
            "requested_quantity": 30,
            "delivered_quantity": 30
        },
        {
            "product_id": str(test_product.id),
            "location_id": str(location2.id),
            "requested_quantity": 20,
            "delivered_quantity": 20
        }
    ]
    
    delivery_order = document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=items
    )
    
    assert delivery_order is not None
    
    # Verify items were created for both locations
    delivery_items = db_session.query(DeliveryOrderItem).filter(
        DeliveryOrderItem.delivery_order_id == delivery_order.id
    ).all()
    
    assert len(delivery_items) == 2
    location_ids = {str(item.location_id) for item in delivery_items}
    assert str(location1.id) in location_ids
    assert str(location2.id) in location_ids


def test_stock_adjustment_calculation(document_manager, test_user, test_product, test_location):
    """Test that stock adjustment correctly calculates the difference."""
    # Test negative adjustment (physical < recorded)
    adjustment1 = document_manager.create_stock_adjustment(
        product_id=str(test_product.id),
        location_id=str(test_location.id),
        recorded_quantity=100,
        physical_quantity=95,
        reason="Shrinkage",
        created_by=str(test_user.id)
    )
    
    assert adjustment1.adjustment_difference == -5
    
    # Test positive adjustment (physical > recorded)
    adjustment2 = document_manager.create_stock_adjustment(
        product_id=str(test_product.id),
        location_id=str(test_location.id),
        recorded_quantity=100,
        physical_quantity=110,
        reason="Found items",
        created_by=str(test_user.id)
    )
    
    assert adjustment2.adjustment_difference == 10
    
    # Test zero adjustment (physical == recorded)
    adjustment3 = document_manager.create_stock_adjustment(
        product_id=str(test_product.id),
        location_id=str(test_location.id),
        recorded_quantity=100,
        physical_quantity=100,
        reason="Verification",
        created_by=str(test_user.id)
    )
    
    assert adjustment3.adjustment_difference == 0


def test_list_documents_with_complex_filters(document_manager, db_session, test_user, test_product):
    """Test listing documents with complex filtering scenarios."""
    # Create multiple locations
    location1 = Location(
        id=uuid.uuid4(),
        name="Warehouse 1",
        type=LocationType.warehouse,
        is_archived=False
    )
    location2 = Location(
        id=uuid.uuid4(),
        name="Warehouse 2",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(location1)
    db_session.add(location2)
    db_session.commit()
    
    # Create receipts at different locations
    items1 = [
        {
            "product_id": str(test_product.id),
            "location_id": str(location1.id),
            "expected_quantity": 100,
            "received_quantity": 100
        }
    ]
    
    items2 = [
        {
            "product_id": str(test_product.id),
            "location_id": str(location2.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    
    document_manager.create_receipt(
        supplier_name="Supplier 1",
        created_by=str(test_user.id),
        items=items1
    )
    
    document_manager.create_receipt(
        supplier_name="Supplier 2",
        created_by=str(test_user.id),
        items=items2
    )
    
    # Filter by location1
    location1_docs = document_manager.list_documents(location_id=str(location1.id))
    assert len(location1_docs) == 1
    
    # Filter by location2
    location2_docs = document_manager.list_documents(location_id=str(location2.id))
    assert len(location2_docs) == 1
    
    # Filter by document type and status
    pending_receipts = document_manager.list_documents(
        document_type="receipt",
        status="pending"
    )
    assert len(pending_receipts) == 2


def test_transfer_between_multiple_locations(document_manager, stock_manager, db_session, test_user, test_product):
    """Test creating transfers between multiple location pairs."""
    # Create three locations
    loc1 = Location(id=uuid.uuid4(), name="Loc 1", type=LocationType.warehouse, is_archived=False)
    loc2 = Location(id=uuid.uuid4(), name="Loc 2", type=LocationType.warehouse, is_archived=False)
    loc3 = Location(id=uuid.uuid4(), name="Loc 3", type=LocationType.warehouse, is_archived=False)
    db_session.add_all([loc1, loc2, loc3])
    db_session.commit()
    
    # Add stock at loc1 and loc2
    stock_manager.update_stock(str(test_product.id), str(loc1.id), 100)
    stock_manager.update_stock(str(test_product.id), str(loc2.id), 50)
    
    # Create transfer from loc1 to loc2
    transfer1 = document_manager.create_transfer(
        source_location_id=str(loc1.id),
        destination_location_id=str(loc2.id),
        product_id=str(test_product.id),
        quantity=30,
        created_by=str(test_user.id)
    )
    
    # Create transfer from loc2 to loc3
    transfer2 = document_manager.create_transfer(
        source_location_id=str(loc2.id),
        destination_location_id=str(loc3.id),
        product_id=str(test_product.id),
        quantity=20,
        created_by=str(test_user.id)
    )
    
    assert transfer1 is not None
    assert transfer2 is not None
    
    # Verify transfers exist
    transfers = document_manager.list_documents(document_type="transfer")
    assert len(transfers) == 2
