#!/usr/bin/env python
"""
build_courses_json.py

Usage:
    python scripts/build_courses_json.py INPUT_SCHEDULE_JSON OUTPUT_COURSES_JSON

Takes the schedule.json produced by parse_enrollware.py and writes
a smaller courses.json containing just the course-level records and
a tiny meta block.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/build_courses_json.py "
            "INPUT_SCHEDULE_JSON OUTPUT_COURSES_JSON",
            file=sys.stderr,
        )
        sys.exit(1)

    schedule_path = Path(sys.argv[1])
    courses_path = Path(sys.argv[2])

    if not schedule_path.exists():
        print(f"ERROR: schedule JSON not found: {schedule_path}", file=sys.stderr)
        sys.exit(1)

    with schedule_path.open("r", encoding="utf-8") as f:
        schedule = json.load(f)

    courses = schedule.get("courses", [])

    out = {
        "meta": {
            "source_schedule": str(schedule_path),
            "generated_at": datetime.utcnow().isoformat(timespec="microseconds") + "Z",
            "course_count": len(courses),
        },
        "courses": courses,
    }

    courses_path.parent.mkdir(parents=True, exist_ok=True)
    with courses_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        f"Wrote {len(courses)} courses to {courses_path} "
        f"from {schedule_path}."
    )


if __name__ == "__main__":
    main()
