# Design Document: CoreInventory

## Overview

CoreInventory is a straightforward inventory management system that tracks products, stock levels, and movements across multiple locations. The design emphasizes simplicity and clarity - each component has a single, well-defined responsibility.

The system follows a document-based workflow where operations (receipts, deliveries, transfers, adjustments) are created as pending documents, then validated to update stock. This provides a clear audit trail while keeping the implementation simple.

### Core Principles

- **Simple data flow**: Documents → Validation → Stock Update → History Log
- **Clear boundaries**: Authentication, document management, stock tracking, and reporting are separate concerns
- **Minimal state**: Stock quantities and document status are the primary mutable state
- **Append-only history**: All movements are logged permanently for audit purposes

### Technology Stack

The design is technology-agnostic but assumes:
- Relational database for structured data and transactional integrity
- Web-based interface for accessibility
- Standard authentication mechanisms (session or token-based)

## Architecture

The system uses a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  (Dashboard, Product Management, Document Processing)    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Business Logic                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Authenticator│  │  Validator   │  │ Stock Manager│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  (Products, Stock, Documents, Move_History, Users)       │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Authenticator**
- Handles user signup, login, password reset
- Manages session state
- Validates credentials

**Validator**
- Validates documents (receipts, deliveries, transfers, adjustments)
- Enforces business rules (sufficient stock, valid locations)
- Triggers stock updates and history logging

**Stock Manager**
- Updates stock quantities
- Checks stock availability
- Calculates running balances
- Manages low stock alerts

**Document Manager**
- Creates and retrieves documents
- Tracks document status
- Prevents modification of validated documents

**History Logger**
- Records all stock movements
- Maintains move history and stock ledger
- Provides filtering and export capabilities

## Components and Interfaces

### Authenticator

```
signup(email: string, password: string) -> Result<User, Error>
login(email: string, password: string) -> Result<Session, Error>
requestPasswordReset(email: string) -> Result<void, Error>
resetPassword(otp: string, newPassword: string) -> Result<void, Error>
logout(sessionId: string) -> Result<void, Error>
validateSession(sessionId: string) -> Result<User, Error>
```

### Validator

```
validateReceipt(receiptId: string, userId: string) -> Result<void, Error>
validateDeliveryOrder(orderId: string, userId: string) -> Result<void, Error>
validateTransfer(transferId: string, userId: string) -> Result<void, Error>
validateStockAdjustment(adjustmentId: string, userId: string) -> Result<void, Error>
```

The Validator coordinates with Stock Manager and History Logger to ensure atomic updates.

### Stock Manager

```
getStock(productId: string, locationId: string) -> number
updateStock(productId: string, locationId: string, delta: number) -> Result<void, Error>
checkAvailability(productId: string, locationId: string, required: number) -> boolean
getStockByProduct(productId: string) -> List<LocationStock>
getLowStockProducts(threshold: number) -> List<Product>
```

### Document Manager

```
createReceipt(data: ReceiptData) -> Result<Receipt, Error>
createDeliveryOrder(data: DeliveryOrderData) -> Result<DeliveryOrder, Error>
createTransfer(data: TransferData) -> Result<Transfer, Error>
createStockAdjustment(data: AdjustmentData) -> Result<StockAdjustment, Error>
getDocument(documentId: string) -> Result<Document, Error>
listDocuments(filters: DocumentFilters) -> List<Document>
```

### History Logger

```
logMovement(movement: MovementData) -> Result<void, Error>
getMoveHistory(filters: HistoryFilters) -> List<MoveHistory>
getStockLedger(filters: LedgerFilters) -> List<LedgerEntry>
exportLedger(filters: LedgerFilters, format: string) -> Result<File, Error>
```

### Product Manager

```
createProduct(data: ProductData) -> Result<Product, Error>
updateProduct(productId: string, data: ProductData) -> Result<Product, Error>
getProduct(productId: string) -> Result<Product, Error>
searchProducts(query: string) -> List<Product>
filterProducts(filters: ProductFilters) -> List<Product>
```

### Location Manager

```
createLocation(data: LocationData) -> Result<Location, Error>
updateLocation(locationId: string, data: LocationData) -> Result<Location, Error>
archiveLocation(locationId: string) -> Result<void, Error>
getLocation(locationId: string) -> Result<Location, Error>
listLocations() -> List<Location>
```

## Data Models

### User
```
id: string (UUID)
email: string (unique)
password_hash: string
name: string
created_at: timestamp
updated_at: timestamp
```

### Product
```
id: string (UUID)
sku: string (unique)
name: string
category: string
unit_of_measure: string
low_stock_threshold: number (optional)
created_at: timestamp
updated_at: timestamp
```

### Stock
```
id: string (UUID)
product_id: string (foreign key)
location_id: string (foreign key)
quantity: number
updated_at: timestamp

unique constraint: (product_id, location_id)
```

### Location
```
id: string (UUID)
name: string
type: enum (warehouse, rack, floor_area)
parent_id: string (optional, foreign key to Location)
is_archived: boolean
created_at: timestamp
```

### Receipt
```
id: string (UUID)
supplier_name: string
supplier_contact: string (optional)
status: enum (pending, validated)
validated_by: string (optional, foreign key to User)
validated_at: timestamp (optional)
created_by: string (foreign key to User)
created_at: timestamp
```

### Receipt_Item
```
id: string (UUID)
receipt_id: string (foreign key)
product_id: string (foreign key)
location_id: string (foreign key)
expected_quantity: number
received_quantity: number
```

### Delivery_Order
```
id: string (UUID)
customer_name: string
customer_contact: string (optional)
status: enum (pending, picking, packing, validated)
validated_by: string (optional, foreign key to User)
validated_at: timestamp (optional)
created_by: string (foreign key to User)
created_at: timestamp
```

### Delivery_Order_Item
```
id: string (UUID)
delivery_order_id: string (foreign key)
product_id: string (foreign key)
location_id: string (foreign key)
requested_quantity: number
delivered_quantity: number
```

### Transfer
```
id: string (UUID)
source_location_id: string (foreign key)
destination_location_id: string (foreign key)
product_id: string (foreign key)
quantity: number
status: enum (pending, validated)
validated_by: string (optional, foreign key to User)
validated_at: timestamp (optional)
created_by: string (foreign key to User)
created_at: timestamp
```

### Stock_Adjustment
```
id: string (UUID)
product_id: string (foreign key)
location_id: string (foreign key)
recorded_quantity: number
physical_quantity: number
adjustment_difference: number (computed: physical - recorded)
reason: string
status: enum (pending, validated)
validated_by: string (optional, foreign key to User)
validated_at: timestamp (optional)
created_by: string (foreign key to User)
created_at: timestamp
```

### Move_History
```
id: string (UUID)
product_id: string (foreign key)
location_id: string (foreign key)
quantity_change: number (positive for increase, negative for decrease)
document_type: enum (receipt, delivery_order, transfer, stock_adjustment, initial_stock)
document_id: string
source_location_id: string (optional, for transfers)
destination_location_id: string (optional, for transfers)
reason: string (optional)
user_id: string (foreign key to User)
timestamp: timestamp
```

### Stock_Ledger
```
id: string (UUID)
product_id: string (foreign key)
location_id: string (foreign key)
quantity_change: number
running_balance: number
document_type: enum
document_id: string
user_id: string (foreign key to User)
timestamp: timestamp
```

Note: Stock_Ledger can be a materialized view or computed from Move_History with running balance calculation.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication Round Trip

*For any* valid email and password combination, signing up a user and then logging in with those credentials should succeed and return a valid session.

**Validates: Requirements 1.1, 1.2**

### Property 2: Password Reset Round Trip

*For any* user account, requesting a password reset, using the generated OTP to set a new password, and then logging in with the new password should succeed.

**Validates: Requirements 1.4**

### Property 3: Invalid Credentials Rejection

*For any* invalid credentials (wrong password, non-existent email, or malformed input), authentication attempts should fail with a descriptive error message.

**Validates: Requirements 1.5**

### Property 4: Session Persistence

*For any* authenticated user session, subsequent requests using that session should remain valid until explicit logout.

**Validates: Requirements 1.6, 14.4**

### Property 5: Dashboard Count Accuracy

*For any* set of products, locations, and documents, the dashboard counts (total products, low stock products, zero stock products, pending documents) should equal the actual count of entities matching each criterion.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 6: Product Creation Completeness

*For any* valid product data (name, SKU, category, unit of measure, initial stock), creating a product should result in a product existing with all specified attributes and the correct stock level.

**Validates: Requirements 3.1**

### Property 7: SKU Uniqueness Enforcement

*For any* two products with the same SKU, the second product creation should fail with an error indicating SKU conflict.

**Validates: Requirements 3.2**

### Property 8: Product Update Preserves SKU

*For any* existing product and new product details, updating the product should change the specified fields while preserving the original SKU unchanged.

**Validates: Requirements 3.3**

### Property 9: Initial Stock Creates History

*For any* product created with initial stock quantity > 0, there should exist a corresponding Move_History entry with document_type = "initial_stock" and quantity_change equal to the initial quantity.

**Validates: Requirements 3.4**

### Property 10: Product Search Completeness

*For any* product in the system, searching by its exact SKU or any substring of its name should return that product in the search results.

**Validates: Requirements 3.5, 15.1, 15.3, 15.4**

### Property 11: Filter Result Correctness

*For any* filter criteria (category, document type, status, location, date range), all returned results should match the specified criteria, and no matching entities should be excluded.

**Validates: Requirements 3.6, 8.3, 11.3, 12.1, 12.2, 12.3, 12.4**

### Property 12: Multiple Filter Conjunction

*For any* combination of multiple filters applied simultaneously, the results should match all filter criteria (AND logic), with each result satisfying every specified condition.

**Validates: Requirements 12.5**

### Property 13: Document Creation Completeness

*For any* valid document data (receipt, delivery order, transfer, or stock adjustment), creating the document should succeed and store all specified items with their quantities.

**Validates: Requirements 4.1, 4.2, 5.1, 5.2, 6.1, 7.1**

### Property 14: New Documents Start Pending

*For any* newly created document (receipt, delivery order, transfer, stock adjustment), its initial status should be "pending".

**Validates: Requirements 4.3**

### Property 15: Receipt Validation Increases Stock

*For any* receipt with items, validating the receipt should increase stock for each product-location pair by the received quantity specified in the receipt.

**Validates: Requirements 4.4**

### Property 16: Delivery Validation Decreases Stock

*For any* delivery order with items and sufficient stock, validating the order should decrease stock for each product-location pair by the delivered quantity.

**Validates: Requirements 5.4**

### Property 17: Insufficient Stock Prevents Delivery

*For any* delivery order where any item's requested quantity exceeds available stock at the specified location, validation should fail with an error indicating insufficient stock.

**Validates: Requirements 5.5**

### Property 18: Transfer Validates Source Stock

*For any* transfer, if the source location has insufficient stock (quantity < transfer amount), the transfer creation or validation should fail with an error.

**Validates: Requirements 6.2**

### Property 19: Transfer Conserves Quantity

*For any* validated transfer, the stock decrease at the source location should exactly equal the stock increase at the destination location (conservation of quantity).

**Validates: Requirements 6.3**

### Property 20: Adjustment Difference Calculation

*For any* stock adjustment, the adjustment_difference field should equal (physical_quantity - recorded_quantity).

**Validates: Requirements 7.2**

### Property 21: Adjustment Sets Physical Quantity

*For any* stock adjustment, validating the adjustment should set the stock at the specified location to exactly the physical_quantity value.

**Validates: Requirements 7.3**

### Property 22: Adjustment Requires Reason

*For any* stock adjustment without a reason field, creation should fail with an error indicating that reason is required.

**Validates: Requirements 7.5**

### Property 23: Stock Changes Create History

*For any* stock change (from receipt, delivery, transfer, or adjustment validation), the system should create a corresponding Move_History entry with correct product, location, quantity_change, document_type, document_id, and user_id.

**Validates: Requirements 4.5, 5.6, 6.4, 7.4, 8.1**

### Property 24: Move History Completeness

*For any* Move_History entry, it should contain all required fields: timestamp, product_id, location_id, quantity_change, document_type, document_id, and user_id.

**Validates: Requirements 8.2**

### Property 25: Move History Chronological Order

*For any* list of Move_History entries returned by the system, each entry's timestamp should be greater than or equal to the next entry's timestamp (reverse chronological order).

**Validates: Requirements 8.4**

### Property 26: Stock Ledger Running Balance

*For any* product at a location, the running balance in the Stock_Ledger should equal the sum of all quantity_change values in Move_History for that product-location pair up to that point in time.

**Validates: Requirements 9.2**

### Property 27: Low Stock Alert Presence

*For any* product with a configured low_stock_threshold, if current stock < threshold, then a low stock alert should be present; if stock >= threshold, no alert should be present.

**Validates: Requirements 10.1, 10.4**

### Property 28: Threshold Configuration Persistence

*For any* product and threshold value, setting the low_stock_threshold should persist the value and make it retrievable in subsequent queries.

**Validates: Requirements 10.3**

### Property 29: Location Stock Independence

*For any* product at multiple locations, stock changes at one location should not affect the stock quantity at any other location.

**Validates: Requirements 11.2, 11.4**

### Property 30: Validated Documents Are Immutable

*For any* document (receipt, delivery order, transfer, stock adjustment) with status = "validated", any attempt to modify the document should fail with an error.

**Validates: Requirements 4.6, 5.7, 6.6**

### Property 31: Location Hierarchy Preservation

*For any* location with a parent_id, the parent relationship should be maintained and retrievable, allowing navigation of the location hierarchy.

**Validates: Requirements 13.2**

### Property 32: Location With Stock Cannot Be Deleted

*For any* location with existing stock (any product has quantity > 0 at that location), attempts to delete or archive the location should fail with an error.

**Validates: Requirements 13.3**

### Property 33: Profile Update Persistence

*For any* user and updated profile data (name, email, password), updating the profile should persist the changes and make them retrievable in subsequent queries or authentication attempts.

**Validates: Requirements 14.1, 14.2, 14.3**

### Property 34: Search Results Include Required Fields

*For any* search result, the returned data should include product name, SKU, category, and current stock level.

**Validates: Requirements 15.5**

## Error Handling

The system uses a Result type pattern for error handling, making failures explicit and forcing callers to handle errors.

### Error Categories

**Authentication Errors**
- Invalid credentials
- Email already exists
- Invalid OTP
- Session expired
- Unauthorized access

**Validation Errors**
- Insufficient stock
- Duplicate SKU
- Invalid document status
- Missing required fields
- Invalid quantity (negative or zero where positive required)

**Business Rule Errors**
- Cannot modify validated document
- Cannot delete location with stock
- Cannot transfer to same location
- Invalid location hierarchy

**Data Errors**
- Entity not found
- Foreign key constraint violation
- Unique constraint violation

### Error Response Format

All errors should include:
- Error code (for programmatic handling)
- Human-readable message
- Context (entity ID, field name, etc.)
- Timestamp

Example:
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Cannot validate delivery order: insufficient stock for product SKU-123 at location WH-01",
    "context": {
      "product_id": "uuid-123",
      "location_id": "uuid-456",
      "required": 100,
      "available": 50
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Transaction Handling

Document validation operations must be atomic:
1. Check all preconditions (stock availability, valid status)
2. Update stock for all items
3. Create all history entries
4. Update document status

If any step fails, all changes must be rolled back. Use database transactions to ensure atomicity.

### Idempotency

Validation operations should be idempotent - validating an already-validated document should return success without side effects (no duplicate stock changes or history entries).

## Testing Strategy

### Dual Testing Approach

The system requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples demonstrating correct behavior
- Edge cases (empty lists, zero quantities, boundary values)
- Error conditions (invalid input, constraint violations)
- Integration points between components

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Invariants that must be maintained
- Round-trip properties (serialize/deserialize, create/retrieve)

Both approaches are complementary - unit tests catch concrete bugs and document expected behavior, while property tests verify general correctness across a wide input space.

### Property-Based Testing Configuration

**Library Selection:**
- JavaScript/TypeScript: fast-check
- Python: Hypothesis
- Java: jqwik
- C#: FsCheck
- Go: gopter

**Test Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `Feature: core-inventory, Property {number}: {property_text}`

**Example Property Test Structure:**

```typescript
// Feature: core-inventory, Property 19: Transfer Conserves Quantity
test('transfer conserves quantity', () => {
  fc.assert(
    fc.property(
      fc.record({
        product: arbitraryProduct(),
        sourceLocation: arbitraryLocation(),
        destLocation: arbitraryLocation(),
        quantity: fc.integer({ min: 1, max: 1000 })
      }),
      async ({ product, sourceLocation, destLocation, quantity }) => {
        // Setup: ensure source has sufficient stock
        await setStock(product.id, sourceLocation.id, quantity + 100);
        
        const initialSource = await getStock(product.id, sourceLocation.id);
        const initialDest = await getStock(product.id, destLocation.id);
        
        // Execute transfer
        const transfer = await createTransfer({
          productId: product.id,
          sourceLocationId: sourceLocation.id,
          destinationLocationId: destLocation.id,
          quantity
        });
        await validateTransfer(transfer.id);
        
        // Verify conservation
        const finalSource = await getStock(product.id, sourceLocation.id);
        const finalDest = await getStock(product.id, destLocation.id);
        
        expect(initialSource - finalSource).toBe(quantity);
        expect(finalDest - initialDest).toBe(quantity);
        expect((initialSource + initialDest)).toBe(finalSource + finalDest);
      }
    ),
    { numRuns: 100 }
  );
});
```

### Unit Test Coverage

**Authentication Module:**
- Successful signup and login
- Password reset flow
- Invalid credentials handling
- Session management

**Product Management:**
- Product CRUD operations
- SKU uniqueness enforcement
- Search and filtering
- Initial stock handling

**Document Processing:**
- Receipt validation flow
- Delivery order validation with stock checks
- Transfer between locations
- Stock adjustment processing

**Stock Management:**
- Stock updates
- Multi-location tracking
- Low stock alerts
- Running balance calculation

**History and Audit:**
- Move history creation
- Stock ledger accuracy
- Filtering and export

### Integration Testing

Test complete workflows:
1. Create product → Add stock via receipt → Deliver to customer → Verify history
2. Create product at location A → Transfer to location B → Verify stock at both locations
3. Physical count differs → Create adjustment → Verify stock and history
4. Multiple concurrent operations → Verify no race conditions or lost updates

### Performance Testing

- Search performance with 100,000+ products
- Dashboard KPI calculation with large datasets
- Concurrent document validation
- History query performance with millions of entries

### Test Data Generation

Use property-based testing libraries to generate:
- Random products with valid SKUs, names, categories
- Random locations with valid hierarchies
- Random documents with valid item lists
- Random stock levels and quantities
- Random users and sessions

Ensure generators produce both typical and edge cases (empty strings, very long strings, zero quantities, very large quantities, etc.).
