import requests
from typing import Dict, Union

# --- CONSTANTS ---
TOMORROW_API_KEY = "REDACTED-TOMORROW-IO-KEY"
TOMORROW_API_URL = "https://api.tomorrow.io/v4/weather/realtime"

# --- FETCH FUNCTION ---
def fetch_tomorrow_io(lat: float, lon: float) -> Dict[str, Union[str, float]]:
    try:
        params = {
            "location": f"{lat},{lon}",
            "apikey": TOMORROW_API_KEY
        }
        response = requests.get(TOMORROW_API_URL, params=params)
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

# --- MAIN REPORT FUNCTION ---
def get_weather_info(lat: float, lon: float) -> str:
    tomorrow = fetch_tomorrow_io(lat, lon)

    report_lines = ["\nCombined Weather Insights for the field location are following:\n"]

    if "error" not in tomorrow:
        report_lines.append("🛰️ Tomorrow.io:")
        report_lines.append(f"- Temp: {tomorrow['temperature']}°C")
        report_lines.append(f"- Humidity: {tomorrow['humidity']}%")
        report_lines.append(f"- Rain Probability: {tomorrow['rain_probability']}%")
        if tomorrow['soil_moisture'] != "N/A":
            report_lines.append(f"- Soil Moisture: {tomorrow['soil_moisture']} m³/m³")
        if tomorrow['evapotranspiration'] != "N/A":
            report_lines.append(f"- Evapotranspiration: {tomorrow['evapotranspiration']} mm/day")

    if "error" in tomorrow:
        report_lines.append(f"\n⚠️ {tomorrow['error']}")

    return "\n".join(report_lines)
