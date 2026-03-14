# Troubleshooting: Products Not Displaying

## Issue
After creating a product, it doesn't appear in the product list or in the dropdowns for receipts/deliveries.

## What Was Fixed

### 1. **Automatic Tab Switching**
- After creating a product, the app now automatically switches to the Products tab
- After creating a location, the app now automatically switches to the Locations tab
- After creating a receipt/delivery, the app switches to the respective tab

### 2. **Better Error Messages**
- Added detailed error messages in alerts
- Added console logging for debugging
- Shows specific error details from the API

### 3. **Form Clearing**
- All form fields are now properly cleared after submission
- Prevents duplicate submissions

## How to Debug

### Step 1: Check Browser Console
1. Open your browser (Chrome/Edge/Firefox)
2. Press `F12` to open Developer Tools
3. Go to the "Console" tab
4. Try creating a product
5. Look for any error messages in red

### Step 2: Check Network Tab
1. In Developer Tools, go to "Network" tab
2. Try creating a product
3. Look for the POST request to `/api/products`
4. Click on it and check:
   - **Status Code**: Should be 201 (Created)
   - **Response**: Should show the created product
   - **Request Payload**: Should show your product data

### Step 3: Check Database
Run this command to see what's actually in the database:
```bash
python check_database.py
```

This will show:
- How many users exist
- How many products exist
- How many locations exist

### Step 4: Check API Directly
You can test the API directly using curl or the test script:
```bash
python test_api_calls.py
```

## Common Issues & Solutions

### Issue 1: "Authorization header is required"
**Problem:** Not logged in or session expired

**Solution:**
1. Refresh the page
2. Log out and log back in
3. Check if `sessionToken` exists in browser localStorage (F12 → Application → Local Storage)

### Issue 2: Products created but not showing
**Problem:** Frontend not refreshing properly

**Solution:**
1. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache
3. Check browser console for JavaScript errors

### Issue 3: "Failed to add product" error
**Problem:** Validation error or duplicate SKU

**Solution:**
1. Check the error message in the alert
2. Make sure SKU is unique
3. Fill in all required fields (SKU, Name, Category, Unit)

### Issue 4: Dropdowns empty in Receipt/Delivery modals
**Problem:** Products/locations not loading into dropdowns

**Solution:**
1. Make sure you have at least one product created
2. Make sure you have at least one location created
3. Check browser console for API errors
4. Try refreshing the page

## Testing Workflow

### Complete Test Sequence:
1. **Create a Location**
   - Go to Locations tab
   - Click "+ Add Location"
   - Enter name (e.g., "Main Warehouse")
   - Select type (e.g., "warehouse")
   - Click "Add Location"
   - ✅ Should see it in the Locations list

2. **Create a Product**
   - Go to Products tab
   - Click "+ Add Product"
   - Enter SKU (e.g., "PROD001")
   - Enter Name (e.g., "Test Product")
   - Enter Category (e.g., "Electronics")
   - Enter Unit (e.g., "pieces")
   - Optionally: Set threshold and initial stock
   - Click "Add Product"
   - ✅ Should see it in the Products list

3. **Create a Receipt**
   - Go to Receipts tab
   - Click "+ Create Receipt"
   - Enter Supplier Name
   - Select the product you created
   - Select the location you created
   - Enter quantity
   - Click "Create Receipt"
   - ✅ Should see it in the Receipts list
   - Click "Validate" to add stock

4. **Create a Delivery**
   - Go to Deliveries tab
   - Click "+ Create Delivery"
   - Enter Customer Name
   - Select the product
   - Select the location
   - Enter quantity (must be ≤ available stock)
   - Click "Create Delivery"
   - ✅ Should see it in the Deliveries list
   - Click "Validate" to remove stock

## API Endpoints Reference

### Products
- `POST /api/products` - Create product
- `GET /api/products/search?q=` - List all products
- `GET /api/products/<id>` - Get specific product

### Locations
- `POST /api/locations` - Create location
- `GET /api/locations` - List all locations

### Documents
- `POST /api/documents/receipts` - Create receipt
- `POST /api/documents/delivery-orders` - Create delivery
- `GET /api/documents?document_type=receipt` - List receipts
- `GET /api/documents?document_type=delivery_order` - List deliveries

## Still Having Issues?

### Check Server Logs
Look at the terminal where you ran `python run_flask.py` for any error messages.

### Restart the Server
```bash
# Stop the server (Ctrl+C)
# Start it again
python run_flask.py
```

### Check Database File
Make sure `core_inventory.db` exists in your project root.

### Reinitialize Database (CAUTION: Deletes all data)
```bash
# Backup first if you have important data
python init_database.py
```

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari

## Quick Fixes

### Fix 1: Clear Everything and Start Fresh
```bash
# Stop the server
# Delete the database
del core_inventory.db  # Windows
rm core_inventory.db   # Linux/Mac

# Reinitialize
python init_database.py

# Start server
python run_flask.py
```

### Fix 2: Hard Refresh Browser
- Windows: `Ctrl + F5`
- Mac: `Cmd + Shift + R`
- Or: Clear browser cache completely

### Fix 3: Check if Server is Running
Open http://localhost:5000/health in your browser.
Should see: `{"status": "healthy", "timestamp": "..."}`

## Contact/Support

If you're still having issues:
1. Check the browser console (F12)
2. Check the server terminal output
3. Run `python check_database.py` to see database contents
4. Share any error messages you see
