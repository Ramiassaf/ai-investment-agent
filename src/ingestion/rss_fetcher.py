import feedparser
import requests
from typing import Any

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}

def fetch_rss_feed(url: str, timeout: int = 15, debug: bool = False) -> list[dict[str, Any]]:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()

    content_type_raw = r.headers.get("Content-Type", "")
    content_type = content_type_raw.lower()
    body_preview = r.text[:300].replace("\n", " ").strip()
    text_head = r.text[:200].lower()

    if debug:
        print("\n--- RSS FETCH DEBUG ---")
        print("Requested URL:", url)
        print("Final URL:", r.url)
        print("Status:", r.status_code)
        print("Content-Type:", content_type_raw)
        print("Bytes:", len(r.content))
        print("Preview:", body_preview)

    # Guard: refuse HTML masquerading as RSS
    if (
        "text/html" in content_type
        or "<!doctype html" in text_head
        or "<html" in text_head
    ):
        raise ValueError(
            "Expected RSS/Atom XML but got HTML. This URL is a webpage, not an RSS endpoint."
        )

    parsed = feedparser.parse(r.content)

    if debug:
        print("Bozo:", getattr(parsed, "bozo", 0))
        if getattr(parsed, "bozo", 0) == 1:
            print("Bozo exception:", getattr(parsed, "bozo_exception", None))
        print("Entries:", len(parsed.entries))
        print("------------------------\n")

    return [dict(e) for e in parsed.entries]