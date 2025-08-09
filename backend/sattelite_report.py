"""Crop health report from satellite data (Google Earth Engine).

Uses the latest Sentinel-2, Landsat 8, Sentinel-1 and MODIS images from the
last 90 days, computes vegetation/water/nitrogen indices, clusters stressed
pixels with DBSCAN and writes a markdown report.
"""

import logging
import threading
from datetime import UTC, datetime, timedelta

import ee
import numpy as np
from sklearn.cluster import DBSCAN

import config

logger = logging.getLogger(__name__)

_ee_initialized = False
_ee_lock = threading.Lock()


class EarthEngineUnavailable(RuntimeError):
    """Raised when Earth Engine is not configured or not authenticated."""


def ensure_earth_engine() -> None:
    """Initialize Earth Engine on first use.

    Credentials: GEE_SERVICE_ACCOUNT_KEY if set, otherwise the login saved by
    `earthengine authenticate`, otherwise application default credentials.
    """
    global _ee_initialized
    if _ee_initialized:
        return

    if config.OFFLINE_MODE:
        raise EarthEngineUnavailable(
            "OFFLINE_MODE is enabled; Earth Engine is disabled."
        )
    if not config.GEE_PROJECT_ID:
        raise EarthEngineUnavailable(
            "PROJECT_ID is not set. Create a Google Cloud project registered for "
            "Earth Engine and set PROJECT_ID in backend/.env (see the README)."
        )

    with _ee_lock:
        if _ee_initialized:
            return

        credentials = "persistent"  # the library's own default
        if config.GEE_SERVICE_ACCOUNT_KEY:
            try:
                credentials = ee.ServiceAccountCredentials(
                    None, key_file=config.GEE_SERVICE_ACCOUNT_KEY
                )
            except Exception as exc:
                raise EarthEngineUnavailable(
                    "Could not load the service account key at "
                    f"GEE_SERVICE_ACCOUNT_KEY: {exc}"
                ) from exc

        try:
            ee.Initialize(credentials, project=config.GEE_PROJECT_ID)
        except Exception as exc:
            hint = (
                "Check that the service account is registered for Earth Engine "
                "and has the Earth Engine Resource Viewer role."
                if config.GEE_SERVICE_ACCOUNT_KEY
                else "Run 'uv run earthengine authenticate' in backend/ once."
            )
            raise EarthEngineUnavailable(
                f"Earth Engine initialization failed: {exc}. {hint}"
            ) from exc

        _ee_initialized = True
        logger.info(
            "Earth Engine initialized for project %s (%s)",
            config.GEE_PROJECT_ID,
            "service account" if config.GEE_SERVICE_ACCOUNT_KEY else "user login",
        )


# Thresholds for parameter interpretation
THRESHOLDS = {
    'NDVI': [
        (None, 0.2, "Very low: Bare soil or crop failure"),
        (0.2, 0.4, "Low: Stressed or sparse vegetation"),
        (0.4, 0.6, "Moderate: Crops established but with some stress"),
        (0.6, None, "High: Healthy, dense green cover")
    ],
    'NDWI': [
        (None, 0.1, "Dry: Drought or water stress"),
        (0.1, 0.3, "Adequate moisture: Sufficient but watch for dry spells"),
        (0.3, None, "Wet: Possible waterlogging or heavy irrigation/rain")
    ],
    'EVI': [
        (None, 0.1, "Very low: No canopy or early growth"),
        (0.1, 0.3, "Low: Thin canopy, early stages"),
        (0.3, 0.5, "Moderate: Expanding leaf area"),
        (0.5, None, "High: Vigorous, high-biomass crop")
    ],
    'NDRE': [
        (None, 0.1, "Potential N deficiency or early growth"),
        (0.1, 0.3, "Normal/Moderate chlorophyll content"),
        (0.3, None, "Rich: Likely no nitrogen deficit")
    ],
    'SAVI': [
        (None, 0.2, "Mostly bare soil"),
        (0.2, 0.5, "Low to moderate cover"),
        (0.5, None, "Dense vegetation")
    ],
    'MSAVI': [
        (None, 0.3, "Sparse vegetation/early growth"),
        (0.3, 0.6, "Medium cover"),
        (0.6, None, "Dense, healthy vegetation")
    ],
    'VARI': [
        (None, 0.05, "Low greenness, possible crop stress"),
        (0.05, None, "Green, photosynthetically active vegetation")
    ],
    'SoilMoisture': [
        (None, 0.1, "Very dry soil, drought likely"),
        (0.1, 0.3, "Low moisture"),
        (0.3, 0.6, "Moderate soil moisture"),
        (0.6, None, "High soil moisture - possible waterlogging or irrigation")
    ],
    'SurfaceTemp': [
        (None, 18, "Cool soil temperature, ideal for crops"),
        (18, 34, "Normal temperature range"),
        (34, None, "High temperature - potential heat stress")
    ],
    'SAR_VH': [
        (None, -18, "Very low backscatter - possible very dry soil or bare soil"),
        (-18, -13, "Moderate backscatter"),
        (-13, None, "High backscatter - dense vegetation or moist soil")
    ],
    'SAR_VV': [
        (None, -18, "Very low backscatter - bare soil or dry conditions"),
        (-18, -13, "Moderate backscatter"),
        (-13, None, "High backscatter - dense vegetation or moist soil")
    ]
}



def _fmt(value, digits=2):
    """Format a statistic, tolerating bands that returned no data."""
    return "n/a" if value is None else f"{value:.{digits}f}"


def generate_deep_interpretation(
    s2_stats, l8_stats, s1_stats, modis_stats, modis_lai_stats, modis_temp_stats, prev_stats=None
):
    interpretation = []
    # --- Sentinel-2 (High-res) ---
    if s2_stats:
        ndvi = s2_stats.get('NDVI', {}).get('mean')
        ndvi_std = s2_stats.get('NDVI', {}).get('stdDev', 0)
        evi = s2_stats.get('EVI', {}).get('mean')
        ndwi = s2_stats.get('NDWI', {}).get('mean')
        ndre = s2_stats.get('NDRE', {}).get('mean')
        savi = s2_stats.get('SAVI', {}).get('mean')
        status = []

        # Combined logic with explicit values
        if ndvi is not None and ndvi < 0.2 and ndwi is not None and ndwi < 0:
            status.append(
                f"Very low vegetation (NDVI={ndvi:.2f}) and active water stress (NDWI={ndwi:.2f}) - likely bare, failed emergence, or severe drought."
            )
        elif (ndvi and 0.2 <= ndvi < 0.4) and (ndwi and ndwi < 0.1) and (evi and evi < 0.3):
            status.append(
                f"Crop is struggling: thin canopy (EVI={evi:.2f}), low NDVI ({ndvi:.2f}), dry soil (NDWI={ndwi:.2f}) - could be drought onset, pests, or early stress."
            )
        elif (ndvi and 0.4 <= ndvi < 0.6) and (ndwi and ndwi > 0.2):
            status.append(
                f"Healthy, steadily growing crop with good water (NDVI={ndvi:.2f}, NDWI={ndwi:.2f}) - maintain regimen."
            )
        elif (ndvi and ndvi > 0.6) and (evi and evi > 0.5) and (ndwi and ndwi > 0.15):
            status.append(
                f"Field is at vegetative peak: vigorous NDVI={ndvi:.2f}, EVI={evi:.2f}, well-watered (NDWI={ndwi:.2f})."
            )
        else:
            status.append(
                f"Mixed crop condition: NDVI={_fmt(ndvi)}, EVI={_fmt(evi)}, NDWI={_fmt(ndwi)}. Combined indices do not strongly indicate a healthy or a severely stressed field."
            )

        if ndre is not None:
            if ndre < 0.13:
                status.append(
                    f"Nitrogen deficiency likely (NDRE={ndre:.2f})."
                )
            elif ndre < 0.2:
                status.append(
                    f"Borderline/low nitrogen (NDRE={ndre:.2f}). Consider split or foliar N application."
                )
            elif ndre > 0.3:
                status.append(
                    f"Robust nitrogen/chlorophyll (NDRE={ndre:.2f}). No action needed."
                )

        # Variability and spatial advice
        if ndvi_std and ndvi_std > 0.12:
            status.append(
                f"Significant spatial variability present (NDVI stdDev={ndvi_std:.2f}) - patchy emergence or management differences, apply zone-based treatment."
            )

        if savi is not None and savi < 0.3:
            status.append(
                f"Field is mostly bare (SAVI={savi:.2f}); consider resowing or weed management."
            )

        interpretation.append("**Sentinel-2 Analysis:**\n- " + "\n- ".join(status))

    # --- Landsat 8 ---
    if l8_stats:
        ndvi = l8_stats.get('NDVI', {}).get('mean')
        ndwi = l8_stats.get('NDWI', {}).get('mean')
        evi = l8_stats.get('EVI', {}).get('mean')
        temp = l8_stats.get('SurfaceTemp', {}).get('mean', None)
        temp_status = ""
        ls_status = []
        if temp is not None:
            if temp < 10:
                temp_status = f"Surface temp cool at {temp:.2f}°C: likely morning pass or immediate post-rain/irrigation."
            elif temp > 34:
                temp_status = f"Surface temp high at {temp:.2f}°C: high heat stress possible."
            else:
                temp_status = f"Normal field temperature {temp:.2f}°C."
        if ndvi is not None and ndvi < 0.15 and ndwi is not None and ndwi < 0.12:
            ls_status.append(
                f"Extremely low NDVI ({ndvi:.2f}) and low NDWI ({ndwi:.2f}) - bare soil or failed stand, perhaps recently harvested."
            )
        elif ndvi is not None and ndvi < 0.3:
            ls_status.append(
                f"Sparse vegetative cover (NDVI={ndvi:.2f}) - underperforming, yield limited."
            )
        if evi is not None and evi < 0.2:
            ls_status.append(
                f"Stunted canopy expansion (EVI={evi:.2f})."
            )
        if temp_status:
            ls_status.append(temp_status)
        interpretation.append("**Landsat 8 Analysis:**\n- " + "\n- ".join(ls_status))

    # --- Sentinel-1 SAR ---
    if s1_stats and s1_stats.get('VV', {}).get('mean') is not None:
        vv = s1_stats['VV']['mean']
        vh = s1_stats.get('VH', {}).get('mean')
        sar_msg = []
        if vv is not None and vv > -10:
            sar_msg.append(
                f"SAR VV high ({vv:.2f} dB): peak crop growth or moist soil."
            )
        elif vv is not None and vv < -15 and vh is not None and vh < -18:
            sar_msg.append(
                f"SAR VV/VH both low (VV={vv:.2f} dB, VH={vh:.2f} dB): very dry or bare soil likely."
            )
        elif vv is not None and vh is not None:
            sar_msg.append(
                f"Intermediate SAR backscatter (VV={vv:.2f}, VH={vh:.2f}). May reflect patchy crop or partial regrowth."
            )
        interpretation.append("**Sentinel-1 SAR Analysis:**\n- " + " / ".join(sar_msg))

    # --- MODIS NDVI/EVI/LAI (apply scale factor) ---
    if modis_stats:
        ndvi = modis_stats.get('NDVI', {}).get('mean')
        evi = modis_stats.get('EVI', {}).get('mean')
        if ndvi is not None and evi is not None:
            ndvi_c = ndvi * 0.0001 if ndvi > 1 else ndvi
            evi_c = evi * 0.0001 if evi > 1 else evi
            if ndvi_c < 0.3 and evi_c < 0.25:
                interpretation.append(
                    f"MODIS confirms low field status (NDVI={ndvi_c:.2f}, EVI={evi_c:.2f}); landscape stress is widespread."
                )
            elif ndvi_c > 0.5 and evi_c > 0.3:
                interpretation.append(
                    f"MODIS regional indices NDVI={ndvi_c:.2f}, EVI={evi_c:.2f}: field above average regionally."
                )
    if modis_lai_stats:
        lai = modis_lai_stats.get('Lai_500m', {}).get('mean')
        if lai is not None:
            if lai < 2:
                interpretation.append(f"MODIS LAI ({lai:.2f}) is poor (sparse).")
            elif lai < 4:
                interpretation.append(f"MODIS LAI moderate ({lai:.2f}); not at global max, likely N or water limited.")
            else:
                interpretation.append(f"MODIS LAI high ({lai:.2f}); near peak for cereals/maize.")

    return "\n\n".join(interpretation)



def generate_flagged_area_interpretation(flagged_areas, meta=None, cluster_eps=0.0005, min_samples=3):
    """
    - flagged_areas: list of dicts with coordinate, parameter, value, threshold_message per flagged pixel
    - meta: optional metadata for context
    - cluster_eps: DBSCAN epsilon in degrees (approx 50m at equator if 0.0005)
    - min_samples: min points for a cluster (adjust for field size/resolution)
    Returns a detailed agronomic interpretation string for your report.
    """
    if not flagged_areas or len(flagged_areas) == 0:
        return "No flagged areas detected. Field is within healthy thresholds as per the latest satellite pass."

    coords = [area['coordinates'] for area in flagged_areas]
    if len(coords) < min_samples:
        return "Only isolated flagged pixels were found; no spatial clusters detected. These may be random anomalies or noise. No urgent action needed unless similar patterns persist over time."

    coords_np = np.array(coords)
    # DBSCAN clustering (in degrees; for metric use projected coords)
    clustering = DBSCAN(eps=cluster_eps, min_samples=min_samples).fit(coords_np)
    labels = clustering.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    clusters = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue  # ignore "noise"
        clusters.setdefault(label, []).append(flagged_areas[idx])

    # Compose results
    result = []
    if n_clusters == 0:
        result.append("Flagged areas are scattered single points, no clustering detected. These are most likely isolated anomalies or natural field micro-variability.")
        return "\n".join(result)

    result.append("## Flagged Area Agronomic Summary")
    result.append(f"Detected {n_clusters} clusters of flagged areas (min {min_samples} points each):")

    # Cluster summary table with aggregated data
    cluster_table = "| Cluster # | Center Longitude | Center Latitude | Issue | Avg Value | Points Count |\n|-----------|------------------|-----------------|-------|-----------|--------------|"

    for i, points in clusters.items():
        # Calculate center coordinates
        lons = [p['coordinates'][0] for p in points]
        lats = [p['coordinates'][1] for p in points]
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)

        # Group by parameter and calculate averages
        param_groups = {}
        for point in points:
            param = point['parameter']
            param_groups.setdefault(param, []).append(point)

        # Create issue summary for this cluster
        issue_parts = []
        for param, param_points in param_groups.items():
            avg_val = sum(p['value'] for p in param_points) / len(param_points)
            # Use the full threshold message instead of splitting
            threshold_msg = param_points[0]['threshold_message']
            issue_parts.append(f"{param}: {threshold_msg} (avg: {avg_val:.2f})")

        issue_summary = "; ".join(issue_parts)
        total_points = len(points)

        cluster_table += f"\n| {i+1} | {center_lon:.5f} | {center_lat:.5f} | {issue_summary} | - | {total_points} |"

    result.append(cluster_table)
    result.append("\n*Each coordinate marks the center of a detected stress cluster, scout these first.*\n")

    # Parameter/context diagnostics
    ndvi_vals = [p['value'] for ps in clusters.values() for p in ps if p['parameter'] == "NDVI"]
    ndwi_vals = [p['value'] for ps in clusters.values() for p in ps if p['parameter'] == "NDWI"]
    ndre_vals = [p['value'] for ps in clusters.values() for p in ps if p['parameter'] == "NDRE"]
    result.append("### Clustered Parameter Diagnostics")
    if ndvi_vals:
        mean_ndvi = np.mean(ndvi_vals)
        min_ndvi = np.min(ndvi_vals)
        if min_ndvi < 0.12:
            result.append(f"- Many flagged clusters contain NDVI < 0.18 (mean {mean_ndvi:.2f}, min {min_ndvi:.2f}): severe crop stress, stand loss, or bare soil likely.")
        else:
            result.append(f"- Cluster mean NDVI: {mean_ndvi:.2f} (some stress).")
    if ndwi_vals:
        mean_ndwi = np.mean(ndwi_vals)
        min_ndwi = np.min(ndwi_vals)
        if min_ndwi < 0.08:
            result.append(f"- NDWI in clusters < 0.1 (mean {mean_ndwi:.2f}, min {min_ndwi:.2f}): active drought or deficit irrigation risk.")
    if ndre_vals:
        min_ndre = np.min(ndre_vals)
        if min_ndre < 0.13:
            result.append(f"- Some clusters have NDRE < 0.13 (min {min_ndre:.2f}): possible nitrogen deficiency or delayed development.")

    # Recommendations
    result.append("\n### Actionable Recommendations")
    result.append("- **Scout each cluster center coordinate first.** These are priority zones most likely to be at risk for yield loss, failed establishment, or urgent water/nutrient intervention.")
    if ndvi_vals and min_ndvi < 0.12:
        result.append("- **Apply targeted soil/nutrient or irrigation rescue treatments** in clusters with very low NDVI and NDWI, based on scouting findings.")
    if ndre_vals and min_ndre < 0.13:
        result.append("- **Nitrogen management:** Consider foliar/split N for clusters with flagged NDRE if crop stage allows.")
    result.append("- Log field observations and match with flagged clusters. Repeat mapping after management changes or next satellite pass to confirm recovery.")

    if meta:
        result.append(f"\n_Observation Window: {meta.get('analysis_period',{})}, Source Dates: {meta.get('satellite_sources',{})}_")

    return "\n".join(result)
def interpret(param, value):
    thresholds = THRESHOLDS.get(param, [])
    for lower, upper, msg in thresholds:
        if lower is None and value is not None and value < upper:
            return msg
        if upper is None and value is not None and value >= lower:
            return msg
        if (lower is not None and upper is not None and value is not None and lower <= value < upper):
            return msg
    return None


def add_all_indices(image):
    """Add indices to a Sentinel-2 image.

    S2 reflectance is stored x10000. EVI, SAVI and MSAVI need real reflectance
    (0-1), so the bands are scaled first.
    """
    refl = image.select(['B2', 'B3', 'B4', 'B5', 'B8', 'B11']).divide(10000)
    blue, green, red = refl.select('B2'), refl.select('B3'), refl.select('B4')
    nir = refl.select('B8')

    ndvi = refl.normalizedDifference(['B8', 'B4']).rename('NDVI')
    evi = refl.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': nir, 'RED': red, 'BLUE': blue}
    ).rename('EVI')
    ndwi = refl.normalizedDifference(['B8', 'B11']).rename('NDWI')
    savi = refl.expression(
        '((NIR - RED) * (1 + L)) / (NIR + RED + L)',
        {'NIR': nir, 'RED': red, 'L': 0.5}
    ).rename('SAVI')
    msavi = refl.expression(
        '0.5 * (2 * NIR + 1 - sqrt((2 * NIR + 1)**2 - 8 * (NIR - RED)))',
        {'NIR': nir, 'RED': red}
    ).rename('MSAVI')
    ndre = refl.normalizedDifference(['B8', 'B5']).rename('NDRE')
    vari = refl.expression(
        '(GREEN - RED) / (GREEN + RED - BLUE)',
        {'GREEN': green, 'RED': red, 'BLUE': blue}
    ).rename('VARI')
    return image.addBands([ndvi, evi, ndwi, savi, msavi, ndre, vari])

def add_sentinel1_sar_indices(image):
    if image:
        vv = image.select('VV')
        vh = image.select('VH')
        vh_vv_ratio = vh.divide(vv).rename('VH_VV_RATIO')
        vh_vv_diff = vh.subtract(vv).rename('VH_VV_DIFF')
        image = image.addBands([vh_vv_ratio, vh_vv_diff])
        return image
    return None

def scale_modis_vegetation(image):
    """MOD13Q1: NDVI and EVI are stored x 10000."""
    return image.addBands(
        image.select(['NDVI', 'EVI']).multiply(0.0001), None, True
    )


def scale_modis_lai(image):
    """MOD15A2H: LAI x10, FPAR x100. Values above 100 are fill (water, urban, cloud)."""
    lai = image.select('Lai_500m')
    fpar = image.select('Fpar_500m')
    return image.addBands(
        [
            lai.updateMask(lai.lte(100)).multiply(0.1),
            fpar.updateMask(fpar.lte(100)).multiply(0.01),
        ],
        None,
        True,
    )


def scale_modis_lst(image):
    """MOD11A1: LST is Kelvin / 0.02. Returned in deg C."""
    return image.addBands(
        image.select('LST_Day_1km').multiply(0.02).subtract(273.15), None, True
    )


def fetch_closest_pixel(img, aoi, band, scale):
    """For MODIS/Landsat/small AOI, get pixel value of grid cell over center."""
    center = aoi.centroid()
    vals = img.reduceRegion(ee.Reducer.first(), center, scale).getInfo()
    return vals.get(band, None)

def date_of_image(img):
    """Extract date from image metadata."""
    if not img:
        return "Not available"
    try:
        img_info = img.getInfo()
        timestamp_keys = ['system:time_start', 'system:time_end']
        for key in timestamp_keys:
            if img_info['properties'].get(key):
                ts = img_info['properties'][key] / 1000
                try:
                    return datetime.fromtimestamp(ts, tz=UTC).strftime('%Y-%m-%d')
                except Exception:
                    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    except Exception:
        pass
    return "Not available"

def get_latest(collection_id, aoi, start, end, cloud_filter=None, bands=None, proc_func=None, scale=10):
    """Latest image in the date range and its band stats.

    Returns (None, "Not available", {}) if there is no image. first() doesn't
    return None for an empty collection, so the size is checked.
    """
    col = ee.ImageCollection(collection_id).filterBounds(aoi).filterDate(start, end)
    if cloud_filter:
        col = col.filter(cloud_filter)
    if col.size().getInfo() == 0:
        return None, "Not available", {}

    img = ee.Image(col.sort('system:time_start', False).first())
    if proc_func:
        img = proc_func(img)

    stats = {}
    date = date_of_image(img)

    # For MODIS/Landsat on small polygons, use sample-at-center
    for band in bands or []:
        try:
            pixel = fetch_closest_pixel(img, aoi, band, scale)
            if isinstance(pixel, (float, int)):
                stats[band] = {'mean': pixel}
        except Exception:
            pass

    # For Sentinel-2/Sentinel-1, use region mean
    try:
        reducer = ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True)
        statres = img.reduceRegion(reducer, aoi, scale, maxPixels=1e9).getInfo()
        for k, v in statres.items():
            try:
                param, stat = k.rsplit('_', 1)
                stats.setdefault(param, {})[stat] = v
            except Exception:
                stats[k] = v
    except Exception:
        pass

    return img, date, stats

def add_indices_s2(image):
    """Add Sentinel-2 specific indices (alias for existing function)."""
    return add_all_indices(image)

def add_indices_l8(image):
    """Add indices and surface temperature (deg C) to a Landsat 8 C2 L2 image.

    Reflectance = DN * 0.0000275 - 0.2, temperature = DN * 0.00341802 + 149 (K).
    """
    sr = image.select(['SR_B2', 'SR_B4', 'SR_B5', 'SR_B6']).multiply(0.0000275).add(-0.2)
    ndvi = sr.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    ndwi = sr.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDWI')
    evi = sr.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': sr.select('SR_B5'), 'RED': sr.select('SR_B4'), 'BLUE': sr.select('SR_B2')}
    ).rename('EVI')
    temp_c = (
        image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
        .rename('SurfaceTemp')
    )
    return image.addBands([ndvi, ndwi, evi, temp_c])

def add_sar_indices(image):
    """Add SAR indices (alias for existing function)."""
    return add_sentinel1_sar_indices(image)

# Add index bands configuration
INDEX_BANDS = {
    'Sentinel-2': ['NDVI', 'NDWI', 'EVI', 'NDRE', 'SAVI', 'MSAVI', 'VARI'],
    'Landsat-8': ['NDVI', 'NDWI', 'EVI', 'SurfaceTemp'],
    'Sentinel-1': ['VV', 'VH', 'VH_VV_RATIO', 'VH_VV_DIFF']
}

def generate_interpretation(s2_stats, l8_stats, s2_date, l8_date):
    """Per-satellite index summary, one line per index."""
    llm_report = []

    def _index_lines(stats, params):
        lines = []
        for param in params:
            value = stats.get(param, {}).get('mean')
            meaning = interpret(param, value) or "no reading"
            lines.append(f"  - {param}: {_fmt(value)} ({meaning})")
        return lines

    if s2_stats:
        lines = [f"As of {s2_date} (Sentinel-2):"]
        lines += _index_lines(s2_stats, ['NDVI', 'NDWI', 'NDRE', 'SAVI', 'MSAVI', 'EVI', 'VARI'])
        llm_report.append("\n".join(lines))
    else:
        llm_report.append("Sentinel-2: No valid image found in last 90 days.")

    if l8_stats:
        lines = [f"As of {l8_date} (Landsat 8):"]
        lines += _index_lines(l8_stats, ['NDVI', 'NDWI', 'EVI'])
        temp_c = l8_stats.get('SurfaceTemp', {}).get('mean')  # already deg C
        if temp_c is not None:
            if temp_c < 18:
                tmsg = "Cool soil/canopy - ideal for crops"
            elif temp_c > 34:
                tmsg = "High temperature - potential heat stress"
            else:
                tmsg = "Normal temperature range"
            lines.append(f"  - Surface Temperature: {temp_c:.2f}°C ({tmsg})")
        llm_report.append("\n".join(lines))
    else:
        llm_report.append("Landsat 8: No valid image found in last 90 days.")

    return "\n\n".join(llm_report)

# getInfo() returns at most 5000 features
MAX_FLAGGED_SAMPLES = 500


def generate_flagged_areas(image, geometry, bands, thresholds, scale=10):
    """Pixels below each band's threshold, with coordinates. EE errors are raised."""
    if image is None:
        return []

    available = set(image.bandNames().getInfo())
    flagged_pixels = []
    for param, th in zip(bands, thresholds, strict=False):
        if param not in available:
            continue
        band_img = image.select(param)
        masked = band_img.updateMask(band_img.lt(th[1]))
        samples = (
            masked.sample(
                region=geometry,
                scale=scale,
                numPixels=MAX_FLAGGED_SAMPLES,
                seed=0,
                geometries=True,
            )
            .limit(MAX_FLAGGED_SAMPLES)
            .getInfo()
        )
        for feature in samples.get('features', []):
            flagged_pixels.append({
                'message': "flagged area detected",
                'parameter': param,
                'threshold_message': th[2],
                'value': feature['properties'].get(param),
                'coordinates': feature['geometry']['coordinates'],
            })
    return flagged_pixels


def generate_multisatellite_report(geometry_geojson, user_login, utc_now):
    ensure_earth_engine()
    geometry = ee.Geometry.Polygon(geometry_geojson)
    dt_now = datetime.strptime(utc_now, '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
    dt_start = dt_now - timedelta(days=90)
    start_date_str = dt_start.strftime('%Y-%m-%d')
    end_date_str = dt_now.strftime('%Y-%m-%d')

    # Enhanced satellite data collection using new get_latest function
    # ---- Sentinel-2
    s2, s2_date, s2_stats = get_latest(
        "COPERNICUS/S2_SR_HARMONIZED", geometry, start_date_str, end_date_str,
        cloud_filter=ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15),
        bands=INDEX_BANDS['Sentinel-2'], proc_func=add_indices_s2, scale=10
    )

    # ---- Landsat-8
    l8, l8_date, l8_stats = get_latest(
        'LANDSAT/LC08/C02/T1_L2', geometry, start_date_str, end_date_str,
        cloud_filter=ee.Filter.lt('CLOUD_COVER', 15),
        bands=INDEX_BANDS['Landsat-8'], proc_func=add_indices_l8, scale=30
    )

    # ---- MODIS NDVI/EVI
    modis, modis_date, modis_stats = get_latest(
        'MODIS/061/MOD13Q1', geometry, start_date_str, end_date_str,
        bands=['NDVI', 'EVI'], proc_func=scale_modis_vegetation, scale=500
    )

    # ---- MODIS LAI/FPAR
    modis_lai, modis_lai_date, modis_lai_stats = get_latest(
        'MODIS/061/MOD15A2H', geometry, start_date_str, end_date_str,
        bands=['Lai_500m', 'Fpar_500m'], proc_func=scale_modis_lai, scale=500
    )

    # ---- MODIS Land Surface Temperature
    modis_temp, modis_temp_date, modis_temp_stats = get_latest(
        'MODIS/061/MOD11A1', geometry, start_date_str, end_date_str,
        bands=['LST_Day_1km'], proc_func=scale_modis_lst, scale=1000
    )

    # ---- Sentinel-1 SAR
    s1, s1_date, s1_stats = get_latest(
        'COPERNICUS/S1_GRD', geometry, start_date_str, end_date_str,
        cloud_filter=ee.Filter.eq('instrumentMode', 'IW'),
        bands=INDEX_BANDS['Sentinel-1'], proc_func=add_sar_indices, scale=10
    )

    llm_text_report = f"""
# Comprehensive Multi-Satellite Crop & Field Health Report

**User:** {user_login}  
**Analysis Date (UTC):** {utc_now}  
**Analysis Period:** {start_date_str} to {end_date_str}

## Latest Image Acquisition Dates

| Satellite      | Date        |
| -------------- | ----------- |
| Sentinel-2     | {s2_date}   |
| Sentinel-1     | {s1_date}   |
| Landsat 8      | {l8_date}   |
| MODIS NDVI/EVI | {modis_date}   |
| MODIS LAI      | {modis_lai_date}   |
| MODIS LST      | {modis_temp_date}|

## Field Status Flags  
"""

    llm_text_report += "\n" + generate_interpretation(s2_stats, l8_stats, s2_date, l8_date) + "\n"
    test2 = generate_deep_interpretation(s2_stats, l8_stats, s1_stats, modis_stats, modis_lai_stats, modis_temp_stats)
    llm_text_report += "\n" + test2 + "\n"

    healthy_message = (
        "No flagged pixels found. Everything is within healthy thresholds."
    )
    flagged_coords_vals = []
    if s2 is None and l8 is None:
        interpretation = (
            "No recent cloud-free Sentinel-2 or Landsat image, so stressed "
            "areas could not be mapped."
        )
    else:
        try:
            flagged_coords_vals.extend(generate_flagged_areas(s2, geometry, ['NDVI', 'NDWI', 'NDRE'], [
                (None, 0.2, "NDVI low: possible sparse or stressed vegetation"),
                (None, 0.1, "NDWI low: likely dry/drought stress"),
                (None, 0.1, "NDRE low: potential N deficiency"),
            ], scale=10)[:10])
            flagged_coords_vals.extend(generate_flagged_areas(l8, geometry, ['NDVI', 'NDWI'], [
                (None, 0.2, "NDVI low: sparse or failed zones"),
                (None, 0.1, "NDWI low: water deficit"),
            ], scale=30)[:10])

            interpretation = (
                generate_flagged_area_interpretation(flagged_coords_vals)
                if flagged_coords_vals
                else healthy_message
            )
        except Exception as exc:
            logger.warning("Flagged-area mapping failed: %s", exc)
            interpretation = (
                "Pixel-level stress mapping could not be completed for this field."
            )
            flagged_coords_vals = []
    llm_text_report += "\n" + interpretation + "\n"


    metadata = {
        'user': user_login,
        'analysis_date_utc': utc_now,
        'analysis_period': {'start': start_date_str, 'end': end_date_str},
        'satellite_sources': {
            'Sentinel-2': s2_date,
            'Sentinel-1': s1_date,
            'Landsat 8': l8_date,
            'MODIS NDVI/EVI': modis_date,
            'MODIS LAI': modis_lai_date,
            'MODIS LST': modis_temp_date
        }
    }


    raw_details = {
        'sentinel2': {'stats': s2_stats, 'date': s2_date},
        'sentinel1': {'stats': s1_stats, 'date': s1_date},
        'landsat8': {'stats': l8_stats, 'date': l8_date},
        'modis_ndvi_evi': {'stats': modis_stats, 'date': modis_date},
        'modis_lai': {'stats': modis_lai_stats, 'date': modis_lai_date},
        'modis_lst': {'stats': modis_temp_stats, 'date': modis_temp_date}
    }

    return [llm_text_report, raw_details, flagged_coords_vals, metadata]

if __name__ == "__main__":
    # Test run on the demo farm: uv run python sattelite_report.py
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    lat_min, lat_max, lon_min, lon_max = 30.85, 30.95, 75.80, 75.90
    demo_field = [  # Earth Engine wants [lon, lat]
        [lon_min, lat_min],
        [lon_max, lat_min],
        [lon_max, lat_max],
        [lon_min, lat_max],
    ]

    try:
        report, _details, _flagged, meta = generate_multisatellite_report(
            demo_field, "smoke-test", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        )
    except EarthEngineUnavailable as exc:
        sys.exit(f"Earth Engine is not ready: {exc}")

    print(report)
    print("\nLatest acquisitions:", meta["satellite_sources"])
