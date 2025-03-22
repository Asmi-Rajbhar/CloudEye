from flask import Flask, request, jsonify
import pandas as pd
import joblib
import requests
from flask_cors import CORS  # Import CORS to handle cross-origin requests
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load the trained CatBoost model
model = joblib.load("realtimecloudburstmodel.joblib")  # Load your model using joblib

# Function to fetch weather data from OpenWeather API
def get_weather_data(city_name):
    api_key = "f4fb60c4cf28d30ba8661272f0a35341"  # Your OpenWeather API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    response = requests.get(url)

    # Log the response for debugging
    logging.debug(f"API response: {response.json()}")

    if response.status_code != 200:
        raise Exception(f"Error fetching data from OpenWeather: {response.json().get('message')}")

    data = response.json()

    # Extract necessary fields for prediction, adding more robustness for missing fields
    weather_data = {
        "precipitation": data.get('rain', {}).get('1h', 0),  # Rain in mm (use 0 if not available)
        "apparent_temperature": data['main'].get('feels_like', None),  # Feels-like temperature in Celsius
        "cloud_cover_mean (%)": data['clouds'].get('all', None),  # Cloud cover percentage
        "wind_speed_10m": data['wind'].get('speed', None),  # Wind speed at 10 meters in m/s
        "relative_humidity_2m_mean (%)": data['main'].get('humidity', None),  # Humidity percentage
    }

    # Check if any field is None and raise an error if crucial fields are missing
    if None in weather_data.values():
        raise Exception(f"Missing crucial weather data fields: {weather_data}")

    return pd.DataFrame([weather_data])

@app.route('/predict', methods=['GET'])
def predict():
    city = request.args.get('city')
    if not city:
        return jsonify({'message': 'City parameter is required'}), 400

    try:
        # Get real-time weather data
        weather_df = get_weather_data(city)

        # Log the dataframe for debugging
        logging.debug(f"Weather DataFrame: {weather_df}")

        # Predict cloudburst using the updated weather data
        prediction = model.predict(weather_df)

        # Convert to Python's native data types to avoid serialization issues
        response = {
            'prediction': int(prediction[0]),  # Convert NumPy int64 to Python int
            'apparentTemperature': float(weather_df['apparent_temperature'][0]),  # float
            'relativeHumidity': int(weather_df['relative_humidity_2m_mean (%)'][0]),  # int
            'precipitation': float(weather_df['precipitation'][0])  # float
        }

        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in prediction: {e}")
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
