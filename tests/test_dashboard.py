"""Unit tests for Dashboard component."""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core_inventory.database import Base
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User
from core_inventory.models.receipt import Receipt, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.components.dashboard import Dashboard


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


class TestTotalProductCount:
    """Tests for get_total_product_count."""
    
    def test_zero_products(self, dashboard):
        """Should return 0 when no products exist."""
        count = dashboard.get_total_product_count()
        assert count == 0
    
    def test_single_product(self, dashboard, db_session):
        """Should return 1 when one product exists."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        count = dashboard.get_total_product_count()
        assert count == 1
    
    def test_multiple_products(self, dashboard, db_session):
        """Should return correct count for multiple products."""
        products = [
            Product(
                id=uuid.uuid4(),
                sku=f"SKU-{i:03d}",
                name=f"Product {i}",
                category="Category A",
                unit_of_measure="pieces"
            )
            for i in range(1, 6)
        ]
        for product in products:
            db_session.add(product)
        db_session.commit()
        
        count = dashboard.get_total_product_count()
        assert count == 5


class TestLowStockProductCount:
    """Tests for get_low_stock_product_count."""
    
    def test_no_products_with_threshold(self, dashboard, db_session):
        """Should return 0 when no products have threshold configured."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=None
        )
        db_session.add(product)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 0
    
    def test_product_above_threshold(self, dashboard, db_session, test_location):
        """Should not count product with stock above threshold."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        db_session.add(product)
        db_session.commit()
        
        # Add stock above threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=test_location.id,
            quantity=15
        )
        db_session.add(stock)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 0
    
    def test_product_below_threshold(self, dashboard, db_session, test_location):
        """Should count product with stock below threshold."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        db_session.add(product)
        db_session.commit()
        
        # Add stock below threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=test_location.id,
            quantity=5
        )
        db_session.add(stock)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 1
    
    def test_product_at_threshold(self, dashboard, db_session, test_location):
        """Should not count product with stock exactly at threshold."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        db_session.add(product)
        db_session.commit()
        
        # Add stock exactly at threshold
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=test_location.id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 0
    
    def test_product_with_no_stock_records(self, dashboard, db_session):
        """Should count product with threshold but no stock records."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        db_session.add(product)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 1
    
    def test_product_across_multiple_locations(self, dashboard, db_session):
        """Should sum stock across all locations when checking threshold."""
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
        
        # Create product with threshold
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=20
        )
        db_session.add(product)
        db_session.commit()
        
        # Add stock at both locations (total = 25, above threshold)
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location1.id,
            quantity=10
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location2.id,
            quantity=15
        )
        db_session.add(stock1)
        db_session.add(stock2)
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 0
    
    def test_multiple_products_mixed_status(self, dashboard, db_session, test_location):
        """Should correctly count only low stock products."""
        # Product 1: below threshold
        product1 = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product1.id,
            location_id=test_location.id,
            quantity=5
        )
        
        # Product 2: above threshold
        product2 = Product(
            id=uuid.uuid4(),
            sku="SKU-002",
            name="Product 2",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product2.id,
            location_id=test_location.id,
            quantity=20
        )
        
        # Product 3: no threshold configured
        product3 = Product(
            id=uuid.uuid4(),
            sku="SKU-003",
            name="Product 3",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=None
        )
        
        db_session.add_all([product1, product2, product3, stock1, stock2])
        db_session.commit()
        
        count = dashboard.get_low_stock_product_count()
        assert count == 1


class TestZeroStockProductCount:
    """Tests for get_zero_stock_product_count."""
    
    def test_no_products(self, dashboard):
        """Should return 0 when no products exist."""
        count = dashboard.get_zero_stock_product_count()
        assert count == 0
    
    def test_product_with_no_stock_records(self, dashboard, db_session):
        """Should count product with no stock records as zero stock."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        count = dashboard.get_zero_stock_product_count()
        assert count == 1
    
    def test_product_with_zero_quantity(self, dashboard, db_session, test_location):
        """Should count product with stock record but zero quantity."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=test_location.id,
            quantity=0
        )
        db_session.add(stock)
        db_session.commit()
        
        count = dashboard.get_zero_stock_product_count()
        assert count == 1
    
    def test_product_with_positive_stock(self, dashboard, db_session, test_location):
        """Should not count product with positive stock."""
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        stock = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=test_location.id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        count = dashboard.get_zero_stock_product_count()
        assert count == 0
    
    def test_product_across_multiple_locations_sum_zero(self, dashboard, db_session):
        """Should count product if total stock across all locations is zero."""
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
        
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        # Both locations have zero stock
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location1.id,
            quantity=0
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=product.id,
            location_id=location2.id,
            quantity=0
        )
        db_session.add(stock1)
        db_session.add(stock2)
        db_session.commit()
        
        count = dashboard.get_zero_stock_product_count()
        assert count == 1


class TestPendingDocumentCounts:
    """Tests for pending document count methods."""
    
    def test_pending_receipt_count_zero(self, dashboard):
        """Should return 0 when no receipts exist."""
        count = dashboard.get_pending_receipt_count()
        assert count == 0
    
    def test_pending_receipt_count(self, dashboard, db_session, test_user):
        """Should count only pending receipts."""
        # Create pending receipt
        receipt1 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 1",
            status=ReceiptStatus.pending,
            created_by=test_user.id
        )
        # Create validated receipt
        receipt2 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 2",
            status=ReceiptStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        db_session.add(receipt1)
        db_session.add(receipt2)
        db_session.commit()
        
        count = dashboard.get_pending_receipt_count()
        assert count == 1
    
    def test_pending_delivery_order_count_zero(self, dashboard):
        """Should return 0 when no delivery orders exist."""
        count = dashboard.get_pending_delivery_order_count()
        assert count == 0
    
    def test_pending_delivery_order_count(self, dashboard, db_session, test_user):
        """Should count only pending delivery orders."""
        # Create pending delivery order
        order1 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 1",
            status=DeliveryOrderStatus.pending,
            created_by=test_user.id
        )
        # Create validated delivery order
        order2 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 2",
            status=DeliveryOrderStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        # Create picking status delivery order
        order3 = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 3",
            status=DeliveryOrderStatus.picking,
            created_by=test_user.id
        )
        db_session.add_all([order1, order2, order3])
        db_session.commit()
        
        count = dashboard.get_pending_delivery_order_count()
        assert count == 1
    
    def test_pending_transfer_count_zero(self, dashboard):
        """Should return 0 when no transfers exist."""
        count = dashboard.get_pending_transfer_count()
        assert count == 0
    
    def test_pending_transfer_count(self, dashboard, db_session, test_user, test_location):
        """Should count only pending transfers."""
        # Create another location
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse 2",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location2)
        db_session.commit()
        
        # Create product
        product = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add(product)
        db_session.commit()
        
        # Create pending transfer
        transfer1 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product.id,
            quantity=10,
            status=TransferStatus.pending,
            created_by=test_user.id
        )
        # Create validated transfer
        transfer2 = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product.id,
            quantity=5,
            status=TransferStatus.validated,
            created_by=test_user.id,
            validated_by=test_user.id
        )
        db_session.add(transfer1)
        db_session.add(transfer2)
        db_session.commit()
        
        count = dashboard.get_pending_transfer_count()
        assert count == 1


class TestGetAllKPIs:
    """Tests for get_all_kpis method."""
    
    def test_all_kpis_empty_database(self, dashboard):
        """Should return all zeros for empty database."""
        kpis = dashboard.get_all_kpis()
        
        assert kpis["total_products"] == 0
        assert kpis["low_stock_products"] == 0
        assert kpis["zero_stock_products"] == 0
        assert kpis["pending_receipts"] == 0
        assert kpis["pending_delivery_orders"] == 0
        assert kpis["pending_transfers"] == 0
    
    def test_all_kpis_with_data(self, dashboard, db_session, test_user, test_location):
        """Should return correct values for all KPIs."""
        # Create products
        product1 = Product(
            id=uuid.uuid4(),
            sku="SKU-001",
            name="Product 1",
            category="Category A",
            unit_of_measure="pieces",
            low_stock_threshold=10
        )
        product2 = Product(
            id=uuid.uuid4(),
            sku="SKU-002",
            name="Product 2",
            category="Category A",
            unit_of_measure="pieces"
        )
        db_session.add_all([product1, product2])
        db_session.commit()
        
        # Add stock (product1 has low stock, product2 has zero stock)
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=product1.id,
            location_id=test_location.id,
            quantity=5
        )
        db_session.add(stock1)
        db_session.commit()
        
        # Create pending documents
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier 1",
            status=ReceiptStatus.pending,
            created_by=test_user.id
        )
        delivery_order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer 1",
            status=DeliveryOrderStatus.pending,
            created_by=test_user.id
        )
        
        # Create another location for transfer
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse 2",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location2)
        db_session.commit()
        
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=test_location.id,
            destination_location_id=location2.id,
            product_id=product1.id,
            quantity=2,
            status=TransferStatus.pending,
            created_by=test_user.id
        )
        
        db_session.add_all([receipt, delivery_order, transfer])
        db_session.commit()
        
        # Get all KPIs
        kpis = dashboard.get_all_kpis()
        
        assert kpis["total_products"] == 2
        assert kpis["low_stock_products"] == 1
        assert kpis["zero_stock_products"] == 1
        assert kpis["pending_receipts"] == 1
        assert kpis["pending_delivery_orders"] == 1
        assert kpis["pending_transfers"] == 1
