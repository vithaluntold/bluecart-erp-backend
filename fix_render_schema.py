"""
Fix Render Database Schema to Match Simple Data Structure
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Render PostgreSQL Connection
RENDER_DB_URL = "postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp"

def check_current_schema(cursor):
    """Check current table structure"""
    print("\n" + "="*60)
    print("  CHECKING CURRENT SCHEMA")
    print("="*60)
    
    # Check users table columns
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    user_columns = cursor.fetchall()
    print("\n📋 Users table columns:")
    for col in user_columns:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    # Check hubs table
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'hubs'
        ORDER BY ordinal_position
    """)
    hub_columns = cursor.fetchall()
    print("\n📋 Hubs table columns:")
    for col in hub_columns:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    # Check shipments table
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'shipments'
        ORDER BY ordinal_position
    """)
    shipment_columns = cursor.fetchall()
    print("\n📋 Shipments table columns:")
    for col in shipment_columns:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    return user_columns, hub_columns, shipment_columns

def fix_users_table(cursor):
    """Add missing columns to users table"""
    print("\n" + "="*60)
    print("  FIXING USERS TABLE")
    print("="*60)
    
    # Add name column if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255)")
        print("✅ Added 'name' column")
    except Exception as e:
        print(f"⚠️  Name column: {e}")
    
    # Add role column if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50)")
        print("✅ Added 'role' column")
    except Exception as e:
        print(f"⚠️  Role column: {e}")
    
    # Add created_at if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'created_at' column")
    except Exception as e:
        print(f"⚠️  Created_at column: {e}")
    
    # Add updated_at if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'updated_at' column")
    except Exception as e:
        print(f"⚠️  Updated_at column: {e}")

def fix_hubs_table(cursor):
    """Add missing columns to hubs table"""
    print("\n" + "="*60)
    print("  FIXING HUBS TABLE")
    print("="*60)
    
    # Add manager_id if missing
    try:
        cursor.execute("ALTER TABLE hubs ADD COLUMN IF NOT EXISTS manager_id VARCHAR(50)")
        print("✅ Added 'manager_id' column")
    except Exception as e:
        print(f"⚠️  Manager_id column: {e}")
    
    # Add created_at if missing
    try:
        cursor.execute("ALTER TABLE hubs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'created_at' column")
    except Exception as e:
        print(f"⚠️  Created_at column: {e}")
    
    # Add updated_at if missing
    try:
        cursor.execute("ALTER TABLE hubs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'updated_at' column")
    except Exception as e:
        print(f"⚠️  Updated_at column: {e}")

def fix_shipments_table(cursor):
    """Add missing columns to shipments table"""
    print("\n" + "="*60)
    print("  FIXING SHIPMENTS TABLE")
    print("="*60)
    
    # Add driver_id if missing
    try:
        cursor.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS driver_id VARCHAR(50)")
        print("✅ Added 'driver_id' column")
    except Exception as e:
        print(f"⚠️  Driver_id column: {e}")
    
    # Add weight if missing
    try:
        cursor.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS weight DECIMAL(10, 2)")
        print("✅ Added 'weight' column")
    except Exception as e:
        print(f"⚠️  Weight column: {e}")
    
    # Add dimensions if missing
    try:
        cursor.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS dimensions VARCHAR(100)")
        print("✅ Added 'dimensions' column")
    except Exception as e:
        print(f"⚠️  Dimensions column: {e}")
    
    # Add created_at if missing
    try:
        cursor.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'created_at' column")
    except Exception as e:
        print(f"⚠️  Created_at column: {e}")
    
    # Add updated_at if missing
    try:
        cursor.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()")
        print("✅ Added 'updated_at' column")
    except Exception as e:
        print(f"⚠️  Updated_at column: {e}")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("  RENDER DATABASE SCHEMA FIX")
    print("="*60)
    
    try:
        # Connect to database
        print("\n🔌 Connecting to Render PostgreSQL...")
        conn = psycopg2.connect(RENDER_DB_URL)
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Connected to database")
        
        # Check current schema
        check_current_schema(cursor)
        
        # Fix tables
        fix_users_table(cursor)
        fix_hubs_table(cursor)
        fix_shipments_table(cursor)
        
        # Commit changes
        conn.commit()
        print("\n✅ All schema changes committed")
        
        # Check updated schema
        print("\n" + "="*60)
        print("  UPDATED SCHEMA")
        print("="*60)
        check_current_schema(cursor)
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("  ✅ SCHEMA FIX COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
