document.getElementById('predictionForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent form from reloading the page

    const location = document.getElementById('location').value;  // Get the location input
    console.log("Fetching weather data for:", location);  // Log the location to the console

    // Call the function to fetch weather data and make predictions
    fetchWeatherData(location);
});

function fetchWeatherData(location) {
    const apiKey = 'f4fb60c4cf28d30ba8661272f0a35341';  // OpenWeather API key
    const apiUrl = `https://api.openweathermap.org/data/2.5/weather?q=${location}&appid=${apiKey}&units=metric`;

    // Fetch weather data from OpenWeather API
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`City not found: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Fetched data:", data);  // Log the fetched data to check it
            // Update the UI with fetched weather data
            document.getElementById('temperature').textContent = data.main.temp;
            document.getElementById('humidity').textContent = data.main.humidity;
            document.getElementById('windSpeed').textContent = data.wind.speed;
            document.getElementById('pressure').textContent = data.main.pressure;
            document.getElementById('precipitation').textContent = data.rain ? data.rain['1h'] : 0;

            // Call prediction function (you can customize this logic)
            makePrediction(data);
        })
        .catch(error => {
            console.error('Error fetching weather data:', error);
            document.getElementById('predictionResult').textContent = `Error: ${error.message}`;
        });
}

function makePrediction(weatherData) {
    const precipitation = weatherData.rain ? weatherData.rain['1h'] : 0;
    let predictionMessage = '';

    if (precipitation > 50) {
        predictionMessage = 'High risk of cloudburst. Stay Alert!';
    } else if (precipitation > 20) {
        predictionMessage = 'Moderate risk of cloudburst. Monitor weather conditions closely.';
    } else {
        predictionMessage = 'Low risk of cloudburst.';
    }

    document.getElementById('predictionResult').textContent = predictionMessage;
}
