import json
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent
CLASSES_DIR = BASE_DIR / "docs" / "classes"  # adjust if you keep /classes elsewhere
TEMPLATE_PATH = CLASSES_DIR / "template.html"
SCHEDULE_JSON = BASE_DIR / "docs" / "data" / "schedule.json"  # adjust to your actual path

TODAY = date.today()

def load_template():
    return TEMPLATE_PATH.read_text(encoding="utf-8")

def load_schedule():
    with SCHEDULE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)

def format_datetime(class_obj):
    # Adjust field names to match your JSON exactly
    # Examples:
    #   class_obj["start_date"] = "2025-01-14"
    #   class_obj["start_time"] = "09:00"
    date_str = class_obj.get("start_date")
    time_str = class_obj.get("start_time")

    if not date_str:
        return ""

    dt_str = date_str
    if time_str:
        dt_str += " " + time_str

    try:
        # If your schedule.json is using ISO date only, you may need two branches:
        if time_str:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return dt_str

    # Example output: "Wednesday, January 14, 2025 at 9:00 AM"
    if time_str:
        return dt.strftime("%A, %B %-d, %Y at %-I:%M %p")
    else:
        return dt.strftime("%A, %B %-d, %Y")

def is_past_class(class_obj):
    date_str = class_obj.get("start_date")
    if not date_str:
        return False
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False
    return d < TODAY

def build_past_banner(class_obj):
    if not is_past_class(class_obj):
        return ""
    # Banner shown when class date has passed
    return """
    <div class="past-class-banner">
      <strong>This class date has passed.</strong>
      <p>Registration is closed for this specific session. Please see other available dates below.</p>
    </div>
    """

def build_upcoming_list(class_obj, all_classes_for_same_course):
    """
    all_classes_for_same_course is a list of class objects with the same course type.
    Filter to future sessions and render a small list.
    """
    items = []
    for other in all_classes_for_same_course:
        if not other.get("start_date"):
            continue
        try:
            d = datetime.strptime(other["start_date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < TODAY:
            continue

        dt_text = format_datetime(other)
        loc_text = other.get("city_state") or other.get("location") or ""
        register_url = other.get("enroll_url") or other.get("register_url") or "#"

        items.append(f"""
        <li>
          <a href="{register_url}">
            {dt_text} – {loc_text}
          </a>
        </li>
        """)

    if not items:
        return "<p>No upcoming sessions are currently listed. Check back soon or call 910-395-5193.</p>"

    return "<ul>\n" + "\n".join(items) + "\n</ul>"

def render_page(template_html, class_obj, siblings_for_same_course):
    # Pull course-level and class-level fields from JSON
    course_name = class_obj.get("course_name") or class_obj.get("course_title") or "CPR Class"
    class_datetime = format_datetime(class_obj)
    class_location = class_obj.get("display_location") or class_obj.get("location") or ""
    meta_description = class_obj.get("meta_description") or (
        f"{course_name} on {class_datetime} in {class_location} with 910CPR."
    )

    # THIS IS THE FIX FOR YOUR “GARBAGE” LINKS:
    # Use the schedule URL from JSON instead of a generic one.
    # Replace the .get(...) key names with whatever you actually used.
    course_schedule_url = (
        class_obj.get("course_schedule_url") or
        class_obj.get("schedule_url") or
        "#"
    )

    register_url = class_obj.get("enroll_url") or class_obj.get("register_url") or "#"

    past_banner_html = build_past_banner(class_obj)
    upcoming_list_html = build_upcoming_list(class_obj, siblings_for_same_course)

    if is_past_class(class_obj):
        register_button_text = "Registration closed. See other times"
        schedule_link_text = "See other dates for this class"
        # When past, send main button to schedule page, not enroll
        register_href = course_schedule_url if course_schedule_url != "#" else register_url
    else:
        register_button_text = "Register for this class"
        schedule_link_text = "See more upcoming dates"
        register_href = register_url

    page_title = f"{course_name} – {class_datetime} – 910CPR"

    html = template_html
    html = html.replace("{{PAGE_TITLE}}", page_title)
    html = html.replace("{{META_DESCRIPTION}}", meta_description)
    html = html.replace("{{COURSE_NAME}}", course_name)
    html = html.replace("{{CLASS_DATETIME}}", class_datetime)
    html = html.replace("{{CLASS_LOCATION}}", class_location)
    html = html.replace("{{PAST_BANNER_HTML}}", past_banner_html)
    html = html.replace("{{REGISTER_URL}}", register_href)
    html = html.replace("{{REGISTER_BUTTON_TEXT}}", register_button_text)
    html = html.replace("{{UPCOMING_LIST_HTML}}", upcoming_list_html)
    html = html.replace("{{COURSE_SCHEDULE_URL}}", course_schedule_url)
    html = html.replace("{{SCHEDULE_LINK_TEXT}}", schedule_link_text)

    return html

def main():
    template_html = load_template()
    schedule = load_schedule()

    # You’ll need to adapt this part to the actual structure of schedule.json.
    #
    # Example assumption:
    #   schedule.json = { "classes": [ { ...class fields... }, ... ] }
    #
    # Or if it’s a flat list: [ { ... }, ... ]
    if isinstance(schedule, dict) and "classes" in schedule:
        classes = schedule["classes"]
    else:
        classes = schedule

    # Group classes by "course_id" or "course_code" so we can build the upcoming list.
    by_course = {}
    for cls in classes:
        course_key = cls.get("course_code") or cls.get("offer_code") or "unknown"
        by_course.setdefault(course_key, []).append(cls)

    # Output each class lander
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)

    for cls in classes:
        course_key = cls.get("course_code") or cls.get("offer_code") or "unknown"
        siblings = by_course.get(course_key, [])

        slug = cls.get("slug") or cls.get("lander_slug")
        if not slug:
            # Fallback: generate a slug like bls-wilmington-2025-01-14-0900
            base = course_key.lower().replace(" ", "-")
            date_str = cls.get("start_date", "")
            time_str = cls.get("start_time", "")
            slug_parts = [base, date_str, time_str.replace(":", "")]
            slug = "-".join([p for p in slug_parts if p])

        out_path = CLASSES_DIR / f"{slug}.html"
        html = render_page(template_html, cls, siblings)

        out_path.write_text(html, encoding="utf-8")
        print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
