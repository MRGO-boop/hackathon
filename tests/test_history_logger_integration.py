"""Integration tests for History Logger component."""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from core_inventory.components.history_logger import HistoryLogger
from core_inventory.components.stock_manager import StockManager
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.models.user import User


class TestHistoryLoggerIntegration:
    """Integration tests for History Logger with other components."""
    
    def test_log_movement_within_transaction(self, db_session: Session):
        """Test that log_movement works within a transaction context."""
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
        
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Execute - simulate a receipt validation transaction
        try:
            # Update stock
            stock_manager.update_stock(
                product_id=str(product.id),
                location_id=str(location.id),
                delta=100
            )
            
            # Log movement
            history_logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=100,
                document_type="receipt",
                document_id="REC-001",
                user_id=str(user.id)
            )
            
            # Commit transaction
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        
        # Verify both stock and history were updated
        stock = stock_manager.get_stock(str(product.id), str(location.id))
        assert stock == 100
        
        history = history_logger.get_move_history()
        assert len(history) == 1
        assert history[0]["quantity_change"] == 100
    
    def test_transaction_rollback_prevents_history_logging(self, db_session: Session):
        """Test that rolling back a transaction prevents history from being logged."""
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
        
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Execute - simulate a failed transaction
        try:
            # Update stock
            stock_manager.update_stock(
                product_id=str(product.id),
                location_id=str(location.id),
                delta=100
            )
            
            # Log movement
            history_logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=100,
                document_type="receipt",
                document_id="REC-001",
                user_id=str(user.id)
            )
            
            # Simulate an error and rollback
            raise Exception("Simulated error")
        except Exception:
            db_session.rollback()
        
        # Verify neither stock nor history were updated
        stock = stock_manager.get_stock(str(product.id), str(location.id))
        assert stock == 0
        
        history = history_logger.get_move_history()
        assert len(history) == 0
    
    def test_multiple_movements_create_accurate_ledger(self, db_session: Session):
        """Test that multiple stock movements create an accurate ledger."""
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
        
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Execute - simulate multiple operations
        operations = [
            (100, "receipt", "REC-001"),
            (-30, "delivery_order", "DEL-001"),
            (50, "receipt", "REC-002"),
            (-20, "delivery_order", "DEL-002"),
        ]
        
        for delta, doc_type, doc_id in operations:
            stock_manager.update_stock(
                product_id=str(product.id),
                location_id=str(location.id),
                delta=delta
            )
            history_logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=delta,
                document_type=doc_type,
                document_id=doc_id,
                user_id=str(user.id)
            )
            db_session.commit()
        
        # Verify final stock
        final_stock = stock_manager.get_stock(str(product.id), str(location.id))
        assert final_stock == 100  # 100 - 30 + 50 - 20
        
        # Verify ledger
        ledger = history_logger.get_stock_ledger(
            product_id=str(product.id),
            location_id=str(location.id)
        )
        assert len(ledger) == 4
        assert ledger[0]["running_balance"] == 100
        assert ledger[1]["running_balance"] == 70
        assert ledger[2]["running_balance"] == 120
        assert ledger[3]["running_balance"] == 100
        
        # Verify ledger running balance matches actual stock
        assert ledger[-1]["running_balance"] == final_stock
    
    def test_transfer_creates_two_history_entries(self, db_session: Session):
        """Test that a transfer creates history entries for both locations."""
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
        
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Setup initial stock at source
        stock_manager.update_stock(
            product_id=str(product.id),
            location_id=str(source_location.id),
            delta=100
        )
        history_logger.log_movement(
            product_id=str(product.id),
            location_id=str(source_location.id),
            quantity_change=100,
            document_type="initial_stock",
            document_id="INIT-001",
            user_id=str(user.id)
        )
        db_session.commit()
        
        # Execute transfer
        transfer_quantity = 50
        
        # Decrease at source
        stock_manager.update_stock(
            product_id=str(product.id),
            location_id=str(source_location.id),
            delta=-transfer_quantity
        )
        history_logger.log_movement(
            product_id=str(product.id),
            location_id=str(source_location.id),
            quantity_change=-transfer_quantity,
            document_type="transfer",
            document_id="TRF-001",
            user_id=str(user.id),
            source_location_id=str(source_location.id),
            destination_location_id=str(dest_location.id)
        )
        
        # Increase at destination
        stock_manager.update_stock(
            product_id=str(product.id),
            location_id=str(dest_location.id),
            delta=transfer_quantity
        )
        history_logger.log_movement(
            product_id=str(product.id),
            location_id=str(dest_location.id),
            quantity_change=transfer_quantity,
            document_type="transfer",
            document_id="TRF-001",
            user_id=str(user.id),
            source_location_id=str(source_location.id),
            destination_location_id=str(dest_location.id)
        )
        db_session.commit()
        
        # Verify stock at both locations
        source_stock = stock_manager.get_stock(str(product.id), str(source_location.id))
        dest_stock = stock_manager.get_stock(str(product.id), str(dest_location.id))
        assert source_stock == 50
        assert dest_stock == 50
        
        # Verify history entries
        history = history_logger.get_move_history(document_type="transfer")
        assert len(history) == 2
        
        # Verify both entries reference the same transfer document
        assert history[0]["document_id"] == "TRF-001"
        assert history[1]["document_id"] == "TRF-001"
        
        # Verify source and destination are recorded
        assert history[0]["source_location_id"] == str(source_location.id)
        assert history[0]["destination_location_id"] == str(dest_location.id)
    
    def test_ledger_export_matches_actual_stock(self, db_session: Session):
        """Test that exported ledger data matches actual stock levels."""
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
        
        stock_manager = StockManager(db_session)
        history_logger = HistoryLogger(db_session)
        
        # Execute operations
        operations = [
            (100, "receipt", "REC-001"),
            (-25, "delivery_order", "DEL-001"),
            (75, "receipt", "REC-002"),
        ]
        
        for delta, doc_type, doc_id in operations:
            stock_manager.update_stock(
                product_id=str(product.id),
                location_id=str(location.id),
                delta=delta
            )
            history_logger.log_movement(
                product_id=str(product.id),
                location_id=str(location.id),
                quantity_change=delta,
                document_type=doc_type,
                document_id=doc_id,
                user_id=str(user.id)
            )
            db_session.commit()
        
        # Export ledger
        import json
        json_export = history_logger.export_ledger(
            format="json",
            product_id=str(product.id),
            location_id=str(location.id)
        )
        ledger_data = json.loads(json_export)
        
        # Verify
        final_stock = stock_manager.get_stock(str(product.id), str(location.id))
        assert ledger_data[-1]["running_balance"] == final_stock
        assert final_stock == 150  # 100 - 25 + 75
