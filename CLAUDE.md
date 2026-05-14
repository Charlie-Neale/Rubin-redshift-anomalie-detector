# Fink SN Ia Peculiar Velocity Anomaly Detector

## Project Overview
This project connects to the Fink astronomical alert broker to detect Type Ia supernovae and identify peculiar velocity anomalies. For each SN Ia alert it compares two independent distance estimates: one from the host galaxy (via the Mangrove crossmatch in the alert payload) and one from the Ia standard-candle assumption (via the alert's apparent magnitude). A mismatch implies the supernova is moving with significant peculiar velocity relative to the Hubble flow. Anomalies are flagged, logged, and surfaced via GitHub issues and a Streamlit dashboard.

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

## Fink Alert Schema (verified live, ZTF, 2026-05)

Fields used by this project, with their location inside a Fink alert dict:

| Need | Field | Notes |
|---|---|---|
| Object ID | `objectId` | e.g. `ZTF26aarzhok` |
| RA / Dec | `candidate.ra`, `candidate.dec` | degrees |
| Apparent magnitude (PSF) | `candidate.magpsf` | use this as the standard-candle input |
| Filter band | `candidate.fid` | 1 = g, 2 = r, 3 = i |
| Julian date | `candidate.jd` | observation time |
| Host luminosity distance | `mangrove.lum_dist` | **string, in Mpc** — cast to float; check for absent/`'None'` host |
| TNS spectroscopic class | `tns` | e.g. `'SN Ia'`, `'SN II'`, `'nan'`, or empty |
| Ia ML probability (SuperNNova) | `snn_snia_vs_nonia` | float in [0, 1] |
| Ia ML probability (RandomForest) | `rf_snia_vs_nonia` | float in [0, 1] |

The broader topic `fink_sn_candidates_ztf` returns many non-Ia SNe (e.g. SN II); `fink_early_sn_candidates_ztf` is pre-filtered for early Ia candidates and is the production topic.

---

## Physics Reference

The anomaly compares two independent redshift estimates for the same alert:

### z_host — from the host galaxy (Mangrove crossmatch)
The alert's `mangrove.lum_dist` gives the host galaxy's luminosity distance in Mpc. Convert to redshift by inverting `astropy.cosmology.Planck18.luminosity_distance(z)` (e.g. `astropy.cosmology.z_at_value`). Treat `z_host` as the "true" redshift of the system.

### z_standard_candle — from the Ia apparent magnitude
Assume the SN is a standard Type Ia candle with absolute magnitude **M = −19.3**:
```
mew = candidate.magpsf - (-19.3)            # distance modulus
d_L = 10 ** ((mew - 25) / 5)                # luminosity distance in Mpc
z_standard_candle = invert(Planck18, d_L)   # via astropy.cosmology.z_at_value
```

### Anomaly Score
```
anomaly_score = abs(z_standard_candle - z_host) / z_host
```
If the SN is moving with significant peculiar velocity relative to the Hubble flow, the two redshifts disagree and the score is large.

### Peculiar Velocity Threshold
Flag alerts where peculiar velocity deviation > **1000 km/s**:
```
v_peculiar = c * (z_standard_candle - z_host)        # km/s
```

### Caveats
- The standard-candle assumption fails for Ia subtypes (91T-like, 91bg-like, Iax). The `is_sn_ia` filter in `fink_connection.py` currently accepts these — for production we may want to restrict to normal `'SN Ia'` only.
- Magnitude must be the peak, not a single-epoch sample. For an MVP we use `candidate.magpsf` directly; a production version should track the light curve via `prv_candidates` and pick the peak.
- Extinction (Milky Way + host) is ignored in the MVP.

---

## SN Ia Filter Logic

In `fink_connection.py:is_sn_ia()`:

1. If `tns` is set and not in `{'nan', ''}`, accept iff `tns` is in `SN_IA_TNS_CLASSES` (spectroscopic ground truth).
2. Otherwise fall back to `snn_snia_vs_nonia >= SNN_SNIA_THRESHOLD` (currently 0.5).

`cdsxmatch` and `finkclass` do **not** carry SN type information and should not be used.

---

## Key Dependencies

```bash
pip install fink-client astropy pandas streamlit plotly PyGithub python-dotenv
```

---

## Configuration

Credentials live in `.env` (gitignored). Required keys:
```
FINK_USERNAME=charles
FINK_GROUP_ID=charles_utoronto
FINK_SERVERS=kafka-ztf.fink-broker.org:24499
FINK_TOPICS=fink_early_sn_candidates_ztf
FINK_SURVEY=ztf
```
Note: Fink uses SASL but does not issue passwords for public ZTF topics — `FINK_PASSWORD` is intentionally absent.

`fink_client_register` (CLI) writes `~/.finkclient/<survey>_credentials.yml` as an alternative to env vars. Either path works; this project uses env vars.

---

## Development Phases

Build in this order — do not skip ahead:

1. **fink_connection.py** — ✅ done. Connects to Fink stream, filters SN Ia, prints raw alerts.
2. **physics_engine.py + redshift_resolver.py** — ✅ done. Pure-math standard-candle and Mangrove host-z resolver.
3. **nightly_runner.py** (+ light_curve.py, github_issues.py, anomaly_log.py) — ✅ done. End-to-end: stream → Ia filter → light-curve peak detection → host-z resolve → anomaly check → GitHub issue + CSV.
4. **dashboard.py + visualise.py** — ✅ done. Streamlit app reading `anomalies.csv`, 3D Plotly sky map coloured by anomaly score, sidebar filters (date range + min score), demo-data toggle for when the CSV is empty.

### Running nightly_runner

```bash
# First run: exercise the full pipeline without opening issues.
.venv/bin/python nightly_runner.py --dry-run

# Production:
.venv/bin/python nightly_runner.py
```

Exits when the topic drains (≥6 consecutive empty polls = ~60s idle) or after 30 minutes. Output:
- One GitHub issue per unique anomalous `objectId` on `Charlie-Neale/Rubin-redshift-anomalie-detector` (label `peculiar-velocity-anomaly`). Dedup against currently-open issues.
- One row per flagged alert appended to `anomalies.csv` (gitignored).

### Running the dashboard

```bash
.venv/bin/streamlit run dashboard.py
```

Opens in your browser (default `http://localhost:8501`). If `anomalies.csv` is empty, toggle **Use demo data** in the sidebar to see the layout with synthetic data.

---

## GitHub Issue Format (for anomalies)

When `nightly_runner.py` detects an anomaly, open a GitHub issue with:
- Object ID (`objectId`) and any TNS name
- RA / Dec coordinates
- z_host vs z_standard_candle
- Anomaly score and estimated peculiar velocity (km/s)
- Link to sky map (use [Aladin Lite](https://aladin.u-strasbg.fr/AladinLite/) or similar)

---

## Dashboard Spec (dashboard.py)

- **3D Plotly scatter plot**: X = RA, Y = Dec, Z = host luminosity distance (Mpc)
- **Colour**: anomaly score magnitude
- **Hover info**: objectId, z_host, z_standard_candle, peculiar velocity
- Streamlit sidebar filters: date range, anomaly score threshold

---

## Testing

- Test `physics_engine.py` with a hardcoded sample alert before integrating with the live stream.
- Sample sanity values (Planck18):
  - `magpsf = 18.5` → `mew ≈ 37.8` → `d_L ≈ 363 Mpc` → `z_standard_candle ≈ 0.077`
- Use `pytest` for unit tests on physics functions.

---

## Notes

- Fink stream credentials go in `.env` (never commit).
- All cosmology calculations use `astropy.cosmology.Planck18` — do not hardcode H0.
- Prefer explicit variable names over abbreviations in physics calculations for clarity.
- `mangrove.lum_dist` is a string in the alert payload — always cast to float and guard against `'None'` / missing host matches.
