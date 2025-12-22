#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrollware_to_schedule.py

Builds:
  docs/data/enrollware-schedule.html -> docs/data/schedule.json

Goal:
- Always produce session rows by finding Enrollware enrollment URLs robustly.
- Derive schedule_url from #ct###### whenever possible.

Run:
  python scripts/enrollware_to_schedule.py
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore


ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"
LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else None


def log(msg: str) -> None:
    sys.stderr.write(str(msg).rstrip() + "\n")


# -------------------------
# CT / schedule URL helpers
# -------------------------

def extract_course_number_from_text(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"#ct(\d+)", text, flags=re.IGNORECASE)
    return m.group(1) if m else None


def find_course_number_in_panel(panel) -> str | None:
    if panel is None:
        return None

    # 1) hrefs
    for a in panel.find_all("a", href=True):
        cn = extract_course_number_from_text(a.get("href"))
        if cn:
            return cn

    # 2) any attribute values (onclick, data-*, etc.)
    for tag in panel.find_all(True):
        attrs = getattr(tag, "attrs", {}) or {}
        for _, v in attrs.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                candidates = [str(x) for x in v]
            else:
                candidates = [str(v)]
            for cand in candidates:
                cn = extract_course_number_from_text(cand)
                if cn:
                    return cn

    # 3) raw panel HTML
    try:
        html = str(panel)
    except Exception:
        html = ""
    return extract_course_number_from_text(html)


def build_schedule_url(course_number: str | None) -> str | None:
    if not course_number:
        return None
    return urljoin(ENROLLWARE_BASE, f"schedule#ct{course_number}")


# -------------------------
# Enrollment URL extraction
# -------------------------

# Matches:
#   enroll?id=123
#   enroll.aspx?id=123
#   /enroll?id=123&x=y
ENROLL_ID_RE = re.compile(r"(?:^|/)(enroll(?:\.aspx)?)\?[^\"']*?\bid=(\d+)", re.IGNORECASE)

def extract_enroll_url_from_text(text: str | None) -> str | None:
    if not text:
        return None
    m = ENROLL_ID_RE.search(text)
    if not m:
        return None
    # Rebuild a clean relative url from the match
    enroll_path = m.group(1)  # enroll or enroll.aspx
    enroll_id = m.group(2)
    return f"{enroll_path}?id={enroll_id}"


def find_enroll_links_in_panel(panel):
    """
    Returns list of tuples:
      (register_url_abs, session_id, context_text)
    Searches hrefs AND onclick AND any attribute blobs.
    """
    found = []
    seen = set()

    # 1) anchor href
    for a in panel.find_all("a", href=True):
        rel = extract_enroll_url_from_text(a.get("href"))
        if rel:
            absu = urljoin(ENROLLWARE_BASE, rel)
            sid = ENROLL_ID_RE.search(rel).group(2)
            ctx = a.parent.get_text(" ", strip=True) if a.parent else a.get_text(" ", strip=True)
            key = (absu, sid)
            if key not in seen:
                seen.add(key)
                found.append((absu, sid, ctx))

    # 2) any tag attribute (onclick, data-href, etc.)
    for tag in panel.find_all(True):
        attrs = getattr(tag, "attrs", {}) or {}
        for _, v in attrs.items():
            if v is None:
                continue
            blobs = []
            if isinstance(v, (list, tuple)):
                blobs = [str(x) for x in v]
            else:
                blobs = [str(v)]

            for blob in blobs:
                rel = extract_enroll_url_from_text(blob)
                if not rel:
                    continue
                absu = urljoin(ENROLLWARE_BASE, rel)
                sid = ENROLL_ID_RE.search(rel).group(2)
                ctx = tag.get_text(" ", strip=True) or (tag.parent.get_text(" ", strip=True) if tag.parent else "")
                key = (absu, sid)
                if key not in seen:
                    seen.add(key)
                    found.append((absu, sid, ctx))

    return found


# -------------------------
# Date parsing
# -------------------------

def normalize_whitespace(s: str | None) -> str:
    if not s:
        return ""
    s = s.replace("\xa0", " ")
    return " ".join(s.split())


def parse_start_datetime(text: str | None):
    """
    Attempts to parse typical Enrollware strings like:
      "Monday, December 29, 2025 at 9:00 AM"
    Returns (start_iso, start_ms, is_past) or (None, None, None)
    """
    if not text:
        return (None, None, None)

    s = normalize_whitespace(text)

    fmts = [
        "%A, %B %d, %Y at %I:%M %p",
        "%A, %B %d, %Y at %I %p",
        "%B %d, %Y at %I:%M %p",
        "%B %d, %Y at %I %p",
    ]

    dt = None
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            break
        except Exception:
            continue

    if not dt:
        return (None, None, None)

    if LOCAL_TZ:
        dt = dt.replace(tzinfo=LOCAL_TZ)

    start_iso = dt.isoformat()
    start_ms = int(dt.timestamp() * 1000)

    now = datetime.now(tz=LOCAL_TZ) if LOCAL_TZ else datetime.now()
    is_past = dt < now

    return (start_iso, start_ms, is_past)


# -------------------------
# Main conversion
# -------------------------

def html_to_schedule_rows(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    panels = soup.select(".enrpanel")
    log(f"[enrollware_to_schedule] Found {len(panels)} enrpanel blocks.")

    course_meta = {}  # course_id -> dict

    # course-level metadata
    for panel in panels:
        course_id = (panel.get("id") or "").strip()
        cid = course_id.replace("enrpanel", "").strip()
        if not cid:
            continue

        # title
        title_el = panel.select_one(".enrtitle") or panel.select_one("h2") or panel.select_one("h3")
        course_name = normalize_whitespace(title_el.get_text(" ", strip=True) if title_el else "")

        course_number = find_course_number_in_panel(panel)
        schedule_url = build_schedule_url(course_number)

        course_meta[cid] = {
            "course_name": course_name,
            "course_number": course_number,
            "schedule_url": schedule_url,
        }

    rows = []
    for panel in panels:
        course_id = (panel.get("id") or "").strip()
        cid = course_id.replace("enrpanel", "").strip()
        if not cid:
            continue

        meta = course_meta.get(cid, {})
        title = meta.get("course_name") or ""
        course_number = meta.get("course_number")
        schedule_url = meta.get("schedule_url")

        enroll_links = find_enroll_links_in_panel(panel)

        # If still none, log one example panel id for debugging (but keep going)
        if not enroll_links:
            continue

        for register_url, session_id, context_text in enroll_links:
            context_text = normalize_whitespace(context_text)

            start_iso, start_ms, is_past = parse_start_datetime(context_text)

            # location: look for a nearby "NC -" style substring
            location = None
            loc_m = re.search(r"\bNC\b\s*[-–]\s*.+$", context_text)
            if loc_m:
                location = normalize_whitespace(loc_m.group(0))

            rows.append(
                {
                    "id": session_id,
                    "course_id": cid,
                    "course_number": course_number,
                    "title": title,
                    "date": context_text,
                    "time": None,
                    "location": location,
                    "url": register_url,
                    "register_url": register_url,
                    "schedule_url": schedule_url,
                    "start_iso": start_iso,
                    "start_ms": start_ms,
                    "is_past": is_past,
                    "end_iso": None,
                }
            )

    log(f"[enrollware_to_schedule] Built {len(rows)} schedule rows.")
    return rows


def main(argv):
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "docs" / "data" / "enrollware-schedule.html"
    output_path = repo_root / "docs" / "data" / "schedule.json"

    if not input_path.exists():
        log(f"ERROR: missing input HTML: {input_path}")
        return 1

    html_text = input_path.read_text(encoding="utf-8", errors="ignore")
    rows = html_to_schedule_rows(html_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"Wrote {len(rows)} rows to: {output_path}")

    if len(rows) == 0:
        log("ERROR: Built 0 rows. That means we still didn't detect any enroll URLs in the snapshot.")
        log("Next debug step: open docs/data/enrollware-schedule.html and Ctrl+F for 'enroll' and 'id='.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
