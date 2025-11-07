#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert pivot.json -> legacy flat schedule.json expected by index.html
(schema used by your current frontend: [{id, classType, title, start, end, location, instructor, seats, url}])

Rules:
- classType inferred from course title (ACLS/PALS/BLS/Heartsaver/HSI/Other).
- start = start_iso when available; else null.
- end, instructor, seats are null (not in source).
- Title is the course title (stable across a course’s sessions).
- Keeps all sessions; frontend will filter the window (28 days) itself.
"""

import sys
import json

def guess_type(title: str) -> str:
    t = (title or "").lower()
    if "acls" in t: return "ACLS"
    if "pals" in t: return "PALS"
    if "bls" in t: return "BLS"
    if "heartsaver" in t: return "Heartsaver"
    if "hsi" in t: return "HSI"
    return "Other"

def main():
    if len(sys.argv) < 2:
        print("Usage: pivot_to_legacy.py docs/data/pivot.json", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        pivot = json.load(f)

    courses_by_id = {c["id"]: c for c in pivot.get("courses", [])}
    out = []
    for s in pivot.get("sessions", []):
        course = courses_by_id.get(s.get("course_id")) or {}
        title = course.get("title") or s.get("title") or "Untitled"
        out.append({
            "id": s.get("id"),
            "classType": guess_type(title),
            "title": title,
            "start": s.get("start_iso"),   # frontend already guards invalid
            "end": None,
            "location": s.get("location"),
            "instructor": None,
            "seats": None,
            "url": s.get("url")
        })

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
