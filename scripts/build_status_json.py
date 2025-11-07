#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_status_json.py
Creates docs/data/status.json with a quick health snapshot of your data pipeline.
Usage:
  python scripts/build_status_json.py \
    --snapshot docs/data/enrollware-schedule.html \
    --schedule docs/data/schedule.json \
    --out docs/data/status.json
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

def file_info(path: str):
    try:
        st = os.stat(path)
        with open(path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        return {
            "exists": True,
            "bytes": int(st.st_size),
            "md5": md5
        }
    except FileNotFoundError:
        return {
            "exists": False,
            "bytes": 0,
            "md5": None
        }
    except Exception as e:
        # If unreadable for another reason
        return {
            "exists": False,
            "bytes": 0,
            "md5": f"error:{type(e).__name__}"
        }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", required=True, help="Path to docs/data/enrollware-schedule.html")
    p.add_argument("--schedule", required=True, help="Path to docs/data/schedule.json")
    p.add_argument("--out", required=True, help="Path to write docs/data/status.json")
    args = p.parse_args()

    snapshot = file_info(args.snapshot)
    schedule = file_info(args.schedule)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "schedule": schedule,
        "github": {
            "sha": os.environ.get("GITHUB_SHA"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "repo": os.environ.get("GITHUB_REPOSITORY")
        }
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Print a terse summary for logs
    ok = snapshot["exists"] and snapshot["bytes"] > 0 and schedule["exists"] and schedule["bytes"] > 0
    print(f"status: {'OK' if ok else 'INCOMPLETE'} "
          f"(snapshot:{'Y' if snapshot['exists'] else 'N'}/{snapshot['bytes']}B, "
          f"schedule:{'Y' if schedule['exists'] else 'N'}/{schedule['bytes']}B)")

    # Exit non-zero if either file is missing/empty (useful if you want the workflow to fail hard)
    # Comment the next 3 lines if you prefer soft success.
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
