import json
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule.json"
OUT_DIR = ROOT / "docs" / "assets" / "images" / "course"
ZIP_PATH = ROOT / "course-number-images.zip"


def extract_enrollware_course_number(item: dict) -> str | None:
    """
    Try to pull the REAL Enrollware course number from any URL-ish field.

    We look for patterns like:
      ?course=265876
      #ct359474
    and fall back to any 'ct123456' style tag we can find.
    """
    # Try the obvious URL fields first
    url_candidates = [
        item.get("schedule_url"),
        item.get("course_url"),
        item.get("register_url"),
        item.get("url"),
    ]

    for url in url_candidates:
        if not url or not isinstance(url, str):
            continue

        # 1) ?course=265876
        m = re.search(r"[?&#]course=(\d+)", url)
        if m:
            return m.group(1)

        # 2) #ct359474
        m = re.search(r"#ct(\d+)", url)
        if m:
            return m.group(1)

    # If we still haven't found it, scan all string fields for a ct123456 pattern
    for value in item.values():
        if not isinstance(value, str):
            continue
        m = re.search(r"\bct(\d+)\b", value, re.IGNORECASE)
        if m:
            return m.group(1)

    return None


def load_enrollware_course_numbers():
    """
    Load schedule.json and return a sorted list of unique Enrollware course numbers (as strings).
    """
    if not SCHEDULE_PATH.exists():
        raise FileNotFoundError(f"schedule.json not found at {SCHEDULE_PATH}")

    with SCHEDULE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    course_numbers = set()

    # Look across all likely collections: courses and class/session arrays
    collections = []

    courses = data.get("courses") or []
    if isinstance(courses, list):
        collections.append(courses)

    for key in ("classes", "sessions", "items", "class_list"):
        arr = data.get(key) or []
        if isinstance(arr, list):
            collections.append(arr)

    if not collections:
        raise RuntimeError("No course or class arrays found in schedule.json. Check structure.")

    for coll in collections:
        for item in coll:
            if not isinstance(item, dict):
                continue
            num = extract_enrollware_course_number(item)
            if num:
                course_numbers.add(num)

    if not course_numbers:
        raise RuntimeError(
            "No Enrollware course numbers found. "
            "Could not match ?course=123456 or #ct123456 patterns in schedule.json."
        )

    return sorted(course_numbers, key=int)


def make_svg_for_course_number(course_number: str) -> str:
    """Return SVG markup for a simple numbered tile keyed by the Enrollware course number."""
    label = course_number
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#e3f1ff"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="1200" height="630" fill="url(#bg)" />
  <rect x="80" y="80" width="1040" height="470" rx="40" fill="#ffffff" stroke="#b8c7e3" stroke-width="4"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        font-size="140" fill="#074a86" font-weight="700">
    {label}
  </text>
  <text x="50%" y="72%" dominant-baseline="middle" text-anchor="middle"
        font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        font-size="32" fill="#5d6a7c">
    Enrollware course #{label}
  </text>
</svg>
'''
    return svg


def main():
    print(f"Using schedule.json at: {SCHEDULE_PATH}")
    course_numbers = load_enrollware_course_numbers()
    print(f"Found {len(course_numbers)} Enrollware course numbers in schedule.json:")
    print("  " + ", ".join(course_numbers))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Optional: do NOT auto-delete old files, just overwrite matches.
    for num in course_numbers:
        svg_content = make_svg_for_course_number(num)
        out_path = OUT_DIR / f"{num}.svg"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(svg_content)
        created_files.append(out_path)
        print(f"  wrote {out_path.relative_to(ROOT)}")

    # Build zip for convenience
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in created_files:
            arcname = path.relative_to(ROOT)
            z.write(path, arcname)

    print(f"\nCreated zip: {ZIP_PATH.name} with {len(created_files)} files.")


if __name__ == "__main__":
    main()
