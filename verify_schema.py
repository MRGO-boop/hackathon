"""Verify database schema was created correctly."""
from sqlalchemy import inspect
from core_inventory.database import engine

def verify_schema():
    """Verify all tables were created."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        'users', 'products', 'locations', 'stock',
        'receipts', 'receipt_items',
        'delivery_orders', 'delivery_order_items',
        'transfers', 'stock_adjustments',
        'move_history', 'stock_ledger',
        'alembic_version'
    ]
    
    print("Database Tables:")
    print("=" * 50)
    for table in sorted(tables):
        print(f"✓ {table}")
        columns = inspector.get_columns(table)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    
    print("\n" + "=" * 50)
    print(f"Total tables: {len(tables)}")
    
    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"\n⚠ Missing tables: {missing}")
    else:
        print("\n✓ All expected tables created successfully!")

if __name__ == "__main__":
    verify_schema()
