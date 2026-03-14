"""Unit tests for History Logger component."""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from core_inventory.components.history_logger import HistoryLogger, HistoryError
from core_inventory.models.move_history import MoveHistory, DocumentType
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.models.user import User


class TestLogMovement:
    """Tests for log_movement function."""
    
    def test_log_movement_creates_history_entry(self, db_session: Session):
        """Test that log_movement creates a Move_History entry with all fields."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Execute
        history_id = logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        
        # Verify
        assert history_id is not None
        history = db_session.query(MoveHistory).filter(
            MoveHistory.id == uuid.UUID(history_id)
        ).first()
        assert history is not None
        assert history.product_id == product.id
        assert history.location_id == location.id
        assert history.quantity_change == 100
        assert history.document_type == DocumentType.receipt
        assert history.document_id == "REC-001"
        assert history.user_id == user.id
        assert history.timestamp is not None
    
    def test_log_movement_with_transfer_locations(self, db_session: Session):
        """Test logging a transfer with source and destination locations."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        source_location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        dest_location = Location(
            id=uuid.uuid4(),
            name="Warehouse B",
            type="warehouse"
        )
        db_session.add_all([user, product, source_location, dest_location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Execute
        history_id = logger.log_movement(
            product_id=str(product.id),
            location_id=str(source_location.id),
            quantity_change=-50,
            document_type="transfer",
            document_id="TRF-001",
            user_id=str(user.id),
            source_location_id=str(source_location.id),
            destination_location_id=str(dest_location.id)
        )
        
        # Verify
        history = db_session.query(MoveHistory).filter(
            MoveHistory.id == uuid.UUID(history_id)
        ).first()
        assert history.source_location_id == source_location.id
        assert history.destination_location_id == dest_location.id
    
    def test_log_movement_with_reason(self, db_session: Session):
        """Test logging an adjustment with reason."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Execute
        history_id = logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=10,
            document_type="stock_adjustment",
            document_id="ADJ-001",
            user_id=str(user.id),
            reason="Physical count discrepancy"
        )
        
        # Verify
        history = db_session.query(MoveHistory).filter(
            MoveHistory.id == uuid.UUID(history_id)
        ).first()
        assert history.reason == "Physical count discrepancy"
    
    def test_log_movement_invalid_product_id(self, db_session: Session):
        """Test that invalid product ID raises error."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Execute & Verify
        with pytest.raises(HistoryError) as exc_info:
            logger.log_movement(
                product_id="invalid-id",
                location_id=str(location.id),
                quantity_change=100,
                document_type="receipt",
                document_id="REC-001",
                user_id=str(user.id)
            )
        assert exc_info.value.code == "INVALID_ID"
    
    def test_log_movement_nonexistent_product(self, db_session: Session):
        """Test that nonexistent product raises error."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        fake_product_id = str(uuid.uuid4())
        
        # Execute & Verify
        with pytest.raises(HistoryError) as exc_info:
            logger.log_movement(
                product_id=fake_product_id,
                location_id=str(location.id),
                quantity_change=100,
                document_type="receipt",
                document_id="REC-001",
                user_id=str(user.id)
            )
        assert exc_info.value.code == "PRODUCT_NOT_FOUND"
    
    def test_log_movement_invalid_document_type(self, db_session: Session):
        """Test that invalid document type raises error."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Execute & Verify
        with pytest.raises(HistoryError) as exc_info:
            logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=100,
                document_type="invalid_type",
                document_id="DOC-001",
                user_id=str(user.id)
            )
        assert exc_info.value.code == "INVALID_DOCUMENT_TYPE"


class TestGetMoveHistory:
    """Tests for get_move_history function."""
    
    def test_get_move_history_returns_all_entries(self, db_session: Session):
        """Test that get_move_history returns all entries without filters."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        # Create multiple history entries
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=-50,
            document_type="delivery_order",
            document_id="DEL-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        history = logger.get_move_history()
        
        # Verify
        assert len(history) == 2
        assert history[0]["document_type"] == "delivery_order"  # Most recent first
        assert history[1]["document_type"] == "receipt"
    
    def test_get_move_history_chronological_order(self, db_session: Session):
        """Test that entries are returned in reverse chronological order."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Create entries with slight time differences
        for i in range(5):
            logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=10,
                document_type="receipt",
                document_id=f"REC-{i:03d}",
                user_id=str(user.id)
            )
            db_session.flush()
        db_session.commit()
        
        # Execute
        history = logger.get_move_history()
        
        # Verify - timestamps should be descending
        assert len(history) == 5
        for i in range(len(history) - 1):
            current_time = datetime.fromisoformat(history[i]["timestamp"])
            next_time = datetime.fromisoformat(history[i + 1]["timestamp"])
            assert current_time >= next_time
    
    def test_get_move_history_filter_by_product(self, db_session: Session):
        """Test filtering by product ID."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product1 = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Product 1",
            category="Test",
            unit_of_measure="pcs"
        )
        product2 = Product(
            id=uuid.uuid4(),
            sku="TEST-002",
            name="Product 2",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product1, product2, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product1.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product2.id),
            location_id=str(location.id),
            quantity_change=200,
            document_type="receipt",
            document_id="REC-002",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        history = logger.get_move_history(product_id=str(product1.id))
        
        # Verify
        assert len(history) == 1
        assert history[0]["product_id"] == str(product1.id)
    
    def test_get_move_history_filter_by_location(self, db_session: Session):
        """Test filtering by location ID."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location1 = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse B",
            type="warehouse"
        )
        db_session.add_all([user, product, location1, location2])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location1.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location2.id),
            quantity_change=200,
            document_type="receipt",
            document_id="REC-002",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        history = logger.get_move_history(location_id=str(location2.id))
        
        # Verify
        assert len(history) == 1
        assert history[0]["location_id"] == str(location2.id)
    
    def test_get_move_history_filter_by_document_type(self, db_session: Session):
        """Test filtering by document type."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=-50,
            document_type="delivery_order",
            document_id="DEL-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        history = logger.get_move_history(document_type="receipt")
        
        # Verify
        assert len(history) == 1
        assert history[0]["document_type"] == "receipt"
    
    def test_get_move_history_filter_by_date_range(self, db_session: Session):
        """Test filtering by date range."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Create entry
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute with date range that includes the entry
        now = datetime.utcnow()
        start_date = now - timedelta(hours=1)
        end_date = now + timedelta(hours=1)
        history = logger.get_move_history(start_date=start_date, end_date=end_date)
        
        # Verify
        assert len(history) == 1
        
        # Execute with date range that excludes the entry
        past_start = now - timedelta(days=2)
        past_end = now - timedelta(days=1)
        history = logger.get_move_history(start_date=past_start, end_date=past_end)
        
        # Verify
        assert len(history) == 0


class TestGetStockLedger:
    """Tests for get_stock_ledger function."""
    
    def test_get_stock_ledger_calculates_running_balance(self, db_session: Session):
        """Test that running balance is calculated correctly."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Create movements
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=-30,
            document_type="delivery_order",
            document_id="DEL-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=50,
            document_type="receipt",
            document_id="REC-002",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        ledger = logger.get_stock_ledger()
        
        # Verify
        assert len(ledger) == 3
        assert ledger[0]["running_balance"] == 100
        assert ledger[1]["running_balance"] == 70
        assert ledger[2]["running_balance"] == 120
    
    def test_get_stock_ledger_separate_balances_per_location(self, db_session: Session):
        """Test that running balance is calculated separately per location."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location1 = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        location2 = Location(
            id=uuid.uuid4(),
            name="Warehouse B",
            type="warehouse"
        )
        db_session.add_all([user, product, location1, location2])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        
        # Create movements at different locations
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location1.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location2.id),
            quantity_change=200,
            document_type="receipt",
            document_id="REC-002",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location1.id),
            quantity_change=50,
            document_type="receipt",
            document_id="REC-003",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        ledger = logger.get_stock_ledger()
        
        # Verify - balances should be independent per location
        location1_entries = [e for e in ledger if e["location_id"] == str(location1.id)]
        location2_entries = [e for e in ledger if e["location_id"] == str(location2.id)]
        
        assert len(location1_entries) == 2
        assert location1_entries[0]["running_balance"] == 100
        assert location1_entries[1]["running_balance"] == 150
        
        assert len(location2_entries) == 1
        assert location2_entries[0]["running_balance"] == 200
    
    def test_get_stock_ledger_filter_by_product(self, db_session: Session):
        """Test filtering ledger by product."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product1 = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Product 1",
            category="Test",
            unit_of_measure="pcs"
        )
        product2 = Product(
            id=uuid.uuid4(),
            sku="TEST-002",
            name="Product 2",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product1, product2, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product1.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        logger.log_movement(
            product_id=str(product2.id),
            location_id=str(location.id),
            quantity_change=200,
            document_type="receipt",
            document_id="REC-002",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        ledger = logger.get_stock_ledger(product_id=str(product1.id))
        
        # Verify
        assert len(ledger) == 1
        assert ledger[0]["product_id"] == str(product1.id)


class TestExportLedger:
    """Tests for export_ledger function."""
    
    def test_export_ledger_csv_format(self, db_session: Session):
        """Test exporting ledger in CSV format."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        csv_data = logger.export_ledger(format="csv")
        
        # Verify
        assert csv_data is not None
        assert "id,product_id,location_id" in csv_data
        assert str(product.id) in csv_data
        assert "100" in csv_data
    
    def test_export_ledger_json_format(self, db_session: Session):
        """Test exporting ledger in JSON format."""
        # Setup
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hash",
            name="Test User"
        )
        product = Product(
            id=uuid.uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test",
            unit_of_measure="pcs"
        )
        location = Location(
            id=uuid.uuid4(),
            name="Warehouse A",
            type="warehouse"
        )
        db_session.add_all([user, product, location])
        db_session.commit()
        
        logger = HistoryLogger(db_session)
        logger.log_movement(
            product_id=str(product.id),
            location_id=str(location.id),
            quantity_change=100,
            document_type="receipt",
            document_id="REC-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute
        json_data = logger.export_ledger(format="json")
        
        # Verify
        import json
        parsed = json.loads(json_data)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["quantity_change"] == 100
        assert parsed[0]["running_balance"] == 100
    
    def test_export_ledger_invalid_format(self, db_session: Session):
        """Test that invalid format raises error."""
        logger = HistoryLogger(db_session)
        
        # Execute & Verify
        with pytest.raises(HistoryError) as exc_info:
            logger.export_ledger(format="xml")
        assert exc_info.value.code == "INVALID_FORMAT"
