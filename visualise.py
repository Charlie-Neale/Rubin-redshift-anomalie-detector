"""Pandas/Plotly helpers shared by the Streamlit dashboard.

No Streamlit imports here — these functions are pure data + figure builders
so they can be unit-tested and reused in notebooks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from anomaly_log import COLUMNS, LOG_PATH

_NUMERIC_COLUMNS = [
    "ra", "dec", "peak_jd", "peak_magpsf", "fid",
    "z_host", "z_standard_candle",
    "d_l_host_mpc", "d_l_standard_candle_mpc",
    "anomaly_score", "peculiar_velocity_kms",
]


def load_anomalies(path: Path = LOG_PATH) -> pd.DataFrame:
    """Load anomalies.csv. Return an empty DataFrame with the right schema if missing."""
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(path)
    for col in _NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "run_timestamp_utc" in df.columns:
        df["run_timestamp_utc"] = pd.to_datetime(
            df["run_timestamp_utc"], errors="coerce", utc=True
        )
    return df


def filter_anomalies(
    df: pd.DataFrame,
    min_score: float | None = None,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    if min_score is not None:
        mask &= df["anomaly_score"].fillna(0) >= min_score
    if start_date is not None:
        mask &= df["run_timestamp_utc"] >= pd.Timestamp(start_date, tz="UTC")
    if end_date is not None:
        mask &= df["run_timestamp_utc"] <= pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    return df[mask]


def build_3d_scatter(df: pd.DataFrame) -> go.Figure:
    """3D scatter: RA × Dec × host luminosity distance, coloured by anomaly score."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            scene=dict(
                xaxis_title="RA (deg)",
                yaxis_title="Dec (deg)",
                zaxis_title="d_L host (Mpc)",
            ),
            title="No anomalies to display",
            height=600,
        )
        return fig

    hover = df.apply(
        lambda r: (
            f"<b>{r['objectId']}</b><br>"
            f"z_host = {r['z_host']:.4f}<br>"
            f"z_sc = {r['z_standard_candle']:.4f}<br>"
            f"v_pec = {r['peculiar_velocity_kms']:+.0f} km/s<br>"
            f"score = {r['anomaly_score']:.3f}<br>"
            f"TNS = {r.get('tns', '') or 'unclassified'}"
        ),
        axis=1,
    )
    fig = go.Figure(
        data=go.Scatter3d(
            x=df["ra"],
            y=df["dec"],
            z=df["d_l_host_mpc"],
            mode="markers",
            marker=dict(
                size=6,
                color=df["anomaly_score"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="anomaly score"),
            ),
            text=hover,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        scene=dict(
            xaxis_title="RA (deg)",
            yaxis_title="Dec (deg)",
            zaxis_title="d_L host (Mpc)",
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig


def generate_demo_data(n: int = 12, seed: int = 42) -> pd.DataFrame:
    """Synthetic anomalies for visualising the dashboard when anomalies.csv is empty."""
    import numpy as np

    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "run_timestamp_utc": (
            pd.to_datetime("2026-05-14T12:00:00Z")
            + pd.to_timedelta(rng.integers(0, 86400 * 7, n), unit="s")
        ),
        "objectId": [f"ZTF26aDEMO{i:03d}" for i in range(n)],
        "ra": rng.uniform(0, 360, n),
        "dec": rng.uniform(-30, 90, n),
        "peak_jd": rng.uniform(2461100, 2461200, n),
        "peak_magpsf": rng.uniform(16, 19, n),
        "fid": [2] * n,
        "z_host": rng.uniform(0.02, 0.08, n),
        "z_standard_candle": rng.uniform(0.02, 0.10, n),
        "d_l_host_mpc": rng.uniform(80, 350, n),
        "d_l_standard_candle_mpc": rng.uniform(80, 400, n),
        "anomaly_score": rng.uniform(0.1, 1.5, n),
        "peculiar_velocity_kms": rng.uniform(-15000, 15000, n),
        "tns": rng.choice(["SN Ia", "SN Ia-91T-like", ""], n),
    })
