"""Initialize the database with all tables."""
# Import all models first so they register with Base
from core_inventory.models.user import User
from core_inventory.models.product import Product
from core_inventory.models.location import Location
from core_inventory.models.stock import Stock
from core_inventory.models.receipt import Receipt, ReceiptItem
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderItem
from core_inventory.models.transfer import Transfer
from core_inventory.models.stock_adjustment import StockAdjustment
from core_inventory.models.move_history import MoveHistory
from core_inventory.models.session import Session
from core_inventory.models.password_reset import PasswordReset

from core_inventory.database import Base, engine

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
print("\nTables created:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
