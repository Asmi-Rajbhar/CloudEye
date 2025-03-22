document.getElementById('predictionForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent form from reloading the page

    const location = document.getElementById('location').value;
    fetchWeatherData(location);
});

function fetchWeatherData(location) {
    const apiKey = 'f4fb60c4cf28d30ba8661272f0a35341';
    const apiUrl = `https://api.openweathermap.org/data/2.5/weather?q=${location}&appid=${apiKey}&units=metric`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`City not found: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('temperature').textContent = data.main.temp;
            document.getElementById('humidity').textContent = data.main.humidity;
            document.getElementById('windSpeed').textContent = data.wind.speed;
            document.getElementById('pressure').textContent = data.main.pressure;
            document.getElementById('precipitation').textContent = data.rain ? data.rain['1h'] : 0;

            // Prepare weather data to send to the Flask backend for prediction
            const weatherData = {
                precipitation: data.rain ? data.rain['1h'] : 0,
                relative_humidity: data.main.humidity,
                wind_speed: data.wind.speed,
                apparent_temperature: data.main.feels_like
            };

            // Call the Flask API to get cloudburst prediction
            predictCloudburst(weatherData);
        })
        .catch(error => {
            console.error('Error fetching weather data:', error);
            document.getElementById('predictionResult').textContent = `Error: ${error.message}`;
        });
}

function predictCloudburst(weatherData) {
    // Update this URL if your Flask app is running on a different port or domain
    const apiUrl = 'http://127.0.0.1:5000/predict';

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(weatherData)
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('predictionResult').textContent = `Cloudburst Risk: ${data.cloudburst_chance}%`;
        })
        .catch(error => {
            console.error('Error fetching prediction:', error);
            document.getElementById('predictionResult').textContent = `Error: ${error.message}`;
        });
}
