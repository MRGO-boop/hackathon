# Requirements Document

## Introduction

CoreInventory is a modular Inventory Management System (IMS) that digitizes and streamlines all stock-related operations within a business. The system replaces manual registers, Excel sheets, and scattered tracking methods with a centralized, real-time application. It supports multi-warehouse operations, real-time stock tracking, and comprehensive movement history logging.

## Glossary

- **System**: The CoreInventory application
- **User**: An authenticated person using the System (Inventory Manager or Warehouse Staff)
- **Product**: An item tracked in inventory with SKU, name, category, and unit of measure
- **Stock**: The quantity of a Product available at a specific Location
- **Location**: A physical place where Stock is stored (warehouse, rack, floor area)
- **Receipt**: An incoming goods document that increases Stock when validated
- **Delivery_Order**: An outgoing goods document that decreases Stock when validated
- **Transfer**: A movement of Stock between two Locations within the organization
- **Stock_Adjustment**: A correction document to reconcile physical count with recorded Stock
- **Move_History**: A log entry recording any Stock movement with timestamp and details
- **Stock_Ledger**: A comprehensive log of all Stock movements across all Products
- **SKU**: Stock Keeping Unit - a unique identifier for each Product
- **KPI**: Key Performance Indicator displayed on the Dashboard
- **Low_Stock_Threshold**: A configurable quantity below which a Product triggers a low stock alert
- **Validator**: The component responsible for validating documents and updating Stock
- **Authenticator**: The component responsible for user authentication and authorization

## Requirements

### Requirement 1: User Authentication

**User Story:** As a User, I want to securely access the System, so that only authorized personnel can manage inventory.

#### Acceptance Criteria

1. THE Authenticator SHALL provide signup functionality with email and password
2. THE Authenticator SHALL provide login functionality with email and password
3. WHEN a User requests password reset, THE Authenticator SHALL send a one-time password (OTP) to the User's email
4. WHEN a valid OTP is provided, THE Authenticator SHALL allow the User to set a new password
5. WHEN authentication fails, THE Authenticator SHALL return a descriptive error message
6. THE Authenticator SHALL maintain session state for authenticated Users

### Requirement 2: Dashboard Display

**User Story:** As an Inventory Manager, I want to view key metrics at a glance, so that I can quickly assess inventory status.

#### Acceptance Criteria

1. THE System SHALL display total count of Products
2. THE System SHALL display count of Products below Low_Stock_Threshold
3. THE System SHALL display count of Products with zero Stock
4. THE System SHALL display count of pending Receipts
5. THE System SHALL display count of pending Delivery_Orders
6. THE System SHALL display count of pending Transfers
7. THE System SHALL update all KPIs in real-time when Stock changes

### Requirement 3: Product Management

**User Story:** As an Inventory Manager, I want to create and manage Products, so that I can track all items in inventory.

#### Acceptance Criteria

1. THE System SHALL allow creation of Products with name, SKU, category, unit of measure, and initial Stock quantity
2. THE System SHALL enforce unique SKU for each Product
3. THE System SHALL allow updating Product details except SKU
4. WHEN initial Stock quantity is provided during Product creation, THE System SHALL record this as a Move_History entry
5. THE System SHALL allow searching Products by SKU or name
6. THE System SHALL allow filtering Products by category

### Requirement 4: Receipt Processing

**User Story:** As a Warehouse Staff member, I want to record incoming goods, so that Stock levels are accurately increased.

#### Acceptance Criteria

1. THE System SHALL allow creation of Receipts with supplier information and Product list
2. WHEN creating a Receipt, THE System SHALL allow adding multiple Products with expected quantities
3. THE System SHALL maintain Receipt status as pending until validated
4. WHEN a Receipt is validated, THE Validator SHALL increase Stock for each Product by the received quantity
5. WHEN a Receipt is validated, THE System SHALL record a Move_History entry for each Product
6. THE System SHALL prevent modification of validated Receipts

### Requirement 5: Delivery Order Processing

**User Story:** As a Warehouse Staff member, I want to process outgoing goods, so that Stock levels are accurately decreased.

#### Acceptance Criteria

1. THE System SHALL allow creation of Delivery_Orders with customer information and Product list
2. WHEN creating a Delivery_Order, THE System SHALL allow adding multiple Products with requested quantities
3. THE System SHALL maintain Delivery_Order status through picking and packing stages
4. WHEN a Delivery_Order is validated, THE Validator SHALL decrease Stock for each Product by the delivered quantity
5. IF Stock is insufficient for a Delivery_Order, THEN THE System SHALL prevent validation and display an error message
6. WHEN a Delivery_Order is validated, THE System SHALL record a Move_History entry for each Product
7. THE System SHALL prevent modification of validated Delivery_Orders

### Requirement 6: Internal Transfer Management

**User Story:** As a Warehouse Staff member, I want to move Stock between Locations, so that inventory is positioned where needed.

#### Acceptance Criteria

1. THE System SHALL allow creation of Transfers specifying source Location, destination Location, Product, and quantity
2. WHEN a Transfer is created, THE System SHALL validate that sufficient Stock exists at the source Location
3. WHEN a Transfer is validated, THE Validator SHALL decrease Stock at source Location and increase Stock at destination Location by the transfer quantity
4. WHEN a Transfer is validated, THE System SHALL record a Move_History entry with both source and destination Locations
5. THE System SHALL support Transfers between warehouses, between racks, and between floor areas
6. THE System SHALL prevent modification of validated Transfers

### Requirement 7: Stock Adjustment Processing

**User Story:** As an Inventory Manager, I want to adjust Stock levels, so that recorded quantities match physical counts.

#### Acceptance Criteria

1. THE System SHALL allow creation of Stock_Adjustments specifying Product, Location, recorded quantity, and physical quantity
2. THE System SHALL calculate the adjustment difference as physical quantity minus recorded quantity
3. WHEN a Stock_Adjustment is validated, THE Validator SHALL update Stock to match the physical quantity
4. WHEN a Stock_Adjustment is validated, THE System SHALL record a Move_History entry with the adjustment reason
5. THE System SHALL require a reason for all Stock_Adjustments

### Requirement 8: Move History Tracking

**User Story:** As an Inventory Manager, I want to view all Stock movements, so that I can audit inventory changes.

#### Acceptance Criteria

1. THE System SHALL record a Move_History entry for every Stock change
2. THE Move_History entry SHALL include timestamp, Product, Location, quantity change, document type, document reference, and User
3. THE System SHALL allow filtering Move_History by date range, Product, Location, and document type
4. THE System SHALL display Move_History in reverse chronological order
5. THE System SHALL maintain Move_History entries permanently without deletion

### Requirement 9: Stock Ledger Maintenance

**User Story:** As an Inventory Manager, I want a comprehensive log of all movements, so that I can trace any Stock discrepancy.

#### Acceptance Criteria

1. THE System SHALL maintain a Stock_Ledger with all Stock movements across all Products
2. THE Stock_Ledger SHALL include running balance for each Product at each Location
3. THE System SHALL allow exporting Stock_Ledger data for external analysis
4. THE Stock_Ledger SHALL be append-only with no deletion capability

### Requirement 10: Low Stock Alerts

**User Story:** As an Inventory Manager, I want to be notified of low Stock, so that I can reorder before stockouts occur.

#### Acceptance Criteria

1. WHERE Low_Stock_Threshold is configured for a Product, THE System SHALL display an alert when Stock falls below the threshold
2. THE System SHALL display low stock alerts on the Dashboard
3. THE System SHALL allow configuring Low_Stock_Threshold per Product
4. WHEN Stock increases above Low_Stock_Threshold, THE System SHALL remove the alert

### Requirement 11: Multi-Warehouse Support

**User Story:** As an Inventory Manager, I want to manage multiple warehouses, so that I can track Stock across all facilities.

#### Acceptance Criteria

1. THE System SHALL allow configuration of multiple Locations with name and type (warehouse, rack, floor area)
2. THE System SHALL track Stock separately for each Location
3. THE System SHALL allow filtering all operations by Location
4. THE System SHALL display Stock levels per Location for each Product

### Requirement 12: Dynamic Filtering

**User Story:** As a User, I want to filter documents and data, so that I can quickly find relevant information.

#### Acceptance Criteria

1. THE System SHALL allow filtering documents by document type (Receipt, Delivery_Order, Transfer, Stock_Adjustment)
2. THE System SHALL allow filtering documents by status (pending, validated)
3. THE System SHALL allow filtering documents by Location
4. THE System SHALL allow filtering Products by category
5. THE System SHALL apply multiple filters simultaneously
6. WHEN filters are applied, THE System SHALL update results in real-time

### Requirement 13: Warehouse Configuration

**User Story:** As an Inventory Manager, I want to configure warehouse settings, so that the System matches my operational structure.

#### Acceptance Criteria

1. THE System SHALL allow creating, updating, and archiving Locations
2. THE System SHALL allow configuring Location hierarchy (warehouse contains racks, racks contain positions)
3. THE System SHALL prevent deletion of Locations with existing Stock
4. THE System SHALL allow setting default Location for new Products

### Requirement 14: User Profile Management

**User Story:** As a User, I want to manage my profile, so that I can update my information and log out securely.

#### Acceptance Criteria

1. THE System SHALL display User profile information including name and email
2. THE System SHALL allow Users to update their name and email
3. THE System SHALL allow Users to change their password
4. THE System SHALL provide a logout function that terminates the User session
5. WHEN a User logs out, THE System SHALL redirect to the login page

### Requirement 15: SKU Search and Smart Filters

**User Story:** As a Warehouse Staff member, I want to quickly search for Products, so that I can process operations efficiently.

#### Acceptance Criteria

1. THE System SHALL provide search functionality accepting SKU or Product name
2. THE System SHALL return search results within 500 milliseconds for databases with up to 100,000 Products
3. THE System SHALL support partial matching on Product name
4. THE System SHALL support exact matching on SKU
5. THE System SHALL display search results with Product name, SKU, category, and current Stock level

