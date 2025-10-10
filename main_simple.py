from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from pydantic import BaseModel, Field
import random
import string

# Initialize FastAPI app
app = FastAPI(
    title="BlueCart ERP API",
    description="Complete ERP system for logistics and shipment management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (for development/testing)
shipments_db: Dict[str, Dict] = {}

# Pydantic models
class Dimensions(BaseModel):
    length: float = Field(..., gt=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)

class ShipmentCreate(BaseModel):
    senderName: str = Field(..., min_length=1)
    senderPhone: Optional[str] = None
    senderAddress: str = Field(..., min_length=1)
    receiverName: str = Field(..., min_length=1)
    receiverPhone: Optional[str] = None
    receiverAddress: str = Field(..., min_length=1)
    packageDetails: str = Field(..., min_length=1)
    weight: float = Field(..., gt=0)
    dimensions: Dimensions
    serviceType: str = Field("standard", pattern="^(standard|express|overnight)$")
    cost: float = Field(..., gt=0)

class ShipmentResponse(BaseModel):
    id: str
    trackingNumber: str
    senderName: str
    senderPhone: Optional[str]
    senderAddress: str
    receiverName: str
    receiverPhone: Optional[str]
    receiverAddress: str
    packageDetails: str
    weight: float
    dimensions: Dict[str, float]
    serviceType: str
    status: str
    pickupDate: Optional[str]
    estimatedDelivery: Optional[str]
    actualDelivery: Optional[str]
    route: Optional[str]
    hubId: Optional[str]
    events: List[Dict[str, Any]]
    cost: float
    createdAt: str
    updatedAt: str

class HealthCheck(BaseModel):
    status: str
    message: str
    timestamp: datetime

# Helper functions
def generate_id():
    return f"SH{int(datetime.now().timestamp())}"

def generate_tracking_number():
    return f"TN{int(datetime.now().timestamp())}"

def calculate_estimated_delivery(service_type: str) -> str:
    from datetime import timedelta
    base_date = datetime.now()
    days_map = {"standard": 3, "express": 2, "overnight": 1}
    days = days_map.get(service_type, 3)
    estimated = base_date + timedelta(days=days)
    return estimated.isoformat()

# API Endpoints
@app.get("/", response_model=HealthCheck)
async def root():
    return HealthCheck(
        status="healthy",
        message="BlueCart ERP FastAPI Backend is running",
        timestamp=datetime.now()
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        message="BlueCart ERP FastAPI Backend - All systems operational",
        timestamp=datetime.now()
    )

@app.post("/api/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(shipment: ShipmentCreate):
    """Create a new shipment"""
    try:
        shipment_id = generate_id()
        tracking_number = generate_tracking_number()
        now = datetime.now().isoformat()
        
        # Create initial event
        initial_event = {
            "id": f"EV{int(datetime.now().timestamp())}",
            "timestamp": now,
            "status": "pending",
            "location": "Origin Hub",
            "description": "Shipment created and pending pickup"
        }
        
        # Create shipment
        new_shipment = {
            "id": shipment_id,
            "trackingNumber": tracking_number,
            "senderName": shipment.senderName,
            "senderPhone": shipment.senderPhone,
            "senderAddress": shipment.senderAddress,
            "receiverName": shipment.receiverName,
            "receiverPhone": shipment.receiverPhone,
            "receiverAddress": shipment.receiverAddress,
            "packageDetails": shipment.packageDetails,
            "weight": shipment.weight,
            "dimensions": shipment.dimensions.dict(),
            "serviceType": shipment.serviceType,
            "status": "pending",
            "pickupDate": None,
            "estimatedDelivery": calculate_estimated_delivery(shipment.serviceType),
            "actualDelivery": None,
            "route": None,
            "hubId": None,
            "events": [initial_event],
            "cost": shipment.cost,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Store in memory
        shipments_db[shipment_id] = new_shipment
        
        print(f"✅ Created shipment: {tracking_number} (ID: {shipment_id})")
        return ShipmentResponse(**new_shipment)
        
    except Exception as e:
        print(f"❌ Error creating shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create shipment: {str(e)}"
        )

@app.get("/api/shipments")
async def get_shipments(skip: int = 0, limit: int = 100):
    """Get all shipments"""
    try:
        all_shipments = list(shipments_db.values())
        
        # Sort by creation date (newest first)
        all_shipments.sort(key=lambda x: x["createdAt"], reverse=True)
        
        # Apply pagination
        paginated_shipments = all_shipments[skip:skip + limit]
        
        return {
            "shipments": paginated_shipments,
            "total": len(all_shipments),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        print(f"❌ Error getting shipments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve shipments: {str(e)}"
        )

@app.get("/api/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: str):
    """Get a specific shipment by ID or tracking number"""
    try:
        # Try to find by ID first
        shipment = shipments_db.get(shipment_id)
        
        # If not found by ID, try to find by tracking number
        if not shipment:
            for s in shipments_db.values():
                if s["trackingNumber"] == shipment_id:
                    shipment = s
                    break
        
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )
        
        return ShipmentResponse(**shipment)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve shipment: {str(e)}"
        )

@app.put("/api/shipments/{shipment_id}")
async def update_shipment(shipment_id: str, updates: dict):
    """Update a specific shipment"""
    try:
        shipment = shipments_db.get(shipment_id)
        
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )
        
        # Update fields
        for key, value in updates.items():
            if key in shipment and value is not None:
                shipment[key] = value
        
        shipment["updatedAt"] = datetime.now().isoformat()
        
        print(f"✅ Updated shipment: {shipment_id}")
        return ShipmentResponse(**shipment)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update shipment: {str(e)}"
        )

@app.delete("/api/shipments/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: str):
    """Delete a specific shipment"""
    try:
        if shipment_id not in shipments_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )
        
        del shipments_db[shipment_id]
        print(f"✅ Deleted shipment: {shipment_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete shipment: {str(e)}"
        )

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        total_shipments = len(shipments_db)
        
        # Count by status
        status_counts = {}
        total_revenue = 0
        
        for shipment in shipments_db.values():
            status = shipment.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_revenue += shipment.get("cost", 0)
        
        return {
            "total_shipments": total_shipments,
            "pending_shipments": status_counts.get("pending", 0),
            "in_transit_shipments": status_counts.get("in_transit", 0),
            "delivered_shipments": status_counts.get("delivered", 0),
            "failed_shipments": status_counts.get("failed", 0),
            "total_revenue": round(total_revenue, 2),
            "average_delivery_time": None,
            "top_routes": [],
            "daily_shipments": []
        }
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )

if __name__ == "__main__":
    print("🚀 Starting BlueCart ERP FastAPI Backend...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )