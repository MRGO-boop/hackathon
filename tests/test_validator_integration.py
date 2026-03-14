"""Integration tests for Validator component."""
import pytest
import uuid
from core_inventory.components.validator import Validator, ValidationError
from core_inventory.components.stock_manager import StockManager
from core_inventory.components.history_logger import HistoryLogger
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


class TestValidatorTransactionAtomicity:
    """Tests for transaction atomicity in validator operations."""
    
    def test_receipt_validation_atomic_commit(self, db_session, setup_test_data):
        """Test that receipt validation commits all changes atomically."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Create receipt with multiple items
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Test Supplier",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        items = [
            ReceiptItem(
                id=uuid.uuid4(),
                receipt_id=receipt.id,
                product_id=data["product1"].id,
                location_id=data["warehouse1"].id,
                expected_quantity=100,
                received_quantity=100
            ),
            ReceiptItem(
                id=uuid.uuid4(),
                receipt_id=receipt.id,
                product_id=data["product2"].id,
                location_id=data["warehouse1"].id,
                expected_quantity=50,
                received_quantity=50
            )
        ]
        db_session.add_all(items)
        db_session.commit()
        
        # Validate receipt
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Verify all changes committed
        db_session.refresh(receipt)
        assert receipt.status == ReceiptStatus.validated
        
        # Verify stock updated for all items
        stock1 = db_session.query(Stock).filter(
            Stock.product_id == data["product1"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        stock2 = db_session.query(Stock).filter(
            Stock.product_id == data["product2"].id,
            Stock.location_id == data["warehouse1"].id
        ).first()
        
        assert stock1.quantity == 100
        assert stock2.quantity == 50
        
        # Verify history entries created for all items
        history_entries = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(receipt.id)
        ).all()
        assert len(history_entries) == 2
    
    def test_delivery_validation_rollback_on_error(self, db_session, setup_test_data):
        """Test that delivery validation rolls back on insufficient stock."""
        data = setup_test_data
        validator = Validator(db_session)
        
        # Setup stock for first item only
        stock1 = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock1)
        db_session.commit()
        
        # Create delivery order with two items (second has no stock)
        order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Test Customer",
            status=DeliveryOrderStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(order)
        db_session.commit()
        
        items = [
            DeliveryOrderItem(
                id=uuid.uuid4(),
                delivery_order_id=order.id,
                product_id=data["product1"].id,
                location_id=data["warehouse1"].id,
                requested_quantity=30,
                delivered_quantity=30
            ),
            DeliveryOrderItem(
                id=uuid.uuid4(),
                delivery_order_id=order.id,
                product_id=data["product2"].id,
                location_id=data["warehouse1"].id,
                requested_quantity=20,
                delivered_quantity=20
            )
        ]
        db_session.add_all(items)
        db_session.commit()
        
        # Attempt validation (should fail on second item)
        with pytest.raises(ValidationError):
            validator.validate_delivery_order(str(order.id), str(data["user"].id))
        
        # Verify rollback: order status unchanged
        db_session.refresh(order)
        assert order.status == DeliveryOrderStatus.pending
        
        # Verify rollback: stock unchanged
        db_session.refresh(stock1)
        assert stock1.quantity == 100
        
        # Verify rollback: no history entries created
        history_entries = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(order.id)
        ).all()
        assert len(history_entries) == 0


class TestValidatorCoordinationWithComponents:
    """Tests for validator coordination with Stock Manager and History Logger."""
    
    def test_receipt_validation_coordinates_stock_and_history(self, db_session, setup_test_data):
        """Test that receipt validation properly coordinates stock updates and history logging."""
        data = setup_test_data
        validator = Validator(db_session)
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
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
            received_quantity=95
        )
        db_session.add(item)
        db_session.commit()
        
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Verify stock via Stock Manager
        stock = stock_manager.get_stock(str(data["product1"].id), str(data["warehouse1"].id))
        assert stock == 95
        
        # Verify history via History Logger
        history = history_logger.get_move_history(
            product_id=str(data["product1"].id),
            location_id=str(data["warehouse1"].id)
        )
        assert len(history) == 1
        assert history[0]["quantity_change"] == 95
        assert history[0]["document_type"] == "receipt"
    
    def test_transfer_validation_creates_dual_history_entries(self, db_session, setup_test_data):
        """Test that transfer validation creates history entries for both locations."""
        data = setup_test_data
        validator = Validator(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Setup initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        # Create and validate transfer
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
        
        validator.validate_transfer(str(transfer.id), str(data["user"].id))
        
        # Verify history at source location
        source_history = history_logger.get_move_history(
            location_id=str(data["warehouse1"].id)
        )
        assert len(source_history) == 1
        assert source_history[0]["quantity_change"] == -30
        assert source_history[0]["source_location_id"] == str(data["warehouse1"].id)
        assert source_history[0]["destination_location_id"] == str(data["warehouse2"].id)
        
        # Verify history at destination location
        dest_history = history_logger.get_move_history(
            location_id=str(data["warehouse2"].id)
        )
        assert len(dest_history) == 1
        assert dest_history[0]["quantity_change"] == 30
        assert dest_history[0]["source_location_id"] == str(data["warehouse1"].id)
        assert dest_history[0]["destination_location_id"] == str(data["warehouse2"].id)


class TestCompleteWorkflows:
    """Integration tests for complete document workflows."""
    
    def test_complete_receipt_to_delivery_workflow(self, db_session, setup_test_data):
        """Test complete workflow: receive stock via receipt, then deliver via order."""
        data = setup_test_data
        validator = Validator(db_session)
        stock_manager = StockManager(db_session)
        
        # Step 1: Create and validate receipt
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier A",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        receipt_item = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=100,
            received_quantity=100
        )
        db_session.add(receipt_item)
        db_session.commit()
        
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Verify stock after receipt
        stock_after_receipt = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse1"].id)
        )
        assert stock_after_receipt == 100
        
        # Step 2: Create and validate delivery order
        order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name="Customer A",
            status=DeliveryOrderStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(order)
        db_session.commit()
        
        order_item = DeliveryOrderItem(
            id=uuid.uuid4(),
            delivery_order_id=order.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            requested_quantity=30,
            delivered_quantity=30
        )
        db_session.add(order_item)
        db_session.commit()
        
        validator.validate_delivery_order(str(order.id), str(data["user"].id))
        
        # Verify final stock
        final_stock = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse1"].id)
        )
        assert final_stock == 70
        
        # Verify complete history
        history = db_session.query(MoveHistory).filter(
            MoveHistory.product_id == data["product1"].id,
            MoveHistory.location_id == data["warehouse1"].id
        ).order_by(MoveHistory.timestamp).all()
        
        assert len(history) == 2
        assert history[0].document_type.value == "receipt"
        assert history[0].quantity_change == 100
        assert history[1].document_type.value == "delivery_order"
        assert history[1].quantity_change == -30
    
    def test_complete_transfer_workflow(self, db_session, setup_test_data):
        """Test complete transfer workflow between two warehouses."""
        data = setup_test_data
        validator = Validator(db_session)
        stock_manager = StockManager(db_session)
        
        # Setup: Add stock at warehouse1 via receipt
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier A",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(receipt)
        db_session.commit()
        
        receipt_item = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=200,
            received_quantity=200
        )
        db_session.add(receipt_item)
        db_session.commit()
        
        validator.validate_receipt(str(receipt.id), str(data["user"].id))
        
        # Transfer stock from warehouse1 to warehouse2
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=data["warehouse1"].id,
            destination_location_id=data["warehouse2"].id,
            product_id=data["product1"].id,
            quantity=80,
            status=TransferStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(transfer)
        db_session.commit()
        
        validator.validate_transfer(str(transfer.id), str(data["user"].id))
        
        # Verify stock at both locations
        stock_w1 = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse1"].id)
        )
        stock_w2 = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse2"].id)
        )
        
        assert stock_w1 == 120
        assert stock_w2 == 80
        
        # Verify total stock conserved
        assert stock_w1 + stock_w2 == 200
    
    def test_stock_adjustment_workflow(self, db_session, setup_test_data):
        """Test stock adjustment workflow after physical count."""
        data = setup_test_data
        validator = Validator(db_session)
        stock_manager = StockManager(db_session)
        
        # Setup: Add initial stock
        stock = Stock(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            quantity=100
        )
        db_session.add(stock)
        db_session.commit()
        
        # Physical count reveals discrepancy
        adjustment = StockAdjustment(
            id=uuid.uuid4(),
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            recorded_quantity=100,
            physical_quantity=92,
            adjustment_difference=-8,
            reason="Physical count found 8 units missing",
            status=StockAdjustmentStatus.pending,
            created_by=data["user"].id
        )
        db_session.add(adjustment)
        db_session.commit()
        
        validator.validate_stock_adjustment(str(adjustment.id), str(data["user"].id))
        
        # Verify stock corrected to physical count
        final_stock = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse1"].id)
        )
        assert final_stock == 92
        
        # Verify history includes reason
        history = db_session.query(MoveHistory).filter(
            MoveHistory.document_id == str(adjustment.id)
        ).first()
        assert history.reason == "Physical count found 8 units missing"
        assert history.quantity_change == -8


class TestConcurrentValidations:
    """Tests for handling concurrent validation scenarios."""
    
    def test_multiple_receipts_same_product_different_locations(self, db_session, setup_test_data):
        """Test validating multiple receipts for same product at different locations."""
        data = setup_test_data
        validator = Validator(db_session)
        stock_manager = StockManager(db_session)
        
        # Create two receipts for same product at different locations
        receipt1 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier A",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        receipt2 = Receipt(
            id=uuid.uuid4(),
            supplier_name="Supplier B",
            status=ReceiptStatus.pending,
            created_by=data["user"].id
        )
        db_session.add_all([receipt1, receipt2])
        db_session.commit()
        
        item1 = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt1.id,
            product_id=data["product1"].id,
            location_id=data["warehouse1"].id,
            expected_quantity=100,
            received_quantity=100
        )
        item2 = ReceiptItem(
            id=uuid.uuid4(),
            receipt_id=receipt2.id,
            product_id=data["product1"].id,
            location_id=data["warehouse2"].id,
            expected_quantity=150,
            received_quantity=150
        )
        db_session.add_all([item1, item2])
        db_session.commit()
        
        # Validate both receipts
        validator.validate_receipt(str(receipt1.id), str(data["user"].id))
        validator.validate_receipt(str(receipt2.id), str(data["user"].id))
        
        # Verify independent stock tracking
        stock_w1 = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse1"].id)
        )
        stock_w2 = stock_manager.get_stock(
            str(data["product1"].id),
            str(data["warehouse2"].id)
        )
        
        assert stock_w1 == 100
        assert stock_w2 == 150
