"""Tests for redshift_resolver: Mangrove parsing and edge cases."""

from __future__ import annotations

import pytest

from redshift_resolver import resolve_z


def _alert_with_lum_dist(lum_dist):
    return {"mangrove": {"lum_dist": lum_dist}}


def test_resolve_z_from_real_alert_1():
    # ZTF26aarzhok: host at 104.53 Mpc
    z = resolve_z(_alert_with_lum_dist("104.533613914"))
    assert z is not None
    assert z == pytest.approx(0.024, abs=0.005)


def test_resolve_z_from_real_alert_2():
    # ZTF26aauvgeo: host at 221.04 Mpc
    z = resolve_z(_alert_with_lum_dist("221.038974964"))
    assert z is not None
    assert z == pytest.approx(0.050, abs=0.005)


def test_resolve_z_missing_host():
    # ZTF26aahuhpc: no host match in alert payload
    assert resolve_z(_alert_with_lum_dist("None")) is None


def test_resolve_z_missing_mangrove_key():
    assert resolve_z({}) is None


def test_resolve_z_empty_mangrove_dict():
    assert resolve_z({"mangrove": {}}) is None


def test_resolve_z_empty_string():
    assert resolve_z(_alert_with_lum_dist("")) is None


def test_resolve_z_nan_string():
    assert resolve_z(_alert_with_lum_dist("nan")) is None


def test_resolve_z_negative():
    assert resolve_z(_alert_with_lum_dist("-5.0")) is None


def test_resolve_z_zero():
    assert resolve_z(_alert_with_lum_dist("0")) is None


def test_resolve_z_non_numeric():
    assert resolve_z(_alert_with_lum_dist("foo")) is None
