# CoreInventory - Final Setup Instructions

## ✅ Database is Ready!
All 14 tables have been created successfully.

## 🚀 To Start the API:

### Option 1: Manual (Recommended)
Open TWO terminal windows:

**Terminal 1 - Start Server:**
```bash
cd C:\Users\Lenovo\Desktop\hackathon
venv\Scripts\activate
python run_flask.py
```
Leave this running!

**Terminal 2 - Test API:**
```bash
cd C:\Users\Lenovo\Desktop\hackathon
venv\Scripts\activate
python test_api_calls.py
```

### Option 2: Quick Test
If the server is already running in another terminal, just run:
```bash
python test_api_calls.py
```

## 📊 What the Test Does:
1. Creates a user account
2. Logs in and gets a session token
3. Creates a warehouse location
4. Creates a product with 50 units of stock
5. Creates and validates a receipt (+20 units)
6. Shows final stock: 70 units
7. Displays move history

## 🌐 Access the API:
- Health Check: http://localhost:5000/health
- API Base: http://localhost:5000/api
- Documentation: See API_DOCUMENTATION.md

## 🎯 Next Steps:
- Use Postman to test more endpoints
- Try creating delivery orders, transfers, adjustments
- Build a frontend application
- Deploy to production

## ❓ Troubleshooting:
- If "Cannot connect": Make sure server is running in another terminal
- If "500 error": Database tables are created, just restart the server
- If port 5000 busy: Change port in run_flask.py

Good luck! 🎉
