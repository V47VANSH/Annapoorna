import requests

# --- API KEY ---
TOMORROW_API_KEY = "REDACTED-TOMORROW-IO-KEY"

def fetch_tomorrow_io(lat: float, lon: float) -> dict:
    """
    Fetches real-time weather data from Tomorrow.io for a given latitude and longitude.
    """
    url = (
        f"https://api.tomorrow.io/v4/weather/realtime"
        f"?location={lat},{lon}&apikey={TOMORROW_API_KEY}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        values = response.json().get("data", {}).get("values", {})
        
        return {
            "temperature": values.get("temperature", "N/A"),
            "humidity": values.get("humidity", "N/A"),
            "rain_probability": values.get("precipitationProbability", "N/A"),
            "soil_moisture": values.get("soilMoistureVolumetric0To10cm", "N/A"),
            "evapotranspiration": values.get("evapotranspiration", "N/A")
        }

    except Exception as e:
        return {"error": f"Tomorrow.io error: {str(e)}"}

def get_weather_info(lat: float, lon: float) -> str:
    """
    Generates a formatted weather report using Tomorrow.io data.
    """
    weather = fetch_tomorrow_io(lat, lon)

    report_lines = ["\nCombined Weather Insights for the field location are following:\n"]

    if "error" not in weather:
        report_lines.append("🛰️ Tomorrow.io:")
        report_lines.append(f"- Temp: {weather['temperature']}°C")
        report_lines.append(f"- Humidity: {weather['humidity']}%")
        report_lines.append(f"- Rain Probability: {weather['rain_probability']}%")

        if weather['soil_moisture'] != "N/A":
            report_lines.append(f"- Soil Moisture: {weather['soil_moisture']} m³/m³")
        if weather['evapotranspiration'] != "N/A":
            report_lines.append(f"- Evapotranspiration: {weather['evapotranspiration']} mm/day")

    else:
        report_lines.append(f"\n⚠️ {weather['error']}")

    return "\n".join(report_lines)
