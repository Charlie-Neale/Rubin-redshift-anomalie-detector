"""Connect to the Fink live alert stream and print raw SN Ia alerts."""

import os
import sys
from pprint import pprint

from dotenv import load_dotenv
from fink_client.consumer import AlertConsumer

load_dotenv()

SN_IA_TNS_CLASSES = {
    "SN Ia",
    "SN Ia-91T-like",
    "SN Ia-91bg-like",
    "SN Iax[02cx-like]",
}
SNN_SNIA_THRESHOLD = 0.5  # snn_snia_vs_nonia probability cutoff when TNS class is missing

POLL_TIMEOUT_SECONDS = 10
MAX_ALERTS = None  # None = run until interrupted


def build_config() -> dict:
    """Read Fink broker credentials from environment variables."""
    required = ["FINK_USERNAME", "FINK_SERVERS", "FINK_GROUP_ID"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {', '.join(missing)}. "
            f"Set them in a .env file (see CLAUDE.md)."
        )

    return {
        "username": os.environ["FINK_USERNAME"],
        "bootstrap.servers": os.environ["FINK_SERVERS"],
        "group.id": os.environ["FINK_GROUP_ID"],
    }


def is_sn_ia(alert: dict) -> bool:
    """Return True if the alert is classified as a Type Ia supernova candidate.

    Prefers TNS spectroscopic class when present (definitive); otherwise falls
    back to Fink's SuperNNova Ia-vs-non-Ia probability.
    """
    tns = alert.get("tns")
    if tns and tns not in {"nan", ""}:
        return tns in SN_IA_TNS_CLASSES
    return (alert.get("snn_snia_vs_nonia") or 0.0) >= SNN_SNIA_THRESHOLD


def stream_alerts() -> None:
    config = build_config()
    topics = os.getenv("FINK_TOPICS", "fink_sn_candidates_ztf").split(",")
    survey = os.getenv("FINK_SURVEY", "ztf")

    consumer = AlertConsumer(topics, config, survey=survey)
    print(f"Subscribed to topics: {topics} (survey={survey})", file=sys.stderr)

    seen = 0
    try:
        while MAX_ALERTS is None or seen < MAX_ALERTS:
            topic, alert, key = consumer.poll(timeout=POLL_TIMEOUT_SECONDS)
            if alert is None:
                continue
            if not is_sn_ia(alert):
                continue
            print(f"\n--- Alert from topic={topic} ---")
            pprint(alert)
            seen += 1
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
    finally:
        consumer.close()


if __name__ == "__main__":
    stream_alerts()
