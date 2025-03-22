document.getElementById("predict-btn").addEventListener("click", async () => {
    const city = document.getElementById("city").value.trim();
    const resultDiv = document.getElementById("result");

    if (!city) {
        alert("Please enter a city name.");
        return;
    }

    resultDiv.innerHTML = "Loading...";

    try {
        const response = await fetch(`http://localhost:5000/predict?city=${city}`); // Replace with your backend API endpoint
        const data = await response.json();

        if (response.ok) {
            const cloudburstPrediction = data.prediction ? 'Yes' : 'No';
            const apparentTemperature = data.apparentTemperature;
            const relativeHumidity = data.relativeHumidity;
            const precipitation = data.precipitation;

            resultDiv.innerHTML = `
                <h2>Prediction Results</h2>
                <p><strong>Cloudburst Prediction:</strong> ${cloudburstPrediction}</p>
                <p><strong>Apparent Temperature:</strong> ${apparentTemperature} °C</p>
                <p><strong>Relative Humidity:</strong> ${relativeHumidity}%</p>
                <p><strong>Precipitation in Last Hour:</strong> ${precipitation} mm</p>
            `;
        } else {
            resultDiv.innerHTML = `<p>Error: ${data.message}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p>An error occurred: ${error.message}</p>`;
    }
});
