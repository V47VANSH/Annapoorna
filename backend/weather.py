"""Current weather for a field.

Uses Tomorrow.io if a key is set (it has soil moisture and evapotranspiration),
otherwise Open-Meteo, which doesn't need a key.
"""

import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

NOT_AVAILABLE = "N/A"

# Open-Meteo sometimes times out or returns 503, a retry usually works.
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _get_with_retry(url: str, params: dict) -> requests.Response:
    """GET with retries on timeouts, connection errors, 429 and 5xx."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        last_attempt = attempt == RETRY_ATTEMPTS
        try:
            response = requests.get(
                url, params=params, timeout=config.WEATHER_TIMEOUT_SECONDS
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            if last_attempt:
                raise
            logger.info(
                "Weather request attempt %d failed (%s); retrying",
                attempt,
                exc.__class__.__name__,
            )
        else:
            if response.status_code not in _RETRYABLE_STATUS or last_attempt:
                response.raise_for_status()
                return response
            logger.info(
                "Weather request attempt %d got HTTP %d; retrying",
                attempt,
                response.status_code,
            )
        time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise AssertionError("unreachable")  # pragma: no cover


def fetch_tomorrow_io(lat: float, lon: float) -> dict[str, str | float]:
    """Current conditions from Tomorrow.io, or {"error": ...}."""
    if not config.TOMORROW_API_KEY:
        return {"error": "TOMORROW_API_KEY is not configured."}

    try:
        response = _get_with_retry(
            config.TOMORROW_API_URL,
            {"location": f"{lat},{lon}", "apikey": config.TOMORROW_API_KEY},
        )
        values = response.json().get("data", {}).get("values", {})

        return {
            "source": "Tomorrow.io",
            "temperature": values.get("temperature", NOT_AVAILABLE),
            "humidity": values.get("humidity", NOT_AVAILABLE),
            "rain_probability": values.get("precipitationProbability", NOT_AVAILABLE),
            "soil_moisture": values.get(
                "soilMoistureVolumetric0To10cm", NOT_AVAILABLE
            ),
            "evapotranspiration": values.get("evapotranspiration", NOT_AVAILABLE),
        }

    except requests.RequestException as exc:
        # don't log the exception text, the URL contains the key
        logger.warning("Tomorrow.io request failed: %s", exc.__class__.__name__)
        return {"error": "Tomorrow.io is unreachable."}
    except ValueError as exc:
        logger.warning("Tomorrow.io returned a malformed response: %s", exc)
        return {"error": "Tomorrow.io returned an unexpected response."}


def fetch_open_meteo(lat: float, lon: float) -> dict[str, str | float]:
    """Fetch realtime conditions from Open-Meteo, which requires no API key."""
    try:
        response = _get_with_retry(
            config.OPEN_METEO_API_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,precipitation,"
                    "soil_moisture_0_to_1cm"
                ),
                "daily": "precipitation_probability_max,et0_fao_evapotranspiration",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        payload = response.json()

        current = payload.get("current", {})
        daily = payload.get("daily", {})

        def _first(key: str):
            values = daily.get(key) or []
            return values[0] if values else NOT_AVAILABLE

        return {
            "source": "Open-Meteo",
            "temperature": current.get("temperature_2m", NOT_AVAILABLE),
            "humidity": current.get("relative_humidity_2m", NOT_AVAILABLE),
            "rain_probability": _first("precipitation_probability_max"),
            "soil_moisture": current.get("soil_moisture_0_to_1cm", NOT_AVAILABLE),
            "evapotranspiration": _first("et0_fao_evapotranspiration"),
        }

    except requests.RequestException as exc:
        logger.warning("Open-Meteo request failed: %s", exc.__class__.__name__)
        return {"error": "Open-Meteo is unreachable."}
    except (ValueError, IndexError, TypeError) as exc:
        logger.warning("Open-Meteo returned a malformed response: %s", exc)
        return {"error": "Open-Meteo returned an unexpected response."}


def get_current_conditions(lat: float, lon: float) -> dict[str, str | float]:
    """Return conditions from the best available source."""
    if config.OFFLINE_MODE:
        return {"error": "OFFLINE_MODE is enabled; weather lookup is disabled."}

    primary = fetch_tomorrow_io(lat, lon)
    if "error" not in primary:
        return primary

    if not config.ALLOW_KEYLESS_FALLBACKS:
        return primary

    logger.info("Falling back to Open-Meteo (%s)", primary["error"])
    fallback = fetch_open_meteo(lat, lon)
    if "error" not in fallback:
        fallback["fallback_reason"] = primary["error"]
    return fallback


def get_weather_info(lat: float, lon: float) -> str:
    """Render the weather section of the daily field report."""
    conditions = get_current_conditions(lat, lon)

    lines = ["\nCombined Weather Insights for the field location are following:\n"]

    if "error" in conditions:
        lines.append(f"\n⚠️ Weather data unavailable: {conditions['error']}")
        return "\n".join(lines)

    lines.append(f"🛰️ {conditions['source']}:")
    lines.append(f"- Temp: {conditions['temperature']}°C")
    lines.append(f"- Humidity: {conditions['humidity']}%")
    lines.append(f"- Rain Probability: {conditions['rain_probability']}%")
    if conditions["soil_moisture"] != NOT_AVAILABLE:
        lines.append(f"- Soil Moisture: {conditions['soil_moisture']} m³/m³")
    if conditions["evapotranspiration"] != NOT_AVAILABLE:
        lines.append(
            f"- Evapotranspiration: {conditions['evapotranspiration']} mm/day"
        )

    if "fallback_reason" in conditions:
        lines.append(
            f"\n_(Using the keyless Open-Meteo fallback: {conditions['fallback_reason']} "
            "Soil moisture and evapotranspiration are modelled rather than measured.)_"
        )

    return "\n".join(lines)
