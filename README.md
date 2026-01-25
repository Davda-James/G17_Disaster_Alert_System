# G17 Disaster Alert System (DAS)

**DisasterWatch** is a full-stack, location-based emergency alert system that enables administrators to broadcast disaster alerts (Floods, Earthquakes, Fires) and automatically notifies registered users within a specific radius via SMS and Email, while intelligently suppressing duplicate alerts to prevent notification fatigue.

> **📖 For detailed setup instructions (with Docker and without), see [`reports/Setup_Guide.pdf`](reports/Setup_Guide_G17.pdf)**

---

## Key Features

* **Precision Geolocation:** Automatically converts City/State names into Latitude/Longitude using OpenStreetMap (Nominatim).
* **Radius-Based Notifications:** Calculates distance between the disaster and users using Geodesic logic. Only users within **200km** get notified.
* **Multi-Channel Alerts:** Integrated with **Twilio** (SMS) and **SMTP** (Email) to deliver real-time notifications to affected users.
* **Smart Suppression Logic:** If an alert for the same location was sent within the last **12 hours**, the system saves the record but suppresses notifications to avoid alert fatigue.
* **Secure Authentication:** JWT-based Signup/Login with password hashing (Bcrypt) and role-based access control.
* **Interactive Dashboard:** React + TypeScript UI to visualize alerts, manage profile, and submit new reports.
* **Default Admin Account:** Auto-creates `admin@gov.org` user on startup for immediate system access.

---

## Tech Stack

### Frontend
* **React + Vite:** Fast, modern UI framework.
* **TypeScript:** Type-safe code.
* **Tailwind CSS:** Styling and layout.
* **Lucide React:** Iconography.
* **Shadcn UI:** Component library.

### Backend
* **Flask (Python):** REST API server.
* **PyMongo:** Database interaction.
* **Geopy:** Geospatial distance calculations.
* **Flask-JWT-Extended:** Authentication handling.
* **Twilio SDK:** SMS delivery.

### Database & External APIs
* **MongoDB:** NoSQL database for Users and Alerts.
* **OpenStreetMap (Nominatim):** Free Geocoding API.
* **Twilio:** SMS Gateway.

---

## Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and enter project
git clone https://github.com/Davda-James/G17_Disaster_Alert_System.git
cd G17_Disaster_Alert_System

# Start all services (MongoDB, Backend, Frontend)
docker-compose up -d --build

# Check services are running
docker-compose ps
```

**Access the application:**
- Frontend Dashboard: http://localhost:8080
- Backend API: http://localhost:5000
- Default Admin: `admin@gov.org` / `admin123`

### Option 2: Local Development
```bash
# Prerequisites: Python 3.9+, Node.js 16+, MongoDB 5.0+ running locally

# Terminal 1: Start Backend
cd Backend
python -m venv venv
# On Windows: venv\Scripts\activate | On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py

# Terminal 2: Start Frontend
cd Frontend
npm install  # or bun install
npm run dev  # or bun run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- Default Admin: `admin@gov.org` / `admin123`

> ⚠️ **Important:** Update `.env` file to use `mongodb://localhost:27017` for local setup (not `mongo:27017`)

---


### What Code Does What?

| Component | Location | Purpose |
|-----------|----------|---------|
| **User Authentication** | `Backend/app.py` routes: `/api/signup`, `/api/login`, `/api/me` | User registration, login, profile retrieval |
| **Alert Creation** | `Backend/app.py` route: `/api/alerts` (POST) | Create alerts, trigger notifications |
| **Alert Retrieval** | `Backend/app.py` route: `/api/alerts` (GET) | Fetch alerts with filtering |
| **Geolocation** | `Backend/app.py` function: `get_coordinates()` | Convert City/State to Lat/Lng via OpenStreetMap |
| **Distance Calculation** | `Backend/app.py` functions: `should_trigger_sms()`, `should_trigger_email()` | Check if users within radius |
| **SMS Broadcasting** | `Backend/app.py` function: `broadcast_sms_to_users()` | Send SMS via Twilio |
| **Email Broadcasting** | `Backend/app.py` function: `broadcast_email_to_users()` | Send Email via SMTP |
| **Admin User Creation** | `Backend/app.py` function: `ensure_admin_user()` | Auto-create admin on startup |
| **Frontend Dashboard** | `Frontend/src/pages/DashboardPage.tsx` | Main UI for viewing alerts |
| **Alert Form Modal** | `Frontend/src/components/NotifyAlertModal.tsx` | Form to create new alerts |
| **Login/Signup** | `Frontend/src/pages/LoginPage.tsx`, `SignupPage.tsx` | User authentication UI |
| **Database** | MongoDB (Docker service: `mongo`) | Stores users & alerts |

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Davda-James/G17_Disaster_Alert_System.git
cd G17_Disaster_Alert_System
```

### 2. Configure Environment
Create/update `.env` file in project root:
```env
# MongoDB (Docker: use 'mongo', Local: use 'localhost')
MONGO_URI=mongodb://mongo:27017/my_database

# JWT Secret (change in production!)
JWT_SECRET_KEY=your-secret-key-here

# Twilio (optional, for SMS)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_NUMBER=+1234567890

# SMTP (optional, for email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Choose Your Setup Method

**Option A: Docker (Easiest)**
```bash
docker-compose up -d --build
```

**Option B: Local Development**
See section below or refer to [`reports/Setup_Guide.pdf`](reports/Setup_Guide_G17.pdf) for detailed steps.

### 4. Access the Application
- **Dashboard:** http://localhost:8080 (Docker) or http://localhost:5173 (Local)
- **API:** http://localhost:5000
- **Login:** admin@gov.org / admin123

> 📖 **For comprehensive setup instructions with troubleshooting, see [`reports/Setup_Guide.pdf`](reports/Setup_Guide_G17.pdf)**

---

## Backend Setup (Flask)

### Without Docker
```bash
cd Backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set MongoDB URI in .env (use localhost!)
# MONGO_URI=mongodb://localhost:27017/my_database

# Run server
python app.py
```

The backend runs on `http://localhost:5000`.

---

## Frontend Setup (React)

### Without Docker
Open a new terminal:
```bash
cd Frontend

# Install dependencies (npm or bun)
npm install
# OR
bun install

# Start development server
npm run dev
# OR
bun run dev
```

The frontend runs on `http://localhost:5173` (or configured port).

---

## System Architecture & Data Flow

The system follows a multi-phase approach to handle disaster alerts:

### Phase 1: User Registration (Geocoding)
1. User signs up with Name, Email, Phone, and Location (City/State)
2. Backend calls OpenStreetMap (Nominatim API) to convert "City, State" → Latitude/Longitude
3. User profile saved to MongoDB with coordinates
4. User is now "mappable" for alert notifications

### Phase 2: Alert Creation (Processing Core)
1. Admin creates alert (Title, Message, Location, Severity)
2. Backend geocodes alert location if exact coordinates not provided
3. System checks for **recent alerts within 200km radius** (within last 12 hours)
4. If found: Alert saved but notifications **suppressed** (prevents alert fatigue)
5. If not found: Proceed to notification phase

### Phase 3: Alert Broadcasting (Notification Delivery)
1. Backend retrieves ALL users from MongoDB
2. For each user, calculates **Geodesic distance** between user and alert
3. If user within 200km radius:
   - Format phone number (add +91 for India)
   - Send SMS via **Twilio** API
   - Send Email via **SMTP** server
4. Alert marked as `sms_sent: true` and `email_sent: true` in database

### Phase 4: Dashboard Updates
1. Frontend polls `GET /api/alerts` endpoint
2. Dashboard refreshes to show new alert
3. Affected users receive notifications on their devices



---

## API Endpoints

All endpoints are documented in the backend code (`Backend/app.py`).

### Authentication Routes (No JWT Required)

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `POST` | `/api/signup` | Register new user & geocode location | `{name, email, password, phone, city, state}` |
| `POST` | `/api/login` | Authenticate user & get JWT token | `{email, password}` |

### Protected Routes (JWT Required)

| Method | Endpoint | Description | 
|--------|----------|-------------|
| `GET` | `/api/me` | Get current user profile |
| `PUT` | `/api/user/<user_id>` | Update user profile |
| `POST` | `/api/alerts` | Create new alert (with broadcast) |
| `GET` | `/api/alerts?time=30d&type=all` | Fetch alerts with filtering |

### Query Parameters for `/api/alerts`
- `time`: `24h`, `7d`, `30d` (default: `30d`)
- `type`: Alert type filter (default: `all`)

---

## Default Admin Account

On first run, the system automatically creates a default admin user:

```
Email:    admin@gov.org
Password: admin123
Status:   Authorized (can create alerts)
```

- Can be customized via `ADMIN_PASSWORD` in `.env`
- Auto-verified on every backend startup
- If account exists but not authorized, it's auto-updated to authorized

---

## Testing

### Backend Tests
```bash
cd tests/backend
pytest -v
```

Tests cover:
- User authentication and authorization
- Alert creation and validation
- Geolocation and distance calculations
- Notification delivery logic
- Error handling and edge cases

### Frontend Tests
```bash
cd Frontend
npm run test
```

Tests cover:
- Component rendering
- User interactions
- API integration
- Context management

---

## Troubleshooting

### Common Issues

**Issue:** MongoDB connection refused
- **Docker:** Ensure `MONGO_URI=mongodb://mongo:27017/...` (not localhost)
- **Local:** Ensure MongoDB service is running (`mongosh` to test)

**Issue:** Ports already in use
- **Change ports** in `docker-compose.yml` or local server configs
- **Kill processes:** `lsof -i :5000` (Mac/Linux) or `netstat -ano | findstr :5000` (Windows)

**Issue:** npm dependencies not found
- **Solution:** `cd Frontend && rm -rf node_modules && npm install`

**Issue:** JWT token invalid
- **Solution:** Ensure `JWT_SECRET_KEY` is consistent across server restarts

> For more troubleshooting, see [`reports/Setup_Guide.pdf`](reports/Setup_Guide_G17.pdf)

---

## Documentation Files

| File | Purpose |
|------|---------|
| [`reports/Setup_Guide.pdf`](reports/Setup_Guide_G17.pdf) | **⭐ Start here** - Comprehensive setup guide with Docker & local setup |
| [`reports/User_Guide.pdf`](reports/Setup_Guide_G17.pdf) | System architecture, design decisions, and technical specifications |
| [`README.md`](README.md) | Quick overview and API reference (this file) |

---

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** (ultra-fast build tool)
- **Tailwind CSS** (utility-first styling)
- **Shadcn UI** (component library)
- **Lucide React** (icons)

### Backend
- **Flask** (lightweight Python web framework)
- **PyMongo** (MongoDB Python driver)
- **Flask-JWT-Extended** (JWT authentication)
- **Twilio SDK** (SMS delivery)
- **Geopy** (geospatial calculations)
- **Flask-CORS** (cross-origin requests)

### Database & APIs
- **MongoDB** (NoSQL database)
- **OpenStreetMap Nominatim** (free geocoding)
- **Twilio** (SMS gateway)
- **SMTP** (email delivery)

### DevOps
- **Docker** & **Docker Compose** (containerization)
- **Pytest** (Python testing framework)
- **Vitest** (JavaScript testing)

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open a Pull Request

---

## Project Information

- **Group:** G17
- **Assignment:** Collaborative Software Development
- **Assignment 1:** Full-Stack Alert System
- **Repository:** https://github.com/Davda-James/G17_Disaster_Alert_System

---

## Support & Resources

- 📖 [User Setup Guide](reports/USER_SETUP_GUIDE.tex) - Detailed installation instructions
- 📋 [System Report](reports/das_report.tex) - Architecture and design documentation
- 🔗 [Flask Documentation](https://flask.palletsprojects.com/)
- 🔗 [React Documentation](https://react.dev)
- 🔗 [MongoDB Documentation](https://docs.mongodb.com/)
- 🔗 [Docker Documentation](https://docs.docker.com/)
- 🔗 [Twilio API](https://www.twilio.com/docs/)

---

## Project Structure
```
/
├── frontend/             # React + Vite application
│   ├── src/
│   │   ├── components/   # UI Components (Modals, Buttons)
│   │   ├── contexts/     # Auth Context
│   │   └── pages/        # Dashboard, Login, Signup
│   └── package.json
│
├── backend/              # Flask application
│   ├── app.py            # Main entry point (All logic)
│   └── requirements.txt  # Python dependencies
│
└── README.md             # You are here
```
