"""Tests for anomaly_log.append (CSV writer with header creation)."""

from __future__ import annotations

import csv

import anomaly_log
from light_curve import PeakInfo
from physics_engine import AnomalyResult


def _sample():
    alert = {
        "objectId": "ZTF26aTEST",
        "candidate": {"ra": 100.0, "dec": -20.0},
        "tns": "SN Ia",
    }
    result = AnomalyResult(
        z_host=0.05,
        z_standard_candle=0.10,
        d_l_host_mpc=220.0,
        d_l_standard_candle_mpc=460.0,
        anomaly_score=1.0,
        peculiar_velocity_kms=14990.0,
        is_anomaly=True,
    )
    peak = PeakInfo(peak_magpsf=17.5, peak_jd=2461000.0, fid=2, n_detections_in_band=5)
    return alert, result, peak


def test_writes_header_when_file_is_new(tmp_path):
    path = tmp_path / "anomalies.csv"
    alert, result, peak = _sample()
    anomaly_log.append(alert, result, peak, log_path=path)
    with path.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == anomaly_log.COLUMNS
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["objectId"] == "ZTF26aTEST"
    assert float(rows[0]["peculiar_velocity_kms"]) == 14990.0
    assert float(rows[0]["z_host"]) == 0.05


def test_appends_without_duplicating_header(tmp_path):
    path = tmp_path / "anomalies.csv"
    alert, result, peak = _sample()
    anomaly_log.append(alert, result, peak, log_path=path)
    anomaly_log.append(alert, result, peak, log_path=path)
    anomaly_log.append(alert, result, peak, log_path=path)
    with path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    header_count = sum(
        1 for line in path.read_text().splitlines()
        if line.startswith("run_timestamp_utc")
    )
    assert header_count == 1
