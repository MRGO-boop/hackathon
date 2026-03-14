"""Stock Manager component for stock tracking operations."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core_inventory.models.stock import Stock
from core_inventory.models.product import Product
from core_inventory.models.location import Location


class StockError(Exception):
    """Base exception for stock management errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class LocationStock:
    """Data class for stock at a specific location."""
    def __init__(self, location_id: str, location_name: str, quantity: int):
        self.location_id = location_id
        self.location_name = location_name
        self.quantity = quantity


class StockManager:
    """Handles stock tracking operations."""
    
    def __init__(self, db: Session):
        """Initialize stock manager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_stock(self, product_id: str, location_id: str) -> int:
        """Get stock quantity for a product at a specific location.
        
        Args:
            product_id: Product ID
            location_id: Location ID
            
        Returns:
            int: Stock quantity (0 if no stock record exists)
            
        Raises:
            StockError: If product or location ID is invalid
        """
        # Parse IDs
        try:
            product_uuid = uuid.UUID(product_id)
            location_uuid = uuid.UUID(location_id)
        except (ValueError, AttributeError):
            raise StockError(
                "Invalid product or location ID format",
                "INVALID_ID",
                {"product_id": product_id, "location_id": location_id}
            )
        
        # Query stock
        stock = self.db.query(Stock).filter(
            and_(
                Stock.product_id == product_uuid,
                Stock.location_id == location_uuid
            )
        ).first()
        
        return stock.quantity if stock else 0

    
    def update_stock(
        self,
        product_id: str,
        location_id: str,
        delta: int
    ) -> None:
        """Update stock quantity by a delta amount with transaction support.
        
        This method is designed to be called within a database transaction.
        It will create a stock record if one doesn't exist.
        
        Args:
            product_id: Product ID
            location_id: Location ID
            delta: Change in quantity (positive for increase, negative for decrease)
            
        Raises:
            StockError: If validation fails or stock would become negative
        """
        # Parse IDs
        try:
            product_uuid = uuid.UUID(product_id)
            location_uuid = uuid.UUID(location_id)
        except (ValueError, AttributeError):
            raise StockError(
                "Invalid product or location ID format",
                "INVALID_ID",
                {"product_id": product_id, "location_id": location_id}
            )
        
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise StockError(
                "Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        # Verify location exists
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise StockError(
                "Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        # Get or create stock record
        stock = self.db.query(Stock).filter(
            and_(
                Stock.product_id == product_uuid,
                Stock.location_id == location_uuid
            )
        ).first()
        
        if stock:
            new_quantity = stock.quantity + delta
            if new_quantity < 0:
                raise StockError(
                    f"Insufficient stock: cannot reduce stock below zero",
                    "INSUFFICIENT_STOCK",
                    {
                        "product_id": product_id,
                        "location_id": location_id,
                        "current_quantity": stock.quantity,
                        "delta": delta,
                        "would_be": new_quantity
                    }
                )
            stock.quantity = new_quantity
        else:
            # Create new stock record
            if delta < 0:
                raise StockError(
                    f"Cannot create stock record with negative quantity",
                    "INVALID_QUANTITY",
                    {
                        "product_id": product_id,
                        "location_id": location_id,
                        "delta": delta
                    }
                )
            stock = Stock(
                id=uuid.uuid4(),
                product_id=product_uuid,
                location_id=location_uuid,
                quantity=delta
            )
            self.db.add(stock)
        
        # Note: Commit is handled by the caller to support transactions
        self.db.flush()

    
    def check_availability(
        self,
        product_id: str,
        location_id: str,
        required: int
    ) -> bool:
        """Check if sufficient stock is available at a location.
        
        Args:
            product_id: Product ID
            location_id: Location ID
            required: Required quantity
            
        Returns:
            bool: True if available stock >= required quantity, False otherwise
            
        Raises:
            StockError: If product or location ID is invalid
        """
        if required < 0:
            raise StockError(
                "Required quantity cannot be negative",
                "INVALID_QUANTITY",
                {"required": required}
            )
        
        current_stock = self.get_stock(product_id, location_id)
        return current_stock >= required
    
    def get_stock_by_product(self, product_id: str) -> List[LocationStock]:
        """Get stock levels across all locations for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            List[LocationStock]: List of stock quantities at each location
            
        Raises:
            StockError: If product ID is invalid
        """
        # Parse product ID
        try:
            product_uuid = uuid.UUID(product_id)
        except (ValueError, AttributeError):
            raise StockError(
                "Invalid product ID format",
                "INVALID_PRODUCT_ID",
                {"product_id": product_id}
            )
        
        # Query stock with location details
        results = self.db.query(Stock, Location).join(
            Location, Stock.location_id == Location.id
        ).filter(
            Stock.product_id == product_uuid
        ).all()
        
        # Convert to LocationStock objects
        location_stocks = []
        for stock, location in results:
            location_stocks.append(
                LocationStock(
                    location_id=str(location.id),
                    location_name=location.name,
                    quantity=stock.quantity
                )
            )
        
        return location_stocks

    
    def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get products with stock below their configured threshold.
        
        Args:
            threshold: Optional global threshold to use for products without configured threshold
            
        Returns:
            List[Dict]: List of products with low stock, including product details and stock info
        """
        # Query products with low_stock_threshold configured
        products_with_threshold = self.db.query(Product).filter(
            Product.low_stock_threshold.isnot(None)
        ).all()
        
        low_stock_products = []
        
        for product in products_with_threshold:
            # Get total stock across all locations
            total_stock = self.db.query(Stock).filter(
                Stock.product_id == product.id
            ).with_entities(
                Stock.quantity
            ).all()
            
            total_quantity = sum(stock.quantity for stock in total_stock) if total_stock else 0
            
            # Check if below threshold
            product_threshold = product.low_stock_threshold
            if total_quantity < product_threshold:
                low_stock_products.append({
                    "product_id": str(product.id),
                    "sku": product.sku,
                    "name": product.name,
                    "category": product.category,
                    "current_stock": total_quantity,
                    "threshold": product_threshold
                })
        
        # If global threshold provided, also check products without configured threshold
        if threshold is not None:
            products_without_threshold = self.db.query(Product).filter(
                Product.low_stock_threshold.is_(None)
            ).all()
            
            for product in products_without_threshold:
                # Get total stock across all locations
                total_stock = self.db.query(Stock).filter(
                    Stock.product_id == product.id
                ).with_entities(
                    Stock.quantity
                ).all()
                
                total_quantity = sum(stock.quantity for stock in total_stock) if total_stock else 0
                
                # Check if below global threshold
                if total_quantity < threshold:
                    low_stock_products.append({
                        "product_id": str(product.id),
                        "sku": product.sku,
                        "name": product.name,
                        "category": product.category,
                        "current_stock": total_quantity,
                        "threshold": threshold
                    })
        
        return low_stock_products
