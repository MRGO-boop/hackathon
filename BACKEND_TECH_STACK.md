# CoreInventory Backend Technology Stack

## Overview
Your CoreInventory system uses a **Python-based backend** with a clean, component-driven architecture.

---

## Core Technologies

### 1. **Web Framework: Flask**
- **Flask** - Lightweight Python web framework
- **Flask-CORS** - Cross-Origin Resource Sharing support for frontend communication
- RESTful API architecture with 40+ endpoints
- Decorators for authentication and error handling

### 2. **Database: SQLite + SQLAlchemy**
- **SQLite** - Lightweight, file-based relational database (`core_inventory.db`)
- **SQLAlchemy** - Python ORM (Object-Relational Mapping) for database operations
- **Alembic** - Database migration tool for schema versioning

### 3. **Authentication & Security**
- **bcrypt** - Password hashing (via `passlib`)
- Session-based authentication with expiry
- OTP (One-Time Password) for password resets
- JWT-style session tokens

### 4. **Testing Framework**
- **pytest** - Main testing framework
- **Hypothesis** - Property-based testing for correctness validation
- 100+ test cases covering all components
- Integration tests and property-based tests

### 5. **Environment Management**
- **python-dotenv** - Environment variable management
- **virtualenv** - Python virtual environment isolation

---

## Backend Architecture

### Component-Based Design
Your backend follows a **modular component architecture**:

```
core_inventory/
├── components/           # Business logic components
│   ├── authenticator.py      # User authentication & sessions
│   ├── product_manager.py    # Product CRUD operations
│   ├── location_manager.py   # Location management
│   ├── stock_manager.py      # Stock tracking & queries
│   ├── document_manager.py   # Receipt/Delivery/Transfer documents
│   ├── validator.py          # Document validation & stock updates
│   ├── history_logger.py     # Movement history & audit trail
│   └── dashboard.py          # KPI calculations & analytics
│
├── models/              # Database models (SQLAlchemy)
│   ├── user.py
│   ├── product.py
│   ├── location.py
│   ├── stock.py
│   ├── receipt.py
│   ├── delivery_order.py
│   ├── transfer.py
│   ├── stock_adjustment.py
│   └── move_history.py
│
├── database.py          # Database connection & session management
├── validation.py        # Input validation utilities
└── errors.py           # Custom exception classes
```

---

## Key Backend Features

### 1. **RESTful API (app.py)**
- 40+ REST endpoints organized by domain
- Authentication middleware (`@require_auth`)
- Error handling decorator (`@handle_errors`)
- JSON request/response format
- CORS enabled for frontend communication

### 2. **Database Models (SQLAlchemy ORM)**
```python
# Example: Product Model
class Product(Base):
    __tablename__ = 'products'
    id = Column(UUID, primary_key=True)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    # ... relationships and methods
```

### 3. **Component Pattern**
Each component is self-contained with:
- Business logic encapsulation
- Database session management
- Custom error handling
- Validation logic

Example:
```python
class ProductManager:
    def __init__(self, db_session):
        self.db = db_session
    
    def create_product(self, sku, name, ...):
        # Validation
        # Business logic
        # Database operations
        return product
```

### 4. **Error Handling System**
Custom exception hierarchy:
- `CoreInventoryError` (base)
- `AuthenticationError`
- `ProductError`
- `StockError`
- `ValidationError`
- etc.

Each error includes:
- Error code
- Message
- Context (additional details)
- Timestamp

### 5. **Database Migrations (Alembic)**
```
migrations/
└── versions/
    └── 3d74c238d79f_add_sessions_and_password_resets_tables.py
```
- Version-controlled schema changes
- Automatic migration generation
- Rollback support

---

## API Endpoint Categories

### Authentication (`/api/auth/*`)
- Signup, Login, Logout
- Password reset with OTP
- Profile management
- Session validation

### Products (`/api/products/*`)
- CRUD operations
- Search and filtering
- Multi-criteria filtering

### Locations (`/api/locations/*`)
- Create, update, archive
- Hierarchical location support
- List with filtering

### Stock (`/api/stock/*`)
- Get stock by product/location
- Low stock alerts
- Stock queries

### Documents (`/api/documents/*`)
- Receipts (incoming goods)
- Delivery orders (outgoing goods)
- Transfers (between locations)
- Stock adjustments
- Document validation

### History (`/api/history/*`)
- Movement history
- Stock ledger
- Export functionality (CSV/JSON)

### Dashboard (`/api/dashboard/*`)
- KPI calculations
- Real-time analytics

---

## Database Schema

### Core Tables
1. **users** - User accounts and authentication
2. **sessions** - Active user sessions
3. **password_resets** - OTP tokens for password reset
4. **products** - Product catalog
5. **locations** - Storage locations (hierarchical)
6. **stock** - Current stock levels (product × location)
7. **receipts** - Incoming goods documents
8. **receipt_items** - Line items for receipts
9. **delivery_orders** - Outgoing goods documents
10. **delivery_order_items** - Line items for deliveries
11. **transfers** - Stock transfers between locations
12. **stock_adjustments** - Inventory adjustments
13. **move_history** - Complete audit trail of all movements

---

## Testing Strategy

### 1. **Unit Tests**
- Test individual component methods
- Mock database interactions
- Fast execution

### 2. **Integration Tests**
- Test component interactions
- Real database operations
- End-to-end workflows

### 3. **Property-Based Tests (Hypothesis)**
- Automated test case generation
- Correctness properties validation
- Edge case discovery

Example property:
```python
@given(st.integers(min_value=1, max_value=1000))
def test_stock_never_negative(quantity):
    # Property: Stock should never go negative
    assert stock >= 0
```

---

## Configuration & Deployment

### Environment Variables (.env)
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///core_inventory.db
```

### Running the Backend
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run Flask server
python run_flask.py

# Or use the batch file
START_COREINVENTORY.bat
```

### Database Initialization
```bash
python init_database.py
```

---

## Performance Considerations

1. **Database Indexing**
   - Primary keys (UUID)
   - Foreign keys
   - Unique constraints (SKU, email)

2. **Query Optimization**
   - SQLAlchemy lazy loading
   - Efficient joins
   - Filtered queries

3. **Session Management**
   - Connection pooling
   - Proper session cleanup
   - Context managers

---

## Security Features

1. **Password Security**
   - bcrypt hashing
   - Salt generation
   - No plaintext storage

2. **Session Security**
   - Expiring sessions (24 hours)
   - Session validation on each request
   - Secure token generation

3. **Input Validation**
   - Type checking
   - Range validation
   - SQL injection prevention (ORM)

4. **Error Handling**
   - No sensitive data in error messages
   - Structured error responses
   - Logging for debugging

---

## Summary

**Backend Stack:**
- **Language:** Python 3.x
- **Framework:** Flask (REST API)
- **Database:** SQLite + SQLAlchemy ORM
- **Migrations:** Alembic
- **Testing:** pytest + Hypothesis
- **Security:** bcrypt, session tokens
- **Architecture:** Component-based, modular design

**Key Strengths:**
✅ Clean separation of concerns
✅ Comprehensive test coverage
✅ RESTful API design
✅ Robust error handling
✅ Scalable component architecture
✅ Property-based testing for correctness
✅ Complete audit trail
✅ Type-safe operations
