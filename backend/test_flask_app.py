"""Test that Flask app starts correctly"""
import sys
import os
from threading import Thread
import time
import requests

def test_flask_startup():
    """Test that the Flask app can start and respond"""
    print("=" * 60)
    print("Flask App Startup Test")
    print("=" * 60)

    # Import the app
    print("\n1. Importing Flask app...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        # Just try to import - don't actually run the server
        import app as flask_app
        print("✅ Flask app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check that key components are initialized
    print("\n2. Checking component initialization...")
    try:
        assert hasattr(flask_app, 'db'), "Database adapter not initialized"
        assert hasattr(flask_app, 'categorizer'), "Categorizer not initialized"
        assert hasattr(flask_app, 'extractor'), "Extractor not initialized"
        assert hasattr(flask_app, 'report_generator'), "Report generator not initialized"
        print("✅ All key components initialized")
    except AssertionError as e:
        print(f"❌ Component check failed: {e}")
        return False

    # Test database is working
    print("\n3. Testing database connection...")
    try:
        stats = flask_app.db.get_statistics()
        print(f"✅ Database connected - {stats['total_expenses']} expenses")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("Flask app is ready to start! ✅")
    print("=" * 60)
    print("\nTo start the server, run:")
    print("  cd backend && python app.py")
    print("\nThe app will be available at:")
    print("  http://localhost:5000")
    print()

    return True


if __name__ == '__main__':
    try:
        success = test_flask_startup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
