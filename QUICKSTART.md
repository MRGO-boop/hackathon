# CoreInventory API Quick Start Guide

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=sqlite:///./coreinventory.db
   SECRET_KEY=your-secret-key-change-in-production
   ```

3. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

## Running the API Server

### Option 1: Using the run script
```bash
python run_api.py
```

### Option 2: Direct execution
```bash
python app.py
```

The API will be available at: `http://localhost:5000`

## Testing the API

### Run all tests
```bash
pytest tests/test_api.py -v
```

### Run specific test class
```bash
pytest tests/test_api.py::TestAuthenticationEndpoints -v
```

### Check API health
```bash
curl http://localhost:5000/health
```

## Quick API Usage Example

### 1. Create a user account
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456",
    "name": "Admin User"
  }'
```

### 2. Login to get session token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456"
  }'
```

**Save the `session_id` from the response!**

### 3. Create a location
```bash
curl -X POST http://localhost:5000/api/locations \
  -H "Authorization: Bearer YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Warehouse",
    "type": "warehouse"
  }'
```

**Save the location `id` from the response!**

### 4. Create a product with initial stock
```bash
curl -X POST http://localhost:5000/api/products \
  -H "Authorization: Bearer YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "Dell Laptop",
    "category": "Electronics",
    "unit_of_measure": "pieces",
    "low_stock_threshold": 5,
    "initial_stock_quantity": 50,
    "initial_stock_location_id": "YOUR_LOCATION_ID"
  }'
```

### 5. View dashboard KPIs
```bash
curl -X GET http://localhost:5000/api/dashboard/kpis \
  -H "Authorization: Bearer YOUR_SESSION_ID"
```

### 6. Search for products
```bash
curl -X GET "http://localhost:5000/api/products/search?q=Laptop" \
  -H "Authorization: Bearer YOUR_SESSION_ID"
```

### 7. Create a receipt (incoming goods)
```bash
curl -X POST http://localhost:5000/api/documents/receipts \
  -H "Authorization: Bearer YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Tech Supplier Inc",
    "supplier_contact": "supplier@tech.com",
    "items": [
      {
        "product_id": "YOUR_PRODUCT_ID",
        "location_id": "YOUR_LOCATION_ID",
        "expected_quantity": 20,
        "received_quantity": 20
      }
    ]
  }'
```

**Save the receipt `id` from the response!**

### 8. Validate the receipt (updates stock)
```bash
curl -X POST http://localhost:5000/api/documents/receipts/YOUR_RECEIPT_ID/validate \
  -H "Authorization: Bearer YOUR_SESSION_ID"
```

### 9. Check stock levels
```bash
curl -X GET http://localhost:5000/api/stock/YOUR_PRODUCT_ID/YOUR_LOCATION_ID \
  -H "Authorization: Bearer YOUR_SESSION_ID"
```

### 10. View move history
```bash
curl -X GET http://localhost:5000/api/history/movements \
  -H "Authorization: Bearer YOUR_SESSION_ID"
```

## API Endpoints Overview

### Authentication
- `POST /api/auth/signup` - Create user account
- `POST /api/auth/login` - Login and get session
- `POST /api/auth/logout` - Logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update profile
- `PUT /api/auth/password` - Change password
- `POST /api/auth/password-reset/request` - Request password reset
- `POST /api/auth/password-reset/confirm` - Confirm password reset

### Dashboard
- `GET /api/dashboard/kpis` - Get all KPIs

### Products
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product
- `PUT /api/products/{id}` - Update product
- `GET /api/products/search` - Search products
- `GET /api/products/filter` - Filter products

### Locations
- `POST /api/locations` - Create location
- `GET /api/locations/{id}` - Get location
- `PUT /api/locations/{id}` - Update location
- `POST /api/locations/{id}/archive` - Archive location
- `GET /api/locations` - List locations

### Stock
- `GET /api/stock/{product_id}/{location_id}` - Get stock
- `GET /api/stock/product/{product_id}` - Get stock by product
- `GET /api/stock/low-stock` - Get low stock products

### Documents
- `POST /api/documents/receipts` - Create receipt
- `POST /api/documents/receipts/{id}/validate` - Validate receipt
- `POST /api/documents/delivery-orders` - Create delivery order
- `POST /api/documents/delivery-orders/{id}/validate` - Validate delivery order
- `POST /api/documents/transfers` - Create transfer
- `POST /api/documents/transfers/{id}/validate` - Validate transfer
- `POST /api/documents/stock-adjustments` - Create stock adjustment
- `POST /api/documents/stock-adjustments/{id}/validate` - Validate adjustment
- `GET /api/documents` - List documents
- `GET /api/documents/{type}/{id}` - Get document

### History
- `GET /api/history/movements` - Get move history
- `GET /api/history/ledger` - Get stock ledger
- `GET /api/history/ledger/export` - Export ledger

## Complete Documentation

For detailed API documentation including request/response formats, error codes, and more examples, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Troubleshooting

### Database not found
```bash
alembic upgrade head
```

### Port already in use
Change the port in `app.py` or `run_api.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

### Authentication errors
Make sure to include the session token in the Authorization header:
```
Authorization: Bearer YOUR_SESSION_ID
```

### Module not found errors
```bash
pip install -r requirements.txt
```

## Development

### Running in development mode
The API runs in debug mode by default, which provides:
- Auto-reload on code changes
- Detailed error messages
- Request logging

### Running tests with coverage
```bash
pytest tests/test_api.py --cov=app --cov-report=html
```

### Viewing test coverage
Open `htmlcov/index.html` in your browser after running coverage.

## Production Deployment

For production deployment:

1. **Set a strong SECRET_KEY** in `.env`
2. **Use a production database** (PostgreSQL recommended)
3. **Disable debug mode** in `app.py`:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```
4. **Use a production WSGI server** like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
5. **Set up HTTPS** using a reverse proxy (nginx, Apache)
6. **Configure CORS** appropriately for your frontend domain

## Support

For issues or questions:
- Check the API documentation: `API_DOCUMENTATION.md`
- Review the design document: `.kiro/specs/core-inventory/design.md`
- Review the requirements: `.kiro/specs/core-inventory/requirements.md`
