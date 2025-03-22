document.getElementById('prediction-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Get user input values
    const precipitation = document.getElementById('precipitation').value;
    const cloudCoverMean = document.getElementById('cloud_cover_mean').value;
    const relativeHumidity = document.getElementById('relative_humidity').value;
    const windSpeed = document.getElementById('wind_speed').value;
    const apparentTemperature = document.getElementById('apparent_temperature').value;

    // Create a data object
    const data = {
        precipitation: parseFloat(precipitation),
        cloud_cover_mean: parseInt(cloudCoverMean),
        relative_humidity: parseInt(relativeHumidity),
        wind_speed: parseFloat(windSpeed),
        apparent_temperature: parseFloat(apparentTemperature),
    };

    // Make a request to the backend API
    fetch('http://127.0.0.1:5000/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        // Display the prediction result
        if (result.cloudburst_chance !== undefined) {
            document.getElementById('result').innerHTML = 
                `There is a ${result.cloudburst_chance.toFixed(2)}% chance of a cloudburst.`;
        } else {
            document.getElementById('result').innerHTML = 
                `Error: ${result.error}`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('result').innerHTML = 'Error predicting cloudburst chance.';
    });
});
