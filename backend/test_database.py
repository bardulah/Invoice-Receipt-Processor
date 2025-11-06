"""Comprehensive database tests"""
import os
import sys
import shutil
from datetime import datetime, date
from db import DatabaseAdapter


class TestDatabase:
    """Test suite for DatabaseAdapter"""

    def __init__(self):
        self.test_folder = 'test_db_data'
        self.db = None
        self.passed = 0
        self.failed = 0

    def setup(self):
        """Set up test environment"""
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        os.makedirs(self.test_folder, exist_ok=True)
        self.db = DatabaseAdapter(self.test_folder, 'test.db')

    def teardown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    def assert_equal(self, actual, expected, message):
        """Assert that actual equals expected"""
        if actual == expected:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            print(f"  ❌ {message}")
            print(f"     Expected: {expected}")
            print(f"     Actual: {actual}")

    def assert_true(self, condition, message):
        """Assert that condition is True"""
        if condition:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            print(f"  ❌ {message}")

    def test_add_expense(self):
        """Test adding expenses"""
        print("\nTest: Add Expense")
        print("-" * 60)

        expense_data = {
            'date': '2024-01-15',
            'vendor': 'Test Vendor',
            'amount': 100.50,
            'category': 'Office Supplies',
            'description': 'Test expense',
            'currency': 'USD'
        }

        expense_id = self.db.add_expense(expense_data)
        self.assert_true(expense_id.startswith('EXP'), "Expense ID starts with EXP")

        expenses = self.db.get_expenses()
        self.assert_equal(len(expenses), 1, "One expense added")
        self.assert_equal(expenses[0]['vendor'], 'Test Vendor', "Vendor matches")
        self.assert_equal(expenses[0]['amount'], 100.50, "Amount matches")

    def test_get_expenses_with_filters(self):
        """Test filtering expenses"""
        print("\nTest: Get Expenses with Filters")
        print("-" * 60)

        # Add multiple expenses
        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Vendor A',
            'amount': 100.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-02-15',
            'vendor': 'Vendor B',
            'amount': 200.00,
            'category': 'Software & Services',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-03-15',
            'vendor': 'Vendor A',
            'amount': 150.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        # Test category filter
        office_supplies = self.db.get_expenses(category='Office Supplies')
        self.assert_equal(len(office_supplies), 2, "Filter by category works")

        # Test vendor filter
        vendor_a = self.db.get_expenses(vendor='Vendor A')
        self.assert_equal(len(vendor_a), 2, "Filter by vendor works")

        # Test date range filter
        jan_expenses = self.db.get_expenses(start_date='2024-01-01', end_date='2024-01-31')
        self.assert_equal(len(jan_expenses), 1, "Filter by date range works")

        # Test search
        search_results = self.db.get_expenses(search='Software')
        self.assert_equal(len(search_results), 1, "Search works")

    def test_statistics(self):
        """Test statistics generation"""
        print("\nTest: Statistics")
        print("-" * 60)

        # Add expenses
        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Vendor A',
            'amount': 100.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-01-20',
            'vendor': 'Vendor B',
            'amount': 200.00,
            'category': 'Software & Services',
            'currency': 'USD'
        })

        stats = self.db.get_statistics()

        self.assert_equal(stats['total_expenses'], 2, "Total expenses count correct")
        self.assert_equal(stats['total_amount'], 300.00, "Total amount correct")
        self.assert_equal(len(stats['by_category']), 2, "Category breakdown correct")
        self.assert_equal(len(stats['by_vendor']), 2, "Vendor breakdown correct")

    def test_vendor_history(self):
        """Test vendor history building"""
        print("\nTest: Vendor History")
        print("-" * 60)

        # Add expenses with same vendor in different categories
        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Adobe',
            'amount': 50.00,
            'category': 'Software & Services',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-02-15',
            'vendor': 'Adobe',
            'amount': 50.00,
            'category': 'Software & Services',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-03-15',
            'vendor': 'Adobe',
            'amount': 100.00,
            'category': 'Marketing',
            'currency': 'USD'
        })

        history = self.db.build_vendor_history()

        self.assert_true('adobe' in history, "Vendor history contains Adobe")
        self.assert_equal(history['adobe']['Software & Services'], 2, "Correct count for Software & Services")
        self.assert_equal(history['adobe']['Marketing'], 1, "Correct count for Marketing")

    def test_get_all_vendors(self):
        """Test getting all vendors"""
        print("\nTest: Get All Vendors")
        print("-" * 60)

        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Vendor A',
            'amount': 100.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Vendor B',
            'amount': 200.00,
            'category': 'Software & Services',
            'currency': 'USD'
        })

        vendors = self.db.get_all_vendors()
        self.assert_equal(len(vendors), 2, "Two unique vendors")
        self.assert_true('Vendor A' in vendors, "Vendor A in list")
        self.assert_true('Vendor B' in vendors, "Vendor B in list")

    def test_get_all_categories(self):
        """Test getting all categories"""
        print("\nTest: Get All Categories")
        print("-" * 60)

        categories = self.db.get_all_categories()
        self.assert_true(len(categories) > 0, "Categories list not empty")
        self.assert_true('Office Supplies' in categories, "Office Supplies in categories")
        self.assert_true('Software & Services' in categories, "Software & Services in categories")

    def test_update_expense(self):
        """Test updating an expense"""
        print("\nTest: Update Expense")
        print("-" * 60)

        expense_id = self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Old Vendor',
            'amount': 100.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        # Update the expense
        success = self.db.update_expense(expense_id, {
            'vendor': 'New Vendor',
            'amount': 150.00
        })

        self.assert_true(success, "Update succeeded")

        # Verify the update
        expense = self.db.get_expense_by_id(expense_id)
        self.assert_equal(expense['vendor'], 'New Vendor', "Vendor updated")
        self.assert_equal(expense['amount'], 150.00, "Amount updated")

    def test_delete_expense(self):
        """Test deleting an expense"""
        print("\nTest: Delete Expense")
        print("-" * 60)

        expense_id = self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'Test Vendor',
            'amount': 100.00,
            'category': 'Office Supplies',
            'currency': 'USD'
        })

        # Delete the expense
        success = self.db.delete_expense(expense_id)
        self.assert_true(success, "Delete succeeded")

        # Verify deletion
        expense = self.db.get_expense_by_id(expense_id)
        self.assert_true(expense is None, "Expense deleted")

    def test_multi_currency(self):
        """Test multi-currency support"""
        print("\nTest: Multi-Currency Support")
        print("-" * 60)

        self.db.add_expense({
            'date': '2024-01-15',
            'vendor': 'International Vendor',
            'amount': 100.00,
            'currency': 'USD',
            'original_amount': 85.00,
            'original_currency': 'EUR',
            'converted_to_usd': True
        })

        expenses = self.db.get_expenses()
        self.assert_equal(expenses[0]['currency'], 'USD', "Currency stored")
        self.assert_equal(expenses[0]['original_currency'], 'EUR', "Original currency stored")
        self.assert_true(expenses[0]['converted_to_usd'], "Conversion flag stored")

    def test_concurrent_access(self):
        """Test that database supports concurrent access"""
        print("\nTest: Concurrent Access")
        print("-" * 60)

        # Add multiple expenses in quick succession
        for i in range(10):
            self.db.add_expense({
                'date': '2024-01-15',
                'vendor': f'Vendor {i}',
                'amount': 100.00 * i,
                'category': 'Office Supplies',
                'currency': 'USD'
            })

        expenses = self.db.get_expenses()
        self.assert_equal(len(expenses), 10, "All concurrent writes succeeded")

    def test_empty_database(self):
        """Test operations on empty database"""
        print("\nTest: Empty Database")
        print("-" * 60)

        # Fresh database
        empty_db = DatabaseAdapter(self.test_folder, 'empty_test.db')

        stats = empty_db.get_statistics()
        self.assert_equal(stats['total_expenses'], 0, "Empty database has 0 expenses")
        self.assert_equal(stats['total_amount'], 0, "Empty database has 0 amount")

        vendors = empty_db.get_all_vendors()
        self.assert_equal(len(vendors), 0, "Empty database has no vendors")

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("Database Test Suite")
        print("=" * 60)

        self.setup()

        try:
            self.test_add_expense()
            self.teardown()
            self.setup()

            self.test_get_expenses_with_filters()
            self.teardown()
            self.setup()

            self.test_statistics()
            self.teardown()
            self.setup()

            self.test_vendor_history()
            self.teardown()
            self.setup()

            self.test_get_all_vendors()
            self.teardown()
            self.setup()

            self.test_get_all_categories()
            self.teardown()
            self.setup()

            self.test_update_expense()
            self.teardown()
            self.setup()

            self.test_delete_expense()
            self.teardown()
            self.setup()

            self.test_multi_currency()
            self.teardown()
            self.setup()

            self.test_concurrent_access()
            self.teardown()
            self.setup()

            self.test_empty_database()
            self.teardown()

        finally:
            self.teardown()

        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        if self.failed > 0:
            print(f"❌ Failed: {self.failed}")
        print()

        return self.failed == 0


if __name__ == '__main__':
    tester = TestDatabase()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
