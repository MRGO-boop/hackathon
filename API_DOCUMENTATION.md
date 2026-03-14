# CoreInventory REST API Documentation

## Overview

The CoreInventory REST API provides a complete interface for managing inventory operations including authentication, product management, stock tracking, document processing, and reporting.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Most endpoints require authentication using a session token obtained through the login endpoint.

### Authentication Header

Include the session token in the `Authorization` header:

```
Authorization: Bearer <session_id>
```

## API Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Authentication Endpoints

### POST /api/auth/signup

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /api/auth/login

Authenticate and create a session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

### POST /api/auth/logout

Terminate the current session.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

### POST /api/auth/password-reset/request

Request a password reset OTP.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset OTP sent",
  "otp": "123456"
}
```

### POST /api/auth/password-reset/confirm

Reset password using OTP.

**Request Body:**
```json
{
  "otp": "123456",
  "new_password": "newpassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

### GET /api/auth/profile

Get current user profile.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe"
}
```

### PUT /api/auth/profile

Update user profile.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`

### PUT /api/auth/password

Change password.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

**Response:** `200 OK`

---

## Dashboard Endpoints

### GET /api/dashboard/kpis

Get all dashboard KPIs.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`
```json
{
  "total_products": 150,
  "low_stock_products": 12,
  "zero_stock_products": 5,
  "pending_receipts": 8,
  "pending_delivery_orders": 15,
  "pending_transfers": 3
}
```

---

## Product Endpoints

### POST /api/products

Create a new product.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "sku": "PROD-001",
  "name": "Product Name",
  "category": "Category A",
  "unit_of_measure": "pieces",
  "low_stock_threshold": 10,
  "initial_stock_quantity": 100,
  "initial_stock_location_id": "location-uuid"
}
```

**Response:** `201 Created`

### GET /api/products/{product_id}

Get a product by ID.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### PUT /api/products/{product_id}

Update a product (SKU cannot be changed).

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "name": "Updated Product Name",
  "category": "Category B",
  "unit_of_measure": "kg",
  "low_stock_threshold": 15
}
```

**Response:** `200 OK`

### GET /api/products/search

Search products by SKU or name.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `q` - Search query (SKU or name)

**Response:** `200 OK`

### GET /api/products/filter

Filter products by multiple criteria.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `category` - Filter by category
- `sku` - Filter by SKU
- `name` - Filter by name (partial match)
- `unit_of_measure` - Filter by unit of measure

**Response:** `200 OK`

---

## Location Endpoints

### POST /api/locations

Create a new location.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "name": "Warehouse A",
  "type": "warehouse",
  "parent_id": "parent-location-uuid"
}
```

**Response:** `201 Created`

### GET /api/locations/{location_id}

Get a location by ID.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### PUT /api/locations/{location_id}

Update a location.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "name": "Updated Warehouse Name",
  "type": "warehouse",
  "parent_id": "new-parent-uuid"
}
```

**Response:** `200 OK`

### POST /api/locations/{location_id}/archive

Archive a location (soft delete).

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### GET /api/locations

List all locations.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `include_archived` - Include archived locations (true/false)

**Response:** `200 OK`

---

## Stock Endpoints

### GET /api/stock/{product_id}/{location_id}

Get stock for a product at a specific location.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity": 150
}
```

### GET /api/stock/product/{product_id}

Get stock across all locations for a product.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`
```json
[
  {
    "location_id": "uuid",
    "location_name": "Warehouse A",
    "quantity": 100
  },
  {
    "location_id": "uuid",
    "location_name": "Warehouse B",
    "quantity": 50
  }
]
```

### GET /api/stock/low-stock

Get products with low stock.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `threshold` - Optional global threshold for products without configured threshold

**Response:** `200 OK`

---

## Document Endpoints

### Receipts

#### POST /api/documents/receipts

Create a new receipt.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "supplier_name": "Supplier A",
  "supplier_contact": "contact@supplier.com",
  "items": [
    {
      "product_id": "uuid",
      "location_id": "uuid",
      "expected_quantity": 100,
      "received_quantity": 100
    }
  ]
}
```

**Response:** `201 Created`

#### POST /api/documents/receipts/{receipt_id}/validate

Validate a receipt and update stock.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### Delivery Orders

#### POST /api/documents/delivery-orders

Create a new delivery order.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "customer_name": "Customer A",
  "customer_contact": "contact@customer.com",
  "items": [
    {
      "product_id": "uuid",
      "location_id": "uuid",
      "requested_quantity": 50,
      "delivered_quantity": 50
    }
  ]
}
```

**Response:** `201 Created`

#### POST /api/documents/delivery-orders/{order_id}/validate

Validate a delivery order and update stock.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### Transfers

#### POST /api/documents/transfers

Create a new transfer.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "source_location_id": "uuid",
  "destination_location_id": "uuid",
  "product_id": "uuid",
  "quantity": 50
}
```

**Response:** `201 Created`

#### POST /api/documents/transfers/{transfer_id}/validate

Validate a transfer and update stock.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### Stock Adjustments

#### POST /api/documents/stock-adjustments

Create a new stock adjustment.

**Headers:** `Authorization: Bearer <session_id>`

**Request Body:**
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "recorded_quantity": 100,
  "physical_quantity": 95,
  "reason": "Physical count discrepancy"
}
```

**Response:** `201 Created`

#### POST /api/documents/stock-adjustments/{adjustment_id}/validate

Validate a stock adjustment and update stock.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

### Document Listing

#### GET /api/documents

List documents with optional filtering.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `document_type` - Filter by type (receipt, delivery_order, transfer, stock_adjustment)
- `status` - Filter by status (pending, validated)
- `location_id` - Filter by location

**Response:** `200 OK`

#### GET /api/documents/{document_type}/{document_id}

Get a specific document.

**Headers:** `Authorization: Bearer <session_id>`

**Response:** `200 OK`

---

## History Endpoints

### GET /api/history/movements

Get move history with optional filtering.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `start_date` - Filter by start date (ISO format)
- `end_date` - Filter by end date (ISO format)
- `product_id` - Filter by product
- `location_id` - Filter by location
- `document_type` - Filter by document type

**Response:** `200 OK`

### GET /api/history/ledger

Get stock ledger with running balance.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `start_date` - Filter by start date (ISO format)
- `end_date` - Filter by end date (ISO format)
- `product_id` - Filter by product
- `location_id` - Filter by location

**Response:** `200 OK`

### GET /api/history/ledger/export

Export stock ledger.

**Headers:** `Authorization: Bearer <session_id>`

**Query Parameters:**
- `format` - Export format (csv or json)
- `start_date` - Filter by start date (ISO format)
- `end_date` - Filter by end date (ISO format)
- `product_id` - Filter by product
- `location_id` - Filter by location

**Response:** `200 OK` with file download

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "context": {
      "field": "value"
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Common Error Codes

- `INVALID_CREDENTIALS` - Invalid email or password
- `SESSION_EXPIRED` - Session has expired
- `MISSING_AUTH` - Authorization header missing
- `INSUFFICIENT_STOCK` - Not enough stock for operation
- `SKU_EXISTS` - SKU already exists
- `PRODUCT_NOT_FOUND` - Product not found
- `LOCATION_NOT_FOUND` - Location not found
- `INVALID_STATUS` - Invalid document status for operation

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Running the API

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Environment Variables

Create a `.env` file:

```
DATABASE_URL=sqlite:///./coreinventory.db
SECRET_KEY=your-secret-key-here
```

### Run the Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Run Tests

```bash
pytest tests/test_api.py -v
```

---

## Example Usage

### Complete Workflow Example

```bash
# 1. Signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","name":"John Doe"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Save the session_id from response

# 3. Create Location
curl -X POST http://localhost:5000/api/locations \
  -H "Authorization: Bearer <session_id>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Main Warehouse","type":"warehouse"}'

# 4. Create Product with Initial Stock
curl -X POST http://localhost:5000/api/products \
  -H "Authorization: Bearer <session_id>" \
  -H "Content-Type: application/json" \
  -d '{"sku":"PROD-001","name":"Product 1","category":"Electronics","unit_of_measure":"pieces","low_stock_threshold":10,"initial_stock_quantity":100,"initial_stock_location_id":"<location_id>"}'

# 5. Get Dashboard KPIs
curl -X GET http://localhost:5000/api/dashboard/kpis \
  -H "Authorization: Bearer <session_id>"

# 6. Create Receipt
curl -X POST http://localhost:5000/api/documents/receipts \
  -H "Authorization: Bearer <session_id>" \
  -H "Content-Type: application/json" \
  -d '{"supplier_name":"Supplier A","items":[{"product_id":"<product_id>","location_id":"<location_id>","expected_quantity":50,"received_quantity":50}]}'

# 7. Validate Receipt
curl -X POST http://localhost:5000/api/documents/receipts/<receipt_id>/validate \
  -H "Authorization: Bearer <session_id>"

# 8. Get Move History
curl -X GET http://localhost:5000/api/history/movements \
  -H "Authorization: Bearer <session_id>"
```
