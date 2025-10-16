# 🚀 Render Deployment Guide - BlueCart ERP

## ✅ Database Setup Complete

### Database Configuration
- **Service**: PostgreSQL 17
- **Instance**: Basic-256mb (256 MB RAM, 0.1 CPU, 15 GB Storage)
- **Database Name**: `bluecart_erp`
- **Username**: `bluecart_admin`
- **Region**: Oregon (US West)

### Connection Details
```
Internal URL: postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a/bluecart_erp

External URL: postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp
```

## 📊 Database Status

### ✅ Data Successfully Synced
- **Users**: 6/6 ✅ (All with bcrypt encrypted passwords)
- **Hubs**: 5/5 ✅
- **Shipments**: 3/3 ✅

### 👥 Available User Accounts
| Email | Password | Role | Name |
|-------|----------|------|------|
| admin@bluecart.com | admin123 | admin | Admin User |
| rajesh@bluecart.com | rajesh123 | hub_manager | Rajesh Kumar |
| priya@bluecart.com | priya123 | hub_manager | Priya Singh |
| amit@bluecart.com | amit123 | driver | Amit Patel |
| sneha@bluecart.com | sneha123 | driver | Sneha Verma |
| ops@bluecart.com | ops123 | operations | Operations Team |

### 🔐 Security Features
- ✅ All passwords encrypted with bcrypt
- ✅ Login validation tested (3/3 tests passed)
- ✅ Wrong password rejection working
- ✅ Password updates encrypted automatically

## 🌐 Web Service Deployment

### Step 1: Create New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `vithaluntold/bluecart-erp-backend`

### Step 2: Configure Web Service

**Basic Settings:**
- **Name**: `bluecart-erp-backend`
- **Region**: Oregon (US West) - Same as database
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: Already configured in `Procfile`

### Step 3: Set Environment Variables

Add these environment variables in Render dashboard:

```bash
# Database Connection
DATABASE_URL=postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a/bluecart_erp

# Python Version
PYTHON_VERSION=3.12.0

# Application Settings (optional)
PORT=8000
HOST=0.0.0.0
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (usually 2-5 minutes)
3. Your app will be available at: `https://bluecart-erp-backend.onrender.com`

## 🔧 Files Already Configured

### ✅ `Procfile`
```
web: uvicorn main_postgres:app --host 0.0.0.0 --port $PORT
```

### ✅ `requirements.txt`
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
bcrypt>=4.0.1
psycopg2-binary>=2.9.9
```

### ✅ `render.yaml`
```yaml
services:
  - type: web
    name: bluecart-erp-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main_postgres:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bluecart-erp-db
          property: connectionString
      - key: PYTHON_VERSION
        value: 3.12.0

databases:
  - name: bluecart-erp-db
    databaseName: bluecart_erp
    user: bluecart_admin
```

### ✅ `main_postgres.py`
- FastAPI backend with PostgreSQL
- Bcrypt password encryption
- User authentication endpoints
- Hub management endpoints
- Shipment tracking endpoints

## 📝 Testing After Deployment

### 1. Check Health
```bash
curl https://bluecart-erp-backend.onrender.com/
```

Expected response:
```json
{
  "message": "BlueCart ERP API",
  "status": "running",
  "database": "connected"
}
```

### 2. Test Login API
```bash
curl -X POST https://bluecart-erp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bluecart.com","password":"admin123"}'
```

Expected response:
```json
{
  "id": 1,
  "email": "admin@bluecart.com",
  "name": "Admin User",
  "role": "admin",
  "phone": "+91-9876543210"
}
```

### 3. Get All Users
```bash
curl https://bluecart-erp-backend.onrender.com/api/users
```

### 4. Get All Hubs
```bash
curl https://bluecart-erp-backend.onrender.com/api/hubs
```

### 5. Get All Shipments
```bash
curl https://bluecart-erp-backend.onrender.com/api/shipments
```

## 🔄 Frontend Integration

Update your frontend `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=https://bluecart-erp-backend.onrender.com
```

Or update the API client directly:

```typescript
// lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://bluecart-erp-backend.onrender.com';
```

## 🛠️ Maintenance Scripts

### Re-sync Data from Local to Render
```bash
python sync_simple_to_postgres.py
```

### Test Login Functionality
```bash
python test_render_login.py
```

### Fix Database Schema
```bash
python fix_render_schema.py
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with email/password
- `GET /api/users` - Get all users
- `GET /api/users/{user_id}` - Get specific user
- `PUT /api/users/{user_id}` - Update user profile

### Hubs
- `GET /api/hubs` - Get all hubs
- `GET /api/hubs/{hub_id}` - Get specific hub
- `POST /api/hubs` - Create new hub
- `PUT /api/hubs/{hub_id}` - Update hub
- `DELETE /api/hubs/{hub_id}` - Delete hub

### Shipments
- `GET /api/shipments` - Get all shipments
- `GET /api/shipments/{shipment_id}` - Get specific shipment
- `POST /api/shipments` - Create new shipment
- `PUT /api/shipments/{shipment_id}` - Update shipment
- `DELETE /api/shipments/{shipment_id}` - Delete shipment

## 🎯 Next Steps

1. ✅ Database configured and data synced
2. ✅ Backend code pushed to GitHub
3. 🔄 **Create Web Service on Render** (you need to do this)
4. 🔄 **Set environment variables** (DATABASE_URL)
5. 🔄 **Deploy and test**
6. 🔄 **Update frontend to use production API**

## 💡 Tips

### Free Tier Limitations
- Web service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Database is always running (not affected)

### Upgrade Options
- For faster response times, upgrade to Starter plan ($7/month)
- Keeps service always running
- Better performance and reliability

### Monitoring
- Check logs in Render dashboard
- Monitor database usage
- Set up health check alerts

## 🆘 Troubleshooting

### Database Connection Issues
```python
# Test connection locally
python -c "import psycopg2; conn = psycopg2.connect('postgresql://bluecart_admin:Suftlt22razRiPN9143GEpIt0WJdfKWe@dpg-d3ijvkje5dus73977f1g-a.oregon-postgres.render.com/bluecart_erp'); print('Connected!')"
```

### Login Not Working
1. Check database has users: `python test_render_login.py`
2. Verify passwords are encrypted
3. Check backend logs on Render
4. Test API endpoint with curl

### Schema Issues
Run the fix script:
```bash
python fix_render_schema.py
```

## 📞 Support

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**Last Updated**: October 17, 2025  
**Status**: ✅ Database Ready | 🔄 Awaiting Web Service Deployment
