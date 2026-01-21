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

app = Flask(__name__)

# --- 1. CONFIGURATION & CONSTANTS ---
app.config["MONGO_URI"] = "mongodb://localhost:27017/my_database"
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-this" 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=7)

# Twilio Config
app.config['TWILIO_ACCOUNT_SID'] = 'ACOUNT_SID'
app.config['TWILIO_AUTH_TOKEN'] = 'AUTH_TOKEN'
app.config['TWILIO_NUMBER'] = 'TWILIO_NO_SENDING' 

# Logic Constants (Mock Values / Settings)
CONSTANTS = {
    "SMS_RADIUS_KM": 200,          
    "DUPLICATE_CHECK_RADIUS_KM": 100, # Radius to check for existing alerts
    "DUPLICATE_TIME_WINDOW_HOURS": 12, # Time window to suppress new SMS
    "DEFAULT_LAT": 20.5937,        # Center of India Lat
    "DEFAULT_LNG": 78.9629,        # Center of India Lng
    "USER_AGENT": "DisasterWatchApp/1.0"
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
            return {
                "lat": float(data[0]['lat']),
                "lng": float(data[0]['lon'])
            }
        return {"lat": CONSTANTS["DEFAULT_LAT"], "lng": CONSTANTS["DEFAULT_LNG"]}
        
    except Exception as e:
        print(f"Geocoding error: {e}")
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
        return {"status": "success", "sid": message.sid}
    except TwilioRestException as e:
        print(f"Twilio Error for {formatted_number}: {e}")
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
                    print(f" SMS Suppressed: Similar alert found {distance:.2f}km away.")
                    return False # Found a match, DO NOT send SMS

        return True # No matching alert found, proceed with SMS

    except Exception as e:
        print(f"Error in suppression logic: {e}")
        return True # Fail-safe: Send SMS if check fails

def broadcast_sms_to_users(alert_data):
    """Iterates users and sends SMS if within radius."""
    try:
        users = mongo.db.users.find({})
        count = 0
        alert_point = (alert_data['coordinates']['lat'], alert_data['coordinates']['lng'])

        for user in users:
            user_loc = user.get('location', {})
            user_coords = user_loc.get('coordinates')
            
            if user_coords and 'lat' in user_coords:
                user_point = (user_coords['lat'], user_coords['lng'])
                
                # Check User Radius
                if geodesic(alert_point, user_point).km <= CONSTANTS["SMS_RADIUS_KM"]:
                    phone = user.get("phone")
                    if phone:
                        send_twilio_sms(phone, alert_data['title'], alert_data['message'])
                        count += 1
        
        print(f" SMS Broadcast Complete: Sent to {count} users.")
        return True
    except Exception as e:
        print(f" SMS Broadcast Failed: {e}")
        return False

# --- 3. ROUTES ---

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    users = mongo.db.users

    if users.find_one({"email": data['email']}) or users.find_one({"phone": data['phone']}):
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
    access_token = create_access_token(identity=str(result.inserted_id))
    created_user = users.find_one({"_id": result.inserted_id})
    
    return jsonify({ "token": access_token, "user": user_serializer(created_user) }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = mongo.db.users
    user = users.find_one({"email": data['email']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({ "token": access_token, "user": user_serializer(user) }), 200
    
    return jsonify({"msg": "Invalid email or password"}), 401

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    if user:
        return jsonify({"user": user_serializer(user)}), 200
    return jsonify({"msg": "User not found"}), 404

@app.route('/api/user/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
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

    updated_user = users.find_one({"_id": ObjectId(user_id)})
    return jsonify(user_serializer(updated_user)), 200

# --- UPDATED ALERT CREATION LOGIC ---

@app.route('/api/alerts', methods=['POST'])
@jwt_required()
def create_alert():
    current_user_id = get_jwt_identity()
    data = request.json
    
    required = ['title', 'message', 'type', 'severity', 'location']
    if not all(k in data for k in required):
        return jsonify({"msg": "Missing required fields"}), 400

    #  Resolve Coordinates
    alert_coords = data.get('coordinates')
    if not alert_coords or alert_coords.get('lat') == 0:
        # Fallback if frontend failed
        # Note: data['location'] comes as "City, State" from frontend
        parts = data['location'].split(',')
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else ""
        alert_coords = get_coordinates(city, state)
    
    #  Check Logic: Should we send SMS?
    trigger_sms = should_trigger_sms(alert_coords)

    #  Create Alert Object
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
        "sms_sent": trigger_sms # <--- NEW PROPERTY FLAG
    }

    #  Save to DB (Always save, even if SMS suppressed) SEE WE CAN ALSO DECIDE TO NOT SAVE 
    result = mongo.db.alerts.insert_one(new_alert)
    
    # Broadcast SMS (Only if trigger is True)
    if trigger_sms:
        broadcast_sms_to_users(new_alert)
    else:
        print(" Alert Saved, but SMS suppressed (Duplicate detected).")

    # 6. Return Response
    new_alert['id'] = str(result.inserted_id)
    new_alert['user_id'] = str(new_alert['user_id'])
    del new_alert['_id']
    
    return jsonify(new_alert), 201

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    time_filter = request.args.get('time', '30d')
    type_filter = request.args.get('type', 'all')
    
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
    
    alerts = []
    for doc in alerts_cursor:
        doc['id'] = str(doc['_id'])
        doc['user_id'] = str(doc['user_id'])
        doc['sms_sent'] = doc.get('sms_sent', False) # Handle old alerts lacking this field
        del doc['_id']
        alerts.append(doc)

    return jsonify(alerts), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)