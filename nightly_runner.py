"""End-to-end peculiar-velocity anomaly detector.

Connects to the Fink stream, filters SN Ia alerts, detects light-curve peaks
from the in-alert prv_candidates history, computes the standard-candle vs
host-galaxy redshift mismatch, and opens a GitHub issue + CSV row per unique
anomalous object.

Usage:
    .venv/bin/python nightly_runner.py [--dry-run]

Scheduling (examples, not auto-configured):

  macOS launchd — ~/Library/LaunchAgents/com.charlieneale.fink-runner.plist:
      ProgramArguments: /full/path/.venv/bin/python /full/path/nightly_runner.py
      StartCalendarInterval: hour 14 (10:00 ET — after ZTF night ends)
      StandardOutPath / StandardErrorPath: /tmp/fink-runner.log

  GitHub Actions — .github/workflows/nightly.yml:
      on: { schedule: [{ cron: '0 14 * * *' }] }
      run: .venv/bin/python nightly_runner.py
      env: { GITHUB_TOKEN: ${{ secrets.RUBIN_REDSHIFT_TOKEN }}, GITHUB_REPO: ... }
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from fink_client.consumer import AlertConsumer

import anomaly_log
from fink_connection import build_config, is_sn_ia
from github_issues import GitHubIssueClient
from light_curve import extract_peak_for_anomaly
from physics_engine import compute_anomaly
from redshift_resolver import resolve_z

load_dotenv()

MAX_RUNTIME_SECONDS = 30 * 60
CONSECUTIVE_EMPTY_POLLS_BEFORE_EXIT = 6
POLL_TIMEOUT_SECONDS = 10


def main(dry_run: bool = False) -> int:
    config = build_config()
    topics = os.getenv("FINK_TOPICS", "fink_early_sn_candidates_ztf").split(",")
    survey = os.getenv("FINK_SURVEY", "ztf")

    client: GitHubIssueClient | None = None
    seen_object_ids: set[str]
    if dry_run:
        print("[DRY-RUN] No GitHub issues will be opened; no CSV rows will be written.", file=sys.stderr)
        seen_object_ids = set()
    else:
        gh_token = os.getenv("GITHUB_TOKEN")
        gh_repo = os.getenv("GITHUB_REPO")
        if not gh_token or not gh_repo:
            print(
                "GITHUB_TOKEN and GITHUB_REPO must be set in .env for live runs. "
                "Use --dry-run to test without them.",
                file=sys.stderr,
            )
            return 1
        client = GitHubIssueClient(gh_token, gh_repo)
        seen_object_ids = client.open_anomaly_object_ids()
        print(
            f"Loaded {len(seen_object_ids)} existing open anomaly issues for dedup.",
            file=sys.stderr,
        )

    consumer = AlertConsumer(topics, config, survey=survey)
    print(f"Subscribed to topics: {topics} (survey={survey})", file=sys.stderr)

    stats = {
        "alerts_polled": 0,
        "ia_after_filter": 0,
        "past_peak": 0,
        "host_resolved": 0,
        "anomalies_flagged": 0,
    }
    start = time.time()
    empty_polls = 0

    try:
        while True:
            if time.time() - start > MAX_RUNTIME_SECONDS:
                print("Wall-clock cap reached, exiting.", file=sys.stderr)
                break

            topic, alert, key = consumer.poll(timeout=POLL_TIMEOUT_SECONDS)
            if alert is None:
                empty_polls += 1
                if empty_polls >= CONSECUTIVE_EMPTY_POLLS_BEFORE_EXIT:
                    print(
                        f"Topic drained ({empty_polls} consecutive empty polls), exiting.",
                        file=sys.stderr,
                    )
                    break
                continue
            empty_polls = 0
            stats["alerts_polled"] += 1

            if not is_sn_ia(alert):
                continue
            stats["ia_after_filter"] += 1

            peak = extract_peak_for_anomaly(alert)
            if peak is None:
                continue
            stats["past_peak"] += 1

            z_host = resolve_z(alert)
            if z_host is None:
                continue
            stats["host_resolved"] += 1

            result = compute_anomaly(peak.peak_magpsf, z_host)
            if not result.is_anomaly:
                continue

            object_id = alert["objectId"]
            if object_id in seen_object_ids:
                print(f"Skip duplicate: {object_id}", file=sys.stderr)
                continue

            if dry_run:
                print(
                    f"[DRY-RUN] Would flag {object_id} "
                    f"v_pec={result.peculiar_velocity_kms:+.0f} km/s "
                    f"score={result.anomaly_score:.2f}",
                    file=sys.stderr,
                )
            else:
                assert client is not None
                issue_number = client.open_anomaly_issue(alert, result, peak)
                anomaly_log.append(alert, result, peak)
                print(
                    f"Opened issue #{issue_number} for {object_id} "
                    f"v_pec={result.peculiar_velocity_kms:+.0f} km/s",
                    file=sys.stderr,
                )
            seen_object_ids.add(object_id)
            stats["anomalies_flagged"] += 1
    except KeyboardInterrupt:
        print("Interrupted by user.", file=sys.stderr)
    finally:
        consumer.close()

    runtime = time.time() - start
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(
        f"\n=== Summary ({mode}) ===\n"
        f"runtime:           {runtime:.1f}s\n"
        f"alerts polled:     {stats['alerts_polled']}\n"
        f"after Ia filter:   {stats['ia_after_filter']}\n"
        f"past peak:         {stats['past_peak']}\n"
        f"host resolved:     {stats['host_resolved']}\n"
        f"anomalies flagged: {stats['anomalies_flagged']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run end-to-end without opening GitHub issues or writing CSV.",
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
