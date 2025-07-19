import requests

# --- API KEYS ---
OPENWEATHER_API_KEY = "REDACTED-OPENWEATHER-KEY"
WEATHERBIT_API_KEY = "REDACTED-WEATHERBIT-KEY"
TOMORROW_API_KEY = "REDACTED-TOMORROW-IO-KEY"

# --- FETCH FUNCTIONS ---
def fetch_openweather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"].capitalize()
        }
    except Exception as e:
        return {"error": f"OpenWeatherMap error: {str(e)}"}

def fetch_weatherbit(lat, lon):
    try:
        url = f"https://api.weatherbit.io/v2.0/current?lat={lat}&lon={lon}&key={WEATHERBIT_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["data"][0]
        return {
            "temperature": data["temp"],
            "humidity": data["rh"],
            "solar_rad": data.get("solar_rad", "N/A"),
            "soil_temp": data.get("soil_temp", "N/A"),
            "description": data["weather"]["description"]
        }
    except Exception as e:
        return {"error": f"Weatherbit error: {str(e)}"}

def fetch_tomorrow_io(lat, lon):
    try:
        url = f"https://api.tomorrow.io/v4/weather/realtime?location={lat},{lon}&apikey={TOMORROW_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get("data", {}).get("values", {})
        return {
            "temperature": data.get("temperature", "N/A"),
            "humidity": data.get("humidity", "N/A"),
            "rain_probability": data.get("precipitationProbability", "N/A"),
            "soil_moisture": data.get("soilMoistureVolumetric0To10cm", "N/A"),
            "evapotranspiration": data.get("evapotranspiration", "N/A")
        }
    except Exception as e:
        return {"error": f"Tomorrow.io error: {str(e)}"}

# --- MAIN FUNCTION (Agent-friendly) ---
def get_weather_info(lat, lon) -> str:
    tomorrow = fetch_tomorrow_io(lat, lon)

    report = f"\nCombined Weather Insights for the field location are following:\n"

    if "error" not in tomorrow:
        report += f"""
🛰️ Tomorrow.io:
- Temp: {tomorrow['temperature']}°C
- Humidity: {tomorrow['humidity']}%
- Rain Probability: {tomorrow['rain_probability']}%
{"- Soil Moisture: "+tomorrow['soil_moisture']+" m³/m³" if tomorrow['soil_moisture']!="N/A" else ""}
{"- Evapotranspiration: "+tomorrow['evapotranspiration']+" mm/day" if tomorrow['evapotranspiration']!="N/A" else ""}"""

    # Add any API errors
    for api_response in [tomorrow]:
        if "error" in api_response:
            report += f"\n\n⚠️ {api_response['error']}"

    return report