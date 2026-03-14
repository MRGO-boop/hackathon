"""Integration tests for multi-filter functionality."""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.user import User
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType
from core_inventory.components.product_manager import ProductManager
from core_inventory.components.document_manager import DocumentManager


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
def test_locations(db_session):
    """Create test locations."""
    locations = []
    for i in range(3):
        location = Location(
            id=uuid.uuid4(),
            name=f"Warehouse {i+1}",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location)
        locations.append(location)
    db_session.commit()
    return locations


def test_product_multi_filter_integration(db_session):
    """Test product filtering with multiple simultaneous filters."""
    pm = ProductManager(db_session)
    
    # Create diverse products
    products_data = [
        {"sku": "ELEC-001", "name": "Laptop Computer", "category": "Electronics", "unit": "pieces"},
        {"sku": "ELEC-002", "name": "Desktop Computer", "category": "Electronics", "unit": "pieces"},
        {"sku": "ELEC-003", "name": "Monitor", "category": "Electronics", "unit": "kg"},
        {"sku": "FURN-001", "name": "Office Desk", "category": "Furniture", "unit": "pieces"},
        {"sku": "FURN-002", "name": "Computer Chair", "category": "Furniture", "unit": "pieces"},
    ]
    
    for data in products_data:
        pm.create_product(
            sku=data["sku"],
            name=data["name"],
            category=data["category"],
            unit_of_measure=data["unit"]
        )
    
    # Test 1: Filter by category only
    electronics = pm.filter_products(category="Electronics")
    assert len(electronics) == 3
    assert all(p.category == "Electronics" for p in electronics)
    
    # Test 2: Filter by category and unit_of_measure
    electronics_pieces = pm.filter_products(
        category="Electronics",
        unit_of_measure="pieces"
    )
    assert len(electronics_pieces) == 2
    assert all(p.category == "Electronics" and p.unit_of_measure == "pieces" for p in electronics_pieces)
    
    # Test 3: Filter by category and name
    computers = pm.filter_products(
        category="Electronics",
        name="Computer"
    )
    assert len(computers) == 2
    assert all("Computer" in p.name for p in computers)
    
    # Test 4: Filter by all criteria
    specific_product = pm.filter_products(
        sku="ELEC-001",
        category="Electronics",
        name="Laptop",
        unit_of_measure="pieces"
    )
    assert len(specific_product) == 1
    assert specific_product[0].sku == "ELEC-001"
    
    # Test 5: Filter with no matches
    no_match = pm.filter_products(
        category="Electronics",
        name="Chair"
    )
    assert len(no_match) == 0


def test_document_multi_filter_integration(db_session, test_user, test_locations):
    """Test document filtering with multiple simultaneous filters."""
    dm = DocumentManager(db_session)
    pm = ProductManager(db_session)
    
    # Create test products
    product1 = pm.create_product(
        sku="PROD-001",
        name="Product 1",
        category="Electronics",
        unit_of_measure="pieces"
    )
    product2 = pm.create_product(
        sku="PROD-002",
        name="Product 2",
        category="Electronics",
        unit_of_measure="pieces"
    )
    
    # Create receipts at different locations
    for i, location in enumerate(test_locations[:2]):
        items = [
            {
                "product_id": str(product1.id),
                "location_id": str(location.id),
                "expected_quantity": 100,
                "received_quantity": 95
            }
        ]
        dm.create_receipt(
            supplier_name=f"Supplier {i+1}",
            created_by=str(test_user.id),
            items=items
        )
    
    # Create delivery orders at different locations
    for i, location in enumerate(test_locations[:2]):
        items = [
            {
                "product_id": str(product2.id),
                "location_id": str(location.id),
                "requested_quantity": 50,
                "delivered_quantity": 50
            }
        ]
        dm.create_delivery_order(
            customer_name=f"Customer {i+1}",
            created_by=str(test_user.id),
            items=items
        )
    
    # Test 1: Filter by document type only
    receipts = dm.list_documents(document_type="receipt")
    assert len(receipts) == 2
    assert all(doc["document_type"] == "receipt" for doc in receipts)
    
    # Test 2: Filter by status only
    pending_docs = dm.list_documents(status="pending")
    assert len(pending_docs) == 4  # 2 receipts + 2 delivery orders
    assert all(doc["status"] == "pending" for doc in pending_docs)
    
    # Test 3: Filter by location only
    location1_docs = dm.list_documents(location_id=str(test_locations[0].id))
    assert len(location1_docs) == 2  # 1 receipt + 1 delivery order
    
    # Test 4: Filter by document type and status
    pending_receipts = dm.list_documents(
        document_type="receipt",
        status="pending"
    )
    assert len(pending_receipts) == 2
    assert all(doc["document_type"] == "receipt" and doc["status"] == "pending" for doc in pending_receipts)
    
    # Test 5: Filter by document type and location
    location1_receipts = dm.list_documents(
        document_type="receipt",
        location_id=str(test_locations[0].id)
    )
    assert len(location1_receipts) == 1
    assert location1_receipts[0]["document_type"] == "receipt"
    
    # Test 6: Filter by all criteria (document type, status, location)
    specific_docs = dm.list_documents(
        document_type="receipt",
        status="pending",
        location_id=str(test_locations[0].id)
    )
    assert len(specific_docs) == 1
    assert specific_docs[0]["document_type"] == "receipt"
    assert specific_docs[0]["status"] == "pending"
    
    # Test 7: Filter with no matches
    no_match = dm.list_documents(
        document_type="receipt",
        location_id=str(test_locations[2].id)  # No documents at this location
    )
    assert len(no_match) == 0


def test_real_time_filter_updates(db_session, test_user, test_locations):
    """Test that filters return real-time results as data changes."""
    dm = DocumentManager(db_session)
    pm = ProductManager(db_session)
    
    # Create a product
    product = pm.create_product(
        sku="PROD-100",
        name="Test Product",
        category="Electronics",
        unit_of_measure="pieces"
    )
    
    # Initially, no receipts
    receipts = dm.list_documents(document_type="receipt")
    initial_count = len(receipts)
    
    # Create a receipt
    items = [
        {
            "product_id": str(product.id),
            "location_id": str(test_locations[0].id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    dm.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=items
    )
    
    # Query again - should see the new receipt immediately
    receipts = dm.list_documents(document_type="receipt")
    assert len(receipts) == initial_count + 1
    
    # Create another receipt at a different location
    items2 = [
        {
            "product_id": str(product.id),
            "location_id": str(test_locations[1].id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    dm.create_receipt(
        supplier_name="Another Supplier",
        created_by=str(test_user.id),
        items=items2
    )
    
    # Query with location filter - should only see location 0 receipt
    location0_receipts = dm.list_documents(
        document_type="receipt",
        location_id=str(test_locations[0].id)
    )
    assert len(location0_receipts) == 1
    
    # Query with location filter - should only see location 1 receipt
    location1_receipts = dm.list_documents(
        document_type="receipt",
        location_id=str(test_locations[1].id)
    )
    assert len(location1_receipts) == 1
    
    # Query all receipts - should see both
    all_receipts = dm.list_documents(document_type="receipt")
    assert len(all_receipts) == initial_count + 2
