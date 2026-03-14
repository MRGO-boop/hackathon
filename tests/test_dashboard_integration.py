"""Integration tests for Dashboard component."""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User
from core_inventory.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.components.dashboard import Dashboard
from core_inventory.components.product_manager import ProductManager
from core_inventory.components.document_manager import DocumentManager
from core_inventory.components.validator import Validator


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
def dashboard(db_session):
    """Create a Dashboard instance."""
    return Dashboard(db_session)


@pytest.fixture
def product_manager(db_session):
    """Create a ProductManager instance."""
    return ProductManager(db_session)


@pytest.fixture
def document_manager(db_session):
    """Create a DocumentManager instance."""
    return DocumentManager(db_session)


@pytest.fixture
def validator(db_session):
    """Create a Validator instance."""
    return Validator(db_session)


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


class TestDashboardRealTimeUpdates:
    """Test that dashboard KPIs update in real-time when stock changes."""
    
    def test_kpis_update_after_receipt_validation(
        self, dashboard, product_manager, document_manager, validator, 
        test_user, test_location, db_session
    ):
        """Dashboard should reflect changes after receipt validation."""
        # Create product with low stock threshold
        product = product_manager.create_product(
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=50
        )
        
        # Initial KPIs - product exists with zero stock
        kpis = dashboard.get_all_kpis()
        assert kpis["total_products"] == 1
        assert kpis["zero_stock_products"] == 1
        assert kpis["low_stock_products"] == 1  # Zero is below threshold
        assert kpis["pending_receipts"] == 0
        
        # Create a receipt
        receipt = document_manager.create_receipt(
            supplier_name="Supplier A",
            created_by=str(test_user.id),
            items=[{
                "product_id": str(product.id),
                "location_id": str(test_location.id),
                "expected_quantity": 100,
                "received_quantity": 100
            }]
        )
        
        # KPIs after receipt creation - should show pending receipt
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_receipts"] == 1
        assert kpis["zero_stock_products"] == 1  # Still zero until validated
        
        # Validate receipt
        validator.validate_receipt(str(receipt.id), str(test_user.id))
        
        # KPIs after validation - stock should be updated
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_receipts"] == 0
        assert kpis["zero_stock_products"] == 0
        assert kpis["low_stock_products"] == 0  # 100 is above threshold of 50
    
    def test_kpis_update_after_delivery_validation(
        self, dashboard, product_manager, document_manager, validator,
        test_user, test_location, db_session
    ):
        """Dashboard should reflect changes after delivery validation."""
        # Create product with initial stock
        product = product_manager.create_product(
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=20,
            initial_stock_quantity=100,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Initial KPIs
        kpis = dashboard.get_all_kpis()
        assert kpis["low_stock_products"] == 0  # 100 is above threshold
        assert kpis["pending_delivery_orders"] == 0
        
        # Create delivery order
        delivery_order = document_manager.create_delivery_order(
            customer_name="Customer A",
            created_by=str(test_user.id),
            items=[{
                "product_id": str(product.id),
                "location_id": str(test_location.id),
                "requested_quantity": 85,
                "delivered_quantity": 85
            }]
        )
        
        # KPIs after delivery creation
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_delivery_orders"] == 1
        
        # Validate delivery
        validator.validate_delivery_order(str(delivery_order.id), str(test_user.id))
        
        # KPIs after validation - stock reduced to 15, below threshold of 20
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_delivery_orders"] == 0
        assert kpis["low_stock_products"] == 1
        assert kpis["zero_stock_products"] == 0
    
    def test_kpis_update_after_transfer_validation(
        self, dashboard, product_manager, document_manager, validator,
        test_user, test_location, db_session
    ):
        """Dashboard should reflect changes after transfer validation."""
        # Create second location
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse 2",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location2)
        db_session.commit()
        
        # Create product with initial stock at location 1
        product = product_manager.create_product(
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=30,
            initial_stock_quantity=50,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Initial KPIs
        kpis = dashboard.get_all_kpis()
        assert kpis["low_stock_products"] == 0  # 50 is above threshold
        assert kpis["pending_transfers"] == 0
        
        # Create transfer
        transfer = document_manager.create_transfer(
            source_location_id=str(test_location.id),
            destination_location_id=str(location2.id),
            product_id=str(product.id),
            quantity=25,
            created_by=str(test_user.id)
        )
        
        # KPIs after transfer creation
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_transfers"] == 1
        
        # Validate transfer
        validator.validate_transfer(str(transfer.id), str(test_user.id))
        
        # KPIs after validation - total stock still 50, but distributed
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_transfers"] == 0
        assert kpis["low_stock_products"] == 0  # Total still 50
        assert kpis["zero_stock_products"] == 0


class TestDashboardComplexScenarios:
    """Test dashboard with complex real-world scenarios."""
    
    def test_multiple_products_various_states(
        self, dashboard, product_manager, test_user, test_location, db_session
    ):
        """Test dashboard with multiple products in various states."""
        # Product 1: Normal stock
        product1 = product_manager.create_product(
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=10,
            initial_stock_quantity=50,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Product 2: Low stock
        product2 = product_manager.create_product(
            sku="SKU-002",
            name="Product 2",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=20,
            initial_stock_quantity=5,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Product 3: Zero stock
        product3 = product_manager.create_product(
            sku="SKU-003",
            name="Product 3",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=15
        )
        
        # Product 4: No threshold configured
        product4 = product_manager.create_product(
            sku="SKU-004",
            name="Product 4",
            category="Electronics",
            unit_of_measure="pieces",
            initial_stock_quantity=100,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Check KPIs
        kpis = dashboard.get_all_kpis()
        assert kpis["total_products"] == 4
        assert kpis["low_stock_products"] == 2  # Product 2 and 3
        assert kpis["zero_stock_products"] == 1  # Product 3
    
    def test_pending_documents_mixed_statuses(
        self, dashboard, document_manager, test_user, test_location, db_session
    ):
        """Test dashboard counts only pending documents, not validated ones."""
        # Create products
        product1 = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces"
        )
        product2 = Product(
            id=uuid.uuid4(),
            sku="SKU-002",
            name="Product 2",
            category="Electronics",
            unit_of_measure="pieces"
        )
        db_session.add_all([product1, product2])
        db_session.commit()
        
        # Add stock for products
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product1.id,
            location_id=test_location.id,
            quantity=100
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product2.id,
            location_id=test_location.id,
            quantity=100
        )
        db_session.add_all([stock1, stock2])
        db_session.commit()
        
        # Create receipts - 2 pending, 1 validated
        receipt1 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 1",
            status=ReceiptStatus.pending,
            created_by=test_user.id
        )
        receipt2 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 2",
            status=ReceiptStatus.pending,
            created_by=test_user.id
        )
        receipt3 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 3",
            status=ReceiptStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        db_session.add_all([receipt1, receipt2, receipt3])
        db_session.commit()
        
        # Create delivery orders - 1 pending, 1 picking, 1 validated
        order1 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 1",
            status=DeliveryOrderStatus.pending,
            created_by=test_user.id
        )
        order2 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 2",
            status=DeliveryOrderStatus.picking,
            created_by=test_user.id
        )
        order3 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 3",
            status=DeliveryOrderStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        db_session.add_all([order1, order2, order3])
        db_session.commit()
        
        # Create second location for transfers
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse 2",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location2)
        db_session.commit()
        
        # Create transfers - 3 pending, 2 validated
        transfer1 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product1.id,
            quantity=10,
            status=TransferStatus.pending,
            created_by=test_user.id
        )
        transfer2 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product2.id,
            quantity=10,
            status=TransferStatus.pending,
            created_by=test_user.id
        )
        transfer3 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product1.id,
            quantity=5,
            status=TransferStatus.pending,
            created_by=test_user.id
        )
        transfer4 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product2.id,
            quantity=5,
            status=TransferStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        transfer5 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product1.id,
            quantity=3,
            status=TransferStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        db_session.add_all([transfer1, transfer2, transfer3, transfer4, transfer5])
        db_session.commit()
        
        # Check KPIs
        kpis = dashboard.get_all_kpis()
        assert kpis["pending_receipts"] == 2
        assert kpis["pending_delivery_orders"] == 1  # Only pending status
        assert kpis["pending_transfers"] == 3
    
    def test_stock_across_multiple_warehouses(
        self, dashboard, product_manager, test_user, test_location, db_session
    ):
        """Test that dashboard correctly sums stock across multiple locations."""
        # Create additional locations
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse 2",
            type=LocationType.warehouse,
            is_archived=False
        )
        location3 = Location(
            id=uuid.uuid4(),
            name="Warehouse 3",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add_all([location2, location3])
        db_session.commit()
        
        # Create product with threshold
        product = product_manager.create_product(
            sku="SKU-001",
            name="Product 1",
            category="Electronics",
            unit_of_measure="pieces",
            low_stock_threshold=100,
            initial_stock_quantity=30,
            initial_stock_location_id=str(test_location.id),
            user_id=str(test_user.id)
        )
        
        # Add stock at other locations
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location2.id,
            quantity=40
        )
        stock3 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location3.id,
            quantity=35
        )
        db_session.add_all([stock2, stock3])
        db_session.commit()
        
        # Total stock = 30 + 40 + 35 = 105, which is above threshold of 100
        kpis = dashboard.get_all_kpis()
        assert kpis["low_stock_products"] == 0
        assert kpis["zero_stock_products"] == 0
        
        # Now reduce stock at location 2 to bring total below threshold
        stock2.quantity = 20
        db_session.commit()
        
        # Total stock = 30 + 20 + 35 = 85, which is below threshold of 100
        kpis = dashboard.get_all_kpis()
        assert kpis["low_stock_products"] == 1
        assert kpis["zero_stock_products"] == 0
