"""Test authentication system"""
import os
import sys


def test_auth_manager():
    """Test AuthManager functionality"""
    print("=" * 60)
    print("Authentication Test Suite")
    print("=" * 60)

    from auth import AuthManager
    import shutil

    # Create test database
    test_folder = 'test_auth_data'
    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)
    os.makedirs(test_folder, exist_ok=True)

    try:
        auth = AuthManager(test_folder, 'test_users.db')
        passed = 0
        failed = 0

        # Test 1: Register user
        print("\n1. Testing user registration...")
        try:
            user = auth.register_user('test@example.com', 'testuser', 'password123')
            assert user['email'] == 'test@example.com'
            assert user['username'] == 'testuser'
            assert 'id' in user
            print("✅ User registration works")
            passed += 1
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            failed += 1

        # Test 2: Duplicate email
        print("\n2. Testing duplicate email prevention...")
        try:
            auth.register_user('test@example.com', 'another', 'password123')
            print("❌ Should have raised error for duplicate email")
            failed += 1
        except ValueError as e:
            if 'email already registered' in str(e).lower():
                print("✅ Duplicate email prevented")
                passed += 1
            else:
                print(f"❌ Wrong error: {e}")
                failed += 1

        # Test 3: Duplicate username
        print("\n3. Testing duplicate username prevention...")
        try:
            auth.register_user('another@example.com', 'testuser', 'password123')
            print("❌ Should have raised error for duplicate username")
            failed += 1
        except ValueError as e:
            if 'username already taken' in str(e).lower():
                print("✅ Duplicate username prevented")
                passed += 1
            else:
                print(f"❌ Wrong error: {e}")
                failed += 1

        # Test 4: Authenticate with correct credentials
        print("\n4. Testing authentication with correct password...")
        try:
            user = auth.authenticate_user('test@example.com', 'password123')
            assert user is not None
            assert user['email'] == 'test@example.com'
            print("✅ Authentication with correct password works")
            passed += 1
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            failed += 1

        # Test 5: Authenticate with username
        print("\n5. Testing authentication with username...")
        try:
            user = auth.authenticate_user('testuser', 'password123')
            assert user is not None
            assert user['username'] == 'testuser'
            print("✅ Authentication with username works")
            passed += 1
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            failed += 1

        # Test 6: Wrong password
        print("\n6. Testing authentication with wrong password...")
        try:
            user = auth.authenticate_user('test@example.com', 'wrongpassword')
            assert user is None
            print("✅ Wrong password rejected")
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

        # Test 7: Non-existent user
        print("\n7. Testing authentication with non-existent user...")
        try:
            user = auth.authenticate_user('nonexistent@example.com', 'password123')
            assert user is None
            print("✅ Non-existent user rejected")
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

        # Test 8: Get user by ID
        print("\n8. Testing get user by ID...")
        try:
            user = auth.authenticate_user('test@example.com', 'password123')
            user_id = user['id']
            retrieved = auth.get_user_by_id(user_id)
            assert retrieved['email'] == 'test@example.com'
            print("✅ Get user by ID works")
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

        # Test 9: Update password
        print("\n9. Testing password update...")
        try:
            user = auth.authenticate_user('test@example.com', 'password123')
            auth.update_password(user['id'], 'newpassword123')

            # Try old password
            result = auth.authenticate_user('test@example.com', 'password123')
            assert result is None

            # Try new password
            result = auth.authenticate_user('test@example.com', 'newpassword123')
            assert result is not None
            print("✅ Password update works")
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

        # Test 10: User count
        print("\n10. Testing user count...")
        try:
            count = auth.get_user_count()
            assert count == 1
            print(f"✅ User count correct: {count}")
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

        print("\n" + "=" * 60)
        print(f"Test Results: {passed} passed, {failed} failed")
        print("=" * 60)

        return failed == 0

    finally:
        # Cleanup
        if os.path.exists(test_folder):
            shutil.rmtree(test_folder)


def test_flask_jwt():
    """Test Flask JWT integration"""
    print("\n" + "=" * 60)
    print("Flask JWT Integration Test")
    print("=" * 60)

    try:
        import app as flask_app

        # Check JWT is configured
        assert hasattr(flask_app, 'jwt'), "JWT not configured"
        print("✅ JWT configured in Flask app")

        # Check auth endpoints exist
        rules = [rule.rule for rule in flask_app.app.url_map.iter_rules()]
        auth_endpoints = [
            '/api/auth/register',
            '/api/auth/login',
            '/api/auth/refresh',
            '/api/auth/me',
            '/api/auth/password'
        ]

        for endpoint in auth_endpoints:
            assert endpoint in rules, f"Missing endpoint: {endpoint}"
            print(f"✅ Endpoint exists: {endpoint}")

        print("\n✅ All Flask JWT integration tests passed")
        return True

    except Exception as e:
        print(f"\n❌ Flask JWT integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success1 = test_auth_manager()
    success2 = test_flask_jwt()

    if success1 and success2:
        print("\n" + "=" * 60)
        print("All Authentication Tests Passed! ✅")
        print("=" * 60)
        print("\nKey features:")
        print("  • Secure password hashing with pbkdf2_sha256")
        print("  • JWT access and refresh tokens")
        print("  • Email and username authentication")
        print("  • Optional authentication (backward compatible)")
        print("  • User-scoped expense filtering")
        print()
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("Some tests failed ❌")
        print("=" * 60)
        sys.exit(1)
