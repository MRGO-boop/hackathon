"""Validator component for validating documents and updating stock atomically."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from core_inventory.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.models.stock_adjustment import StockAdjustment, StockAdjustmentStatus
from core_inventory.components.stock_manager import StockManager, StockError
from core_inventory.components.history_logger import HistoryLogger, HistoryError


class ValidationError(Exception):
    """Base exception for validation errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class Validator:
    """Handles document validation and coordinates stock updates with history logging."""
    
    def __init__(self, db: Session):
        """Initialize validator with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.stock_manager = StockManager(db)
        self.history_logger = HistoryLogger(db)

    
    def validate_receipt(self, receipt_id: str, user_id: str) -> None:
        """Validate a receipt and update stock atomically.
        
        This function:
        1. Checks that the receipt exists and is in pending status
        2. Increases stock for each item by the received quantity
        3. Creates Move_History entries for each item
        4. Updates receipt status to validated
        5. Is idempotent - validating an already-validated receipt returns success
        
        All operations are performed within a database transaction for atomicity.
        
        Args:
            receipt_id: Receipt ID to validate
            user_id: User performing the validation
            
        Raises:
            ValidationError: If validation fails
        """
        # Parse IDs
        try:
            receipt_uuid = uuid.UUID(receipt_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise ValidationError(
                "Invalid receipt or user ID format",
                "INVALID_ID",
                {"receipt_id": receipt_id, "user_id": user_id}
            )
        
        try:
            # Get receipt
            receipt = self.db.query(Receipt).filter(Receipt.id == receipt_uuid).first()
            if not receipt:
                raise ValidationError(
                    "Receipt not found",
                    "RECEIPT_NOT_FOUND",
                    {"receipt_id": receipt_id}
                )
            
            # Idempotency check - if already validated, return success
            if receipt.status == ReceiptStatus.validated:
                return
            
            # Check status is pending
            if receipt.status != ReceiptStatus.pending:
                raise ValidationError(
                    f"Cannot validate receipt with status {receipt.status.value}",
                    "INVALID_STATUS",
                    {"receipt_id": receipt_id, "status": receipt.status.value}
                )
            
            # Get receipt items
            receipt_items = self.db.query(ReceiptItem).filter(
                ReceiptItem.receipt_id == receipt_uuid
            ).all()
            
            if not receipt_items:
                raise ValidationError(
                    "Receipt has no items",
                    "NO_ITEMS",
                    {"receipt_id": receipt_id}
                )
            
            # Process each item
            for item in receipt_items:
                # Update stock
                self.stock_manager.update_stock(
                    product_id=str(item.product_id),
                    location_id=str(item.location_id),
                    delta=item.received_quantity
                )
                
                # Log movement
                self.history_logger.log_movement(
                    product_id=str(item.product_id),
                    location_id=str(item.location_id),
                    quantity_change=item.received_quantity,
                    document_type="receipt",
                    document_id=receipt_id,
                    user_id=user_id
                )
            
            # Update receipt status
            receipt.status = ReceiptStatus.validated
            receipt.validated_by = user_uuid
            receipt.validated_at = datetime.utcnow()
            
            # Commit transaction
            self.db.commit()
            
        except (StockError, HistoryError) as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to validate receipt: {e.message}",
                e.code,
                {"receipt_id": receipt_id, "original_error": e.message}
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValidationError(
                f"Database error during receipt validation: {str(e)}",
                "DATABASE_ERROR",
                {"receipt_id": receipt_id}
            )

    
    def validate_delivery_order(self, order_id: str, user_id: str) -> None:
        """Validate a delivery order and update stock atomically.
        
        This function:
        1. Checks that the delivery order exists and is in pending/picking/packing status
        2. Checks stock availability for all items before validation
        3. Decreases stock for each item by the delivered quantity
        4. Creates Move_History entries for each item
        5. Updates delivery order status to validated
        
        All operations are performed within a database transaction for atomicity.
        
        Args:
            order_id: Delivery order ID to validate
            user_id: User performing the validation
            
        Raises:
            ValidationError: If validation fails or insufficient stock
        """
        # Parse IDs
        try:
            order_uuid = uuid.UUID(order_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise ValidationError(
                "Invalid order or user ID format",
                "INVALID_ID",
                {"order_id": order_id, "user_id": user_id}
            )
        
        try:
            # Get delivery order
            order = self.db.query(DeliveryOrder).filter(DeliveryOrder.id == order_uuid).first()
            if not order:
                raise ValidationError(
                    "Delivery order not found",
                    "DELIVERY_ORDER_NOT_FOUND",
                    {"order_id": order_id}
                )
            
            # Check status is not already validated
            if order.status == DeliveryOrderStatus.validated:
                raise ValidationError(
                    "Delivery order is already validated",
                    "ALREADY_VALIDATED",
                    {"order_id": order_id}
                )
            
            # Get delivery order items
            order_items = self.db.query(DeliveryOrderItem).filter(
                DeliveryOrderItem.delivery_order_id == order_uuid
            ).all()
            
            if not order_items:
                raise ValidationError(
                    "Delivery order has no items",
                    "NO_ITEMS",
                    {"order_id": order_id}
                )
            
            # Check stock availability for all items first
            for item in order_items:
                available = self.stock_manager.check_availability(
                    product_id=str(item.product_id),
                    location_id=str(item.location_id),
                    required=item.delivered_quantity
                )
                
                if not available:
                    current_stock = self.stock_manager.get_stock(
                        product_id=str(item.product_id),
                        location_id=str(item.location_id)
                    )
                    raise ValidationError(
                        f"Insufficient stock for delivery order",
                        "INSUFFICIENT_STOCK",
                        {
                            "order_id": order_id,
                            "product_id": str(item.product_id),
                            "location_id": str(item.location_id),
                            "required": item.delivered_quantity,
                            "available": current_stock
                        }
                    )
            
            # Process each item
            for item in order_items:
                # Update stock (decrease)
                self.stock_manager.update_stock(
                    product_id=str(item.product_id),
                    location_id=str(item.location_id),
                    delta=-item.delivered_quantity
                )
                
                # Log movement
                self.history_logger.log_movement(
                    product_id=str(item.product_id),
                    location_id=str(item.location_id),
                    quantity_change=-item.delivered_quantity,
                    document_type="delivery_order",
                    document_id=order_id,
                    user_id=user_id
                )
            
            # Update delivery order status
            order.status = DeliveryOrderStatus.validated
            order.validated_by = user_uuid
            order.validated_at = datetime.utcnow()
            
            # Commit transaction
            self.db.commit()
            
        except (StockError, HistoryError) as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to validate delivery order: {e.message}",
                e.code,
                {"order_id": order_id, "original_error": e.message}
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValidationError(
                f"Database error during delivery order validation: {str(e)}",
                "DATABASE_ERROR",
                {"order_id": order_id}
            )

    
    def validate_transfer(self, transfer_id: str, user_id: str) -> None:
        """Validate a transfer and update stock atomically.
        
        This function:
        1. Checks that the transfer exists and is in pending status
        2. Validates sufficient stock at source location
        3. Decreases stock at source location
        4. Increases stock at destination location
        5. Creates Move_History entry with both locations
        6. Updates transfer status to validated
        
        All operations are performed within a database transaction for atomicity.
        
        Args:
            transfer_id: Transfer ID to validate
            user_id: User performing the validation
            
        Raises:
            ValidationError: If validation fails or insufficient stock at source
        """
        # Parse IDs
        try:
            transfer_uuid = uuid.UUID(transfer_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise ValidationError(
                "Invalid transfer or user ID format",
                "INVALID_ID",
                {"transfer_id": transfer_id, "user_id": user_id}
            )
        
        try:
            # Get transfer
            transfer = self.db.query(Transfer).filter(Transfer.id == transfer_uuid).first()
            if not transfer:
                raise ValidationError(
                    "Transfer not found",
                    "TRANSFER_NOT_FOUND",
                    {"transfer_id": transfer_id}
                )
            
            # Check status is pending
            if transfer.status == TransferStatus.validated:
                raise ValidationError(
                    "Transfer is already validated",
                    "ALREADY_VALIDATED",
                    {"transfer_id": transfer_id}
                )
            
            if transfer.status != TransferStatus.pending:
                raise ValidationError(
                    f"Cannot validate transfer with status {transfer.status.value}",
                    "INVALID_STATUS",
                    {"transfer_id": transfer_id, "status": transfer.status.value}
                )
            
            # Check stock availability at source location
            available = self.stock_manager.check_availability(
                product_id=str(transfer.product_id),
                location_id=str(transfer.source_location_id),
                required=transfer.quantity
            )
            
            if not available:
                current_stock = self.stock_manager.get_stock(
                    product_id=str(transfer.product_id),
                    location_id=str(transfer.source_location_id)
                )
                raise ValidationError(
                    f"Insufficient stock at source location for transfer",
                    "INSUFFICIENT_STOCK",
                    {
                        "transfer_id": transfer_id,
                        "product_id": str(transfer.product_id),
                        "source_location_id": str(transfer.source_location_id),
                        "required": transfer.quantity,
                        "available": current_stock
                    }
                )
            
            # Decrease stock at source location
            self.stock_manager.update_stock(
                product_id=str(transfer.product_id),
                location_id=str(transfer.source_location_id),
                delta=-transfer.quantity
            )
            
            # Increase stock at destination location
            self.stock_manager.update_stock(
                product_id=str(transfer.product_id),
                location_id=str(transfer.destination_location_id),
                delta=transfer.quantity
            )
            
            # Log movement at source location (decrease)
            self.history_logger.log_movement(
                product_id=str(transfer.product_id),
                location_id=str(transfer.source_location_id),
                quantity_change=-transfer.quantity,
                document_type="transfer",
                document_id=transfer_id,
                user_id=user_id,
                source_location_id=str(transfer.source_location_id),
                destination_location_id=str(transfer.destination_location_id)
            )
            
            # Log movement at destination location (increase)
            self.history_logger.log_movement(
                product_id=str(transfer.product_id),
                location_id=str(transfer.destination_location_id),
                quantity_change=transfer.quantity,
                document_type="transfer",
                document_id=transfer_id,
                user_id=user_id,
                source_location_id=str(transfer.source_location_id),
                destination_location_id=str(transfer.destination_location_id)
            )
            
            # Update transfer status
            transfer.status = TransferStatus.validated
            transfer.validated_by = user_uuid
            transfer.validated_at = datetime.utcnow()
            
            # Commit transaction
            self.db.commit()
            
        except (StockError, HistoryError) as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to validate transfer: {e.message}",
                e.code,
                {"transfer_id": transfer_id, "original_error": e.message}
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValidationError(
                f"Database error during transfer validation: {str(e)}",
                "DATABASE_ERROR",
                {"transfer_id": transfer_id}
            )

    
    def validate_stock_adjustment(self, adjustment_id: str, user_id: str) -> None:
        """Validate a stock adjustment and update stock atomically.
        
        This function:
        1. Checks that the stock adjustment exists and is in pending status
        2. Sets stock to the physical_quantity value
        3. Creates Move_History entry with the adjustment reason
        4. Updates stock adjustment status to validated
        
        All operations are performed within a database transaction for atomicity.
        
        Args:
            adjustment_id: Stock adjustment ID to validate
            user_id: User performing the validation
            
        Raises:
            ValidationError: If validation fails
        """
        # Parse IDs
        try:
            adjustment_uuid = uuid.UUID(adjustment_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise ValidationError(
                "Invalid adjustment or user ID format",
                "INVALID_ID",
                {"adjustment_id": adjustment_id, "user_id": user_id}
            )
        
        try:
            # Get stock adjustment
            adjustment = self.db.query(StockAdjustment).filter(
                StockAdjustment.id == adjustment_uuid
            ).first()
            
            if not adjustment:
                raise ValidationError(
                    "Stock adjustment not found",
                    "STOCK_ADJUSTMENT_NOT_FOUND",
                    {"adjustment_id": adjustment_id}
                )
            
            # Check status is pending
            if adjustment.status == StockAdjustmentStatus.validated:
                raise ValidationError(
                    "Stock adjustment is already validated",
                    "ALREADY_VALIDATED",
                    {"adjustment_id": adjustment_id}
                )
            
            if adjustment.status != StockAdjustmentStatus.pending:
                raise ValidationError(
                    f"Cannot validate stock adjustment with status {adjustment.status.value}",
                    "INVALID_STATUS",
                    {"adjustment_id": adjustment_id, "status": adjustment.status.value}
                )
            
            # Get current stock
            current_stock = self.stock_manager.get_stock(
                product_id=str(adjustment.product_id),
                location_id=str(adjustment.location_id)
            )
            
            # Calculate the delta needed to reach physical_quantity
            delta = adjustment.physical_quantity - current_stock
            
            # Update stock to physical_quantity
            if delta != 0:
                self.stock_manager.update_stock(
                    product_id=str(adjustment.product_id),
                    location_id=str(adjustment.location_id),
                    delta=delta
                )
            
            # Log movement with reason
            self.history_logger.log_movement(
                product_id=str(adjustment.product_id),
                location_id=str(adjustment.location_id),
                quantity_change=delta,
                document_type="stock_adjustment",
                document_id=adjustment_id,
                user_id=user_id,
                reason=adjustment.reason
            )
            
            # Update stock adjustment status
            adjustment.status = StockAdjustmentStatus.validated
            adjustment.validated_by = user_uuid
            adjustment.validated_at = datetime.utcnow()
            
            # Commit transaction
            self.db.commit()
            
        except (StockError, HistoryError) as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to validate stock adjustment: {e.message}",
                e.code,
                {"adjustment_id": adjustment_id, "original_error": e.message}
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValidationError(
                f"Database error during stock adjustment validation: {str(e)}",
                "DATABASE_ERROR",
                {"adjustment_id": adjustment_id}
            )
