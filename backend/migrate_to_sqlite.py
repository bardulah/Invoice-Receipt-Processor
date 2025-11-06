"""Migration script to move data from JSON to SQLite"""
import json
import os
import shutil
from datetime import datetime
from db import DatabaseAdapter


def migrate_json_to_sqlite(data_folder='data'):
    """Migrate expenses from JSON to SQLite database"""
    print("=" * 60)
    print("Migration: JSON to SQLite")
    print("=" * 60)

    expenses_file = os.path.join(data_folder, 'expenses.json')

    # Check if JSON file exists
    if not os.path.exists(expenses_file):
        print(f"No expenses.json found at {expenses_file}")
        print("Nothing to migrate. Starting with fresh database.")
        return True

    # Load JSON data
    print(f"Loading data from {expenses_file}...")
    try:
        with open(expenses_file, 'r') as f:
            expenses = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        return False

    if not expenses:
        print("No expenses found in JSON file.")
        return True

    print(f"Found {len(expenses)} expenses to migrate")

    # Create database adapter
    db = DatabaseAdapter(data_folder)

    # Check if database already has data
    existing_stats = db.get_statistics()
    if existing_stats['total_expenses'] > 0:
        print(f"Warning: Database already contains {existing_stats['total_expenses']} expenses")
        response = input("Continue and add JSON data to existing database? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return False

    # Migrate each expense
    print("\nMigrating expenses...")
    success_count = 0
    error_count = 0

    for i, expense in enumerate(expenses, 1):
        try:
            # Add expense to database
            expense_id = db.add_expense(expense)
            success_count += 1

            if i % 10 == 0:
                print(f"Migrated {i}/{len(expenses)} expenses...")

        except Exception as e:
            print(f"Error migrating expense {expense.get('id', 'unknown')}: {e}")
            error_count += 1

    print("\nMigration Summary:")
    print(f"✅ Successfully migrated: {success_count} expenses")
    if error_count > 0:
        print(f"❌ Errors: {error_count} expenses")

    # Create backup of JSON file
    backup_file = os.path.join(data_folder, f'expenses_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f"\nCreating backup: {backup_file}")
    shutil.copy2(expenses_file, backup_file)

    # Verify migration
    print("\nVerifying migration...")
    stats = db.get_statistics()
    print(f"Database now contains: {stats['total_expenses']} expenses")
    print(f"Total amount: ${stats['total_amount']:,.2f}")

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update backend/app.py to use DatabaseAdapter")
    print("2. Test the application")
    print("3. If everything works, you can delete the backup JSON file")
    print()

    return True


if __name__ == '__main__':
    import sys

    # Allow specifying data folder as argument
    data_folder = sys.argv[1] if len(sys.argv) > 1 else 'data'

    success = migrate_json_to_sqlite(data_folder)
    sys.exit(0 if success else 1)
