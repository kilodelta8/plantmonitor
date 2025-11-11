// --- 1. Element References ---
const gaugeFill = document.getElementById('gauge-fill');
const gaugePercentText = document.getElementById('gauge-percent-text');

const tempValue = document.getElementById('temp-value');
const humidityValue = document.getElementById('humidity-value');
const weatherDesc = document.getElementById('weather-desc');
const weatherRain = document.getElementById('weather-rain');

const manualWaterBtn = document.getElementById('manual-water-btn');
const autoToggle = document.getElementById('auto-toggle');

const lastWateredText = document.getElementById('last-watered-text');
const lastUpdateText = document.getElementById('last-update-text');

// --- 2. Helper Functions ---

/**
 * Updates the conic-gradient gauge.
 * @param {number} percent - The moisture percentage (0-100).
 */
function setGaugeValue(percent) {
    // Clamp value
    const clampedPercent = Math.max(0, Math.min(100, percent));
    
    // Update the gauge fill
    // This creates a conic gradient: blue from 0 to percent, gray from percent to 100
    gaugeFill.style.background = `conic-gradient(
        var(--accent-blue) 0% ${clampedPercent}%, 
        var(--gauge-bg) ${clampedPercent}% 100%
    )`;
    
    // Update the text in the middle
    gaugePercentText.textContent = `${clampedPercent}%`;
}

/**
 * Fetches data from the /data endpoint and updates the entire dashboard.
 */
async function updateDashboard() {
    try {
        // FIX: Changed fetch('/data') to fetch('./data') for robust URL parsing in sandboxed environments.
        const response = await fetch('./data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Update Gauge
        setGaugeValue(data.moisture_percent);

        // Update Sensor Cards
        tempValue.textContent = `${data.temp_c.toFixed(1)}°C`; // toFixed for clean look
        humidityValue.textContent = `${data.humidity.toFixed(1)}%`;

        // Update Weather Card
        weatherDesc.textContent = data.weather_desc;
        weatherRain.textContent = data.weather_rain ? "Rain is Expected" : "No Rain Expected";
        // Bonus: Change icon color based on rain
        const weatherIcon = document.querySelector('.sensor-icon.weather');
        weatherIcon.style.color = data.weather_rain ? 'var(--accent-blue)' : 'var(--accent-green)';

        // Update Status Card
        lastWateredText.textContent = data.last_water;
        lastUpdateText.textContent = data.last_update;

        // Update Control State
        autoToggle.checked = data.auto_watering_enabled;

    } catch (error) {
        console.error("Error fetching dashboard data:", error);
    }
}

// --- 3. Event Listeners ---

/**
 * Handles the click on the "Manual Water" button.
 */
manualWaterBtn.addEventListener('click', async () => {
    console.log("Manual water button clicked.");
    manualWaterBtn.disabled = true; // Prevent double-clicking
    manualWaterBtn.textContent = "Watering...";

    try {
        // FIX: Changed fetch('/water_manual') to fetch('./water_manual').
        const response = await fetch('./water_manual', { method: 'POST' });
        const result = await response.json();
        console.log(result.message);
        
        // Immediately fetch new data to show the "Last Watered" update
        await updateDashboard(); 
        
    } catch (error) {
        console.error("Error triggering manual water:", error);
    } finally {
        // Re-enable the button after 3 seconds
        setTimeout(() => {
            manualWaterBtn.disabled = false;
            manualWaterBtn.innerHTML = '<i class="fa-solid fa-faucet-drip"></i> Manual Water';
        }, 3000);
    }
});

/**
 * Handles changing the "Auto-Watering" toggle switch.
 */
autoToggle.addEventListener('change', async () => {
    console.log("Auto-toggle changed:", autoToggle.checked);
    
    try {
        // FIX: Changed fetch('/toggle_auto') to fetch('./toggle_auto').
        const response = await fetch('./toggle_auto', { method: 'POST' });
        const result = await response.json();
        console.log(result.message);
        
        // Update the toggle to match the server's response
        autoToggle.checked = result.enabled;

    } catch (error) {
        console.error("Error toggling auto-water:", error);
    }
});

// --- 4. Initialization ---

// Set the initial gauge value on page load
// We use the value passed by Flask/Jinja2
setGaugeValue(parseFloat(gaugePercentText.textContent));

// Start polling for new data every 5 seconds
setInterval(updateDashboard, 5000);

console.log("Dashboard initialized. Polling started.");
