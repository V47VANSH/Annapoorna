"""Tests for the report text built from satellite stats (no Earth Engine calls)."""

import sattelite_report as sat

HEALTHY_S2 = {
    "NDVI": {"mean": 0.72, "stdDev": 0.05},
    "EVI": {"mean": 0.55},
    "NDWI": {"mean": 0.25},
    "NDRE": {"mean": 0.35},
    "SAVI": {"mean": 0.6},
    "MSAVI": {"mean": 0.7},
    "VARI": {"mean": 0.2},
}


class TestSurfaceTemperature:
    def test_summary_reports_celsius(self):
        text = sat.generate_interpretation({}, {"SurfaceTemp": {"mean": 27.5}}, "", "2025-07-15")
        assert "27.50°C" in text
        assert "Normal temperature range" in text

    def test_deep_interpretation_does_not_mistake_celsius_for_heat_stress(self):
        text = sat.generate_deep_interpretation(
            {}, {"SurfaceTemp": {"mean": 27.5}, "NDVI": {"mean": 0.5}}, {}, {}, {}, {}
        )
        assert "Normal field temperature 27.50°C" in text
        assert "heat stress" not in text

    def test_genuine_heat_is_still_flagged(self):
        text = sat.generate_interpretation({}, {"SurfaceTemp": {"mean": 41.0}}, "", "")
        assert "heat stress" in text


class TestMissingValues:
    def test_summary_tolerates_missing_bands(self):
        text = sat.generate_interpretation({"NDVI": {"mean": 0.5}}, {}, "2025-07-15", "")
        assert "NDVI: 0.50" in text
        assert "EVI: n/a" in text

    def test_deep_interpretation_tolerates_missing_bands(self):
        text = sat.generate_deep_interpretation({"NDVI": {}}, {}, {}, {}, {}, {})
        assert "Sentinel-2" in text

    def test_no_imagery_is_reported_as_such(self):
        text = sat.generate_interpretation({}, {}, "", "")
        assert "Sentinel-2: No valid image" in text
        assert "Landsat 8: No valid image" in text


class TestScaledInputs:
    def test_healthy_field_is_described_as_healthy(self):
        text = sat.generate_deep_interpretation(HEALTHY_S2, {}, {}, {}, {}, {})
        assert "vegetative peak" in text

    def test_lai_thresholds_apply_to_real_lai(self):
        text = sat.generate_deep_interpretation(
            {}, {}, {}, {}, {"Lai_500m": {"mean": 1.5}}, {}
        )
        assert "poor (sparse)" in text


class TestFlaggedAreas:
    def test_no_image_yields_no_flags(self):
        assert sat.generate_flagged_areas(None, None, ["NDVI"], [(None, 0.2, "low")]) == []

    def test_clusters_are_described(self):
        points = [
            {
                "message": "flagged area detected",
                "parameter": "NDVI",
                "threshold_message": "NDVI low",
                "value": 0.1 + i * 0.001,
                "coordinates": [75.85 + i * 0.0001, 30.90],
            }
            for i in range(6)
        ]

        text = sat.generate_flagged_area_interpretation(points)

        assert text
        assert "NDVI" in text


def test_sample_cap_stays_under_the_earth_engine_limit():
    assert sat.MAX_FLAGGED_SAMPLES < 5000
