"""Tests for physics_engine: distance modulus, redshift round-trips, anomaly logic."""

from __future__ import annotations

import pytest

from physics_engine import (
    ABSOLUTE_MAG_IA,
    compute_anomaly,
    distance_modulus,
    luminosity_distance_from_modulus,
    luminosity_distance_from_redshift,
    redshift_from_luminosity_distance,
)


def test_distance_modulus():
    assert distance_modulus(18.5) == pytest.approx(18.5 - ABSOLUTE_MAG_IA)
    assert distance_modulus(20.0, -19.0) == pytest.approx(39.0)


def test_luminosity_distance_from_modulus():
    # μ = 25 ⇔ d_L = 10 pc * 10^5 = 1 Mpc; μ = 30 ⇔ 10 Mpc
    assert luminosity_distance_from_modulus(25) == pytest.approx(1.0)
    assert luminosity_distance_from_modulus(30) == pytest.approx(10.0)


def test_redshift_distance_roundtrip():
    for z in (0.01, 0.05, 0.1, 0.3, 1.0):
        d_l = luminosity_distance_from_redshift(z)
        z_back = redshift_from_luminosity_distance(d_l)
        assert z_back == pytest.approx(z, rel=1e-4)


def test_claude_md_sanity():
    modulus = distance_modulus(18.5)
    d_l = luminosity_distance_from_modulus(modulus)
    z = redshift_from_luminosity_distance(d_l)
    assert modulus == pytest.approx(37.8, abs=0.1)
    assert d_l == pytest.approx(363, rel=0.05)
    assert z == pytest.approx(0.077, rel=0.05)


def test_compute_anomaly_no_host():
    result = compute_anomaly(apparent_mag=18.5, z_host=None)
    assert result.z_host is None
    assert result.z_standard_candle == pytest.approx(0.077, rel=0.05)
    assert result.anomaly_score is None
    assert result.peculiar_velocity_kms is None
    assert result.is_anomaly is False
    assert result.d_l_standard_candle_mpc == pytest.approx(363, rel=0.05)
    assert result.d_l_host_mpc is None


def test_compute_anomaly_matched():
    result = compute_anomaly(apparent_mag=18.5, z_host=0.077)
    assert result.is_anomaly is False
    assert result.anomaly_score == pytest.approx(0, abs=0.05)
    assert abs(result.peculiar_velocity_kms) < 1000


def test_compute_anomaly_flagged():
    result = compute_anomaly(apparent_mag=18.5, z_host=0.04)
    assert result.is_anomaly is True
    assert result.anomaly_score is not None
    assert abs(result.peculiar_velocity_kms) > 1000


def test_compute_anomaly_velocity_signed():
    # v_pec carries the sign of (z_sc - z_host).
    pos = compute_anomaly(apparent_mag=18.5, z_host=0.04)
    neg = compute_anomaly(apparent_mag=18.5, z_host=0.12)
    assert pos.peculiar_velocity_kms > 0
    assert neg.peculiar_velocity_kms < 0
