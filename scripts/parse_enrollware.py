#!/usr/bin/env python
"""
parse_enrollware.py

Parse a saved copy of the Enrollware schedule page and produce schedule.json.

Default paths (relative to repo root):
- Input  HTML: docs/data/enrollware-schedule.html
- Output JSON: docs/data/schedule.json

Structure of output (Option B):

[
  {
    "course_id": "241108",
    "option_title_html": "...",      # raw <option> innerHTML from dropdown
    "panel_value_html": "...",       # raw value="" from <div class="enrpanel">
    "description_html": "...",       # full ugly description HTML before the class list
    "description_text": "...",       # plain-text version of description_html
    "classes": [
      {
        "course_id": "241108",
        "class_id": "12353585",
        "url": "https://coastalcprtraining.enrollware.com/enroll?id=12353585",
        "date_text": "Monday, November 17, 2025",
        "date_iso": "2025-11-17",
        "time_text": "9:00 AM",
        "seats_left": 5,
        "location": "NC - Burgaw: 111 S Wright St @ 910CPR's Office",
        "raw_text": "Monday, November 17, 2025 at 9:00 AM (5 seats left)"
      },
      ...
    ]
  },
  ...
]

You can override the input and output paths via command-line:

    python scripts/parse_enrollware.py [input_html] [output_json]

Examples:

    # Use defaults:
    python scripts/parse_enrollware.py

    # Explicit paths:
    python scripts/parse_enrollware.py docs/data/enrollware-schedule.html docs/data/schedule.json
"""

import json
import re
import sys
import datetime
from pathlib import Path

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Default locations inside the repo
DEFAULT_INPUT_HTML = "docs/data/enrollware-schedule.html"
DEFAULT_OUTPUT_JSON = "docs/data/schedule.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_soup(path: str) -> BeautifulSoup:
    """
    Load HTML from disk and return a BeautifulSoup DOM.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input HTML not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return BeautifulSoup(f, "html.parser")


def build_course_map(soup: BeautifulSoup) -> dict:
    """
    Build a mapping from course_id -> <option> inner HTML from the dropdown:

        <select name="ctl00$maincontent$courseList" ...>
            <option value="241108">AHA - ACLS Provider - In-person Initial ...</option>
            ...
        </select>

    Returns:

        {
            "241108": "AHA - ACLS Provider - In-person Initial <img ...> ...",
            ...
        }
    """
    course_map: dict[str, str] = {}

    select = soup.find("select", attrs={"name": "ctl00$maincontent$courseList"})
    if not select:
        return course_map

    for opt in select.find_all("option"):
        value = opt.get("value")
        if not value:
            continue

        # Keep full inner HTML of the option (including <img>, <div>, etc.)
        inner_html = "".join(str(x) for x in opt.contents).strip()
        course_map[value] = inner_html

    return course_map


def extract_description_html(body_div) -> str:
    """
    From a <div class="enrpanel-body">, return everything from the top of
    the body up to (but not including) <ul class="enrclass-list"> as an HTML
    string.

    This preserves your "ugly" description exactly as rendered by Enrollware.
    """
    if not body_div:
        return ""

    ul_classes = body_div.find("ul", class_="enrclass-list")
    if not ul_classes:
        # No class list – just keep the entire body
        return body_div.decode_contents().strip()

    parts: list[str] = []

    # Collect siblings up to (but not including) the <ul class="enrclass-list">
    for child in body_div.children:
        if child is ul_classes:
            break
        parts.append(str(child))

    return "".join(parts).strip()


def html_to_text(html: str) -> str:
    """
    Convert HTML to a reasonably clean text string.
    Keeps basic spacing but strips tags.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def parse_class_li(li, course_id: str) -> dict | None:
    """
    Parse one <li> inside <ul class="enrclass-list">.

    - Skip "Registration is closed" entries.
    - For open classes, return a dict with fields:
        course_id, class_id, url, date_text, date_iso, time_text,
        seats_left, location, raw_text
    """
    a = li.find("a")
    if not a:
        return None

    title_attr = a.get("title", "") or ""
    a_classes = a.get("class", []) or []

    # Closed class – ignore these; they have no seats
    if "greylink" in a_classes or "Registration is closed" in title_attr:
        return None

    href = a.get("href", "") or ""
    m_id = re.search(r"id=(\d+)", href)
    class_id = m_id.group(1) if m_id else None

    # Build text from <a> contents BEFORE any <span> (date/time/seats string)
    text_nodes = []
    for node in a.contents:
        if getattr(node, "name", None) == "span":
            break
        text_nodes.append(str(node))

    # Clean HTML → text
    main_text = BeautifulSoup("".join(text_nodes), "html.parser").get_text(" ", strip=True)
    # Example main_text:
    # "Monday, November 17, 2025 at 9:00 AM (5 seats left)"

    seats_left = None
    m_seats = re.search(r"\((\d+)\s+seat", main_text)
    if m_seats:
        try:
            seats_left = int(m_seats.group(1))
        except ValueError:
            seats_left = None

    if m_seats:
        main_text_wo_seats = main_text[:m_seats.start()].strip()
    else:
        main_text_wo_seats = main_text

    # Split date vs time
    if " at " in main_text_wo_seats:
        date_text, time_text = main_text_wo_seats.split(" at ", 1)
    else:
        date_text, time_text = main_text_wo_seats, ""

    date_text = date_text.strip()
    time_text = time_text.strip()

    # Parse ISO date for easier filtering / sorting
    date_iso = None
    try:
        # "Monday, November 17, 2025"
        dt_date = datetime.datetime.strptime(date_text, "%A, %B %d, %Y")
        date_iso = dt_date.strftime("%Y-%m-%d")
    except Exception:
        # If format changes, just leave date_iso as None; raw text is still there.
        pass

    # Location from <span>...</span>
    span = a.find("span")
    location = span.get_text(" ", strip=True) if span else ""

    return {
        "course_id": course_id,
        "class_id": class_id,
        "url": href,
        "date_text": date_text,
        "date_iso": date_iso,
        "time_text": time_text,
        "seats_left": seats_left,
        "location": location,
        "raw_text": main_text,
    }


def parse_schedule(soup: BeautifulSoup, course_map: dict) -> list[dict]:
    """
    Walk all <div class="enrpanel"> blocks and build a list of course objects,
    each with:

      - course_id
      - option_title_html (from dropdown)
      - panel_value_html (from div.enrpanel)
      - description_html (from div.enrpanel-body before the class list)
      - description_text (plain-text version of description_html)
      - classes[] (parsed live class instances)
    """
    courses: list[dict] = []

    for panel in soup.select("div.enrpanel"):
        # Course anchor: <a name="ct241108">
        name_anchor = panel.find("a", attrs={"name": re.compile(r"^ct\d+")})
        if not name_anchor:
            continue

        anchor_name = name_anchor.get("name", "") or ""
        # Strip "ct" prefix → "241108"
        course_id = anchor_name[2:]

        body_div = panel.find("div", class_="enrpanel-body")
        description_html = extract_description_html(body_div)
        description_text = html_to_text(description_html)

        # The raw "ugly" panel value attribute
        panel_value_html = panel.get("value", "") or ""

        # Parse all live class instances for this course
        class_instances: list[dict] = []
        ul_classes = body_div.find("ul", class_="enrclass-list") if body_div else None
        if ul_classes:
            for li in ul_classes.find_all("li"):
                class_info = parse_class_li(li, course_id)
                if class_info:
                    class_instances.append(class_info)

        course_entry = {
            "course_id": course_id,
            "option_title_html": course_map.get(course_id),
            "panel_value_html": panel_value_html,
            "description_html": description_html,   # full ugly HTML
            "description_text": description_text,   # plain text
            "classes": class_instances,
        }
        courses.append(course_entry)

    return courses


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    """
    CLI entry point.

    argv[0] = optional input HTML path  (defaults to DEFAULT_INPUT_HTML)
    argv[1] = optional output JSON path (defaults to DEFAULT_OUTPUT_JSON)
    """
    if argv is None:
        argv = sys.argv[1:]

    input_html = argv[0] if len(argv) >= 1 else DEFAULT_INPUT_HTML
    output_json = argv[1] if len(argv) >= 2 else DEFAULT_OUTPUT_JSON

    soup = load_soup(input_html)
    course_map = build_course_map(soup)
    courses = parse_schedule(soup, course_map)

    out_path = Path(output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(courses)} courses to {out_path} from {input_html}.")


if __name__ == "__main__":
    main()
