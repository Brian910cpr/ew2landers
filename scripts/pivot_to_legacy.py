#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pivot_to_legacy.py (verbose)

Convert pivot.json → legacy flat schedule.json expected by your index drawer.
"""

import sys
import json
from pathlib import Path


def log(msg: str) -> None:
    print(f"[pivot_to_legacy] {msg}", flush=True)


def guess_type(title: str) -> str:
    t = (title or "").lower()
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "bls" in t:
        return "BLS"
    if "heartsaver" in t:
        return "Heartsaver"
    if "hsi" in t:
        return "HSI"
    return "Other"


def main():
    log("Starting pivot_to_legacy main().")

    if len(sys.argv) < 2:
        print("Usage: pivot_to_legacy.py docs/data/pivot.json", file=sys.stderr)
        sys.exit(1)

    pivot_path = Path(sys.argv[1])
    if not pivot_path.is_file():
        print(f"pivot.json not found: {pivot_path}", file=sys.stderr)
        sys.exit(1)

    log(f"Reading pivot from {pivot_path}")
    pivot = json.loads(pivot_path.read_text(encoding="utf-8"))

    courses = {c["id"]: c for c in pivot.get("courses", [])}
    log(f"Found {len(courses)} courses.")
    sessions = pivot.get("sessions", [])
    log(f"Found {len(sessions)} sessions.")

    out = []
    for s in sessions:
        title = courses.get(s.get("course_id"), {}).get("title") or s.get("title") or "Untitled"
        out.append({
            "id": s.get("id"),
            "classType": guess_type(title),
            "title": title,
            "start": s.get("start_iso"),
            "end": None,
            "location": s.get("location"),
            "instructor": None,
            "seats": None,
            "url": s.get("url"),
        })

    log(f"Built {len(out)} legacy rows.")
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=False))
    log("Done writing legacy JSON to stdout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
