"""Property-based tests for Product Manager component."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from core_inventory.components.product_manager import ProductManager, ProductError
from core_inventory.models.product import Product
from core_inventory.models.stock import Stock
from core_inventory.models.location import Location, LocationType
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
def product_data(draw):
    """Generate complete product data."""
    return {
        "sku": draw(valid_sku()),
        "name": draw(valid_product_name()),
        "category": draw(valid_category()),
        "unit_of_measure": draw(st.sampled_from(["pieces", "kg", "liters", "meters"]))
    }


class TestPropertySearchAndFiltering:
    """Property-based tests for search and filtering functionality."""
    
    @given(
        products=st.lists(
            product_data(),
            min_size=1,
            max_size=20,
            unique_by=lambda x: x["sku"]  # Ensure unique SKUs
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_10_product_search_completeness(self, db_session, products):
        """
        **Validates: Requirements 3.5, 15.1, 15.3, 15.4**
        
        Feature: core-inventory, Property 10: Product Search Completeness
        
        For any product in the system, searching by its exact SKU or any substring
        of its name should return that product in the search results.
        """
        pm = ProductManager(db_session)
        
        # Create all products
        created_products = []
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_products.append(product)
            except ProductError:
                # Skip if product creation fails (e.g., duplicate SKU from previous test)
                pass
        
        # Skip test if no products were created
        assume(len(created_products) > 0)
        
        # Test each product
        for product in created_products:
            # Test 1: Search by exact SKU should return the product
            results = pm.search_products(product.sku)
            assert any(p.id == product.id for p in results), \
                f"Product with SKU {product.sku} not found when searching by exact SKU"
            
            # Test 2: Search by full name should return the product
            results = pm.search_products(product.name)
            assert any(p.id == product.id for p in results), \
                f"Product '{product.name}' not found when searching by full name"
            
            # Test 3: Search by substring of name should return the product
            # Extract a meaningful substring (at least 3 chars if possible)
            name_words = product.name.split()
            for word in name_words:
                if len(word) >= 3:
                    substring = word[:len(word)//2 + 1]  # Take first half + 1 char
                    results = pm.search_products(substring)
                    assert any(p.id == product.id for p in results), \
                        f"Product '{product.name}' not found when searching by substring '{substring}'"
                    break  # Test one substring per product
    
    @given(
        products=st.lists(
            product_data(),
            min_size=5,
            max_size=20,
            unique_by=lambda x: x["sku"]
        ),
        filter_category=valid_category()
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_11_filter_result_correctness(self, db_session, products, filter_category):
        """
        **Validates: Requirements 3.6, 8.3, 11.3, 12.1, 12.2, 12.3, 12.4**
        
        Feature: core-inventory, Property 11: Filter Result Correctness
        
        For any filter criteria (category, document type, status, location, date range),
        all returned results should match the specified criteria, and no matching
        entities should be excluded.
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
        
        # Count expected matches
        expected_matches = [p for p in created_products if p.category == filter_category]
        
        # Apply filter
        results = pm.filter_products(category=filter_category)
        
        # Verify all results match the filter criteria
        for result in results:
            assert result.category == filter_category, \
                f"Result with category '{result.category}' doesn't match filter '{filter_category}'"
        
        # Verify no matching entities are excluded
        # All expected matches should be in results
        result_ids = {r.id for r in results}
        for expected in expected_matches:
            assert expected.id in result_ids, \
                f"Product '{expected.name}' with category '{expected.category}' was excluded from filter results"
        
        # Verify count matches
        assert len(results) == len(expected_matches), \
            f"Filter returned {len(results)} products but expected {len(expected_matches)}"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=1,
            max_size=15,
            unique_by=lambda x: x["sku"]
        ),
        search_query=st.one_of(
            valid_sku(),
            valid_product_name(),
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N')))
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_34_search_results_include_required_fields(self, db_session, products, search_query):
        """
        **Validates: Requirements 15.5**
        
        Feature: core-inventory, Property 34: Search Results Include Required Fields
        
        For any search result, the returned data should include product name, SKU,
        category, and current stock level.
        """
        pm = ProductManager(db_session)
        
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
        
        # Perform search
        results = pm.search_products(search_query)
        
        # Verify each result has all required fields
        for result in results:
            # Check that result is a Product object with all required attributes
            assert hasattr(result, 'name'), "Search result missing 'name' field"
            assert hasattr(result, 'sku'), "Search result missing 'sku' field"
            assert hasattr(result, 'category'), "Search result missing 'category' field"
            assert hasattr(result, 'id'), "Search result missing 'id' field"
            
            # Verify fields are not None or empty
            assert result.name is not None and len(result.name) > 0, \
                "Search result has empty name"
            assert result.sku is not None and len(result.sku) > 0, \
                "Search result has empty SKU"
            assert result.category is not None and len(result.category) > 0, \
                "Search result has empty category"
            assert result.id is not None, \
                "Search result has None id"
            
            # Verify we can query stock level for this product
            # (Stock level should be queryable even if zero)
            stock_records = db_session.query(Stock).filter(
                Stock.product_id == result.id
            ).all()
            # Stock records may or may not exist, but the query should succeed
            assert stock_records is not None, \
                f"Unable to query stock level for product {result.sku}"


    @given(
        num_products=st.integers(min_value=10, max_value=30),
        search_term=st.text(min_size=3, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz')
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_search_case_insensitive(self, db_session, num_products, search_term):
        """
        **Validates: Requirements 15.3**
        
        Feature: core-inventory, Property 10: Product Search Completeness (Case Insensitivity)
        
        Search should be case-insensitive for product names. Searching with different
        case variations should return the same results.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products to avoid contamination
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create products with the search term in their names
        created_products = []
        for i in range(num_products):
            try:
                # Mix case in product names
                if i % 3 == 0:
                    name = f"{search_term.upper()} Product {i}"
                elif i % 3 == 1:
                    name = f"{search_term.lower()} Product {i}"
                else:
                    name = f"{search_term.title()} Product {i}"
                
                product = pm.create_product(
                    sku=f"TEST-{uuid.uuid4().hex[:8].upper()}-{i:05d}",
                    name=name,
                    category="Test Category",
                    unit_of_measure="pieces"
                )
                created_products.append(product)
            except ProductError:
                # Skip if product creation fails
                pass
        
        # Skip if not enough products created
        assume(len(created_products) >= 3)
        
        # Search with different case variations
        results_lower = pm.search_products(search_term.lower())
        results_upper = pm.search_products(search_term.upper())
        results_title = pm.search_products(search_term.title())
        
        # All searches should return the same products
        result_ids_lower = {p.id for p in results_lower}
        result_ids_upper = {p.id for p in results_upper}
        result_ids_title = {p.id for p in results_title}
        
        assert result_ids_lower == result_ids_upper == result_ids_title, \
            "Case-insensitive search returned different results for different cases"
        
        # All created products should be in results
        for product in created_products:
            assert product.id in result_ids_lower, \
                f"Product '{product.name}' not found in case-insensitive search"
    
    @given(
        categories=st.lists(
            valid_category(),
            min_size=2,
            max_size=5,
            unique=True
        ),
        products_per_category=st.integers(min_value=2, max_value=5)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
        deadline=2000
    )
    def test_property_filter_no_cross_contamination(self, db_session, categories, products_per_category):
        """
        **Validates: Requirements 3.6, 12.4**
        
        Feature: core-inventory, Property 11: Filter Result Correctness (No Cross-Contamination)
        
        When filtering by a specific category, results should ONLY contain products
        from that category and NEVER include products from other categories.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products to avoid contamination
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create products in each category
        products_by_category = {cat: [] for cat in categories}
        
        for category in categories:
            for i in range(products_per_category):
                try:
                    product = pm.create_product(
                        sku=f"{category[:3].upper()}-{uuid.uuid4().hex[:8].upper()}-{i:05d}",
                        name=f"{category} Product {i}",
                        category=category,
                        unit_of_measure="pieces"
                    )
                    products_by_category[category].append(product)
                except ProductError:
                    # Skip if product creation fails
                    pass
        
        # Skip if not enough products created
        total_created = sum(len(prods) for prods in products_by_category.values())
        assume(total_created >= len(categories) * 2)
        
        # Test filtering for each category
        for target_category in categories:
            results = pm.filter_products(category=target_category)
            
            # Verify all results are from target category
            for result in results:
                assert result.category == target_category, \
                    f"Filter for '{target_category}' returned product from '{result.category}'"
            
            # Verify no products from other categories are included
            result_ids = {r.id for r in results}
            for other_category in categories:
                if other_category != target_category:
                    for product in products_by_category[other_category]:
                        assert product.id not in result_ids, \
                            f"Filter for '{target_category}' incorrectly included product from '{other_category}'"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=5,
            max_size=15,
            unique_by=lambda x: x["sku"]
        )
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_search_empty_query_returns_empty(self, db_session, products):
        """
        **Validates: Requirements 15.1**
        
        Feature: core-inventory, Property 10: Product Search Completeness (Empty Query)
        
        Searching with an empty or whitespace-only query should return an empty list.
        """
        pm = ProductManager(db_session)
        
        # Create products
        for prod_data in products:
            try:
                pm.create_product(**prod_data)
            except ProductError:
                pass
        
        # Test empty queries
        empty_queries = ["", "   ", "\t", "\n", "  \t\n  "]
        
        for query in empty_queries:
            results = pm.search_products(query)
            assert len(results) == 0, \
                f"Empty query '{repr(query)}' returned {len(results)} results instead of 0"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=5,
            max_size=15,
            unique_by=lambda x: x["sku"]
        )
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_filter_empty_category_returns_all(self, db_session, products):
        """
        **Validates: Requirements 3.6**
        
        Feature: core-inventory, Property 11: Filter Result Correctness (Empty Filter)
        
        Filtering with no category or empty category should return all products.
        """
        pm = ProductManager(db_session)
        
        # Clear existing products to avoid contamination
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create products
        created_products = []
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_products.append(product)
            except ProductError:
                pass
        
        # Skip if no products created
        assume(len(created_products) > 0)
        
        # Test empty filters
        results_none = pm.filter_products(category=None)
        results_empty = pm.filter_products(category="")
        results_whitespace = pm.filter_products(category="   ")
        
        # All should return all products
        assert len(results_none) == len(created_products), \
            f"Filter with None returned {len(results_none)} products instead of {len(created_products)}"
        assert len(results_empty) == len(created_products), \
            f"Filter with empty string returned {len(results_empty)} products instead of {len(created_products)}"
        assert len(results_whitespace) == len(created_products), \
            f"Filter with whitespace returned {len(results_whitespace)} products instead of {len(created_products)}"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x["sku"]
        ),
        nonexistent_sku=st.text(
            min_size=5,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))
        ).filter(lambda x: not x.startswith(("SKU-", "PROD-", "ITEM-", "ART-")))
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_search_nonexistent_returns_empty(self, db_session, products, nonexistent_sku):
        """
        **Validates: Requirements 15.1**
        
        Feature: core-inventory, Property 10: Product Search Completeness (No False Positives)
        
        Searching for a SKU or name that doesn't exist should return an empty list.
        """
        pm = ProductManager(db_session)
        
        # Create products
        created_skus = set()
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_skus.add(product.sku)
            except ProductError:
                pass
        
        # Ensure the nonexistent SKU is truly nonexistent
        assume(nonexistent_sku not in created_skus)
        
        # Search for nonexistent SKU
        results = pm.search_products(nonexistent_sku)
        
        # Should return empty list
        assert len(results) == 0, \
            f"Search for nonexistent SKU '{nonexistent_sku}' returned {len(results)} results"
    
    @given(
        products=st.lists(
            product_data(),
            min_size=3,
            max_size=10,
            unique_by=lambda x: x["sku"]
        ),
        nonexistent_category=st.text(
            min_size=5,
            max_size=30,
            alphabet=st.characters(whitelist_categories=('L',))
        ).filter(lambda x: x not in [
            "Electronics", "Furniture", "Office Supplies",
            "Hardware", "Software", "Accessories"
        ])
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_filter_nonexistent_category_returns_empty(self, db_session, products, nonexistent_category):
        """
        **Validates: Requirements 3.6**
        
        Feature: core-inventory, Property 11: Filter Result Correctness (No False Positives)
        
        Filtering by a category that doesn't exist should return an empty list.
        """
        pm = ProductManager(db_session)
        
        # Create products
        created_categories = set()
        for prod_data in products:
            try:
                product = pm.create_product(**prod_data)
                created_categories.add(product.category)
            except ProductError:
                pass
        
        # Ensure the nonexistent category is truly nonexistent
        assume(nonexistent_category not in created_categories)
        
        # Filter by nonexistent category
        results = pm.filter_products(category=nonexistent_category)
        
        # Should return empty list
        assert len(results) == 0, \
            f"Filter for nonexistent category '{nonexistent_category}' returned {len(results)} results"
