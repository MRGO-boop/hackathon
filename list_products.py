"""Quick script to list all products in the database."""
from core_inventory.database import get_db
from core_inventory.models.product import Product

db = next(get_db())
try:
    products = db.query(Product).all()
    
    if len(products) == 0:
        print("\n❌ No products found in database!")
        print("   Create a product through the web interface first.")
    else:
        print(f"\n✅ Found {len(products)} product(s):\n")
        for p in products:
            print(f"   SKU: {p.sku}")
            print(f"   Name: {p.name}")
            print(f"   Category: {p.category}")
            print(f"   Unit: {p.unit_of_measure}")
            print(f"   Threshold: {p.low_stock_threshold}")
            print(f"   ID: {p.id}")
            print()
finally:
    db.close()
