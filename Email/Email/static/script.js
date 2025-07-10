document.getElementById("predict-btn").addEventListener("click", async () => {
    const city = document.getElementById("city-input").value.trim();
    const resultDiv = document.getElementById("result");

    if (!city) {
        alert("Please enter a city name.");
        return;
    }

    resultDiv.innerHTML = "Loading...";

    try {
        const response = await fetch(`http://127.0.0.1:5001/predict?city=${city}`);
        const data = await response.json();

        if (response.ok) {
            const cloudburstPrediction = data.prediction ? 'Yes' : 'No';
            resultDiv.innerHTML = `
                <h3>Prediction Results</h3>
                <p><strong>Cloudburst Prediction:</strong> ${cloudburstPrediction}</p>
                <p><strong>Apparent Temperature:</strong> ${data.apparentTemperature} °C</p>
                <p><strong>Relative Humidity:</strong> ${data.relativeHumidity}%</p>
                <p><strong>Precipitation:</strong> ${data.precipitation} mm</p>
            `;
        } else {
            resultDiv.innerHTML = `<p>Error: ${data.message}</p>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p>An error occurred: ${error.message}</p>`;
    }
});

document.getElementById("signup-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const city = document.getElementById("city").value;

    const response = await fetch("http://127.0.0.1:5001/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, city })
    });

    const data = await response.json();
    if (response.ok) {
        alert("Sign up successful!");
    } else {
        alert("Error: " + data.message);
    }
});
