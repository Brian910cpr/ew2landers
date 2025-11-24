#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_schedule_with_course_ids.py

Post-processes docs/data/schedule.json to inject REAL 6-digit Enrollware
course numbers and schedule URLs, using enrollware-schedule.html as the source.

Usage:
  python enrich_schedule_with_course_ids.py \
    --html docs/data/enrollware-schedule.html \
    --schedule docs/data/schedule.json
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, help="Path to enrollware-schedule.html snapshot")
    parser.add_argument("--schedule", required=True, help="Path to schedule.json (will be updated)")
    return parser.parse_args()


def extract_course_ids_from_html(html_path: Path) -> list[int]:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    panels = soup.select("div.enrpanel")

    ids = []
    for p in panels:
        a = p.find("a", attrs={"name": True})
        if not a:
            ids.append(None)
            continue

        name = a.get("name", "")
        m = re.search(r"\d+", name)
        if not m:
            ids.append(None)
            continue

        ids.append(int(m.group(0)))
    return ids


def load_schedule(schedule_path: Path):
    data = json.loads(schedule_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "courses" in data and isinstance(data["courses"], list):
        return data, data["courses"]
    if isinstance(data, list):
        return data, data
    raise TypeError("schedule.json must be a list or a dict with 'courses' array")


def enrich_schedule_with_ids(container, courses, course_ids):
    n = min(len(courses), len(course_ids))
    for i in range(n):
        cid = course_ids[i]
        if cid is None:
            continue
        c = courses[i]
        if not isinstance(c, dict):
            continue
        c["course_number"] = cid
        c["enrollware_schedule_url"] = f"https://coastalcprtraining.enrollware.com/schedule#ct{cid}"
    return container


def main():
    args = parse_args()
    html_path = Path(args.html)
    schedule_path = Path(args.schedule)

    if not html_path.is_file():
        print(f"ERROR: missing HTML file: {html_path}", file=sys.stderr)
        sys.exit(1)
    if not schedule_path.is_file():
        print(f"ERROR: missing schedule.json: {schedule_path}", file=sys.stderr)
        sys.exit(1)

    ids = extract_course_ids_from_html(html_path)
    container, courses = load_schedule(schedule_path)
    enriched = enrich_schedule_with_ids(container, courses, ids)

    schedule_path.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print("✓ schedule.json updated with real Enrollware course numbers.")


if __name__ == "__main__":
    main()
