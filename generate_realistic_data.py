"""
BlueCart ERP - Realistic Shipment Data Generator
==============================================
Generates 1287+ shipments with realistic delays, bottlenecks, and process loops
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests

# Configuration
BASE_URL = "http://localhost:8000"
TOTAL_SHIPMENTS = 1287

# Indian cities and logistics hubs
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
    "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Kanpur",
    "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad",
    "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik"
]

HUBS = [
    "Mumbai Central Hub", "Delhi North Hub", "Bangalore Tech Hub", 
    "Chennai Port Hub", "Hyderabad Central", "Kolkata East Hub",
    "Pune West Hub", "Ahmedabad Industrial Hub", "Jaipur Pink Hub"
]

# Realistic company names and addresses
COMPANIES = [
    {"name": "TechCorp Solutions Pvt Ltd", "phone": "+91-9876543210"},
    {"name": "Global Logistics India", "phone": "+91-9876543211"},
    {"name": "Mumbai Traders Co.", "phone": "+91-9876543212"},
    {"name": "Delhi Electronics Hub", "phone": "+91-9876543213"},
    {"name": "Bangalore Software Exports", "phone": "+91-9876543214"},
    {"name": "Chennai Auto Parts Ltd", "phone": "+91-9876543215"},
    {"name": "Hyderabad Pharma Corp", "phone": "+91-9876543216"},
    {"name": "Kolkata Textiles Pvt Ltd", "phone": "+91-9876543217"},
    {"name": "Pune Manufacturing Co", "phone": "+91-9876543218"},
    {"name": "Ahmedabad Chemical Works", "phone": "+91-9876543219"},
]

# Package types and their typical weights/dimensions
PACKAGE_TYPES = [
    {"type": "Electronics", "weight_range": (0.5, 5.0), "dimensions": {"length": (20, 50), "width": (15, 40), "height": (5, 25)}},
    {"type": "Pharmaceuticals", "weight_range": (0.1, 2.0), "dimensions": {"length": (10, 30), "width": (8, 25), "height": (3, 15)}},
    {"type": "Auto Parts", "weight_range": (2.0, 25.0), "dimensions": {"length": (30, 80), "width": (20, 60), "height": (10, 40)}},
    {"type": "Textiles", "weight_range": (1.0, 15.0), "dimensions": {"length": (40, 100), "width": (30, 80), "height": (15, 50)}},
    {"type": "Documents", "weight_range": (0.1, 1.0), "dimensions": {"length": (20, 35), "width": (15, 25), "height": (1, 5)}},
    {"type": "Food Products", "weight_range": (0.5, 10.0), "dimensions": {"length": (25, 60), "width": (20, 45), "height": (8, 30)}},
    {"type": "Machinery Parts", "weight_range": (5.0, 50.0), "dimensions": {"length": (50, 120), "width": (40, 90), "height": (20, 60)}},
]

# Service types with different processing patterns
SERVICE_TYPES = ["standard", "express", "overnight"]

# Status progression patterns with bottlenecks
STATUS_PATTERNS = {
    "smooth": ["pending", "picked_up", "in_transit", "out_for_delivery", "delivered"],
    "delayed_pickup": ["pending", "pending", "pending", "picked_up", "in_transit", "out_for_delivery", "delivered"],
    "hub_bottleneck": ["pending", "picked_up", "in_transit", "in_transit", "in_transit", "out_for_delivery", "delivered"],
    "delivery_issues": ["pending", "picked_up", "in_transit", "out_for_delivery", "out_for_delivery", "out_for_delivery", "delivered"],
    "failed_attempt": ["pending", "picked_up", "in_transit", "out_for_delivery", "failed", "out_for_delivery", "delivered"],
    "multiple_failures": ["pending", "picked_up", "in_transit", "out_for_delivery", "failed", "out_for_delivery", "failed", "out_for_delivery", "delivered"],
    "stuck_in_transit": ["pending", "picked_up", "in_transit", "in_transit", "in_transit", "in_transit", "out_for_delivery", "delivered"],
}

def generate_realistic_events(status_pattern: List[str], start_date: datetime, service_type: str) -> List[Dict]:
    """Generate realistic events with proper timestamps and locations"""
    events = []
    current_time = start_date
    
    # Service type affects speed
    time_multipliers = {"overnight": 0.3, "express": 0.6, "standard": 1.0}
    multiplier = time_multipliers.get(service_type, 1.0)
    
    for i, status in enumerate(status_pattern):
        if status == "pending":
            base_hours = random.uniform(2, 24) * multiplier
        elif status == "picked_up":
            base_hours = random.uniform(4, 12) * multiplier
        elif status == "in_transit":
            base_hours = random.uniform(6, 48) * multiplier
        elif status == "out_for_delivery":
            base_hours = random.uniform(2, 24) * multiplier
        elif status == "failed":
            base_hours = random.uniform(8, 72) * multiplier
        else:  # delivered
            base_hours = random.uniform(1, 6) * multiplier
        
        # Add some randomness
        hours_offset = base_hours + random.uniform(-base_hours*0.3, base_hours*0.3)
        current_time += timedelta(hours=max(0.5, hours_offset))
        
        # Generate location based on status
        if status == "pending":
            location = "Origin Hub"
            description = "Shipment created and pending pickup"
        elif status == "picked_up":
            location = random.choice(HUBS)
            description = f"Package picked up from sender and arrived at {location}"
        elif status == "in_transit":
            location = random.choice(HUBS)
            description = f"Package in transit at {location}"
        elif status == "out_for_delivery":
            location = "Local Delivery Hub"
            description = "Package out for delivery to recipient"
        elif status == "failed":
            location = "Local Delivery Hub"
            reasons = ["Recipient not available", "Incorrect address", "Access restricted", "Weather conditions", "Vehicle breakdown"]
            description = f"Delivery failed: {random.choice(reasons)}"
        else:  # delivered
            location = "Destination"
            description = "Package successfully delivered to recipient"
        
        event = {
            "id": f"EV{int(current_time.timestamp())}{random.randint(100, 999)}",
            "timestamp": current_time.isoformat(),
            "status": status,
            "location": location,
            "description": description
        }
        events.append(event)
    
    return events

def generate_realistic_cost(weight: float, service_type: str, distance_km: int) -> float:
    """Generate realistic shipping cost based on weight, service, and distance"""
    base_rate = {"standard": 25, "express": 45, "overnight": 80}
    rate = base_rate.get(service_type, 25)
    
    # Weight-based pricing
    weight_cost = weight * 8.5
    
    # Distance-based pricing (₹1.2 per km for standard)
    distance_multiplier = {"standard": 1.2, "express": 1.8, "overnight": 2.5}
    distance_cost = distance_km * distance_multiplier.get(service_type, 1.2)
    
    # Fuel surcharge and taxes
    fuel_surcharge = (rate + weight_cost + distance_cost) * 0.12
    taxes = (rate + weight_cost + distance_cost + fuel_surcharge) * 0.18
    
    total = rate + weight_cost + distance_cost + fuel_surcharge + taxes
    return round(total, 2)

def generate_shipment_data() -> Dict[str, Any]:
    """Generate a single realistic shipment"""
    # Choose random companies for sender and receiver
    sender_company = random.choice(COMPANIES)
    receiver_company = random.choice(COMPANIES)
    
    # Choose cities
    sender_city = random.choice(CITIES)
    receiver_city = random.choice([city for city in CITIES if city != sender_city])
    
    # Generate addresses
    sender_address = f"{random.randint(1, 999)}, {random.choice(['MG Road', 'Main Street', 'Industrial Area', 'Tech Park', 'Commercial Complex'])}, {sender_city}, {random.choice(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Telangana', 'Gujarat'])} {random.randint(400001, 695001)}"
    receiver_address = f"{random.randint(1, 999)}, {random.choice(['Ring Road', 'Station Road', 'Market Area', 'Residential Complex', 'Business District'])}, {receiver_city}, {random.choice(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Telangana', 'Gujarat'])} {random.randint(400001, 695001)}"
    
    # Choose package type
    package_type = random.choice(PACKAGE_TYPES)
    weight = round(random.uniform(*package_type["weight_range"]), 2)
    
    dimensions = {
        "length": round(random.uniform(*package_type["dimensions"]["length"]), 1),
        "width": round(random.uniform(*package_type["dimensions"]["width"]), 1),
        "height": round(random.uniform(*package_type["dimensions"]["height"]), 1)
    }
    
    # Service type
    service_type = random.choice(SERVICE_TYPES)
    
    # Calculate estimated distance (simplified)
    distance_km = random.randint(50, 2500)
    
    # Generate cost
    cost = generate_realistic_cost(weight, service_type, distance_km)
    
    # Choose status pattern based on realistic probabilities
    pattern_weights = {
        "smooth": 0.60,  # 60% smooth deliveries
        "delayed_pickup": 0.12,  # 12% pickup delays
        "hub_bottleneck": 0.10,  # 10% hub issues
        "delivery_issues": 0.08,  # 8% delivery problems
        "failed_attempt": 0.06,  # 6% single failure attempts
        "multiple_failures": 0.03,  # 3% multiple failures
        "stuck_in_transit": 0.01   # 1% severe transit issues
    }
    
    pattern_name = random.choices(
        list(pattern_weights.keys()),
        weights=list(pattern_weights.values())
    )[0]
    
    status_pattern = STATUS_PATTERNS[pattern_name]
    
    # Generate realistic creation date (last 6 months)
    start_date = datetime.now() - timedelta(days=random.randint(1, 180))
    
    # Generate events
    events = generate_realistic_events(status_pattern, start_date, service_type)
    
    # Current status is the last event's status
    current_status = events[-1]["status"]
    
    # Estimate delivery based on service type
    if service_type == "overnight":
        delivery_days = 1
    elif service_type == "express":
        delivery_days = 2
    else:
        delivery_days = random.randint(3, 7)
    
    estimated_delivery = start_date + timedelta(days=delivery_days)
    
    # Actual delivery if delivered
    actual_delivery = events[-1]["timestamp"] if current_status == "delivered" else None
    
    return {
        "senderName": sender_company["name"],
        "senderPhone": sender_company["phone"],
        "senderAddress": sender_address,
        "receiverName": receiver_company["name"],
        "receiverPhone": receiver_company["phone"],
        "receiverAddress": receiver_address,
        "packageDetails": f"{package_type['type']} - {random.choice(['Fragile', 'Standard', 'Heavy', 'Express', 'Perishable'])} packaging",
        "weight": weight,
        "dimensions": dimensions,
        "serviceType": service_type,
        "cost": cost,
        "events": events,
        "status": current_status,
        "estimatedDelivery": estimated_delivery.isoformat(),
        "actualDelivery": actual_delivery,
        "hubId": random.choice(HUBS),
        "route": f"{sender_city} → {random.choice(HUBS)} → {receiver_city}"
    }

def create_shipment_via_api(shipment_data: Dict) -> bool:
    """Create a shipment via the API"""
    try:
        response = requests.post(f"{BASE_URL}/api/shipments", json=shipment_data, timeout=10)
        if response.status_code == 201:
            print(f"✅ Created shipment: {response.json().get('trackingNumber', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to create shipment: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating shipment: {e}")
        return False

def main():
    """Generate and populate realistic shipment data"""
    print(f"🚀 Starting realistic shipment data generation...")
    print(f"📦 Target: {TOTAL_SHIPMENTS} shipments")
    print(f"🌐 API Endpoint: {BASE_URL}")
    
    # Test API connectivity
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend not responding. Status: {response.status_code}")
            return
        print("✅ Backend API is responding")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    successful_creations = 0
    failed_creations = 0
    
    print(f"\n📊 Creating {TOTAL_SHIPMENTS} realistic shipments...")
    
    for i in range(TOTAL_SHIPMENTS):
        try:
            shipment_data = generate_shipment_data()
            
            if create_shipment_via_api(shipment_data):
                successful_creations += 1
            else:
                failed_creations += 1
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"📈 Progress: {i + 1}/{TOTAL_SHIPMENTS} ({((i + 1)/TOTAL_SHIPMENTS)*100:.1f}%)")
                print(f"   ✅ Success: {successful_creations}, ❌ Failed: {failed_creations}")
        
        except KeyboardInterrupt:
            print("\n🛑 Process interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error at shipment {i + 1}: {e}")
            failed_creations += 1
    
    print(f"\n🎉 Data generation completed!")
    print(f"📊 Final Results:")
    print(f"   ✅ Successfully created: {successful_creations} shipments")
    print(f"   ❌ Failed: {failed_creations} shipments")
    print(f"   📈 Success rate: {(successful_creations/(successful_creations + failed_creations))*100:.1f}%")
    
    if successful_creations > 0:
        print(f"\n🔍 Your BlueCart ERP now has realistic data with:")
        print(f"   📦 Varied shipment types and weights")
        print(f"   🚚 Multiple delivery patterns including delays")
        print(f"   🏭 Hub bottlenecks and process loops")
        print(f"   📊 Realistic failure scenarios")
        print(f"   💰 Dynamic pricing based on weight/distance/service")

if __name__ == "__main__":
    main()