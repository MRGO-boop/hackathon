"""Run Flask server."""
import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from app import app

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("CoreInventory REST API Server")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    print("API Documentation: See API_DOCUMENTATION.md")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
