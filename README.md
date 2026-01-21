# DisasterWatch

DisasterWatch is a full-stack, location-based emergency alert system. It allows administrators to broadcast disaster alerts (Floods, Earthquakes, Fires) and automatically notifies registered users within a specific radius via SMS, while intelligently suppressing duplicate alerts to prevent spam.

---

## Key Features

* **Precision Geolocation:** Automatically converts City/State names into Latitude/Longitude using OpenStreetMap (Nominatim).
* **Radius-Based Notifications:** Calculates distance between the disaster and users using Geodesic logic. Only users within **50km** get notified.
* **Automatic SMS Broadcast:** Integrated with **Twilio** to send real-time SMS alerts to affected users immediately upon alert creation.
* **Smart Spam Suppression:** If an alert for the same location was sent within the last **12 hours**, the system saves the record but suppresses the SMS to avoid panic fatigue.
* **Secure Authentication:** JWT-based Signup/Login with password hashing (Bcrypt).
* **Interactive Dashboard:** React-based UI to visualize alerts and submit new reports.

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

## Getting Started

### 1. Backend Setup (Flask)
```bash
# 1. Navigate to backend folder (if applicable) or root
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install flask flask-pymongo flask-bcrypt flask-jwt-extended flask-cors geopy requests twilio

# 5. Start the Server
python app.py
```

The backend runs on `http://localhost:50002`.

### 2. Frontend Setup (React)

Open a new terminal:
```bash
# 1. Navigate to frontend folder
cd frontend

# 2. Install Node modules
npm install

# 3. Start the Development Server
npm run dev
```

The frontend runs on `http://localhost:5173` (usually).

---

## Configuration

Ensure your `app.py` has the following keys configured (or use a `.env` file):
```python
# app.py
app.config["MONGO_URI"] = "mongodb://localhost:27017/my_database"
app.config["JWT_SECRET_KEY"] = "your-secret-key"
app.config["TWILIO_ACCOUNT_SID"] = "your_twilio_sid"
app.config["TWILIO_AUTH_TOKEN"] = "your_twilio_token"
app.config["TWILIO_NUMBER"] = "+1234567890"
```

---

## System Architecture: 

Here is the step-by-step logic flow of the system during operation:

### 1. User Signup (The Geocoding Phase)

- **User Input:** User fills out the Signup form (Name, Email, Phone, City: "Pune", State: "Maharashtra").
- **API Call:** Frontend hits `POST /api/signup`.
- **Backend Logic:**
  - The backend pauses to call the OpenStreetMap API.
  - It converts "Pune, Maharashtra" into coordinates: `Lat: 18.5204, Lng: 73.8567`.
  - It saves the User and these Coordinates into MongoDB.
- **Result:** The user is now "mappable" for future disasters.

### 2. Alert Creation (The Processing Core)

An admin logs in and creates an alert (e.g., "Flood Warning in Pune").

- **Frontend:** Sends alert data + location string to `POST /api/alerts`.
- **Backend - Step A (Geocoding):**
  - If exact coordinates aren't provided, it geocodes "Pune" to get the disaster's center point.
- **Backend - Step B (Duplicate Check / Suppression):**
  - The system checks MongoDB: "Has an SMS been sent for a disaster within 100km of this point in the last 12 hours?"
  - If **YES:** The new alert is saved to DB, but SMS is skipped (`sms_sent: false`).
  - If **NO:** The system proceeds to Step C.
- **Backend - Step C (Radius Search):**
  - The system pulls ALL users from the database.
  - It loops through them and uses Geodesic distance to measure the distance between the User and the Disaster.
- **Backend - Step D (The Trigger):**
  - If User A is within 50km, their phone number is formatted (adding +91).
  - Twilio is triggered to send the SMS.
  - The Alert is saved to MongoDB with `sms_sent: true`.

### 3. Dashboard Update

- The frontend reacts to the successful response.
- The Dashboard refreshes to show the new Alert card.
- If the user checks their phone, they receive the physical SMS.

---

## API Endpoints

| Method | Endpoint      | Protected? | Description                               |
|--------|---------------|------------|-------------------------------------------|
| POST   | `/api/signup` | No         | Register new user & geocode location.     |
| POST   | `/api/login`  | No         | Authenticate & receive JWT.               |
| GET    | `/api/me`     | Yes        | Get current user profile.                 |
| POST   | `/api/alerts` | Yes        | Create alert, calculate radius, send SMS. |
| GET    | `/api/alerts` | Yes        | Fetch list of active alerts.              |

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
