"""WinForge update checker - queries GitHub Releases API."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from loguru import logger

import app

API_URL = "https://api.github.com/repos/051-lab/WinForge/releases/latest"
TIMEOUT = 5
USER_AGENT = "WinForge-updater"


@dataclass
class UpdateResult:
    available: bool
    current: str
    latest: str
    url: str


def check_for_updates() -> UpdateResult:
    """Check GitHub Releases for a newer version."""
    current = app.__version__
    fallback = UpdateResult(available=False, current=current, latest=current, url="")

    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        logger.warning("Update check failed (network): {}", exc)
        return fallback
    except Exception as exc:
        logger.warning("Update check failed (unexpected): {}", exc)
        return fallback

    tag = data.get("tag_name", "")
    html_url = data.get("html_url", "")

    if not tag:
        logger.warning("Update check: no tag_name in response")
        return fallback

    latest = tag.lstrip("v")
    available = latest != current
    logger.info("Update check: current={} latest={} available={}", current, latest, available)
    return UpdateResult(available=available, current=current, latest=latest, url=html_url)
