"""Unit tests for DocumentManager component."""
import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.user import User
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType
from core_inventory.models.stock import Stock
from core_inventory.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.models.stock_adjustment import StockAdjustment, StockAdjustmentStatus
from core_inventory.components.document_manager import DocumentManager, DocumentError


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


# Receipt Tests

def test_create_receipt_success(document_manager, test_user, test_product, test_location):
    """Test successful receipt creation."""
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
        items=items,
        supplier_contact="supplier@example.com"
    )
    
    assert receipt is not None
    assert receipt.supplier_name == "Test Supplier"
    assert receipt.supplier_contact == "supplier@example.com"
    assert receipt.status == ReceiptStatus.pending
    assert receipt.created_by == test_user.id


def test_create_receipt_without_supplier_name(document_manager, test_user, test_product, test_location):
    """Test receipt creation fails without supplier name."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_receipt(
            supplier_name="",
            created_by=str(test_user.id),
            items=items
        )
    
    assert exc_info.value.code == "INVALID_SUPPLIER_NAME"


def test_create_receipt_without_items(document_manager, test_user):
    """Test receipt creation fails without items."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_receipt(
            supplier_name="Test Supplier",
            created_by=str(test_user.id),
            items=[]
        )
    
    assert exc_info.value.code == "NO_ITEMS"



def test_create_receipt_with_invalid_product(document_manager, test_user, test_location):
    """Test receipt creation fails with invalid product ID."""
    items = [
        {
            "product_id": str(uuid.uuid4()),  # Non-existent product
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_receipt(
            supplier_name="Test Supplier",
            created_by=str(test_user.id),
            items=items
        )
    
    assert exc_info.value.code == "PRODUCT_NOT_FOUND"


def test_create_receipt_with_invalid_location(document_manager, test_user, test_product):
    """Test receipt creation fails with invalid location ID."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(uuid.uuid4()),  # Non-existent location
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_receipt(
            supplier_name="Test Supplier",
            created_by=str(test_user.id),
            items=items
        )
    
    assert exc_info.value.code == "LOCATION_NOT_FOUND"


def test_create_receipt_with_negative_quantity(document_manager, test_user, test_product, test_location):
    """Test receipt creation fails with negative quantity."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": -10,
            "received_quantity": 95
        }
    ]
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_receipt(
            supplier_name="Test Supplier",
            created_by=str(test_user.id),
            items=items
        )
    
    assert exc_info.value.code == "INVALID_QUANTITY"


# Delivery Order Tests

def test_create_delivery_order_success(document_manager, test_user, test_product, test_location):
    """Test successful delivery order creation."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    
    delivery_order = document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=items,
        customer_contact="customer@example.com"
    )
    
    assert delivery_order is not None
    assert delivery_order.customer_name == "Test Customer"
    assert delivery_order.customer_contact == "customer@example.com"
    assert delivery_order.status == DeliveryOrderStatus.pending
    assert delivery_order.created_by == test_user.id



def test_create_delivery_order_without_customer_name(document_manager, test_user, test_product, test_location):
    """Test delivery order creation fails without customer name."""
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_delivery_order(
            customer_name="",
            created_by=str(test_user.id),
            items=items
        )
    
    assert exc_info.value.code == "INVALID_CUSTOMER_NAME"


def test_create_delivery_order_without_items(document_manager, test_user):
    """Test delivery order creation fails without items."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_delivery_order(
            customer_name="Test Customer",
            created_by=str(test_user.id),
            items=[]
        )
    
    assert exc_info.value.code == "NO_ITEMS"


# Transfer Tests

def test_create_transfer_success(document_manager, db_session, test_user, test_product, test_location):
    """Test successful transfer creation with sufficient stock."""
    # Create another location
    dest_location = Location(
        id=uuid.uuid4(),
        name="Destination Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(dest_location)
    db_session.commit()
    
    # Add stock at source location
    stock = Stock(
        id=uuid.uuid4(),
        product_id=test_product.id,
        location_id=test_location.id,
        quantity=100
    )
    db_session.add(stock)
    db_session.commit()
    
    transfer = document_manager.create_transfer(
        source_location_id=str(test_location.id),
        destination_location_id=str(dest_location.id),
        product_id=str(test_product.id),
        quantity=50,
        created_by=str(test_user.id)
    )
    
    assert transfer is not None
    assert transfer.source_location_id == test_location.id
    assert transfer.destination_location_id == dest_location.id
    assert transfer.product_id == test_product.id
    assert transfer.quantity == 50
    assert transfer.status == TransferStatus.pending
    assert transfer.created_by == test_user.id


def test_create_transfer_insufficient_stock(document_manager, db_session, test_user, test_product, test_location):
    """Test transfer creation fails with insufficient stock."""
    # Create another location
    dest_location = Location(
        id=uuid.uuid4(),
        name="Destination Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(dest_location)
    db_session.commit()
    
    # Add insufficient stock at source location
    stock = Stock(
        id=uuid.uuid4(),
        product_id=test_product.id,
        location_id=test_location.id,
        quantity=10
    )
    db_session.add(stock)
    db_session.commit()
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_transfer(
            source_location_id=str(test_location.id),
            destination_location_id=str(dest_location.id),
            product_id=str(test_product.id),
            quantity=50,
            created_by=str(test_user.id)
        )
    
    assert exc_info.value.code == "INSUFFICIENT_STOCK"



def test_create_transfer_same_location(document_manager, db_session, test_user, test_product, test_location):
    """Test transfer creation fails when source and destination are the same."""
    # Add stock at source location
    stock = Stock(
        id=uuid.uuid4(),
        product_id=test_product.id,
        location_id=test_location.id,
        quantity=100
    )
    db_session.add(stock)
    db_session.commit()
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_transfer(
            source_location_id=str(test_location.id),
            destination_location_id=str(test_location.id),
            product_id=str(test_product.id),
            quantity=50,
            created_by=str(test_user.id)
        )
    
    assert exc_info.value.code == "SAME_LOCATION"


def test_create_transfer_invalid_quantity(document_manager, db_session, test_user, test_product, test_location):
    """Test transfer creation fails with invalid quantity."""
    # Create another location
    dest_location = Location(
        id=uuid.uuid4(),
        name="Destination Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(dest_location)
    db_session.commit()
    
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_transfer(
            source_location_id=str(test_location.id),
            destination_location_id=str(dest_location.id),
            product_id=str(test_product.id),
            quantity=0,
            created_by=str(test_user.id)
        )
    
    assert exc_info.value.code == "INVALID_QUANTITY"


# Stock Adjustment Tests

def test_create_stock_adjustment_success(document_manager, test_user, test_product, test_location):
    """Test successful stock adjustment creation."""
    adjustment = document_manager.create_stock_adjustment(
        product_id=str(test_product.id),
        location_id=str(test_location.id),
        recorded_quantity=100,
        physical_quantity=95,
        reason="Physical count discrepancy",
        created_by=str(test_user.id)
    )
    
    assert adjustment is not None
    assert adjustment.product_id == test_product.id
    assert adjustment.location_id == test_location.id
    assert adjustment.recorded_quantity == 100
    assert adjustment.physical_quantity == 95
    assert adjustment.adjustment_difference == -5
    assert adjustment.reason == "Physical count discrepancy"
    assert adjustment.status == StockAdjustmentStatus.pending
    assert adjustment.created_by == test_user.id


def test_create_stock_adjustment_positive_difference(document_manager, test_user, test_product, test_location):
    """Test stock adjustment with positive difference."""
    adjustment = document_manager.create_stock_adjustment(
        product_id=str(test_product.id),
        location_id=str(test_location.id),
        recorded_quantity=100,
        physical_quantity=110,
        reason="Found additional items",
        created_by=str(test_user.id)
    )
    
    assert adjustment.adjustment_difference == 10



def test_create_stock_adjustment_without_reason(document_manager, test_user, test_product, test_location):
    """Test stock adjustment creation fails without reason."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_stock_adjustment(
            product_id=str(test_product.id),
            location_id=str(test_location.id),
            recorded_quantity=100,
            physical_quantity=95,
            reason="",
            created_by=str(test_user.id)
        )
    
    assert exc_info.value.code == "REASON_REQUIRED"


def test_create_stock_adjustment_negative_quantity(document_manager, test_user, test_product, test_location):
    """Test stock adjustment creation fails with negative quantity."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.create_stock_adjustment(
            product_id=str(test_product.id),
            location_id=str(test_location.id),
            recorded_quantity=-10,
            physical_quantity=95,
            reason="Test",
            created_by=str(test_user.id)
        )
    
    assert exc_info.value.code == "INVALID_QUANTITY"


# Get Document Tests

def test_get_receipt_document(document_manager, test_user, test_product, test_location):
    """Test getting a receipt document by ID."""
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
    
    retrieved = document_manager.get_document(str(receipt.id), "receipt")
    
    assert retrieved is not None
    assert retrieved.id == receipt.id
    assert retrieved.supplier_name == "Test Supplier"


def test_get_document_not_found(document_manager):
    """Test getting a non-existent document."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.get_document(str(uuid.uuid4()), "receipt")
    
    assert exc_info.value.code == "DOCUMENT_NOT_FOUND"


def test_get_document_invalid_type(document_manager):
    """Test getting a document with invalid type."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.get_document(str(uuid.uuid4()), "invalid_type")
    
    assert exc_info.value.code == "INVALID_DOCUMENT_TYPE"


# List Documents Tests

def test_list_all_documents(document_manager, test_user, test_product, test_location):
    """Test listing all documents without filters."""
    # Create a receipt
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create a delivery order
    delivery_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=delivery_items
    )
    
    documents = document_manager.list_documents()
    
    assert len(documents) == 2
    assert any(doc["document_type"] == "receipt" for doc in documents)
    assert any(doc["document_type"] == "delivery_order" for doc in documents)



def test_list_documents_by_type(document_manager, test_user, test_product, test_location):
    """Test listing documents filtered by type."""
    # Create a receipt
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create a delivery order
    delivery_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=delivery_items
    )
    
    receipts = document_manager.list_documents(document_type="receipt")
    
    assert len(receipts) == 1
    assert receipts[0]["document_type"] == "receipt"


def test_list_documents_by_status(document_manager, test_user, test_product, test_location):
    """Test listing documents filtered by status."""
    # Create a receipt
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    pending_docs = document_manager.list_documents(status="pending")
    
    assert len(pending_docs) >= 1
    assert all(doc["status"] == "pending" for doc in pending_docs)


def test_list_documents_by_location(document_manager, db_session, test_user, test_product, test_location):
    """Test listing documents filtered by location."""
    # Create another location
    other_location = Location(
        id=uuid.uuid4(),
        name="Other Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(other_location)
    db_session.commit()
    
    # Create receipt at test_location
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create receipt at other_location
    other_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(other_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    document_manager.create_receipt(
        supplier_name="Other Supplier",
        created_by=str(test_user.id),
        items=other_items
    )
    
    location_docs = document_manager.list_documents(location_id=str(test_location.id))
    
    assert len(location_docs) >= 1



def test_list_documents_multiple_filters(document_manager, test_user, test_product, test_location):
    """Test listing documents with multiple filters."""
    # Create a receipt
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create a delivery order
    delivery_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=delivery_items
    )
    
    filtered_docs = document_manager.list_documents(
        document_type="receipt",
        status="pending",
        location_id=str(test_location.id)
    )
    
    assert len(filtered_docs) == 1
    assert filtered_docs[0]["document_type"] == "receipt"
    assert filtered_docs[0]["status"] == "pending"


def test_list_documents_invalid_status(document_manager):
    """Test listing documents with invalid status."""
    with pytest.raises(DocumentError) as exc_info:
        document_manager.list_documents(document_type="receipt", status="invalid_status")
    
    assert exc_info.value.code == "INVALID_STATUS"


def test_create_receipt_multiple_items(document_manager, db_session, test_user, test_product, test_location):
    """Test creating a receipt with multiple items."""
    # Create another product
    product2 = Product(
        id=uuid.uuid4(),
        sku="TEST-SKU-002",
        name="Test Product 2",
        category="Test Category",
        unit_of_measure="pcs"
    )
    db_session.add(product2)
    db_session.commit()
    
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        },
        {
            "product_id": str(product2.id),
            "location_id": str(test_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    
    receipt = document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=items
    )
    
    # Verify items were created
    receipt_items = db_session.query(ReceiptItem).filter(
        ReceiptItem.receipt_id == receipt.id
    ).all()
    
    assert len(receipt_items) == 2


def test_create_delivery_order_multiple_items(document_manager, db_session, test_user, test_product, test_location):
    """Test creating a delivery order with multiple items."""
    # Create another product
    product2 = Product(
        id=uuid.uuid4(),
        sku="TEST-SKU-003",
        name="Test Product 3",
        category="Test Category",
        unit_of_measure="pcs"
    )
    db_session.add(product2)
    db_session.commit()
    
    items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 30,
            "delivered_quantity": 30
        },
        {
            "product_id": str(product2.id),
            "location_id": str(test_location.id),
            "requested_quantity": 20,
            "delivered_quantity": 20
        }
    ]
    
    delivery_order = document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=items
    )
    
    # Verify items were created
    delivery_items = db_session.query(DeliveryOrderItem).filter(
        DeliveryOrderItem.delivery_order_id == delivery_order.id
    ).all()
    
    assert len(delivery_items) == 2



# Multi-Filter Tests

def test_list_documents_all_filters_combined(document_manager, db_session, test_user, test_product, test_location):
    """Test listing documents with all filters applied simultaneously."""
    # Create another location
    other_location = Location(
        id=uuid.uuid4(),
        name="Other Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(other_location)
    db_session.commit()
    
    # Create receipt at test_location with pending status
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create receipt at other_location
    other_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(other_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    document_manager.create_receipt(
        supplier_name="Other Supplier",
        created_by=str(test_user.id),
        items=other_items
    )
    
    # Create delivery order at test_location
    delivery_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 30,
            "delivered_quantity": 30
        }
    ]
    document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=delivery_items
    )
    
    # Filter by document_type=receipt, status=pending, location=test_location
    filtered_docs = document_manager.list_documents(
        document_type="receipt",
        status="pending",
        location_id=str(test_location.id)
    )
    
    # Should only return the first receipt
    assert len(filtered_docs) == 1
    assert filtered_docs[0]["document_type"] == "receipt"
    assert filtered_docs[0]["status"] == "pending"


def test_list_documents_type_and_status_filter(document_manager, test_user, test_product, test_location):
    """Test listing documents filtered by type and status."""
    # Create multiple receipts
    for i in range(3):
        items = [
            {
                "product_id": str(test_product.id),
                "location_id": str(test_location.id),
                "expected_quantity": 100,
                "received_quantity": 95
            }
        ]
        document_manager.create_receipt(
            supplier_name=f"Supplier {i}",
            created_by=str(test_user.id),
            items=items
        )
    
    # Create delivery orders
    for i in range(2):
        items = [
            {
                "product_id": str(test_product.id),
                "location_id": str(test_location.id),
                "requested_quantity": 50,
                "delivered_quantity": 50
            }
        ]
        document_manager.create_delivery_order(
            customer_name=f"Customer {i}",
            created_by=str(test_user.id),
            items=items
        )
    
    # Filter by type and status
    receipts = document_manager.list_documents(
        document_type="receipt",
        status="pending"
    )
    
    assert len(receipts) == 3
    assert all(doc["document_type"] == "receipt" for doc in receipts)
    assert all(doc["status"] == "pending" for doc in receipts)


def test_list_documents_status_and_location_filter(document_manager, db_session, test_user, test_product, test_location):
    """Test listing documents filtered by status and location."""
    # Create another location
    other_location = Location(
        id=uuid.uuid4(),
        name="Other Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(other_location)
    db_session.commit()
    
    # Create receipts at test_location
    for i in range(2):
        items = [
            {
                "product_id": str(test_product.id),
                "location_id": str(test_location.id),
                "expected_quantity": 100,
                "received_quantity": 95
            }
        ]
        document_manager.create_receipt(
            supplier_name=f"Supplier {i}",
            created_by=str(test_user.id),
            items=items
        )
    
    # Create receipt at other_location
    other_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(other_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    document_manager.create_receipt(
        supplier_name="Other Supplier",
        created_by=str(test_user.id),
        items=other_items
    )
    
    # Filter by status and location
    filtered_docs = document_manager.list_documents(
        status="pending",
        location_id=str(test_location.id)
    )
    
    # Should return documents from test_location only
    assert len(filtered_docs) >= 2
    assert all(doc["status"] == "pending" for doc in filtered_docs)


def test_list_documents_type_and_location_filter(document_manager, db_session, test_user, test_product, test_location):
    """Test listing documents filtered by type and location."""
    # Create another location
    other_location = Location(
        id=uuid.uuid4(),
        name="Other Warehouse",
        type=LocationType.warehouse,
        is_archived=False
    )
    db_session.add(other_location)
    db_session.commit()
    
    # Create receipt at test_location
    receipt_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "expected_quantity": 100,
            "received_quantity": 95
        }
    ]
    document_manager.create_receipt(
        supplier_name="Test Supplier",
        created_by=str(test_user.id),
        items=receipt_items
    )
    
    # Create delivery order at test_location
    delivery_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(test_location.id),
            "requested_quantity": 50,
            "delivered_quantity": 50
        }
    ]
    document_manager.create_delivery_order(
        customer_name="Test Customer",
        created_by=str(test_user.id),
        items=delivery_items
    )
    
    # Create receipt at other_location
    other_items = [
        {
            "product_id": str(test_product.id),
            "location_id": str(other_location.id),
            "expected_quantity": 50,
            "received_quantity": 50
        }
    ]
    document_manager.create_receipt(
        supplier_name="Other Supplier",
        created_by=str(test_user.id),
        items=other_items
    )
    
    # Filter by type and location
    filtered_docs = document_manager.list_documents(
        document_type="receipt",
        location_id=str(test_location.id)
    )
    
    assert len(filtered_docs) == 1
    assert filtered_docs[0]["document_type"] == "receipt"
