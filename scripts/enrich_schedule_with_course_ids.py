#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_schedule_with_course_ids.py

Placeholder / pass-through enricher for docs/data/schedule.json.

Right now, it simply:
  * loads docs/data/schedule.json
  * logs some info
  * writes it back out unchanged

This keeps the GitHub Actions workflow happy and gives us a hook
to add real Enrollware course-ID enrichment later, without breaking anything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def log(msg: str) -> None:
    print(f"[enrich_schedule] {msg}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-process schedule.json (currently a no-op pass-through)."
    )
    parser.add_argument(
        "--html",
        required=True,
        help="Path to enrollware-schedule HTML snapshot (not used yet, but logged).",
    )
    parser.add_argument(
        "--schedule",
        required=True,
        help="Path to schedule.json to enrich (currently rewritten unchanged).",
    )

    args = parser.parse_args()

    html_path = Path(args.html)
    schedule_path = Path(args.schedule)

    log(f"HTML snapshot path: {html_path} (exists={html_path.exists()})")
    log(f"Schedule JSON path: {schedule_path} (exists={schedule_path.exists()})")

    if not schedule_path.exists():
        log("ERROR: schedule.json does not exist; nothing to enrich.")
        raise SystemExit(1)

    # Load schedule.json
    raw_text = schedule_path.read_text(encoding="utf-8")
    data: Dict[str, Any] = json.loads(raw_text)
    top_keys = list(data.keys())
    log(f"Loaded schedule.json. Top-level keys: {top_keys}")

    # --- PLACEHOLDER ENRICHMENT ---
    # In the future, we can:
    #   * parse html_path
    #   * map course names/aliases to real Enrollware course IDs
    #   * inject those IDs into each course/session
    #
    # For now, this is a pass-through: we just normalize formatting and re-save.

    schedule_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log("Rewrote schedule.json (no structural changes made).")
    log("Done.")


if __name__ == "__main__":
    main()
