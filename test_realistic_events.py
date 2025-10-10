"""
Test creating a few shipments with realistic events and statuses
"""

from generate_realistic_data import *

# Generate just 5 shipments to test the new backend handling
def test_realistic_data():
    print("🧪 Testing realistic shipment creation with events...")
    
    for i in range(5):
        # Generate realistic data
        shipment_data = generate_shipment_data()
        
        print(f"\n📦 Test Shipment {i+1}:")
        print(f"   📊 Status: {shipment_data['status']}")
        print(f"   🚚 Events: {len(shipment_data['events'])} events")
        print(f"   💰 Cost: ₹{shipment_data['cost']}")
        
        # Create via API
        if create_shipment_via_api(shipment_data):
            print(f"   ✅ Success!")
        else:
            print(f"   ❌ Failed!")

if __name__ == "__main__":
    test_realistic_data()