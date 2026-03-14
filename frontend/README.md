# CoreInventory Frontend

A clean, modern web interface for the CoreInventory API.

## Features

✅ **Dashboard** - View key metrics at a glance
✅ **Products** - Manage products with search functionality
✅ **Locations** - Manage warehouse locations
✅ **Receipts** - Process incoming goods
✅ **Deliveries** - Process outgoing goods
✅ **History** - View all stock movements
✅ **Authentication** - Secure login/signup

## How to Use

1. **Start the API server** (if not already running):
   ```bash
   RUN_SERVER.bat
   ```

2. **Open the frontend**:
   - Go to: http://localhost:5000
   - Or open `frontend/index.html` directly in your browser

3. **Create an account**:
   - Click "Sign up"
   - Enter your details
   - Login with your credentials

4. **Start managing inventory**:
   - Add locations (warehouses, racks, etc.)
   - Add products with initial stock
   - Create receipts for incoming goods
   - Create delivery orders for outgoing goods
   - View real-time dashboard updates

## Technology Stack

- **Pure HTML/CSS/JavaScript** - No frameworks needed
- **Responsive Design** - Works on desktop and mobile
- **REST API Integration** - Connects to Flask backend
- **Local Storage** - Persists session across page reloads

## API Endpoints Used

- `/api/auth/*` - Authentication
- `/api/dashboard/kpis` - Dashboard metrics
- `/api/products/*` - Product management
- `/api/locations/*` - Location management
- `/api/documents/*` - Document management
- `/api/history/*` - Movement history

## Customization

You can customize the look and feel by editing:
- `styles.css` - Colors, fonts, layout
- `app.js` - Functionality and API calls
- `index.html` - Structure and content

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with ES6 support

Enjoy using CoreInventory! 🎉
