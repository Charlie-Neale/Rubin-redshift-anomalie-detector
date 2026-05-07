# Fink SN Ia Peculiar Velocity Anomaly Detector

## Project Overview
This project connects to the Fink astronomical alert broker to detect Type Ia supernovae and identify peculiar velocity anomalies by comparing photometric redshift to expected redshift using distance modulus calculations. Anomalies are flagged, logged, and surfaced via GitHub issues and a Streamlit dashboard.

---

## Architecture

```
fink_connection.py    # Live Fink broker stream ingestion, filters for SN Ia alerts
physics_engine.py     # Computes distance modulus, luminosity distance, anomaly score
nightly_runner.py     # Scheduled script: detects anomalies, opens GitHub issues
dashboard.py          # Streamlit app: 3D Plotly scatter of galaxies, anomaly display
visualise.py          # Visualisation utilities (sky maps, plots)
```

---

## Physics Reference

### Distance Modulus
```
mew = apparent_magnitude - absolute_magnitude_Ia
```
- Absolute magnitude of SN Ia: **-19.3** (standard candle)
- `apparent_magnitude` comes from Rubin/Fink alert peak magnitude

### Luminosity Distance
```
d_L = 10 ** ((mew - 25) / 5)   # in Megaparsecs
```

### Redshift from Distance
Use `astropy.cosmology.Planck18` to convert luminosity distance → expected redshift z.

### Anomaly Score
```
anomaly_score = abs(observed_z - expected_z) / expected_z
```

### Peculiar Velocity Threshold
Flag alerts where peculiar velocity deviation > **1000 km/s** (convert from delta-z using `v = c * delta_z`).

---

## Key Dependencies

```bash
pip install fink-client astropy pandas streamlit plotly PyGithub
```

---

## Development Phases

Build in this order — do not skip ahead:

1. **fink_connection.py** — Connect to Fink stream, filter SN Ia, print raw alerts. Verify stream works before adding physics.
2. **physics_engine.py** — Standalone module, testable with hardcoded sample alert. No I/O dependencies.
3. **nightly_runner.py** — Calls fink_connection + physics_engine, opens GitHub issue if anomaly detected.
4. **dashboard.py + visualise.py** — Streamlit app, only after data pipeline is confirmed working.

---

## GitHub Issue Format (for anomalies)

When `nightly_runner.py` detects an anomaly, open a GitHub issue with:
- Alert ID and SN Ia candidate name
- RA / Dec coordinates
- Observed z vs expected z
- Anomaly score and estimated peculiar velocity (km/s)
- Link to sky map (use [Aladin Lite](https://aladin.u-strasbg.fr/AladinLite/) or similar)

---

## Dashboard Spec (dashboard.py)

- **3D Plotly scatter plot**: X = RA, Y = Dec, Z = luminosity distance
- **Colour**: Magnitude of redshift anomaly score
- **Hover info**: Alert ID, z_obs, z_exp, peculiar velocity
- Streamlit sidebar filters: date range, anomaly score threshold

---

## Testing

- Test `physics_engine.py` with a hardcoded SN Ia alert before connecting to live stream
- Sample test values:
  - apparent magnitude: 18.5 → mew ≈ 37.8 → d_L ≈ 363 Mpc → z_expected ≈ 0.077
- Use `pytest` for unit tests on physics functions

---

## Notes

- Fink stream credentials go in a `.env` file (never commit to repo)
- All cosmology calculations use `astropy.cosmology.Planck18` — do not hardcode H0
- Prefer explicit variable names over abbreviations in physics calculations for clarity
