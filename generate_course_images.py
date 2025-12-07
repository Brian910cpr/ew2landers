import json
import os
import zipfile
from pathlib import Path

# Adjust if your layout is slightly different
ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule.json"
OUT_DIR = ROOT / "docs" / "assets" / "images" / "course"
ZIP_PATH = ROOT / "course-number-images.zip"

def load_course_ids():
    """Load schedule.json and return a sorted list of unique course_ids."""
    if not SCHEDULE_PATH.exists():
        raise FileNotFoundError(f"schedule.json not found at {SCHEDULE_PATH}")

    with SCHEDULE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    ids = set()

    # 1) Look for a "courses" array with ids
    courses = data.get("courses") or []
    for c in courses:
        cid = c.get("id")
        if isinstance(cid, int):
            ids.add(cid)

    # 2) Look for "classes" or "sessions" array with course_id
    for key in ("classes", "sessions", "items", "class_list"):
        arr = data.get(key) or []
        for item in arr:
            cid = item.get("course_id")
            if isinstance(cid, int):
                ids.add(cid)

    if not ids:
        raise RuntimeError("No course IDs found in schedule.json. "
                           "Check the JSON structure or adjust the script.")

    return sorted(ids)

def make_svg_for_course(course_id: int) -> str:
    """Return SVG markup for a simple numbered tile."""
    cid_str = str(course_id)
    # Simple 1200x630 Open-Graph-ish rectangle with big centered text
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
    {cid_str}
  </text>
  <text x="50%" y="72%" dominant-baseline="middle" text-anchor="middle"
        font-family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        font-size="32" fill="#5d6a7c">
    Enrollware course #{cid_str}
  </text>
</svg>
'''
    return svg

def main():
    course_ids = load_course_ids()
    print(f"Found {len(course_ids)} course IDs in schedule.json")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    created_files = []

    for cid in course_ids:
        svg_content = make_svg_for_course(cid)
        out_path = OUT_DIR / f"{cid}.svg"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(svg_content)
        created_files.append(out_path)
        print(f"  wrote {out_path.relative_to(ROOT)}")

    # Build zip for convenience
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in created_files:
            # Store with a nice relative path inside the zip
            arcname = path.relative_to(ROOT)
            z.write(path, arcname)
    print(f"\nCreated zip: {ZIP_PATH.name} with {len(created_files)} files.")

if __name__ == "__main__":
    main()
