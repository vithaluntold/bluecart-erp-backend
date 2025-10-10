from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://localhost:3005,https://bluecart-erp-frontend.onrender.com").split(",")

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
sessions_db: Dict[str, Dict] = {}

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
    senderName: Optional[str] = None
    senderPhone: Optional[str] = None
    senderAddress: Optional[str] = None
    receiverName: Optional[str] = None
    receiverPhone: Optional[str] = None
    receiverAddress: Optional[str] = None
    packageDetails: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    serviceType: Optional[str] = "standard"
    status: str = "pending"
    pickupDate: Optional[str] = None
    estimatedDelivery: Optional[str] = None
    actualDelivery: Optional[str] = None
    route: Optional[str] = None
    hubId: Optional[str] = None
    events: Optional[List[Dict[str, Any]]] = []
    cost: Optional[float] = None
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

class UserSession(BaseModel):
    id: str
    user_id: str
    device: str
    ip_address: str
    location: str
    last_activity: str
    created_at: str
    is_current: bool

class SessionResponse(BaseModel):
    sessions: List[UserSession]

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

def generate_session_id():
    return f"SES{int(datetime.now().timestamp())}"

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

@app.put("/api/users/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: dict):
    """Update user notification and other preferences"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for preferences update: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user preferences (store in a separate preferences dict or in user record)
        # For now, we'll store preferences in the user record
        current_time = datetime.now().isoformat()
        
        if "preferences" not in users_db[user_id]:
            users_db[user_id]["preferences"] = {}
            
        users_db[user_id]["preferences"].update(preferences)
        users_db[user_id]["updatedAt"] = current_time
        
        print(f"✅ User preferences updated successfully: {user_id}")
        return {"message": "Preferences updated successfully", "preferences": users_db[user_id]["preferences"]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

@app.get("/api/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user notification and other preferences"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for preferences: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        preferences = users_db[user_id].get("preferences", {})
        return {"preferences": preferences}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )

@app.post("/api/users/{user_id}/2fa/setup")
async def setup_2fa(user_id: str):
    """Generate 2FA secret and QR code for user"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for 2FA setup: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate a secret for the user (in production, use proper TOTP library)
        # For demo purposes, we'll generate a simple secret
        import secrets
        import string
        
        secret = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32))
        
        # Store the secret temporarily (in production, store encrypted)
        if "security" not in users_db[user_id]:
            users_db[user_id]["security"] = {}
        
        users_db[user_id]["security"]["totp_secret"] = secret
        users_db[user_id]["security"]["totp_enabled"] = False  # Not enabled until verified
        
        # Create QR code data (format for authenticator apps)
        app_name = "BlueCart ERP"
        user_email = users_db[user_id].get("email", "user@bluecart.com")
        qr_data = f"otpauth://totp/{app_name}:{user_email}?secret={secret}&issuer={app_name}"
        
        print(f"✅ 2FA setup initialized for user: {user_id}")
        return {
            "secret": secret,
            "qr_data": qr_data,
            "manual_entry_code": f"{secret[:4]}-{secret[4:8]}-{secret[8:12]}-{secret[12:16]}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error setting up 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}"
        )

@app.post("/api/users/{user_id}/2fa/verify")
async def verify_2fa(user_id: str, verification_data: dict):
    """Verify TOTP code and enable 2FA"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for 2FA verification: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        code = verification_data.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Verification code required")
        
        # In production, verify the TOTP code against the secret
        # For demo purposes, we'll accept any 6-digit code
        if len(code) == 6 and code.isdigit():
            users_db[user_id]["security"]["totp_enabled"] = True
            
            print(f"✅ 2FA enabled for user: {user_id}")
            return {"message": "2FA enabled successfully", "enabled": True}
        else:
            raise HTTPException(status_code=400, detail="Invalid verification code")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error verifying 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}"
        )

@app.get("/api/users/{user_id}/2fa/status")
async def get_2fa_status(user_id: str):
    """Get 2FA status for user"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for 2FA status: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        security = users_db[user_id].get("security", {})
        enabled = security.get("totp_enabled", False)
        
        return {"enabled": enabled}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting 2FA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get 2FA status: {str(e)}"
        )

# Session Management Endpoints
@app.get("/api/users/{user_id}/sessions", response_model=SessionResponse)
async def get_user_sessions(user_id: str):
    """Get all sessions for a user"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for sessions: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user sessions from sessions_db
        user_sessions = []
        for session_id, session_data in sessions_db.items():
            if session_data.get("user_id") == user_id:
                user_sessions.append(UserSession(**session_data))
        
        return SessionResponse(sessions=user_sessions)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user sessions: {str(e)}"
        )

@app.post("/api/users/{user_id}/sessions/{session_id}/revoke")
async def revoke_session(user_id: str, session_id: str):
    """Revoke a specific session"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for session revoke: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        if session_id not in sessions_db:
            print(f"❌ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify session belongs to user
        session_data = sessions_db[session_id]
        if session_data.get("user_id") != user_id:
            print(f"❌ Session {session_id} does not belong to user {user_id}")
            raise HTTPException(status_code=403, detail="Session does not belong to user")
        
        # Remove session
        del sessions_db[session_id]
        print(f"✅ Session revoked: {session_id}")
        
        return {"message": "Session revoked successfully", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}"
        )

@app.post("/api/users/{user_id}/sessions/revoke-all")
async def revoke_all_sessions(user_id: str):
    """Revoke all sessions for a user except current"""
    try:
        if user_id not in users_db:
            print(f"❌ User not found for session revoke all: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find and remove all non-current sessions for the user
        sessions_to_remove = []
        for session_id, session_data in sessions_db.items():
            if session_data.get("user_id") == user_id and not session_data.get("is_current", False):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del sessions_db[session_id]
        
        print(f"✅ Revoked {len(sessions_to_remove)} sessions for user {user_id}")
        
        return {
            "message": f"Revoked {len(sessions_to_remove)} sessions successfully",
            "revoked_count": len(sessions_to_remove)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error revoking all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke all sessions: {str(e)}"
        )

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get enhanced dashboard analytics data with 7-day trends"""
    try:
        total_shipments = len(shipments_db)
        total_hubs = len(hubs_db)
        total_users = len(users_db)
        
        # Count by status
        status_counts = {}
        total_revenue = 0
        
        for shipment in shipments_db.values():
            status = shipment.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_revenue += shipment.get("cost", 0)
        
        # Generate 7-day trend data
        daily_data = []
        revenue_data = []
        current_date = datetime.now()
        
        for day_offset in range(6, -1, -1):  # Last 7 days
            day_date = current_date - timedelta(days=day_offset)
            day_str = day_date.strftime("%Y-%m-%d")
            day_name = day_date.strftime("%a")
            
            # Count shipments for this day
            day_shipments = 0
            day_revenue = 0
            day_delivered = 0
            
            for shipment in shipments_db.values():
                shipment_date = shipment.get("createdAt", "")
                if shipment_date.startswith(day_str):
                    day_shipments += 1
                    day_revenue += shipment.get("cost", 0)
                    if shipment.get("status") == "delivered":
                        day_delivered += 1
            
            daily_data.append({
                "date": day_str,
                "day": day_name,
                "shipments": day_shipments,
                "delivered": day_delivered,
                "pending": day_shipments - day_delivered
            })
            
            revenue_data.append({
                "date": day_str,
                "day": day_name,
                "revenue": round(day_revenue, 2)
            })
        
        # Calculate metrics
        active_hubs = sum(1 for hub in hubs_db.values() if hub.get("status") == "active")
        driver_count = sum(1 for user in users_db.values() if user.get("role") == "driver")
        
        return {
            "total_shipments": total_shipments,
            "active_shipments": status_counts.get("in-transit", 0) + status_counts.get("picked-up", 0),
            "total_hubs": total_hubs,
            "active_hubs": active_hubs,
            "total_users": total_users,
            "driver_count": driver_count,
            "pending_shipments": status_counts.get("pending", 0),
            "in_transit_shipments": status_counts.get("in-transit", 0),
            "delivered_shipments": status_counts.get("delivered", 0),
            "failed_shipments": status_counts.get("failed", 0),
            "total_revenue": round(total_revenue, 2),
            "daily_shipments": daily_data,
            "daily_revenue": revenue_data,
            "status_distribution": [
                {"status": "Delivered", "count": status_counts.get("delivered", 0), "color": "#22c55e"},
                {"status": "In Transit", "count": status_counts.get("in-transit", 0), "color": "#8b5cf6"},
                {"status": "Pending", "count": status_counts.get("pending", 0), "color": "#f59e0b"},
                {"status": "Out for Delivery", "count": status_counts.get("out-for-delivery", 0), "color": "#f97316"},
                {"status": "Failed", "count": status_counts.get("failed", 0), "color": "#ef4444"}
            ]
        }
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )

def generate_dynamic_test_data():
    """Generate 7 days of dynamic test data for analytics and dashboard"""
    if shipments_db:  # Clear existing if any
        shipments_db.clear()
    
    # Generate shipments for the last 7 days
    statuses = ["pending", "picked-up", "in-transit", "out-for-delivery", "delivered", "failed"]
    cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune", "Ahmedabad", "Jaipur"]
    service_types = ["standard", "express", "overnight"]
    
    current_date = datetime.now()
    
    # Generate varying number of shipments per day (more recent = more shipments)
    daily_shipment_counts = [15, 18, 22, 25, 30, 35, 40]  # Last 7 days
    
    shipment_counter = 1
    for day_offset in range(6, -1, -1):  # 6 days ago to today
        day_date = current_date - timedelta(days=day_offset)
        daily_count = daily_shipment_counts[day_offset]
        
        for i in range(daily_count):
            shipment_id = f"SH{str(shipment_counter).zfill(3)}"
            tracking_number = f"BC{day_date.strftime('%Y%m%d')}{str(i+1).zfill(3)}"
            
            # Determine status based on day (older shipments more likely to be delivered)
            if day_offset >= 5:  # 5+ days old - mostly delivered
                status_weights = [0.05, 0.05, 0.1, 0.05, 0.7, 0.05]
            elif day_offset >= 3:  # 3-4 days old - mixed
                status_weights = [0.1, 0.15, 0.25, 0.2, 0.25, 0.05]
            elif day_offset >= 1:  # 1-2 days old - mostly in transit
                status_weights = [0.15, 0.25, 0.35, 0.15, 0.05, 0.05]
            else:  # Today - mostly pending/picked up
                status_weights = [0.4, 0.35, 0.15, 0.05, 0.03, 0.02]
            
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Generate realistic sender/receiver data
            sender_city = random.choice(cities)
            receiver_city = random.choice([c for c in cities if c != sender_city])
            service_type = random.choice(service_types)
            weight = round(random.uniform(0.5, 10.0), 1)
            cost = round(weight * random.uniform(80, 150) + random.uniform(50, 200), 2)
            
            # Create shipment with realistic timestamps
            created_at = (day_date + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))).isoformat()
            
            shipment = {
                "id": shipment_id,
                "trackingNumber": tracking_number,
                "senderName": f"Sender Company {shipment_counter}",
                "senderPhone": f"+91-{random.randint(70,99)}{random.randint(100,999)}-{random.randint(10000,99999)}",
                "senderAddress": f"{random.randint(100,999)} Business Park, {sender_city}",
                "receiverName": f"Receiver Corp {shipment_counter}",
                "receiverPhone": f"+91-{random.randint(70,99)}{random.randint(100,999)}-{random.randint(10000,99999)}",
                "receiverAddress": f"{random.randint(100,999)} Commercial Street, {receiver_city}",
                "packageDetails": random.choice(["Electronics", "Clothing", "Books", "Furniture", "Food Items"]),
                "weight": weight,
                "dimensions": {
                    "length": random.randint(20, 80),
                    "width": random.randint(15, 60),
                    "height": random.randint(5, 40)
                },
                "serviceType": service_type,
                "status": status,
                "pickupDate": created_at if status != "pending" else None,
                "estimatedDelivery": (day_date + timedelta(days=random.randint(1, 3))).isoformat(),
                "actualDelivery": created_at if status == "delivered" else None,
                "route": f"RT{random.randint(1000000000, 9999999999)}" if status in ["in-transit", "out-for-delivery", "delivered"] else None,
                "hubId": f"HUB{str(random.randint(1, 9)).zfill(3)}",
                "events": [
                    {
                        "id": f"EV{shipment_counter}",
                        "timestamp": created_at,
                        "status": status,
                        "location": f"{sender_city} Hub",
                        "description": f"Shipment {status.replace('-', ' ')}"
                    }
                ],
                "cost": cost,
                "createdAt": created_at,
                "updatedAt": created_at
            }
            
            shipments_db[shipment_id] = shipment
            shipment_counter += 1
    
    print(f"✅ Generated {len(shipments_db)} dynamic shipments over 7 days")

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
        
        # Add an admin user
        admin_user = {
            "id": "USR000",
            "name": "Admin User",
            "email": "admin@bluecart.com",
            "phone": "+91-98765-43210",
            "role": "admin",
            "status": "active",
            "createdAt": current_time,
            "updatedAt": current_time
        }
        test_users.append(admin_user)
        
        for user in test_users:
            users_db[user["id"]] = user
            
        print(f"✅ Initialized {len(test_users)} test users/drivers (including admin)")
    
    # Generate dynamic 7-day test data
    generate_dynamic_test_data()
    
    # Initialize some test shipments with proper schema (keeping for fallback)
    if False:  # Disabled - using dynamic data instead
        test_shipments = [
            {
                "id": "SH001",
                "trackingNumber": "BC2024010001",
                "senderName": "Tech Solutions Pvt Ltd",
                "senderPhone": "+91-22-98765432",
                "senderAddress": "123 Tech Park, Mumbai, Maharashtra 400001",
                "receiverName": "Global Electronics",
                "receiverPhone": "+91-80-87654321", 
                "receiverAddress": "456 Electronic City, Bangalore, Karnataka 560100",
                "packageDetails": "Laptop computers and accessories",
                "weight": 2.5,
                "dimensions": {"length": 40, "width": 30, "height": 10},
                "serviceType": "express",
                "status": "pending",
                "pickupDate": current_time,
                "estimatedDelivery": current_time,
                "actualDelivery": None,
                "route": None,
                "hubId": "HUB001",
                "events": [
                    {
                        "id": "EV001",
                        "timestamp": current_time,
                        "status": "pending",
                        "location": "Mumbai Hub",
                        "description": "Shipment created and pending pickup"
                    }
                ],
                "cost": 450.0,
                "createdAt": current_time,
                "updatedAt": current_time
            },
            {
                "id": "SH002", 
                "trackingNumber": "BC2024010002",
                "senderName": "Fashion Hub",
                "senderPhone": "+91-11-98765433",
                "senderAddress": "789 Fashion Street, Delhi, Delhi 110001",
                "receiverName": "Style Store",
                "receiverPhone": "+91-22-87654322",
                "receiverAddress": "321 Style Plaza, Mumbai, Maharashtra 400002",
                "packageDetails": "Designer clothing and accessories",
                "weight": 1.8,
                "dimensions": {"length": 50, "width": 40, "height": 15},
                "serviceType": "standard",
                "status": "pending",
                "pickupDate": current_time,
                "estimatedDelivery": current_time,
                "actualDelivery": None,
                "route": None,
                "hubId": "HUB002",
                "events": [
                    {
                        "id": "EV002",
                        "timestamp": current_time,
                        "status": "pending",
                        "location": "Delhi Hub",
                        "description": "Shipment created and pending pickup"
                    }
                ],
                "cost": 280.0,
                "createdAt": current_time,
                "updatedAt": current_time
            },
            {
                "id": "SH003",
                "trackingNumber": "BC2024010003", 
                "senderName": "Book Palace",
                "senderPhone": "+91-80-98765434",
                "senderAddress": "654 Book Avenue, Bangalore, Karnataka 560001",
                "receiverName": "Knowledge Center",
                "receiverPhone": "+91-11-87654323",
                "receiverAddress": "987 Learning Street, Delhi, Delhi 110002",
                "packageDetails": "Educational books and stationery",
                "weight": 3.2,
                "dimensions": {"length": 35, "width": 25, "height": 20},
                "serviceType": "express",
                "status": "in-transit",
                "pickupDate": current_time,
                "estimatedDelivery": current_time,
                "actualDelivery": None,
                "route": "RT1759918067",
                "hubId": "HUB003",
                "events": [
                    {
                        "id": "EV003",
                        "timestamp": current_time,
                        "status": "pending",
                        "location": "Bangalore Hub",
                        "description": "Shipment created and pending pickup"
                    },
                    {
                        "id": "EV004",
                        "timestamp": current_time,
                        "status": "in-transit",
                        "location": "In Transit",
                        "description": "Package picked up and in transit"
                    }
                ],
                "cost": 380.0,
                "createdAt": current_time,
                "updatedAt": current_time
            }
        ]
        
        for shipment in test_shipments:
            shipments_db[shipment["id"]] = shipment
            
        print(f"✅ Initialized {len(test_shipments)} test shipments")
    
    # Initialize test sessions for admin user
    if not sessions_db:
        current_time = datetime.now().isoformat()
        test_sessions = [
            {
                "id": "SES001",
                "user_id": "USR000",
                "device": "Chrome Browser - Windows",
                "ip_address": "192.168.1.100",
                "location": "Mumbai, India",
                "last_activity": current_time,
                "created_at": current_time,
                "is_current": True
            },
            {
                "id": "SES002", 
                "user_id": "USR000",
                "device": "Mobile App - Android",
                "ip_address": "192.168.1.101",
                "location": "Mumbai, India",
                "last_activity": (datetime.now() - timedelta(hours=2)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "is_current": False
            },
            {
                "id": "SES003",
                "user_id": "USR000", 
                "device": "Safari Browser - MacOS",
                "ip_address": "192.168.1.102",
                "location": "Delhi, India",
                "last_activity": (datetime.now() - timedelta(hours=8)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "is_current": False
            }
        ]
        
        for session in test_sessions:
            sessions_db[session["id"]] = session
            
        print(f"✅ Initialized {len(test_sessions)} test sessions")

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