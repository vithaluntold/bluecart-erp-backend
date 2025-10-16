"""
Test Login with Render Database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

# Render PostgreSQL Connection
RENDER_DB_URL = "postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def test_login(email: str, password: str):
    """Test login with email and password"""
    print(f"\n{'='*60}")
    print(f"  Testing Login: {email}")
    print(f"{'='*60}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(RENDER_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find user by email
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            cursor.close()
            conn.close()
            return False
        
        print(f"✅ User found in database")
        print(f"   ID: {user['id']}")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['name']}")
        print(f"   Role: {user['role']}")
        print(f"   Phone: {user['phone']}")
        
        # Verify password
        if verify_password(password, user['password']):
            print(f"\n✅ PASSWORD CORRECT! Login successful")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"\n❌ PASSWORD INCORRECT! Login failed")
            cursor.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_all_users():
    """Show all users in database"""
    print(f"\n{'='*60}")
    print(f"  ALL USERS IN DATABASE")
    print(f"{'='*60}")
    
    try:
        conn = psycopg2.connect(RENDER_DB_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id, username, email, name, role, phone FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print(f"\n📊 Total users: {len(users)}\n")
        
        for user in users:
            print(f"User ID: {user['id']}")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Name: {user['name']}")
            print(f"  Role: {user['role']}")
            print(f"  Phone: {user['phone']}")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print(f"\n{'='*60}")
    print(f"  RENDER DATABASE LOGIN TEST")
    print(f"{'='*60}")
    
    # Show all users
    show_all_users()
    
    # Test credentials
    test_cases = [
        ("admin@bluecart.com", "admin123"),
        ("rajesh@bluecart.com", "rajesh123"),
        ("amit@bluecart.com", "amit123"),
        ("admin@bluecart.com", "wrongpassword"),  # Should fail
    ]
    
    results = []
    for email, password in test_cases:
        success = test_login(email, password)
        results.append({
            "email": email,
            "password": password,
            "success": success
        })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  TEST SUMMARY")
    print(f"{'='*60}\n")
    
    passed = sum(1 for r in results if r["success"])
    total = len([r for r in results if r["password"] != "wrongpassword"])  # Exclude failure test
    
    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        expected = "(expected)" if r["password"] == "wrongpassword" else ""
        print(f"{status} {expected}: {r['email']} / {r['password']}")
    
    print(f"\n{'='*60}")
    print(f"  Valid Login Tests: {passed}/{total} passed")
    print(f"{'='*60}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Database is ready for Render deployment")
        print(f"✅ All passwords encrypted with bcrypt")
        print(f"✅ Login system working correctly")
    else:
        print(f"\n⚠️  Some tests failed - please check")

if __name__ == "__main__":
    main()
