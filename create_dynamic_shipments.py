import requests
import json
import time

# Create a few test shipments to demonstrate dynamic dashboard
api_base = "http://localhost:8000"

shipments_to_create = [
    {
        "sender_name": "Dynamic Test Co",
        "receiver_name": "Real Client Ltd", 
        "origin_hub": "Mumbai Central Hub",
        "destination_hub": "Delhi North Hub",
        "weight": 3.2,
        "value": 2500
    },
    {
        "sender_name": "Live Demo Inc",
        "receiver_name": "Active Receiver",
        "origin_hub": "Delhi North Hub", 
        "destination_hub": "Bangalore South Hub",
        "weight": 1.8,
        "value": 1800
    },
    {
        "sender_name": "Dynamic Corp",
        "receiver_name": "Real Time Customer",
        "origin_hub": "Chennai East Hub",
        "destination_hub": "Mumbai Central Hub", 
        "weight": 4.5,
        "value": 3200
    }
]

print("🚀 Creating dynamic test shipments...")

for i, shipment in enumerate(shipments_to_create, 1):
    try:
        response = requests.post(
            f"{api_base}/api/shipments",
            headers={"Content-Type": "application/json"},
            json=shipment
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Shipment {i} created: {result['trackingNumber']}")
        else:
            print(f"❌ Failed to create shipment {i}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error creating shipment {i}: {e}")
    
    time.sleep(1)  # Small delay between requests

print("✅ Dynamic test shipments created! Dashboard stats should update automatically.")
print("🔄 The dashboard auto-refreshes every 30 seconds, or click 'Refresh' button.")