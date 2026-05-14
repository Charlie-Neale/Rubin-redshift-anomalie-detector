"""Light-curve peak detection from a Fink alert.

A Fink alert ships with `alert['prv_candidates']` — up to ~30 days of prior
detections of the same object. We use that history (plus the current detection)
to estimate the SN's peak r-band magnitude and decide whether the SN has
started fading. Only past-peak alerts produce a PeakInfo; still-brightening
alerts return None, and the orchestrator skips them until a later alert in the
same season sees the SN fade.

A hysteresis on the magnitude (PAST_PEAK_HYSTERESIS_MAG) prevents flagging on
noisy single-epoch dips.
"""

from __future__ import annotations

from dataclasses import dataclass

BAND_FOR_PEAK = 2  # ZTF fid: 1=g, 2=r, 3=i. r is the Ia workhorse.
MIN_BAND_DETECTIONS = 3
PAST_PEAK_HYSTERESIS_MAG = 0.1


@dataclass
class PeakInfo:
    peak_magpsf: float
    peak_jd: float
    fid: int
    n_detections_in_band: int


def extract_peak_for_anomaly(alert: dict) -> PeakInfo | None:
    current = alert.get("candidate") or {}
    history = alert.get("prv_candidates") or []

    samples = [current] + list(history)
    band_samples = [
        s for s in samples
        if s.get("fid") == BAND_FOR_PEAK and s.get("magpsf") is not None
    ]
    if len(band_samples) < MIN_BAND_DETECTIONS:
        return None

    peak = min(band_samples, key=lambda s: s["magpsf"])

    current_magpsf = current.get("magpsf")
    current_jd = current.get("jd")
    if current_magpsf is None or current_jd is None:
        return None

    if current_magpsf < peak["magpsf"] + PAST_PEAK_HYSTERESIS_MAG:
        return None
    if current_jd <= peak["jd"]:
        return None

    return PeakInfo(
        peak_magpsf=float(peak["magpsf"]),
        peak_jd=float(peak["jd"]),
        fid=BAND_FOR_PEAK,
        n_detections_in_band=len(band_samples),
    )
