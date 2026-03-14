"""Simple script to start the API with automatic database setup."""
import os
from dotenv import load_dotenv

load_dotenv()

# Try to create database tables directly
try:
    from core_inventory.database import Base, engine
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"Warning: Could not create tables: {e}")
    print("You may need to run: alembic upgrade head")

# Start the API
from app import app

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("CoreInventory REST API Server")
    print("=" * 60)
    print(f"Server: http://localhost:5000")
    print(f"Health: http://localhost:5000/health")
    print(f"Docs: See API_DOCUMENTATION.md")
    print("=" * 60)
    print("\nPress CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
