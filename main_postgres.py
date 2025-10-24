"""
BlueCart ERP Backend - PostgreSQL Version for Render Deployment
Handles authentication with bcrypt password encryption
"""
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
import uvicorn
import bcrypt
import json
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# Environment Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp')
CORS_ORIGINS = json.loads(os.getenv('CORS_ORIGINS', '["http://localhost:3000","https://*.onrender.com"]'))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
PROJECT_NAME = os.getenv('PROJECT_NAME', 'BlueCart ERP Backend')
VERSION = os.getenv('VERSION', '2.0.0')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Initialize connection pool
db_pool = None

def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL
        )
        print("✅ Database connection pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database pool: {e}")
        raise

def get_db():
    """Get database connection from pool"""
    if db_pool is None:
        init_db_pool()
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

# Password Hashing Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Initialize FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description="Logistics and shipment management system with PostgreSQL",
    version=VERSION,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class LoginCredentials(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class Hub(BaseModel):
    id: str
    name: str
    code: str
    address: str
    city: str
    state: str
    pincode: str
    phone: str
    capacity: int
    current_load: int = 0
    status: str = "active"
    manager: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Shipment(BaseModel):
    id: int
    tracking_number: str
    origin_hub: str
    destination_hub: str
    weight: float
    price: float
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup():
    """Initialize database connection on startup"""
    init_db_pool()
    
    # Create system_settings table if it doesn't exist
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        # Create system_settings table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            setting_type VARCHAR(20) DEFAULT 'string',
            category VARCHAR(50) NOT NULL,
            description TEXT,
            is_editable BOOLEAN DEFAULT TRUE,
            is_sensitive BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cur.execute(create_table_sql)
        
        # Insert default settings if table is empty
        cur.execute("SELECT COUNT(*) FROM system_settings")
        count = cur.fetchone()[0]
        
        if count == 0:
            default_settings = [
                ('timezone', 'UTC', 'string', 'system', 'Default system timezone'),
                ('language', 'en', 'string', 'system', 'Default system language'),
                ('maintenance_mode', 'false', 'boolean', 'system', 'System maintenance mode'),
                ('email_notifications', 'true', 'boolean', 'notifications', 'Enable email notifications'),
                ('sms_notifications', 'true', 'boolean', 'notifications', 'Enable SMS notifications'),
                ('push_notifications', 'false', 'boolean', 'notifications', 'Enable push notifications'),
                ('delivery_updates', 'true', 'boolean', 'notifications', 'Enable delivery update notifications'),
                ('hub_updates', 'true', 'boolean', 'notifications', 'Enable hub update notifications'),
            ]
            
            insert_sql = """
            INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cur.executemany(insert_sql, default_settings)
            print(f"✅ Inserted {len(default_settings)} default settings")
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        print("✅ system_settings table ready")
        
    except Exception as e:
        print(f"❌ Error setting up system_settings table: {e}")
        if conn:
            conn.rollback()
            db_pool.putconn(conn)
    
    print("🚀 BlueCart ERP Backend started")

@app.on_event("shutdown")
async def shutdown():
    """Close database connections on shutdown"""
    if db_pool:
        db_pool.closeall()
    print("👋 BlueCart ERP Backend stopped")

# ==================== HEALTH CHECK ====================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Render"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        db_pool.putconn(conn)
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "BlueCart ERP API",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "deployment": "Render",
        "docs": "/docs"
    }

# ==================== AUTHENTICATION ====================

@app.post("/api/auth/login", tags=["Authentication"])
async def login(credentials: LoginCredentials):
    """Login endpoint with bcrypt password verification"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user by email
        cur.execute(
            "SELECT id, username, email, password_hash, full_name, phone, role, created_at FROM users WHERE email = %s",
            (credentials.email,)
        )
        user = cur.fetchone()
        
        cur.close()
        db_pool.putconn(conn)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Return user data (without password)
        return {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "phone": user['phone'],
            "role": user['role'],
            "created_at": user['created_at'].isoformat() if user['created_at'] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

# ==================== USER MANAGEMENT ====================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"

@app.post("/api/users", response_model=UserResponse, tags=["Users"])
async def create_user(user: UserCreate):
    """Create a new user with hashed password"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Insert new user
        cur.execute("""
            INSERT INTO users 
            (username, email, password_hash, full_name, phone, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id, username, email, full_name, phone, role, created_at
        """, (
            user.username,
            user.email,
            hashed_password,
            user.full_name,
            user.phone,
            user.role
        ))
        
        created_user = cur.fetchone()
        conn.commit()
        
        cur.close()
        db_pool.putconn(conn)
        
        return created_user
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
async def get_users():
    """Get all users (without passwords)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, username, email, full_name, phone, role, created_at 
            FROM users 
            ORDER BY id
        """)
        users = cur.fetchall()
        
        cur.close()
        db_pool.putconn(conn)
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int):
    """Get user by ID (without password)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, username, email, full_name, phone, role, created_at 
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        
        cur.close()
        db_pool.putconn(conn)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )

@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(user_id: int, update_data: UserUpdate):
    """Update user information (including password)"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle password encryption separately
        if 'password' in update_dict:
            hashed_password = hash_password(update_dict['password'])
            update_fields.append("password = %s")
            values.append(hashed_password)
            del update_dict['password']
        
        # Add other fields
        for key, value in update_dict.items():
            update_fields.append(f"{key} = %s")
            values.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Add user_id to values
        values.append(user_id)
        
        # Execute update
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)} 
            WHERE id = %s 
            RETURNING id, username, email, full_name, phone, role, created_at
        """
        
        cur.execute(query, values)
        updated_user = cur.fetchone()
        
        if not updated_user:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@app.delete("/api/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int):
    """Delete a user"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": f"User {user_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )

# ==================== HUBS ====================

class HubCreate(BaseModel):
    name: str
    city: str
    state: str
    country: str = "India"
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "active"

@app.post("/api/hubs", tags=["Hubs"])
async def create_hub(hub: HubCreate):
    """Create a new hub"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            INSERT INTO hubs 
            (name, city, state, country, postal_code, latitude, longitude, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING *
        """, (
            hub.name,
            hub.city,
            hub.state,
            hub.country,
            hub.postal_code,
            hub.latitude,
            hub.longitude,
            hub.status
        ))
        
        created_hub = cur.fetchone()
        conn.commit()
        
        cur.close()
        db_pool.putconn(conn)
        
        return created_hub
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating hub: {str(e)}"
        )

@app.get("/api/hubs", response_model=List[Dict[str, Any]], tags=["Hubs"])
async def get_hubs():
    """Get all hubs"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM hubs ORDER BY created_at DESC")
        hubs = cur.fetchall()
        
        cur.close()
        db_pool.putconn(conn)
        
        return hubs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching hubs: {str(e)}"
        )

@app.get("/api/hubs/{hub_id}", tags=["Hubs"])
async def get_hub(hub_id: int):
    """Get hub by ID"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM hubs WHERE id = %s", (hub_id,))
        hub = cur.fetchone()
        
        cur.close()
        db_pool.putconn(conn)
        
        if not hub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hub {hub_id} not found"
            )
        
        return hub
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching hub: {str(e)}"
        )

@app.put("/api/hubs/{hub_id}", tags=["Hubs"])
async def update_hub(hub_id: int, updates: Dict[str, Any]):
    """Update hub details"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        allowed_fields = ['name', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude', 'status']
        
        for key, value in updates.items():
            if key in allowed_fields:
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        values.append(hub_id)
        
        query = f"""
            UPDATE hubs 
            SET {', '.join(update_fields)} 
            WHERE id = %s 
            RETURNING *
        """
        
        cur.execute(query, values)
        updated_hub = cur.fetchone()
        
        if not updated_hub:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hub {hub_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return updated_hub
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating hub: {str(e)}"
        )

@app.delete("/api/hubs/{hub_id}", tags=["Hubs"])
async def delete_hub(hub_id: int):
    """Delete a hub"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM hubs WHERE id = %s RETURNING id", (hub_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hub {hub_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": f"Hub {hub_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting hub: {str(e)}"
        )

# ==================== SHIPMENTS ====================

class ShipmentCreate(BaseModel):
    # Sender Information
    senderName: Optional[str] = None
    senderPhone: Optional[str] = None
    senderAddress: Optional[str] = None
    senderCity: Optional[str] = None
    senderState: Optional[str] = None
    senderPincode: Optional[str] = None
    
    # Receiver Information
    receiverName: Optional[str] = None
    receiverPhone: Optional[str] = None
    receiverAddress: Optional[str] = None
    receiverCity: Optional[str] = None
    receiverState: Optional[str] = None
    receiverPincode: Optional[str] = None
    
    # Package Details
    packageType: Optional[str] = None
    packageDetails: Optional[str] = None
    packageWeight: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    
    # Service and Pricing
    serviceType: str = "standard"
    priority: str = "normal"
    cost: Optional[float] = None
    paymentMethod: Optional[str] = "Cash on Delivery"
    paymentStatus: Optional[str] = "Pending"
    
    # Hub Information
    current_hub_id: Optional[int] = None
    destination_hub_id: Optional[int] = None
    route_id: Optional[int] = None
    
    # Legacy fields for backward compatibility
    cargo_type: Optional[str] = None
    weight_unit: str = "kg"

@app.post("/api/shipments", tags=["Shipments"])
async def create_shipment(shipment: ShipmentCreate):
    """Create a new shipment with comprehensive validation"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Validate and extract weight
        weight = shipment.weight or shipment.packageWeight
        if not weight or weight <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be greater than 0"
            )
        
        # Validate and extract cargo type
        cargo_type = (
            shipment.cargo_type or 
            shipment.packageType or 
            shipment.packageDetails or 
            "General Cargo"
        )
        
        if not cargo_type or len(cargo_type.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Package description is required"
            )
        
        # Validate hubs if provided
        if shipment.current_hub_id:
            cur.execute("SELECT id FROM hubs WHERE id = %s", (shipment.current_hub_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Current hub {shipment.current_hub_id} does not exist"
                )
        
        if shipment.destination_hub_id:
            cur.execute("SELECT id FROM hubs WHERE id = %s", (shipment.destination_hub_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Destination hub {shipment.destination_hub_id} does not exist"
                )
        
        # Validate route if provided
        if shipment.route_id:
            cur.execute("SELECT id FROM routes WHERE id = %s", (shipment.route_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Route {shipment.route_id} does not exist"
                )
        
        # Generate tracking number
        import random
        import string
        tracking_number = f"SHIP{''.join(random.choices(string.digits, k=8))}"
        
        # Ensure unique tracking number
        max_attempts = 10
        for _ in range(max_attempts):
            cur.execute("SELECT id FROM shipments WHERE tracking_number = %s", (tracking_number,))
            if not cur.fetchone():
                break
            tracking_number = f"SHIP{''.join(random.choices(string.digits, k=8))}"
        
        # Map frontend serviceType to backend priority
        priority_map = {
            'overnight': 'urgent',
            'express': 'high',
            'standard': 'normal',
            'economy': 'low'
        }
        priority = priority_map.get(shipment.serviceType, shipment.priority or 'normal')
        
        # Validate priority
        valid_priorities = ['urgent', 'high', 'normal', 'medium', 'low']
        if priority not in valid_priorities:
            priority = 'normal'
        
        # Prepare additional data as JSON for future extension
        additional_data = {
            'senderName': shipment.senderName,
            'senderPhone': shipment.senderPhone,
            'senderAddress': shipment.senderAddress,
            'senderCity': shipment.senderCity,
            'senderState': shipment.senderState,
            'senderPincode': shipment.senderPincode,
            'receiverName': shipment.receiverName,
            'receiverPhone': shipment.receiverPhone,
            'receiverAddress': shipment.receiverAddress,
            'receiverCity': shipment.receiverCity,
            'receiverState': shipment.receiverState,
            'receiverPincode': shipment.receiverPincode,
            'packageType': shipment.packageType,
            'dimensions': shipment.dimensions,
            'serviceType': shipment.serviceType,
            'cost': shipment.cost,
            'paymentMethod': getattr(shipment, 'paymentMethod', 'Cash on Delivery'),
            'paymentStatus': getattr(shipment, 'paymentStatus', 'Pending'),
        }
        
        # Add additional_data column if it doesn't exist
        try:
            cur.execute("ALTER TABLE shipments ADD COLUMN IF NOT EXISTS additional_data JSONB")
            conn.commit()
        except Exception:
            conn.rollback()  # If column already exists or other error, continue
        
        has_additional_data_column = True  # Assume it exists now
        
        if has_additional_data_column:
            # Insert with additional_data column
            cur.execute("""
                INSERT INTO shipments 
                (tracking_number, cargo_type, weight, weight_unit, priority, status, 
                 current_hub_id, destination_hub_id, route_id, additional_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING *
            """, (
                tracking_number,
                cargo_type[:255],  # Limit to 255 chars
                weight,
                shipment.weight_unit or 'kg',
                priority,
                'pending',
                shipment.current_hub_id,
                shipment.destination_hub_id,
                shipment.route_id,
                json.dumps(additional_data)
            ))
        else:
            # Insert basic shipment without additional_data
            cur.execute("""
                INSERT INTO shipments 
                (tracking_number, cargo_type, weight, weight_unit, priority, status, 
                 current_hub_id, destination_hub_id, route_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING *
            """, (
                tracking_number,
                cargo_type[:255],  # Limit to 255 chars
                weight,
                shipment.weight_unit or 'kg',
                priority,
                'pending',
                shipment.current_hub_id,
                shipment.destination_hub_id,
                shipment.route_id
            ))
        
        created_shipment = cur.fetchone()
        
        if not created_shipment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create shipment in database"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        print(f"✅ Shipment created: {tracking_number}")
        return created_shipment
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error creating shipment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/shipments", response_model=List[Dict[str, Any]], tags=["Shipments"])
async def get_shipments(
    status: Optional[str] = None,
    limit: int = 100
):
    """Get all shipments with optional status filter"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if status:
            cur.execute(
                "SELECT * FROM shipments WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                (status, limit)
            )
        else:
            cur.execute(
                "SELECT * FROM shipments ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
        
        shipments = cur.fetchall()
        
        cur.close()
        db_pool.putconn(conn)
        
        # Process each shipment to merge additional_data if present
        processed_shipments = []
        for shipment in shipments:
            shipment_dict = dict(shipment)
            if 'additional_data' in shipment_dict and shipment_dict['additional_data'] is not None:
                try:
                    # additional_data is already a dict from JSONB, no need to parse JSON
                    additional_data = shipment_dict['additional_data']
                    if isinstance(additional_data, str):
                        # If it's a string, parse it
                        additional_data = json.loads(additional_data)
                    
                    # Merge additional data into the main object if it's a dict
                    if isinstance(additional_data, dict):
                        shipment_dict.update(additional_data)
                        # Remove the raw additional_data field
                        del shipment_dict['additional_data']
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, just return basic data
                    pass
            processed_shipments.append(shipment_dict)
        
        return processed_shipments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shipments: {str(e)}"
        )

@app.get("/api/shipments/{shipment_id}", tags=["Shipments"])
async def get_shipment(shipment_id: int):
    """Get shipment by ID"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM shipments WHERE id = %s", (shipment_id,))
        shipment = cur.fetchone()
        
        cur.close()
        db_pool.putconn(conn)
        
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )
        
        # Convert to dict and merge additional_data if present
        shipment_dict = dict(shipment)
        if 'additional_data' in shipment_dict and shipment_dict['additional_data'] is not None:
            try:
                # additional_data is already a dict from JSONB, no need to parse JSON
                additional_data = shipment_dict['additional_data']
                
                if isinstance(additional_data, str):
                    # If it's a string, parse it
                    additional_data = json.loads(additional_data)
                
                # Merge additional data into the main object if it's a dict
                if isinstance(additional_data, dict):
                    shipment_dict.update(additional_data)
                    # Remove the raw additional_data field
                    del shipment_dict['additional_data']
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, just return basic data
                pass
        
        return shipment_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shipment: {str(e)}"
        )

@app.put("/api/shipments/{shipment_id}", tags=["Shipments"])
async def update_shipment(shipment_id: int, updates: Dict[str, Any]):
    """Update shipment status and details"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current shipment to merge additional_data
        cur.execute("SELECT *, additional_data FROM shipments WHERE id = %s", (shipment_id,))
        current_shipment = cur.fetchone()
        
        if not current_shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )
        
        # Separate direct table fields from additional_data fields
        direct_fields = ['status', 'current_hub_id', 'destination_hub_id', 'route_id', 'priority', 'weight', 'cargo_type']
        additional_data_fields = ['paymentStatus', 'paymentMethod', 'senderName', 'receiverName', 'senderPhone', 'receiverPhone', 'senderAddress', 'receiverAddress']
        
        # Build update for direct fields
        direct_updates = {}
        additional_updates = {}
        
        for key, value in updates.items():
            if key in direct_fields:
                direct_updates[key] = value
            elif key in additional_data_fields:
                additional_updates[key] = value
        
        # Get current additional_data
        current_additional = current_shipment.get('additional_data', {}) or {}
        if isinstance(current_additional, str):
            current_additional = json.loads(current_additional)
        
        # Merge additional_data updates
        current_additional.update(additional_updates)
        
        # Build update query
        update_fields = []
        values = []
        
        # Add direct field updates
        for key, value in direct_updates.items():
            update_fields.append(f"{key} = %s")
            values.append(value)
        
        # Add additional_data update if we have additional updates
        if additional_updates:
            update_fields.append("additional_data = %s")
            values.append(json.dumps(current_additional))
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        values.append(shipment_id)
        
        query = f"""
            UPDATE shipments 
            SET {', '.join(update_fields)} 
            WHERE id = %s 
            RETURNING *
        """
        
        cur.execute(query, values)
        updated_shipment = cur.fetchone()
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        # Process the response to merge additional_data
        shipment_dict = dict(updated_shipment)
        if 'additional_data' in shipment_dict and shipment_dict['additional_data'] is not None:
            additional_data = shipment_dict['additional_data']
            if isinstance(additional_data, str):
                additional_data = json.loads(additional_data)
            if isinstance(additional_data, dict):
                shipment_dict.update(additional_data)
                del shipment_dict['additional_data']
        
        return shipment_dict
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating shipment: {str(e)}"
        )

@app.delete("/api/shipments/{shipment_id}", tags=["Shipments"])
async def delete_shipment(shipment_id: int):
    """Delete a shipment"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM shipments WHERE id = %s RETURNING id", (shipment_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": f"Shipment {shipment_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting shipment: {str(e)}"
        )

# ==================== USER PASSWORD UPDATE ====================

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@app.put("/api/users/{user_id}/password", tags=["Users"])
async def update_user_password(user_id: int, password_data: PasswordUpdate):
    """Update user password"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current user with password hash
        cur.execute("SELECT id, email, password_hash FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Verify current password
        if not bcrypt.checkpw(password_data.current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        cur.execute(
            "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_password_hash, user_id)
        )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password: {str(e)}"
        )

# ==================== ROUTES ====================

class RouteCreate(BaseModel):
    name: str
    origin_hub_id: int
    destination_hub_id: int
    distance_km: float
    estimated_hours: Optional[float] = None
    status: str = "active"

@app.post("/api/routes", tags=["Routes"])
async def create_route(route: RouteCreate):
    """Create a new route between hubs"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Validate hubs exist
        cur.execute("SELECT id FROM hubs WHERE id IN (%s, %s)", (route.origin_hub_id, route.destination_hub_id))
        if cur.rowcount < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid origin or destination hub"
            )
        
        cur.execute("""
            INSERT INTO routes 
            (name, origin_hub_id, destination_hub_id, distance_km, estimated_hours, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            route.name,
            route.origin_hub_id,
            route.destination_hub_id,
            route.distance_km,
            route.estimated_hours,
            route.status
        ))
        
        created_route = cur.fetchone()
        conn.commit()
        
        cur.close()
        db_pool.putconn(conn)
        
        return created_route
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating route: {str(e)}"
        )

@app.get("/api/routes", tags=["Routes"])
async def get_routes():
    """Get all routes"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT r.*, 
                   oh.name as origin_hub_name, 
                   dh.name as destination_hub_name
            FROM routes r
            LEFT JOIN hubs oh ON r.origin_hub_id = oh.id
            LEFT JOIN hubs dh ON r.destination_hub_id = dh.id
            ORDER BY r.id
        """)
        routes = cur.fetchall()
        
        cur.close()
        db_pool.putconn(conn)
        
        return routes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching routes: {str(e)}"
        )

@app.get("/api/routes/{route_id}", tags=["Routes"])
async def get_route(route_id: int):
    """Get route by ID"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT r.*, 
                   oh.name as origin_hub_name, 
                   dh.name as destination_hub_name
            FROM routes r
            LEFT JOIN hubs oh ON r.origin_hub_id = oh.id
            LEFT JOIN hubs dh ON r.destination_hub_id = dh.id
            WHERE r.id = %s
        """, (route_id,))
        route = cur.fetchone()
        
        cur.close()
        db_pool.putconn(conn)
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found"
            )
        
        return route
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching route: {str(e)}"
        )

@app.put("/api/routes/{route_id}", tags=["Routes"])
async def update_route(route_id: int, updates: Dict[str, Any]):
    """Update route details"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        allowed_fields = ['name', 'origin_hub_id', 'destination_hub_id', 'distance_km', 'estimated_time_hours', 'status']
        
        for key, value in updates.items():
            if key in allowed_fields:
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        values.append(route_id)
        
        query = f"""
            UPDATE routes 
            SET {', '.join(update_fields)} 
            WHERE id = %s 
            RETURNING *
        """
        
        cur.execute(query, values)
        updated_route = cur.fetchone()
        
        if not updated_route:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return updated_route
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating route: {str(e)}"
        )

@app.delete("/api/routes/{route_id}", tags=["Routes"])
async def delete_route(route_id: int):
    """Delete a route"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM routes WHERE id = %s RETURNING id", (route_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found"
            )
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": f"Route {route_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting route: {str(e)}"
        )

# ==================== SETTINGS ENDPOINTS ====================

@app.get("/api/settings")
def get_settings():
    """Get all system settings"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT setting_key, setting_value, setting_type, category 
            FROM system_settings 
            ORDER BY category, setting_key
        """)
        
        settings = []
        for row in cur.fetchall():
            settings.append({
                "setting_key": row[0],
                "setting_value": row[1],
                "setting_type": row[2],
                "category": row[3]
            })
        
        cur.close()
        db_pool.putconn(conn)
        
        return {"settings": settings}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching settings: {str(e)}"
        )

@app.post("/api/settings")
def save_settings(settings_data: dict):
    """Save system settings"""
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        
        # Clear existing settings first
        cur.execute("DELETE FROM system_settings")
        
        # Insert new settings
        for category, category_settings in settings_data.items():
            if isinstance(category_settings, dict):
                for key, value in category_settings.items():
                    setting_type = "string"
                    if isinstance(value, bool):
                        setting_type = "boolean"
                        value = str(value).lower()
                    elif isinstance(value, (int, float)):
                        setting_type = "number"
                        value = str(value)
                    
                    cur.execute("""
                        INSERT INTO system_settings (setting_key, setting_value, setting_type, category) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (setting_key) 
                        DO UPDATE SET setting_value = %s, setting_type = %s, category = %s
                    """, (key, str(value), setting_type, category, str(value), setting_type, category))
        
        conn.commit()
        cur.close()
        db_pool.putconn(conn)
        
        return {"message": "Settings saved successfully"}
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving settings: {str(e)}"
        )

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(
        "main_postgres:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
