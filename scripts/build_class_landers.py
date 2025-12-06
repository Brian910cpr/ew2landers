import json
import re
from datetime import datetime
from pathlib import Path

# Paths – tweak if your layout is different
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "docs" / "data"
CLASSES_DIR = ROOT / "docs" / "classes"
TEMPLATE_PATH = CLASSES_DIR / "template.html"

SCHEDULE_JSON = DATA_DIR / "schedule.json"
COURSES_JSON = DATA_DIR / "courses.json"

# -------------- helpers --------------

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_course_name_index(schedule):
    """
    schedule['courses'] is an array of {id, name} that matches course_id in sessions.
    """
    course_index = {}
    for c in schedule.get("courses", []):
        course_index[c["id"]] = c["name"]
    return course_index

def build_course_ct_anchor_map(schedule):
    """
    Build course_id -> ct_number using the 'aggregator' sessions:
      - id == "" (no session id)
      - register_url contains 'course=NNNNNN'
    """
    course_to_ct = {}

    for s in schedule.get("sessions", []):
        sid = s.get("id", "")
        if sid:
            continue  # real sessions only, skip here

        reg = s.get("register_url", "")
        m = re.search(r"course=(\d+)", reg)
        if not m:
            continue

        ct = m.group(1)
        course_id = s.get("course_id")
        if course_id is not None:
            course_to_ct[course_id] = ct

    return course_to_ct

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "class"

def parse_start_datetime(start_display):
    """
    start_display looks like: 'Thursday, December 11, 2025 at 1:00 PM'
    """
    try:
        return datetime.strptime(start_display, "%A, %B %d, %Y at %I:%M %p")
    except Exception:
        return None

def is_future_class(start_display):
    dt = parse_start_datetime(start_display)
    if not dt:
        return True  # if we can't parse, be safe and treat as future
    return dt >= datetime.now()

def build_filename_for_session(session):
    """
    Pick a stable filename for each class lander.

    If you already use a specific scheme, change this to match.
    Safe default: class-<id>.html
    """
    sid = session["id"]
    return f"class-{sid}.html"

# -------------- main build --------------

def main():
    # Ensure output dir exists
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    schedule = load_json(SCHEDULE_JSON)
    courses_meta = load_json(COURSES_JSON)

    # Look up course names for convenience (if you want them)
    schedule_course_index = build_course_name_index(schedule)

    # Map course_id -> ctNNNNNN
    course_to_ct = build_course_ct_anchor_map(schedule)

    # Index course_id -> courses.json entry (for cleanTitle, family, etc.)
    courses_by_id = {c["course_id"]: c for c in courses_meta.get("courses", [])}

    # Read template
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Filter real sessions (id not empty)
    sessions = [
        s for s in schedule.get("sessions", [])
        if str(s.get("id", "")).strip() != ""
    ]

    print(f"Building {len(sessions)} class landers...")

    for s in sessions:
        sid = s["id"]
        course_id = s["course_id"]
        course_name = s["course_name"]
        start_display = s["start_display"]
        location = s["location"]
        register_url = s["register_url"]

        # Figure out course-level schedule link from ct number
        ct_number = course_to_ct.get(course_id)
        if ct_number:
            schedule_url = f"https://coastalcprtraining.enrollware.com/schedule#ct{ct_number}"
        else:
            # Fallback: generic schedule (you can tighten this later)
            schedule_url = "https://coastalcprtraining.enrollware.com/schedule"

        # Button behavior based on date
        future = is_future_class(start_display)
        if future:
            primary_label = "Register for this class"
            primary_href = register_url
            secondary_label = "See other dates and times"
            secondary_href = schedule_url
        else:
            primary_label = "Registration closed. See other times?"
            primary_href = schedule_url
            secondary_label = "See current schedule"
            secondary_href = schedule_url

        # Pull any extra metadata from courses.json if you want
        course_meta = courses_by_id.get(course_id)
        if course_meta:
            clean_title = course_meta.get("cleanTitle", course_name)
            family = course_meta.get("family", "")
        else:
            clean_title = course_name
            family = ""

        page_title = f"{clean_title} – {start_display} – {location}"

        # Very simple string replace template.
        # Make sure template.html actually has these tokens.
        html = template_html
        html = html.replace("{{TITLE}}", page_title)
        html = html.replace("{{COURSE_NAME}}", clean_title)
        html = html.replace("{{COURSE_FAMILY}}", family)
        html = html.replace("{{START_DISPLAY}}", start_display)
        html = html.replace("{{LOCATION}}", location)
        html = html.replace("{{REGISTER_URL}}", register_url)
        html = html.replace("{{SCHEDULE_URL}}", schedule_url)
        html = html.replace("{{PRIMARY_LABEL}}", primary_label)
        html = html.replace("{{PRIMARY_HREF}}", primary_href)
        html = html.replace("{{SECONDARY_LABEL}}", secondary_label)
        html = html.replace("{{SECONDARY_HREF}}", secondary_href)
        html = html.replace("{{SESSION_ID}}", sid)

        # Write file
        filename = build_filename_for_session(s)
        out_path = CLASSES_DIR / filename
        out_path.write_text(html, encoding="utf-8")

    print("Done.")

if __name__ == "__main__":
    main()
