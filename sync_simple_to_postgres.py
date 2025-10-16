"""
Sync Simple In-Memory Data to PostgreSQL (Render Database)
This script dumps all data from main_simple.py to the Render PostgreSQL database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import datetime

# Render PostgreSQL Connection
RENDER_DB_URL = "postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp"

# Sample data from main_simple.py
users_data = [
    {
        "id": "1",
        "email": "admin@bluecart.com",
        "password": "admin123",  # Will be hashed
        "name": "Admin User",
        "role": "admin",
        "phone": "+91-9876543210"
    },
    {
        "id": "2",
        "email": "rajesh@bluecart.com",
        "password": "rajesh123",
        "name": "Rajesh Kumar",
        "role": "hub_manager",
        "phone": "+91-9876543211"
    },
    {
        "id": "3",
        "email": "priya@bluecart.com",
        "password": "priya123",
        "name": "Priya Singh",
        "role": "hub_manager",
        "phone": "+91-9876543212"
    },
    {
        "id": "4",
        "email": "amit@bluecart.com",
        "password": "amit123",
        "name": "Amit Patel",
        "role": "driver",
        "phone": "+91-9876543213"
    },
    {
        "id": "5",
        "email": "sneha@bluecart.com",
        "password": "sneha123",
        "name": "Sneha Verma",
        "role": "driver",
        "phone": "+91-9876543214"
    },
    {
        "id": "6",
        "email": "ops@bluecart.com",
        "password": "ops123",
        "name": "Operations Team",
        "role": "operations",
        "phone": "+91-9876543215"
    }
]

hubs_data = [
    {
        "id": "1",
        "name": "Mumbai Central Hub",
        "location": "Mumbai, Maharashtra",
        "capacity": 10000,
        "current_load": 7500,
        "status": "active",
        "manager_id": "2"
    },
    {
        "id": "2",
        "name": "Delhi North Hub",
        "location": "Delhi, NCR",
        "capacity": 8000,
        "current_load": 6000,
        "status": "active",
        "manager_id": "3"
    },
    {
        "id": "3",
        "name": "Bangalore Tech Hub",
        "location": "Bangalore, Karnataka",
        "capacity": 12000,
        "current_load": 8500,
        "status": "active",
        "manager_id": "2"
    },
    {
        "id": "4",
        "name": "Chennai Port Hub",
        "location": "Chennai, Tamil Nadu",
        "capacity": 6000,
        "current_load": 4000,
        "status": "active",
        "manager_id": "3"
    },
    {
        "id": "5",
        "name": "Kolkata East Hub",
        "location": "Kolkata, West Bengal",
        "capacity": 5000,
        "current_load": 3200,
        "status": "maintenance",
        "manager_id": "2"
    }
]

shipments_data = [
    {
        "id": "1",
        "tracking_number": "BC1001",
        "origin": "Mumbai Central Hub",
        "destination": "Delhi North Hub",
        "status": "in_transit",
        "current_location": "Surat, Gujarat",
        "estimated_delivery": "2024-01-25",
        "driver_id": "4",
        "weight": 150.5,
        "dimensions": "120x80x60 cm"
    },
    {
        "id": "2",
        "tracking_number": "BC1002",
        "origin": "Bangalore Tech Hub",
        "destination": "Chennai Port Hub",
        "status": "delivered",
        "current_location": "Chennai Port Hub",
        "estimated_delivery": "2024-01-20",
        "driver_id": "5",
        "weight": 85.2,
        "dimensions": "100x60x50 cm"
    },
    {
        "id": "3",
        "tracking_number": "BC1003",
        "origin": "Delhi North Hub",
        "destination": "Kolkata East Hub",
        "status": "pending",
        "current_location": "Delhi North Hub",
        "estimated_delivery": "2024-01-28",
        "driver_id": None,
        "weight": 220.0,
        "dimensions": "150x100x80 cm"
    }
]

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def sync_users(cursor):
    """Sync users to PostgreSQL"""
    print("\n" + "="*60)
    print("  SYNCING USERS")
    print("="*60)
    
    # Clear existing users
    cursor.execute("DELETE FROM users")
    print("✅ Cleared existing users")
    
    # Insert users with hashed passwords
    for user in users_data:
        hashed_password = hash_password(user["password"])
        # Create username from email (part before @)
        username = user["email"].split('@')[0]
        
        cursor.execute("""
            INSERT INTO users (id, username, email, password, name, role, phone, full_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            int(user["id"]),  # Convert to integer
            username,
            user["email"],
            hashed_password,
            user["name"],
            user["role"],
            user["phone"],
            user["name"]  # Use name as full_name too
        ))
        print(f"✅ Created user: {user['email']} (username: {username}, password encrypted)")
    
    print(f"\n📊 Total users synced: {len(users_data)}")

def sync_hubs(cursor):
    """Sync hubs to PostgreSQL"""
    print("\n" + "="*60)
    print("  SYNCING HUBS")
    print("="*60)
    
    # Clear existing hubs
    cursor.execute("DELETE FROM hubs")
    print("✅ Cleared existing hubs")
    
    # Insert hubs
    for hub in hubs_data:
        cursor.execute("""
            INSERT INTO hubs (id, name, address, capacity, current_load, status, manager_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            hub["id"],
            hub["name"],
            hub["location"],  # Maps to address
            hub["capacity"],
            hub["current_load"],
            hub["status"],
            hub["manager_id"]
        ))
        print(f"✅ Created hub: {hub['name']} - {hub['location']}")
    
    print(f"\n📊 Total hubs synced: {len(hubs_data)}")

def sync_shipments(cursor):
    """Sync shipments to PostgreSQL"""
    print("\n" + "="*60)
    print("  SYNCING SHIPMENTS")
    print("="*60)
    
    # Clear existing shipments
    cursor.execute("DELETE FROM shipments")
    print("✅ Cleared existing shipments")
    
    # Insert shipments
    for shipment in shipments_data:
        cursor.execute("""
            INSERT INTO shipments (
                tracking_number, origin_hub, destination_hub, status, 
                driver_id, weight, dimensions, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            shipment["tracking_number"],
            shipment["origin"],  # Maps to origin_hub
            shipment["destination"],  # Maps to destination_hub
            shipment["status"],
            shipment["driver_id"],
            shipment["weight"],
            shipment["dimensions"]
        ))
        print(f"✅ Created shipment: {shipment['tracking_number']} - {shipment['status']}")
    
    print(f"\n📊 Total shipments synced: {len(shipments_data)}")

def verify_data(cursor):
    """Verify all data was synced correctly"""
    print("\n" + "="*60)
    print("  VERIFICATION SUMMARY")
    print("="*60)
    
    # Count users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    print(f"\n👥 Users: {user_count}/{len(users_data)} {'✅' if user_count == len(users_data) else '❌'}")
    
    # Count hubs
    cursor.execute("SELECT COUNT(*) as count FROM hubs")
    hub_count = cursor.fetchone()['count']
    print(f"🏢 Hubs: {hub_count}/{len(hubs_data)} {'✅' if hub_count == len(hubs_data) else '❌'}")
    
    # Count shipments
    cursor.execute("SELECT COUNT(*) as count FROM shipments")
    shipment_count = cursor.fetchone()['count']
    print(f"📦 Shipments: {shipment_count}/{len(shipments_data)} {'✅' if shipment_count == len(shipments_data) else '❌'}")
    
    # Show sample user (without password)
    print("\n" + "="*60)
    print("  SAMPLE USER DATA")
    print("="*60)
    cursor.execute("SELECT id, email, name, role, phone FROM users WHERE email = 'admin@bluecart.com'")
    admin = cursor.fetchone()
    if admin:
        print(f"\n✅ Admin User:")
        print(f"   ID: {admin['id']}")
        print(f"   Email: {admin['email']}")
        print(f"   Name: {admin['name']}")
        print(f"   Role: {admin['role']}")
        print(f"   Phone: {admin['phone']}")
    
    # Show sample hub
    print("\n" + "="*60)
    print("  SAMPLE HUB DATA")
    print("="*60)
    cursor.execute("SELECT * FROM hubs WHERE id = '1'")
    hub = cursor.fetchone()
    if hub:
        print(f"\n✅ {hub['name']}:")
        print(f"   Location: {hub['location']}")
        print(f"   Capacity: {hub['capacity']}")
        print(f"   Current Load: {hub['current_load']}")
        print(f"   Status: {hub['status']}")
        print(f"   Manager ID: {hub['manager_id']}")
    
    # Show sample shipment
    print("\n" + "="*60)
    print("  SAMPLE SHIPMENT DATA")
    print("="*60)
    cursor.execute("SELECT * FROM shipments WHERE id = '1'")
    shipment = cursor.fetchone()
    if shipment:
        print(f"\n✅ {shipment['tracking_number']}:")
        print(f"   Origin: {shipment['origin']}")
        print(f"   Destination: {shipment['destination']}")
        print(f"   Status: {shipment['status']}")
        print(f"   Current Location: {shipment['current_location']}")
        print(f"   Driver ID: {shipment['driver_id']}")
        print(f"   Weight: {shipment['weight']} kg")

def main():
    """Main sync function"""
    print("\n" + "="*60)
    print("  BLUECART ERP - DATABASE SYNC")
    print("  Syncing Simple Data to Render PostgreSQL")
    print("="*60)
    
    try:
        # Connect to database
        print("\n🔌 Connecting to Render PostgreSQL...")
        conn = psycopg2.connect(RENDER_DB_URL)
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("✅ Connected to database")
        
        # Sync all data
        sync_users(cursor)
        sync_hubs(cursor)
        sync_shipments(cursor)
        
        # Commit transaction
        conn.commit()
        print("\n✅ All changes committed to database")
        
        # Verify data
        verify_data(cursor)
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("  ✅ SYNC COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n🎉 All data synced to Render PostgreSQL database")
        print("🔐 All passwords encrypted with bcrypt")
        print("📊 Ready for testing at: https://your-render-app.onrender.com")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
