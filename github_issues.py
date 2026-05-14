"""GitHub Issues client for posting peculiar-velocity anomaly alerts."""

from __future__ import annotations

from github import Github, GithubException

from light_curve import PeakInfo
from physics_engine import AnomalyResult

ANOMALY_LABEL = "peculiar-velocity-anomaly"
_LABEL_COLOR = "B60205"
_LABEL_DESCRIPTION = "SN Ia with peculiar velocity inconsistent with Hubble flow"
_TITLE_PREFIX = "[Anomaly]"


class GitHubIssueClient:
    def __init__(self, token: str, repo_full_name: str):
        self._gh = Github(token)
        self._repo = self._gh.get_repo(repo_full_name)

    def open_anomaly_object_ids(self) -> set[str]:
        try:
            label = self._repo.get_label(ANOMALY_LABEL)
        except GithubException as e:
            if e.status == 404:
                return set()
            raise

        ids: set[str] = set()
        for issue in self._repo.get_issues(state="open", labels=[label]):
            parts = issue.title.split()
            if len(parts) >= 2 and parts[0] == _TITLE_PREFIX:
                ids.add(parts[1])
        return ids

    def open_anomaly_issue(
        self, alert: dict, result: AnomalyResult, peak: PeakInfo
    ) -> int:
        label = self._ensure_label()
        object_id = alert["objectId"]
        candidate = alert.get("candidate") or {}
        ra = candidate.get("ra")
        dec = candidate.get("dec")
        tns = alert.get("tns") or ""
        title = (
            f"{_TITLE_PREFIX} {object_id} — "
            f"v_pec = {result.peculiar_velocity_kms:+.0f} km/s"
        )
        body = _format_body(object_id, ra, dec, tns, result, peak)
        issue = self._repo.create_issue(title=title, body=body, labels=[label])
        return issue.number

    def _ensure_label(self):
        try:
            return self._repo.get_label(ANOMALY_LABEL)
        except GithubException as e:
            if e.status == 404:
                return self._repo.create_label(
                    name=ANOMALY_LABEL,
                    color=_LABEL_COLOR,
                    description=_LABEL_DESCRIPTION,
                )
            raise


def _format_body(object_id, ra, dec, tns, result, peak) -> str:
    aladin = f"https://aladin.u-strasbg.fr/AladinLite/?target={ra}+{dec}&fov=0.05"
    fink_portal = f"https://fink-portal.org/{object_id}"
    tns_line = (
        f"- **TNS class**: `{tns}`" if tns else "- **TNS class**: _(unclassified)_"
    )
    return f"""## {object_id}

- **Coordinates**: RA = `{ra}`, Dec = `{dec}`
{tns_line}
- **Peak**: magpsf = `{peak.peak_magpsf:.3f}` (r-band) at JD `{peak.peak_jd}` — based on `{peak.n_detections_in_band}` r-band detections

### Anomaly

| | |
|---|---|
| z_host (Mangrove) | `{result.z_host:.4f}` |
| z_standard_candle (Ia, M=−19.3) | `{result.z_standard_candle:.4f}` |
| d_L host (Mpc) | `{result.d_l_host_mpc:.1f}` |
| d_L standard candle (Mpc) | `{result.d_l_standard_candle_mpc:.1f}` |
| anomaly score | `{result.anomaly_score:.3f}` |
| **peculiar velocity** | **`{result.peculiar_velocity_kms:+.0f}` km/s** |

### Links
- [Aladin Lite sky map]({aladin})
- [Fink portal]({fink_portal})
"""
