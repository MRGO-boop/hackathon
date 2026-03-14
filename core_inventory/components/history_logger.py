"""History Logger component for tracking stock movements and maintaining audit trail."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from core_inventory.models.move_history import MoveHistory, DocumentType
from core_inventory.models.stock_ledger import StockLedger
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.models.user import User


class HistoryError(Exception):
    """Base exception for history logging errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class HistoryLogger:
    """Handles recording and retrieval of stock movement history."""
    
    def __init__(self, db: Session):
        """Initialize history logger with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def log_movement(
        self,
        product_id: str,
        location_id: str,
        quantity_change: int,
        document_type: str,
        document_id: str,
        user_id: str,
        source_location_id: Optional[str] = None,
        destination_location_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> str:
        """Create a Move_History entry for a stock movement.
        
        This method is designed to be called within a database transaction.
        
        Args:
            product_id: Product ID
            location_id: Location ID where the movement occurred
            quantity_change: Change in quantity (positive for increase, negative for decrease)
            document_type: Type of document (receipt, delivery_order, transfer, stock_adjustment, initial_stock)
            document_id: Reference to the source document
            user_id: User who performed the action
            source_location_id: Optional source location (for transfers)
            destination_location_id: Optional destination location (for transfers)
            reason: Optional reason (for adjustments)
            
        Returns:
            str: ID of the created Move_History entry
            
        Raises:
            HistoryError: If validation fails
        """
        # Parse and validate IDs
        try:
            product_uuid = uuid.UUID(product_id)
            location_uuid = uuid.UUID(location_id)
            user_uuid = uuid.UUID(user_id)
            source_uuid = uuid.UUID(source_location_id) if source_location_id else None
            dest_uuid = uuid.UUID(destination_location_id) if destination_location_id else None
        except (ValueError, AttributeError) as e:
            raise HistoryError(
                "Invalid ID format",
                "INVALID_ID",
                {
                    "product_id": product_id,
                    "location_id": location_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
        
        # Validate document type
        try:
            doc_type_enum = DocumentType[document_type]
        except KeyError:
            raise HistoryError(
                f"Invalid document type: {document_type}",
                "INVALID_DOCUMENT_TYPE",
                {"document_type": document_type}
            )
        
        # Verify entities exist
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise HistoryError(
                "Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise HistoryError(
                "Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        user = self.db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HistoryError(
                "User not found",
                "USER_NOT_FOUND",
                {"user_id": user_id}
            )
        
        # Create move history entry
        move_history = MoveHistory(
            id=uuid.uuid4(),
            product_id=product_uuid,
            location_id=location_uuid,
            quantity_change=quantity_change,
            document_type=doc_type_enum,
            document_id=document_id,
            source_location_id=source_uuid,
            destination_location_id=dest_uuid,
            reason=reason,
            user_id=user_uuid
        )
        
        self.db.add(move_history)
        self.db.flush()
        
        return str(move_history.id)

    
    def get_move_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        product_id: Optional[str] = None,
        location_id: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get move history with optional filtering.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            product_id: Optional product ID filter
            location_id: Optional location ID filter
            document_type: Optional document type filter
            
        Returns:
            List[Dict]: List of move history entries in reverse chronological order
            
        Raises:
            HistoryError: If validation fails
        """
        # Start with base query
        query = self.db.query(MoveHistory)
        
        # Apply filters
        if start_date:
            query = query.filter(MoveHistory.timestamp >= start_date)
        
        if end_date:
            query = query.filter(MoveHistory.timestamp <= end_date)
        
        if product_id:
            try:
                product_uuid = uuid.UUID(product_id)
                query = query.filter(MoveHistory.product_id == product_uuid)
            except (ValueError, AttributeError):
                raise HistoryError(
                    "Invalid product ID format",
                    "INVALID_PRODUCT_ID",
                    {"product_id": product_id}
                )
        
        if location_id:
            try:
                location_uuid = uuid.UUID(location_id)
                query = query.filter(MoveHistory.location_id == location_uuid)
            except (ValueError, AttributeError):
                raise HistoryError(
                    "Invalid location ID format",
                    "INVALID_LOCATION_ID",
                    {"location_id": location_id}
                )
        
        if document_type:
            try:
                doc_type_enum = DocumentType[document_type]
                query = query.filter(MoveHistory.document_type == doc_type_enum)
            except KeyError:
                raise HistoryError(
                    f"Invalid document type: {document_type}",
                    "INVALID_DOCUMENT_TYPE",
                    {"document_type": document_type}
                )
        
        # Order by timestamp descending (reverse chronological)
        query = query.order_by(desc(MoveHistory.timestamp))
        
        # Execute query
        results = query.all()
        
        # Convert to dictionaries
        history_entries = []
        for entry in results:
            history_entries.append({
                "id": str(entry.id),
                "product_id": str(entry.product_id),
                "location_id": str(entry.location_id),
                "quantity_change": entry.quantity_change,
                "document_type": entry.document_type.value,
                "document_id": entry.document_id,
                "source_location_id": str(entry.source_location_id) if entry.source_location_id else None,
                "destination_location_id": str(entry.destination_location_id) if entry.destination_location_id else None,
                "reason": entry.reason,
                "user_id": str(entry.user_id),
                "timestamp": entry.timestamp.isoformat()
            })
        
        return history_entries

    
    def get_stock_ledger(
        self,
        product_id: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get stock ledger with running balance calculation.
        
        The stock ledger is computed from Move_History entries with running balance
        calculated for each product-location combination.
        
        Args:
            product_id: Optional product ID filter
            location_id: Optional location ID filter
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List[Dict]: List of ledger entries with running balance in chronological order
            
        Raises:
            HistoryError: If validation fails
        """
        # Start with base query
        query = self.db.query(MoveHistory)
        
        # Apply filters
        if product_id:
            try:
                product_uuid = uuid.UUID(product_id)
                query = query.filter(MoveHistory.product_id == product_uuid)
            except (ValueError, AttributeError):
                raise HistoryError(
                    "Invalid product ID format",
                    "INVALID_PRODUCT_ID",
                    {"product_id": product_id}
                )
        
        if location_id:
            try:
                location_uuid = uuid.UUID(location_id)
                query = query.filter(MoveHistory.location_id == location_uuid)
            except (ValueError, AttributeError):
                raise HistoryError(
                    "Invalid location ID format",
                    "INVALID_LOCATION_ID",
                    {"location_id": location_id}
                )
        
        if start_date:
            query = query.filter(MoveHistory.timestamp >= start_date)
        
        if end_date:
            query = query.filter(MoveHistory.timestamp <= end_date)
        
        # Order by timestamp ascending for running balance calculation
        query = query.order_by(MoveHistory.timestamp.asc())
        
        # Execute query
        results = query.all()
        
        # Calculate running balance per product-location combination
        balances: Dict[tuple, int] = {}  # (product_id, location_id) -> running_balance
        ledger_entries = []
        
        for entry in results:
            key = (str(entry.product_id), str(entry.location_id))
            
            # Update running balance
            if key not in balances:
                balances[key] = 0
            balances[key] += entry.quantity_change
            
            # Create ledger entry
            ledger_entries.append({
                "id": str(entry.id),
                "product_id": str(entry.product_id),
                "location_id": str(entry.location_id),
                "quantity_change": entry.quantity_change,
                "running_balance": balances[key],
                "document_type": entry.document_type.value,
                "document_id": entry.document_id,
                "user_id": str(entry.user_id),
                "timestamp": entry.timestamp.isoformat()
            })
        
        return ledger_entries
    
    def export_ledger(
        self,
        format: str = "csv",
        product_id: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export stock ledger data for external analysis.
        
        Args:
            format: Export format (csv or json)
            product_id: Optional product ID filter
            location_id: Optional location ID filter
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            str: Exported data as string in the specified format
            
        Raises:
            HistoryError: If format is invalid or validation fails
        """
        # Get ledger data
        ledger_entries = self.get_stock_ledger(
            product_id=product_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "csv":
            # Generate CSV format
            import csv
            from io import StringIO
            
            output = StringIO()
            if ledger_entries:
                fieldnames = ledger_entries[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ledger_entries)
            
            return output.getvalue()
        
        elif format == "json":
            # Generate JSON format
            import json
            return json.dumps(ledger_entries, indent=2)
        
        else:
            raise HistoryError(
                f"Unsupported export format: {format}",
                "INVALID_FORMAT",
                {"format": format, "supported_formats": ["csv", "json"]}
            )
