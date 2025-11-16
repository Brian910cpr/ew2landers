#!/usr/bin/env python
"""
parse_enrollware.py

Usage:
    python scripts/parse_enrollware.py INPUT_HTML OUTPUT_JSON

Parses the Enrollware public schedule HTML into a flat sessions list
plus course-level records, preserving the original ugly HTML descriptions.

Key behaviors:
- Uses the <select id="maincontent_courseList"> to discover valid course_ids.
- Only panels whose anchor name="ct######" matches that list are parsed.
  (This automatically drops the bogus "BLS Quick Reference Guide" panel.)
- Each <div class="enrpanel"> becomes one course record.
- Each <li> inside <ul class="enrclass-list"> becomes one session record,
  unless it is marked "Registration is closed" or has class "greylink".
- deliveryMode is "in_person" or "blended" (Option A).
- family is one of:
    BLS, ACLS, PALS, PEARS, ASLS, First Aid/CPR/AED, CPR/AED, Other
- certBody is one of:
    AHA, ARC, HSI, USCG, OTHER
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup  # type: ignore


# ---------- classification helpers ----------

def classify_cert_body(text: str) -> str:
    t = text.lower()
    if "aha" in t or "_aha" in t or "heartcode" in t:
        return "AHA"
    if "red cross" in t or "arc -" in t or "_arc" in t:
        return "ARC"
    if "hsi" in t or "_hsi" in t:
        return "HSI"
    if "merchant mariner" in t or "amerha-216" in t or "u.s. coast guard" in t or "us coast guard" in t or "uscg" in t:
        return "USCG"
    if "osha" in t:
        return "OTHER"
    # default catch-all
    return "OTHER"


def classify_family(text: str) -> str:
    """
    Map the course name/description into one of the agreed families:
    BLS, ACLS, PALS, PEARS, ASLS, First Aid/CPR/AED, CPR/AED, Other
    """
    t = text.lower()

    # High-priority specific families first
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "pears" in t:
        return "PEARS"
    if "asls" in t or "advanced stroke life support" in t:
        return "ASLS"

    # BLS (but avoid double-counting elementary first aid or others)
    if " bls" in t or t.startswith("bls "):
        return "BLS"

    # First Aid / CPR / AED
    if "first aid" in t and "cpr" in t and "aed" in t:
        return "First Aid/CPR/AED"
    if "elementary first aid" in t:
        # USCG flavor, still conceptually FA/CPR/AED
        return "First Aid/CPR/AED"
    if "merchant mariner" in t:
        # treat as Other per our discussion
        return "Other"

    # CPR/AED without explicit first aid
    if "cpr/aed" in t or ("cpr" in t and "aed" in t):
        return "CPR/AED"

    # Everything else: OSHA, Infant CPR & Choking, Family & Friends, etc.
    return "Other"


def classify_delivery_mode(text: str) -> str:
    """
    Option A: "in_person" vs "blended".
    Any mention of online / HeartCode / blended learning pushes it to "blended".
    """
    t = text.lower()
    blended_markers = [
        "heartcode",
        "online + in-person",
        "online class with in-person",
        "online class with in-person skill session",
        "blended learning",
        "online coursework with in-person skills",
        "online heartsaver",
        "online + in-person skills",
        "online class",
        "online program",
        "online only",
    ]
    for m in blended_markers:
        if m in t:
            return "blended"
    return "in_person"


def clean_course_title(option_text: str) -> str:
    """
    Take the <option> visible text and trim to a reasonably short course title.
    Generally we want the leading "AHA - BLS Provider - In-person Initial"
    part, not the trailing descriptive subtitle.
    """
    text = " ".join(option_text.split())
    # Try cutting at common descriptive phrases
    cut_markers = [
        " Instructor-led Classroom",
        " Blended Learning",
        " Online Class",
        " Online + In-Person",
        " Online + In-person",
        " ONLINE",
        " – Online",
        " — Online",
    ]
    for marker in cut_markers:
        idx = text.find(marker)
        if idx > 0:
            return text[:idx].strip()
    return text.strip()


# ---------- dataclasses ----------

@dataclass
class CourseRecord:
    course_id: int
    uglyTitle: str
    cleanTitle: str
    family: str
    certBody: str
    deliveryMode: str
    uglyHTML: str
    session_ids: List[int]


@dataclass
class SessionRecord:
    session_id: int
    course_id: int
    family: str
    certBody: str
    deliveryMode: str
    start: Optional[str]
    end: Optional[str]
    location: str
    city: Optional[str]
    state: Optional[str]
    instructor: Optional[str]
    seats: Optional[int]
    title: str
    raw_label: str


# ---------- parsing helpers ----------

def load_soup(path: Path) -> BeautifulSoup:
    with path.open("r", encoding="utf-8") as f:
        html = f.read()
    return BeautifulSoup(html, "html.parser")


def parse_course_select(soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
    """
    Read <select id="maincontent_courseList"> and return:
      { course_id_str: { "option_text": "...", "clean_title": "..." } }
    """
    mapping: Dict[str, Dict[str, str]] = {}
    select = soup.find("select", id="maincontent_courseList")
    if not select:
        return mapping

    for opt in select.find_all("option"):
        value = (opt.get("value") or "").strip()
        if not value or not value.isdigit():
            continue
        option_text = opt.get_text(" ", strip=True)
        mapping[value] = {
            "option_text": option_text,
            "clean_title": clean_course_title(option_text),
        }
    return mapping


DATE_RE = re.compile(r"^\s*([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}\s+at\s+\d{1,2}:\d{2}\s+[AP]M)")


def parse_session_datetime(label: str) -> Optional[datetime]:
    """
    label example:
      "Thursday, November 13, 2025 at 1:00 PM (5 seats  left)"
    We strip the parentheses part and parse the leading datetime.
    """
    m = DATE_RE.match(label)
    if not m:
        return None
    dt_str = m.group(1)
    try:
        return datetime.strptime(dt_str, "%A, %B %d, %Y at %I:%M %p")
    except ValueError:
        return None


SEATS_RE = re.compile(r"(\d+)\s+seat")


def parse_seats(label: str) -> Optional[int]:
    m = SEATS_RE.search(label.lower())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


LOCATION_CITY_STATE_RE = re.compile(r"\b([A-Za-z .'-]+),\s*([A-Z]{2})\b")


def split_city_state(location: str) -> Tuple[Optional[str], Optional[str]]:
    m = LOCATION_CITY_STATE_RE.search(location)
    if not m:
        return None, None
    city = m.group(1).strip()
    state = m.group(2).strip()
    return city, state


def extract_ugly_html_without_classlist(body_div) -> str:
    """
    Take the <div class="enrpanel-body"> and return inner HTML,
    but without the <ul class="enrclass-list"> used for sessions.
    """
    if body_div is None:
        return ""
    # We don't want to mutate the original soup too much, so copy
    body_clone = BeautifulSoup(str(body_div), "html.parser")
    ul = body_clone.find("ul", class_="enrclass-list")
    if ul:
        ul.decompose()
    # Return inner HTML of the cloned body div
    inner = "".join(str(child) for child in body_clone.div.contents)
    return inner.strip()


def parse_enrollware(html_path: Path) -> Dict[str, object]:
    soup = load_soup(html_path)

    # 1) Get the course list from the dropdown
    course_select_map = parse_course_select(soup)
    valid_course_ids = set(course_select_map.keys())

    courses: Dict[int, CourseRecord] = {}
    sessions: List[SessionRecord] = []

    # 2) Parse each panel
    panels = soup.find_all("div", class_="enrpanel")
    for panel in panels:
        # anchor like <a name='ct241108'></a>
        anchor = panel.find("a", attrs={"name": re.compile(r"^ct\d+$")})
        if not anchor:
            continue
        course_id_str = anchor.get("name", "")[2:]
        if course_id_str not in valid_course_ids:
            # This automatically drops the BLS Quick Reference Guide panel
            continue

        course_id = int(course_id_str)
        course_info = course_select_map[course_id_str]
        option_text = course_info["option_text"]
        clean_title = course_info["clean_title"]

        ugly_title = panel.get("value") or ""
        if not ugly_title:
            # fallback to the clickable heading content
            trigger = panel.find("a", class_="enrtrigger")
            ugly_title = trigger.decode_contents() if trigger else clean_title

        # classification based on the option text (or ugly title as backup)
        base_text = option_text or ugly_title
        family = classify_family(base_text)
        cert_body = classify_cert_body(base_text)
        delivery_mode = classify_delivery_mode(base_text)

        # ugly HTML description (without the session list)
        body_div = panel.find("div", class_="enrpanel-body")
        ugly_html = extract_ugly_html_without_classlist(body_div)

        # initialize course record if new
        if course_id not in courses:
            courses[course_id] = CourseRecord(
                course_id=course_id,
                uglyTitle=ugly_title,
                cleanTitle=clean_title,
                family=family,
                certBody=cert_body,
                deliveryMode=delivery_mode,
                uglyHTML=ugly_html,
                session_ids=[],
            )

        # 3) Session list
        class_list = panel.find("ul", class_="enrclass-list")
        if not class_list:
            continue

        for li in class_list.find_all("li"):
            a = li.find("a")
            if not a:
                continue

            title_attr = (a.get("title") or "").strip().lower()
            class_attr = (a.get("class") or [])
            if "registration is closed" in title_attr:
                continue
            if any(cls.lower() == "greylink" for cls in class_attr):
                # closed / unavailable
                continue

            href = a.get("href") or ""
            m = re.search(r"id=(\d+)", href)
            if not m:
                continue
            session_id = int(m.group(1))

            # first text node before the <span> is the date/time label
            # we take the first non-empty stripped string that is not from <span>
            raw_label = ""
            for content in a.contents:
                if getattr(content, "name", None) == "span":
                    break
                if isinstance(content, str):
                    raw_label += content
            raw_label = " ".join(raw_label.split())

            dt = parse_session_datetime(raw_label)
            start_iso = dt.isoformat(timespec="seconds") if dt else None

            seats = parse_seats(raw_label)

            span_loc = a.find("span")
            location = span_loc.get_text(" ", strip=True) if span_loc else ""

            city, state = split_city_state(location)

            session = SessionRecord(
                session_id=session_id,
                course_id=course_id,
                family=family,
                certBody=cert_body,
                deliveryMode=delivery_mode,
                start=start_iso,
                end=None,
                location=location,
                city=city,
                state=state,
                instructor=None,  # not present in public schedule
                seats=seats,
                title=clean_title,
                raw_label=raw_label,
            )
            sessions.append(session)
            courses[course_id].session_ids.append(session_id)

    # Build final JSON structure
    data = {
        "meta": {
            "source": str(html_path),
            "fetched_at": datetime.utcnow().isoformat(timespec="microseconds") + "Z",
            "panel_count": len(panels),
            "session_count": len(sessions),
        },
        "courses": [asdict(c) for c in sorted(courses.values(), key=lambda c: c.course_id)],
        "sessions": [asdict(s) for s in sessions],
    }
    return data


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/parse_enrollware.py "
            "INPUT_HTML OUTPUT_JSON",
            file=sys.stderr,
        )
        sys.exit(1)

    input_html = Path(sys.argv[1])
    output_json = Path(sys.argv[2])

    if not input_html.exists():
        print(f"ERROR: input HTML not found: {input_html}", file=sys.stderr)
        sys.exit(1)

    data = parse_enrollware(input_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Wrote {len(data['courses'])} courses and "
        f"{len(data['sessions'])} sessions to {output_json} "
        f"from {input_html}."
    )


if __name__ == "__main__":
    main()
