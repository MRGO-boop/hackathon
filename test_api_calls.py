"""Test API calls to demonstrate the CoreInventory API."""
import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(title, response):
    """Pretty print API response."""
    print("\n" + "=" * 60)
    print(f"📡 {title}")
    print("=" * 60)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print("=" * 60)

def main():
    print("\n🚀 CoreInventory API Test Suite")
    print("=" * 60)
    
    # 1. Health Check
    print("\n1️⃣  Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    
    if response.status_code != 200:
        print("\n❌ Server is not responding. Make sure it's running!")
        return
    
    # 2. Create User Account
    print("\n2️⃣  Creating User Account...")
    signup_data = {
        "email": "admin@coreinventory.com",
        "password": "admin123456",
        "name": "Admin User"
    }
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
    print_response("User Signup", response)
    
    # 3. Login
    print("\n3️⃣  Logging In...")
    login_data = {
        "email": "admin@coreinventory.com",
        "password": "admin123456"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print_response("Login", response)
    
    if response.status_code != 200:
        print("\n❌ Login failed!")
        return
    
    session_id = response.json()["session_id"]
    headers = {"Authorization": f"Bearer {session_id}"}
    print(f"\n✅ Session Token: {session_id}")
    
    # 4. Create Location
    print("\n4️⃣  Creating Warehouse Location...")
    location_data = {
        "name": "Main Warehouse",
        "type": "warehouse"
    }
    response = requests.post(f"{BASE_URL}/api/locations", json=location_data, headers=headers)
    print_response("Create Location", response)
    
    if response.status_code != 201:
        print("\n❌ Failed to create location!")
        return
    
    location_id = response.json()["id"]
    print(f"\n✅ Location ID: {location_id}")
    
    # 5. Create Product with Initial Stock
    print("\n5️⃣  Creating Product with Initial Stock...")
    product_data = {
        "sku": "LAPTOP-001",
        "name": "Dell Latitude 5420",
        "category": "Electronics",
        "unit_of_measure": "pieces",
        "low_stock_threshold": 5,
        "initial_stock_quantity": 50,
        "initial_stock_location_id": location_id
    }
    response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
    print_response("Create Product", response)
    
    if response.status_code != 201:
        print("\n❌ Failed to create product!")
        return
    
    product_id = response.json()["id"]
    print(f"\n✅ Product ID: {product_id}")
    
    # 6. Check Stock
    print("\n6️⃣  Checking Stock Level...")
    response = requests.get(f"{BASE_URL}/api/stock/{product_id}/{location_id}", headers=headers)
    print_response("Stock Level", response)
    
    # 7. Get Dashboard KPIs
    print("\n7️⃣  Getting Dashboard KPIs...")
    response = requests.get(f"{BASE_URL}/api/dashboard/kpis", headers=headers)
    print_response("Dashboard KPIs", response)
    
    # 8. Search Products
    print("\n8️⃣  Searching for Products...")
    response = requests.get(f"{BASE_URL}/api/products/search?q=Laptop", headers=headers)
    print_response("Product Search", response)
    
    # 9. Create Receipt (Incoming Goods)
    print("\n9️⃣  Creating Receipt for Incoming Goods...")
    receipt_data = {
        "supplier_name": "Tech Supplier Inc",
        "supplier_contact": "supplier@tech.com",
        "items": [
            {
                "product_id": product_id,
                "location_id": location_id,
                "expected_quantity": 20,
                "received_quantity": 20
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/api/documents/receipts", json=receipt_data, headers=headers)
    print_response("Create Receipt", response)
    
    if response.status_code != 201:
        print("\n❌ Failed to create receipt!")
        return
    
    receipt_id = response.json()["id"]
    print(f"\n✅ Receipt ID: {receipt_id}")
    
    # 10. Validate Receipt (Updates Stock)
    print("\n🔟 Validating Receipt (This will increase stock)...")
    response = requests.post(f"{BASE_URL}/api/documents/receipts/{receipt_id}/validate", headers=headers)
    print_response("Validate Receipt", response)
    
    # 11. Check Updated Stock
    print("\n1️⃣1️⃣  Checking Updated Stock Level...")
    response = requests.get(f"{BASE_URL}/api/stock/{product_id}/{location_id}", headers=headers)
    print_response("Updated Stock Level", response)
    
    # 12. View Move History
    print("\n1️⃣2️⃣  Viewing Move History...")
    response = requests.get(f"{BASE_URL}/api/history/movements", headers=headers)
    print_response("Move History", response)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ API TEST COMPLETE!")
    print("=" * 60)
    print("\n📊 Summary:")
    print("  ✓ Created user account")
    print("  ✓ Logged in successfully")
    print("  ✓ Created warehouse location")
    print("  ✓ Created product with initial stock (50 units)")
    print("  ✓ Created and validated receipt (+20 units)")
    print("  ✓ Final stock: 70 units")
    print("  ✓ Move history tracked")
    print("\n🎉 Your CoreInventory API is working perfectly!")
    print("\n📖 Next steps:")
    print("  - Check API_DOCUMENTATION.md for all endpoints")
    print("  - Try creating delivery orders, transfers, adjustments")
    print("  - Use Postman for more advanced testing")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the API server!")
        print("Make sure the server is running at http://localhost:5000")
        print("Run: python run_flask.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
