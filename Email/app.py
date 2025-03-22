from flask import Flask, request, jsonify, render_template  # Import render_template
import sqlite3  # Built-in SQLite module
import joblib
import pandas as pd
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the trained model
model = joblib.load("realtimecloudburstmodel.joblib")

# Initialize database and create table if not exists
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        city TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# Route for the homepage to serve index.html
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')  # Render the index.html file

# Function to fetch weather data
def get_weather_data(city_name):
    api_key = "f4fb60c4cf28d30ba8661272f0a35341"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    response = requests.get(url)

    # Log the entire API response for debugging
    print(f"API Response for {city_name}: {response.json()}")  # Print the raw response

    if response.status_code != 200:
        raise Exception(f"Error fetching data from OpenWeather: {response.json().get('message')}")

    data = response.json()
    weather_data = {
        "precipitation": data.get('rain', {}).get('1h', 0),  # Fetch precipitation data for the last 1 hour
        "apparent_temperature": data['main']['feels_like'],
        "cloud_cover_mean (%)": data['clouds']['all'],
        "wind_speed_10m": data['wind']['speed'],
        "relative_humidity_2m_mean (%)": data['main']['humidity'],
    }
    return pd.DataFrame([weather_data])


# Route for cloudburst prediction
@app.route('/predict', methods=['GET'])
def predict():
    city = request.args.get('city')
    if not city:
        return jsonify({'message': 'City parameter is required'}), 400

    try:
        weather_df = get_weather_data(city)
        prediction = model.predict(weather_df)
        response = {
            'prediction': int(prediction[0]),
            'apparentTemperature': float(weather_df['apparent_temperature'][0]),
            'relativeHumidity': int(weather_df['relative_humidity_2m_mean (%)'][0]),
            'precipitation': float(weather_df['precipitation'][0])
        }
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

    if not username or not email or not city:
        return jsonify({'message': 'All fields are required'}), 400

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, city) VALUES (?, ?, ?)", (username, email, city))
        conn.commit()
        conn.close()

        return jsonify({'message': 'User signed up successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Initialize the database on startup
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
