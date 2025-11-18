#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
910CPR – Enrollware Schedule Parser (Revised, Clean)

Parses an Enrollware HTML export into two JSON outputs:

1) docs/data/schedule.json
   Rich canonical dataset

2) docs/data/schedule-sidebar.json
   Minimal dataset for GoDaddy Periscope Drawer

Usage:
  python scripts/parse_enrollware.py docs/data/enrollware-schedule.html docs/data/schedule.json
"""

import sys
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime


# -----------------------------------------------------------
# Delivery Mode Normalizer
# -----------------------------------------------------------
def normalize_delivery_mode(title: str) -> str:
    t = title.lower()

    if "heartcode" in t:
        return "HEARTCODE"
    if "blended" in t:
        return "BLENDED"
    if "online" in t and "skills" not in t:
        return "ONLINE"

    return "ILT"  # default


# -----------------------------------------------------------
# Family Normalizer (canonical)
# -----------------------------------------------------------
def normalize_family(course_title: str) -> str:
    t = course_title.lower()

    if "bls" in t:
        return "BLS"
    if "acls" in t:
        return "ACLS"
    if "pals" in t:
        return "PALS"
    if "pears" in t:
        return "PEARS"
    if "asls" in t:
        return "ASLS"

    if "first aid" in t and "cpr" in t:
        return "FA-CPR-AED"
    if "cpr" in t and "aed" in t:
        return "CPR-AED"

    if "family" in t and "friends" in t:
        return "FNF"

    if "instructor" in t:
        return "INSTRUCTOR"

    return "OTHER"


# -----------------------------------------------------------
# Cert Body normalizer
# -----------------------------------------------------------
def normalize_cert_body(title: str) -> str:
    t = title.lower()
    if "aha" in t:
        return "AHA"
    if "red cross" in t or "arc" in t:
        return "ARC"
    if "hsi" in t:
        return "HSI"
    return "AHA"


# -----------------------------------------------------------
# Parse Enrollware-style date/time
# Example: "Thu 11/13/25 1:00p"
# -----------------------------------------------------------
def parse_enrollware_datetime(raw_dt: str):
    if not raw_dt:
        return None

    s = raw_dt.replace("\xa0", " ").strip()

    if " - " in s:
        s = s.split(" - ")[0].strip()

    # Convert trailing 'a'/'p' to AM/PM
    m = re.search(r'([ap])$', s)
    if m:
        s = s[:-1] + ("AM" if m.group(1) == "a" else "PM")

    fmts = [
        "%a %m/%d/%y %I:%M%p",
        "%m/%d/%y %I:%M%p",
        "%m/%d/%Y %I:%M%p",
    ]

    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except:
            pass

    return None


# -----------------------------------------------------------
# Parse the Enrollware HTML table
# -----------------------------------------------------------
def parse_html(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")
    sessions = []
    courses = {}

    for r in rows:
        cols = r.find_all("td")
        if len(cols) < 5:
            continue

        raw_dt = cols[0].get_text(strip=True)
        session_id_text = cols[1].get_text(strip=True)
        title = cols[2].get_text(strip=True)
        location = cols[3].get_text(strip=True)
        enrolled_text = cols[-2].get_text(strip=True)

        # Skip header rows
        if not re.search(r"\d", session_id_text):
            continue

        dt = parse_enrollware_datetime(raw_dt)
        if dt is None:
            continue

        m = re.search(r"(\d{4,9})", session_id_text)
        if m:
            course_id = int(m.group(1))
        else:
            course_id = abs(hash(title)) % 10_000_000

        # Compute seats remaining from "X / Y"
        seats = 0
        capacity = None
        m2 = re.search(r"(\d+)\s*/\s*(\d+)", enrolled_text)
        if m2:
            enrolled_num = int(m2.group(1))
            capacity = int(m2.group(2))
            seats = max(0, capacity - enrolled_num)

        fam = normalize_family(title)
        body = normalize_cert_body(title)
        mode = normalize_delivery_mode(title)

        # Save course object
        if course_id not in courses:
            courses[course_id] = {
                "courseId": course_id,
                "title": title,
                "family": fam,
                "certBody": body,
                "deliveryMode": mode,
                "price": 0.0
            }

        # Save session
        sessions.append({
            "session_id": session_id_text,
            "course_id": course_id,
            "title": title,
            "family": fam,
            "certBody": body,
            "deliveryMode": mode,
            "location": location,
            "start": dt.isoformat(),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%I:%M %p").lstrip("0"),
            "seats": seats,
            "capacity": capacity
        })

    return courses, sessions


# -----------------------------------------------------------
# Build sidebar-friendly sessions
# -----------------------------------------------------------
def build_sidebar_sessions(courses, sessions):
    out = []

    for s in sessions:
        c = courses.get(s["course_id"], {})
        session_id = s["session_id"]

        register_url = f"https://coastalcprtraining.enrollware.com/enroll?id={session_id}"

        out.append({
            "sessionId": session_id,
            "courseId": s["course_id"],
            "family": s["family"],
            "certBody": s["certBody"],
            "deliveryMode": s["deliveryMode"],
            "location": s["location"],
            "date": s["date"],
            "time": s["time"],
            "seats": s["seats"],
            "price": float(c.get("price", 0.0)),
            "registerUrl": register_url
        })

    return out


# -----------------------------------------------------------
# Main runner
# -----------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_enrollware.py input.html docs/data/schedule.json")
        sys.exit(1)

    input_html = sys.argv[1]
    output_json = sys.argv[2]

    courses, sessions = parse_html(input_html)

    # Write rich canonical
    rich = {
        "generated_at": datetime.now().isoformat(),
        "courses": list(courses.values()),
        "sessions": sessions
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(rich, f, ensure_ascii=False, indent=2)

    # Write sidebar format
    sidebar = build_sidebar_sessions(courses, sessions)
    sidebar_path = output_json.replace("schedule.json", "schedule-sidebar.json")

    with open(sidebar_path, "w", encoding="utf-8") as f:
        json.dump(sidebar, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(courses)} courses and {len(sessions)} sessions")
    print(f"Sidebar file: {sidebar_path}")


if __name__ == "__main__":
    main()
