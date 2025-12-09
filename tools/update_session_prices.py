#!/usr/bin/env python3
"""
update_session_prices.py

Reads docs/data/schedule.json, follows each Enrollware "register_url",
scrapes the session price from the enroll page, and writes it back to
schedule.json as "price".

- Uses a local cache (docs/data/prices-cache.json) so the same enroll URL
  isn't fetched repeatedly.
- Extraction is intentionally generic: it looks for the first "$##.##"
  pattern in the page text. If you find a more precise CSS selector in
  Enrollware's HTML, you can tighten extract_price() later.

Run from the repo root, for example:

    python tools/update_session_prices.py
"""

import json
import time
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Paths (relative to repo root)
ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule.json"
CACHE_PATH = ROOT / "docs" / "data" / "prices-cache.json"

# HTTP settings
HEADERS = {
    "User-Agent": "910CPR-schedule-scraper/1.0 (+https://910cpr.com)"
}
REQUEST_TIMEOUT = 15  # seconds
THROTTLE_SECONDS = 0.4  # pause between requests


def load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        print(f"[WARN] Could not parse JSON at {path}: {e}")
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def extract_price(html: str) -> str | None:
    """
    Generic price extractor:
    - Walks text nodes and grabs the first "$##.##" style pattern.
    """
    soup = BeautifulSoup(html, "html.parser")

    # If you discover a specific selector later, you can do:
    # price_el = soup.select_one("CSS_SELECTOR_HERE")
    # if price_el:
    #     m = re.search(r"\$\s*\d+(?:\.\d{2})?", price_el.get_text(" ", strip=True))
    #     if m:
    #         return m.group(0)

    pattern = re.compile(r"\$\s*\d+(?:\.\d{2})?")
    for text in soup.stripped_strings:
        if "$" not in text:
            continue
        m = pattern.search(text)
        if m:
            return m.group(0)

    return None


def fetch_price_for_url(url: str, cache: dict) -> str | None:
    if not url:
        return None

    if url in cache:
        return cache[url]

    try:
        print(f"[INFO] Fetching price from {url}")
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Request failed for {url}: {e}")
        cache[url] = None
        return None

    price = extract_price(resp.text)
    if price:
        print(f"       → Found price: {price}")
    else:
        print("       → No price found")

    cache[url] = price
    time.sleep(THROTTLE_SECONDS)
    return price


def main():
    if not SCHEDULE_PATH.exists():
        print(f"[ERROR] schedule.json not found at {SCHEDULE_PATH}")
        return

    schedule = load_json(SCHEDULE_PATH, {"sessions": []})
    sessions = schedule.get("sessions") or []

    if not sessions:
        print("[WARN] schedule.json has no sessions")
        return

    price_cache = load_json(CACHE_PATH, {})

    updated_count = 0
    total = len(sessions)

    for idx, sess in enumerate(sessions, start=1):
        url = sess.get("register_url") or ""
        if not url:
            continue

        existing = sess.get("price")
        if existing:
            # Already has a price; keep it and seed the cache
            price_cache.setdefault(url, existing)
            continue

        print(
            f"\n[{idx}/{total}] course_id={sess.get('course_id')} "
            f"course_name={sess.get('course_name')!r}"
        )

        price = fetch_price_for_url(url, price_cache)
        if price:
            sess["price"] = price
            updated_count += 1

    save_json(SCHEDULE_PATH, schedule)
    save_json(CACHE_PATH, price_cache)

    print(f"\n[DONE] Updated {updated_count} session(s) with prices.")
    print(f"       schedule.json: {SCHEDULE_PATH}")
    print(f"       cache:         {CACHE_PATH}")


if __name__ == "__main__":
    main()
