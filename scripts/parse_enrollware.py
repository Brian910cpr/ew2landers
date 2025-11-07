#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, re, json
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"

SECTION_HINTS = [
    "healthcare provider: bls",
    "healthcare provider: acls",
    "healthcare provider: pals",
    "healthcare provider: asls",
    "cpr / aed & first aid",
    "cpr / aed only",
    "instructor programs",
    "other programs",
]

CITY_HINTS = r"(Wilmington|Burgaw|Jacksonville|Shipyard|Sound Rd|Hinton Ave|Gum Branch|Merlot|Wright St)"

def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def to_abs_url(href: str) -> str:
    href = href or ""
    return href if href.startswith("http") else (ENROLLWARE_BASE + href.lstrip("./"))

def looks_like_section(text: str) -> bool:
    if not text:
        return False
    x = text.strip().lower()
    return (x in SECTION_HINTS) or any(x.startswith(h) for h in SECTION_HINTS)

def section_id_from_text(t: str) -> str:
    x = (t or "").lower()
    if "bls" in x:  return "bls"
    if "acls" in x: return "acls"
    if "pals" in x: return "pals"
    return "faid"

def brand_from_title(t: str) -> str:
    x = (t or "").lower()
    if x.startswith("arc") or "american red cross" in x or "arc -" in x: return "Red Cross"
    if "hsi" in x: return "HSI"
    if "aha" in x or "american heart" in x: return "AHA"
    return "Other"

def slug(s: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", (s or "").lower()))

def find_nearest_section_title(a):
    cur = a
    steps = 0
    while cur and steps < 200:
        steps += 1
        sib = getattr(cur, "previous_sibling", None)
        while sib:
            if getattr(sib, "get_text", None):
                txt = normspace(sib.get_text(" ", strip=True))
                if looks_like_section(txt):
                    return txt
            sib = sib.previous_sibling
        cur = getattr(cur, "parent", None)
        if getattr(cur, "name", None) == "body":
            break
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_enrollware.py docs/data/enrollware-schedule.html", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    anchors = soup.select('a[href*="enroll?id="]')

    sections, sec_idx = [], {}
    courses, course_idx = [], {}
    sessions = []

    for a in anchors:
        href = a.get("href") or ""
        url = to_abs_url(href)
        idm = re.search(r"id=(\d+)", url)
        sess_id = int(idm.group(1)) if idm else None

        row = a.find_parent(["tr","li","div","section","article"]) or a
        row_text = normspace(row.get_text(" ", strip=True))

        atitle = normspace(a.get("title"))
        title = atitle or normspace(a.get_text(" ", strip=True)) or row_text

        section_title = find_nearest_section_title(a) or "Other Programs"
        st_key = section_title.lower()
        if st_key not in sec_idx:
            sid = section_id_from_text(section_title)
            sec_idx[st_key] = len(sections)
            sections.append({"id": sid, "title": section_title, "index": len(sections)})

        ct_key = title.lower()
        if ct_key not in course_idx:
            courses.append({
                "id": slug(title),
                "title": title,
                "section_id": sections[sec_idx[st_key]]["id"],
                "brand": brand_from_title(title),
                "first_seen_index": len(courses),
                "description_html": None
            })
            course_idx[ct_key] = len(courses) - 1

        tm = re.search(r"\b\d{1,2}:\d{2}\s?(AM|PM)\b", row_text, re.I)
        start_text = row_text[max(0, tm.start()-30): tm.end()+40] if tm else row_text[:140]

        try:
            dt = dateparser.parse(start_text, fuzzy=True)
            start_iso = dt.isoformat() if dt and (dt.hour or dt.minute) else None
        except Exception:
            start_iso = None

        locm = re.search(CITY_HINTS, row_text, re.I)
        location = locm.group(0) if locm else ""

        sessions.append({
            "course_id": courses[course_idx[ct_key]]["id"],
            "title": title,
            "start_text": start_text.strip(),
            "start_iso": start_iso,
            "location": location,
            "url": url,
            "id": sess_id
        })

    print(json.dumps({
        "meta": {"source": html_path, "anchor_count": len(anchors)},
        "sections": sections,
        "courses": courses,
        "sessions": sessions
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
