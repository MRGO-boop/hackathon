# CoreInventory - Complete System Guide

## 🎉 Congratulations!

Your complete CoreInventory system is ready with both backend API and frontend interface!

## 🚀 Quick Start

### Option 1: One-Click Start (Easiest)
```bash
START_COREINVENTORY.bat
```
This will:
- Start the API server
- Open the frontend in your browser automatically
- Everything ready to use!

### Option 2: Manual Start
```bash
# Terminal 1 - Start server
RUN_SERVER.bat

# Then open browser to:
http://localhost:5000
```

## 📱 Using the Frontend

### 1. First Time Setup
1. Open http://localhost:5000
2. Click "Sign up" to create an account
3. Enter your name, email, and password
4. Login with your credentials

### 2. Add Locations
1. Go to "Locations" tab
2. Click "+ Add Location"
3. Enter location name (e.g., "Main Warehouse")
4. Select type (warehouse, rack, or floor_area)
5. Click "Add Location"

### 3. Add Products
1. Go to "Products" tab
2. Click "+ Add Product"
3. Fill in product details:
   - SKU (unique identifier)
   - Product name
   - Category
   - Unit of measure (pieces, kg, etc.)
   - Low stock threshold (optional)
   - Initial stock quantity (optional)
   - Location (if adding initial stock)
4. Click "Add Product"

### 4. Process Receipts (Incoming Goods)
1. Go to "Receipts" tab
2. Click "+ Create Receipt"
3. Enter supplier information
4. Add products and quantities
5. Click "Validate" to update stock

### 5. Process Deliveries (Outgoing Goods)
1. Go to "Deliveries" tab
2. Click "+ Create Delivery"
3. Enter customer information
4. Add products and quantities
5. Click "Validate" to decrease stock

### 6. View Dashboard
- See total products
- Monitor low stock alerts
- Track pending documents
- Real-time updates

### 7. View History
- See all stock movements
- Track who made changes
- Audit trail for compliance

## 🏗️ System Architecture

```
┌─────────────────────────────────────┐
│         Frontend (Browser)          │
│    HTML + CSS + JavaScript          │
│    http://localhost:5000            │
└─────────────┬───────────────────────┘
              │
              │ REST API Calls
              │
┌─────────────▼───────────────────────┐
│      Flask API Server               │
│      http://localhost:5000/api      │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  8 Core Components:          │  │
│  │  - Authenticator             │  │
│  │  - Product Manager           │  │
│  │  - Location Manager          │  │
│  │  - Stock Manager             │  │
│  │  - Document Manager          │  │
│  │  - Validator                 │  │
│  │  - History Logger            │  │
│  │  - Dashboard                 │  │
│  └──────────────────────────────┘  │
└─────────────┬───────────────────────┘
              │
              │ SQLAlchemy ORM
              │
┌─────────────▼───────────────────────┐
│      SQLite Database                │
│      coreinventory.db               │
│                                     │
│  14 Tables:                         │
│  - users, products, locations       │
│  - stock, receipts, deliveries      │
│  - transfers, adjustments           │
│  - move_history, stock_ledger       │
│  - sessions, password_resets        │
│  - receipt_items, delivery_items    │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
hackathon/
├── frontend/                  # Web interface
│   ├── index.html            # Main HTML
│   ├── styles.css            # Styling
│   ├── app.js                # JavaScript logic
│   └── README.md             # Frontend docs
│
├── core_inventory/           # Backend components
│   ├── components/           # 8 core components
│   ├── models/               # Database models
│   ├── database.py           # DB configuration
│   ├── errors.py             # Error handling
│   └── validation.py         # Input validation
│
├── tests/                    # Test suite
│   ├── test_api.py          # API integration tests
│   ├── test_*.py            # Component tests
│   └── test_*_properties.py # Property-based tests
│
├── migrations/               # Database migrations
├── docs/                     # Documentation
├── app.py                    # Flask application
├── run_flask.py             # Server runner
├── init_database.py         # DB initialization
├── test_api_calls.py        # API test script
│
├── START_COREINVENTORY.bat  # One-click startup
├── RUN_SERVER.bat           # Server only
├── requirements.txt         # Python dependencies
├── .env                     # Configuration
│
└── .kiro/specs/             # Specification documents
    └── core-inventory/
        ├── requirements.md   # Requirements
        ├── design.md        # Design document
        └── tasks.md         # Implementation tasks
```

## 🔧 Configuration

### Environment Variables (.env)
```
DATABASE_URL=sqlite:///./coreinventory.db
SECRET_KEY=dev-secret-key-change-in-production
```

### API Base URL (frontend/app.js)
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## 🧪 Testing

### Test the API
```bash
python test_api_calls.py
```

### Run all tests
```bash
pytest tests/ -v
```

### Test specific component
```bash
pytest tests/test_product_manager.py -v
```

## 📊 Features Implemented

### ✅ Authentication
- User signup and login
- Session management
- Password reset (OTP-based)
- Secure logout

### ✅ Product Management
- Create, read, update products
- SKU uniqueness enforcement
- Search and filtering
- Low stock alerts
- Initial stock tracking

### ✅ Location Management
- Create warehouses, racks, floor areas
- Location hierarchy
- Archive locations
- Stock validation before deletion

### ✅ Stock Management
- Real-time stock tracking
- Multi-location support
- Low stock alerts
- Stock availability checks

### ✅ Document Processing
- **Receipts** - Incoming goods
- **Delivery Orders** - Outgoing goods
- **Transfers** - Between locations
- **Stock Adjustments** - Physical counts

### ✅ Validation & History
- Document validation workflow
- Atomic stock updates
- Complete audit trail
- Move history tracking
- Stock ledger with running balance

### ✅ Dashboard
- Total products count
- Low stock alerts
- Zero stock alerts
- Pending documents count
- Real-time updates

### ✅ Reporting
- Move history with filters
- Stock ledger
- Export capabilities
- Date range filtering

## 🔒 Security Features

- Password hashing (bcrypt)
- Session-based authentication
- Authorization checks
- Input validation
- SQL injection prevention (ORM)
- CORS configuration

## 📈 Performance

- Indexed database queries
- Efficient search (< 500ms for 100k products)
- Optimized stock lookups
- Cached dashboard KPIs

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Use different port in run_flask.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database errors
```bash
# Recreate database
del coreinventory.db
python init_database.py
```

### Frontend can't connect
- Make sure server is running
- Check API_BASE_URL in app.js
- Check browser console for errors

### Module not found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 🚀 Production Deployment

### 1. Update Configuration
- Set strong SECRET_KEY in .env
- Use PostgreSQL instead of SQLite
- Disable debug mode

### 2. Use Production Server
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Set up HTTPS
- Use nginx or Apache as reverse proxy
- Get SSL certificate (Let's Encrypt)

### 4. Environment Variables
```
DATABASE_URL=postgresql://user:pass@localhost/coreinventory
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
```

## 📚 Documentation

- **API Documentation**: `API_DOCUMENTATION.md`
- **Quick Start Guide**: `QUICKSTART.md`
- **Requirements**: `.kiro/specs/core-inventory/requirements.md`
- **Design Document**: `.kiro/specs/core-inventory/design.md`
- **Frontend Guide**: `frontend/README.md`

## 🎯 Next Steps

1. **Customize the frontend** - Update colors, branding
2. **Add more features** - Reports, analytics, exports
3. **Deploy to production** - Make it accessible online
4. **Mobile app** - Build React Native or Flutter app
5. **Advanced features** - Barcode scanning, notifications

## 💡 Tips

- Use Chrome DevTools to debug frontend issues
- Check browser console for JavaScript errors
- Monitor Flask logs for API errors
- Use Postman for API testing
- Regular database backups

## 🆘 Support

- Check `API_DOCUMENTATION.md` for endpoint details
- Review `frontend/README.md` for UI guidance
- See `FIX_SQLITE_ISSUE.md` for database problems
- Run `python check_environment.py` to verify setup

---

**Congratulations! You now have a fully functional inventory management system!** 🎉

Start the system with `START_COREINVENTORY.bat` and begin managing your inventory!
