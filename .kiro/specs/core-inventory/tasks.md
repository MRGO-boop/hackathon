# Implementation Plan: CoreInventory

## Overview

This plan implements CoreInventory as a document-based inventory management system following the layered architecture from the design. Implementation uses Python with a relational database for transactional integrity. The workflow follows: Documents → Validation → Stock Update → History Log.

## Tasks

- [x] 1. Set up project structure and database schema
  - Create Python project with virtual environment
  - Set up database connection and migration framework
  - Define database schema for all tables (User, Product, Stock, Location, Receipt, Receipt_Item, Delivery_Order, Delivery_Order_Item, Transfer, Stock_Adjustment, Move_History, Stock_Ledger)
  - Create database migration scripts
  - _Requirements: All requirements depend on data layer_

- [x] 2. Implement Authenticator component
  - [x] 2.1 Implement user signup and login
    - Write `signup(email, password)` function with password hashing
    - Write `login(email, password)` function with session creation
    - Write `validateSession(sessionId)` function
    - _Requirements: 1.1, 1.2, 1.6_
  
  - [ ]* 2.2 Write property test for authentication round trip
    - **Property 1: Authentication Round Trip**
    - **Validates: Requirements 1.1, 1.2**
  
  - [x] 2.3 Implement password reset flow
    - Write `requestPasswordReset(email)` function with OTP generation and email sending
    - Write `resetPassword(otp, newPassword)` function
    - _Requirements: 1.3, 1.4_
  
  - [ ]* 2.4 Write property test for password reset round trip
    - **Property 2: Password Reset Round Trip**
    - **Validates: Requirements 1.4**
  
  - [x] 2.5 Implement logout and error handling
    - Write `logout(sessionId)` function
    - Implement descriptive error messages for authentication failures
    - _Requirements: 1.5, 14.4_
  
  - [x] 2.6 Write property test for invalid credentials rejection
    - **Property 3: Invalid Credentials Rejection**
    - **Validates: Requirements 1.5**
  
  - [x] 2.7 Write property test for session persistence
    - **Property 4: Session Persistence**
    - **Validates: Requirements 1.6, 14.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Product Manager component
  - [x] 4.1 Implement product CRUD operations
    - Write `createProduct(data)` function with SKU uniqueness enforcement
    - Write `updateProduct(productId, data)` function that preserves SKU
    - Write `getProduct(productId)` function
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 4.2 Write property tests for product operations
    - **Property 6: Product Creation Completeness**
    - **Property 7: SKU Uniqueness Enforcement**
    - **Property 8: Product Update Preserves SKU**
    - **Validates: Requirements 3.1, 3.2, 3.3**
  
  - [x] 4.3 Implement product search and filtering
    - Write `searchProducts(query)` function with SKU exact match and name partial match
    - Write `filterProducts(filters)` function for category filtering
    - _Requirements: 3.5, 3.6, 15.1, 15.3, 15.4, 15.5_
  
  - [x] 4.4 Write property tests for search and filtering
    - **Property 10: Product Search Completeness**
    - **Property 11: Filter Result Correctness**
    - **Property 34: Search Results Include Required Fields**
    - **Validates: Requirements 3.5, 3.6, 15.1, 15.3, 15.4, 15.5**

- [x] 5. Implement Location Manager component
  - [x] 5.1 Implement location management
    - Write `createLocation(data)` function
    - Write `updateLocation(locationId, data)` function
    - Write `archiveLocation(locationId)` function with stock check
    - Write `getLocation(locationId)` and `listLocations()` functions
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ]* 5.2 Write property tests for location operations
    - **Property 31: Location Hierarchy Preservation**
    - **Property 32: Location With Stock Cannot Be Deleted**
    - **Validates: Requirements 13.2, 13.3**

- [x] 6. Implement Stock Manager component
  - [x] 6.1 Implement stock tracking operations
    - Write `getStock(productId, locationId)` function
    - Write `updateStock(productId, locationId, delta)` function with transaction support
    - Write `checkAvailability(productId, locationId, required)` function
    - Write `getStockByProduct(productId)` function for multi-location view
    - _Requirements: 11.2, 11.4_
  
  - [x] 6.2 Implement low stock alert logic
    - Write `getLowStockProducts(threshold)` function
    - Implement threshold configuration per product
    - _Requirements: 10.1, 10.3, 10.4_
  
  - [ ]* 6.3 Write property tests for stock operations
    - **Property 27: Low Stock Alert Presence**
    - **Property 28: Threshold Configuration Persistence**
    - **Property 29: Location Stock Independence**
    - **Validates: Requirements 10.1, 10.3, 10.4, 11.2, 11.4**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement History Logger component
  - [x] 8.1 Implement move history tracking
    - Write `logMovement(movement)` function to create Move_History entries
    - Write `getMoveHistory(filters)` function with date range, product, location, and document type filtering
    - Ensure chronological ordering (reverse)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 8.2 Implement stock ledger functionality
    - Write `getStockLedger(filters)` function with running balance calculation
    - Write `exportLedger(filters, format)` function for data export
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ]* 8.3 Write property tests for history operations
    - **Property 23: Stock Changes Create History**
    - **Property 24: Move History Completeness**
    - **Property 25: Move History Chronological Order**
    - **Property 26: Stock Ledger Running Balance**
    - **Validates: Requirements 4.5, 5.6, 6.4, 7.4, 8.1, 8.2, 8.4, 9.2**

- [x] 9. Implement Document Manager component
  - [x] 9.1 Implement receipt document operations
    - Write `createReceipt(data)` function with pending status
    - Write `getDocument(documentId)` function
    - Write `listDocuments(filters)` function with document type, status, and location filtering
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 9.2 Implement delivery order document operations
    - Write `createDeliveryOrder(data)` function with pending status
    - Support status transitions (pending → picking → packing → validated)
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 9.3 Implement transfer document operations
    - Write `createTransfer(data)` function with source stock validation
    - _Requirements: 6.1, 6.2_
  
  - [x] 9.4 Implement stock adjustment document operations
    - Write `createStockAdjustment(data)` function with required reason field
    - Calculate adjustment_difference as (physical_quantity - recorded_quantity)
    - _Requirements: 7.1, 7.2, 7.5_
  
  - [ ]* 9.5 Write property tests for document operations
    - **Property 13: Document Creation Completeness**
    - **Property 14: New Documents Start Pending**
    - **Property 20: Adjustment Difference Calculation**
    - **Property 22: Adjustment Requires Reason**
    - **Validates: Requirements 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 7.1, 7.2, 7.5**

- [x] 10. Implement Validator component
  - [x] 10.1 Implement receipt validation
    - Write `validateReceipt(receiptId, userId)` function
    - Coordinate with Stock Manager to increase stock for each item
    - Coordinate with History Logger to create Move_History entries
    - Use database transactions for atomicity
    - Implement idempotency (validating already-validated receipt returns success)
    - _Requirements: 4.4, 4.5, 4.6_
  
  - [ ]* 10.2 Write property tests for receipt validation
    - **Property 15: Receipt Validation Increases Stock**
    - **Property 9: Initial Stock Creates History** (for products with initial stock)
    - **Property 30: Validated Documents Are Immutable**
    - **Validates: Requirements 3.4, 4.4, 4.5, 4.6**
  
  - [x] 10.3 Implement delivery order validation
    - Write `validateDeliveryOrder(orderId, userId)` function
    - Check stock availability before validation
    - Coordinate with Stock Manager to decrease stock for each item
    - Coordinate with History Logger to create Move_History entries
    - Return error if insufficient stock
    - Use database transactions for atomicity
    - _Requirements: 5.4, 5.5, 5.6, 5.7_
  
  - [ ]* 10.4 Write property tests for delivery validation
    - **Property 16: Delivery Validation Decreases Stock**
    - **Property 17: Insufficient Stock Prevents Delivery**
    - **Validates: Requirements 5.4, 5.5, 5.6**
  
  - [x] 10.5 Implement transfer validation
    - Write `validateTransfer(transferId, userId)` function
    - Validate sufficient stock at source location
    - Coordinate with Stock Manager to decrease source and increase destination stock
    - Coordinate with History Logger to create Move_History entry with both locations
    - Use database transactions for atomicity
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 10.6 Write property tests for transfer validation
    - **Property 18: Transfer Validates Source Stock**
    - **Property 19: Transfer Conserves Quantity**
    - **Validates: Requirements 6.2, 6.3, 6.4**
  
  - [x] 10.7 Implement stock adjustment validation
    - Write `validateStockAdjustment(adjustmentId, userId)` function
    - Coordinate with Stock Manager to set stock to physical_quantity
    - Coordinate with History Logger to create Move_History entry with reason
    - Use database transactions for atomicity
    - _Requirements: 7.3, 7.4_
  
  - [ ]* 10.8 Write property tests for adjustment validation
    - **Property 21: Adjustment Sets Physical Quantity**
    - **Validates: Requirements 7.3, 7.4**

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement Dashboard functionality
  - [x] 12.1 Implement dashboard KPI calculations
    - Write function to calculate total product count
    - Write function to calculate low stock product count
    - Write function to calculate zero stock product count
    - Write function to calculate pending document counts (receipts, delivery orders, transfers)
    - Ensure real-time updates when stock changes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 12.2 Write property test for dashboard accuracy
    - **Property 5: Dashboard Count Accuracy**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 13. Implement User Profile Management
  - [x] 13.1 Implement profile operations
    - Write function to get user profile information
    - Write function to update user name and email
    - Write function to change password
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [x] 13.2 Write property test for profile updates
    - **Property 33: Profile Update Persistence**
    - **Validates: Requirements 14.1, 14.2, 14.3**

- [x] 14. Implement dynamic filtering system
  - [x] 14.1 Implement multi-filter support
    - Extend `listDocuments(filters)` to support multiple simultaneous filters
    - Extend `filterProducts(filters)` to support multiple simultaneous filters
    - Implement real-time result updates
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [x] 14.2 Write property test for multiple filters
    - **Property 12: Multiple Filter Conjunction**
    - **Validates: Requirements 12.5**

- [x] 15. Implement error handling and validation
  - [x] 15.1 Create error response format
    - Define error classes for each error category (Authentication, Validation, Business Rule, Data)
    - Implement error response format with code, message, context, and timestamp
    - _Requirements: All requirements depend on proper error handling_
  
  - [x] 15.2 Add input validation
    - Validate all user inputs (email format, positive quantities, non-empty required fields)
    - Return descriptive validation errors
    - _Requirements: All requirements_

- [x] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Integration and API layer
  - [x] 17.1 Create REST API endpoints or web interface
    - Wire all components together through API layer or web framework
    - Implement authentication middleware
    - Implement request/response handling
    - _Requirements: All requirements_
  
  - [ ]* 17.2 Write integration tests
    - Test complete workflows: create product → receipt → delivery → verify history
    - Test transfer workflow: create product at location A → transfer to B → verify both locations
    - Test adjustment workflow: create adjustment → validate → verify stock and history
    - _Requirements: All requirements_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- All validation operations use database transactions for atomicity
- Implementation uses Python with a relational database (PostgreSQL, MySQL, or SQLite)
