"""Resolve a host-galaxy redshift for a Fink alert.

Today: only the Mangrove crossmatch (`alert['mangrove']['lum_dist']`).
Returns None when no host is matched, leaving downstream code to skip the
alert. Future option (b) extensions (TNS spec-z, NED query) should be
added inside resolve_z and tried in order without changing its signature.
"""

from __future__ import annotations

from physics_engine import redshift_from_luminosity_distance

_MISSING_VALUES = {None, "None", "", "nan", "NaN", "null"}


def resolve_z(alert: dict) -> float | None:
    mangrove = alert.get("mangrove") or {}
    raw = mangrove.get("lum_dist")
    if raw in _MISSING_VALUES:
        return None
    try:
        d_l_mpc = float(raw)
    except (TypeError, ValueError):
        return None
    if d_l_mpc <= 0:
        return None
    return redshift_from_luminosity_distance(d_l_mpc)
