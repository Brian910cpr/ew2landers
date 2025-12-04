#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, help="Path to enrollware HTML snapshot")
    parser.add_argument("--schedule", required=True, help="Path to schedule.json")
    args = parser.parse_args()

    html_path = Path(args.html)
    sched_path = Path(args.schedule)

    print("[enrich] NO-OP enrich_schedule_with_course_ids.py")
    print(f"  HTML: {html_path} (exists={html_path.exists()})")
    if not sched_path.exists():
        raise SystemExit(f"[enrich] schedule.json not found at {sched_path}")

    data = json.loads(sched_path.read_text(encoding="utf-8"))
    # No changes yet; just re-dump so workflow has something to do.
    sched_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[enrich] schedule.json size={sched_path.stat().st_size} bytes")

if __name__ == "__main__":
    main()
