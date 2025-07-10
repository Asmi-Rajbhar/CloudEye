from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import sqlite3
import joblib
import pandas as pd
import requests
from flask_cors import CORS
from math import radians, sin, cos, sqrt, atan2

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load the trained model
model = joblib.load("realtimecloudburstmodel.joblib")

# SQLite Database File
DB_PATH = "cloudburst.db"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

# Initialize database connection
def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Ensure 'UserData' table exists
def create_user_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS UserData (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        Username TEXT NOT NULL,
                        EmailId TEXT UNIQUE NOT NULL,
                        City TEXT NOT NULL,
                        Address TEXT NOT NULL,
                        Latitude REAL NOT NULL,
                        Longitude REAL NOT NULL)''')
    conn.commit()
    conn.close()

# Function to fetch weather data using coordinates
def get_weather_data(lat, lon):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if response is not successful
        
        data = response.json()
        weather_data = {
            "precipitation": data.get('rain', {}).get('1h', 0),
            "apparent_temperature": data['main']['feels_like'],
            "cloud_cover_mean (%)": data['clouds']['all'],
            "wind_speed_10m": data['wind']['speed'],
            "relative_humidity_2m_mean (%)": data['main']['humidity'],
            "location": data.get('name', 'Unknown')
        }
        return pd.DataFrame([weather_data]), weather_data

    except Exception as e:
        raise Exception(f"Failed to fetch weather data: {str(e)}")

def find_safe_locations(current_lat, current_lon, radius_km=30):
    """Find safe locations within a given radius"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT City, Address, Latitude, Longitude FROM UserData')
        locations = cursor.fetchall()
        cursor.close()
        conn.close()

        safe_locations = []
        for city, address, lat, lon in locations:
            distance = calculate_distance(current_lat, current_lon, lat, lon)
            
            if distance <= radius_km and distance > 0:
                weather_df, weather_data = get_weather_data(lat, lon)
                prediction = model.predict(weather_df)[0]
                
                if prediction == 0 and weather_data['precipitation'] < 5:
                    safe_locations.append({
                        'city': city,
                        'address': address,
                        'distance': round(distance, 2),
                        'weather': weather_data
                    })
        
        return sorted(safe_locations, key=lambda x: x['distance'])[:5]
    except Exception as e:
        print(f"Error finding safe locations: {e}")
        return []

# Home Route (Fix for 404 Error)
@app.route('/')
def home():
    return jsonify({'message': 'Cloudburst Prediction API is running'}), 200

# Route for cloudburst prediction with safe locations
@app.route('/predict', methods=['GET'])
def predict():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({'message': 'Latitude and longitude parameters are required'}), 400

    try:
        weather_df, weather_data = get_weather_data(lat, lon)
        prediction = model.predict(weather_df)
        
        response = {
            'prediction': int(prediction[0]),
            'location': weather_data['location'],
            'current_weather': {
                'temperature': float(weather_data['apparent_temperature']),
                'humidity': int(weather_data['relative_humidity_2m_mean (%)']),
                'precipitation': float(weather_data['precipitation']),
                'wind_speed': float(weather_data['wind_speed_10m']),
                'cloud_cover': int(weather_data['cloud_cover_mean (%)'])
            }
        }

        # If there's a risk of cloudburst, find safe locations
        if prediction[0] == 1 or weather_data['precipitation'] > 10:
            safe_locations = find_safe_locations(float(lat), float(lon))
            response['safe_locations'] = safe_locations

        return jsonify(response)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Route for user signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    city = data.get('city')
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not all([username, email, city, address, latitude, longitude]):
        return jsonify({'message': 'All fields are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure table exists
        create_user_table()

        cursor.execute(
            'INSERT INTO UserData (Username, EmailId, City, Address, Latitude, Longitude) VALUES (?, ?, ?, ?, ?, ?)',
            (username, email, city, address, latitude, longitude)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'User signed up successfully'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Email already exists!'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    create_user_table()
    app.run(debug=True, port=5001)
