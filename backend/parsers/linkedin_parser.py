"""
Parser for LinkedIn Profile URLs.

Extracts the public profile identifier from the URL and validates its format.
LinkedIn scraping requires authentication; this module validates the URL
and returns the parsed identifier as a stub for downstream enrichment.
"""
import re


# Matches https://linkedin.com/in/<identifier> with optional trailing parts
_LINKEDIN_RE = re.compile(
    r"^https?://(?:www\.)?linkedin\.com/in/([\w\-\.%]+)(?:/.*)?$"
)


def parse_linkedin(url: str) -> dict:
    """
    Validate a LinkedIn profile URL and extract the profile identifier.

    Args:
        url: LinkedIn profile URL string.

    Returns:
        Dict with 'profile_id' and 'profile_url' keys.

    Raises:
        ValueError: If the URL is not a valid LinkedIn profile URL.
    """
    url = url.strip().rstrip("/")
    match = _LINKEDIN_RE.match(url)

    if not match:
        raise ValueError(
            f"'{url}' does not look like a valid LinkedIn profile URL. "
            "Expected format: https://linkedin.com/in/profile-id"
        )

    profile_id = match.group(1)

    # ── Stub: replace with LinkedIn API / scraping logic when ready ─────
    # Actual LinkedIn data extraction requires OAuth or a scraping service.
    # ────────────────────────────────────────────────────────────────────

    return {
        "profile_id":  profile_id,
        "profile_url": f"https://www.linkedin.com/in/{profile_id}",
    }
