import ee
from datetime import datetime, timedelta, timezone
import json

# Initialize Earth Engine (run ee.Authenticate() interactively if needed)
# try:
#     ee.Initialize()
# except Exception:
#     ee.Authenticate()
#     ee.Initialize()
from dotenv import load_dotenv  # added to load env variables
import os                       # added for env var support
load_dotenv(dotenv_path=".env.local")  # load env variables

PROJECT_ID = os.environ.get("PROJECT_ID") 




# Initialize GEE
# ee.Authenticate()
ee.Initialize(project=PROJECT_ID)


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
        msavi = s2_stats.get('MSAVI', {}).get('mean')
        vari = s2_stats.get('VARI', {}).get('mean')
        status = []

        # Combined logic with explicit values
        if ndvi is not None and ndvi < 0.2 and ndwi is not None and ndwi < 0:
            status.append(
                f"Very low vegetation (NDVI={ndvi:.2f}) and active water stress (NDWI={ndwi:.2f}) — likely bare, failed emergence, or severe drought."
            )
        elif (ndvi and 0.2 <= ndvi < 0.4) and (ndwi and ndwi < 0.1) and (evi and evi < 0.3):
            status.append(
                f"Crop is struggling: thin canopy (EVI={evi:.2f}), low NDVI ({ndvi:.2f}), dry soil (NDWI={ndwi:.2f}) — could be drought onset, pests, or early stress."
            )
        elif (ndvi and 0.4 <= ndvi < 0.6) and (ndwi and ndwi > 0.2):
            status.append(
                f"Healthy, steadily growing crop with good water (NDVI={ndvi:.2f}, NDWI={ndwi:.2f}) — maintain regimen."
            )
        elif (ndvi and ndvi > 0.6) and (evi and evi > 0.5) and (ndwi and ndwi > 0.15):
            status.append(
                f"Field is at vegetative peak: vigorous NDVI={ndvi:.2f}, EVI={evi:.2f}, well-watered (NDWI={ndwi:.2f})."
            )
        else:
            status.append(
                f"Mixed crop condition: NDVI={ndvi}, EVI={evi}, NDWI={ndwi}. Combined indices do not strongly indicate a healthy or a severely stressed field."
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
                f"Significant spatial variability present (NDVI stdDev={ndvi_std:.2f}) — patchy emergence or management differences, apply zone-based treatment."
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
                f"Extremely low NDVI ({ndvi:.2f}) and low NDWI ({ndwi:.2f}) — bare soil or failed stand, perhaps recently harvested."
            )
        elif ndvi is not None and ndvi < 0.3:
            ls_status.append(
                f"Sparse vegetative cover (NDVI={ndvi:.2f}) — underperforming, yield limited."
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



# def generate_deep_interpretation(s2_stats, l8_stats, s1_stats, modis_stats, modis_lai_stats, modis_temp_stats, prev_stats=None):
#     interpretation = []
    
#     # --- Sentinel-2 (High-res) ---
#     if s2_stats:
#         ndvi = s2_stats.get('NDVI', {}).get('mean')
#         evi = s2_stats.get('EVI', {}).get('mean')
#         ndwi = s2_stats.get('NDWI', {}).get('mean')
#         ndre = s2_stats.get('NDRE', {}).get('mean')
#         savi = s2_stats.get('SAVI', {}).get('mean')
#         msavi = s2_stats.get('MSAVI', {}).get('mean')
#         vari = s2_stats.get('VARI', {}).get('mean')
#         ndvi_std = s2_stats.get('NDVI', {}).get('stdDev', 0)
#         evi_std = s2_stats.get('EVI', {}).get('stdDev', 0)
#         status = []
        
#         # Combined crop vigor and drought logic
#         if ndvi is not None and ndvi < 0.2 and ndwi is not None and ndwi < 0:
#             status.append("Very low vegetation and active water stress: likely bare, failed emergence, or severe drought.")
#         elif ndvi and 0.2 <= ndvi < 0.4 and ndwi and ndwi < 0.1 and evi and evi < 0.3:
#             status.append("Crop is struggling: thin canopy, dry soil—could be drought onset, pests, or early growth stress.")
#         elif ndvi and 0.4 <= ndvi < 0.6 and ndwi and ndwi > 0.2:
#             status.append("Healthy, steadily growing crop with good water conditions.")
#         elif ndvi and ndvi > 0.6 and evi and evi > 0.5 and ndwi and ndwi > 0.15:
#             status.append("Crop field is at or near vegetative peak; monitor for lodging or disease if NDWI > 0.3.")
#         else:
#             status.append("Mixed vegetation vigor and moderate stress; patches might be performing, but whole-field yield could be limited.")

#         if ndre is not None:
#             if ndre < 0.13:
#                 status.append("Nitrogen likely deficient or crop is in early growth phase.")
#             elif ndre < 0.2:
#                 status.append("Borderline/low nitrogen: consider split or foliar application.")
#             elif ndre > 0.3:
#                 status.append("Robust nitrogen uptake and strong chlorophyll content.")

#         # Variability and spatial advice
#         if ndvi_std and ndvi_std > 0.12:
#             status.append("Strong intra-field NDVI variability: indicates patchy emergence or management differences. Apply zone-based treatments.")

#         if savi is not None and savi < 0.3:
#             status.append("Field is mostly bare; consider resowing or weed management.")

#         interpretation.append("**Sentinel-2 Analysis:**\n- " + "\n- ".join(status))

#     # --- Landsat 8 (Medium-res) ---
#     if l8_stats:
#         ndvi = l8_stats.get('NDVI', {}).get('mean')
#         ndwi = l8_stats.get('NDWI', {}).get('mean')
#         evi = l8_stats.get('EVI', {}).get('mean')
#         temp = l8_stats.get('SurfaceTemp', {}).get('mean', None)
#         temp_status = ""
#         if temp is not None:
#             if temp < 10:
#                 temp_status = "Likely early day/acquisition or cold snap—no heat risk present."
#             elif temp > 34:
#                 temp_status = "High surface temp: risk of heat and drought stress."
#             else:
#                 temp_status = "Normal crop temperature range; no acute heat issue."
#         ls_status = []
#         if ndvi is not None and ndvi < 0.15 and ndwi is not None and ndwi < 0.12:
#             ls_status.append("Very low vegetation and poor moisture: likely bare, stressed, or recently harvested.")
#         elif ndvi is not None and ndvi < 0.3:
#             ls_status.append("Underperforming crop, sparse vegetative cover—yields will be limited.")
#         if evi is not None and evi < 0.2:
#             ls_status.append("Canopy expansion is stunted.")
#         interpretation.append("**Landsat 8 Analysis:**\n- " + "\n- ".join(ls_status + ([f"Surface temperature: {temp:.2f}°C. {temp_status}"] if temp else [])))

#     # --- Sentinel-1 SAR Moisture/Structure ---
#     if s1_stats and s1_stats.get('VV', {}).get('mean') is not None:
#         vv = s1_stats['VV']['mean']
#         vh = s1_stats.get('VH', {}).get('mean')
#         sar_msg = []
#         if vv is not None and vv > -10:
#             sar_msg.append("SAR backscatter high: peak crop or persistent soil moisture.")
#         elif vv is not None and vv < -15 and vh is not None and vh < -18:
#             sar_msg.append("Very dry, bare, or recently tilled soil detected.")
#         elif vv is not None and vh is not None:
#             sar_msg.append("RADAR indicates intermediate coverage; may reflect regrowth or partial crop loss.")
#         interpretation.append("**Sentinel-1 SAR:**\n- " + " / ".join(sar_msg))

#     # --- MODIS NDVI/EVI/LAI, with scale factor fix ---
#     if modis_stats:
#         ndvi = modis_stats.get('NDVI', {}).get('mean')
#         evi = modis_stats.get('EVI', {}).get('mean')
#         if ndvi is not None and evi is not None:
#             ndvi_c = ndvi * 0.0001 if ndvi > 1 else ndvi
#             evi_c = evi * 0.0001 if evi > 1 else evi
#             if ndvi_c < 0.3 and evi_c < 0.25:
#                 interpretation.append("**MODIS NDVI/EVI**: Large-scale stress, with regional NDVI/EVI below crop growth benchmarks.")
#             elif ndvi_c > 0.5 and evi_c > 0.3:
#                 interpretation.append("**MODIS NDVI/EVI**: Field is comparatively healthy at landscape scale.")
#     if modis_lai_stats:
#         lai = modis_lai_stats.get('Lai_500m', {}).get('mean')
#         if lai is not None:
#             if lai < 2:
#                 interpretation.append("**MODIS LAI**: Weak canopy; stands are sparse, significant stand loss possible.")
#             elif 2 <= lai < 4:
#                 interpretation.append("**MODIS LAI**: Target for healthy wheat/maize is 3–5; field is moderate, may be N or water limited.")
#             else:
#                 interpretation.append("**MODIS LAI**: Good leaf area; likely above-average yield if stress is short-term.")

#     # --- Temporal change/trend integration (optional, if you store previous stats) ---
#     # if prev_stats: (e.g., compare NDVI, NDWI, LAI for trend detection and alert on rapid drops)
#     # You may also auto-detect yield scenarios, heat/drought impact, etc.

#     return "\n\n".join(interpretation)



from sklearn.cluster import DBSCAN
import numpy as np

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
    clustered_flagged = []
    clusters = {}
    for idx, label in enumerate(labels):
        if label == -1: continue  # ignore "noise"
        clusters.setdefault(label, []).append(flagged_areas[idx])
    
    # Compose results
    result = []
    if n_clusters == 0:
        result.append("Flagged areas are scattered single points—no clustering detected. These are most likely isolated anomalies or natural field micro-variability.")
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
    result.append("\n*Each coordinate marks the center of a detected stress cluster—scout these first.*\n")
    
    # Parameter/context diagnostics
    all_params = [p['parameter'] for ps in clusters.values() for p in ps]
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
        mean_ndre = np.mean(ndre_vals)
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
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': image.select('B8'), 'RED': image.select('B4'), 'BLUE': image.select('B2')}
    ).rename('EVI')
    ndwi = image.normalizedDifference(['B8', 'B11']).rename('NDWI')
    savi = image.expression(
        '((NIR - RED) * (1 + L)) / (NIR + RED + L)',
        {'NIR': image.select('B8'), 'RED': image.select('B4'), 'L': 0.5}
    ).rename('SAVI')
    msavi = image.expression(
        '0.5 * (2 * NIR + 1 - sqrt((2 * NIR + 1)**2 - 8 * (NIR - RED)))',
        {'NIR': image.select('B8').float(), 'RED': image.select('B4').float()}
    ).rename('MSAVI')
    ndre = image.normalizedDifference(['B8', 'B5']).rename('NDRE')
    vari = image.expression(
        '(GREEN - RED)/(GREEN + RED - BLUE)',
        {'GREEN': image.select('B3'), 'RED': image.select('B4'), 'BLUE': image.select('B2')}
    ).rename('VARI')
    image = image.addBands([ndvi, evi, ndwi, savi, msavi, ndre, vari])
    return image

def add_sentinel1_sar_indices(image):
    if image:
        vv = image.select('VV')
        vh = image.select('VH')
        vh_vv_ratio = vh.divide(vv).rename('VH_VV_RATIO')
        vh_vv_diff = vh.subtract(vv).rename('VH_VV_DIFF')
        image = image.addBands([vh_vv_ratio, vh_vv_diff])
        return image
    return None

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
                    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
                except Exception:
                    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    except Exception:
        pass
    return "Not available"

def get_latest(collection_id, aoi, start, end, cloud_filter=None, bands=None, proc_func=None, scale=10):
    """Enhanced function to get latest image with flexible statistics collection."""
    col = ee.ImageCollection(collection_id).filterBounds(aoi).filterDate(start, end)
    if cloud_filter:
        col = col.filter(cloud_filter)
    img = col.sort('system:time_start', False).first()
    if img and proc_func:
        img = proc_func(img)
    elif not img:
        return None, "Not available", {}
    
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
    """Add Landsat-8 specific indices."""
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    ndwi = image.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDWI')
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': image.select('SR_B5'), 'RED': image.select('SR_B4'), 'BLUE': image.select('SR_B2')}
    ).rename('EVI')
    temp = image.select('ST_B10').multiply(0.00341802).add(149.0).rename('SurfaceTemp')
    return image.addBands([ndvi, ndwi, evi, temp])

def add_sar_indices(image):
    """Add SAR indices (alias for existing function)."""
    return add_sentinel1_sar_indices(image)

# Add index bands configuration
INDEX_BANDS = {
    'Sentinel-2': ['NDVI', 'NDWI', 'EVI', 'NDRE', 'SAVI', 'MSAVI', 'VARI'],
    'Landsat-8': ['NDVI', 'NDWI', 'EVI', 'SurfaceTemp'],
    'Sentinel-1': ['VV', 'VH', 'VH_VV_RATIO', 'VH_VV_DIFF']
}

def get_latest_image_and_date(collection_id, geometry, start_date, end_date, filter_dict, sort_field='system:time_start'):
    col = ee.ImageCollection(collection_id).filterBounds(geometry).filterDate(start_date, end_date)
    for f, v in filter_dict.items():
        if isinstance(v, (int, float)):
            col = col.filter(ee.Filter.lt(f, v))
        elif isinstance(v, str):
            col = col.filter(ee.Filter.eq(f, v))
        else:
            col = col.filter(v)
    col = col.sort(sort_field, False)
    img = col.first()
    dt = "Not available"
    if img:
        img_info = img.getInfo()
        timestamp_keys = ['system:time_start', 'system:time_end']
        for key in timestamp_keys:
            if img_info['properties'].get(key):
                ts = img_info['properties'][key] / 1000
                try:
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
                except Exception:
                    dt = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                break
    return img, dt

def get_latest_sentinel2_image(geometry, start_date, end_date):
    img, dt = get_latest_image_and_date(
        'COPERNICUS/S2_SR_HARMONIZED', geometry, start_date, end_date, {'CLOUDY_PIXEL_PERCENTAGE': 15}
    )
    return (add_all_indices(ee.Image(img)), dt) if img else (None, dt)

def get_latest_sentinel1_image(geometry, start_date, end_date):
    img, dt = get_latest_image_and_date(
        'COPERNICUS/S1_GRD',
        geometry,
        start_date,
        end_date,
        filter_dict={'instrumentMode': 'IW'}
    )
    return (add_sentinel1_sar_indices(ee.Image(img)), dt) if img else (None, dt)

def get_latest_landsat_image(geometry, start_date, end_date):
    img, dt = get_latest_image_and_date(
        'LANDSAT/LC08/C02/T1_L2', geometry, start_date, end_date, {'CLOUD_COVER': 15}
    )
    if img:
        image = ee.Image(img)
        ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        ndwi = image.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDWI')
        evi = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {'NIR': image.select('SR_B5'), 'RED': image.select('SR_B4'), 'BLUE': image.select('SR_B2')}
        ).rename('EVI')
        temp = image.select('ST_B10').multiply(0.00341802).add(149.0).rename('SurfaceTemp')
        image = image.addBands([ndvi, ndwi, evi, temp])
        return (image, dt)
    return (None, dt)

def get_latest_modis_img(geometry, start_date, end_date):
    img, dt = get_latest_image_and_date(
        'MODIS/061/MOD15A2H', geometry, start_date, end_date, {}
    )
    return (ee.Image(img), dt) if img else (None, dt)

def get_image_statistics(image, geometry, scale=10):
    if not image:
        return {}
    reducers = ee.Reducer.mean() \
        .combine(ee.Reducer.stdDev(), sharedInputs=True) \
        .combine(ee.Reducer.min(), sharedInputs=True) \
        .combine(ee.Reducer.max(), sharedInputs=True)
    stats = image.reduceRegion(reducer=reducers, geometry=geometry, scale=scale, maxPixels=1e9).getInfo()
    results = {}
    for key, value in stats.items():
        band, stat = key.rsplit('_', 1)
        if band not in results:
            results[band] = {}
        results[band][stat] = value
    return results

def generate_interpretation(s2_stats, l8_stats, s2_date, l8_date):
    llm_report = []

    if s2_stats:
        ndvi = s2_stats.get('NDVI', {}).get('mean')
        ndwi = s2_stats.get('NDWI', {}).get('mean')
        ndre = s2_stats.get('NDRE', {}).get('mean')
        evi  = s2_stats.get('EVI', {}).get('mean')
        savi = s2_stats.get('SAVI', {}).get('mean')
        msavi = s2_stats.get('MSAVI', {}).get('mean')
        vari = s2_stats.get('VARI', {}).get('mean')
        s2text = (
            f"As of {s2_date} (Sentinel-2):\n"
            f"  - NDVI: {ndvi:.2f} ({interpret('NDVI', ndvi)})\n"
            f"  - NDWI: {ndwi:.2f} ({interpret('NDWI', ndwi)})\n"
            f"  - NDRE: {ndre:.2f} ({interpret('NDRE', ndre)})\n"
            f"  - SAVI: {savi:.2f} ({interpret('SAVI', savi)})\n"
            f"  - MSAVI: {msavi:.2f} ({interpret('MSAVI', msavi)})\n"
            f"  - EVI: {evi:.2f} ({interpret('EVI', evi)})\n"
            f"  - VARI: {vari:.2f} ({interpret('VARI', vari)})"
        )
        llm_report.append(s2text)
    else:
        llm_report.append(f"Sentinel-2: No valid image found in last 90 days.")

    if l8_stats:
        ndvi = l8_stats.get('NDVI', {}).get('mean')
        ndwi = l8_stats.get('NDWI', {}).get('mean')
        evi = l8_stats.get('EVI', {}).get('mean')
        temp = l8_stats.get('SurfaceTemp', {}).get('mean', None)
        temp_c = temp - 273.15 if temp is not None else None
        text = (
            f"As of {l8_date} (Landsat 8):\n"
            f"  - NDVI: {ndvi:.2f} ({interpret('NDVI', ndvi)})\n"
            f"  - NDWI: {ndwi:.2f} ({interpret('NDWI', ndwi)})\n"
            f"  - EVI: {evi:.2f} ({interpret('EVI', evi)})"
        )
        if temp_c is not None:
            if temp_c < 18:
                tmsg = "Cool soil/canopy 10ideal for crops"
            elif temp_c > 34:
                tmsg = "High temperature - potential heat stress"
            else:
                tmsg = "Normal temperature range"
            text += (f"\n  - Surface Temperature: {temp_c:.2f}B0C ({tmsg})")
        llm_report.append(text)
    else:
        llm_report.append(f"Landsat 8: No valid image found in last 90 days.")

    return "\n\n".join(llm_report)

def get_field_issue_flags(stats, bands, thresholds):
    flags = []
    for param, th in zip(bands, thresholds):
        mean_val = stats.get(param, {}).get('mean', None)
        if mean_val is not None:
            if mean_val < th[1]:
                flags.append({
                    'parameter': param,
                    'threshold_message': th[2],
                    'mean_value': mean_val
                })
    return flags

def generate_flagged_areas(image, geometry, bands, thresholds, scale=10):
    try:
        flagged_pixels = []
        message = "No flagged pixels found. Everything is within healthy thresholds."
        if not image:
            return flagged_pixels

        for param, th in zip(bands, thresholds):
            band_names = image.bandNames().getInfo()
            if param not in band_names:
                continue
            threshold_val = th[1]
            band_img = image.select(param)
            mask = band_img.lt(threshold_val)
            masked_img = band_img.updateMask(mask)
            if not masked_img:
                return flagged_pixels.append({"message": message})
            samples = masked_img.sample(region=geometry, scale=scale, geometries=True).getInfo()
            for feature in samples.get('features', []):
                coords = feature['geometry']['coordinates']
                props = feature['properties']
                flagged_pixels.append({
                    'message': "flagged aread detected",
                    'parameter': param,
                    'threshold_message': th[2],
                    'value': props.get(param),
                    'coordinates': coords
                })
        return flagged_pixels
    except Exception as e:
        print(f"Error generating flagged areas: {e}")
        flagged_pixels = []
        message = "No flagged pixels found. Everything is within healthy thresholds."
        return flagged_pixels.append({"message": message})
        

def generate_multisatellite_report(geometry_geojson, user_login, utc_now):
    geometry = ee.Geometry.Polygon(geometry_geojson)
    dt_now = datetime.strptime(utc_now, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
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
    # print(f"Sentinel-2 stats")
    
    # ---- Landsat-8
    l8, l8_date, l8_stats = get_latest(
        'LANDSAT/LC08/C02/T1_L2', geometry, start_date_str, end_date_str,
        cloud_filter=ee.Filter.lt('CLOUD_COVER', 15),
        bands=INDEX_BANDS['Landsat-8'], proc_func=add_indices_l8, scale=30
    )
    
    # ---- MODIS NDVI/EVI
    modis, modis_date, modis_stats = get_latest(
        'MODIS/061/MOD13Q1', geometry, start_date_str, end_date_str,
        bands=['NDVI', 'EVI'], scale=500
    )
    
    # ---- MODIS LAI/FPAR
    modis_lai, modis_lai_date, modis_lai_stats = get_latest(
        'MODIS/061/MOD15A2H', geometry, start_date_str, end_date_str,
        bands=['Lai_500m', 'Fpar_500m'], scale=500
    )
    
    # ---- MODIS Land Surface Temperature
    modis_temp, modis_temp_date, modis_temp_stats = get_latest(
        'MODIS/061/MOD11A1', geometry, start_date_str, end_date_str,
        bands=['LST_Day_1km'], scale=1000
    )
    
    # ---- Sentinel-1 SAR
    s1, s1_date, s1_stats = get_latest(
        'COPERNICUS/S1_GRD', geometry, start_date_str, end_date_str,
        cloud_filter=ee.Filter.eq('instrumentMode', 'IW'),
        bands=INDEX_BANDS['Sentinel-1'], proc_func=add_sar_indices, scale=10
    )
    # print (f"Sentinel-1 stats")

    llm_text_report = f"""
# Comprehensive Multi-Satellite Crop & Field Health Report

**User:** {user_login}  
**Analysis Date (UTC):** {utc_now}  
**Analysis Period:** {start_date_str} – {end_date_str}

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

    s2_flagged = get_field_issue_flags(s2_stats, ['NDVI', 'NDWI', 'NDRE'], [
        (None, 0.2, "NDVI low: possible sparse or stressed vegetation"),
        (None, 0.1, "NDWI low: likely dry/drought stress"),
        (None, 0.1, "NDRE low: potential N deficiency"),
    ])
    l8_flagged = get_field_issue_flags(l8_stats, ['NDVI', 'NDWI'], [
        (None, 0.2, "NDVI low: sparse or failed zones"),
        (None, 0.1, "NDWI low: water deficit"),
    ])

    try:


        flagged_areas = []
        flagged_areas.extend(s2_flagged)
        flagged_areas.extend(l8_flagged)

        flagged_coords_vals = []
        flagged_coords_vals.extend(generate_flagged_areas(s2, geometry, ['NDVI', 'NDWI', 'NDRE'], [
            (None, 0.2, "NDVI low: possible sparse or stressed vegetation"),
            (None, 0.1, "NDWI low: likely dry/drought stress"),
            (None, 0.1, "NDRE low: potential N deficiency"),
        ], scale=10)[:10])

        if l8 is not None:
            flagged_coords_vals.extend(generate_flagged_areas(l8, geometry, ['NDVI', 'NDWI'], [
                (None, 0.2, "NDVI low: sparse or failed zones"),
                (None, 0.1, "NDWI low: water deficit"),
            ], scale=30)[:10])

        if (flagged_coords_vals[0].get("message") == "No flagged pixels found. Everything is within healthy thresholds."):
            interpretation = flagged_coords_vals[0]["message"]
        else:
            interpretation = generate_flagged_area_interpretation(flagged_coords_vals)
        # llm_text_report += "\n" + interpretation + "\n"
    except Exception as e:
        print(f"Error generating flagged areas: {e}")
        # llm_text_report += "\nError generating flagged areas: " + str(e) + "\n"
        interpretation = "No flagged areas found "
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
    # interpretation = generate_flagged_area_interpretation(flagged_coords_vals)
    

    raw_details = {
        'sentinel2': {'stats': s2_stats, 'date': s2_date},
        'sentinel1': {'stats': s1_stats, 'date': s1_date},
        'landsat8': {'stats': l8_stats, 'date': l8_date},
        'modis_ndvi_evi': {'stats': modis_stats, 'date': modis_date},
        'modis_lai': {'stats': modis_lai_stats, 'date': modis_lai_date},
        'modis_lst': {'stats': modis_temp_stats, 'date': modis_temp_date}
    }

    return [llm_text_report, raw_details, flagged_coords_vals, metadata]

# ===== Example Usage =====
# if __name__ == '__main__':
#     user = 'YOUR_USER'
#     utc_now = '2025-07-19 11:24:00'
#     my_field =  [ [ 76.9707, 29.4292 ],  #// Southwest
#   [ 76.9780, 29.4292 ], # // Southeast
#   [ 76.9780, 29.4340 ], # // Northeast
#   [ 76.9707, 29.4340 ], # // Northwest
#   [ 76.9707, 29.4292 ]  # // Closing point
# ]
#     text_report, details, flagged, meta = generate_multisatellite_report(my_field, user, utc_now)
#     print('--- LLM Text Report ---')
#     print(text_report)
    # print('\n--- Raw Details ---')
    # print(json.dumps(details, indent=4))
    # print('\n--- Flagged Areas Sample (max 10) ---')
    # print(flagged[:10])
    # print('\n--- Metadata ---')
    # print(json.dumps(meta, indent=4))