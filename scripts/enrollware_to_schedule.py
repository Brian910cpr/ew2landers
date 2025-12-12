#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrollware_to_schedule.py

One-step builder:
  docs/data/enrollware-schedule.html  ->  docs/data/schedule.json (flat legacy list)

Uses the same DOM anchors your existing parser uses:
  - #enraccordion .enrpanel
  - ul.enrclass-list > li > a[href*="enroll"]

Logs go to STDERR so schedule.json stays clean JSON.

Usage:
  python scripts/enrollware_to_schedule.py
  python scripts/enrollware_to_schedule.py INPUT_HTML OUTPUT_JSON
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"

ROOT = Path(__file__).resolve().parents[1]  # repo root
DEFAULT_INPUT = ROOT / "docs" / "data" / "enrollware-schedule.html"
DEFAULT_OUTPUT = ROOT / "docs" / "data" / "schedule.json"


def log(msg: str) -> None:
    print(f"[enrollware_to_schedule] {msg}", file=sys.stderr, flush=True)


def extract_session_id_from_href(href: str):
    if not href:
        return None
    try:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "id" in qs and qs["id"]:
            return int(qs["id"][0])
    except Exception:
        pass

    digits = "".join(ch for ch in href if ch.isdigit())
    return int(digits) if digits else None


def extract_course_number_from_text(text: str):
    """
    Try to find a course filter value like ct209811 in any text/href.
    Returns digits as string, or None.
    """
    if not text:
        return None
    m = re.search(r"#ct(\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"[?&]course=(\d+)", text)
    if m:
        return m.group(1)
    return None


def normalize_course_name(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    s = " ".join(s.split())
    return s


def extract_date_text(anchor_tag) -> str:
    txt = anchor_tag.get_text(" ", strip=True)
    return " ".join(txt.split())


def try_extract_price(panel_text: str):
    if not panel_text:
        return None
    m = re.search(r"\$\s*\d+(?:\.\d{2})?", panel_text)
    if not m:
        return None
    return m.group(0).replace(" ", "")


def html_to_schedule_rows(html_text: str):
    soup = BeautifulSoup(html_text, "lxml")

    panels = soup.select("#enraccordion .enrpanel")
    if not panels:
        log("No #enraccordion .enrpanel found; falling back to .enrpanel.")
        panels = soup.select(".enrpanel")

    log(f"Found {len(panels)} enrpanel blocks.")

    rows = []
    course_index = {}  # course_name -> course_id
    course_meta = {}   # course_id -> dict

    for panel in panels:
        raw_course_name = panel.get("value") or ""
        if not raw_course_name:
            title_el = panel.select_one(".enrpanel-title")
            if title_el:
                raw_course_name = title_el.get_text(" ", strip=True)

        course_name = normalize_course_name(raw_course_name)
        if not course_name:
            continue

        if course_name not in course_index:
            cid = len(course_index) + 1
            course_index[course_name] = cid
        else:
            cid = course_index[course_name]

        course_number = None
        for a in panel.find_all("a", href=True):
            course_number = extract_course_number_from_text(a["href"])
            if course_number:
                break

        panel_text = panel.get_text(" ", strip=True)
        price = try_extract_price(panel_text)

        if cid not in course_meta:
            course_meta[cid] = {
                "course_number": course_number,
                "price": price,
                "course_name": course_name,
            }
        else:
            if not course_meta[cid].get("course_number") and course_number:
                course_meta[cid]["course_number"] = course_number
            if not course_meta[cid].get("price") and price:
                course_meta[cid]["price"] = price

        for ul in panel.select("ul.enrclass-list"):
            for li in ul.find_all("li"):
                a = li.find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if "enroll" not in href:
                    continue

                session_id = extract_session_id_from_href(href)
                if not session_id:
                    continue

                start_display = extract_date_text(a)
                span = li.find("span")
                location = span.get_text(" ", strip=True) if span else ""
                register_url = urljoin(ENROLLWARE_BASE, href)

                rows.append({
                    "id": session_id,
                    "course_id": cid,
                    "course_number": course_meta[cid].get("course_number"),
                    "title": course_name,
                    "date": start_display,   # keep raw display for now
                    "time": None,
                    "location": location,
                    "price": course_meta[cid].get("price"),
                    "url": register_url,
                    "start_iso": None,
                    "end_iso": None,
                })

    log(f"Built {len(rows)} schedule rows.")
    return rows


def main(argv) -> int:
    input_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_INPUT
    output_path = Path(argv[2]) if len(argv) >= 3 else DEFAULT_OUTPUT

    if not input_path.exists():
        log(f"Input HTML not found: {input_path}")
        return 1

    html_text = input_path.read_text(encoding="utf-8", errors="ignore")
    rows = html_to_schedule_rows(html_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"Wrote {len(rows)} rows to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
