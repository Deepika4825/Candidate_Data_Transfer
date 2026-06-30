"""
Parser for GitHub Profile URLs.

Extracts the username from the URL and validates its format.
Actual API calls to GitHub are intentionally left as a stub —
replace the stub with a live requests.get() call when ready.
"""
import re


# Matches https://github.com/<username> with optional trailing slash / path
_GITHUB_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9\-]{0,37}[A-Za-z0-9])?)(?:/.*)?$"
)


def parse_github(url: str) -> dict:
    """
    Validate a GitHub profile URL and extract the username.

    Args:
        url: GitHub profile URL string.

    Returns:
        Dict with 'username' and 'profile_url' keys.

    Raises:
        ValueError: If the URL is not a valid GitHub profile URL.
    """
    url = url.strip().rstrip("/")
    match = _GITHUB_RE.match(url)

    if not match:
        raise ValueError(
            f"'{url}' does not look like a valid GitHub profile URL. "
            "Expected format: https://github.com/username"
        )

    username = match.group(1)

    # ── Stub: replace with actual GitHub API call when needed ──────────
    # import requests
    # response = requests.get(f"https://api.github.com/users/{username}", timeout=10)
    # response.raise_for_status()
    # profile_data = response.json()
    # ───────────────────────────────────────────────────────────────────

    return {
        "username":    username,
        "profile_url": f"https://github.com/{username}",
    }
