import json
import os
from pathlib import Path
from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont

Root paths

ROOT = Path(file).resolve().parent
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule.json"
OUTPUT_DIR = ROOT / "docs" / "assets" / "images" / "course"

def load_schedule(path: Path):
if not path.exists():
raise FileNotFoundError(f"schedule.json not found at: {path}")
with path.open("r", encoding="utf-8") as f:
return json.load(f)

def extract_course_number_from_url(url: str):
"""
Try to pull a numeric course or ct value out of a URL string.
Examples it can handle:
...schedule#ct209811
...?course=209811
"""
if not isinstance(url, str):
return None

# Look for "#ctNNNNNN"
if "#ct" in url:
    frag = url.split("#ct", 1)[1]
    digits = "".join(ch for ch in frag if ch.isdigit())
    return digits or None

# Look for "course=NNNNNN"
if "course=" in url:
    frag = url.split("course=", 1)[1]
    digits = "".join(ch for ch in frag if ch.isdigit())
    return digits or None

return None


def extract_course_number_and_title(schedule):
"""
Build a mapping: course_number -> representative title string.
We:
- find a course number (explicit field or parsed from URL)
- grab the first non-empty title we see for that course
"""
known_keys = [
"course_number",
"courseNumber",
"enrollware_course_number",
"enrollwareCourseNumber",
]

mapping = OrderedDict()  # course_number -> title

for item in schedule:
    if not isinstance(item, dict):
        continue

    course_number = None

    # Try explicit keys first
    for key in known_keys:
        if key in item and item[key]:
            course_number = str(item[key])
            break

    # Fallback: derive from URL
    if not course_number:
        url = item.get("url") or item.get("enroll_url") or item.get("enrollUrl")
        course_number = extract_course_number_from_url(url)

    if not course_number:
        continue

    # Normalize to digits if possible
    digits = "".join(ch for ch in str(course_number) if ch.isdigit())
    if not digits:
        continue

    # Get title
    title = item.get("title") or item.get("name") or ""
    if digits not in mapping and title:
        mapping[digits] = title

return mapping


def clean_course_label(raw_title: str) -> str:
"""
Turn a full Enrollware title into a clean 'AHA BLS Provider' style label:
- Keep certifying body (AHA, ARC, HSI) if present
- Remove trailing location segments
- Normalize some common patterns
"""

if not raw_title:
    return "CPR / First Aid"

title = raw_title.strip()

# Split on common dash types and remove obvious location segments
# e.g. "AHA BLS Provider – Wilmington" -> ["AHA BLS Provider", "Wilmington"]
parts = [p.strip() for p in title.replace("—", "-").split("-")]

# Known city/location words we want to drop if they appear as last segment
location_keywords = [
    "Wilmington",
    "Shipyard",
    "Jacksonville",
    "Burgaw",
    "Holly Ridge",
    "Myrtle Beach",
    "NC",
    "SC",
]

if len(parts) > 1:
    last = parts[-1]
    # If last part looks like a location (contains a known keyword or a comma),
    # drop it and keep the rest.
    if any(kw.lower() in last.lower() for kw in location_keywords) or "," in last:
        parts = parts[:-1]

base = " - ".join(parts).strip()

# Normalize common certifying body names
# We want something like "AHA BLS Provider", "ARC BLS", "HSI First Aid/CPR/AED"
replacements = [
    ("American Heart Association", "AHA"),
    ("American Heart Assoc.", "AHA"),
    ("American Red Cross", "ARC"),
    ("Red Cross", "ARC"),
]
for old, new in replacements:
    if old.lower() in base.lower():
        base = base.replace(old, new)

# If base starts with BLS/ACLS/PALS etc. but has no body, we can leave it; not fatal.
# Also normalize the pipe character into a slash for visual clarity.
base = base.replace("|", "/")

# Trim excessive whitespace
base = " ".join(base.split())

# Hard fallback if something goes weird
if not base:
    return "CPR / First Aid"

return base


def ensure_output_dir(path: Path):
path.mkdir(parents=True, exist_ok=True)

def draw_text_centered(draw, text, font, box, fill):
"""
Draw text centered within a given (x1, y1, x2, y2) box.
"""
x1, y1, x2, y2 = box
w, h = draw.textsize(text, font=font)
x = x1 + (x2 - x1 - w) / 2
y = y1 + (y2 - y1 - h) / 2
draw.text((x, y), text, font=font, fill=fill)

def make_course_image_png(course_number: str, course_label: str, output_path: Path):
"""
Create a PNG tile for the given course number + course label.
Layout:
- Top bar with '910CPR • CPR & Medical Training'
- Big centered course_label
- Small 'Course # NNNNNN'
- Footer 'Class dates and registration at 910CPR.com'
"""
width, height = 800, 450
background = (243, 247, 252) # very light blue/gray
border = (180, 196, 214)
accent = (16, 92, 135) # deep blue
text_color = (20, 20, 20)
muted = (80, 80, 80)

img = Image.new("RGB", (width, height), background)
draw = ImageDraw.Draw(img)

# Fonts
try:
    title_font = ImageFont.truetype("arial.ttf", 52)
    small_font = ImageFont.truetype("arial.ttf", 24)
    tiny_font = ImageFont.truetype("arial.ttf", 20)
except Exception:
    title_font = ImageFont.load_default()
    small_font = ImageFont.load_default()
    tiny_font = ImageFont.load_default()

# Border
draw.rectangle([(0, 0), (width - 1, height - 1)], outline=border, width=3)

# Top accent bar
bar_height = 70
draw.rectangle([(0, 0), (width, bar_height)], fill=accent)
bar_text = "910CPR \u2022 CPR & Medical Training"
draw_text_centered(draw, bar_text, small_font, (0, 0, width, bar_height), fill=(255, 255, 255))

# Main course label (big)
main_box = (40, bar_height + 40, width - 40, bar_height + 40 + 140)
draw_text_centered(draw, course_label, title_font, main_box, fill=text_color)

# Course number (small)
num_text = f"Course # {course_number}"
num_box = (40, bar_height + 40 + 140, width - 40, bar_height + 40 + 200)
draw_text_centered(draw, num_text, small_font, num_box, fill=muted)

# Footer
footer_text = "Class dates and registration at 910CPR.com"
footer_box = (40, height - 70, width - 40, height - 20)
draw_text_centered(draw, footer_text, tiny_font, footer_box, fill=muted)

output_path.parent.mkdir(parents=True, exist_ok=True)
img.save(output_path, format="PNG")


def main():
print(f"Using schedule.json at: {SCHEDULE_PATH}")
schedule_data = load_schedule(SCHEDULE_PATH)

# schedule.json may be a list or a dict with "sessions"
if isinstance(schedule_data, dict):
    if "sessions" in schedule_data and isinstance(schedule_data["sessions"], list):
        schedule_list = schedule_data["sessions"]
    else:
        # If it's not obviously wrapped, try treating it as a sequence anyway
        schedule_list = list(schedule_data.get("sessions", []))
else:
    schedule_list = schedule_data

if not isinstance(schedule_list, list):
    raise ValueError("schedule.json is not an array or sessions list I can iterate.")

# Build mapping: course_number -> raw_title
number_title_map = extract_course_number_and_title(schedule_list)
if not number_title_map:
    print("No course numbers found in schedule.json – nothing to do.")
    return

ensure_output_dir(OUTPUT_DIR)

print(f"Found {len(number_title_map)} Enrollware course numbers in schedule.json:")
print("  " + ", ".join(number_title_map.keys()))

for course_number, raw_title in number_title_map.items():
    label = clean_course_label(raw_title)
    out_path = OUTPUT_DIR / f"{course_number}.png"
    make_course_image_png(course_number, label, out_path)
    print(f"  wrote {out_path.as_posix()}")

print(f"\nGenerated {len(number_title_map)} PNG images in {OUTPUT_DIR.as_posix()}")


if name == "main":
main()