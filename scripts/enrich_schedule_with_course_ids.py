#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_schedule_with_course_ids.py (verbose)

Injects real Enrollware 6-digit course numbers + schedule URLs into schedule.json.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup  # type: ignore


def log(msg: str) -> None:
    print(f"[enrich_schedule] {msg}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Verbose enrichment of schedule.json.")
    parser.add_argument("--html", required=True)
    parser.add_argument("--schedule", required=True)
    return parser.parse_args()


def extract_course_ids_from_html(html_path: Path) -> List[int | None]:
    log(f"Reading HTML snapshot: {html_path}")
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    log(f"Snapshot size: {len(html)} bytes")

    soup = BeautifulSoup(html, "html.parser")
    panels = soup.select("div.enrpanel")
    log(f"Found {len(panels)} .enrpanel panels.")

    ids: List[int | None] = []

    for idx, p in enumerate(panels, start=1):
        a = p.find("a", attrs={"name": True})
        if not a:
            log(f"Panel #{idx}: no anchor with name attr -> None")
            ids.append(None)
            continue

        name = a.get("name", "")
        m = re.search(r"\d+", name)
        if not m:
            log(f"Panel #{idx}: name={name!r} had no digits -> None")
            ids.append(None)
            continue

        cid = int(m.group(0))
        log(f"Panel #{idx}: extracted course_id={cid}")
        ids.append(cid)

    return ids


def load_schedule(schedule_path: Path):
    log(f"Loading schedule.json from {schedule_path}")
    data = json.loads(schedule_path.read_text(encoding="utf-8"))

    if isinstance(data, dict) and "courses" in data:
        log("Detected dict container with 'courses'.")
        return data, data["courses"]

    if isinstance(data, list):
        log("Detected list-only schedule.")
        return data, data

    raise TypeError("schedule.json must be a list or dict with 'courses'")


def enrich_schedule_with_ids(container, courses, course_ids):
    log("Beginning enrichment pass.")
    limit = min(len(courses), len(course_ids))
    updated = 0

    for idx in range(limit):
        cid = course_ids[idx]
        if cid is None:
            continue
        c = courses[idx]
        if isinstance(c, dict):
            c["course_number"] = cid
            c["enrollware_schedule_url"] = f"https://coastalcprtraining.enrollware.com/schedule#ct{cid}"
            updated += 1

    log(f"Enrichment complete: updated {updated} course entries.")
    return container


def main():
    log("Starting enrichment main().")
    args = parse_args()

    html_path = Path(args.html)
    schedule_path = Path(args.schedule)

    if not html_path.exists():
        print(f"ERROR: HTML not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    if not schedule_path.exists():
        print(f"ERROR: schedule.json not found: {schedule_path}", file=sys.stderr)
        sys.exit(1)

    course_ids = extract_course_ids_from_html(html_path)
    container, courses = load_schedule(schedule_path)
    enriched = enrich_schedule_with_ids(container, courses, course_ids)

    log(f"Writing enriched schedule.json to {schedule_path}")
    schedule_path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    log("Done enriching.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
