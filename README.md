# EV Charging Station Network API

A complete RESTful API for managing an EV Charging Station Network built with **Django 5.1** and **Django REST Framework**. Features dynamic pricing, geospatial search (Haversine), concurrency-safe bookings, and real-time charger availability tracking.

## Tech Stack

- **Backend:** Python 3.10+, Django 5.1, Django REST Framework
- **Database:** MySQL 8.0+
- **Authentication:** Token-based (DRF TokenAuthentication)
- **Queue:** Celery + Redis (optional, for background tasks)

## Features

- User registration/login with token authentication
- Station management with geospatial search (Haversine formula)
- Charger status tracking (available/busy/maintenance/offline)
- Concurrency-safe booking system (prevents double-booking)
- Dynamic pricing: Peak hours (6-10 PM) +20%, Night (11 PM-6 AM) -10%
- Session lifecycle: Book → Start → End → Invoice
- Overstay fines (₹5/minute after scheduled end)
- Filtering by city, charger type, availability, date range
- Pagination (15 items/page)

## Quick Setup (1-Click)

### Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip

### Step 1: Clone and Install

```bash
git clone <repository-url>
cd "evm charger backend"
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials (DB_USER, DB_PASSWORD, etc.)
```

### Step 3: Create MySQL Database

```sql
CREATE DATABASE ev_charging CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 4: Run Migrations and Seed Data

```bash
python manage.py makemigrations accounts stations charging
python manage.py migrate
python manage.py seed_data
```

### Step 5: Start Server

```bash
python manage.py runserver
```

API is now live at `http://localhost:8000/api/`

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Login | No |
| POST | `/api/auth/logout/` | Logout | Yes |
| GET/PUT | `/api/auth/profile/` | View/Update profile | Yes |

### Vehicles
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/auth/vehicles/` | List user vehicles | Yes |
| POST | `/api/auth/vehicles/` | Add vehicle | Yes |
| GET/PUT/DELETE | `/api/auth/vehicles/{id}/` | Vehicle CRUD | Yes |

### Stations
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/stations/` | List stations | No |
| GET | `/api/stations/?lat=12.97&lng=77.59&radius=5` | Nearby search | No |
| GET | `/api/stations/nearby/?lat=12.97&lng=77.59&radius=5` | Nearby endpoint | No |
| GET | `/api/stations/{id}/` | Station detail | No |
| POST | `/api/stations/` | Create station | Owner |
| PUT | `/api/stations/{id}/` | Update station | Owner |

### Chargers
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/stations/{station_id}/chargers/` | List chargers | No |
| GET | `/api/stations/{station_id}/chargers/{id}/` | Charger detail | No |
| POST | `/api/stations/{station_id}/chargers/` | Add charger | Owner |
| PATCH | `/api/stations/{station_id}/chargers/{id}/status/` | Update status | Owner |

### Bookings
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/bookings/` | List user bookings | Yes |
| POST | `/api/bookings/` | Create booking | Yes |
| GET | `/api/bookings/{id}/` | Booking detail | Yes |
| PATCH | `/api/bookings/{id}/cancel/` | Cancel booking | Yes |

### Charging Sessions
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/sessions/start/` | Start session | Yes |
| POST | `/api/sessions/{id}/end/` | End session | Yes |
| GET | `/api/sessions/` | List user sessions | Yes |
| GET | `/api/sessions/{id}/` | Session detail | Yes |
| GET | `/api/sessions/{id}/cost-preview/` | Cost preview | Yes |

### Pricing
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/pricing/estimate/?charger_id=1&duration_hours=1.5` | Price estimate | No |

## Geospatial Search

```
GET /api/stations/?lat=12.9716&lng=77.5946&radius=5
```

Uses the **Haversine formula** via raw SQL for high-performance distance calculation. Results include `distance_km` and are sorted by proximity.

## Dynamic Pricing

| Time Period | Hours | Multiplier |
|------------|-------|------------|
| Normal | 6 AM - 6 PM | 1.00x |
| Peak | 6 PM - 10 PM | 1.20x (+20%) |
| Off-Peak | 11 PM - 6 AM | 0.90x (-10%) |

DC-Fast chargers incur an additional ₹2/kWh surcharge.

## Test Credentials (Seeded Data)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@evcharge.com | admin123456 |
| Station Owner | owner1@evcharge.com | owner123456 |
| User | rahul.sharma@test.com | test123456 |

## Database Schema

### Tables
- **users** - Extended Django user with role and phone
- **vehicles** - User vehicles with battery and connector info
- **stations** - EV stations with lat/lng and amenities
- **chargers** - Individual chargers with type, power, pricing
- **bookings** - Time-slot bookings with concurrency control
- **charging_sessions** - Active/completed sessions with cost breakdown

### Key Relationships
- User → Vehicles (1:N)
- User → Stations (1:N, as owner)
- Station → Chargers (1:N)
- User → Bookings (1:N)
- Charger → Bookings (1:N)
- Booking → ChargingSession (1:1)

## Project Structure

```
├── manage.py
├── requirements.txt
├── .env.example
├── EV_Charging_API.postman_collection.json   # 40+ endpoints, ready for 
├── ev_charging/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── core/                 # Shared utilities
│   ├── utils.py          # Haversine, pricing logic
│   ├── pagination.py     # 15 items/page
│   ├── permissions.py    # Role-based access 
│   ├── renderers.py      # StandardJSONRenderer 
│   └── exceptions.py     # Custom 422 for validation errors
├── accounts/             # User & vehicle management
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── stations/             # Station & charger management
│   ├── models.py
│   ├── serializers.py
│   └── views.py
└── charging/             # Bookings & charging sessions
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── services.py       # Business logic
```
