"""Streamlit dashboard for visualising peculiar-velocity anomalies.

Run with:
    .venv/bin/streamlit run dashboard.py

Reads anomalies.csv (produced by nightly_runner.py). When the CSV is empty,
toggle the **Use demo data** switch in the sidebar to load a synthetic
dataset and inspect the layout.
"""

from __future__ import annotations

import streamlit as st

from anomaly_log import LOG_PATH
from visualise import (
    build_3d_scatter,
    filter_anomalies,
    generate_demo_data,
    load_anomalies,
)

st.set_page_config(page_title="SN Ia Peculiar Velocity Anomalies", layout="wide")
st.title("SN Ia Peculiar Velocity Anomalies")
st.caption(
    "Type Ia supernovae whose standard-candle distance disagrees with their host's "
    "catalog distance by > 1000 km/s. Data from `anomalies.csv` (Fink / ZTF stream)."
)

with st.sidebar:
    st.header("Source")
    demo = st.toggle(
        "Use demo data",
        value=False,
        help="Synthetic anomalies for testing the layout when anomalies.csv is empty.",
    )
    df = generate_demo_data() if demo else load_anomalies()

    st.header("Filters")
    if df.empty:
        st.info("No data to filter.")
        min_score = 0.0
        start_date = end_date = None
    else:
        score_min = float(df["anomaly_score"].min())
        score_max = float(df["anomaly_score"].max())
        min_score = st.slider(
            "Min anomaly score",
            min_value=score_min,
            max_value=score_max,
            value=score_min,
            step=max((score_max - score_min) / 100, 0.001),
        )
        ts = df["run_timestamp_utc"].dropna()
        if not ts.empty:
            date_range = st.date_input(
                "Date range",
                value=(ts.min().date(), ts.max().date()),
                min_value=ts.min().date(),
                max_value=ts.max().date(),
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = end_date = None
        else:
            start_date = end_date = None

filtered = filter_anomalies(
    df, min_score=min_score, start_date=start_date, end_date=end_date
)

c1, c2, c3 = st.columns(3)
c1.metric("Anomalies (filtered)", len(filtered))
c2.metric(
    "Median |v_pec| (km/s)",
    f"{filtered['peculiar_velocity_kms'].abs().median():.0f}" if not filtered.empty else "—",
)
c3.metric(
    "Median anomaly score",
    f"{filtered['anomaly_score'].median():.2f}" if not filtered.empty else "—",
)

if df.empty:
    st.warning(
        f"`{LOG_PATH}` is empty or missing. Run `nightly_runner.py` to populate it, "
        "or toggle **Use demo data** in the sidebar."
    )
    st.stop()

st.subheader("3D sky map")
st.plotly_chart(build_3d_scatter(filtered), width="stretch")

st.subheader("Anomalies")
st.dataframe(
    filtered[
        [
            "objectId", "tns", "ra", "dec",
            "z_host", "z_standard_candle",
            "d_l_host_mpc", "anomaly_score", "peculiar_velocity_kms",
            "peak_magpsf", "peak_jd", "run_timestamp_utc",
        ]
    ],
    width="stretch",
    hide_index=True,
)
