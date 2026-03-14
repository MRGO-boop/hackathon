"""Property-based tests for multi-filter functionality."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from core_inventory.components.product_manager import ProductManager, ProductError
from core_inventory.components.document_manager import DocumentManager, DocumentError
from core_inventory.models.product import Product
from core_inventory.models.location import Location, LocationType
from core_inventory.models.user import User
from core_inventory.models.receipt import Receipt, ReceiptStatus
from core_inventory.models.delivery_order import DeliveryOrder, DeliveryOrderStatus
from core_inventory.models.transfer import Transfer, TransferStatus
from core_inventory.models.stock_adjustment import StockAdjustment, StockAdjustmentStatus
import uuid


# Custom strategies for generating test data
@st.composite
def valid_sku(draw):
    """Generate valid SKU strings."""
    prefix = draw(st.sampled_from(["SKU", "PROD", "ITEM", "ART"]))
    number = draw(st.integers(min_value=1, max_value=99999))
    return f"{prefix}-{number:05d}"


@st.composite
def valid_product_name(draw):
    """Generate valid product names."""
    adjectives = ["Premium", "Standard", "Deluxe", "Basic", "Professional"]
    nouns = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Desk", "Chair"]
    adj = draw(st.sampled_from(adjectives))
    noun = draw(st.sampled_from(nouns))
    return f"{adj} {noun}"


@st.composite
def valid_category(draw):
    """Generate valid category names."""
    return draw(st.sampled_from([
        "Electronics", "Furniture", "Office Supplies", 
        "Hardware", "Software", "Accessories"
    ]))


@st.composite
def valid_unit_of_measure(draw):
    """Generate valid unit of measure."""
    return draw(st.sampled_from(["pieces", "kg", "liters", "meters"]))


@st.composite
def product_data(draw):
    """Generate complete product data."""
    return {
        "sku": draw(valid_sku()),
        "name": draw(valid_product_name()),
        "category": draw(valid_category()),
        "unit_of_measure": draw(valid_unit_of_measure())
    }


class TestPropertyMultipleFilterConjunction:
    """Property-based tests for multiple filter conjunction (AND logic)."""
    
    @given(
        products=st.lists(
            product_data(),
            min_size=10,
            max_size=30,
            unique_by=lambda x: x["sku"]
        ),
        filter_category=valid_category(),
        filter_unit=valid_unit_of_measure()
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_12_multiple_filter_conjunction_products(
        self, db_session, products, filter_category, filter_unit
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        For any combination of multiple filters applied simultaneously, the results
        should match all filter criteria (AND logic), with each result satisfying
        every specified condition.
        
        This test verifies product filtering with multiple criteria.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products to avoid contamination
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create all products
        created_products = []
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_products.append(product)
            except ProductError:
                # Skip if product creation fails
                pass
        
        # Skip test if no products were created
        assume(len(created_products) > 0)
        
        # Calculate expected matches (products matching ALL filter criteria)
        expected_matches = [
            p for p in created_products
            if p.category == filter_category and p.unit_of_measure == filter_unit
        ]
        
        # Apply multiple filters simultaneously
        results = pm.filter_products(
            category=filter_category,
            unit_of_measure=filter_unit
        )
        
        # Property verification: All results must match ALL filter criteria
        for result in results:
            assert result.category == filter_category, \
                f"Result with category '{result.category}' doesn't match filter '{filter_category}'"
            assert result.unit_of_measure == filter_unit, \
                f"Result with unit '{result.unit_of_measure}' doesn't match filter '{filter_unit}'"
        
        # Property verification: No matching entities should be excluded
        result_ids = {r.id for r in results}
        for expected in expected_matches:
            assert expected.id in result_ids, \
                f"Product '{expected.name}' (category={expected.category}, unit={expected.unit_of_measure}) " \
                f"was excluded from multi-filter results"
        
        # Property verification: Count matches expected
        assert len(results) == len(expected_matches), \
            f"Multi-filter returned {len(results)} products but expected {len(expected_matches)}"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=10,
            max_size=25,
            unique_by=lambda x: x["sku"]
        ),
        filter_category=valid_category(),
        filter_name_substring=st.sampled_from(["Laptop", "Phone", "Desk", "Chair", "Monitor"])
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_12_three_filter_conjunction_products(
        self, db_session, products, filter_category, filter_name_substring
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        Test with three simultaneous filters: category, name substring, and unit of measure.
        All results must satisfy ALL three conditions.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create all products
        created_products = []
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_products.append(product)
            except ProductError:
                pass
        
        assume(len(created_products) > 0)
        
        # Apply three filters simultaneously
        results = pm.filter_products(
            category=filter_category,
            name=filter_name_substring,
            unit_of_measure="pieces"
        )
        
        # Calculate expected matches
        expected_matches = [
            p for p in created_products
            if (p.category == filter_category and
                filter_name_substring in p.name and
                p.unit_of_measure == "pieces")
        ]
        
        # Verify all results match ALL three criteria
        for result in results:
            assert result.category == filter_category, \
                f"Result category '{result.category}' doesn't match filter '{filter_category}'"
            assert filter_name_substring in result.name, \
                f"Result name '{result.name}' doesn't contain '{filter_name_substring}'"
            assert result.unit_of_measure == "pieces", \
                f"Result unit '{result.unit_of_measure}' doesn't match 'pieces'"
        
        # Verify no matching entities excluded
        result_ids = {r.id for r in results}
        for expected in expected_matches:
            assert expected.id in result_ids, \
                f"Product '{expected.name}' matching all three filters was excluded"
        
        # Verify count
        assert len(results) == len(expected_matches), \
            f"Three-filter query returned {len(results)} but expected {len(expected_matches)}"
    
    @given(
        num_products=st.integers(min_value=15, max_value=30),
        filter_category=valid_category(),
        filter_unit=valid_unit_of_measure(),
        filter_sku_prefix=st.sampled_from(["SKU", "PROD", "ITEM", "ART"])
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_12_four_filter_conjunction_products(
        self, db_session, num_products, filter_category, filter_unit, filter_sku_prefix
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        Test with four simultaneous filters: category, unit, SKU, and name.
        Verifies that AND logic works correctly with maximum filter combination.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create diverse products
        created_products = []
        for i in range(num_products):
            try:
                # Vary the SKU prefix
                if i % 4 == 0:
                    sku = f"SKU-{i:05d}"
                elif i % 4 == 1:
                    sku = f"PROD-{i:05d}"
                elif i % 4 == 2:
                    sku = f"ITEM-{i:05d}"
                else:
                    sku = f"ART-{i:05d}"
                
                # Vary category and unit
                categories = ["Electronics", "Furniture", "Office Supplies"]
                units = ["pieces", "kg", "liters"]
                
                product = pm.create_product(
                    sku=sku,
                    name=f"Test Product {i}",
                    category=categories[i % len(categories)],
                    unit_of_measure=units[i % len(units)]
                )
                created_products.append(product)
            except ProductError:
                pass
        
        assume(len(created_products) >= 10)
        
        # Apply four filters simultaneously
        results = pm.filter_products(
            category=filter_category,
            unit_of_measure=filter_unit,
            sku=f"{filter_sku_prefix}-00000",  # Specific SKU
            name="Test"  # Name substring
        )
        
        # Calculate expected matches
        expected_matches = [
            p for p in created_products
            if (p.category == filter_category and
                p.unit_of_measure == filter_unit and
                p.sku == f"{filter_sku_prefix}-00000" and
                "Test" in p.name)
        ]
        
        # Verify all results match ALL four criteria
        for result in results:
            assert result.category == filter_category
            assert result.unit_of_measure == filter_unit
            assert result.sku == f"{filter_sku_prefix}-00000"
            assert "Test" in result.name
        
        # Verify completeness
        result_ids = {r.id for r in results}
        for expected in expected_matches:
            assert expected.id in result_ids
        
        assert len(results) == len(expected_matches)
    
    @given(
        num_documents=st.integers(min_value=10, max_value=20),
        filter_doc_type=st.sampled_from(["receipt", "delivery_order"]),
        filter_status=st.sampled_from(["pending", "validated"])
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=3000
    )
    def test_property_12_multiple_filter_conjunction_documents(
        self, db_session, num_documents, filter_doc_type, filter_status
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        For any combination of multiple filters applied simultaneously on documents,
        the results should match all filter criteria (AND logic).
        
        This test verifies document filtering with document_type and status.
        """
        dm = DocumentManager(db_session)
        pm = ProductManager(db_session)
        
        # Clear existing data
        db_session.query(Receipt).delete()
        db_session.query(DeliveryOrder).delete()
        db_session.query(Product).delete()
        db_session.query(Location).delete()
        db_session.query(User).delete()
        db_session.commit()
        
        # Create test user
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test User"
        )
        db_session.add(user)
        
        # Create test location
        location = Location(
            id=uuid.uuid4(),
            name="Test Warehouse",
            type=LocationType.warehouse,
            is_archived=False
        )
        db_session.add(location)
        
        # Create test product
        product = pm.create_product(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        db_session.commit()
        
        # Create diverse documents
        created_receipts = []
        created_delivery_orders = []
        
        for i in range(num_documents):
            items = [{
                "product_id": str(product.id),
                "location_id": str(location.id),
                "expected_quantity": 100,
                "received_quantity": 95
            }]
            
            # Create receipts
            if i % 2 == 0:
                receipt = dm.create_receipt(
                    supplier_name=f"Supplier {i}",
                    created_by=str(user.id),
                    items=items
                )
                # Validate some receipts
                if i % 4 == 0:
                    receipt.status = ReceiptStatus.validated
                    db_session.commit()
                created_receipts.append(receipt)
            
            # Create delivery orders
            else:
                do_items = [{
                    "product_id": str(product.id),
                    "location_id": str(location.id),
                    "requested_quantity": 50,
                    "delivered_quantity": 50
                }]
                delivery_order = dm.create_delivery_order(
                    customer_name=f"Customer {i}",
                    created_by=str(user.id),
                    items=do_items
                )
                # Validate some delivery orders
                if i % 4 == 1:
                    delivery_order.status = DeliveryOrderStatus.validated
                    db_session.commit()
                created_delivery_orders.append(delivery_order)
        
        # Apply multiple filters simultaneously
        results = dm.list_documents(
            document_type=filter_doc_type,
            status=filter_status
        )
        
        # Calculate expected matches
        if filter_doc_type == "receipt":
            expected_matches = [
                r for r in created_receipts
                if r.status.value == filter_status
            ]
        else:  # delivery_order
            expected_matches = [
                d for d in created_delivery_orders
                if d.status.value == filter_status
            ]
        
        # Property verification: All results must match ALL filter criteria
        for result in results:
            assert result["document_type"] == filter_doc_type, \
                f"Result document_type '{result['document_type']}' doesn't match filter '{filter_doc_type}'"
            assert result["status"] == filter_status, \
                f"Result status '{result['status']}' doesn't match filter '{filter_status}'"
        
        # Property verification: No matching entities should be excluded
        result_ids = {r["id"] for r in results}
        for expected in expected_matches:
            assert str(expected.id) in result_ids, \
                f"Document {expected.id} (type={filter_doc_type}, status={filter_status}) was excluded"
        
        # Property verification: Count matches expected
        assert len(results) == len(expected_matches), \
            f"Multi-filter returned {len(results)} documents but expected {len(expected_matches)}"
    
    @given(
        num_documents=st.integers(min_value=12, max_value=20)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=3000
    )
    def test_property_12_three_filter_conjunction_documents(
        self, db_session, num_documents
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        Test with three simultaneous filters on documents: document_type, status, and location.
        All results must satisfy ALL three conditions.
        """
        dm = DocumentManager(db_session)
        pm = ProductManager(db_session)
        
        # Clear existing data
        db_session.query(Receipt).delete()
        db_session.query(DeliveryOrder).delete()
        db_session.query(Product).delete()
        db_session.query(Location).delete()
        db_session.query(User).delete()
        db_session.commit()
        
        # Create test user
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed",
            name="Test User"
        )
        db_session.add(user)
        
        # Create multiple test locations
        locations = []
        for i in range(3):
            location = Location(
                id=uuid.uuid4(),
                name=f"Warehouse {i}",
                type=LocationType.warehouse,
                is_archived=False
            )
            db_session.add(location)
            locations.append(location)
        
        # Create test product
        product = pm.create_product(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            unit_of_measure="pieces"
        )
        db_session.commit()
        
        # Create diverse documents at different locations
        created_receipts = []
        
        for i in range(num_documents):
            location = locations[i % len(locations)]
            items = [{
                "product_id": str(product.id),
                "location_id": str(location.id),
                "expected_quantity": 100,
                "received_quantity": 95
            }]
            
            receipt = dm.create_receipt(
                supplier_name=f"Supplier {i}",
                created_by=str(user.id),
                items=items
            )
            
            # Validate some receipts
            if i % 3 == 0:
                receipt.status = ReceiptStatus.validated
                db_session.commit()
            
            created_receipts.append((receipt, location))
        
        # Choose a specific location to filter by
        target_location = locations[0]
        
        # Apply three filters simultaneously
        results = dm.list_documents(
            document_type="receipt",
            status="pending",
            location_id=str(target_location.id)
        )
        
        # Calculate expected matches
        expected_matches = [
            r for r, loc in created_receipts
            if (r.status.value == "pending" and loc.id == target_location.id)
        ]
        
        # Verify all results match ALL three criteria
        for result in results:
            assert result["document_type"] == "receipt"
            assert result["status"] == "pending"
            # Verify location by checking the document's items
        
        # Verify completeness
        result_ids = {r["id"] for r in results}
        for expected in expected_matches:
            assert str(expected.id) in result_ids, \
                f"Receipt {expected.id} at location {target_location.id} with status pending was excluded"
        
        # Verify count
        assert len(results) == len(expected_matches), \
            f"Three-filter query returned {len(results)} but expected {len(expected_matches)}"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=10,
            max_size=20,
            unique_by=lambda x: x["sku"]
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_12_no_false_positives_multi_filter(
        self, db_session, products
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        Verify that multi-filter results NEVER include products that fail to match
        even one of the filter criteria (no false positives).
        """
        pm = ProductManager(db_session)
        
        # Clear existing products
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create all products
        created_products = []
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_products.append(product)
            except ProductError:
                pass
        
        assume(len(created_products) >= 5)
        
        # Choose specific filter values
        filter_category = "Electronics"
        filter_unit = "pieces"
        
        # Apply filters
        results = pm.filter_products(
            category=filter_category,
            unit_of_measure=filter_unit
        )
        
        # Verify NO false positives: every result must match BOTH criteria
        for result in results:
            # If category doesn't match, it's a false positive
            if result.category != filter_category:
                pytest.fail(
                    f"FALSE POSITIVE: Product '{result.name}' with category '{result.category}' "
                    f"was included despite filter requiring '{filter_category}'"
                )
            
            # If unit doesn't match, it's a false positive
            if result.unit_of_measure != filter_unit:
                pytest.fail(
                    f"FALSE POSITIVE: Product '{result.name}' with unit '{result.unit_of_measure}' "
                    f"was included despite filter requiring '{filter_unit}'"
                )
        
        # Additional check: products that match only ONE criterion should NOT be in results
        result_ids = {r.id for r in results}
        
        for product in created_products:
            # Product matches only category but not unit
            if product.category == filter_category and product.unit_of_measure != filter_unit:
                assert product.id not in result_ids, \
                    f"Product '{product.name}' matches category but not unit, should be excluded"
            
            # Product matches only unit but not category
            if product.category != filter_category and product.unit_of_measure == filter_unit:
                assert product.id not in result_ids, \
                    f"Product '{product.name}' matches unit but not category, should be excluded"
            
            # Product matches neither
            if product.category != filter_category and product.unit_of_measure != filter_unit:
                assert product.id not in result_ids, \
                    f"Product '{product.name}' matches neither criterion, should be excluded"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=10,
            max_size=20,
            unique_by=lambda x: x["sku"]
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_12_empty_result_when_no_matches(
        self, db_session, products
    ):
        """
        **Validates: Requirements 12.5**
        
        Feature: core-inventory, Property 12: Multiple Filter Conjunction
        
        When multiple filters are applied and no products match ALL criteria,
        the result should be an empty list (not None, not error).
        """
        pm = ProductManager(db_session)
        
        # Clear existing products
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create products
        for prod_data in products:
            try:
                pm.create_product(**prod_data)
            except ProductError:
                pass
        
        # Apply filters that are unlikely to match anything
        # (combination that probably doesn't exist)
        results = pm.filter_products(
            category="NonExistentCategory12345",
            unit_of_measure="pieces",
            name="ImpossibleProductName98765"
        )
        
        # Should return empty list, not None
        assert results is not None, "Multi-filter should return empty list, not None"
        assert isinstance(results, list), "Multi-filter should return a list"
        assert len(results) == 0, \
            f"Multi-filter with impossible criteria returned {len(results)} results instead of 0"
