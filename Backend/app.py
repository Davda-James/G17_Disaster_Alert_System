from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from bson.objectid import ObjectId
from geopy.distance import geodesic
import datetime
from datetime import timedelta
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import smtplib
from email.message import EmailMessage
import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- LOGGING CONFIGURATION ---
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create a custom logger with Backend prefix
logger = logging.getLogger('BackendLogger')
logger.setLevel(logging.DEBUG)

# Create rotating file handler
log_file = os.path.join(logs_dir, 'backend.log')
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)  # 10MB per file, keep 10 backups
handler.setLevel(logging.DEBUG)

# Create formatter with Backend prefix and timestamp
formatter = logging.Formatter('Backend-[%(asctime)s] - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Suppress sensitive data logging
def sanitize_log_message(message):
    """Remove sensitive user data from log messages."""
    if isinstance(message, str):
        # Hide email patterns
        import re
        message = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED_EMAIL]', message)
        # Hide phone patterns
        message = re.sub(r'\+?91\d{10}|\+?\d{10,12}', '[REDACTED_PHONE]', message)
        # Hide password fields
        message = re.sub(r'"password"\s*:\s*"[^"]*"', '"password": "[REDACTED]"', message)
        message = re.sub(r"'password'\s*:\s*'[^']*'", "'password': '[REDACTED]'", message)
    return message

# --- 1. CONFIGURATION & CONSTANTS ---
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/my_database")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "Group-17")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=7)

# Twilio Config
app.config['TWILIO_ACCOUNT_SID'] = os.getenv("TWILIO_ACCOUNT_SID", "")
app.config['TWILIO_AUTH_TOKEN'] = os.getenv("TWILIO_AUTH_TOKEN", "")
app.config['TWILIO_NUMBER'] = os.getenv("TWILIO_NUMBER", "")

# SMTP Config
app.config['SMTP_HOST'] = os.getenv("SMTP_HOST", "")
app.config['SMTP_PORT'] = int(os.getenv("SMTP_PORT", 587))
app.config['SMTP_USER'] = os.getenv("SMTP_USER", "")
app.config['SMTP_PASSWORD'] = os.getenv("SMTP_PASSWORD", "")
app.config['FROM_EMAIL'] = os.getenv("FROM_EMAIL", "")
app.config['SMTP_USE_TLS'] = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

# Logic Constants (These are Just for the cases when workflow fails and we redirect to some deafault cases)
CONSTANTS = {
    "SMS_RADIUS_KM": 200,          
    "DUPLICATE_CHECK_RADIUS_KM": 200, # Radius to check for existing alerts
    "DUPLICATE_TIME_WINDOW_HOURS": 12, # Time window to suppress new SMS
    "DEFAULT_LAT": 20.5937,        # Center of India Lat
    "DEFAULT_LNG": 78.9629,        # Center of India Lng
    "USER_AGENT": "DisasterWatchApp/1.0",
    "MAX_ROUNDS": 5
}

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app) 


def get_coordinates(city, state, country="India"):
    """Fetches Latitude and Longitude from OpenStreetMap."""
    try:
        query = f"{city}, {state}, {country}"
        headers = { 'User-Agent': CONSTANTS["USER_AGENT"] }
        url = "https://nominatim.openstreetmap.org/search"
        params = { 'q': query, 'format': 'json', 'limit': 1 }
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            logger.info(f"Coordinates fetched for {city}, {state}")
            return {
                "lat": float(data[0]['lat']),
                "lng": float(data[0]['lon'])
            }
        logger.warning(f"No coordinates found for {city}, {state}. Using defaults.")
        return {"lat": CONSTANTS["DEFAULT_LAT"], "lng": CONSTANTS["DEFAULT_LNG"]}
        
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return {"lat": CONSTANTS["DEFAULT_LAT"], "lng": CONSTANTS["DEFAULT_LNG"]}

def user_serializer(user):
    """Converts MongoDB user object to JSON."""
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "phone": user.get("phone", ""),
        "location": user.get("location", {}),
        "isAuthorized": user.get("isAuthorized", False),
        "notificationPreferences": user.get("notificationPreferences", {}),
    }

def send_twilio_sms(to_number, title, message_body):
    """Sends SMS via Twilio."""
    formatted_number = to_number.strip()
    if not formatted_number.startswith('+'):
        formatted_number = f"+91{formatted_number}" # Default to India +91

    final_message = f"🚨 {title.upper()} 🚨\n{message_body}\n- DisasterWatch Team"
    client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

    try:
        message = client.messages.create(
            body=final_message,
            from_=app.config['TWILIO_NUMBER'],
            to=formatted_number
        )
        logger.info(f"SMS sent successfully to [REDACTED_PHONE]. Message SID: {message.sid}")
        return {"status": "success", "sid": message.sid}
    except TwilioRestException as e:
        logger.error(f"Twilio Error for [REDACTED_PHONE]: {e}")
        return {"status": "error", "message": str(e)}

def should_trigger_sms(new_alert_coords):
    """
    Checks if a similar alert (SMS sent) exists within 
    RADIUS and TIME WINDOW.
    Returns: Boolean (True = Send SMS, False = Suppress)
    """
    try:
        alerts_collection = mongo.db.alerts
        
        #  Define Time Window
        time_threshold = datetime.datetime.utcnow() - timedelta(hours=CONSTANTS["DUPLICATE_TIME_WINDOW_HOURS"])
        
        #  Query for recent alerts where SMS was actually sent
        recent_active_alerts = alerts_collection.find({
            "timestamp": {"$gte": time_threshold},
            "sms_sent": True  # Only check alerts that triggered SMS
        })

        new_point = (new_alert_coords['lat'], new_alert_coords['lng'])

        #  Check Distance for each recent alert
        for existing_alert in recent_active_alerts:
            existing_coords = existing_alert.get('coordinates')
            if existing_coords and 'lat' in existing_coords:
                existing_point = (existing_coords['lat'], existing_coords['lng'])
                
                distance = geodesic(new_point, existing_point).km
                
                if distance <= CONSTANTS["DUPLICATE_CHECK_RADIUS_KM"]:
                    logger.info(f"SMS Suppressed: Similar alert found {distance:.2f}km away.")
                    return False # Found a match, DO NOT send SMS

        logger.info(f"SMS check passed - no duplicates found within radius")
        return True # No matching alert found, proceed with SMS

    except Exception as e:
        logger.error(f"Error in suppression logic: {e}")
        return True # Fail-safe: Send SMS if check fails

def should_trigger_email(new_alert_coords):
    """
    Returns True if an email should be sent for an alert at `new_alert_coords`.
    Suppresses sending when a recent alert (within DUPLICATE_TIME_WINDOW_HOURS)
    that already had email_sent=True exists within DUPLICATE_CHECK_RADIUS_KM.
    """
    try:
        alerts_collection = mongo.db.alerts
        time_threshold = datetime.datetime.utcnow() - timedelta(hours=CONSTANTS["DUPLICATE_TIME_WINDOW_HOURS"])

        # Only consider alerts that previously had emails actually sent
        recent_email_alerts = alerts_collection.find({
            "timestamp": {"$gte": time_threshold},
            "email_sent": True
        })

        new_point = (new_alert_coords['lat'], new_alert_coords['lng'])

        for existing_alert in recent_email_alerts:
            existing_coords = existing_alert.get('coordinates')
            if not existing_coords or 'lat' not in existing_coords or 'lng' not in existing_coords:
                continue

            existing_point = (existing_coords['lat'], existing_coords['lng'])
            distance_km = geodesic(new_point, existing_point).km

            if distance_km <= CONSTANTS["DUPLICATE_CHECK_RADIUS_KM"]:
                logger.info(f"Email Suppressed: Similar alert found {distance_km:.2f} km away.")
                return False

        logger.info(f"Email check passed - no duplicates found within radius")
        return True

    except Exception as e:
        # Fail-safe: if suppression check fails, allow sending (avoid silent missed alerts)
        logger.error(f"Error in email suppression logic: {e}")
        return True


def broadcast_sms_to_users(alert_data):
    """Iterates users and sends SMS if within radius."""
    
    try:
        # 1. Fetch all users
        # Convert cursor to list immediately to avoid cursor exhaustion issues
        all_users = list(mongo.db.users.find({}))
        logger.info(f"Starting SMS broadcast for alert: {alert_data.get('title', 'Unknown')}")
        
        alert_point = (alert_data['coordinates']['lat'], alert_data['coordinates']['lng'])
        
        # 2. FILTER FIRST: Identify who actually needs the SMS
        # This saves CPU by doing the math only once per user
        recipients = []
        for user in all_users:
            user_loc = user.get('location', {})
            user_coords = user_loc.get('coordinates')
            
            if user_coords and 'lat' in user_coords:
                user_point = (user_coords['lat'], user_coords['lng'])
                if geodesic(alert_point, user_point).km <= CONSTANTS["SMS_RADIUS_KM"]:
                    if user.get("phone"):
                        recipients.append(user)

        logger.info(f"Found {len(recipients)} users within SMS radius")
        
        curr_round = 0
        users_to_process = recipients 
        success_count = 0

        while curr_round < CONSTANTS["MAX_ROUNDS"] and len(users_to_process) > 0:
          
            
            failed_in_this_round = [] 
            for user in users_to_process:
                phone = user.get("phone")
                logger.debug(f"Sending SMS to user [REDACTED_PHONE]")
                # Send SMS
                response = send_twilio_sms(phone, alert_data['title'], alert_data['message'])
                
                if response['status'] == 'success':
                    success_count += 1
                else:
                    
                    failed_in_this_round.append(user)
            users_to_process = failed_in_this_round
            curr_round += 1
        
        logger.info(f"SMS Broadcast Complete: Sent to {success_count} users.")
        return True
    except Exception as e:
        logger.error(f"SMS Broadcast Failed: {e}")
        return False
    
def broadcast_email_to_users(alert_data):
    """Iterate users and send email alerts to those within radius and who opted-in."""
    try:
        all_users = list(mongo.db.users.find({}))
        logger.info(f"Starting email broadcast for alert: {alert_data.get('title', 'Unknown')}")
        
        alert_point = (alert_data['coordinates']['lat'], alert_data['coordinates']['lng'])

        # 1) Build recipient list (respect user notification preferences)
        recipients = []
        for user in all_users:
            prefs = user.get("notificationPreferences", {})
            # Skip if user opted out of email
            if prefs.get("email") is False:
                continue

            user_loc = user.get("location", {})
            user_coords = user_loc.get("coordinates")
            if user_coords and 'lat' in user_coords:
                user_point = (user_coords['lat'], user_coords['lng'])
                if geodesic(alert_point, user_point).km <= CONSTANTS["SMS_RADIUS_KM"]:
                    if user.get("email"):
                        recipients.append(user)

        logger.info(f"Found {len(recipients)} users within email radius")

        # 2) Retry loop (same logic as broadcast_sms_to_users)
        curr_round = 0
        users_to_process = recipients
        success_count = 0

        while curr_round < CONSTANTS["MAX_ROUNDS"] and len(users_to_process) > 0:
            failed_in_this_round = []
            for user in users_to_process:
                to_email = user.get("email")
                try:
                    logger.debug(f"Sending email to user [REDACTED_EMAIL]")
                    # Build email
                    msg = EmailMessage()
                    msg["Subject"] = f"🚨 {alert_data['title'].upper()} 🚨"
                    msg["From"] = app.config.get("FROM_EMAIL") or app.config.get("SMTP_USER")
                    msg["To"] = to_email
                    body = f"{alert_data.get('message','')}\n\nLocation: {alert_data.get('location')}\n- DisasterWatch Team"
                    msg.set_content(body)

                    # SMTP send
                    smtp_host = app.config.get("SMTP_HOST")
                    smtp_port = int(app.config.get("SMTP_PORT", 587))
                    smtp_user = app.config.get("SMTP_USER")
                    smtp_pass = app.config.get("SMTP_PASSWORD")
                    use_tls = app.config.get("SMTP_USE_TLS", True)

                    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                        if use_tls:
                            server.starttls()
                        if smtp_user and smtp_pass:
                            server.login(smtp_user, smtp_pass)
                        server.send_message(msg)

                    success_count += 1
                except Exception as e:
                    logger.error(f"Email failed for [REDACTED_EMAIL]: {e}")
                    failed_in_this_round.append(user)

            users_to_process = failed_in_this_round
            curr_round += 1

        logger.info(f"Email Broadcast Complete: Sent to {success_count} users.")
        return True

    except Exception as e:
        logger.error(f"Email Broadcast Failed: {e}")
        return False

# --- 3. ROUTES ---

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    users = mongo.db.users
    
    logger.info(f"Signup attempt with email: [REDACTED_EMAIL]")

    if users.find_one({"email": data['email']}) :
        logger.warning(f"Signup failed - user already exists with email: [REDACTED_EMAIL]")
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    is_authorized = data['email'].lower().endswith(".admin@gmail.com")
    coords = get_coordinates(data['city'], data['state'])

    new_user = {
        "name": data['name'],
        "email": data['email'],
        "password": hashed_password,
        "phone": data['phone'],
        "location": {
            "city": data['city'],
            "state": data['state'],
            "country": "India",
            "coordinates": coords
        },
        "isAuthorized": is_authorized,
        "notificationPreferences": { "email": True, "sms": True, "push": True },
        "created_at": datetime.datetime.utcnow()
    }

    result = users.insert_one(new_user)
    logger.info(f"User created successfully with ID: {result.inserted_id}")
    
    access_token = create_access_token(identity=str(result.inserted_id))
    created_user = users.find_one({"_id": result.inserted_id})
    
    return jsonify({ "token": access_token, "user": user_serializer(created_user) }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = mongo.db.users
    
    logger.info(f"Login attempt with email: [REDACTED_EMAIL]")
    
    user = users.find_one({"email": data['email']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        logger.info(f"Login successful for user ID: {user['_id']}")
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({ "token": access_token, "user": user_serializer(user) }), 200
    
    logger.warning(f"Login failed - invalid credentials for email: [REDACTED_EMAIL]")
    return jsonify({"msg": "Invalid email or password"}), 401

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    logger.debug(f"Fetching current user: {current_user_id}")
    
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    if user:
        logger.debug(f"User found: {current_user_id}")
        return jsonify({"user": user_serializer(user)}), 200
    
    logger.warning(f"User not found: {current_user_id}")
    return jsonify({"msg": "User not found"}), 404

@app.route('/api/user/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    
    logger.info(f"Update user request for ID: {user_id}")
    
    if current_user_id != user_id:
        logger.warning(f"Unauthorized update attempt - user {current_user_id} tried to update {user_id}")
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    users = mongo.db.users
    new_coords = None
    
    if 'location' in data and 'city' in data['location']:
        loc = data['location']
        new_coords = get_coordinates(loc.get('city'), loc.get('state'), loc.get('country', 'India'))

    update_fields = {}
    allowed_fields = ["name", "phone", "location", "notificationPreferences"]
    
    for field in allowed_fields:
        if field in data:
            update_fields[field] = data[field]
            
    if new_coords and 'location' in update_fields:
        update_fields['location']['coordinates'] = new_coords

    if update_fields:
        users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
        logger.info(f"User {user_id} updated successfully with fields: {', '.join(update_fields.keys())}")

    updated_user = users.find_one({"_id": ObjectId(user_id)})
    return jsonify(user_serializer(updated_user)), 200

# --- UPDATED ALERT CREATION LOGIC ---
# ... (imports remain the same)

# --- HELPER: SAFE SERIALIZER ---
def serialize_alert(doc):
    """
    Safely converts a MongoDB alert document to a JSON-ready dictionary.
    Ensures timestamps are ISO strings and ObjectIds are strings.
    """
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "title": doc.get("title", "Untitled Alert"),
        "message": doc.get("message", ""),
        "type": doc.get("type", "info"),
        "severity": doc.get("severity", "medium"),
        "location": doc.get("location", "Unknown Location"),
        # Ensure coordinates are always a dictionary with lat/lng
        "coordinates": doc.get("coordinates", {"lat": 0, "lng": 0}),
        "status": doc.get("status", "active"),
        # CRITICAL FIX: Convert datetime to ISO string for Frontend
        "timestamp": doc["timestamp"].isoformat() if isinstance(doc.get("timestamp"), datetime.datetime) else str(datetime.datetime.utcnow().isoformat()),
        "sms_sent": doc.get("sms_sent", False),
        "email_sent": doc.get("email_sent",False)
    }

# ... (rest of your config and earlier functions)

# --- UPDATED ROUTES ---

@app.route('/api/alerts', methods=['POST'])
@jwt_required()
def create_alert():
    current_user_id = get_jwt_identity()
    data = request.json
    
    # INPUT VALIDATION: Check for required fields
    required_fields = ['title', 'message', 'type', 'severity', 'location']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None or (isinstance(data[field], str) and data[field].strip() == "")]
    
    if missing_fields:
        logger.warning(f"Alert creation failed - missing fields: {missing_fields}")
        return jsonify({"msg": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    logger.info(f"New alert created by user {current_user_id} - Title: {data.get('title', 'Unknown')}")
    
    # 1. Logic to get coords and check SMS (Same as your code)
    alert_coords = data.get('coordinates')
    if not alert_coords or alert_coords.get('lat') == 0:
        parts = data['location'].split(',')
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else ""
        alert_coords = get_coordinates(city, state)

    trigger_sms = should_trigger_sms(alert_coords)
    trigger_email = should_trigger_email(alert_coords)
    
    logger.debug(f"Alert SMS trigger: {trigger_sms}, Email trigger: {trigger_email}")

    # 2. Create Alert Object
    new_alert = {
        "user_id": ObjectId(current_user_id),
        "title": data['title'],
        "message": data['message'],
        "type": data['type'],
        "severity": data['severity'],
        "location": data['location'],
        "coordinates": alert_coords,
        "status": "active",
        "timestamp": datetime.datetime.utcnow(),
        "sms_sent": trigger_sms,
        "email_sent": trigger_email
    }

    result = mongo.db.alerts.insert_one(new_alert)
    logger.info(f"Alert {result.inserted_id} created successfully")

    # 3. Broadcast SMS and email (first sms)
    if trigger_sms:
        logger.info("Initiating SMS broadcast")
        broadcast_sms_to_users(new_alert)

    if trigger_email:
        logger.info("Initiating email broadcast")
        broadcast_email_to_users(new_alert)

    # 4. Fetch the fresh document to return it safely
    saved_alert = mongo.db.alerts.find_one({"_id": result.inserted_id})
    
    # USE THE SERIALIZER
    return jsonify(serialize_alert(saved_alert)), 201


@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    time_filter = request.args.get('time', '30d')
    type_filter = request.args.get('type', 'all')
    
    logger.debug(f"Fetching alerts - Time filter: {time_filter}, Type filter: {type_filter}")
    
    query = {}
    now = datetime.datetime.utcnow()
    
    if time_filter == '24h':
        cutoff = now - timedelta(hours=24)
    elif time_filter == '7d':
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=30)
    
    query['timestamp'] = {"$gte": cutoff}

    if type_filter != 'all':
        query['type'] = type_filter

    alerts_cursor = mongo.db.alerts.find(query).sort("timestamp", -1)
    
    # USE THE SERIALIZER IN THE LOOP
    safe_alerts = [serialize_alert(doc) for doc in alerts_cursor]
    
    logger.info(f"Retrieved {len(safe_alerts)} alerts")

    return jsonify(safe_alerts), 200

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("DisasterWatch Backend Server Starting")
    logger.info("=" * 60)
    app.run(debug=True, port=5000)
