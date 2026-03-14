"""Script to run the CoreInventory API server."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if database exists
if not os.path.exists('coreinventory.db'):
    print("Database not found. Please run migrations first:")
    print("  alembic upgrade head")
    sys.exit(1)

# Import and run the app
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("CoreInventory REST API Server")
    print("=" * 60)
    print(f"Server running at: http://localhost:5000")
    print(f"API Documentation: See API_DOCUMENTATION.md")
    print(f"Health Check: http://localhost:5000/health")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
