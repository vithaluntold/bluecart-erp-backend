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
import os

# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://bluecart-erp-frontend.onrender.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize test data
@app.on_event("startup")
async def startup_event():
    """Initialize test data on server startup"""
    initialize_test_data()

# In-memory storage (for development/testing)
shipments_db: Dict[str, Dict] = {}
hubs_db: Dict[str, Dict] = {}
routes_db: Dict[str, Dict] = {}
users_db: Dict[str, Dict] = {}

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

class HubCreate(BaseModel):
    name: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    pincode: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    manager: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    status: str = Field("active", pattern="^(active|inactive|maintenance)$")

class HubResponse(BaseModel):
    id: str
    name: str
    code: str
    address: str
    city: str
    state: str
    pincode: str
    phone: str
    manager: str
    capacity: int
    currentLoad: int
    status: str
    createdAt: str
    updatedAt: str

class Route(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    assigned_to: str = Field(..., min_length=1)
    hub_id: str = Field(..., min_length=1)
    shipment_ids: List[str] = Field(default_factory=list)
    estimated_distance: Optional[float] = None
    estimated_time: Optional[str] = None
    status: str = Field("planned", pattern="^(planned|in_progress|completed|cancelled)$")

class RouteResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    assigned_to: str
    hub_id: str
    shipment_ids: List[str]
    estimated_distance: Optional[float] = None
    estimated_time: Optional[str] = None
    status: str
    createdAt: str
    updatedAt: str

class User(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    phone: Optional[str] = None
    role: str = Field("driver", pattern="^(admin|manager|driver|operator)$")
    status: str = Field("active", pattern="^(active|inactive)$")

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    status: str
    createdAt: str
    updatedAt: str

class HealthCheck(BaseModel):
    status: str
    message: str
    timestamp: datetime

# Helper functions
def generate_id():
    return f"SH{int(datetime.now().timestamp())}"

def generate_hub_id():
    return f"HUB{int(datetime.now().timestamp())}"

def generate_route_id():
    return f"RT{int(datetime.now().timestamp())}"

def generate_user_id():
    return f"USR{int(datetime.now().timestamp())}"

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
async def create_shipment(shipment_data: dict):
    """Create a new shipment - handles both simple and complex data"""
    try:
        shipment_id = generate_id()
        tracking_number = generate_tracking_number()
        now = datetime.now().isoformat()
        
        # Handle events from data generator or create simple event
        events = shipment_data.get("events", [])
        if not events:
            # Simple creation - create initial event
            events = [{
                "id": f"EV{int(datetime.now().timestamp())}",
                "timestamp": now,
                "status": "pending",
                "location": "Origin Hub",
                "description": "Shipment created and pending pickup"
            }]
        
        # Determine current status from events
        current_status = events[-1]["status"] if events else "pending"
        
        # Handle dimensions - could be dict or Pydantic model
        dimensions = shipment_data.get("dimensions", {})
        if hasattr(dimensions, 'dict'):
            dimensions = dimensions.dict()
        
        # Create shipment
        new_shipment = {
            "id": shipment_id,
            "trackingNumber": tracking_number,
            "senderName": shipment_data.get("senderName"),
            "senderPhone": shipment_data.get("senderPhone"),
            "senderAddress": shipment_data.get("senderAddress"),
            "receiverName": shipment_data.get("receiverName"),
            "receiverPhone": shipment_data.get("receiverPhone"),
            "receiverAddress": shipment_data.get("receiverAddress"),
            "packageDetails": shipment_data.get("packageDetails"),
            "weight": shipment_data.get("weight"),
            "dimensions": dimensions,
            "serviceType": shipment_data.get("serviceType", "standard"),
            "status": current_status,
            "pickupDate": shipment_data.get("pickupDate"),
            "estimatedDelivery": shipment_data.get("estimatedDelivery") or calculate_estimated_delivery(shipment_data.get("serviceType", "standard")),
            "actualDelivery": shipment_data.get("actualDelivery"),
            "route": shipment_data.get("route"),
            "hubId": shipment_data.get("hubId"),
            "events": events,
            "cost": shipment_data.get("cost", 0),
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

# Hub Management Endpoints
@app.post("/api/hubs", response_model=HubResponse, status_code=status.HTTP_201_CREATED)
async def create_hub(hub: HubCreate):
    """Create a new hub"""
    try:
        hub_id = generate_hub_id()
        now = datetime.now().isoformat()
        
        # Create hub
        new_hub = {
            "id": hub_id,
            "name": hub.name,
            "code": hub.code,
            "address": hub.address,
            "city": hub.city,
            "state": hub.state,
            "pincode": hub.pincode,
            "phone": hub.phone,
            "manager": hub.manager,
            "capacity": hub.capacity,
            "currentLoad": 0,  # Start with 0 load
            "status": hub.status,
            "createdAt": now,
            "updatedAt": now
        }
        
        # Store in memory
        hubs_db[hub_id] = new_hub
        
        print(f"✅ Created hub: {hub.name} (ID: {hub_id})")
        return HubResponse(**new_hub)
        
    except Exception as e:
        print(f"❌ Error creating hub: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create hub: {str(e)}"
        )

@app.get("/api/hubs")
async def get_hubs(skip: int = 0, limit: int = 100):
    """Get all hubs"""
    try:
        all_hubs = list(hubs_db.values())
        
        # Sort by creation date (newest first)
        all_hubs.sort(key=lambda x: x["createdAt"], reverse=True)
        
        # Apply pagination
        paginated_hubs = all_hubs[skip:skip + limit]
        
        return {
            "hubs": paginated_hubs,
            "total": len(all_hubs),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        print(f"❌ Error getting hubs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hubs: {str(e)}"
        )

@app.get("/api/hubs/{hub_id}", response_model=HubResponse)
async def get_hub(hub_id: str):
    """Get a specific hub by ID"""
    try:
        hub = hubs_db.get(hub_id)
        
        if not hub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hub not found"
            )
        
        return HubResponse(**hub)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting hub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hub: {str(e)}"
        )

@app.put("/api/hubs/{hub_id}")
async def update_hub(hub_id: str, updates: dict):
    """Update a specific hub"""
    try:
        hub = hubs_db.get(hub_id)
        
        if not hub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hub not found"
            )
        
        # Update fields
        for key, value in updates.items():
            if key in hub and value is not None:
                hub[key] = value
        
        hub["updatedAt"] = datetime.now().isoformat()
        
        print(f"✅ Updated hub: {hub_id}")
        return HubResponse(**hub)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating hub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hub: {str(e)}"
        )

@app.delete("/api/hubs/{hub_id}")
async def delete_hub(hub_id: str):
    """Delete a specific hub"""
    try:
        if hub_id not in hubs_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hub not found"
            )
        
        del hubs_db[hub_id]
        
        print(f"✅ Deleted hub: {hub_id}")
        return {"message": "Hub deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting hub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete hub: {str(e)}"
        )

# Routes endpoints
@app.post("/api/routes", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(route_data: Route):
    """Create a new route"""
    try:
        route_id = generate_route_id()
        current_time = datetime.now().isoformat()
        
        new_route = {
            "id": route_id,
            "name": route_data.name,
            "description": route_data.description,
            "assigned_to": route_data.assigned_to,
            "hub_id": route_data.hub_id,
            "shipment_ids": route_data.shipment_ids,
            "estimated_distance": route_data.estimated_distance,
            "estimated_time": route_data.estimated_time,
            "status": route_data.status,
            "createdAt": current_time,
            "updatedAt": current_time
        }
        
        routes_db[route_id] = new_route
        
        print(f"✅ Created route: {route_id} - {route_data.name}")
        return new_route
        
    except Exception as e:
        print(f"❌ Error creating route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create route: {str(e)}"
        )

@app.get("/api/routes")
async def get_routes(skip: int = 0, limit: int = 100):
    """Get all routes"""
    try:
        all_routes = list(routes_db.values())
        all_routes.sort(key=lambda x: x["createdAt"], reverse=True)
        
        paginated_routes = all_routes[skip:skip + limit]
        
        return {
            "routes": paginated_routes,
            "total": len(all_routes),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"❌ Error getting routes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve routes: {str(e)}"
        )

@app.get("/api/routes/{route_id}", response_model=RouteResponse)
async def get_route(route_id: str):
    """Get a specific route by ID"""
    try:
        route = routes_db.get(route_id)
        if route:
            print(f"✅ Found route: {route_id}")
            return route
            
        # If not found by exact ID, try searching by name or other identifier
        for r in routes_db.values():
            if r["name"].lower() == route_id.lower():
                print(f"✅ Found route by name: {route_id}")
                return r
        
        print(f"❌ Route not found: {route_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve route: {str(e)}"
        )

@app.put("/api/routes/{route_id}")
async def update_route(route_id: str, route_data: Route):
    """Update a specific route"""
    try:
        route = routes_db.get(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Update fields
        route["name"] = route_data.name
        route["description"] = route_data.description
        route["assigned_to"] = route_data.assigned_to
        route["hub_id"] = route_data.hub_id
        route["shipment_ids"] = route_data.shipment_ids
        route["estimated_distance"] = route_data.estimated_distance
        route["estimated_time"] = route_data.estimated_time
        route["status"] = route_data.status
        route["updatedAt"] = datetime.now().isoformat()
        
        routes_db[route_id] = route
        
        print(f"✅ Updated route: {route_id}")
        return route
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update route: {str(e)}"
        )

@app.delete("/api/routes/{route_id}")
async def delete_route(route_id: str):
    """Delete a specific route"""
    try:
        if route_id not in routes_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        del routes_db[route_id]
        
        print(f"✅ Deleted route: {route_id}")
        return {"message": "Route deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete route: {str(e)}"
        )

# Users endpoints
@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: User):
    """Create a new user"""
    try:
        user_id = generate_user_id()
        current_time = datetime.now().isoformat()
        
        new_user = {
            "id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "phone": user_data.phone,
            "role": user_data.role,
            "status": user_data.status,
            "createdAt": current_time,
            "updatedAt": current_time
        }
        
        users_db[user_id] = new_user
        
        print(f"✅ Created user: {user_id} - {user_data.name}")
        return new_user
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@app.get("/api/users")
async def get_users(skip: int = 0, limit: int = 100):
    """Get all users"""
    try:
        all_users = list(users_db.values())
        all_users.sort(key=lambda x: x["createdAt"], reverse=True)
        
        paginated_users = all_users[skip:skip + limit]
        
        return {
            "users": paginated_users,
            "total": len(all_users),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    try:
        user = users_db.get(user_id)
        if user:
            print(f"✅ Found user: {user_id}")
            return user
            
        print(f"❌ User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: dict):
    """Update a specific user by ID"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for update: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        existing_user = users_db[user_id]
        
        # Update only provided fields
        updatable_fields = ["name", "email", "phone", "role", "address", "city", "state", "zipCode"]
        for field in updatable_fields:
            if field in user_data and user_data[field] is not None:
                existing_user[field] = user_data[field]
        
        # Update timestamp
        existing_user["updatedAt"] = datetime.now().isoformat()
        
        users_db[user_id] = existing_user
        
        print(f"✅ User updated successfully: {user_id}")
        return existing_user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        total_shipments = len(shipments_db)
        total_hubs = len(hubs_db)
        
        # Count by status
        status_counts = {}
        total_revenue = 0
        
        for shipment in shipments_db.values():
            status = shipment.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_revenue += shipment.get("cost", 0)
        
        return {
            "total_shipments": total_shipments,
            "total_hubs": total_hubs,
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

def initialize_test_data():
    """Initialize realistic hubs and drivers from the same data as realistic generator"""
    if not hubs_db:  # Only add if no hubs exist
        current_time = datetime.now().isoformat()
        
        # Realistic hub data (same as generate_realistic_data.py)
        realistic_hubs_data = [
            {"name": "Mumbai Central Hub", "city": "Mumbai", "state": "Maharashtra", "code": "MUM-01", "pincode": "400001"},
            {"name": "Delhi North Hub", "city": "Delhi", "state": "Delhi", "code": "DEL-01", "pincode": "110001"},
            {"name": "Bangalore Tech Hub", "city": "Bangalore", "state": "Karnataka", "code": "BLR-01", "pincode": "560001"},
            {"name": "Chennai Port Hub", "city": "Chennai", "state": "Tamil Nadu", "code": "CHE-01", "pincode": "600001"},
            {"name": "Hyderabad Central", "city": "Hyderabad", "state": "Telangana", "code": "HYD-01", "pincode": "500001"},
            {"name": "Kolkata East Hub", "city": "Kolkata", "state": "West Bengal", "code": "KOL-01", "pincode": "700001"},
            {"name": "Pune West Hub", "city": "Pune", "state": "Maharashtra", "code": "PUN-01", "pincode": "411001"},
            {"name": "Ahmedabad Industrial Hub", "city": "Ahmedabad", "state": "Gujarat", "code": "AHM-01", "pincode": "380001"},
            {"name": "Jaipur Pink Hub", "city": "Jaipur", "state": "Rajasthan", "code": "JAI-01", "pincode": "302001"}
        ]
        
        test_hubs = []
        for i, hub_data in enumerate(realistic_hubs_data, 1):
            hub_id = f"HUB{str(i).zfill(3)}"
            test_hubs.append({
                "id": hub_id,
                "name": hub_data["name"],
                "code": hub_data["code"],
                "address": f"Industrial Area, {hub_data['city']}",
                "city": hub_data["city"],
                "state": hub_data["state"],
                "pincode": hub_data["pincode"],
                "phone": f"+91-{random.randint(70,99)}-{random.randint(10000000,99999999)}",
                "manager": f"Manager {chr(65+i)}",
                "capacity": random.randint(3000, 8000),
                "currentLoad": random.randint(1500, 4500),
                "status": "active",
                "createdAt": current_time,
                "updatedAt": current_time
            })
        
        for hub in test_hubs:
            hubs_db[hub["id"]] = hub
        
        print(f"✅ Initialized {len(test_hubs)} test hubs")
    
    # Initialize realistic drivers
    if not users_db:
        # Indian driver names for realistic data
        driver_names = [
            "Rajesh Kumar", "Sneha Reddy", "Amit Singh", "Priya Sharma", "Vikram Patel",
            "Suresh Gupta", "Anita Joshi", "Manoj Verma", "Kavita Nair", "Ravi Mehta",
            "Sanjay Yadav", "Pooja Agarwal", "Deepak Sharma", "Sunita Mishra", "Ashok Pandey",
            "Rekha Bansal", "Vinod Tiwari", "Meera Saxena", "Rohit Jain", "Seema Malhotra",
            "Ajay Chauhan", "Nisha Kapoor", "Ramesh Sinha", "Geeta Rao", "Mukesh Thakur"
        ]
        
        test_users = []
        for i, name in enumerate(driver_names, 1):
            user_id = f"USR{str(i).zfill(3)}"
            email = f"{name.lower().replace(' ', '.')}@bluecart.com"
            phone = f"+91-{random.randint(70,99)}{random.randint(100,999)}-{random.randint(10000,99999)}"
            
            test_users.append({
                "id": user_id,
                "name": name,
                "email": email,
                "phone": phone,
                "role": "driver",
                "status": "active",
                "createdAt": current_time,
                "updatedAt": current_time
            })
        
        for user in test_users:
            users_db[user["id"]] = user
            
        print(f"✅ Initialized {len(test_users)} test users/drivers")
    
    # Initialize some test shipments
    if not shipments_db:
        test_shipments = [
            {
                "id": "SH001",
                "trackingNumber": "BC2024010001",
                "senderName": "Tech Solutions Pvt Ltd",
                "senderPhone": "+91-22-98765432",
                "recipientName": "Global Electronics",
                "recipientPhone": "+91-80-87654321", 
                "pickupAddress": "Mumbai, Maharashtra",
                "deliveryAddress": "Bangalore, Karnataka",
                "weight": 2.5,
                "serviceType": "express",
                "status": "pending",
                "estimatedDelivery": current_time,
                "createdAt": current_time,
                "updatedAt": current_time
            },
            {
                "id": "SH002", 
                "trackingNumber": "BC2024010002",
                "senderName": "Fashion Hub",
                "senderPhone": "+91-11-98765433",
                "recipientName": "Style Store",
                "recipientPhone": "+91-22-87654322",
                "pickupAddress": "Delhi, Delhi", 
                "deliveryAddress": "Mumbai, Maharashtra",
                "weight": 1.8,
                "serviceType": "standard",
                "status": "pending",
                "estimatedDelivery": current_time,
                "createdAt": current_time,
                "updatedAt": current_time
            },
            {
                "id": "SH003",
                "trackingNumber": "BC2024010003", 
                "senderName": "Book Palace",
                "senderPhone": "+91-80-98765434",
                "recipientName": "Knowledge Center",
                "recipientPhone": "+91-11-87654323",
                "pickupAddress": "Bangalore, Karnataka",
                "deliveryAddress": "Delhi, Delhi",
                "weight": 3.2,
                "serviceType": "express",
                "status": "pending", 
                "estimatedDelivery": current_time,
                "createdAt": current_time,
                "updatedAt": current_time
            }
        ]
        
        for shipment in test_shipments:
            shipments_db[shipment["id"]] = shipment
            
        print(f"✅ Initialized {len(test_shipments)} test shipments")

if __name__ == "__main__":
    print("🚀 Starting BlueCart ERP FastAPI Backend...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    
    # Initialize test data
    initialize_test_data()
    
    # Get port from environment variable (for Render deployment) or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )