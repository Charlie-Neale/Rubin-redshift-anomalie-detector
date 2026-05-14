"""Tests for light_curve.extract_peak_for_anomaly."""

from __future__ import annotations

from light_curve import (
    BAND_FOR_PEAK,
    PeakInfo,
    extract_peak_for_anomaly,
)
from tests.fixtures.sample_alerts import (
    ALERT_HOST_BRIGHTENING,
    ALERT_HOST_PAST_PEAK,
)


def test_below_min_detections_returns_none():
    alert = {
        "candidate": {"magpsf": 18.0, "jd": 2461000.0, "fid": 2},
        "prv_candidates": [],
    }
    assert extract_peak_for_anomaly(alert) is None


def test_still_brightening_returns_none():
    # current is the brightest in band → no past-peak hysteresis satisfied.
    assert extract_peak_for_anomaly(ALERT_HOST_BRIGHTENING) is None


def test_past_peak_returns_peakinfo():
    result = extract_peak_for_anomaly(ALERT_HOST_PAST_PEAK)
    assert result is not None
    assert isinstance(result, PeakInfo)
    assert result.peak_magpsf == 17.66
    assert result.peak_jd == 2461169.78
    assert result.fid == BAND_FOR_PEAK
    assert result.n_detections_in_band == 5


def test_mixed_bands_only_r_counted():
    alert = {
        "candidate": {"magpsf": 18.50, "jd": 2461180.0, "fid": 2},
        "prv_candidates": [
            {"magpsf": 17.40, "jd": 2461170.0, "fid": 1},
            {"magpsf": 17.50, "jd": 2461172.0, "fid": 1},
            {"magpsf": 17.60, "jd": 2461174.0, "fid": 2},
            {"magpsf": 17.80, "jd": 2461175.0, "fid": 2},
        ],
    }
    result = extract_peak_for_anomaly(alert)
    assert result is not None
    assert result.peak_magpsf == 17.60
    assert result.n_detections_in_band == 3


def test_magpsf_none_filtered_out():
    alert = {
        "candidate": {"magpsf": 18.50, "jd": 2461180.0, "fid": 2},
        "prv_candidates": [
            {"magpsf": None, "jd": 2461170.0, "fid": 2},
            {"magpsf": 17.60, "jd": 2461174.0, "fid": 2},
            {"magpsf": 17.80, "jd": 2461175.0, "fid": 2},
        ],
    }
    result = extract_peak_for_anomaly(alert)
    assert result is not None
    assert result.n_detections_in_band == 3
    assert result.peak_magpsf == 17.60


def test_below_hysteresis_returns_none():
    # 0.05 mag of fading isn't enough — must be ≥0.10 mag to count as past peak.
    alert = {
        "candidate": {"magpsf": 17.65, "jd": 2461180.0, "fid": 2},
        "prv_candidates": [
            {"magpsf": 17.60, "jd": 2461174.0, "fid": 2},
            {"magpsf": 17.80, "jd": 2461175.0, "fid": 2},
        ],
    }
    assert extract_peak_for_anomaly(alert) is None
