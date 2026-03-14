"""Integration tests for REST API endpoints."""
import pytest
import json
from app import app
from core_inventory.database import SessionLocal, Base, engine
from core_inventory.components.authenticator import Authenticator
from core_inventory.components.product_manager import ProductManager
from core_inventory.components.location_manager import LocationManager


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(db_session):
    """Create a user and return authentication headers."""
    authenticator = Authenticator(db_session)
    user = authenticator.signup(
        email="test@example.com",
        password="testpassword123",
        name="Test User"
    )
    session = authenticator.login(
        email="test@example.com",
        password="testpassword123"
    )
    return {'Authorization': f'Bearer {session.id}'}


@pytest.fixture
def sample_location(db_session):
    """Create a sample location for testing."""
    location_manager = LocationManager(db_session)
    location = location_manager.create_location(
        name="Main Warehouse",
        location_type="warehouse"
    )
    return location


@pytest.fixture
def sample_product(db_session, sample_location, auth_headers):
    """Create a sample product for testing."""
    product_manager = ProductManager(db_session)
    
    # Extract user_id from auth_headers by validating session
    session_id = auth_headers['Authorization'].replace('Bearer ', '')
    authenticator = Authenticator(db_session)
    user = authenticator.validate_session(session_id)
    
    product = product_manager.create_product(
        sku="TEST-001",
        name="Test Product",
        category="Test Category",
        unit_of_measure="pieces",
        low_stock_threshold=10,
        initial_stock_quantity=100,
        initial_stock_location_id=str(sample_location.id),
        user_id=str(user.id)
    )
    return product


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    def test_signup_success(self, client, db_session):
        """Test successful user signup."""
        response = client.post('/api/auth/signup', json={
            'email': 'newuser@example.com',
            'password': 'password123',
            'name': 'New User'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['email'] == 'newuser@example.com'
        assert data['name'] == 'New User'
        assert 'id' in data
    
    def test_signup_duplicate_email(self, client, db_session, auth_headers):
        """Test signup with duplicate email fails."""
        response = client.post('/api/auth/signup', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Duplicate User'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'EMAIL_EXISTS'
    
    def test_login_success(self, client, db_session):
        """Test successful login."""
        # First signup
        client.post('/api/auth/signup', json={
            'email': 'login@example.com',
            'password': 'password123',
            'name': 'Login User'
        })
        
        # Then login
        response = client.post('/api/auth/login', json={
            'email': 'login@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'user_id' in data
        assert 'expires_at' in data
    
    def test_login_invalid_credentials(self, client, db_session):
        """Test login with invalid credentials fails."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_CREDENTIALS'
    
    def test_logout_success(self, client, db_session, auth_headers):
        """Test successful logout."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Logged out successfully'
    
    def test_get_profile(self, client, db_session, auth_headers):
        """Test getting user profile."""
        response = client.get('/api/auth/profile', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'] == 'test@example.com'
        assert data['name'] == 'Test User'
    
    def test_update_profile(self, client, db_session, auth_headers):
        """Test updating user profile."""
        response = client.put('/api/auth/profile', 
                            headers=auth_headers,
                            json={'name': 'Updated Name'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Name'


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    def test_get_dashboard_kpis(self, client, db_session, auth_headers):
        """Test getting dashboard KPIs."""
        response = client.get('/api/dashboard/kpis', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_products' in data
        assert 'low_stock_products' in data
        assert 'zero_stock_products' in data
        assert 'pending_receipts' in data
        assert 'pending_delivery_orders' in data
        assert 'pending_transfers' in data


class TestProductEndpoints:
    """Test product endpoints."""
    
    def test_create_product(self, client, db_session, auth_headers, sample_location):
        """Test creating a product."""
        response = client.post('/api/products',
                             headers=auth_headers,
                             json={
                                 'sku': 'PROD-001',
                                 'name': 'Product 1',
                                 'category': 'Category A',
                                 'unit_of_measure': 'pieces',
                                 'low_stock_threshold': 5,
                                 'initial_stock_quantity': 50,
                                 'initial_stock_location_id': str(sample_location.id)
                             })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['sku'] == 'PROD-001'
        assert data['name'] == 'Product 1'
    
    def test_get_product(self, client, db_session, auth_headers, sample_product):
        """Test getting a product by ID."""
        response = client.get(f'/api/products/{sample_product.id}', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['sku'] == 'TEST-001'
        assert data['name'] == 'Test Product'
    
    def test_update_product(self, client, db_session, auth_headers, sample_product):
        """Test updating a product."""
        response = client.put(f'/api/products/{sample_product.id}',
                            headers=auth_headers,
                            json={'name': 'Updated Product'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Product'
        assert data['sku'] == 'TEST-001'  # SKU should not change
    
    def test_search_products(self, client, db_session, auth_headers, sample_product):
        """Test searching products."""
        response = client.get('/api/products/search?q=TEST', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0
        assert data[0]['sku'] == 'TEST-001'


class TestLocationEndpoints:
    """Test location endpoints."""
    
    def test_create_location(self, client, db_session, auth_headers):
        """Test creating a location."""
        response = client.post('/api/locations',
                             headers=auth_headers,
                             json={
                                 'name': 'Warehouse A',
                                 'type': 'warehouse'
                             })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Warehouse A'
        assert data['type'] == 'warehouse'
    
    def test_get_location(self, client, db_session, auth_headers, sample_location):
        """Test getting a location by ID."""
        response = client.get(f'/api/locations/{sample_location.id}', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Main Warehouse'
    
    def test_list_locations(self, client, db_session, auth_headers, sample_location):
        """Test listing locations."""
        response = client.get('/api/locations', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0


class TestStockEndpoints:
    """Test stock endpoints."""
    
    def test_get_stock(self, client, db_session, auth_headers, sample_product, sample_location):
        """Test getting stock for a product at a location."""
        response = client.get(f'/api/stock/{sample_product.id}/{sample_location.id}',
                            headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['quantity'] == 100
    
    def test_get_stock_by_product(self, client, db_session, auth_headers, sample_product):
        """Test getting stock across all locations for a product."""
        response = client.get(f'/api/stock/product/{sample_product.id}',
                            headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0
        assert data[0]['quantity'] == 100


class TestDocumentEndpoints:
    """Test document endpoints."""
    
    def test_create_receipt(self, client, db_session, auth_headers, sample_product, sample_location):
        """Test creating a receipt."""
        response = client.post('/api/documents/receipts',
                             headers=auth_headers,
                             json={
                                 'supplier_name': 'Supplier A',
                                 'supplier_contact': 'contact@supplier.com',
                                 'items': [{
                                     'product_id': str(sample_product.id),
                                     'location_id': str(sample_location.id),
                                     'expected_quantity': 50,
                                     'received_quantity': 50
                                 }]
                             })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['supplier_name'] == 'Supplier A'
        assert data['status'] == 'pending'
    
    def test_create_delivery_order(self, client, db_session, auth_headers, sample_product, sample_location):
        """Test creating a delivery order."""
        response = client.post('/api/documents/delivery-orders',
                             headers=auth_headers,
                             json={
                                 'customer_name': 'Customer A',
                                 'customer_contact': 'contact@customer.com',
                                 'items': [{
                                     'product_id': str(sample_product.id),
                                     'location_id': str(sample_location.id),
                                     'requested_quantity': 10,
                                     'delivered_quantity': 10
                                 }]
                             })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['customer_name'] == 'Customer A'
        assert data['status'] == 'pending'
    
    def test_create_transfer(self, client, db_session, auth_headers, sample_product, sample_location):
        """Test creating a transfer."""
        # Create a second location
        location_manager = LocationManager(db_session)
        dest_location = location_manager.create_location(
            name="Warehouse B",
            location_type="warehouse"
        )
        
        response = client.post('/api/documents/transfers',
                             headers=auth_headers,
                             json={
                                 'source_location_id': str(sample_location.id),
                                 'destination_location_id': str(dest_location.id),
                                 'product_id': str(sample_product.id),
                                 'quantity': 20
                             })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['quantity'] == 20
        assert data['status'] == 'pending'
    
    def test_list_documents(self, client, db_session, auth_headers, sample_product, sample_location):
        """Test listing documents."""
        # Create a receipt first
        client.post('/api/documents/receipts',
                   headers=auth_headers,
                   json={
                       'supplier_name': 'Supplier A',
                       'items': [{
                           'product_id': str(sample_product.id),
                           'location_id': str(sample_location.id),
                           'expected_quantity': 50,
                           'received_quantity': 50
                       }]
                   })
        
        response = client.get('/api/documents', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0


class TestAuthenticationRequired:
    """Test that endpoints require authentication."""
    
    def test_products_requires_auth(self, client):
        """Test that product endpoints require authentication."""
        response = client.get('/api/products/search?q=test')
        assert response.status_code == 401
    
    def test_dashboard_requires_auth(self, client):
        """Test that dashboard endpoints require authentication."""
        response = client.get('/api/dashboard/kpis')
        assert response.status_code == 401
    
    def test_locations_requires_auth(self, client):
        """Test that location endpoints require authentication."""
        response = client.get('/api/locations')
        assert response.status_code == 401
