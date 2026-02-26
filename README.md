
# AA Flight Booking Demo - SAGA Microservices Architecture

> **FOR REFERENCE ONLY** - Complete flight booking system with SAGA pattern implementation

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Django 3.1+
- SQLite (included)

### Start All Services (Individual Commands / Python 3.12)
```bash
# Start each microservice in its own terminal (Python 3.12)

# Terminal 1: Backend Service (Port 8001)
cd microservices/backend-service && python3.12 manage.py runserver 127.0.0.1:8001

# Terminal 2: Payment Service (Port 8002)
cd microservices/payment-service && python3.12 manage.py runserver 127.0.0.1:8002

# Terminal 3: Loyalty Service (Port 8003)
cd microservices/loyalty-service && python3.12 manage.py runserver 127.0.0.1:8003

# Terminal 4: UI Service (Port 8000)
cd microservices/ui-service && python3.12 manage.py runserver 127.0.0.1:8000
```

### Access Application
- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **Default Login**: admin / admin123

## 🏗️ Architecture Overview

This is a complete microservices-based flight booking system implementing the SAGA pattern for distributed transactions.

### Microservices Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Flight Booking System                    │
│                  SAGA Microservices Demo                    │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  UI Service  │    │   Backend    │    │   Payment    │
    │  Port 8000   │◄──►│   Service    │◄──►│   Service    │
    │              │    │  Port 8001   │    │  Port 8002   │
    └──────────────┘    └──────────────┘    └──────────────┘
           │                     │                     │
           │                     │                     │
           │            ┌──────────────┐              │
           └───────────►│   Loyalty    │◄─────────────┘
                        │   Service    │
                        │  Port 8003   │
                        └──────────────┘
```

### Service Responsibilities

#### 1. UI Service (Port 8000)
- **Purpose**: Frontend interface and API gateway
- **Features**: 
  - Flight search and booking interface
  - User authentication
  - SAGA transaction orchestration
  - Real-time booking status
- **Key Files**: `microservices/ui-service/`

#### 2. Backend Service (Port 8001)
- **Purpose**: Core flight operations and data management
- **Features**:
  - Flight data management
  - Seat reservation
  - Booking confirmation
  - User management
- **Key Files**: `microservices/backend-service/`

#### 3. Payment Service (Port 8002)
- **Purpose**: Payment processing and financial transactions
- **Features**:
  - Payment authorization
  - Transaction processing
  - Payment history
  - Refund handling
- **Key Files**: `microservices/payment-service/`

#### 4. Loyalty Service (Port 8003)
- **Purpose**: Loyalty program and points management
- **Features**:
  - Points calculation and awarding
  - Tier management
  - Loyalty account management
  - Points redemption
- **Key Files**: `microservices/loyalty-service/`

## 🔄 SAGA Pattern Implementation

### What is SAGA?
SAGA is a distributed transaction pattern that ensures data consistency across microservices without using distributed locks. It breaks down a business transaction into a series of smaller, local transactions that can be compensated if needed.

### SAGA Transaction Flow
```
Flight Booking SAGA Transaction:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Step 1    │───►│   Step 2    │───►│   Step 3    │───►│   Step 4    │
│ ReserveSeat │    │ Authorize   │    │ AwardMiles  │    │ Confirm     │
│ (Backend)   │    │ Payment     │    │ (Loyalty)   │    │ Booking     │
│             │    │ (Payment)   │    │             │    │ (Backend)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   Success/Fail        Success/Fail        Success/Fail        Success/Fail
```

### Compensation Pattern
If any step fails, the SAGA orchestrator automatically triggers compensation actions:
- **Step 4 fails**: Reverse loyalty points, refund payment, release seat
- **Step 3 fails**: Refund payment, release seat
- **Step 2 fails**: Release seat
- **Step 1 fails**: No compensation needed

### SAGA Features in This Demo
✅ **Orchestrator Pattern**: Centralized transaction coordination
✅ **Compensation Logic**: Automatic rollback on failures
✅ **Idempotency**: Safe to retry operations
✅ **Logging**: Complete audit trail of all steps
✅ **Failure Simulation**: Built-in failure testing
✅ **Real-time Status**: Live transaction monitoring

## 📊 Database Management System

### Quick Database Setup
```bash
# Complete database setup with sample data
python database_manager.py setup

# Or step by step:
python setup_db_py312.py              # Setup fresh database
python Data/import_all_from_csv.py    # Import sample data
```

### Database Tools
- **Export**: `python Data/export_db_to_csv.py` - Backup all data to CSV
- **Import**: `python Data/import_all_from_csv.py` - Restore data from CSV
- **Setup**: `python setup_db_py312.py` - Initialize fresh database
- **Manager**: `python database_manager.py` - Master orchestration tool

### Supported Data
- ✅ Airports and flight routes
- ✅ User accounts and authentication
- ✅ Flight bookings and tickets
- ✅ Payment transactions
- ✅ Loyalty accounts and points
- ✅ Banking test data

## 🛠️ Development Setup

### 1. Clone Repository
```bash
git clone git@github.com:varnit-j/AA_DEMO_FOR_REFERENCE_ONLY.git
cd AA_DEMO_FOR_REFERENCE_ONLY
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
python database_manager.py setup
```

### 4. Start Services (Individual Commands / Python 3.12)
```bash
# Start each microservice in its own terminal (Python 3.12)

# Terminal 1: Backend Service (Port 8001)
cd microservices/backend-service && python3.12 manage.py runserver 127.0.0.1:8001

# Terminal 2: Payment Service (Port 8002)
cd microservices/payment-service && python3.12 manage.py runserver 127.0.0.1:8002

# Terminal 3: Loyalty Service (Port 8003)
cd microservices/loyalty-service && python3.12 manage.py runserver 127.0.0.1:8003

# Terminal 4: UI Service (Port 8000)
cd microservices/ui-service && python3.12 manage.py runserver 127.0.0.1:8000
```

### 5. Access Application
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/ (admin/admin123)

## 🎯 Key Features

### SAGA Transaction Management
- ✅ Distributed transaction coordination
- ✅ Automatic compensation on failures
- ✅ Real-time transaction monitoring
- ✅ Complete audit logging
- ✅ Failure simulation for testing

### Microservices Architecture
- ✅ Independent service deployment
- ✅ Service-to-service communication
- ✅ Centralized logging
- ✅ Health monitoring
- ✅ Scalable design

### Flight Booking System
- ✅ Flight search and filtering
- ✅ Real-time seat availability
- ✅ Multi-passenger bookings
- ✅ Payment processing
- ✅ Loyalty points integration

### Database Management
- ✅ Automated backup and restore
- ✅ CSV import/export
- ✅ Migration management
- ✅ Data integrity checks
- ✅ Cross-platform compatibility

## 📁 Project Structure

```
AA_Flight_booking_UI_DEMO/
├── 🎯 Core Application
│   ├── manage.py                     # Django management
│   ├── requirements.txt              # Python dependencies
│   ├── db.sqlite3                   # SQLite database
│   └── capstone/                    # Django settings
│
├── 🛠️ Database Tools
│   ├── database_manager.py          # Master database tool
│   ├── setup_db_py312.py           # Database setup
│   ├── database_manager.bat        # Windows wrapper
│   └── database_manager.sh         # Unix wrapper
│
├── 📊 Data Management
│   └── Data/
│       ├── export_db_to_csv.py     # Export tool
│       ├── import_all_from_csv.py  # Import tool
│       ├── airports.csv            # Airport data
│       └── domestic_flights.csv    # Flight data
│
├── 🏗️ Microservices
│   ├── start_python312.py          # Service starter
│   ├── backend-service/             # Core backend (8001)
│   ├── payment-service/             # Payment processing (8002)
│   ├── loyalty-service/             # Loyalty management (8003)
│   └── ui-service/                  # Frontend interface (8000)
│
├── 🎨 Main Application
│   ├── flight/                     # Flight booking app
│   ├── apps/                       # Additional apps
│   │   ├── banking/                # Banking integration
│   │   ├── loyalty/                # Loyalty program
│   │   └── orders/                 # Order management
│   └── payments/                   # Payment processing
│
└── 🧪 Testing
    └── test/                       # Test suite
        ├── test_basic.py           # Basic tests
        └── test_flight_models.py   # Model tests
```

## 🔌 API Endpoints

### Backend Service (Port 8001)
```
GET  /api/flights/search/           # Search flights
GET  /api/flights/{id}/             # Get flight details
POST /api/saga/start-booking/       # Start SAGA transaction
POST /api/saga/reserve-seat/        # Reserve seat (Step 1)
POST /api/saga/confirm-booking/     # Confirm booking (Step 4)
GET  /api/places/                   # Get airports/places
```

### Payment Service (Port 8002)
```
POST /api/saga/authorize-payment/   # Authorize payment (Step 2)
POST /api/payments/process/         # Process payment
GET  /api/payments/history/{user}/  # Payment history
POST /api/payments/refund/          # Process refund
```

### Loyalty Service (Port 8003)
```
POST /api/saga/award-miles/         # Award loyalty points (Step 3)
GET  /loyalty/status/               # Get loyalty status
POST /loyalty/redeem/               # Redeem points
GET  /loyalty/history/{user}/       # Points history
```

### UI Service (Port 8000)
```
GET  /                             # Home page
GET  /flight/                      # Flight search
POST /flight/ticket/book           # Book flight
GET  /review/                      # Booking review
GET  /admin/                       # Admin panel
```

## 🔧 Configuration

### Default Credentials
```
Admin Panel: http://localhost:8000/admin/
Username: admin
Password: admin123
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test flight
python manage.py test apps.loyalty
```

## 🐛 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Python version
python --version  # Should be 3.12+

# Check if ports are available
netstat -ano | findstr ":800"

# Kill existing processes if needed
taskkill /PID <process_id> /F
```

#### Database Issues
```bash
# Reset database
rm db.sqlite3
python database_manager.py setup
```

## 🔒 Security Notes

This is a **DEMO APPLICATION** for reference only:

⚠️ **NOT for Production Use**
- Default credentials are hardcoded
- Debug mode is enabled
- Test data included

## 📚 Learning Resources

### Understanding SAGA Pattern
1. Book a flight and observe the SAGA logs
2. Simulate failures using the failure simulation toggles
3. Monitor console output during transactions

## 🎯 Demo Scenarios

### Successful Booking Flow
1. Visit http://localhost:8000
2. Search for flights (e.g., DFW to ORD)
3. Select a flight and proceed to booking
4. Complete booking and observe SAGA transaction logs

## 📝 License

This project is for **educational and reference purposes only**.

---

**Version**: 1.0
**Python**: 3.12+
**Django**: 3.1+
**Architecture**: Microservices with SAGA Pattern
**Status**: ✅ Ready for Demo