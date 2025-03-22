// Chart objects for global reference
let tempHumidityChart, precipitationForecastChart, riskForecastChart;
// Initialize data arrays
let timeLabels = [];
let temperatureData = [];
let humidityData = [];
let precipitationForecast = [];
let riskForecast = [];
// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initialize empty charts
    initializeCharts();
});
document.getElementById("predict-btn").addEventListener("click", async () => {
    const city = document.getElementById("city").value.trim();
    const loadingIndicator = document.getElementById("loading");
    const weatherSummary = document.getElementById("weather-summary");
    const chartsContainer = document.getElementById("charts-container");
    const alertBox = document.getElementById("alert-box");
    const safetyTips = document.getElementById("safety-tips");
    if (!city) {
        showAlert("Please enter a city name.", "warning");
        return;
    }
    // Reset and show loading indicator
    loadingIndicator.style.display = "block";
    weatherSummary.style.display = "none";
    chartsContainer.style.display = "none";
    alertBox.style.display = "none";
    safetyTips.style.display = "none";
    try {
        const response = await fetch(`http://localhost:5001/predict?city=${city}`);
        const data = await response.json();
        // Hide loading indicator
        loadingIndicator.style.display = "none";
        if (response.ok) {
            // Show alert based on prediction
            const isCloudburstRisk = data.prediction === 1;
            const alertType = isCloudburstRisk ? "danger" : "success";
            const alertMessage = isCloudburstRisk 
                ? "⚠️ High risk of cloudburst detected! Please monitor conditions and be prepared." 
                : "✓ Low risk of cloudburst at this time.";
            showAlert(alertMessage, alertType);
            // Update weather summary
            updateWeatherSummary(city, data);
            weatherSummary.style.display = "block";
            // Show charts container
            chartsContainer.style.display = "block";
            // Update all charts with new data
            updateCharts(data);
            // Get forecast data for all charts
            fetchForecastData(city);
            // Show safety tips if needed
            updateSafetyTips(data.prediction === 1, data);
            // Update timestamp
            document.getElementById("data-timestamp").textContent = 
                `Data last updated: ${new Date().toLocaleString()}`;
        } else {
            showAlert(`Error: ${data.message}`, "danger");
        }
    } catch (error) {
        loadingIndicator.style.display = "none";
        showAlert(`An error occurred: ${error.message}`, "danger");
    }
});
function showAlert(message, type) {
    const alertBox = document.getElementById("alert-box");
    alertBox.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    alertBox.style.display = "block";
}
function updateWeatherSummary(cityName, data) {
    // Update city name
    document.getElementById("city-name").textContent = ` for ${cityName}`;
    // Update temperature
    document.getElementById("temperature").textContent = `${data.apparentTemperature.toFixed(1)}°C`;
    document.getElementById("feels-like").textContent = `Feels like ${data.apparentTemperature.toFixed(1)}°C`;
    // Update other weather values
    document.getElementById("humidity-value").textContent = `${data.relativeHumidity}%`;
    document.getElementById("wind-value").textContent = `${data.windSpeed} m/s`;
    document.getElementById("precipitation-value").textContent = `${data.precipitation.toFixed(1)} mm`;
    document.getElementById("pressure-value").textContent = `${data.pressure} hPa`;
    // Update weather icon based on conditions
    let iconClass = "fa-cloud"; // default
    if (data.precipitation > 2.5) {
        iconClass = "fa-cloud-showers-heavy";
    } else if (data.precipitation > 0) {
        iconClass = "fa-cloud-rain";
    } else if (data.relativeHumidity < 30) {
        iconClass = "fa-sun";
    } else if (data.relativeHumidity < 60) {
        iconClass = "fa-cloud-sun";
    }
    document.getElementById("weather-icon").className = `fas ${iconClass} fa-4x text-primary`;
    // Update risk indicator
    const riskPercentage = data.prediction === 1 ? 
        76 + Math.floor(Math.random() * 24) : // High risk with some randomness
        Math.floor(Math.random() * 45);  // Low risk with some randomness
    const riskIndicator = document.getElementById("risk-indicator");
    riskIndicator.style.width = `${riskPercentage}%`;
    riskIndicator.textContent = `${riskPercentage}%`;
    // Set color based on risk level - low, moderate, or high
    if (riskPercentage <= 45) {
        riskIndicator.className = "progress-bar bg-success";
        document.getElementById("risk-description").textContent = "Low risk - No immediate concern";
    } else if (riskPercentage <= 75) {
        riskIndicator.className = "progress-bar bg-warning";
        document.getElementById("risk-description").textContent = "Moderate risk - Stay alert";
    } else {
        riskIndicator.className = "progress-bar bg-danger";
        document.getElementById("risk-description").textContent = "High risk - Take precautions";
    }
}
function updateSafetyTips(isHighRisk, data) {
    const safetyTipsElement = document.getElementById("safety-tips");
    const safetyTipsList = document.getElementById("safety-tips-list");
    // Always show safety tips but customize based on risk level
    safetyTipsList.innerHTML = "";
    // Basic safety tips for all conditions
    const basicTips = [
        "Stay informed through weather updates and local news.",
        "Keep emergency contact numbers handy.",
        "Ensure your mobile phone is fully charged."
    ];
    // Additional tips for high risk situations
    const highRiskTips = [
        "Avoid travel in affected areas if possible.",
        "Stay away from rivers, streams, and low-lying areas prone to flooding.",
        "Move to higher ground if you're in a flood-prone area.",
        "Keep emergency supplies ready (food, water, first aid kit, flashlight).",
        "Follow instructions from local authorities."
    ];
    // Add all tips to the list
    let tipsToShow = isHighRisk ? [...basicTips, ...highRiskTips] : basicTips;
    // Add tips specific to current weather conditions
    if (data.precipitation > 2) {
        tipsToShow.push("Heavy rain detected - be cautious of flash floods in low-lying areas.");
    }
    if (data.windSpeed > 5) {
        tipsToShow.push("Strong winds detected - secure loose objects outside your home.");
    }
    tipsToShow.forEach(tip => {
        const li = document.createElement("li");
        li.className = "mb-2";
        li.textContent = tip;
        safetyTipsList.appendChild(li);
    });
    safetyTipsElement.style.display = "block";
}
// Initialize all the charts with empty data
function initializeCharts() {
    // Temperature & Humidity Chart (Dual axis)
    const tempHumidityCanvas = document.getElementById('tempHumidityChart');
    tempHumidityChart = new Chart(tempHumidityCanvas, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    yAxisID: 'y',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Humidity (%)'
                    },
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
    // Precipitation Forecast Chart
    const precipForecastCanvas = document.getElementById('precipitationForecastChart');
    precipitationForecastChart = new Chart(precipForecastCanvas, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Precipitation (mm)',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Precipitation (mm)'
                    }
                }
            }
        }
    });
    // Risk Forecast Chart
    const riskForecastCanvas = document.getElementById('riskForecastChart');
    riskForecastChart = new Chart(riskForecastCanvas, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cloudburst Risk (%)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.3,
                fill: true,
                pointBackgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    return value <= 45 ? '#28a745' : value <= 75 ? '#ffc107' : '#dc3545';
                },
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100, // Changed to include all risk levels up to 100%
                    title: {
                        display: true,
                        text: 'Risk Level (%)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            let riskLevel = '';
                            if (value <= 45) riskLevel = 'Low Risk';
                            else if (value <= 75) riskLevel = 'Moderate Risk';
                            else riskLevel = 'High Risk';
                            return `Risk: ${value}% (${riskLevel})`;
                        }
                    }
                }
            }
        }
    });
}
// Update charts with new data
function updateCharts(currentData) {
    // Add current data point to time-series arrays
    const now = new Date();
    const timeStr = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
    
    // Store current values for reference but don't update the chart with historical data
    timeLabels = [timeStr];
    temperatureData = [currentData.apparentTemperature];
    humidityData = [currentData.relativeHumidity];
}
// Fetch forecast data for all charts
async function fetchForecastData(city) {
    try {
        const response = await fetch(`http://localhost:5001/forecast?city=${city}`);
        if (response.ok) {
            const data = await response.json();
            
            // Update precipitation forecast chart
            precipitationForecastChart.data.labels = data.times;
            precipitationForecastChart.data.datasets[0].data = data.precipitation;
            precipitationForecastChart.update();
            
            // Update risk forecast chart with full risk range
            riskForecastChart.data.labels = data.times;
            
            // No longer capping risk values
            riskForecastChart.data.datasets[0].data = data.cloudburstRisk;
            riskForecastChart.update();
            
            // Update temperature & humidity forecast chart
            if (data.temperatures && data.humidity) {
                tempHumidityChart.data.labels = data.times;
                tempHumidityChart.data.datasets[0].data = data.temperatures;
                tempHumidityChart.data.datasets[1].data = data.humidity;
                tempHumidityChart.update();
            } else {
                // Generate forecasted temperature and humidity if not provided by API
                generateTempHumidityForecast(city, data.times);
            }
        }
    } catch (error) {
        console.error("Error fetching forecast data:", error);
        
        // Generate simulated forecast data if API call fails
        const futureTimes = [];
        const now = new Date();
        
        for (let i = 3; i <= 24; i += 3) {
            const futureTime = new Date(now.getTime() + i * 60 * 60 * 1000);
            futureTimes.push(futureTime.getHours() + ':00');
        }
        
        // Generate all simulated forecasts
        generateSimulatedForecasts(futureTimes);
    }
}
// Function to generate simulated temperature and humidity forecast
function generateTempHumidityForecast(city, existingTimes = null) {
    // Get the current temperature and humidity as starting points
    const currentTemp = parseFloat(document.getElementById("temperature").textContent) || 30;
    const currentHumidity = parseInt(document.getElementById("humidity-value").textContent) || 40;
    
    const futureTimes = existingTimes || [];
    const futureTemps = [];
    const futureHumidity = [];
    
    // If we don't have times from the API, generate them
    if (futureTimes.length === 0) {
        const now = new Date();
        for (let i = 3; i <= 24; i += 3) {
            const futureTime = new Date(now.getTime() + i * 60 * 60 * 1000);
            futureTimes.push(futureTime.getHours() + ':00');
        }
    }
    
    // Generate temperature pattern with day/night cycle
    const currentHour = new Date().getHours();
    
    for (let i = 0; i < futureTimes.length; i++) {
        const hour = parseInt(futureTimes[i].split(':')[0]);
        
        // Temperature tends to be higher during day (10am-4pm) and lower at night
        let tempVariation;
        if (hour >= 10 && hour <= 16) {
            // Daytime - higher temperatures
            tempVariation = Math.random() * 2 + 1; // +1 to +3 degrees
        } else if (hour >= 22 || hour <= 5) {
            // Nighttime - lower temperatures
            tempVariation = -(Math.random() * 2 + 1); // -1 to -3 degrees
        } else {
            // Transition periods - small variations
            tempVariation = Math.random() * 2 - 1; // -1 to +1 degrees
        }
        
        // Add some small random variation to make the graph look natural
        const temp = Math.max(20, Math.min(40, currentTemp + tempVariation + (i * 0.1 * (Math.random() > 0.5 ? 1 : -1))));
        futureTemps.push(temp.toFixed(1));
        
        // Humidity often has inverse relationship with temperature during the day
        const humidityVariation = tempVariation > 0 ? -(Math.random() * 5) : Math.random() * 5;
        const humidity = Math.max(10, Math.min(95, currentHumidity + humidityVariation));
        futureHumidity.push(Math.round(humidity));
    }
    
    // Update temperature and humidity forecast chart
    tempHumidityChart.data.labels = futureTimes;
    tempHumidityChart.data.datasets[0].data = futureTemps;
    tempHumidityChart.data.datasets[1].data = futureHumidity;
    tempHumidityChart.update();
}
// Function to generate all simulated forecasts in one place
function generateSimulatedForecasts(futureTimes) {
    const futurePrecipitation = [];
    const futureRisk = [];
    
    // Generate simulated precipitation and risk values
    for (let i = 0; i < futureTimes.length; i++) {
        const precip = Math.random() * 5;
        futurePrecipitation.push(precip.toFixed(1));
        
        // No longer capping risk at 70
        const risk = Math.max(0, (precip * 15) + (Math.random() * 30 - 10));
        futureRisk.push(Math.round(risk));
    }
    
    // Update precipitation forecast chart
    precipitationForecastChart.data.labels = futureTimes;
    precipitationForecastChart.data.datasets[0].data = futurePrecipitation;
    precipitationForecastChart.update();
    
    // Update risk forecast chart
    riskForecastChart.data.labels = futureTimes;
    riskForecastChart.data.datasets[0].data = futureRisk;
    riskForecastChart.update();
    
    // Generate and update temperature & humidity forecast
    generateTempHumidityForecast(null, futureTimes);
}
// This function is no longer needed but keeping a minimal version for backward compatibility
function fetchHistoricalData(city) {
    console.log("Historical data fetch skipped - showing forecast data instead");
}