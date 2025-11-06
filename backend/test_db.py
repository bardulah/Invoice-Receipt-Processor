"""Test database functionality"""
import os
import sys
from datetime import datetime
from db import DatabaseAdapter

def test_database():
    """Test basic database operations"""
    print("=" * 60)
    print("Database Test")
    print("=" * 60)

    # Create test database in temp location
    test_folder = 'test_data'
    os.makedirs(test_folder, exist_ok=True)

    db = DatabaseAdapter(test_folder, 'test_expenses.db')
    print("✅ Database initialized")

    # Test 1: Add expense
    print("\nTest 1: Adding expense...")
    expense_data = {
        'date': '2024-01-15',
        'vendor': 'Test Vendor',
        'amount': 123.45,
        'category': 'Office Supplies',
        'description': 'Test expense',
        'currency': 'USD'
    }

    expense_id = db.add_expense(expense_data)
    print(f"✅ Added expense: {expense_id}")

    # Test 2: Get expenses
    print("\nTest 2: Retrieving expenses...")
    expenses = db.get_expenses()
    print(f"✅ Found {len(expenses)} expenses")
    if expenses:
        print(f"   First expense: {expenses[0]['vendor']} - ${expenses[0]['amount']}")

    # Test 3: Get statistics
    print("\nTest 3: Getting statistics...")
    stats = db.get_statistics()
    print(f"✅ Statistics:")
    print(f"   Total expenses: {stats['total_expenses']}")
    print(f"   Total amount: ${stats['total_amount']:.2f}")
    print(f"   Categories: {len(stats['by_category'])}")

    # Test 4: Filter expenses
    print("\nTest 4: Filtering expenses...")
    filtered = db.get_expenses(category='Office Supplies')
    print(f"✅ Found {len(filtered)} expenses in 'Office Supplies'")

    # Test 5: Vendor history
    print("\nTest 5: Building vendor history...")
    history = db.build_vendor_history()
    print(f"✅ Vendor history contains {len(history)} vendors")

    # Test 6: Get vendors
    print("\nTest 6: Getting all vendors...")
    vendors = db.get_all_vendors()
    print(f"✅ Found {len(vendors)} unique vendors")

    # Cleanup
    db_path = os.path.join(test_folder, 'test_expenses.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(test_folder)

    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)

    return True


if __name__ == '__main__':
    try:
        success = test_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
