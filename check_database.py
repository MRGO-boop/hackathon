"""Quick script to check database contents."""
from core_inventory.database import get_db
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.models.user import User

def check_database():
    """Check what's in the database."""
    db = next(get_db())
    
    try:
        print("\n" + "="*60)
        print("DATABASE CONTENTS CHECK")
        print("="*60)
        
        # Check users
        users = db.query(User).all()
        print(f"\n📊 USERS: {len(users)} total")
        for user in users:
            print(f"  - {user.email} ({user.name})")
        
        # Check products
        products = db.query(Product).all()
        print(f"\n📦 PRODUCTS: {len(products)} total")
        for product in products:
            print(f"  - {product.sku}: {product.name} ({product.category})")
        
        # Check locations
        locations = db.query(Location).all()
        print(f"\n📍 LOCATIONS: {len(locations)} total")
        for location in locations:
            status = "Archived" if location.is_archived else "Active"
            print(f"  - {location.name} ({location.type.value}) - {status}")
        
        print("\n" + "="*60)
        
        if len(products) == 0:
            print("\n⚠️  WARNING: No products found in database!")
            print("   Try creating a product through the web interface.")
        
        if len(locations) == 0:
            print("\n⚠️  WARNING: No locations found in database!")
            print("   Try creating a location through the web interface.")
        
        print()
        
    finally:
        db.close()

if __name__ == '__main__':
    check_database()
