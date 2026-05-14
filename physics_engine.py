"""Standard-candle physics for Type Ia supernovae.

Pure math, no I/O. Given an apparent magnitude and a host-galaxy redshift,
decide whether the SN's standard-candle distance is consistent with the
host's catalog distance, or whether the mismatch implies significant
peculiar velocity.
"""

from __future__ import annotations

from dataclasses import dataclass

import astropy.constants as const
import astropy.units as u
from astropy.cosmology import Planck18, z_at_value

ABSOLUTE_MAG_IA = -19.3
PECULIAR_VELOCITY_THRESHOLD_KMS = 1000.0
SPEED_OF_LIGHT_KMS = const.c.to("km/s").value
COSMOLOGY = Planck18

_Z_BRACKET = (1e-6, 5.0)


@dataclass
class AnomalyResult:
    z_host: float | None
    z_standard_candle: float
    d_l_host_mpc: float | None
    d_l_standard_candle_mpc: float
    anomaly_score: float | None
    peculiar_velocity_kms: float | None
    is_anomaly: bool


def distance_modulus(apparent_mag: float, absolute_mag: float = ABSOLUTE_MAG_IA) -> float:
    return apparent_mag - absolute_mag


def luminosity_distance_from_modulus(modulus: float) -> float:
    return 10 ** ((modulus - 25) / 5)


def redshift_from_luminosity_distance(d_l_mpc: float) -> float:
    return float(
        z_at_value(
            COSMOLOGY.luminosity_distance,
            d_l_mpc * u.Mpc,
            zmin=_Z_BRACKET[0],
            zmax=_Z_BRACKET[1],
        )
    )


def luminosity_distance_from_redshift(z: float) -> float:
    return float(COSMOLOGY.luminosity_distance(z).to("Mpc").value)


def compute_anomaly(
    apparent_mag: float,
    z_host: float | None,
    pec_velocity_threshold_kms: float = PECULIAR_VELOCITY_THRESHOLD_KMS,
) -> AnomalyResult:
    modulus = distance_modulus(apparent_mag)
    d_l_sc = luminosity_distance_from_modulus(modulus)
    z_sc = redshift_from_luminosity_distance(d_l_sc)

    if z_host is None:
        return AnomalyResult(
            z_host=None,
            z_standard_candle=z_sc,
            d_l_host_mpc=None,
            d_l_standard_candle_mpc=d_l_sc,
            anomaly_score=None,
            peculiar_velocity_kms=None,
            is_anomaly=False,
        )

    d_l_host = luminosity_distance_from_redshift(z_host)
    delta_z = z_sc - z_host
    v_pec = float(SPEED_OF_LIGHT_KMS * delta_z)
    return AnomalyResult(
        z_host=z_host,
        z_standard_candle=z_sc,
        d_l_host_mpc=d_l_host,
        d_l_standard_candle_mpc=d_l_sc,
        anomaly_score=abs(delta_z) / z_host,
        peculiar_velocity_kms=v_pec,
        is_anomaly=abs(v_pec) > pec_velocity_threshold_kms,
    )


if __name__ == "__main__":
    print("--- CLAUDE.md sanity (magpsf=18.5, z_host=0.077) ---")
    print(compute_anomaly(apparent_mag=18.5, z_host=0.077))
    print("\n--- No host (magpsf=19.03, z_host=None) ---")
    print(compute_anomaly(apparent_mag=19.03, z_host=None))
    print("\n--- Forced anomaly (magpsf=18.5, z_host=0.04) ---")
    print(compute_anomaly(apparent_mag=18.5, z_host=0.04))
