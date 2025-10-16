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
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp')

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
    title="BlueCart ERP API",
    description="Logistics and shipment management system with PostgreSQL",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            "SELECT id, username, email, password, full_name, phone, role, created_at FROM users WHERE email = %s",
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
        if not verify_password(credentials.password, user['password']):
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

# ==================== HUBS ====================

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
async def get_hub(hub_id: str):
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

# ==================== SHIPMENTS ====================

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
        
        return shipments
        
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
        
        return shipment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shipment: {str(e)}"
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
