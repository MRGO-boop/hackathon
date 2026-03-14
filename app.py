"""CoreInventory REST API Application."""
import os
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from core_inventory.database import get_db
from core_inventory.components.authenticator import Authenticator, AuthenticationError
from core_inventory.components.product_manager import ProductManager, ProductError
from core_inventory.components.location_manager import LocationManager, LocationError
from core_inventory.components.stock_manager import StockManager, StockError
from core_inventory.components.document_manager import DocumentManager, DocumentError
from core_inventory.components.validator import Validator, ValidationError
from core_inventory.components.history_logger import HistoryLogger, HistoryError
from core_inventory.components.dashboard import Dashboard, DashboardError

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


# Error handler decorator
def handle_errors(f):
    """Decorator to handle component errors and return appropriate HTTP responses."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AuthenticationError as e:
            return jsonify({
                'error': {
                    'code': e.code,
                    'message': e.message,
                    'context': e.context,
                    'timestamp': e.timestamp
                }
            }), 401 if e.code in ['INVALID_CREDENTIALS', 'SESSION_EXPIRED', 'SESSION_NOT_FOUND'] else 400
        except (ProductError, LocationError, StockError, DocumentError, ValidationError, HistoryError, DashboardError) as e:
            return jsonify({
                'error': {
                    'code': e.code,
                    'message': e.message,
                    'context': e.context,
                    'timestamp': e.timestamp
                }
            }), 400
        except Exception as e:
            return jsonify({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 500
    return decorated_function


# Authentication middleware
def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get('Authorization')
        if not session_id:
            return jsonify({
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header is required',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 401
        
        # Remove 'Bearer ' prefix if present
        if session_id.startswith('Bearer '):
            session_id = session_id[7:]
        
        db = next(get_db())
        try:
            authenticator = Authenticator(db)
            user = authenticator.validate_session(session_id)
            g.user = user
            g.db = db
            return f(*args, **kwargs)
        except AuthenticationError as e:
            return jsonify({
                'error': {
                    'code': e.code,
                    'message': e.message,
                    'context': e.context,
                    'timestamp': e.timestamp
                }
            }), 401
        finally:
            db.close()
    
    return decorated_function


# Serve frontend - MUST BE BEFORE API ROUTES
@app.route('/')
def serve_frontend():
    """Serve the frontend index.html."""
    return send_from_directory('frontend', 'index.html')


@app.route('/styles.css')
def serve_css():
    """Serve CSS file."""
    return send_from_directory('frontend', 'styles.css')


@app.route('/app.js')
def serve_js():
    """Serve JavaScript file."""
    return send_from_directory('frontend', 'app.js')


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat() + 'Z'})


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.route('/api/auth/signup', methods=['POST'])
@handle_errors
def signup():
    """User signup endpoint."""
    data = request.get_json()
    db = next(get_db())
    try:
        authenticator = Authenticator(db)
        user = authenticator.signup(
            email=data.get('email'),
            password=data.get('password'),
            name=data.get('name')
        )
        return jsonify({
            'id': str(user.id),
            'email': user.email,
            'name': user.name,
            'created_at': user.created_at.isoformat()
        }), 201
    finally:
        db.close()


@app.route('/api/auth/login', methods=['POST'])
@handle_errors
def login():
    """User login endpoint."""
    data = request.get_json()
    db = next(get_db())
    try:
        authenticator = Authenticator(db)
        session = authenticator.login(
            email=data.get('email'),
            password=data.get('password')
        )
        return jsonify({
            'session_id': str(session.id),
            'user_id': str(session.user_id),
            'expires_at': session.expires_at.isoformat()
        }), 200
    finally:
        db.close()


@app.route('/api/auth/logout', methods=['POST'])
@handle_errors
def logout():
    """User logout endpoint."""
    session_id = request.headers.get('Authorization', '').replace('Bearer ', '')
    db = next(get_db())
    try:
        authenticator = Authenticator(db)
        authenticator.logout(session_id)
        return jsonify({'message': 'Logged out successfully'}), 200
    finally:
        db.close()


@app.route('/api/auth/password-reset/request', methods=['POST'])
@handle_errors
def request_password_reset():
    """Request password reset endpoint."""
    data = request.get_json()
    db = next(get_db())
    try:
        authenticator = Authenticator(db)
        otp = authenticator.request_password_reset(email=data.get('email'))
        # In production, this would send an email. For now, return OTP for testing
        return jsonify({'message': 'Password reset OTP sent', 'otp': otp}), 200
    finally:
        db.close()


@app.route('/api/auth/password-reset/confirm', methods=['POST'])
@handle_errors
def reset_password():
    """Reset password with OTP endpoint."""
    data = request.get_json()
    db = next(get_db())
    try:
        authenticator = Authenticator(db)
        authenticator.reset_password(
            otp=data.get('otp'),
            new_password=data.get('new_password')
        )
        return jsonify({'message': 'Password reset successfully'}), 200
    finally:
        db.close()


@app.route('/api/auth/profile', methods=['GET'])
@require_auth
@handle_errors
def get_profile():
    """Get user profile endpoint."""
    authenticator = Authenticator(g.db)
    profile = authenticator.get_profile(str(g.user.id))
    return jsonify(profile), 200


@app.route('/api/auth/profile', methods=['PUT'])
@require_auth
@handle_errors
def update_profile():
    """Update user profile endpoint."""
    data = request.get_json()
    authenticator = Authenticator(g.db)
    user = authenticator.update_profile(
        user_id=str(g.user.id),
        name=data.get('name'),
        email=data.get('email')
    )
    return jsonify({
        'id': str(user.id),
        'email': user.email,
        'name': user.name
    }), 200


@app.route('/api/auth/password', methods=['PUT'])
@require_auth
@handle_errors
def change_password():
    """Change password endpoint."""
    data = request.get_json()
    authenticator = Authenticator(g.db)
    authenticator.change_password(
        user_id=str(g.user.id),
        current_password=data.get('current_password'),
        new_password=data.get('new_password')
    )
    return jsonify({'message': 'Password changed successfully'}), 200


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@app.route('/api/dashboard/kpis', methods=['GET'])
@require_auth
@handle_errors
def get_dashboard_kpis():
    """Get all dashboard KPIs."""
    dashboard = Dashboard(g.db)
    kpis = dashboard.get_all_kpis()
    return jsonify(kpis), 200


# ============================================================================
# Product Endpoints
# ============================================================================

@app.route('/api/products', methods=['POST'])
@require_auth
@handle_errors
def create_product():
    """Create a new product."""
    data = request.get_json()
    product_manager = ProductManager(g.db)
    product = product_manager.create_product(
        sku=data.get('sku'),
        name=data.get('name'),
        category=data.get('category'),
        unit_of_measure=data.get('unit_of_measure'),
        low_stock_threshold=data.get('low_stock_threshold'),
        initial_stock_quantity=data.get('initial_stock_quantity'),
        initial_stock_location_id=data.get('initial_stock_location_id'),
        user_id=str(g.user.id)
    )
    return jsonify({
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'category': product.category,
        'unit_of_measure': product.unit_of_measure,
        'low_stock_threshold': product.low_stock_threshold,
        'created_at': product.created_at.isoformat()
    }), 201


@app.route('/api/products/<product_id>', methods=['GET'])
@require_auth
@handle_errors
def get_product(product_id):
    """Get a product by ID."""
    product_manager = ProductManager(g.db)
    product = product_manager.get_product(product_id)
    return jsonify({
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'category': product.category,
        'unit_of_measure': product.unit_of_measure,
        'low_stock_threshold': product.low_stock_threshold,
        'created_at': product.created_at.isoformat()
    }), 200


@app.route('/api/products/<product_id>', methods=['PUT'])
@require_auth
@handle_errors
def update_product(product_id):
    """Update a product."""
    data = request.get_json()
    product_manager = ProductManager(g.db)
    product = product_manager.update_product(
        product_id=product_id,
        name=data.get('name'),
        category=data.get('category'),
        unit_of_measure=data.get('unit_of_measure'),
        low_stock_threshold=data.get('low_stock_threshold')
    )
    return jsonify({
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'category': product.category,
        'unit_of_measure': product.unit_of_measure,
        'low_stock_threshold': product.low_stock_threshold
    }), 200


@app.route('/api/products/search', methods=['GET'])
@require_auth
@handle_errors
def search_products():
    """Search products by SKU or name."""
    query = request.args.get('q', '')
    product_manager = ProductManager(g.db)
    products = product_manager.search_products(query)
    return jsonify([{
        'id': str(p.id),
        'sku': p.sku,
        'name': p.name,
        'category': p.category,
        'unit_of_measure': p.unit_of_measure,
        'low_stock_threshold': p.low_stock_threshold
    } for p in products]), 200


@app.route('/api/products/filter', methods=['GET'])
@require_auth
@handle_errors
def filter_products():
    """Filter products by multiple criteria."""
    product_manager = ProductManager(g.db)
    products = product_manager.filter_products(
        category=request.args.get('category'),
        sku=request.args.get('sku'),
        name=request.args.get('name'),
        unit_of_measure=request.args.get('unit_of_measure')
    )
    return jsonify([{
        'id': str(p.id),
        'sku': p.sku,
        'name': p.name,
        'category': p.category,
        'unit_of_measure': p.unit_of_measure,
        'low_stock_threshold': p.low_stock_threshold
    } for p in products]), 200


# ============================================================================
# Location Endpoints
# ============================================================================

@app.route('/api/locations', methods=['POST'])
@require_auth
@handle_errors
def create_location():
    """Create a new location."""
    data = request.get_json()
    location_manager = LocationManager(g.db)
    location = location_manager.create_location(
        name=data.get('name'),
        location_type=data.get('type'),
        parent_id=data.get('parent_id')
    )
    return jsonify({
        'id': str(location.id),
        'name': location.name,
        'type': location.type.value,
        'parent_id': str(location.parent_id) if location.parent_id else None,
        'is_archived': location.is_archived,
        'created_at': location.created_at.isoformat()
    }), 201


@app.route('/api/locations/<location_id>', methods=['GET'])
@require_auth
@handle_errors
def get_location(location_id):
    """Get a location by ID."""
    location_manager = LocationManager(g.db)
    location = location_manager.get_location(location_id)
    return jsonify({
        'id': str(location.id),
        'name': location.name,
        'type': location.type.value,
        'parent_id': str(location.parent_id) if location.parent_id else None,
        'is_archived': location.is_archived,
        'created_at': location.created_at.isoformat()
    }), 200


@app.route('/api/locations/<location_id>', methods=['PUT'])
@require_auth
@handle_errors
def update_location(location_id):
    """Update a location."""
    data = request.get_json()
    location_manager = LocationManager(g.db)
    location = location_manager.update_location(
        location_id=location_id,
        name=data.get('name'),
        location_type=data.get('type'),
        parent_id=data.get('parent_id')
    )
    return jsonify({
        'id': str(location.id),
        'name': location.name,
        'type': location.type.value,
        'parent_id': str(location.parent_id) if location.parent_id else None,
        'is_archived': location.is_archived
    }), 200


@app.route('/api/locations/<location_id>/archive', methods=['POST'])
@require_auth
@handle_errors
def archive_location(location_id):
    """Archive a location."""
    location_manager = LocationManager(g.db)
    location_manager.archive_location(location_id)
    return jsonify({'message': 'Location archived successfully'}), 200


@app.route('/api/locations', methods=['GET'])
@require_auth
@handle_errors
def list_locations():
    """List all locations."""
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    location_manager = LocationManager(g.db)
    locations = location_manager.list_locations(include_archived=include_archived)
    return jsonify([{
        'id': str(loc.id),
        'name': loc.name,
        'type': loc.type.value,
        'parent_id': str(loc.parent_id) if loc.parent_id else None,
        'is_archived': loc.is_archived,
        'created_at': loc.created_at.isoformat()
    } for loc in locations]), 200


# ============================================================================
# Stock Endpoints
# ============================================================================

@app.route('/api/stock/<product_id>/<location_id>', methods=['GET'])
@require_auth
@handle_errors
def get_stock(product_id, location_id):
    """Get stock for a product at a location."""
    stock_manager = StockManager(g.db)
    quantity = stock_manager.get_stock(product_id, location_id)
    return jsonify({'product_id': product_id, 'location_id': location_id, 'quantity': quantity}), 200


@app.route('/api/stock/product/<product_id>', methods=['GET'])
@require_auth
@handle_errors
def get_stock_by_product(product_id):
    """Get stock across all locations for a product."""
    stock_manager = StockManager(g.db)
    location_stocks = stock_manager.get_stock_by_product(product_id)
    return jsonify([{
        'location_id': ls.location_id,
        'location_name': ls.location_name,
        'quantity': ls.quantity
    } for ls in location_stocks]), 200


@app.route('/api/stock/low-stock', methods=['GET'])
@require_auth
@handle_errors
def get_low_stock_products():
    """Get products with low stock."""
    threshold = request.args.get('threshold', type=int)
    stock_manager = StockManager(g.db)
    products = stock_manager.get_low_stock_products(threshold=threshold)
    return jsonify(products), 200


# ============================================================================
# Document Endpoints - Receipts
# ============================================================================

@app.route('/api/documents/receipts', methods=['POST'])
@require_auth
@handle_errors
def create_receipt():
    """Create a new receipt."""
    data = request.get_json()
    document_manager = DocumentManager(g.db)
    receipt = document_manager.create_receipt(
        supplier_name=data.get('supplier_name'),
        created_by=str(g.user.id),
        items=data.get('items', []),
        supplier_contact=data.get('supplier_contact')
    )
    return jsonify({
        'id': str(receipt.id),
        'supplier_name': receipt.supplier_name,
        'supplier_contact': receipt.supplier_contact,
        'status': receipt.status.value,
        'created_by': str(receipt.created_by),
        'created_at': receipt.created_at.isoformat()
    }), 201


@app.route('/api/documents/receipts/<receipt_id>/validate', methods=['POST'])
@require_auth
@handle_errors
def validate_receipt(receipt_id):
    """Validate a receipt."""
    validator = Validator(g.db)
    validator.validate_receipt(receipt_id, str(g.user.id))
    return jsonify({'message': 'Receipt validated successfully'}), 200


# ============================================================================
# Document Endpoints - Delivery Orders
# ============================================================================

@app.route('/api/documents/delivery-orders', methods=['POST'])
@require_auth
@handle_errors
def create_delivery_order():
    """Create a new delivery order."""
    data = request.get_json()
    document_manager = DocumentManager(g.db)
    order = document_manager.create_delivery_order(
        customer_name=data.get('customer_name'),
        created_by=str(g.user.id),
        items=data.get('items', []),
        customer_contact=data.get('customer_contact')
    )
    return jsonify({
        'id': str(order.id),
        'customer_name': order.customer_name,
        'customer_contact': order.customer_contact,
        'status': order.status.value,
        'created_by': str(order.created_by),
        'created_at': order.created_at.isoformat()
    }), 201


@app.route('/api/documents/delivery-orders/<order_id>/validate', methods=['POST'])
@require_auth
@handle_errors
def validate_delivery_order(order_id):
    """Validate a delivery order."""
    validator = Validator(g.db)
    validator.validate_delivery_order(order_id, str(g.user.id))
    return jsonify({'message': 'Delivery order validated successfully'}), 200


# ============================================================================
# Document Endpoints - Transfers
# ============================================================================

@app.route('/api/documents/transfers', methods=['POST'])
@require_auth
@handle_errors
def create_transfer():
    """Create a new transfer."""
    data = request.get_json()
    document_manager = DocumentManager(g.db)
    transfer = document_manager.create_transfer(
        source_location_id=data.get('source_location_id'),
        destination_location_id=data.get('destination_location_id'),
        product_id=data.get('product_id'),
        quantity=data.get('quantity'),
        created_by=str(g.user.id)
    )
    return jsonify({
        'id': str(transfer.id),
        'source_location_id': str(transfer.source_location_id),
        'destination_location_id': str(transfer.destination_location_id),
        'product_id': str(transfer.product_id),
        'quantity': transfer.quantity,
        'status': transfer.status.value,
        'created_by': str(transfer.created_by),
        'created_at': transfer.created_at.isoformat()
    }), 201


@app.route('/api/documents/transfers/<transfer_id>/validate', methods=['POST'])
@require_auth
@handle_errors
def validate_transfer(transfer_id):
    """Validate a transfer."""
    validator = Validator(g.db)
    validator.validate_transfer(transfer_id, str(g.user.id))
    return jsonify({'message': 'Transfer validated successfully'}), 200


# ============================================================================
# Document Endpoints - Stock Adjustments
# ============================================================================

@app.route('/api/documents/stock-adjustments', methods=['POST'])
@require_auth
@handle_errors
def create_stock_adjustment():
    """Create a new stock adjustment."""
    data = request.get_json()
    document_manager = DocumentManager(g.db)
    adjustment = document_manager.create_stock_adjustment(
        product_id=data.get('product_id'),
        location_id=data.get('location_id'),
        recorded_quantity=data.get('recorded_quantity'),
        physical_quantity=data.get('physical_quantity'),
        reason=data.get('reason'),
        created_by=str(g.user.id)
    )
    return jsonify({
        'id': str(adjustment.id),
        'product_id': str(adjustment.product_id),
        'location_id': str(adjustment.location_id),
        'recorded_quantity': adjustment.recorded_quantity,
        'physical_quantity': adjustment.physical_quantity,
        'adjustment_difference': adjustment.adjustment_difference,
        'reason': adjustment.reason,
        'status': adjustment.status.value,
        'created_by': str(adjustment.created_by),
        'created_at': adjustment.created_at.isoformat()
    }), 201


@app.route('/api/documents/stock-adjustments/<adjustment_id>/validate', methods=['POST'])
@require_auth
@handle_errors
def validate_stock_adjustment(adjustment_id):
    """Validate a stock adjustment."""
    validator = Validator(g.db)
    validator.validate_stock_adjustment(adjustment_id, str(g.user.id))
    return jsonify({'message': 'Stock adjustment validated successfully'}), 200


# ============================================================================
# Document Listing Endpoint
# ============================================================================

@app.route('/api/documents', methods=['GET'])
@require_auth
@handle_errors
def list_documents():
    """List documents with optional filtering."""
    document_manager = DocumentManager(g.db)
    documents = document_manager.list_documents(
        document_type=request.args.get('document_type'),
        status=request.args.get('status'),
        location_id=request.args.get('location_id')
    )
    return jsonify(documents), 200


@app.route('/api/documents/<document_type>/<document_id>', methods=['GET'])
@require_auth
@handle_errors
def get_document(document_type, document_id):
    """Get a specific document."""
    document_manager = DocumentManager(g.db)
    document = document_manager.get_document(document_id, document_type)
    
    # Serialize document based on type
    result = {
        'id': str(document.id),
        'status': document.status.value,
        'created_by': str(document.created_by),
        'created_at': document.created_at.isoformat(),
        'validated_by': str(document.validated_by) if document.validated_by else None,
        'validated_at': document.validated_at.isoformat() if document.validated_at else None
    }
    
    if document_type == 'receipt':
        result.update({
            'supplier_name': document.supplier_name,
            'supplier_contact': document.supplier_contact
        })
    elif document_type == 'delivery_order':
        result.update({
            'customer_name': document.customer_name,
            'customer_contact': document.customer_contact
        })
    elif document_type == 'transfer':
        result.update({
            'source_location_id': str(document.source_location_id),
            'destination_location_id': str(document.destination_location_id),
            'product_id': str(document.product_id),
            'quantity': document.quantity
        })
    elif document_type == 'stock_adjustment':
        result.update({
            'product_id': str(document.product_id),
            'location_id': str(document.location_id),
            'recorded_quantity': document.recorded_quantity,
            'physical_quantity': document.physical_quantity,
            'adjustment_difference': document.adjustment_difference,
            'reason': document.reason
        })
    
    return jsonify(result), 200


# ============================================================================
# History Endpoints
# ============================================================================

@app.route('/api/history/movements', methods=['GET'])
@require_auth
@handle_errors
def get_move_history():
    """Get move history with optional filtering."""
    history_logger = HistoryLogger(g.db)
    
    # Parse date filters
    start_date = None
    end_date = None
    if request.args.get('start_date'):
        start_date = datetime.fromisoformat(request.args.get('start_date'))
    if request.args.get('end_date'):
        end_date = datetime.fromisoformat(request.args.get('end_date'))
    
    history = history_logger.get_move_history(
        start_date=start_date,
        end_date=end_date,
        product_id=request.args.get('product_id'),
        location_id=request.args.get('location_id'),
        document_type=request.args.get('document_type')
    )
    return jsonify(history), 200


@app.route('/api/history/ledger', methods=['GET'])
@require_auth
@handle_errors
def get_stock_ledger():
    """Get stock ledger with optional filtering."""
    history_logger = HistoryLogger(g.db)
    
    # Parse date filters
    start_date = None
    end_date = None
    if request.args.get('start_date'):
        start_date = datetime.fromisoformat(request.args.get('start_date'))
    if request.args.get('end_date'):
        end_date = datetime.fromisoformat(request.args.get('end_date'))
    
    ledger = history_logger.get_stock_ledger(
        product_id=request.args.get('product_id'),
        location_id=request.args.get('location_id'),
        start_date=start_date,
        end_date=end_date
    )
    return jsonify(ledger), 200


@app.route('/api/history/ledger/export', methods=['GET'])
@require_auth
@handle_errors
def export_ledger():
    """Export stock ledger."""
    history_logger = HistoryLogger(g.db)
    
    # Parse date filters
    start_date = None
    end_date = None
    if request.args.get('start_date'):
        start_date = datetime.fromisoformat(request.args.get('start_date'))
    if request.args.get('end_date'):
        end_date = datetime.fromisoformat(request.args.get('end_date'))
    
    format_type = request.args.get('format', 'csv')
    
    export_data = history_logger.export_ledger(
        format=format_type,
        product_id=request.args.get('product_id'),
        location_id=request.args.get('location_id'),
        start_date=start_date,
        end_date=end_date
    )
    
    return export_data, 200, {
        'Content-Type': 'text/csv' if format_type == 'csv' else 'application/json',
        'Content-Disposition': f'attachment; filename=stock_ledger.{format_type}'
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
