"""Dashboard component for KPI calculations."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.receipt import Receipt, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus


class DashboardError(Exception):
    """Base exception for dashboard errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class Dashboard:
    """Handles dashboard KPI calculations."""
    
    def __init__(self, db: Session):
        """Initialize dashboard with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_total_product_count(self) -> int:
        """Calculate total count of products.
        
        Returns:
            int: Total number of products in the system
        """
        count = self.db.query(Product).count()
        return count
    
    def get_low_stock_product_count(self) -> int:
        """Calculate count of products below their low stock threshold.
        
        Only counts products that have a configured low_stock_threshold.
        A product is considered low stock if its total stock across all
        locations is below its threshold.
        
        Returns:
            int: Number of products with stock below threshold
        """
        # Get products with configured thresholds
        products_with_threshold = self.db.query(Product).filter(
            Product.low_stock_threshold.isnot(None)
        ).all()
        
        low_stock_count = 0
        
        for product in products_with_threshold:
            # Calculate total stock across all locations
            total_stock = self.db.query(func.sum(Stock.quantity)).filter(
                Stock.product_id == product.id
            ).scalar()
            
            # Handle case where product has no stock records
            total_stock = total_stock if total_stock is not None else 0
            
            # Check if below threshold
            if total_stock < product.low_stock_threshold:
                low_stock_count += 1
        
        return low_stock_count
    
    def get_zero_stock_product_count(self) -> int:
        """Calculate count of products with zero stock.
        
        A product has zero stock if:
        - It has no stock records at any location, OR
        - The sum of stock across all locations is zero
        
        Returns:
            int: Number of products with zero stock
        """
        # Get all products
        all_products = self.db.query(Product).all()
        
        zero_stock_count = 0
        
        for product in all_products:
            # Calculate total stock across all locations
            total_stock = self.db.query(func.sum(Stock.quantity)).filter(
                Stock.product_id == product.id
            ).scalar()
            
            # Handle case where product has no stock records
            total_stock = total_stock if total_stock is not None else 0
            
            # Check if zero
            if total_stock == 0:
                zero_stock_count += 1
        
        return zero_stock_count
    
    def get_pending_receipt_count(self) -> int:
        """Calculate count of pending receipts.
        
        Returns:
            int: Number of receipts with pending status
        """
        count = self.db.query(Receipt).filter(
            Receipt.status == ReceiptStatus.pending
        ).count()
        return count
    
    def get_pending_delivery_order_count(self) -> int:
        """Calculate count of pending delivery orders.
        
        Returns:
            int: Number of delivery orders with pending status
        """
        count = self.db.query(DeliveryOrder).filter(
            DeliveryOrder.status == DeliveryOrderStatus.pending
        ).count()
        return count
    
    def get_pending_transfer_count(self) -> int:
        """Calculate count of pending transfers.
        
        Returns:
            int: Number of transfers with pending status
        """
        count = self.db.query(Transfer).filter(
            Transfer.status == TransferStatus.pending
        ).count()
        return count
    
    def get_all_kpis(self) -> Dict[str, int]:
        """Get all dashboard KPIs in a single call.
        
        This method calculates all KPIs and returns them in a dictionary.
        Real-time updates are ensured by querying the database directly.
        
        Returns:
            Dict[str, int]: Dictionary containing all KPI values
        """
        return {
            "total_products": self.get_total_product_count(),
            "low_stock_products": self.get_low_stock_product_count(),
            "zero_stock_products": self.get_zero_stock_product_count(),
            "pending_receipts": self.get_pending_receipt_count(),
            "pending_delivery_orders": self.get_pending_delivery_order_count(),
            "pending_transfers": self.get_pending_transfer_count()
        }
