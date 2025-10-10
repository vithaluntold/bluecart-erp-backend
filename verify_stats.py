import requests
import json
from datetime import datetime

api_base = "http://localhost:8000"

print("📊 Current Dashboard Statistics (Real-time):")
print("=" * 50)

try:
    # Get ALL shipments (not limited to 100)
    shipments_response = requests.get(f"{api_base}/api/shipments?limit=10000")
    shipments_data = shipments_response.json()
    shipments = shipments_data.get('shipments', [])
    
    # Get ALL hubs  
    hubs_response = requests.get(f"{api_base}/api/hubs?limit=1000")
    hubs_data = hubs_response.json()
    hubs = hubs_data.get('hubs', [])
    
    # Get ALL users
    users_response = requests.get(f"{api_base}/api/users?limit=1000") 
    users_data = users_response.json()
    users = users_data.get('users', [])
    
    # Calculate statistics
    total_shipments = len(shipments)
    active_shipments = len([s for s in shipments if s['status'] in ['in-transit', 'picked-up', 'out-for-delivery']])
    total_hubs = len(hubs)
    total_users = len(users)
    drivers = [u for u in users if u.get('role') == 'driver']
    driver_count = len(drivers)
    
    # Today's deliveries
    today = datetime.now().strftime('%Y-%m-%d')
    delivered_today = len([s for s in shipments if s['status'] == 'delivered' and s.get('delivered_at', '').startswith(today)])
    
    # Pending pickups
    pending_pickups = len([s for s in shipments if s['status'] == 'pending'])
    
    # Revenue calculation
    total_revenue = 0
    for shipment in shipments:
        revenue = shipment.get('value', 0) or (shipment.get('weight', 1) * 50 + 200)
        total_revenue += revenue
    
    # Active routes
    active_routes = set()
    for s in shipments:
        if s['status'] in ['in-transit', 'picked-up', 'out-for-delivery']:
            if s.get('origin_hub') and s.get('destination_hub'):
                route = f"{s['origin_hub']}->{s['destination_hub']}"
                active_routes.add(route)
    
    print(f"📦 Total Shipments: {total_shipments}")
    print(f"🚚 Active Shipments: {active_shipments}")
    print(f"🏢 Total Hubs: {total_hubs}")
    print(f"👨‍💼 Delivery Personnel: {driver_count}")  
    print(f"💰 Revenue: ₹{total_revenue:,}")
    print(f"✅ Delivered Today: {delivered_today}")
    print(f"⏳ Pending Pickups: {pending_pickups}")
    print(f"🗺️ Active Routes: {len(active_routes)}")
    
    print("\n🔄 These numbers should match your dashboard!")
    
except Exception as e:
    print(f"❌ Error: {e}")