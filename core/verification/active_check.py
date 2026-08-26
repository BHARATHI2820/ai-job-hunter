"""
Active job verification — Phase 6.

Best-effort HTTP reachability check. This is NOT a guarantee the
posting is still accepting applications — see section 11/35 honesty
constraints. "unknown" is a valid, expected outcome and must never
be silently upgraded to "active".
"""

import requests

TIMEOUT_SECONDS = 6
HEADERS = {
    "User-Agent": "AI-Job-Hunter-Portfolio-Project/0.1 (personal dev project)"
}


def verify_url_active(job_url: str | None) -> dict:
    if not job_url:
        return {
            "active_status": "unknown",
            "active_status_reason": "No job URL to verify",
        }

    try:
        response = requests.head(
            job_url, headers=HEADERS, timeout=TIMEOUT_SECONDS, allow_redirects=True
        )
        if response.status_code == 405:  # some servers reject HEAD
            response = requests.get(
                job_url, headers=HEADERS, timeout=TIMEOUT_SECONDS, allow_redirects=True
            )
    except requests.RequestException as exc:
        return {
            "active_status": "unknown",
            "active_status_reason": f"Could not verify: {type(exc).__name__}",
        }

    if 200 <= response.status_code < 300:
        return {
            "active_status": "active",
            "active_status_reason": "Application page accessible and returned a success status",
        }
    if response.status_code in (404, 410):
        return {
            "active_status": "inactive",
            "active_status_reason": f"Posting page returned {response.status_code} (not found / gone)",
        }
    return {
        "active_status": "unknown",
        "active_status_reason": f"Unexpected status code {response.status_code}",
    }