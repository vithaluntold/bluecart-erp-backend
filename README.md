# BlueCart ERP Backend# FastAPI Backend README



A FastAPI-based backend for the BlueCart ERP logistics management system.## 🚀 BlueCart ERP FastAPI Backend



## FeaturesA high-performance Python backend built with FastAPI for the BlueCart ERP system.



- 🚀 FastAPI with async support### 📋 Features

- 👤 User management and authentication

- 📦 Shipment tracking and management- **FastAPI Framework**: Modern, fast web framework for building APIs

- 🏢 Hub and route management- **PostgreSQL Integration**: Full database support with SQLAlchemy ORM

- 📊 Analytics and dashboard APIs- **JWT Authentication**: Secure user authentication and authorization

- 🔒 Role-based access control- **Automatic API Documentation**: Interactive docs at `/docs` and `/redoc`

- **Docker Support**: Complete containerization with Docker Compose

## Project Structure- **Comprehensive Testing**: Full test suite with pytest

- **Input Validation**: Pydantic schemas for data validation

```- **CORS Support**: Ready for frontend integration

bluecart-backend/

├── main.py              # Main FastAPI application### 🛠️ Tech Stack

├── main_postgres.py     # PostgreSQL version

├── auth.py              # Authentication handlers- **Framework**: FastAPI 0.104.1

├── crud.py              # Database operations- **Database**: PostgreSQL with SQLAlchemy 2.0

├── database.py          # Database configuration- **Authentication**: JWT with python-jose

├── models.py            # Data models- **Validation**: Pydantic v2

├── schemas.py           # Pydantic schemas- **Testing**: pytest with httpx

├── requirements.txt     # Python dependencies- **Deployment**: Docker & Docker Compose

├── Dockerfile          # Docker configuration

├── docker-compose.yml  # Docker Compose setup### 📁 Project Structure

├── Procfile           # Deployment config

└── tests/             # Test files```

```backend/

├── main.py              # FastAPI application entry point

## Quick Start├── models.py            # SQLAlchemy database models

├── schemas.py           # Pydantic schemas for validation

1. **Install dependencies:**├── crud.py              # Database operations

   ```bash├── database.py          # Database connection and setup

   pip install -r requirements.txt├── auth.py              # Authentication and authorization

   ```├── requirements.txt     # Python dependencies

├── Dockerfile           # Docker configuration

2. **Run the development server:**├── docker-compose.yml   # Multi-container setup

   ```bash├── .env                 # Environment variables

   python main.py├── test_api.py          # API tests

   ```└── setup.py             # Setup and testing script

```

3. **Access the API:**

   - API: http://localhost:8000### 🚀 Quick Start

   - Documentation: http://localhost:8000/docs

   - Interactive API: http://localhost:8000/redoc#### Option 1: Python Virtual Environment



## API Endpoints1. **Create and activate virtual environment**:

   ```bash

### Core Endpoints   cd backend

- `GET /health` - Health check   python -m venv venv

- `GET /` - Root endpoint   

   # Windows

### Shipments   venv\Scripts\activate

- `POST /api/shipments` - Create shipment   

- `GET /api/shipments` - List shipments   # Linux/Mac

- `GET /api/shipments/{id}` - Get shipment details   source venv/bin/activate

- `PUT /api/shipments/{id}` - Update shipment   ```



### Users2. **Install dependencies**:

- `POST /api/users` - Create user   ```bash

- `GET /api/users` - List users   pip install -r requirements.txt

- `GET /api/users/{id}` - Get user details   ```

- `PUT /api/users/{id}` - Update user

3. **Set up environment variables**:

### Hubs   ```bash

- `GET /api/hubs` - List hubs   cp .env.example .env

- `GET /api/hubs/{id}` - Get hub details   # Edit .env with your database credentials

   ```

### Routes

- `POST /api/routes` - Create route4. **Run setup script**:

- `GET /api/routes` - List routes   ```bash

- `GET /api/routes/{id}` - Get route details   python setup.py

   ```

### Analytics

- `GET /api/analytics/dashboard` - Dashboard metrics#### Option 2: Docker (Recommended)



## Environment Variables1. **Start all services**:

   ```bash

Create a `.env` file:   cd backend

   docker-compose up -d

```   ```

DATABASE_URL=your_database_url

SECRET_KEY=your_secret_key2. **Access services**:

```   - API: http://localhost:8000

   - API Docs: http://localhost:8000/docs

## Deployment   - pgAdmin: http://localhost:5050 (admin@bluecart.com / admin123)



### Docker### 📊 API Endpoints

```bash

docker build -t bluecart-backend .#### Health & Status

docker run -p 8000:8000 bluecart-backend- `GET /` - Basic health check

```- `GET /health` - Detailed health information



### Render/Heroku#### Shipments

- Uses `Procfile` for deployment- `POST /api/shipments` - Create new shipment

- Set environment variables in platform- `GET /api/shipments` - List all shipments (with pagination)

- `GET /api/shipments/{id}` - Get shipment by ID/tracking number

## Development- `PUT /api/shipments/{id}` - Update shipment

- `DELETE /api/shipments/{id}` - Delete shipment

1. **Set up virtual environment:**- `POST /api/shipments/{id}/events` - Add event to shipment

   ```bash

   python -m venv .venv#### Analytics

   source .venv/bin/activate  # Windows: .venv\Scripts\activate- `GET /api/analytics/dashboard` - Get dashboard statistics

   ```

### 💡 API Usage Examples

2. **Install development dependencies:**

   ```bash#### Create a Shipment

   pip install -r requirements.txt```bash

   ```curl -X POST "http://localhost:8000/api/shipments" \

  -H "Content-Type: application/json" \

3. **Run tests:**  -d '{

   ```bash    "sender_name": "John Doe",

   python -m pytest    "sender_address": "123 Main St, City, State 12345",

   ```    "receiver_name": "Jane Smith",

    "receiver_address": "456 Oak Ave, City, State 67890",

## Contributing    "package_details": "Electronics - Laptop",

    "weight": 2.5,

1. Fork the repository    "dimensions": {

2. Create a feature branch      "length": 40.0,

3. Make your changes      "width": 30.0,

4. Add tests      "height": 5.0

5. Submit a pull request    },

    "service_type": "express",

## License    "cost": 25.99

  }'

MIT License```

#### Get All Shipments
```bash
curl "http://localhost:8000/api/shipments?limit=10&skip=0"
```

#### Get Shipment by ID
```bash
curl "http://localhost:8000/api/shipments/SH12345678"
```

### 🧪 Testing

Run the test suite:
```bash
python -m pytest test_api.py -v
```

Run specific test:
```bash
python -m pytest test_api.py::test_create_shipment -v
```

### 🔧 Development

#### Start development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Database migrations (if using Alembic):
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### 🐳 Docker Commands

```bash
# Build and start services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend
```

### 🔒 Environment Variables

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root
POSTGRES_DB=shipment_erp

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 🔍 Monitoring & Logging

The application includes:
- Health check endpoints for monitoring
- Structured logging
- Error handling and reporting
- Request/response logging in development

### 🚀 Deployment

#### Production Deployment with Docker:
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Environment Setup:
- Set `DEBUG=False`
- Use strong `SECRET_KEY`
- Configure proper database credentials
- Set up SSL certificates
- Configure reverse proxy (nginx)

### 🤝 Integration with Frontend

The FastAPI backend is designed to work with the Next.js frontend:

1. **CORS**: Configured to allow requests from `http://localhost:3000`
2. **API Routes**: RESTful endpoints that match frontend expectations
3. **Data Format**: JSON responses compatible with frontend models
4. **Authentication**: JWT tokens for secure API access

### 📈 Performance

- **Async Support**: FastAPI's async capabilities for high performance
- **Database Connection Pooling**: Efficient database connections
- **Caching**: Redis integration for caching (in docker-compose)
- **Pagination**: Built-in pagination for large datasets

### 🐛 Troubleshooting

#### Common Issues:

1. **Database Connection Error**:
   - Check PostgreSQL is running
   - Verify credentials in `.env`
   - Ensure database exists

2. **Import Errors**:
   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **Port Already in Use**:
   - Change port in `.env` or docker-compose.yml
   - Kill existing processes: `lsof -ti:8000 | xargs kill`

### 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs backend`
2. Review API documentation: http://localhost:8000/docs
3. Run tests to verify setup: `python -m pytest test_api.py -v`

---

**🎉 Your FastAPI backend is ready for production!**