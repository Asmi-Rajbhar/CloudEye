from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import pandas as pd
import joblib
import requests
import numpy as np
from flask_cors import CORS
from datetime import datetime, timedelta
import pytz
import random

load_dotenv()
app = Flask(__name__)
CORS(app)

# Load the trained CatBoost model
model = joblib.load("realtimecloudburstmodel.joblib")

# Function to fetch weather data from OpenWeather API
def get_weather_data(city_name):
    api_key = os.getenv("OPENWEATHER_API_KEY")  # Your OpenWeather API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error fetching data from OpenWeather: {response.json().get('message')}")

    data = response.json()

    # Extract necessary fields for prediction
    weather_data = {
        "precipitation": data.get('rain', {}).get('1h', 0),
        "apparent_temperature": data['main']['feels_like'],
        "cloud_cover_mean (%)": data['clouds']['all'],
        "wind_speed_10m": data['wind']['speed'],
        "relative_humidity_2m_mean (%)": data['main']['humidity'],
    }

    # Add pressure for chart visualization
    weather_data["pressure"] = data['main']['pressure']

    return weather_data, pd.DataFrame([weather_data])

@app.route('/predict', methods=['GET'])
def predict():
    city = request.args.get('city')
    if not city:
        return jsonify({'message': 'City parameter is required'}), 400

    try:
        # Get real-time weather data
        weather_dict, weather_df = get_weather_data(city)

        # Predict cloudburst using the CatBoost model
        prediction = model.predict(weather_df)

        # Get current time in local timezone (Asia/Kolkata for IST)
        timezone = pytz.timezone('Asia/Kolkata')
        fetched_at = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(timezone).isoformat()

        # Prepare response
        response = {
            'prediction': int(prediction[0]),
            'apparentTemperature': float(weather_df['apparent_temperature'][0]),
            'relativeHumidity': int(weather_df['relative_humidity_2m_mean (%)'][0]),
            'precipitation': float(weather_df['precipitation'][0]),
            'pressure': float(weather_dict['pressure']),
            'windSpeed': float(weather_df['wind_speed_10m'][0]),
            'fetchedAt': fetched_at
        }

        return jsonify(response)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/historical', methods=['GET'])
def historical_data():
    city = request.args.get('city')
    if not city:
        return jsonify({'message': 'City parameter is required'}), 400

    try:
        # In a production app, you would fetch this from a database
        # For this demo, we'll generate simulated historical data
        
        # Get current time
        now = datetime.now()
        
        # Generate time labels for the past 8 hours
        times = []
        temperatures = []
        humidity = []
        pressure = []
        
        # Get current weather as a reference point
        weather_dict, _ = get_weather_data(city)
        current_temp = weather_dict['apparent_temperature']
        current_humidity = weather_dict['relative_humidity_2m_mean (%)']
        current_pressure = weather_dict['pressure']
        
        # Generate historical data with small random variations
        for i in range(8, 0, -1):
            past_time = now - timedelta(hours=i)
            times.append(f"{past_time.hour}:{past_time.minute:02d}")
            
            # Random variations from current values
            temp_variation = random.uniform(-3, 3)
            humidity_variation = random.uniform(-10, 10)
            pressure_variation = random.uniform(-5, 5)
            
            temperatures.append(round(current_temp + temp_variation, 1))
            humidity.append(min(100, max(0, round(current_humidity + humidity_variation))))
            pressure.append(round(current_pressure + pressure_variation, 1))
        
        return jsonify({
            'times': times,
            'temperatures': temperatures,
            'humidity': humidity,
            'pressure': pressure
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/forecast', methods=['GET'])
def forecast_data():
    city = request.args.get('city')
    if not city:
        return jsonify({'message': 'City parameter is required'}), 400

    try:
        # In a production app, you would fetch this from a weather API forecast
        # For this demo, we'll generate simulated forecast data
        
        # Get current time
        now = datetime.now()
        
        # Generate time labels for the next 24 hours (every 3 hours)
        times = []
        precipitation = []
        cloudburst_risk = []
        
        # Get current weather as a reference point
        weather_dict, _ = get_weather_data(city)
        current_precip = weather_dict.get('precipitation', 0)
        
        # Base risk on current conditions
        if current_precip > 5 or weather_dict['relative_humidity_2m_mean (%)'] > 85:
            base_risk = 60  # Higher risk for high humidity or current precipitation
        else:
            base_risk = 20  # Lower base risk
            
        # Generate forecast data
        for i in range(1, 25, 3):
            future_time = now + timedelta(hours=i)
            times.append(f"{future_time.hour}:00")
            
            # Generate precipitation forecast with trend
            # More likely to rain if already raining
            if i <= 6:  # Near-term forecast more related to current conditions
                precip_factor = 0.7 if current_precip > 0 else 0.3
            else:
                precip_factor = 0.5  # Medium-term forecast more random
                
            # Random precipitation with some persistence of current conditions
            precip_value = max(0, current_precip * precip_factor + random.uniform(-1, 3))
            precipitation.append(round(precip_value, 1))
            
            # Cloudburst risk based on precipitation and random factors
            risk_value = min(100, max(0, base_risk + (precip_value * 10) + random.uniform(-15, 15)))
            cloudburst_risk.append(round(risk_value))
        
        return jsonify({
            'times': times,
            'precipitation': precipitation,
            'cloudburstRisk': cloudburst_risk
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)