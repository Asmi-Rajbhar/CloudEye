from flask import Flask, request, jsonify
import joblib
import pandas as pd
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the trained model
model = joblib.load('cloudburst_model.joblib')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from the request
        data = request.get_json()

        # Input validation
        required_keys = ['precipitation', 'cloud_cover_mean', 'relative_humidity', 'wind_speed', 'apparent_temperature']
        for key in required_keys:
            if key not in data:
                return jsonify({'error': f'Missing key: {key}'}), 400

        # Convert input data into a DataFrame
        input_data = pd.DataFrame({
            'precipitation': [data['precipitation']],
            'cloud_cover_mean (%)': [data['cloud_cover_mean']],
            'relative_humidity_2m_mean (%)': [data['relative_humidity']],
            'wind_speed_10m': [data['wind_speed']],
            'apparent_temperature': [data['apparent_temperature']],
        })

        # Predict cloudburst probability
        prediction_proba = model.predict_proba(input_data)

        cloudburst_chance = prediction_proba[0][1] * 100  # Convert to percentage

        return jsonify({'cloudburst_chance': cloudburst_chance})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
