from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from pydantic import BaseModel, Field
import random
import string
import bcrypt

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
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (for development/testing)
shipments_db: Dict[str, Dict] = {}
hubs_db: Dict[str, Dict] = {}
users_db: Dict[str, Dict] = {}

# Password Hashing Helper Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Initialize with sample data
def initialize_sample_data():
    """Populate database with sample hubs and shipments"""
    
    # Sample Users with credentials
    sample_users = [
        {
            "id": "USR001",
            "name": "Admin User",
            "email": "admin@bluecart.com",
            "password": "admin123",  # In production, this should be hashed
            "phone": "+91 98765 99999",
            "role": "admin",
            "status": "active",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        },
        {
            "id": "USR002",
            "name": "Rajesh Kumar",
            "email": "rajesh@bluecart.com",
            "password": "manager123",
            "phone": "+91 98765 88888",
            "role": "hub_manager",
            "hubId": "HUB001",
            "status": "active",
            "createdAt": "2024-01-02T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z"
        },
        {
            "id": "USR003",
            "name": "Priya Sharma",
            "email": "priya@bluecart.com",
            "password": "manager123",
            "phone": "+91 98765 77777",
            "role": "hub_manager",
            "hubId": "HUB002",
            "status": "active",
            "createdAt": "2024-01-03T00:00:00Z",
            "updatedAt": "2024-01-03T00:00:00Z"
        },
        {
            "id": "USR004",
            "name": "Amit Patel",
            "email": "amit@bluecart.com",
            "password": "driver123",
            "phone": "+91 98765 66666",
            "role": "driver",
            "status": "active",
            "createdAt": "2024-01-04T00:00:00Z",
            "updatedAt": "2024-01-04T00:00:00Z"
        },
        {
            "id": "USR005",
            "name": "Sneha Desai",
            "email": "sneha@bluecart.com",
            "password": "driver123",
            "phone": "+91 98765 55555",
            "role": "driver",
            "status": "active",
            "createdAt": "2024-01-05T00:00:00Z",
            "updatedAt": "2024-01-05T00:00:00Z"
        },
        {
            "id": "USR006",
            "name": "Operations Manager",
            "email": "ops@bluecart.com",
            "password": "ops123",
            "phone": "+91 98765 44444",
            "role": "operations",
            "status": "active",
            "createdAt": "2024-01-06T00:00:00Z",
            "updatedAt": "2024-01-06T00:00:00Z"
        }
    ]
    
    # Hash passwords before storing
    for user in sample_users:
        plain_password = user["password"]
        user["password"] = hash_password(plain_password)
        users_db[user["id"]] = user
        print(f"✅ Created user: {user['email']} (password encrypted)")
    
    # Sample Hubs
    sample_hubs = [
        {
            "id": "HUB001",
            "name": "Mumbai Central Hub",
            "code": "MUM-C",
            "address": "123 Logistics Park, Andheri",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400058",
            "phone": "+91 22 12345678",
            "manager": "Rajesh Kumar",
            "capacity": 5000,
            "currentLoad": 3200,
            "status": "active",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        },
        {
            "id": "HUB002",
            "name": "Delhi North Hub",
            "code": "DEL-N",
            "address": "456 Industrial Area, Sector 18",
            "city": "New Delhi",
            "state": "Delhi",
            "pincode": "110018",
            "phone": "+91 11 98765432",
            "manager": "Priya Sharma",
            "capacity": 4500,
            "currentLoad": 2800,
            "status": "active",
            "createdAt": "2024-01-02T00:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        },
        {
            "id": "HUB003",
            "name": "Bangalore Tech Hub",
            "code": "BLR-T",
            "address": "789 Tech Park, Whitefield",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560066",
            "phone": "+91 80 55667788",
            "manager": "Amit Patel",
            "capacity": 3500,
            "currentLoad": 1500,
            "status": "active",
            "createdAt": "2024-01-03T00:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        },
        {
            "id": "HUB004",
            "name": "Pune West Hub",
            "code": "PUN-W",
            "address": "321 Distribution Center, Hinjewadi",
            "city": "Pune",
            "state": "Maharashtra",
            "pincode": "411057",
            "phone": "+91 20 44556677",
            "manager": "Sneha Desai",
            "capacity": 3000,
            "currentLoad": 2400,
            "status": "active",
            "createdAt": "2024-01-04T00:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        },
        {
            "id": "HUB005",
            "name": "Chennai South Hub",
            "code": "CHE-S",
            "address": "555 Port Road, Guindy",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600032",
            "phone": "+91 44 33445566",
            "manager": "Vijay Krishnan",
            "capacity": 4000,
            "currentLoad": 3500,
            "status": "maintenance",
            "createdAt": "2024-01-05T00:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
    ]
    
    for hub in sample_hubs:
        hubs_db[hub["id"]] = hub
    
    # Sample Shipments
    sample_shipments = [
        {
            "id": "SHP001",
            "trackingNumber": "BC2024010001",
            "senderName": "Tech Solutions Pvt Ltd",
            "senderPhone": "+91 98765 11111",
            "senderAddress": "123 Business Park, Andheri, Mumbai, Maharashtra, 400058",
            "receiverName": "Rahul Verma",
            "receiverPhone": "+91 98765 22222",
            "receiverAddress": "456 Residential Complex, Sector 21, New Delhi, Delhi, 110021",
            "packageDetails": "Electronic Components",
            "weight": 2.5,
            "dimensions": {"length": 30, "width": 20, "height": 15},
            "serviceType": "express",
            "status": "in-transit",
            "pickupDate": "2024-01-15T14:30:00Z",
            "estimatedDelivery": "2024-01-17T18:00:00Z",
            "actualDelivery": None,
            "route": "HUB001 -> HUB002",
            "hubId": "HUB002",
            "events": [
                {
                    "status": "Booked",
                    "location": "Mumbai",
                    "timestamp": "2024-01-15T09:00:00Z",
                    "description": "Shipment booked online"
                },
                {
                    "status": "Picked Up",
                    "location": "Mumbai Central Hub",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "description": "Package picked up from sender"
                },
                {
                    "status": "In Transit",
                    "location": "Delhi North Hub",
                    "timestamp": "2024-01-16T08:00:00Z",
                    "description": "Arrived at destination hub"
                }
            ],
            "cost": 295.0,
            "createdAt": "2024-01-15T09:00:00Z",
            "updatedAt": "2024-01-16T08:00:00Z"
        },
        {
            "id": "SHP002",
            "trackingNumber": "BC2024010002",
            "senderName": "Fashion Hub",
            "senderPhone": "+91 98765 33333",
            "senderAddress": "789 Mall Road, Bangalore, Karnataka, 560001",
            "receiverName": "Priya Nair",
            "receiverPhone": "+91 98765 44444",
            "receiverAddress": "321 Lake View Apartments, Mumbai, Maharashtra, 400050",
            "packageDetails": "Clothing Items",
            "weight": 1.2,
            "dimensions": {"length": 40, "width": 30, "height": 10},
            "serviceType": "standard",
            "status": "out-for-delivery",
            "pickupDate": "2024-01-14T15:00:00Z",
            "estimatedDelivery": "2024-01-16T18:00:00Z",
            "actualDelivery": None,
            "route": "HUB003 -> HUB001",
            "hubId": "HUB001",
            "events": [
                {
                    "status": "Booked",
                    "location": "Bangalore",
                    "timestamp": "2024-01-14T10:00:00Z",
                    "description": "Shipment created"
                },
                {
                    "status": "Picked Up",
                    "location": "Bangalore Tech Hub",
                    "timestamp": "2024-01-14T15:00:00Z",
                    "description": "Collected from sender"
                },
                {
                    "status": "In Transit",
                    "location": "Mumbai Central Hub",
                    "timestamp": "2024-01-15T20:00:00Z",
                    "description": "Reached destination city"
                },
                {
                    "status": "Out for Delivery",
                    "location": "Mumbai",
                    "timestamp": "2024-01-16T09:00:00Z",
                    "description": "Out for delivery"
                }
            ],
            "cost": 212.0,
            "createdAt": "2024-01-14T10:00:00Z",
            "updatedAt": "2024-01-16T09:00:00Z"
        },
        {
            "id": "SHP003",
            "trackingNumber": "BC2024010003",
            "senderName": "Medical Supplies Co",
            "senderPhone": "+91 98765 55555",
            "senderAddress": "555 Health Street, Pune, Maharashtra, 411001",
            "receiverName": "City Hospital",
            "receiverPhone": "+91 98765 66666",
            "receiverAddress": "777 Hospital Road, Mumbai, Maharashtra, 400012",
            "packageDetails": "Medical Equipment",
            "weight": 5.0,
            "dimensions": {"length": 50, "width": 40, "height": 30},
            "serviceType": "urgent",
            "status": "delivered",
            "pickupDate": "2024-01-13T10:00:00Z",
            "estimatedDelivery": "2024-01-14T12:00:00Z",
            "actualDelivery": "2024-01-14T11:30:00Z",
            "route": "HUB004 -> HUB001",
            "hubId": "HUB001",
            "events": [
                {
                    "status": "Booked",
                    "location": "Pune",
                    "timestamp": "2024-01-13T08:00:00Z",
                    "description": "Urgent shipment booked"
                },
                {
                    "status": "Picked Up",
                    "location": "Pune West Hub",
                    "timestamp": "2024-01-13T10:00:00Z",
                    "description": "Priority pickup completed"
                },
                {
                    "status": "In Transit",
                    "location": "Mumbai Central Hub",
                    "timestamp": "2024-01-13T18:00:00Z",
                    "description": "Express transit"
                },
                {
                    "status": "Out for Delivery",
                    "location": "Mumbai",
                    "timestamp": "2024-01-14T08:00:00Z",
                    "description": "Assigned to delivery agent"
                },
                {
                    "status": "Delivered",
                    "location": "City Hospital, Mumbai",
                    "timestamp": "2024-01-14T11:30:00Z",
                    "description": "Successfully delivered and signed"
                }
            ],
            "cost": 531.0,
            "createdAt": "2024-01-13T08:00:00Z",
            "updatedAt": "2024-01-14T11:30:00Z"
        }
    ]
    
    for shipment in sample_shipments:
        shipments_db[shipment["id"]] = shipment
    
    print(f"✅ Initialized with {len(users_db)} users, {len(hubs_db)} hubs and {len(shipments_db)} shipments")

# Initialize sample data on startup
initialize_sample_data()


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

# User Models
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    status: str
    hubId: Optional[str] = None
    createdAt: str
    updatedAt: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    message: str
    timestamp: datetime

# Helper functions
def generate_id():
    return f"SH{int(datetime.now().timestamp())}"

def generate_hub_id():
    return f"HUB{int(datetime.now().timestamp())}"

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

# Authentication Endpoints
@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    """Authenticate user and return user data"""
    try:
        # Find user by email
        user = None
        for u in users_db.values():
            if u["email"].lower() == credentials.email.lower():
                user = u
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password using bcrypt
        if not verify_password(credentials.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if user.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Return user data (without password)
        user_response = {k: v for k, v in user.items() if k != "password"}
        
        print(f"✅ User logged in: {user['email']} ({user['role']})")
        return {
            "success": True,
            "user": user_response,
            "message": "Login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# User Management Endpoints
@app.get("/api/users")
async def get_users(role: Optional[str] = None):
    """Get all users, optionally filtered by role"""
    try:
        all_users = list(users_db.values())
        
        # Filter by role if provided
        if role:
            all_users = [u for u in all_users if u["role"] == role]
        
        # Remove passwords from response
        users_response = [
            {k: v for k, v in user.items() if k != "password"}
            for user in all_users
        ]
        
        return {
            "users": users_response,
            "total": len(users_response)
        }
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    try:
        user = users_db.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != "password"}
        return UserResponse(**user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, updates: UserUpdate):
    """Update user profile information and password"""
    try:
        user = users_db.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update only provided fields
        update_data = updates.dict(exclude_unset=True)
        
        # Hash password if it's being updated
        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])
            print(f"🔐 Password encrypted for user: {user_id}")
        
        for key, value in update_data.items():
            if value is not None:
                user[key] = value
        
        user["updatedAt"] = datetime.now().isoformat()
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != "password"}
        
        print(f"✅ Updated user: {user_id} - Changes: {list(update_data.keys())}")
        return {
            "success": True,
            "user": user_response,
            "message": "User updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

# Shipment Management Endpoints
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

if __name__ == "__main__":
    print("🚀 Starting BlueCart ERP FastAPI Backend...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for stability
        log_level="info"
    )