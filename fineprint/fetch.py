"""Polite HTTP: robots.txt, per-host spacing, Wayback CDX, raw cache."""
from __future__ import annotations

import time
import tomllib
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "raw"
UA_NAME = "fineprint"
UA = f"{UA_NAME}/0.1 (+https://github.com/dadwritestech/fineprint; public AI-policy change archive)"
HOST_GAP = 6.0       # seconds between requests to the same vendor host
WAYBACK_GAP = 3.0    # seconds between requests to archive.org
TIMEOUT = 45

_last_hit: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml",
                         "Accept-Language": "en-US,en;q=0.8",
                         # requests cannot decode brotli; Wayback sometimes serves it raw
                         "Accept-Encoding": "gzip, deflate"})


def load_pages(path: Path = ROOT / "pages.toml") -> list[dict]:
    with open(path, "rb") as f:
        pages = tomllib.load(f)["page"]
    seen = set()
    for p in pages:
        key = (p["vendor"], p["slug"])
        assert key not in seen, f"duplicate page {key}"
        seen.add(key)
    return pages


def _wait(host: str, gap: float) -> None:
    last = _last_hit.get(host, 0.0)
    delay = last + gap - time.monotonic()
    if delay > 0:
        time.sleep(delay)
    _last_hit[host] = time.monotonic()


def robots_allows(url: str) -> tuple[bool, str]:
    """Conservative robots.txt check for our user agent.

    401/403 on robots.txt -> disallow (we cannot tell what they want).
    404 and other 4xx      -> allow (no robots.txt means no rules).
    5xx / network error    -> disallow for this run.
    """
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots:
        _wait(parts.netloc, HOST_GAP)
        try:
            r = _session.get(origin + "/robots.txt", timeout=TIMEOUT)
            if r.status_code in (401, 403):
                _robots[origin] = None
            elif r.status_code >= 500:
                _robots[origin] = None
            elif r.status_code >= 400:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse([])
                _robots[origin] = rp
            else:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(r.text.splitlines())
                _robots[origin] = rp
        except requests.RequestException:
            _robots[origin] = None
    rp = _robots[origin]
    if rp is None:
        return False, "robots.txt unreadable (403/5xx/network): treated as disallow"
    if not rp.can_fetch(UA_NAME, url):
        return False, "disallowed by robots.txt"
    return True, "ok"


def fetch_live(url: str) -> tuple[int, str]:
    host = urlsplit(url).netloc
    _wait(host, HOST_GAP)
    r = _session.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else "utf-8"
    return r.status_code, r.text


def _wayback_get(url: str, params: dict | None = None, tries: int = 5) -> requests.Response:
    backoff = 10.0
    for attempt in range(tries):
        _wait("web.archive.org", WAYBACK_GAP)
        try:
            r = _session.get(url, params=params, timeout=90)
        except requests.RequestException:
            r = None
        if r is not None and r.status_code < 500 and r.status_code != 429:
            return r
        time.sleep(backoff)
        backoff *= 2
    raise RuntimeError(f"wayback unavailable after {tries} tries: {url}")


def cdx_captures(url: str, since: str, until: str) -> list[dict]:
    """Successful HTML captures between since/until (YYYYMMDD), one per day."""
    r = _wayback_get("https://web.archive.org/cdx/search/cdx", {
        "url": url, "from": since, "to": until, "output": "json",
        "fl": "timestamp,original,statuscode,digest,mimetype",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "timestamp:8",
    })
    if r.status_code != 200 or not r.text.strip():
        return []
    rows = r.json()
    if not rows:
        return []
    head, *body = rows
    return [dict(zip(head, row)) for row in body]


def fetch_wayback(timestamp: str, original: str) -> tuple[int, str]:
    # id_ = the original bytes, without the Wayback toolbar or URL rewriting.
    r = _wayback_get(f"https://web.archive.org/web/{timestamp}id_/{original}")
    r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else "utf-8"
    return r.status_code, r.text


def cache_path(page: dict, stamp: str) -> Path:
    return CACHE / page["vendor"] / page["slug"] / f"{stamp}.html"


def cached(page: dict, stamp: str) -> str | None:
    p = cache_path(page, stamp)
    return p.read_text(encoding="utf-8") if p.exists() else None


def store_cache(page: dict, stamp: str, html: str) -> None:
    p = cache_path(page, stamp)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
