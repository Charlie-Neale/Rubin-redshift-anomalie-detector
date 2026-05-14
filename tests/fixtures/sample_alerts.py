"""Distilled real-ish Fink alert fixtures for offline tests.

Anchored on the three alerts captured during Phase 1 verification
(/tmp/fink_alerts.txt). Only fields the pipeline reads are kept;
prv_candidates entries are synthetic but consistent with ZTF cadence.
"""

# No host match (Mangrove returned 'None' across the board). magpsf is real.
ALERT_NO_HOST = {
    "objectId": "ZTF26aahuhpc",
    "tns": "SN Ia-91T-like",
    "snn_snia_vs_nonia": 0.10947821289300919,
    "candidate": {
        "ra": 185.5,
        "dec": 5.0,
        "magpsf": 19.028287887573242,
        "jd": 2461169.78,
        "fid": 2,
    },
    "prv_candidates": [],
    "mangrove": {
        "2MASS_name": "None",
        "HyperLEDA_name": "None",
        "ang_dist": "None",
        "lum_dist": "None",
    },
}

# Has host (Mangrove 104.5 Mpc), current detection is the brightest in r-band so far.
# Light-curve peak detection should refuse to flag (still brightening).
ALERT_HOST_BRIGHTENING = {
    "objectId": "ZTF26aTEST01",
    "tns": "",
    "snn_snia_vs_nonia": 0.886422872543335,
    "candidate": {
        "ra": 185.8349273,
        "dec": 4.8944429,
        "magpsf": 17.66,
        "jd": 2461169.78,
        "fid": 2,
    },
    "prv_candidates": [
        {"magpsf": 18.00, "jd": 2461166.78, "fid": 2},
        {"magpsf": 17.80, "jd": 2461167.78, "fid": 2},
        {"magpsf": 17.70, "jd": 2461168.78, "fid": 2},
    ],
    "mangrove": {
        "2MASS_name": "None",
        "HyperLEDA_name": "1274905.0",
        "ang_dist": "99.81731182932242",
        "lum_dist": "104.533613914",
    },
}

# Same host, ~10 days later: SN has faded. Light-curve peak detection should
# return PeakInfo with the prior peak (17.66 mag at JD 2461169.78).
ALERT_HOST_PAST_PEAK = {
    "objectId": "ZTF26aTEST02",
    "tns": "SN Ia",
    "snn_snia_vs_nonia": 0.95,
    "candidate": {
        "ra": 185.8349273,
        "dec": 4.8944429,
        "magpsf": 18.50,
        "jd": 2461179.78,
        "fid": 2,
    },
    "prv_candidates": [
        {"magpsf": 18.00, "jd": 2461166.78, "fid": 2},
        {"magpsf": 17.80, "jd": 2461167.78, "fid": 2},
        {"magpsf": 17.66, "jd": 2461169.78, "fid": 2},
        {"magpsf": 17.95, "jd": 2461175.78, "fid": 2},
    ],
    "mangrove": {
        "2MASS_name": "None",
        "HyperLEDA_name": "1274905.0",
        "ang_dist": "99.81731182932242",
        "lum_dist": "104.533613914",
    },
}
