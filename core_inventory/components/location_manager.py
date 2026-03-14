"""Location Manager component for location management operations."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from core_inventory.models.location import Location
from core_inventory.models.stock import Stock


class LocationError(Exception):
    """Base exception for location management errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class LocationManager:
    """Handles location management operations."""
    
    def __init__(self, db: Session):
        """Initialize location manager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_location(
        self,
        name: str,
        location_type: str,
        parent_id: Optional[str] = None
    ) -> Location:
        """Create a new location.
        
        Args:
            name: Location name
            location_type: Type of location (warehouse, rack, floor_area)
            parent_id: Optional parent location ID for hierarchy
            
        Returns:
            Location: The newly created location object
            
        Raises:
            LocationError: If validation fails
        """
        # Validate required fields
        if not name or not name.strip():
            raise LocationError(
                "Location name is required",
                "INVALID_NAME",
                {"field": "name"}
            )
        
        if not location_type or not location_type.strip():
            raise LocationError(
                "Location type is required",
                "INVALID_TYPE",
                {"field": "location_type"}
            )
        
        # Validate location type
        from core_inventory.models.location import LocationType
        try:
            loc_type = LocationType[location_type.strip()]
        except KeyError:
            raise LocationError(
                f"Invalid location type: {location_type}. Must be one of: warehouse, rack, floor_area",
                "INVALID_TYPE",
                {"field": "location_type", "value": location_type}
            )
        
        # Validate parent_id if provided
        parent_uuid = None
        if parent_id:
            try:
                parent_uuid = uuid.UUID(parent_id)
            except (ValueError, AttributeError):
                raise LocationError(
                    "Invalid parent location ID format",
                    "INVALID_PARENT_ID",
                    {"parent_id": parent_id}
                )
            
            # Check if parent exists
            parent = self.db.query(Location).filter(Location.id == parent_uuid).first()
            if not parent:
                raise LocationError(
                    f"Parent location not found",
                    "PARENT_NOT_FOUND",
                    {"parent_id": parent_id}
                )
        
        # Create location
        location = Location(
            id=uuid.uuid4(),
            name=name.strip(),
            type=loc_type,
            parent_id=parent_uuid,
            is_archived=False
        )
        
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        return location
    
    def update_location(
        self,
        location_id: str,
        name: Optional[str] = None,
        location_type: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Location:
        """Update location details.
        
        Args:
            location_id: Location ID to update
            name: Optional new location name
            location_type: Optional new location type
            parent_id: Optional new parent location ID
            
        Returns:
            Location: The updated location object
            
        Raises:
            LocationError: If location not found or validation fails
        """
        # Parse location ID
        try:
            location_uuid = uuid.UUID(location_id)
        except (ValueError, AttributeError):
            raise LocationError(
                "Invalid location ID format",
                "INVALID_LOCATION_ID",
                {"location_id": location_id}
            )
        
        # Find location
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise LocationError(
                f"Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        # Update name if provided
        if name is not None:
            if not name.strip():
                raise LocationError(
                    "Location name cannot be empty",
                    "INVALID_NAME",
                    {"field": "name"}
                )
            location.name = name.strip()
        
        # Update type if provided
        if location_type is not None:
            from core_inventory.models.location import LocationType
            try:
                loc_type = LocationType[location_type.strip()]
                location.type = loc_type
            except KeyError:
                raise LocationError(
                    f"Invalid location type: {location_type}. Must be one of: warehouse, rack, floor_area",
                    "INVALID_TYPE",
                    {"field": "location_type", "value": location_type}
                )
        
        # Update parent_id if provided
        if parent_id is not None:
            if parent_id.strip():
                try:
                    parent_uuid = uuid.UUID(parent_id)
                except (ValueError, AttributeError):
                    raise LocationError(
                        "Invalid parent location ID format",
                        "INVALID_PARENT_ID",
                        {"parent_id": parent_id}
                    )
                
                # Check if parent exists
                parent = self.db.query(Location).filter(Location.id == parent_uuid).first()
                if not parent:
                    raise LocationError(
                        f"Parent location not found",
                        "PARENT_NOT_FOUND",
                        {"parent_id": parent_id}
                    )
                
                location.parent_id = parent_uuid
            else:
                # Empty string means remove parent
                location.parent_id = None
        
        self.db.commit()
        self.db.refresh(location)
        
        return location
    
    def archive_location(self, location_id: str) -> None:
        """Archive a location (soft delete).
        
        Args:
            location_id: Location ID to archive
            
        Raises:
            LocationError: If location not found or has existing stock
        """
        # Parse location ID
        try:
            location_uuid = uuid.UUID(location_id)
        except (ValueError, AttributeError):
            raise LocationError(
                "Invalid location ID format",
                "INVALID_LOCATION_ID",
                {"location_id": location_id}
            )
        
        # Find location
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise LocationError(
                f"Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        # Check if location has existing stock
        stock_count = self.db.query(Stock).filter(
            Stock.location_id == location_uuid,
            Stock.quantity > 0
        ).count()
        
        if stock_count > 0:
            raise LocationError(
                f"Cannot archive location with existing stock. Location has {stock_count} product(s) with stock.",
                "LOCATION_HAS_STOCK",
                {"location_id": location_id, "stock_count": stock_count}
            )
        
        # Archive location
        location.is_archived = True
        self.db.commit()
    
    def get_location(self, location_id: str) -> Location:
        """Retrieve a location by ID.
        
        Args:
            location_id: Location ID to retrieve
            
        Returns:
            Location: The location object
            
        Raises:
            LocationError: If location not found
        """
        # Parse location ID
        try:
            location_uuid = uuid.UUID(location_id)
        except (ValueError, AttributeError):
            raise LocationError(
                "Invalid location ID format",
                "INVALID_LOCATION_ID",
                {"location_id": location_id}
            )
        
        # Find location
        location = self.db.query(Location).filter(Location.id == location_uuid).first()
        if not location:
            raise LocationError(
                f"Location not found",
                "LOCATION_NOT_FOUND",
                {"location_id": location_id}
            )
        
        return location
    
    def list_locations(self, include_archived: bool = False) -> List[Location]:
        """List all locations.
        
        Args:
            include_archived: Whether to include archived locations
            
        Returns:
            List[Location]: List of all locations
        """
        query = self.db.query(Location)
        
        if not include_archived:
            query = query.filter(Location.is_archived == False)
        
        return query.all()
