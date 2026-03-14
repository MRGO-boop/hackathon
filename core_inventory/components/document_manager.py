"""Document Manager component for document operations."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core_inventory.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.models.stock_adjustment import StockAdjustment, StockAdjustmentStatus
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.components.stock_manager import StockManager


class DocumentError(Exception):
    """Base exception for document management errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class DocumentManager:
    """Handles document creation and retrieval operations."""
    
    def __init__(self, db: Session):
        """Initialize document manager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.stock_manager = StockManager(db)

    
    def create_receipt(
        self,
        supplier_name: str,
        created_by: str,
        items: List[Dict[str, Any]],
        supplier_contact: Optional[str] = None
    ) -> Receipt:
        """Create a new receipt document with pending status.
        
        Args:
            supplier_name: Name of the supplier
            created_by: User ID creating the receipt
            items: List of items with product_id, location_id, expected_quantity, received_quantity
            supplier_contact: Optional supplier contact information
            
        Returns:
            Receipt: The newly created receipt
            
        Raises:
            DocumentError: If validation fails
        """
        # Validate input
        if not supplier_name or not supplier_name.strip():
            raise DocumentError(
                "Supplier name is required",
                "INVALID_SUPPLIER_NAME",
                {"field": "supplier_name"}
            )
        
        if not items or len(items) == 0:
            raise DocumentError(
                "Receipt must have at least one item",
                "NO_ITEMS",
                {"field": "items"}
            )
        
        # Parse created_by ID
        try:
            created_by_uuid = uuid.UUID(created_by)
        except (ValueError, AttributeError):
            raise DocumentError(
                "Invalid user ID format",
                "INVALID_USER_ID",
                {"created_by": created_by}
            )
        
        # Create receipt
        receipt = Receipt(
            id=uuid.uuid4(),
            supplier_name=supplier_name.strip(),
            supplier_contact=supplier_contact.strip() if supplier_contact else None,
            status=ReceiptStatus.pending,
            created_by=created_by_uuid
        )
        
        self.db.add(receipt)
        self.db.flush()
        
        # Create receipt items
        for item in items:
            # Validate item fields
            if 'product_id' not in item or 'location_id' not in item:
                raise DocumentError(
                    "Each item must have product_id and location_id",
                    "INVALID_ITEM",
                    {"item": item}
                )
            
            if 'expected_quantity' not in item or 'received_quantity' not in item:
                raise DocumentError(
                    "Each item must have expected_quantity and received_quantity",
                    "INVALID_ITEM",
                    {"item": item}
                )
            
            # Parse IDs
            try:
                product_uuid = uuid.UUID(item['product_id'])
                location_uuid = uuid.UUID(item['location_id'])
            except (ValueError, AttributeError):
                raise DocumentError(
                    "Invalid product or location ID format",
                    "INVALID_ID",
                    {"item": item}
                )
            
            # Validate quantities
            expected_qty = item['expected_quantity']
            received_qty = item['received_quantity']
            
            if not isinstance(expected_qty, int) or expected_qty <= 0:
                raise DocumentError(
                    "Expected quantity must be a positive integer",
                    "INVALID_QUANTITY",
                    {"expected_quantity": expected_qty}
                )
            
            if not isinstance(received_qty, int) or received_qty < 0:
                raise DocumentError(
                    "Received quantity must be a non-negative integer",
                    "INVALID_QUANTITY",
                    {"received_quantity": received_qty}
                )
            
            # Verify product exists
            product = self.db.query(Product).filter(Product.id == product_uuid).first()
            if not product:
                raise DocumentError(
                    "Product not found",
                    "PRODUCT_NOT_FOUND",
                    {"product_id": item['product_id']}
                )
            
            # Verify location exists
            location = self.db.query(Location).filter(Location.id == location_uuid).first()
            if not location:
                raise DocumentError(
                    "Location not found",
                    "LOCATION_NOT_FOUND",
                    {"location_id": item['location_id']}
                )
            
            # Create receipt item
            receipt_item = ReceiptItem(
                id=uuid.uuid4(),
                receipt_id=receipt.id,
                product_id=product_uuid,
                location_id=location_uuid,
                expected_quantity=expected_qty,
                received_quantity=received_qty
            )
            
            self.db.add(receipt_item)
        
        self.db.commit()
        self.db.refresh(receipt)
        
        return receipt

    
    def create_delivery_order(
        self,
        customer_name: str,
        created_by: str,
        items: List[Dict[str, Any]],
        customer_contact: Optional[str] = None
    ) -> DeliveryOrder:
        """Create a new delivery order document with pending status.
        
        Args:
            customer_name: Name of the customer
            created_by: User ID creating the delivery order
            items: List of items with product_id, location_id, requested_quantity, delivered_quantity
            customer_contact: Optional customer contact information
            
        Returns:
            DeliveryOrder: The newly created delivery order
            
        Raises:
            DocumentError: If validation fails
        """
        # Validate input
        if not customer_name or not customer_name.strip():
            raise DocumentError(
                "Customer name is required",
                "INVALID_CUSTOMER_NAME",
                {"field": "customer_name"}
            )
        
        if not items or len(items) == 0:
            raise DocumentError(
                "Delivery order must have at least one item",
                "NO_ITEMS",
                {"field": "items"}
            )
        
        # Parse created_by ID
        try:
            created_by_uuid = uuid.UUID(created_by)
        except (ValueError, AttributeError):
            raise DocumentError(
                "Invalid user ID format",
                "INVALID_USER_ID",
                {"created_by": created_by}
            )
        
        # Create delivery order
        delivery_order = DeliveryOrder(
            id=uuid.uuid4(),
            customer_name=customer_name.strip(),
            customer_contact=customer_contact.strip() if customer_contact else None,
            status=DeliveryOrderStatus.pending,
            created_by=created_by_uuid
        )
        
        self.db.add(delivery_order)
        self.db.flush()
        
        # Create delivery order items
        for item in items:
            # Validate item fields
            if 'product_id' not in item or 'location_id' not in item:
                raise DocumentError(
                    "Each item must have product_id and location_id",
                    "INVALID_ITEM",
                    {"item": item}
                )
            
            if 'requested_quantity' not in item or 'delivered_quantity' not in item:
                raise DocumentError(
                    "Each item must have requested_quantity and delivered_quantity",
                    "INVALID_ITEM",
                    {"item": item}
                )
            
            # Parse IDs
            try:
                product_uuid = uuid.UUID(item['product_id'])
                location_uuid = uuid.UUID(item['location_id'])
            except (ValueError, AttributeError):
                raise DocumentError(
                    "Invalid product or location ID format",
                    "INVALID_ID",
                    {"item": item}
                )
            
            # Validate quantities
            requested_qty = item['requested_quantity']
            delivered_qty = item['delivered_quantity']
            
            if not isinstance(requested_qty, int) or requested_qty <= 0:
                raise DocumentError(
                    "Requested quantity must be a positive integer",
                    "INVALID_QUANTITY",
                    {"requested_quantity": requested_qty}
                )
            
            if not isinstance(delivered_qty, int) or delivered_qty < 0:
                raise DocumentError(
                    "Delivered quantity must be a non-negative integer",
                    "INVALID_QUANTITY",
                    {"delivered_quantity": delivered_qty}
                )
            
            # Verify product exists
            product = self.db.query(Product).filter(Product.id == product_uuid).first()
            if not product:
                raise DocumentError(
                    "Product not found",
                    "PRODUCT_NOT_FOUND",
                    {"product_id": item['product_id']}
                )
            
            # Verify location exists
            location = self.db.query(Location).filter(Location.id == location_uuid).first()
            if not location:
                raise DocumentError(
                    "Location not found",
                    "LOCATION_NOT_FOUND",
                    {"location_id": item['location_id']}
                )
            
            # Create delivery order item
            delivery_order_item = DeliveryOrderItem(
                id=uuid.uuid4(),
                delivery_order_id=delivery_order.id,
                product_id=product_uuid,
                location_id=location_uuid,
                requested_quantity=requested_qty,
                delivered_quantity=delivered_qty
            )
            
            self.db.add(delivery_order_item)
        
        self.db.commit()
        self.db.refresh(delivery_order)
        
        return delivery_order

    
    def create_transfer(
        self,
        source_location_id: str,
        destination_location_id: str,
        product_id: str,
        quantity: int,
        created_by: str
    ) -> Transfer:
        """Create a new transfer document with source stock validation.
        
        Args:
            source_location_id: Source location ID
            destination_location_id: Destination location ID
            product_id: Product ID
            quantity: Quantity to transfer
            created_by: User ID creating the transfer
            
        Returns:
            Transfer: The newly created transfer
            
        Raises:
            DocumentError: If validation fails or insufficient stock at source
        """
        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            raise DocumentError(
                "Quantity must be a positive integer",
                "INVALID_QUANTITY",
                {"quantity": quantity}
            )
        
        # Parse IDs
        try:
            source_uuid = uuid.UUID(source_location_id)
            dest_uuid = uuid.UUID(destination_location_id)
            product_uuid = uuid.UUID(product_id)
            created_by_uuid = uuid.UUID(created_by)
        except (ValueError, AttributeError):
            raise DocumentError(
                "Invalid ID format",
                "INVALID_ID",
                {
                    "source_location_id": source_location_id,
                    "destination_location_id": destination_location_id,
                    "product_id": product_id,
                    "created_by": created_by
                }
            )
        
        # Validate source and destination are different
        if source_location_id == destination_location_id:
            raise DocumentError(
                "Source and destination locations must be different",
                "SAME_LOCATION",
                {
                    "source_location_id": source_location_id,
                    "destination_location_id": destination_location_id
                }
            )
        
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise DocumentError(
                "Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        # Verify source location exists
        source_location = self.db.query(Location).filter(Location.id == source_uuid).first()
        if not source_location:
            raise DocumentError(
                "Source location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": source_location_id}
            )
        
        # Verify destination location exists
        dest_location = self.db.query(Location).filter(Location.id == dest_uuid).first()
        if not dest_location:
            raise DocumentError(
                "Destination location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": destination_location_id}
            )
        
        # Validate source stock availability
        if not self.stock_manager.check_availability(product_id, source_location_id, quantity):
            current_stock = self.stock_manager.get_stock(product_id, source_location_id)
            raise DocumentError(
                f"Insufficient stock at source location: required {quantity}, available {current_stock}",
                "INSUFFICIENT_STOCK",
                {
                    "product_id": product_id,
                    "source_location_id": source_location_id,
                    "required": quantity,
                    "available": current_stock
                }
            )
        
        # Create transfer
        transfer = Transfer(
            id=uuid.uuid4(),
            source_location_id=source_uuid,
            destination_location_id=dest_uuid,
            product_id=product_uuid,
            quantity=quantity,
            status=TransferStatus.pending,
            created_by=created_by_uuid
        )
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer

    
    def create_stock_adjustment(
        self,
        product_id: str,
        location_id: str,
        recorded_quantity: int,
        physical_quantity: int,
        reason: str,
        created_by: str
    ) -> StockAdjustment:
        """Create a new stock adjustment document with required reason field.
        
        Args:
            product_id: Product ID
            location_id: Location ID
            recorded_quantity: Recorded quantity in system
            physical_quantity: Physical count quantity
            reason: Reason for adjustment (required)
            created_by: User ID creating the adjustment
            
        Returns:
            StockAdjustment: The newly created stock adjustment
            
        Raises:
            DocumentError: If validation fails or reason is missing
        """
        # Validate reason is required
        if not reason or not reason.strip():
            raise DocumentError(
                "Reason is required for stock adjustments",
                "REASON_REQUIRED",
                {"field": "reason"}
            )
        
        # Validate quantities
        if not isinstance(recorded_quantity, int) or recorded_quantity < 0:
            raise DocumentError(
                "Recorded quantity must be a non-negative integer",
                "INVALID_QUANTITY",
                {"recorded_quantity": recorded_quantity}
            )
        
        if not isinstance(physical_quantity, int) or physical_quantity < 0:
            raise DocumentError(
                "Physical quantity must be a non-negative integer",
                "INVALID_QUANTITY",
                {"physical_quantity": physical_quantity}
            )
        
        # Parse IDs
        try:
            product_uuid = uuid.UUID(product_id)
            location_uuid = uuid.UUID(location_id)
            created_by_uuid = uuid.UUID(created_by)
        except (ValueError, AttributeError):
            raise DocumentError(
                "Invalid ID format",
                "INVALID_ID",
                {
                    "product_id": product_id,
                    "location_id": location_id,
                    "created_by": created_by
                }
            )
        
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise DocumentError(
                "Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        # Verify location exists
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise DocumentError(
                "Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        # Calculate adjustment difference (physical - recorded)
        adjustment_difference = physical_quantity - recorded_quantity
        
        # Create stock adjustment
        stock_adjustment = StockAdjustment(
            id=uuid.uuid4(),
            product_id=product_uuid,
            location_id=location_uuid,
            recorded_quantity=recorded_quantity,
            physical_quantity=physical_quantity,
            adjustment_difference=adjustment_difference,
            reason=reason.strip(),
            status=StockAdjustmentStatus.pending,
            created_by=created_by_uuid
        )
        
        self.db.add(stock_adjustment)
        self.db.commit()
        self.db.refresh(stock_adjustment)
        
        return stock_adjustment

    
    def get_document(self, document_id: str, document_type: str) -> Any:
        """Get a document by ID and type.
        
        Args:
            document_id: Document ID
            document_type: Type of document ('receipt', 'delivery_order', 'transfer', 'stock_adjustment')
            
        Returns:
            Document object (Receipt, DeliveryOrder, Transfer, or StockAdjustment)
            
        Raises:
            DocumentError: If document not found or invalid type
        """
        # Parse document ID
        try:
            doc_uuid = uuid.UUID(document_id)
        except (ValueError, AttributeError):
            raise DocumentError(
                "Invalid document ID format",
                "INVALID_DOCUMENT_ID",
                {"document_id": document_id}
            )
        
        # Query based on document type
        if document_type == 'receipt':
            document = self.db.query(Receipt).filter(Receipt.id == doc_uuid).first()
        elif document_type == 'delivery_order':
            document = self.db.query(DeliveryOrder).filter(DeliveryOrder.id == doc_uuid).first()
        elif document_type == 'transfer':
            document = self.db.query(Transfer).filter(Transfer.id == doc_uuid).first()
        elif document_type == 'stock_adjustment':
            document = self.db.query(StockAdjustment).filter(StockAdjustment.id == doc_uuid).first()
        else:
            raise DocumentError(
                f"Invalid document type: {document_type}",
                "INVALID_DOCUMENT_TYPE",
                {"document_type": document_type}
            )
        
        if not document:
            raise DocumentError(
                f"{document_type} not found",
                "DOCUMENT_NOT_FOUND",
                {"document_id": document_id, "document_type": document_type}
            )
        
        return document
    
    def list_documents(
        self,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List documents with optional filtering.
        
        Args:
            document_type: Optional filter by document type ('receipt', 'delivery_order', 'transfer', 'stock_adjustment')
            status: Optional filter by status ('pending', 'validated', etc.)
            location_id: Optional filter by location ID
            
        Returns:
            List of documents with their details
            
        Raises:
            DocumentError: If invalid filter values
        """
        results = []
        
        # Parse location_id if provided
        location_uuid = None
        if location_id:
            try:
                location_uuid = uuid.UUID(location_id)
            except (ValueError, AttributeError):
                raise DocumentError(
                    "Invalid location ID format",
                    "INVALID_LOCATION_ID",
                    {"location_id": location_id}
                )
        
        # Query receipts
        if document_type is None or document_type == 'receipt':
            query = self.db.query(Receipt)
            
            # Apply status filter
            if status:
                try:
                    status_enum = ReceiptStatus[status]
                    query = query.filter(Receipt.status == status_enum)
                except KeyError:
                    raise DocumentError(
                        f"Invalid status for receipt: {status}",
                        "INVALID_STATUS",
                        {"status": status, "document_type": "receipt"}
                    )
            
            # Apply location filter
            if location_uuid:
                query = query.join(ReceiptItem).filter(ReceiptItem.location_id == location_uuid)
            
            receipts = query.all()
            for receipt in receipts:
                results.append({
                    "id": str(receipt.id),
                    "document_type": "receipt",
                    "status": receipt.status.value,
                    "supplier_name": receipt.supplier_name,
                    "supplier_contact": receipt.supplier_contact,
                    "created_by": str(receipt.created_by),
                    "created_at": receipt.created_at.isoformat(),
                    "validated_by": str(receipt.validated_by) if receipt.validated_by else None,
                    "validated_at": receipt.validated_at.isoformat() if receipt.validated_at else None
                })
        
        # Query delivery orders
        if document_type is None or document_type == 'delivery_order':
            query = self.db.query(DeliveryOrder)
            
            # Apply status filter
            if status:
                try:
                    status_enum = DeliveryOrderStatus[status]
                    query = query.filter(DeliveryOrder.status == status_enum)
                except KeyError:
                    raise DocumentError(
                        f"Invalid status for delivery_order: {status}",
                        "INVALID_STATUS",
                        {"status": status, "document_type": "delivery_order"}
                    )
            
            # Apply location filter
            if location_uuid:
                query = query.join(DeliveryOrderItem).filter(DeliveryOrderItem.location_id == location_uuid)
            
            delivery_orders = query.all()
            for order in delivery_orders:
                results.append({
                    "id": str(order.id),
                    "document_type": "delivery_order",
                    "status": order.status.value,
                    "customer_name": order.customer_name,
                    "customer_contact": order.customer_contact,
                    "created_by": str(order.created_by),
                    "created_at": order.created_at.isoformat(),
                    "validated_by": str(order.validated_by) if order.validated_by else None,
                    "validated_at": order.validated_at.isoformat() if order.validated_at else None
                })
        
        # Query transfers
        if document_type is None or document_type == 'transfer':
            query = self.db.query(Transfer)
            
            # Apply status filter
            if status:
                try:
                    status_enum = TransferStatus[status]
                    query = query.filter(Transfer.status == status_enum)
                except KeyError:
                    raise DocumentError(
                        f"Invalid status for transfer: {status}",
                        "INVALID_STATUS",
                        {"status": status, "document_type": "transfer"}
                    )
            
            # Apply location filter (source or destination)
            if location_uuid:
                query = query.filter(
                    or_(
                        Transfer.source_location_id == location_uuid,
                        Transfer.destination_location_id == location_uuid
                    )
                )
            
            transfers = query.all()
            for transfer in transfers:
                results.append({
                    "id": str(transfer.id),
                    "document_type": "transfer",
                    "status": transfer.status.value,
                    "product_id": str(transfer.product_id),
                    "source_location_id": str(transfer.source_location_id),
                    "destination_location_id": str(transfer.destination_location_id),
                    "quantity": transfer.quantity,
                    "created_by": str(transfer.created_by),
                    "created_at": transfer.created_at.isoformat(),
                    "validated_by": str(transfer.validated_by) if transfer.validated_by else None,
                    "validated_at": transfer.validated_at.isoformat() if transfer.validated_at else None
                })
        
        # Query stock adjustments
        if document_type is None or document_type == 'stock_adjustment':
            query = self.db.query(StockAdjustment)
            
            # Apply status filter
            if status:
                try:
                    status_enum = StockAdjustmentStatus[status]
                    query = query.filter(StockAdjustment.status == status_enum)
                except KeyError:
                    raise DocumentError(
                        f"Invalid status for stock_adjustment: {status}",
                        "INVALID_STATUS",
                        {"status": status, "document_type": "stock_adjustment"}
                    )
            
            # Apply location filter
            if location_uuid:
                query = query.filter(StockAdjustment.location_id == location_uuid)
            
            adjustments = query.all()
            for adjustment in adjustments:
                results.append({
                    "id": str(adjustment.id),
                    "document_type": "stock_adjustment",
                    "status": adjustment.status.value,
                    "product_id": str(adjustment.product_id),
                    "location_id": str(adjustment.location_id),
                    "recorded_quantity": adjustment.recorded_quantity,
                    "physical_quantity": adjustment.physical_quantity,
                    "adjustment_difference": adjustment.adjustment_difference,
                    "reason": adjustment.reason,
                    "created_by": str(adjustment.created_by),
                    "created_at": adjustment.created_at.isoformat(),
                    "validated_by": str(adjustment.validated_by) if adjustment.validated_by else None,
                    "validated_at": adjustment.validated_at.isoformat() if adjustment.validated_at else None
                })
        
        return results
