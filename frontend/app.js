// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let sessionToken = localStorage.getItem('sessionToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (sessionToken) {
        showDashboard();
        loadDashboardData();
    } else {
        showLogin();
    }
});

// API Helper
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error?.message || 'Request failed');
        }
        
        return data;
    } catch (error) {
        alert('Error: ' + error.message);
        throw error;
    }
}

// Authentication
async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const data = await apiCall('/auth/login', 'POST', { email, password });
        sessionToken = data.session_id;
        localStorage.setItem('sessionToken', sessionToken);
        
        // Get user profile
        const profile = await apiCall('/auth/profile');
        currentUser = profile;
        localStorage.setItem('currentUser', JSON.stringify(profile));
        
        showDashboard();
        loadDashboardData();
    } catch (error) {
        console.error('Login failed:', error);
    }
}

async function signup() {
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    if (!name || !email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        await apiCall('/auth/signup', 'POST', { name, email, password });
        alert('Account created successfully! Please login.');
        showLogin();
    } catch (error) {
        console.error('Signup failed:', error);
    }
}

function logout() {
    apiCall('/auth/logout', 'POST').catch(() => {});
    sessionToken = null;
    currentUser = {};
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('currentUser');
    showLogin();
}

// Screen Navigation
function showLogin() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('loginScreen').classList.add('active');
}

function showSignup() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('signupScreen').classList.add('active');
}

function showDashboard() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('dashboardScreen').classList.add('active');
    document.getElementById('userName').textContent = currentUser.name || 'User';
    loadDashboardData();
}

// Tab Navigation
function showTab(tabName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Load data for the tab
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'products':
            loadProducts();
            break;
        case 'locations':
            loadLocations();
            break;
        case 'receipts':
            loadReceipts();
            break;
        case 'deliveries':
            loadDeliveries();
            break;
        case 'transfers':
            loadTransfers();
            break;
        case 'history':
            loadHistory();
            break;
    }
}

// Dashboard
async function loadDashboardData() {
    try {
        const kpis = await apiCall('/dashboard/kpis');
        document.getElementById('totalProducts').textContent = kpis.total_products;
        document.getElementById('lowStockProducts').textContent = kpis.low_stock_products;
        document.getElementById('zeroStockProducts').textContent = kpis.zero_stock_products;
        document.getElementById('pendingReceipts').textContent = kpis.pending_receipts;
        document.getElementById('pendingDeliveries').textContent = kpis.pending_delivery_orders;
        document.getElementById('pendingTransfers').textContent = kpis.pending_transfers;
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// Products
let allProducts = []; // Store all products for filtering/sorting

async function loadProducts() {
    console.log('Loading products...');
    try {
        const products = await apiCall('/products/search?q=');
        console.log('Products loaded:', products);
        allProducts = products; // Store for filtering
        
        // Populate category filter
        const categories = [...new Set(products.map(p => p.category))];
        const categoryFilter = document.getElementById('categoryFilter');
        const currentCategory = categoryFilter.value;
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            categoryFilter.innerHTML += `<option value="${cat}" ${cat === currentCategory ? 'selected' : ''}>${cat}</option>`;
        });
        
        await displayProducts(products);
    } catch (error) {
        console.error('Failed to load products:', error);
        const container = document.getElementById('productsList');
        container.innerHTML = '<div class="empty-state"><h3>Error loading products</h3><p>' + error.message + '</p></div>';
    }
}

async function displayProducts(products) {
    const container = document.getElementById('productsList');
    
    if (products.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No products found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">SKU</div>';
    html += '<div class="table-cell">Name</div>';
    html += '<div class="table-cell">Category</div>';
    html += '<div class="table-cell">Unit</div>';
    html += '<div class="table-cell">Current Stock</div>';
    html += '<div class="table-cell">Low Stock Threshold</div>';
    html += '<div class="table-cell">Actions</div>';
    html += '</div>';
    
    // Load stock data for each product
    for (const product of products) {
        let totalStock = 0;
        try {
            const stockData = await apiCall(`/stock/product/${product.id}`);
            totalStock = stockData.reduce((sum, loc) => sum + loc.quantity, 0);
        } catch (error) {
            console.error(`Failed to load stock for ${product.sku}:`, error);
        }
        
        // Store stock for filtering
        product.totalStock = totalStock;
        
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${product.sku}</strong></div>`;
        html += `<div class="table-cell">${product.name}</div>`;
        html += `<div class="table-cell">${product.category}</div>`;
        html += `<div class="table-cell">${product.unit_of_measure}</div>`;
        
        // Color code stock levels
        let stockColor = '#10b981'; // green
        if (product.low_stock_threshold && totalStock <= product.low_stock_threshold) {
            stockColor = '#f59e0b'; // orange
        }
        if (totalStock === 0) {
            stockColor = '#ef4444'; // red
        }
        
        html += `<div class="table-cell" style="color: ${stockColor}; font-weight: 600;">${totalStock}</div>`;
        html += `<div class="table-cell">${product.low_stock_threshold || 'N/A'}</div>`;
        html += `<div class="table-cell"><button class="btn-small" style="background: #3b82f6;" onclick='showEditProduct(${JSON.stringify(product)})'>Edit</button></div>`;
        html += '</div>';
    }
    
    container.innerHTML = html;
    console.log('Products displayed successfully');
}

async function applyProductFilters() {
    const searchTerm = document.getElementById('productSearch').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const stockFilter = document.getElementById('stockFilter').value;
    const sortBy = document.getElementById('sortBy').value;
    
    let filtered = allProducts.filter(product => {
        // Search filter
        const matchesSearch = !searchTerm || 
            product.name.toLowerCase().includes(searchTerm) || 
            product.sku.toLowerCase().includes(searchTerm);
        
        // Category filter
        const matchesCategory = !categoryFilter || product.category === categoryFilter;
        
        // Stock filter
        let matchesStock = true;
        if (stockFilter === 'in_stock') {
            matchesStock = (product.totalStock || 0) > (product.low_stock_threshold || 0);
        } else if (stockFilter === 'low_stock') {
            matchesStock = (product.totalStock || 0) > 0 && 
                          (product.totalStock || 0) <= (product.low_stock_threshold || 0);
        } else if (stockFilter === 'out_of_stock') {
            matchesStock = (product.totalStock || 0) === 0;
        }
        
        return matchesSearch && matchesCategory && matchesStock;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'name_asc':
                return a.name.localeCompare(b.name);
            case 'name_desc':
                return b.name.localeCompare(a.name);
            case 'sku_asc':
                return a.sku.localeCompare(b.sku);
            case 'sku_desc':
                return b.sku.localeCompare(a.sku);
            case 'stock_asc':
                return (a.totalStock || 0) - (b.totalStock || 0);
            case 'stock_desc':
                return (b.totalStock || 0) - (a.totalStock || 0);
            default:
                return 0;
        }
    });
    
    await displayProducts(filtered);
}

function showEditProduct(product) {
    document.getElementById('editProductId').value = product.id;
    document.getElementById('editProductSKU').value = product.sku;
    document.getElementById('editProductName').value = product.name;
    document.getElementById('editProductCategory').value = product.category;
    document.getElementById('editProductUnit').value = product.unit_of_measure;
    document.getElementById('editProductThreshold').value = product.low_stock_threshold || '';
    
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('editProductModal').classList.add('active');
}

async function updateProduct() {
    const productId = document.getElementById('editProductId').value;
    const name = document.getElementById('editProductName').value;
    const category = document.getElementById('editProductCategory').value;
    const unit = document.getElementById('editProductUnit').value;
    const threshold = document.getElementById('editProductThreshold').value;
    
    if (!name || !category || !unit) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const data = {
            name,
            category,
            unit_of_measure: unit,
            low_stock_threshold: threshold ? parseInt(threshold) : null
        };
        
        await apiCall(`/products/${productId}`, 'PUT', data);
        
        closeModal();
        alert('Product updated successfully!');
        loadProducts();
    } catch (error) {
        console.error('Failed to update product:', error);
        alert('Failed to update product: ' + error.message);
    }
}

async function searchProducts() {
    applyProductFilters();
}

// Locations
async function loadLocations() {
    try {
        const locations = await apiCall('/locations');
        const container = document.getElementById('locationsList');
        
        if (locations.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No locations yet</h3><p>Add your first location to get started</p></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">Name</div>';
        html += '<div class="table-cell">Type</div>';
        html += '<div class="table-cell">Status</div>';
        html += '</div>';
        
        locations.forEach(location => {
            html += '<div class="table-row">';
            html += `<div class="table-cell"><strong>${location.name}</strong></div>`;
            html += `<div class="table-cell">${location.type}</div>`;
            html += `<div class="table-cell">${location.is_archived ? 'Archived' : 'Active'}</div>`;
            html += '</div>';
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load locations:', error);
    }
}

// Location sub-tabs
function showLocationSubTab(subtab) {
    // Update sub-nav buttons
    document.querySelectorAll('.sub-nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.subtab === subtab) {
            btn.classList.add('active');
        }
    });
    
    // Update sub-tab content
    document.querySelectorAll('.sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    if (subtab === 'list') {
        document.getElementById('locationsListSubTab').classList.add('active');
        loadLocations();
    } else if (subtab === 'stock') {
        document.getElementById('locationsStockSubTab').classList.add('active');
        loadStockByLocation();
    }
}

async function loadStockByLocation() {
    try {
        const locations = await apiCall('/locations');
        const products = await apiCall('/products/search?q=');
        const container = document.getElementById('stockByLocationList');
        
        if (locations.length === 0 || products.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No data available</h3><p>Create locations and products first</p></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">Location</div>';
        html += '<div class="table-cell">Product</div>';
        html += '<div class="table-cell">SKU</div>';
        html += '<div class="table-cell">Quantity</div>';
        html += '</div>';
        
        let hasStock = false;
        
        for (const location of locations) {
            if (location.is_archived) continue;
            
            for (const product of products) {
                try {
                    const stockData = await apiCall(`/stock/${product.id}/${location.id}`);
                    const quantity = stockData.quantity || 0;
                    
                    if (quantity > 0) {
                        hasStock = true;
                        let stockColor = '#10b981'; // green
                        if (product.low_stock_threshold && quantity <= product.low_stock_threshold) {
                            stockColor = '#f59e0b'; // orange
                        }
                        
                        html += '<div class="table-row">';
                        html += `<div class="table-cell"><strong>${location.name}</strong></div>`;
                        html += `<div class="table-cell">${product.name}</div>`;
                        html += `<div class="table-cell">${product.sku}</div>`;
                        html += `<div class="table-cell" style="color: ${stockColor}; font-weight: 600;">${quantity}</div>`;
                        html += '</div>';
                    }
                } catch (error) {
                    // Stock not found for this product/location combination
                    continue;
                }
            }
        }
        
        if (!hasStock) {
            container.innerHTML = '<div class="empty-state"><h3>No stock in any location</h3><p>Create receipts and validate them to add stock</p></div>';
        } else {
            container.innerHTML = html;
        }
    } catch (error) {
        console.error('Failed to load stock by location:', error);
        const container = document.getElementById('stockByLocationList');
        container.innerHTML = '<div class="empty-state"><h3>Error loading stock</h3><p>' + error.message + '</p></div>';
    }
}

// Receipts
async function loadReceipts() {
    try {
        const receipts = await apiCall('/documents?document_type=receipt');
        const container = document.getElementById('receiptsList');
        
        if (receipts.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No receipts yet</h3><p>Create your first receipt to track incoming goods</p></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">ID</div>';
        html += '<div class="table-cell">Supplier</div>';
        html += '<div class="table-cell">Status</div>';
        html += '<div class="table-cell">Created</div>';
        html += '<div class="table-cell">Actions</div>';
        html += '</div>';
        
        receipts.forEach(receipt => {
            html += '<div class="table-row">';
            html += `<div class="table-cell"><strong>${receipt.id.substring(0, 8)}</strong></div>`;
            html += `<div class="table-cell">${receipt.supplier_name}</div>`;
            html += `<div class="table-cell"><span class="badge ${receipt.status}">${receipt.status}</span></div>`;
            html += `<div class="table-cell">${new Date(receipt.created_at).toLocaleDateString()}</div>`;
            html += '<div class="table-cell">';
            if (receipt.status === 'pending') {
                html += `<button class="btn-small btn-validate" onclick="validateReceipt('${receipt.id}')">Validate</button>`;
            }
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load receipts:', error);
    }
}

async function validateReceipt(receiptId) {
    if (!confirm('Validate this receipt? This will update stock levels.')) return;
    
    try {
        await apiCall(`/documents/receipts/${receiptId}/validate`, 'POST');
        alert('Receipt validated successfully!');
        loadReceipts();
        loadDashboardData();
        
        // Refresh products if on products tab
        const productsTab = document.getElementById('productsTab');
        if (productsTab && productsTab.classList.contains('active')) {
            loadProducts();
        }
    } catch (error) {
        console.error('Failed to validate receipt:', error);
    }
}

// Deliveries
async function loadDeliveries() {
    try {
        const deliveries = await apiCall('/documents?document_type=delivery_order');
        const container = document.getElementById('deliveriesList');
        
        if (deliveries.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No delivery orders yet</h3><p>Create your first delivery order to track outgoing goods</p></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">ID</div>';
        html += '<div class="table-cell">Customer</div>';
        html += '<div class="table-cell">Status</div>';
        html += '<div class="table-cell">Created</div>';
        html += '<div class="table-cell">Actions</div>';
        html += '</div>';
        
        deliveries.forEach(delivery => {
            html += '<div class="table-row">';
            html += `<div class="table-cell"><strong>${delivery.id.substring(0, 8)}</strong></div>`;
            html += `<div class="table-cell">${delivery.customer_name}</div>`;
            html += `<div class="table-cell"><span class="badge ${delivery.status}">${delivery.status}</span></div>`;
            html += `<div class="table-cell">${new Date(delivery.created_at).toLocaleDateString()}</div>`;
            html += '<div class="table-cell">';
            if (delivery.status === 'pending') {
                html += `<button class="btn-small btn-validate" onclick="validateDelivery('${delivery.id}')">Validate</button>`;
            }
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load deliveries:', error);
    }
}

async function validateDelivery(deliveryId) {
    if (!confirm('Validate this delivery order? This will decrease stock levels.')) return;
    
    try {
        await apiCall(`/documents/delivery-orders/${deliveryId}/validate`, 'POST');
        alert('Delivery order validated successfully!');
        loadDeliveries();
        loadDashboardData();
        
        // Refresh products if on products tab
        const productsTab = document.getElementById('productsTab');
        if (productsTab && productsTab.classList.contains('active')) {
            loadProducts();
        }
    } catch (error) {
        console.error('Failed to validate delivery:', error);
    }
}

// History
async function loadHistory() {
    try {
        const history = await apiCall('/history/movements');
        const container = document.getElementById('historyList');
        
        if (history.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No movement history yet</h3></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">Date</div>';
        html += '<div class="table-cell">Product</div>';
        html += '<div class="table-cell">Location</div>';
        html += '<div class="table-cell">Quantity Change</div>';
        html += '<div class="table-cell">Document Type</div>';
        html += '</div>';
        
        history.forEach(entry => {
            html += '<div class="table-row">';
            html += `<div class="table-cell">${new Date(entry.timestamp).toLocaleString()}</div>`;
            html += `<div class="table-cell">${entry.product_name || entry.product_id}</div>`;
            html += `<div class="table-cell">${entry.location_name || entry.location_id}</div>`;
            html += `<div class="table-cell" style="color: ${entry.quantity_change > 0 ? '#10b981' : '#ef4444'}">${entry.quantity_change > 0 ? '+' : ''}${entry.quantity_change}</div>`;
            html += `<div class="table-cell">${entry.document_type}</div>`;
            html += '</div>';
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// Modals
function showAddProduct() {
    // Load locations for dropdown
    loadLocationsForDropdown('newProductLocation');
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('addProductModal').classList.add('active');
}

function showAddLocation() {
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('addLocationModal').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

async function addProduct() {
    const sku = document.getElementById('newProductSKU').value;
    const name = document.getElementById('newProductName').value;
    const category = document.getElementById('newProductCategory').value;
    const unit = document.getElementById('newProductUnit').value;
    const threshold = document.getElementById('newProductThreshold').value;
    const initialStock = document.getElementById('newProductInitialStock').value;
    const locationId = document.getElementById('newProductLocation').value;
    
    if (!sku || !name || !category || !unit) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const data = {
            sku,
            name,
            category,
            unit_of_measure: unit,
            low_stock_threshold: threshold ? parseInt(threshold) : null,
            initial_stock_quantity: initialStock ? parseInt(initialStock) : 0,
            initial_stock_location_id: locationId || null
        };
        
        const result = await apiCall('/products', 'POST', data);
        console.log('Product created:', result);
        
        // Clear form first
        document.getElementById('newProductSKU').value = '';
        document.getElementById('newProductName').value = '';
        document.getElementById('newProductCategory').value = '';
        document.getElementById('newProductUnit').value = '';
        document.getElementById('newProductThreshold').value = '';
        document.getElementById('newProductInitialStock').value = '';
        document.getElementById('newProductLocation').value = '';
        
        closeModal();
        
        // Switch to products tab and reload
        showTab('products');
        
        alert('Product added successfully!');
        
        // Reload dashboard data
        loadDashboardData();
    } catch (error) {
        console.error('Failed to add product:', error);
        alert('Failed to add product: ' + error.message);
    }
}

async function addLocation() {
    const name = document.getElementById('newLocationName').value;
    const type = document.getElementById('newLocationType').value;
    
    if (!name || !type) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const result = await apiCall('/locations', 'POST', { name, type });
        console.log('Location created:', result);
        
        // Clear form
        document.getElementById('newLocationName').value = '';
        document.getElementById('newLocationType').value = 'warehouse';
        
        closeModal();
        
        // Switch to locations tab and reload
        showTab('locations');
        
        alert('Location added successfully!');
    } catch (error) {
        console.error('Failed to add location:', error);
        alert('Failed to add location: ' + error.message);
    }
}

// Receipt Functions
async function showAddReceipt() {
    // Load products and locations for dropdowns
    await loadProductsForDropdown('newReceiptProduct');
    await loadLocationsForDropdown('newReceiptLocation');
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('addReceiptModal').classList.add('active');
}

async function loadProductsForDropdown(selectId) {
    try {
        const products = await apiCall('/products/search?q=');
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select Product</option>';
        products.forEach(product => {
            select.innerHTML += `<option value="${product.id}">${product.name} (${product.sku})</option>`;
        });
    } catch (error) {
        console.error('Failed to load products:', error);
    }
}

async function loadLocationsForDropdown(selectId) {
    try {
        const locations = await apiCall('/locations');
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select Location</option>';
        locations.forEach(loc => {
            select.innerHTML += `<option value="${loc.id}">${loc.name}</option>`;
        });
    } catch (error) {
        console.error('Failed to load locations:', error);
    }
}

async function addReceipt() {
    const supplier = document.getElementById('newReceiptSupplier').value;
    const contact = document.getElementById('newReceiptContact').value;
    const productId = document.getElementById('newReceiptProduct').value;
    const locationId = document.getElementById('newReceiptLocation').value;
    const quantity = document.getElementById('newReceiptQuantity').value;
    
    if (!supplier || !productId || !locationId || !quantity) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const data = {
            supplier_name: supplier,
            supplier_contact: contact || null,
            items: [{
                product_id: productId,
                location_id: locationId,
                expected_quantity: parseInt(quantity),
                received_quantity: parseInt(quantity)
            }]
        };
        
        const result = await apiCall('/documents/receipts', 'POST', data);
        console.log('Receipt created:', result);
        
        // Clear form
        document.getElementById('newReceiptSupplier').value = '';
        document.getElementById('newReceiptContact').value = '';
        document.getElementById('newReceiptProduct').value = '';
        document.getElementById('newReceiptLocation').value = '';
        document.getElementById('newReceiptQuantity').value = '';
        
        closeModal();
        
        // Switch to receipts tab and reload
        showTab('receipts');
        
        alert('Receipt created successfully! Don\'t forget to validate it to update stock.');
        
        // Reload dashboard
        loadDashboardData();
    } catch (error) {
        console.error('Failed to create receipt:', error);
        alert('Failed to create receipt: ' + error.message);
    }
}

// Delivery Functions
async function showAddDelivery() {
    // Load products and locations for dropdowns
    await loadProductsForDropdown('newDeliveryProduct');
    await loadLocationsForDropdown('newDeliveryLocation');
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('addDeliveryModal').classList.add('active');
}

async function addDelivery() {
    const customer = document.getElementById('newDeliveryCustomer').value;
    const contact = document.getElementById('newDeliveryContact').value;
    const productId = document.getElementById('newDeliveryProduct').value;
    const locationId = document.getElementById('newDeliveryLocation').value;
    const quantity = document.getElementById('newDeliveryQuantity').value;
    
    if (!customer || !productId || !locationId || !quantity) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const data = {
            customer_name: customer,
            customer_contact: contact || null,
            items: [{
                product_id: productId,
                location_id: locationId,
                requested_quantity: parseInt(quantity),
                delivered_quantity: parseInt(quantity)
            }]
        };
        
        const result = await apiCall('/documents/delivery-orders', 'POST', data);
        console.log('Delivery order created:', result);
        
        // Clear form
        document.getElementById('newDeliveryCustomer').value = '';
        document.getElementById('newDeliveryContact').value = '';
        document.getElementById('newDeliveryProduct').value = '';
        document.getElementById('newDeliveryLocation').value = '';
        document.getElementById('newDeliveryQuantity').value = '';
        
        closeModal();
        
        // Switch to deliveries tab and reload
        showTab('deliveries');
        
        alert('Delivery order created successfully! Don\'t forget to validate it to update stock.');
        
        // Reload dashboard
        loadDashboardData();
    } catch (error) {
        console.error('Failed to create delivery order:', error);
        alert('Failed to create delivery order: ' + error.message);
    }
}

// Transfer Functions
async function loadTransfers() {
    try {
        const transfers = await apiCall('/documents?document_type=transfer');
        const container = document.getElementById('transfersList');
        
        if (transfers.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No transfers yet</h3><p>Create your first transfer to move stock between locations</p></div>';
            return;
        }
        
        let html = '<div class="table-row header">';
        html += '<div class="table-cell">ID</div>';
        html += '<div class="table-cell">Product</div>';
        html += '<div class="table-cell">From → To</div>';
        html += '<div class="table-cell">Quantity</div>';
        html += '<div class="table-cell">Status</div>';
        html += '<div class="table-cell">Created</div>';
        html += '<div class="table-cell">Actions</div>';
        html += '</div>';
        
        transfers.forEach(transfer => {
            html += '<div class="table-row">';
            html += `<div class="table-cell"><strong>${transfer.id.substring(0, 8)}</strong></div>`;
            html += `<div class="table-cell">${transfer.product_name || transfer.product_id.substring(0, 8)}</div>`;
            html += `<div class="table-cell">${transfer.source_location_name || 'Source'} → ${transfer.destination_location_name || 'Dest'}</div>`;
            html += `<div class="table-cell">${transfer.quantity}</div>`;
            html += `<div class="table-cell"><span class="badge ${transfer.status}">${transfer.status}</span></div>`;
            html += `<div class="table-cell">${new Date(transfer.created_at).toLocaleDateString()}</div>`;
            html += '<div class="table-cell">';
            if (transfer.status === 'pending') {
                html += `<button class="btn-small btn-validate" onclick="validateTransfer('${transfer.id}')">Validate</button>`;
            }
            html += '</div>';
            html += '</div>';
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load transfers:', error);
    }
}

async function showAddTransfer() {
    // Load products and locations for dropdowns
    await loadProductsForDropdown('newTransferProduct');
    await loadLocationsForDropdown('newTransferSourceLocation');
    await loadLocationsForDropdown('newTransferDestLocation');
    document.getElementById('modalOverlay').classList.add('active');
    document.getElementById('addTransferModal').classList.add('active');
}

async function addTransfer() {
    const productId = document.getElementById('newTransferProduct').value;
    const sourceLocationId = document.getElementById('newTransferSourceLocation').value;
    const destLocationId = document.getElementById('newTransferDestLocation').value;
    const quantity = document.getElementById('newTransferQuantity').value;
    
    if (!productId || !sourceLocationId || !destLocationId || !quantity) {
        alert('Please fill in all required fields');
        return;
    }
    
    if (sourceLocationId === destLocationId) {
        alert('Source and destination locations must be different');
        return;
    }
    
    try {
        const data = {
            product_id: productId,
            source_location_id: sourceLocationId,
            destination_location_id: destLocationId,
            quantity: parseInt(quantity)
        };
        
        const result = await apiCall('/documents/transfers', 'POST', data);
        console.log('Transfer created:', result);
        
        // Clear form
        document.getElementById('newTransferProduct').value = '';
        document.getElementById('newTransferSourceLocation').value = '';
        document.getElementById('newTransferDestLocation').value = '';
        document.getElementById('newTransferQuantity').value = '';
        
        closeModal();
        
        // Switch to transfers tab and reload
        showTab('transfers');
        
        alert('Transfer created successfully! Don\'t forget to validate it to move the stock.');
        
        // Reload dashboard
        loadDashboardData();
    } catch (error) {
        console.error('Failed to create transfer:', error);
        alert('Failed to create transfer: ' + error.message);
    }
}

async function validateTransfer(transferId) {
    if (!confirm('Validate this transfer? This will move stock between locations.')) return;
    
    try {
        await apiCall(`/documents/transfers/${transferId}/validate`, 'POST');
        alert('Transfer validated successfully!');
        loadTransfers();
        loadDashboardData();
        
        // Refresh products if on products tab
        const productsTab = document.getElementById('productsTab');
        if (productsTab && productsTab.classList.contains('active')) {
            loadProducts();
        }
    } catch (error) {
        console.error('Failed to validate transfer:', error);
    }
}


// ===== RECEIPTS FILTERS AND SORTING =====
let allReceipts = [];

async function loadReceiptsWithStorage() {
    try {
        allReceipts = await apiCall('/documents?document_type=receipt');
        applyReceiptFilters();
    } catch (error) {
        console.error('Failed to load receipts:', error);
    }
}

function applyReceiptFilters() {
    const searchTerm = document.getElementById('receiptSearch').value.toLowerCase();
    const statusFilter = document.getElementById('receiptStatusFilter').value;
    const sortBy = document.getElementById('receiptSortBy').value;
    
    let filtered = allReceipts.filter(receipt => {
        const matchesSearch = receipt.supplier_name.toLowerCase().includes(searchTerm) || 
                            receipt.id.toLowerCase().includes(searchTerm);
        const matchesStatus = !statusFilter || receipt.status === statusFilter;
        return matchesSearch && matchesStatus;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'date_asc':
                return new Date(a.created_at) - new Date(b.created_at);
            case 'date_desc':
                return new Date(b.created_at) - new Date(a.created_at);
            case 'supplier_asc':
                return a.supplier_name.localeCompare(b.supplier_name);
            case 'supplier_desc':
                return b.supplier_name.localeCompare(a.supplier_name);
            default:
                return 0;
        }
    });
    
    displayReceipts(filtered);
}

function displayReceipts(receipts) {
    const container = document.getElementById('receiptsList');
    
    if (receipts.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No receipts found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">ID</div>';
    html += '<div class="table-cell">Supplier</div>';
    html += '<div class="table-cell">Status</div>';
    html += '<div class="table-cell">Created</div>';
    html += '<div class="table-cell">Actions</div>';
    html += '</div>';
    
    receipts.forEach(receipt => {
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${receipt.id.substring(0, 8)}</strong></div>`;
        html += `<div class="table-cell">${receipt.supplier_name}</div>`;
        html += `<div class="table-cell"><span class="badge ${receipt.status}">${receipt.status}</span></div>`;
        html += `<div class="table-cell">${new Date(receipt.created_at).toLocaleDateString()}</div>`;
        html += '<div class="table-cell">';
        if (receipt.status === 'pending') {
            html += `<button class="btn-small btn-validate" onclick="validateReceipt('${receipt.id}')">Validate</button>`;
        }
        html += '</div>';
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Override loadReceipts to use new system
async function loadReceipts() {
    await loadReceiptsWithStorage();
}

// ===== DELIVERIES FILTERS AND SORTING =====
let allDeliveries = [];

async function loadDeliveriesWithStorage() {
    try {
        allDeliveries = await apiCall('/documents?document_type=delivery_order');
        applyDeliveryFilters();
    } catch (error) {
        console.error('Failed to load deliveries:', error);
    }
}

function applyDeliveryFilters() {
    const searchTerm = document.getElementById('deliverySearch').value.toLowerCase();
    const statusFilter = document.getElementById('deliveryStatusFilter').value;
    const sortBy = document.getElementById('deliverySortBy').value;
    
    let filtered = allDeliveries.filter(delivery => {
        const matchesSearch = delivery.customer_name.toLowerCase().includes(searchTerm) || 
                            delivery.id.toLowerCase().includes(searchTerm);
        const matchesStatus = !statusFilter || delivery.status === statusFilter;
        return matchesSearch && matchesStatus;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'date_asc':
                return new Date(a.created_at) - new Date(b.created_at);
            case 'date_desc':
                return new Date(b.created_at) - new Date(a.created_at);
            case 'customer_asc':
                return a.customer_name.localeCompare(b.customer_name);
            case 'customer_desc':
                return b.customer_name.localeCompare(a.customer_name);
            default:
                return 0;
        }
    });
    
    displayDeliveries(filtered);
}

function displayDeliveries(deliveries) {
    const container = document.getElementById('deliveriesList');
    
    if (deliveries.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No deliveries found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">ID</div>';
    html += '<div class="table-cell">Customer</div>';
    html += '<div class="table-cell">Status</div>';
    html += '<div class="table-cell">Created</div>';
    html += '<div class="table-cell">Actions</div>';
    html += '</div>';
    
    deliveries.forEach(delivery => {
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${delivery.id.substring(0, 8)}</strong></div>`;
        html += `<div class="table-cell">${delivery.customer_name}</div>`;
        html += `<div class="table-cell"><span class="badge ${delivery.status}">${delivery.status}</span></div>`;
        html += `<div class="table-cell">${new Date(delivery.created_at).toLocaleDateString()}</div>`;
        html += '<div class="table-cell">';
        if (delivery.status === 'pending') {
            html += `<button class="btn-small btn-validate" onclick="validateDelivery('${delivery.id}')">Validate</button>`;
        }
        html += '</div>';
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Override loadDeliveries to use new system
async function loadDeliveries() {
    await loadDeliveriesWithStorage();
}

// ===== LOCATIONS FILTERS AND SORTING =====
let allLocations = [];

async function loadLocationsWithStorage() {
    try {
        allLocations = await apiCall('/locations');
        applyLocationFilters();
    } catch (error) {
        console.error('Failed to load locations:', error);
    }
}

function applyLocationFilters() {
    const searchTerm = document.getElementById('locationSearch').value.toLowerCase();
    const typeFilter = document.getElementById('locationTypeFilter').value;
    const statusFilter = document.getElementById('locationStatusFilter').value;
    const sortBy = document.getElementById('locationSortBy').value;
    
    let filtered = allLocations.filter(location => {
        const matchesSearch = location.name.toLowerCase().includes(searchTerm);
        const matchesType = !typeFilter || location.type === typeFilter;
        const matchesStatus = !statusFilter || 
                            (statusFilter === 'active' && !location.is_archived) ||
                            (statusFilter === 'archived' && location.is_archived);
        return matchesSearch && matchesType && matchesStatus;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'name_asc':
                return a.name.localeCompare(b.name);
            case 'name_desc':
                return b.name.localeCompare(a.name);
            case 'type_asc':
                return a.type.localeCompare(b.type);
            case 'type_desc':
                return b.type.localeCompare(a.type);
            default:
                return 0;
        }
    });
    
    displayLocations(filtered);
}

function displayLocations(locations) {
    const container = document.getElementById('locationsList');
    
    if (locations.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No locations found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">Name</div>';
    html += '<div class="table-cell">Type</div>';
    html += '<div class="table-cell">Status</div>';
    html += '</div>';
    
    locations.forEach(location => {
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${location.name}</strong></div>`;
        html += `<div class="table-cell">${location.type}</div>`;
        html += `<div class="table-cell">${location.is_archived ? 'Archived' : 'Active'}</div>`;
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Override loadLocations to use new system
async function loadLocations() {
    await loadLocationsWithStorage();
}

// ===== STOCK BY LOCATION FILTERS AND SORTING =====
let allStockByLocation = [];

async function loadStockByLocationWithStorage() {
    try {
        const locations = await apiCall('/locations');
        const products = await apiCall('/products/search?q=');
        
        allStockByLocation = [];
        
        for (const location of locations) {
            if (location.is_archived) continue;
            
            for (const product of products) {
                try {
                    const stockData = await apiCall(`/stock/${product.id}/${location.id}`);
                    const quantity = stockData.quantity || 0;
                    
                    if (quantity > 0) {
                        allStockByLocation.push({
                            location: location,
                            product: product,
                            quantity: quantity
                        });
                    }
                } catch (error) {
                    continue;
                }
            }
        }
        
        // Populate location filter dropdown
        const locationSelect = document.getElementById('stockLocationFilter');
        const uniqueLocations = [...new Set(allStockByLocation.map(s => s.location.id))];
        locationSelect.innerHTML = '<option value="">All Locations</option>';
        uniqueLocations.forEach(locId => {
            const loc = allStockByLocation.find(s => s.location.id === locId).location;
            const option = document.createElement('option');
            option.value = locId;
            option.textContent = loc.name;
            locationSelect.appendChild(option);
        });
        
        applyStockByLocationFilters();
    } catch (error) {
        console.error('Failed to load stock by location:', error);
    }
}

function applyStockByLocationFilters() {
    const searchTerm = document.getElementById('stockLocationSearch').value.toLowerCase();
    const locationFilter = document.getElementById('stockLocationFilter').value;
    const stockLevelFilter = document.getElementById('stockLevelFilter').value;
    const sortBy = document.getElementById('stockSortBy').value;
    
    let filtered = allStockByLocation.filter(item => {
        const matchesSearch = item.location.name.toLowerCase().includes(searchTerm) || 
                            item.product.name.toLowerCase().includes(searchTerm) ||
                            item.product.sku.toLowerCase().includes(searchTerm);
        const matchesLocation = !locationFilter || item.location.id === locationFilter;
        const matchesStockLevel = !stockLevelFilter || 
                                (stockLevelFilter === 'in_stock' && item.quantity > 0) ||
                                (stockLevelFilter === 'low_stock' && item.product.low_stock_threshold && item.quantity <= item.product.low_stock_threshold);
        return matchesSearch && matchesLocation && matchesStockLevel;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'location_asc':
                return a.location.name.localeCompare(b.location.name);
            case 'location_desc':
                return b.location.name.localeCompare(a.location.name);
            case 'product_asc':
                return a.product.name.localeCompare(b.product.name);
            case 'product_desc':
                return b.product.name.localeCompare(a.product.name);
            case 'quantity_asc':
                return a.quantity - b.quantity;
            case 'quantity_desc':
                return b.quantity - a.quantity;
            default:
                return 0;
        }
    });
    
    displayStockByLocation(filtered);
}

function displayStockByLocation(stockItems) {
    const container = document.getElementById('stockByLocationList');
    
    if (stockItems.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No stock found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">Location</div>';
    html += '<div class="table-cell">Product</div>';
    html += '<div class="table-cell">SKU</div>';
    html += '<div class="table-cell">Quantity</div>';
    html += '</div>';
    
    stockItems.forEach(item => {
        let stockColor = '#10b981'; // green
        if (item.product.low_stock_threshold && item.quantity <= item.product.low_stock_threshold) {
            stockColor = '#f59e0b'; // orange
        }
        
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${item.location.name}</strong></div>`;
        html += `<div class="table-cell">${item.product.name}</div>`;
        html += `<div class="table-cell">${item.product.sku}</div>`;
        html += `<div class="table-cell" style="color: ${stockColor}; font-weight: 600;">${item.quantity}</div>`;
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Override loadStockByLocation to use new system
async function loadStockByLocation() {
    await loadStockByLocationWithStorage();
}


// ===== TRANSFERS FILTERS AND SORTING =====
let allTransfers = [];

async function loadTransfersWithStorage() {
    try {
        allTransfers = await apiCall('/documents?document_type=transfer');
        
        // Populate location filter dropdowns
        const locations = await apiCall('/locations');
        
        const sourceSelect = document.getElementById('transferSourceFilter');
        const destSelect = document.getElementById('transferDestFilter');
        
        sourceSelect.innerHTML = '<option value="">All Source Locations</option>';
        destSelect.innerHTML = '<option value="">All Destination Locations</option>';
        
        locations.forEach(location => {
            const sourceOption = document.createElement('option');
            sourceOption.value = location.id;
            sourceOption.textContent = location.name;
            sourceSelect.appendChild(sourceOption);
            
            const destOption = document.createElement('option');
            destOption.value = location.id;
            destOption.textContent = location.name;
            destSelect.appendChild(destOption);
        });
        
        applyTransferFilters();
    } catch (error) {
        console.error('Failed to load transfers:', error);
    }
}

function applyTransferFilters() {
    const searchTerm = document.getElementById('transferSearch').value.toLowerCase();
    const statusFilter = document.getElementById('transferStatusFilter').value;
    const sourceFilter = document.getElementById('transferSourceFilter').value;
    const destFilter = document.getElementById('transferDestFilter').value;
    const sortBy = document.getElementById('transferSortBy').value;
    
    let filtered = allTransfers.filter(transfer => {
        const matchesSearch = transfer.product_name.toLowerCase().includes(searchTerm) || 
                            transfer.id.toLowerCase().includes(searchTerm);
        const matchesStatus = !statusFilter || transfer.status === statusFilter;
        const matchesSource = !sourceFilter || transfer.source_location_id === sourceFilter;
        const matchesDest = !destFilter || transfer.destination_location_id === destFilter;
        return matchesSearch && matchesStatus && matchesSource && matchesDest;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'date_asc':
                return new Date(a.created_at) - new Date(b.created_at);
            case 'date_desc':
                return new Date(b.created_at) - new Date(a.created_at);
            case 'product_asc':
                return a.product_name.localeCompare(b.product_name);
            case 'product_desc':
                return b.product_name.localeCompare(a.product_name);
            case 'quantity_asc':
                return a.quantity - b.quantity;
            case 'quantity_desc':
                return b.quantity - a.quantity;
            default:
                return 0;
        }
    });
    
    displayTransfers(filtered);
}

function displayTransfers(transfers) {
    const container = document.getElementById('transfersList');
    
    if (transfers.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No transfers found</h3><p>Try adjusting your filters</p></div>';
        return;
    }
    
    let html = '<div class="table-row header">';
    html += '<div class="table-cell">ID</div>';
    html += '<div class="table-cell">Product</div>';
    html += '<div class="table-cell">From Location</div>';
    html += '<div class="table-cell">To Location</div>';
    html += '<div class="table-cell">Quantity</div>';
    html += '<div class="table-cell">Status</div>';
    html += '<div class="table-cell">Created</div>';
    html += '<div class="table-cell">Actions</div>';
    html += '</div>';
    
    transfers.forEach(transfer => {
        html += '<div class="table-row">';
        html += `<div class="table-cell"><strong>${transfer.id.substring(0, 8)}</strong></div>`;
        html += `<div class="table-cell">${transfer.product_name}</div>`;
        html += `<div class="table-cell">${transfer.source_location_name}</div>`;
        html += `<div class="table-cell">${transfer.destination_location_name}</div>`;
        html += `<div class="table-cell">${transfer.quantity}</div>`;
        html += `<div class="table-cell"><span class="badge ${transfer.status}">${transfer.status}</span></div>`;
        html += `<div class="table-cell">${new Date(transfer.created_at).toLocaleDateString()}</div>`;
        html += '<div class="table-cell">';
        if (transfer.status === 'pending') {
            html += `<button class="btn-small btn-validate" onclick="validateTransfer('${transfer.id}')">Validate</button>`;
        }
        html += '</div>';
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// Override loadTransfers to use new system
async function loadTransfers() {
    await loadTransfersWithStorage();
}


// ===== SIDEBAR AND USER MENU TOGGLE =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

function toggleUserMenu() {
    const userMenu = document.getElementById('userMenuDropdown');
    userMenu.classList.toggle('active');
}

// Close user menu when clicking outside
document.addEventListener('click', function(event) {
    const userMenu = document.getElementById('userMenuDropdown');
    const userAvatar = document.querySelector('.user-avatar');
    
    if (userMenu && !userMenu.contains(event.target) && !userAvatar.contains(event.target)) {
        userMenu.classList.remove('active');
    }
});

// Close sidebar when clicking on a nav button
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('nav-btn')) {
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    }
});

function showAccountSettings() {
    alert('Account settings feature coming soon!');
    toggleUserMenu();
}

