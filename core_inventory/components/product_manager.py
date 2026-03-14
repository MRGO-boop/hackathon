"""Product Manager component for product management operations."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.move_history import MoveHistory, DocumentType


class ProductError(Exception):
    """Base exception for product management errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class ProductManager:
    """Handles product management operations."""
    
    def __init__(self, db: Session):
        """Initialize product manager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_product(
        self,
        sku: str,
        name: str,
        category: str,
        unit_of_measure: str,
        low_stock_threshold: Optional[int] = None,
        initial_stock_quantity: Optional[int] = None,
        initial_stock_location_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Product:
        """Create a new product with optional initial stock.
        
        Args:
            sku: Unique stock keeping unit identifier
            name: Product name
            category: Product category
            unit_of_measure: Unit of measure (e.g., "pieces", "kg", "liters")
            low_stock_threshold: Optional threshold for low stock alerts
            initial_stock_quantity: Optional initial stock quantity
            initial_stock_location_id: Required if initial_stock_quantity > 0
            user_id: User creating the product (required if initial_stock_quantity > 0)
            
        Returns:
            Product: The newly created product object
            
        Raises:
            ProductError: If validation fails or SKU already exists
        """
        # Validate required fields
        if not sku or not sku.strip():
            raise ProductError(
                "SKU is required",
                "INVALID_SKU",
                {"field": "sku"}
            )
        
        if not name or not name.strip():
            raise ProductError(
                "Product name is required",
                "INVALID_NAME",
                {"field": "name"}
            )
        
        if not category or not category.strip():
            raise ProductError(
                "Category is required",
                "INVALID_CATEGORY",
                {"field": "category"}
            )
        
        if not unit_of_measure or not unit_of_measure.strip():
            raise ProductError(
                "Unit of measure is required",
                "INVALID_UNIT",
                {"field": "unit_of_measure"}
            )
        
        # Validate initial stock requirements
        if initial_stock_quantity is not None and initial_stock_quantity > 0:
            if not initial_stock_location_id:
                raise ProductError(
                    "Location is required when initial stock quantity is provided",
                    "MISSING_LOCATION",
                    {"field": "initial_stock_location_id"}
                )
            if not user_id:
                raise ProductError(
                    "User ID is required when initial stock quantity is provided",
                    "MISSING_USER",
                    {"field": "user_id"}
                )
        
        # Check if SKU already exists
        existing_product = self.db.query(Product).filter(
            Product.sku == sku.strip()
        ).first()
        
        if existing_product:
            raise ProductError(
                f"SKU {sku} already exists",
                "SKU_EXISTS",
                {"sku": sku}
            )
        
        # Create product
        product = Product(
            id=uuid.uuid4(),
            sku=sku.strip(),
            name=name.strip(),
            category=category.strip(),
            unit_of_measure=unit_of_measure.strip(),
            low_stock_threshold=low_stock_threshold
        )
        
        self.db.add(product)
        self.db.flush()  # Flush to get product ID
        
        # Handle initial stock if provided
        if initial_stock_quantity is not None and initial_stock_quantity > 0:
            # Parse location ID
            try:
                location_uuid = uuid.UUID(initial_stock_location_id)
                user_uuid = uuid.UUID(user_id)
            except (ValueError, AttributeError):
                raise ProductError(
                    "Invalid location or user ID format",
                    "INVALID_ID",
                    {"location_id": initial_stock_location_id, "user_id": user_id}
                )
            
            # Create stock record
            stock = Stock(
                id=uuid.uuid4(),
                product_id=product.id,
                location_id=location_uuid,
                quantity=initial_stock_quantity
            )
            self.db.add(stock)
            
            # Create move history entry
            move_history = MoveHistory(
                id=uuid.uuid4(),
                product_id=product.id,
                location_id=location_uuid,
                quantity_change=initial_stock_quantity,
                document_type=DocumentType.initial_stock,
                document_id=str(product.id),
                user_id=user_uuid
            )
            self.db.add(move_history)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product

    
    def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        unit_of_measure: Optional[str] = None,
        low_stock_threshold: Optional[int] = None
    ) -> Product:
        """Update product details (SKU cannot be changed).
        
        Args:
            product_id: Product ID to update
            name: Optional new product name
            category: Optional new category
            unit_of_measure: Optional new unit of measure
            low_stock_threshold: Optional new low stock threshold
            
        Returns:
            Product: The updated product object
            
        Raises:
            ProductError: If product not found or validation fails
        """
        # Parse product ID
        try:
            product_uuid = uuid.UUID(product_id)
        except (ValueError, AttributeError):
            raise ProductError(
                "Invalid product ID format",
                "INVALID_PRODUCT_ID",
                {"product_id": product_id}
            )
        
        # Find product
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise ProductError(
                f"Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        # Update fields if provided
        if name is not None:
            if not name.strip():
                raise ProductError(
                    "Product name cannot be empty",
                    "INVALID_NAME",
                    {"field": "name"}
                )
            product.name = name.strip()
        
        if category is not None:
            if not category.strip():
                raise ProductError(
                    "Category cannot be empty",
                    "INVALID_CATEGORY",
                    {"field": "category"}
                )
            product.category = category.strip()
        
        if unit_of_measure is not None:
            if not unit_of_measure.strip():
                raise ProductError(
                    "Unit of measure cannot be empty",
                    "INVALID_UNIT",
                    {"field": "unit_of_measure"}
                )
            product.unit_of_measure = unit_of_measure.strip()
        
        if low_stock_threshold is not None:
            product.low_stock_threshold = low_stock_threshold
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_product(self, product_id: str) -> Product:
        """Retrieve a product by ID.
        
        Args:
            product_id: Product ID to retrieve
            
        Returns:
            Product: The product object
            
        Raises:
            ProductError: If product not found
        """
        # Parse product ID
        try:
            product_uuid = uuid.UUID(product_id)
        except (ValueError, AttributeError):
            raise ProductError(
                "Invalid product ID format",
                "INVALID_PRODUCT_ID",
                {"product_id": product_id}
            )
        
        # Find product
        product = self.db.query(Product).filter(Product.id == product_uuid).first()
        if not product:
            raise ProductError(
                f"Product not found",
                "PRODUCT_NOT_FOUND",
                {"product_id": product_id}
            )
        
        return product
    
    def search_products(self, query: str) -> List[Product]:
        """Search products by SKU (exact match) or name (partial match).
        
        Args:
            query: Search query string
            
        Returns:
            List[Product]: List of matching products
        """
        # If no query provided, return all products
        if not query or not query.strip():
            return self.db.query(Product).all()
        
        search_term = query.strip()
        
        # Search by exact SKU match or partial name match
        products = self.db.query(Product).filter(
            or_(
                Product.sku == search_term,
                Product.name.ilike(f"%{search_term}%")
            )
        ).all()
        
        return products
    
    def filter_products(
        self,
        category: Optional[str] = None,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        unit_of_measure: Optional[str] = None
    ) -> List[Product]:
        """Filter products by multiple criteria with AND logic.
        
        Args:
            category: Optional category to filter by (exact match)
            sku: Optional SKU to filter by (exact match)
            name: Optional name to filter by (partial match)
            unit_of_measure: Optional unit of measure to filter by (exact match)
            
        Returns:
            List[Product]: List of matching products (all filters applied with AND logic)
        """
        query = self.db.query(Product)
        
        # Apply category filter
        if category and category.strip():
            query = query.filter(Product.category == category.strip())
        
        # Apply SKU filter
        if sku and sku.strip():
            query = query.filter(Product.sku == sku.strip())
        
        # Apply name filter (partial match)
        if name and name.strip():
            query = query.filter(Product.name.ilike(f"%{name.strip()}%"))
        
        # Apply unit of measure filter
        if unit_of_measure and unit_of_measure.strip():
            query = query.filter(Product.unit_of_measure == unit_of_measure.strip())
        
        return query.all()
