"""
Insert test data directly into Render PostgreSQL database
"""
import psycopg2
import bcrypt
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

try:
    print("🔌 Connecting to Render PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check existing tables
    print("\n📋 Checking tables...")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    tables = cur.fetchall()
    print(f"Existing tables: {[t[0] for t in tables]}")
    
    # Check if users table has data
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"\n👥 Current users count: {user_count}")
    
    if user_count == 0:
        print("\n✨ Inserting test users...")
        
        users_data = [
            ('admin@bluecart.com', 'Admin User', 'admin', hash_password('admin123'), '+91-9876543210', 'admin'),
            ('rajesh.kumar@bluecart.com', 'Rajesh Kumar', 'rajesh', hash_password('rajesh123'), '+91-9876543211', 'manager'),
            ('amit.patel@bluecart.com', 'Amit Patel', 'amit', hash_password('amit123'), '+91-9876543212', 'driver'),
            ('priya.sharma@bluecart.com', 'Priya Sharma', 'priya', hash_password('priya123'), '+91-9876543213', 'manager'),
            ('vijay.singh@bluecart.com', 'Vijay Singh', 'vijay', hash_password('vijay123'), '+91-9876543214', 'driver'),
            ('anjali.reddy@bluecart.com', 'Anjali Reddy', 'anjali', hash_password('anjali123'), '+91-9876543215', 'user'),
        ]
        
        for email, full_name, username, password_hash, phone, role in users_data:
            cur.execute("""
                INSERT INTO users (email, full_name, username, password_hash, phone, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, full_name, username, password_hash, phone, role, datetime.now()))
            print(f"   ✅ Added user: {email}")
        
        conn.commit()
        print(f"\n✅ Inserted {len(users_data)} users successfully!")
    else:
        print(f"ℹ️  Users already exist, skipping user insertion")
    
    # Check hubs
    cur.execute("SELECT COUNT(*) FROM hubs")
    hub_count = cur.fetchone()[0]
    print(f"\n🏢 Current hubs count: {hub_count}")
    
    if hub_count == 0:
        print("\n✨ Inserting test hubs...")
        
        hubs_data = [
            ('HUB001', 'Mumbai Central Hub', 'Mumbai', 'Maharashtra', '400001', 19.0760, 72.8777, 'active', 5000, 3500),
            ('HUB002', 'Delhi Distribution Center', 'Delhi', 'Delhi', '110001', 28.7041, 77.1025, 'active', 7000, 4200),
            ('HUB003', 'Bangalore Tech Hub', 'Bangalore', 'Karnataka', '560001', 12.9716, 77.5946, 'active', 4500, 2800),
            ('HUB004', 'Chennai Coastal Hub', 'Chennai', 'Tamil Nadu', '600001', 13.0827, 80.2707, 'active', 3500, 2100),
            ('HUB005', 'Kolkata East Hub', 'Kolkata', 'West Bengal', '700001', 22.5726, 88.3639, 'active', 4000, 2500),
        ]
        
        for hub_id, name, city, state, zip_code, lat, lng, status, capacity, current_load in hubs_data:
            cur.execute("""
                INSERT INTO hubs (id, name, city, state, zip_code, latitude, longitude, status, capacity, current_load, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (hub_id, name, city, state, zip_code, lat, lng, status, capacity, current_load, datetime.now()))
            print(f"   ✅ Added hub: {name}")
        
        conn.commit()
        print(f"\n✅ Inserted {len(hubs_data)} hubs successfully!")
    else:
        print(f"ℹ️  Hubs already exist, skipping hub insertion")
    
    # Check routes
    cur.execute("SELECT COUNT(*) FROM routes")
    route_count = cur.fetchone()[0]
    print(f"\n🚛 Current routes count: {route_count}")
    
    if route_count == 0:
        print("\n✨ Inserting test routes...")
        
        routes_data = [
            ('RT001', 'Mumbai-Delhi Express', 'HUB001', 'HUB002', 1400, 18, 'active'),
            ('RT002', 'Delhi-Bangalore Route', 'HUB002', 'HUB003', 2150, 28, 'active'),
            ('RT003', 'Mumbai-Chennai Coastal', 'HUB001', 'HUB004', 1340, 20, 'active'),
        ]
        
        for route_id, name, source_hub, dest_hub, distance, duration, status in routes_data:
            cur.execute("""
                INSERT INTO routes (id, name, source_hub_id, destination_hub_id, distance_km, estimated_duration_hours, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (route_id, name, source_hub, dest_hub, distance, duration, status, datetime.now()))
            print(f"   ✅ Added route: {name}")
        
        conn.commit()
        print(f"\n✅ Inserted {len(routes_data)} routes successfully!")
    else:
        print(f"ℹ️  Routes already exist, skipping route insertion")
    
    # Check shipments
    cur.execute("SELECT COUNT(*) FROM shipments")
    shipment_count = cur.fetchone()[0]
    print(f"\n📦 Current shipments count: {shipment_count}")
    
    if shipment_count == 0:
        print("\n✨ Inserting test shipments...")
        
        shipments_data = [
            ('SH001', 'Electronics Package', 'HUB001', 'HUB002', 'in_transit', 'high', 15.5),
            ('SH002', 'Clothing Bulk Order', 'HUB002', 'HUB003', 'pending', 'medium', 45.2),
            ('SH003', 'Medical Supplies', 'HUB001', 'HUB004', 'delivered', 'urgent', 8.7),
        ]
        
        for tracking_id, description, origin, destination, status, priority, weight in shipments_data:
            cur.execute("""
                INSERT INTO shipments (tracking_id, description, origin_hub_id, destination_hub_id, status, priority, weight_kg, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (tracking_id, description, origin, destination, status, priority, weight, datetime.now()))
            print(f"   ✅ Added shipment: {tracking_id} - {description}")
        
        conn.commit()
        print(f"\n✅ Inserted {len(shipments_data)} shipments successfully!")
    else:
        print(f"ℹ️  Shipments already exist, skipping shipment insertion")
    
    # Final count check
    print("\n" + "="*60)
    print("📊 FINAL DATABASE SUMMARY")
    print("="*60)
    
    cur.execute("SELECT COUNT(*) FROM users")
    print(f"👥 Total Users: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM hubs")
    print(f"🏢 Total Hubs: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM routes")
    print(f"🚛 Total Routes: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM shipments")
    print(f"📦 Total Shipments: {cur.fetchone()[0]}")
    
    print("\n" + "="*60)
    print("✅ ALL DATA INSERTED SUCCESSFULLY!")
    print("="*60)
    
    print("\n🔐 TEST CREDENTIALS:")
    print("   Admin:   admin@bluecart.com / admin123")
    print("   Manager: rajesh.kumar@bluecart.com / rajesh123")
    print("   Driver:  amit.patel@bluecart.com / amit123")
    
    cur.close()
    conn.close()
    print("\n✅ Database connection closed")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
