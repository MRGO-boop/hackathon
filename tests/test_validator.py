"""Unit tests for Validator component."""
import pytest
import uuid
from datetime import datetime
from core_inventory.components.validator import Validator, ValidationError
from core_inventory.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.models.stock_adjustment import StockAdjustment, StockAdjustmentStatus
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User
from core_inventory.models.stock import Stock
from core_inventory.models.move_history import MoveHistory


@pytest.fixture
def setup_test_data(db_session):
    """Create test users, products, and locations."""
    # Create user
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User"
    )
    
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
        unit_of_measure="pieces"
    )
    product2 = Product(
        id=uuid.uuid4(),
        sku="PROD-002",
        name="Product Two",
        category="Furniture",
        unit_of_measure="pieces"
    )
    
    db_session.add_all([user, warehouse1, warehouse2, product1, product2])
    db_session.commit()
    
    return {
        "user": user,
        "warehouse1": warehouse1,
        "warehouse2": warehouse2,
        "product1": product1,
        "product2": product2
    }


class TestReceiptValidation:
    """Tests for receipt validation."""
    
    def test_validate_receipt_success(self, db_session, setup_test_data):
        """Test successful receipt validation."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Create receipt
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Test Supplier",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        # Add receipt items
        item1 = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=100,
            received_quantity=95
        )
        item2 = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            product_id=data["product2"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=50,
            received_quantity=50
        )
        db_session.add_all([item1, item2])
        db_session.commit()
        
        # Validate receipt
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Verify receipt status
        db_session.refresh(receipt)
        assert receipt.status == ReceiptStatus.validated
        assert receipt.validated_by == data["user"].id
        assert receipt.validated_at is not None
        
        # Verify stock updated
        stock1 = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        stock2 = db_session.query(Stock).filter(
            Stock.product_id == data["product2"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        
        assert stock1.quantity == 95
        assert stock2.quantity == 50
        
        # Verify move history created
        history_entries = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(receipt.id)
        ).all()
        assert len(history_entries) == 2
    
    def test_validate_receipt_idempotency(self, db_session, setup_test_data):
        """Test that validating an already-validated receipt returns success."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Create and validate receipt
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Test Supplier",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        item = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=100,
            received_quantity=100
        )
        db_session.add(item)
        db_session.commit()
        
        # First validation
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Get stock after first validation
        stock_after_first = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        first_quantity = stock_after_first.quantity
        
        # Second validation (should be idempotent)
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Verify stock unchanged
        db_session.refresh(stock_after_first)
        assert stock_after_first.quantity == first_quantity
    
    def test_validate_receipt_not_found(self, db_session, setup_test_data):
        """Test validation fails for non-existent receipt."""
        data = setup_test_data
        validator = Validator(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_receipt(str(uuid.uuid4()), str(data["user"].id))
        
        assert exc_info.value.code == "RECEIPT_NOT_FOUND"
    
    def test_validate_receipt_no_items(self, db_session, setup_test_data):
        """Test validation fails for receipt with no items."""
        data = setup_test_data
        validator = Validator(db_session)
        
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Test Supplier",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        assert exc_info.value.code == "NO_ITEMS"


class TestDeliveryOrderValidation:
    """Tests for delivery order validation."""
    
    def test_validate_delivery_order_success(self, db_session, setup_test_data):
        """Test successful delivery order validation."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        stock2 = Stock(
            id=uuid.uuid4(),
            product_id=data["product2"].id,
            location_id=data["warehouse1"].id,
            quantity=50
        )
        db_session.add_all([stock1, stock2])
        db_session.commit()
        
        # Create delivery order
        order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Test Customer",
            status=DeliveryOrderStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(order)
        db_session.commit()
        
        # Add order items
        item1 = DeliveryOrderItem(
            id=uuid.uuid4(),
            delivery_order_id=order.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            requested_quantity=30,
            delivered_quantity=30
        )
        item2 = DeliveryOrderItem(
            id=uuid.uuid4(),
            delivery_order_id=order.id,
            product_id=data["product2"].id,
            location_id=data["warehouse1"].id,
            requested_quantity=20,
            delivered_quantity=20
        )
        db_session.add_all([item1, item2])
        db_session.commit()
        
        # Validate order
        validator.validate_delivery_order(str(order.id), str(data["user"].id))
        
        # Verify order status
        db_session.refresh(order)
        assert order.status == DeliveryOrderStatus.validated
        assert order.validated_by == data["user"].id
        assert order.validated_at is not None
        
        # Verify stock decreased
        db_session.refresh(stock1)
        db_session.refresh(stock2)
        assert stock1.quantity == 70
        assert stock2.quantity == 30
        
        # Verify move history created
        history_entries = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(order.id)
        ).all()
        assert len(history_entries) == 2
    
    def test_validate_delivery_order_insufficient_stock(self, db_session, setup_test_data):
        """Test validation fails when stock is insufficient."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock (low)
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        # Create delivery order requesting more than available
        order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Test Customer",
            status=DeliveryOrderStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(order)
        db_session.commit()
        
        item = DeliveryOrderItem(
            id=uuid.uuid4(),
            delivery_order_id=order.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            requested_quantity=50,
            delivered_quantity=50
        )
        db_session.add(item)
        db_session.commit()
        
        # Attempt validation
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_delivery_order(str(order.id), str(data["user"].id))
        
        assert exc_info.value.code == "INSUFFICIENT_STOCK"
        
        # Verify stock unchanged (transaction rolled back)
        db_session.refresh(stock)
        assert stock.quantity == 10
    
    def test_validate_delivery_order_already_validated(self, db_session, setup_test_data):
        """Test validation fails for already-validated order."""
        data = setup_test_data
        validator = Validator(db_session)
        
        order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Test Customer",
            status=DeliveryOrderStatus.validated,
            created_by=data["user"].id,
            validated_by=data["user"].id,
            validated_at=datetime.utcnow()
        )
        db_session.add(order)
        db_session.commit()
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_delivery_order(str(order.id), str(data["user"].id))
        
        assert exc_info.value.code == "ALREADY_VALIDATED"


class TestTransferValidation:
    """Tests for transfer validation."""
    
    def test_validate_transfer_success(self, db_session, setup_test_data):
        """Test successful transfer validation."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock at source
        stock_source = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock_source)
        db_session.commit()
        
        # Create transfer
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=data["warehouse1"].id,
            destination_location_id=data["warehouse2"].id,
            product_id=data["product1"].id,
            quantity=30,
            status=TransferStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(transfer)
        db_session.commit()
        
        # Validate transfer
        validator.validate_transfer(str(transfer.id), str(data["user"].id))
        
        # Verify transfer status
        db_session.refresh(transfer)
        assert transfer.status == TransferStatus.validated
        assert transfer.validated_by == data["user"].id
        assert transfer.validated_at is not None
        
        # Verify stock at source decreased
        db_session.refresh(stock_source)
        assert stock_source.quantity == 70
        
        # Verify stock at destination increased
        stock_dest = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse2"].id
        ).first()
        assert stock_dest.quantity == 30
        
        # Verify move history created (2 entries: source and destination)
        history_entries = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(transfer.id)
        ).all()
        assert len(history_entries) == 2
    
    def test_validate_transfer_insufficient_stock(self, db_session, setup_test_data):
        """Test validation fails when source has insufficient stock."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock (low)
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=10
        )
        db_session.add(stock)
        db_session.commit()
        
        # Create transfer requesting more than available
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=data["warehouse1"].id,
            destination_location_id=data["warehouse2"].id,
            product_id=data["product1"].id,
            quantity=50,
            status=TransferStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(transfer)
        db_session.commit()
        
        # Attempt validation
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_transfer(str(transfer.id), str(data["user"].id))
        
        assert exc_info.value.code == "INSUFFICIENT_STOCK"
        
        # Verify stock unchanged
        db_session.refresh(stock)
        assert stock.quantity == 10
    
    def test_validate_transfer_quantity_conservation(self, db_session, setup_test_data):
        """Test that transfer conserves quantity (decrease at source = increase at dest)."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock
        stock_source = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock_source)
        db_session.commit()
        
        # Create transfer
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=data["warehouse1"].id,
            destination_location_id=data["warehouse2"].id,
            product_id=data["product1"].id,
            quantity=40,
            status=TransferStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(transfer)
        db_session.commit()
        
        # Validate transfer
        validator.validate_transfer(str(transfer.id), str(data["user"].id))
        
        # Get final stocks
        stock_source_final = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        stock_dest_final = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse2"].id
        ).first()
        
        # Verify conservation: initial_source - final_source = final_dest - initial_dest
        source_decrease = 100 - stock_source_final.quantity
        dest_increase = stock_dest_final.quantity - 0
        
        assert source_decrease == 40
        assert dest_increase == 40
        assert source_decrease == dest_increase


class TestStockAdjustmentValidation:
    """Tests for stock adjustment validation."""
    
    def test_validate_stock_adjustment_success(self, db_session, setup_test_data):
        """Test successful stock adjustment validation."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        # Create stock adjustment
        adjustment = StockAdjustment(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            recorded_quantity=100,
            physical_quantity=95,
            adjustment_difference=-5,
            reason="Physical count discrepancy",
            status=StockAdjustmentStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(adjustment)
        db_session.commit()
        
        # Validate adjustment
        validator.validate_stock_adjustment(str(adjustment.id), str(data["user"].id))
        
        # Verify adjustment status
        db_session.refresh(adjustment)
        assert adjustment.status == StockAdjustmentStatus.validated
        assert adjustment.validated_by == data["user"].id
        assert adjustment.validated_at is not None
        
        # Verify stock set to physical_quantity
        db_session.refresh(stock)
        assert stock.quantity == 95
        
        # Verify move history created with reason
        history_entry = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(adjustment.id)
        ).first()
        assert history_entry is not None
        assert history_entry.reason == "Physical count discrepancy"
        assert history_entry.quantity_change == -5
    
    def test_validate_stock_adjustment_sets_physical_quantity(self, db_session, setup_test_data):
        """Test that adjustment sets stock to exact physical_quantity."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=50
        )
        db_session.add(stock)
        db_session.commit()
        
        # Create adjustment to increase stock
        adjustment = StockAdjustment(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            recorded_quantity=50,
            physical_quantity=120,
            adjustment_difference=70,
            reason="Found additional stock",
            status=StockAdjustmentStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(adjustment)
        db_session.commit()
        
        # Validate adjustment
        validator.validate_stock_adjustment(str(adjustment.id), str(data["user"].id))
        
        # Verify stock is exactly physical_quantity
        db_session.refresh(stock)
        assert stock.quantity == 120
    
    def test_validate_stock_adjustment_already_validated(self, db_session, setup_test_data):
        """Test validation fails for already-validated adjustment."""
        data = setup_test_data
        validator = Validator(db_session)
        
        adjustment = StockAdjustment(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            recorded_quantity=100,
            physical_quantity=95,
            adjustment_difference=-5,
            reason="Test",
            status=StockAdjustmentStatus.validated,
            created_by=data["user"].id,
            validated_by=data["user"].id,
            validated_at=datetime.utcnow()
        )
        db_session.add(adjustment)
        db_session.commit()
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_stock_adjustment(str(adjustment.id), str(data["user"].id))
        
        assert exc_info.value.code == "ALREADY_VALIDATED"
