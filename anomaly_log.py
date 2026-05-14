"""Append anomaly rows to a local CSV that the Phase 4 dashboard reads."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from light_curve import PeakInfo
from physics_engine import AnomalyResult

LOG_PATH = Path("anomalies.csv")
COLUMNS = [
    "run_timestamp_utc",
    "objectId",
    "ra",
    "dec",
    "peak_jd",
    "peak_magpsf",
    "fid",
    "z_host",
    "z_standard_candle",
    "d_l_host_mpc",
    "d_l_standard_candle_mpc",
    "anomaly_score",
    "peculiar_velocity_kms",
    "tns",
]


def append(
    alert: dict,
    result: AnomalyResult,
    peak: PeakInfo,
    log_path: Path = LOG_PATH,
) -> None:
    candidate = alert.get("candidate") or {}
    row = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "objectId": alert.get("objectId"),
        "ra": candidate.get("ra"),
        "dec": candidate.get("dec"),
        "peak_jd": peak.peak_jd,
        "peak_magpsf": peak.peak_magpsf,
        "fid": peak.fid,
        "z_host": result.z_host,
        "z_standard_candle": result.z_standard_candle,
        "d_l_host_mpc": result.d_l_host_mpc,
        "d_l_standard_candle_mpc": result.d_l_standard_candle_mpc,
        "anomaly_score": result.anomaly_score,
        "peculiar_velocity_kms": result.peculiar_velocity_kms,
        "tns": alert.get("tns"),
    }
    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
