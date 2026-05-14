"""Tests for visualise: data loading, filtering, and chart construction."""

from __future__ import annotations

import pandas as pd

from anomaly_log import COLUMNS
from visualise import (
    build_3d_scatter,
    filter_anomalies,
    generate_demo_data,
    load_anomalies,
)


def test_load_anomalies_missing_file_returns_empty(tmp_path):
    df = load_anomalies(tmp_path / "does-not-exist.csv")
    assert df.empty
    assert list(df.columns) == COLUMNS


def test_load_anomalies_empty_file_returns_empty(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    df = load_anomalies(path)
    assert df.empty


def test_load_anomalies_reads_csv_with_correct_dtypes(tmp_path):
    path = tmp_path / "anomalies.csv"
    generate_demo_data(n=3).to_csv(path, index=False)
    df_out = load_anomalies(path)
    assert len(df_out) == 3
    assert pd.api.types.is_numeric_dtype(df_out["anomaly_score"])
    assert pd.api.types.is_datetime64_any_dtype(df_out["run_timestamp_utc"])


def test_filter_anomalies_by_min_score():
    df = generate_demo_data(n=10, seed=1)
    median = df["anomaly_score"].median()
    high = filter_anomalies(df, min_score=median)
    assert (high["anomaly_score"] >= median).all()
    assert len(high) <= len(df)


def test_filter_anomalies_empty_input_returns_empty():
    df = pd.DataFrame(columns=COLUMNS)
    assert filter_anomalies(df, min_score=0.5).empty


def test_build_3d_scatter_empty_handles_gracefully():
    fig = build_3d_scatter(pd.DataFrame(columns=COLUMNS))
    assert fig is not None
    assert fig.layout.title.text == "No anomalies to display"


def test_build_3d_scatter_with_data():
    df = generate_demo_data(n=5)
    fig = build_3d_scatter(df)
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter3d"
    assert len(fig.data[0].x) == 5


def test_generate_demo_data_shape():
    df = generate_demo_data(n=7)
    assert len(df) == 7
    assert "objectId" in df.columns
    assert (df["fid"] == 2).all()
