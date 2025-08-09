"""Daily field report: weather + satellite data."""

import logging
from datetime import UTC, datetime

from sattelite_report import EarthEngineUnavailable, generate_multisatellite_report
from weather import get_weather_info

logger = logging.getLogger(__name__)


def bounding_box_to_polygon(bounding_box):
    """[lat_min, lat_max, lon_min, lon_max] -> polygon of [lon, lat] points.

    Earth Engine wants [lon, lat] (x, y), the geocoder gives lat first.
    """
    lat_min, lat_max, lon_min, lon_max = bounding_box
    return [
        [lon_min, lat_min],  # south-west
        [lon_max, lat_min],  # south-east
        [lon_max, lat_max],  # north-east
        [lon_min, lat_max],  # north-west
    ]


def generateReport(boundingBox, id):
    """Report for one field. If the satellite part fails, weather is still sent."""
    logger.info("Generating report for bounding box %s (user %s)", boundingBox, id)

    field_polygon = bounding_box_to_polygon(boundingBox)
    lat = (boundingBox[0] + boundingBox[1]) / 2
    lon = (boundingBox[2] + boundingBox[3]) / 2

    weather_report = get_weather_info(lat, lon)

    try:
        crop_health = generate_multisatellite_report(
            field_polygon,
            id,
            datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        )[0]
    except EarthEngineUnavailable as exc:
        logger.warning("Satellite report unavailable: %s", exc)
        crop_health = f"⚠️ Satellite crop health data is unavailable: {exc}"
    except Exception as exc:
        logger.exception("Satellite report failed")
        crop_health = f"⚠️ Satellite crop health data could not be generated: {exc}"

    return f"""
The following is the weather report at the farmer's field

{weather_report}

This is the crop health report given by the satellite

{crop_health}
"""
