"""Test if products API is working."""
import requests

API_BASE = "http://localhost:5000/api"

print("\n" + "="*60)
print("TESTING PRODUCTS API")
print("="*60)

# Step 1: Create a user and login
print("\n1. Creating test user...")
try:
    response = requests.post(f"{API_BASE}/auth/signup", json={
        "email": "test@test.com",
        "password": "test123",
        "name": "Test User"
    })
    if response.status_code == 201:
        print("   ✅ User created")
    else:
        print(f"   ℹ️  User might already exist (status: {response.status_code})")
except Exception as e:
    print(f"   ⚠️  {e}")

# Step 2: Login
print("\n2. Logging in...")
try:
    response = requests.post(f"{API_BASE}/auth/login", json={
        "email": "test@test.com",
        "password": "test123"
    })
    if response.status_code == 200:
        data = response.json()
        token = data['session_id']
        print(f"   ✅ Logged in successfully")
        print(f"   Token: {token[:20]}...")
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 3: Get existing products
print("\n3. Fetching existing products...")
try:
    response = requests.get(
        f"{API_BASE}/products/search?q=",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        products = response.json()
        print(f"   ✅ Found {len(products)} product(s)")
        for p in products:
            print(f"      - {p['sku']}: {p['name']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 4: Create a test product
print("\n4. Creating a test product...")
try:
    response = requests.post(
        f"{API_BASE}/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sku": "TEST-001",
            "name": "Test Product",
            "category": "Test Category",
            "unit_of_measure": "pieces",
            "low_stock_threshold": 10,
            "initial_stock_quantity": 0,
            "initial_stock_location_id": None
        }
    )
    if response.status_code == 201:
        product = response.json()
        print(f"   ✅ Product created successfully")
        print(f"      SKU: {product['sku']}")
        print(f"      Name: {product['name']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 5: Fetch products again
print("\n5. Fetching products again...")
try:
    response = requests.get(
        f"{API_BASE}/products/search?q=",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        products = response.json()
        print(f"   ✅ Found {len(products)} product(s)")
        for p in products:
            print(f"      - {p['sku']}: {p['name']} ({p['category']})")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60 + "\n")
