#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, re, json
from bs4 import BeautifulSoup
from datetime import datetime
try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None

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

def slug(s: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", (s or "").lower()))

def to_abs_url(href: str) -> str:
    href = href or ""
    return href if href.startswith("http") else (ENROLLWARE_BASE + href.lstrip("./"))

def brand_from_title(t: str) -> str:
    x = (t or "").lower()
    if x.startswith("arc") or "american red cross" in x or "arc -" in x: return "Red Cross"
    if "hsi" in x: return "HSI"
    if "aha" in x or "american heart" in x: return "AHA"
    return "Other"

def looks_like_section(text: str) -> bool:
    if not text: return False
    x = text.strip().lower()
    if x in SECTION_HINTS: return True
    return any(x.startswith(h) for h in SECTION_HINTS)

def guess_start_iso(s: str) -> str | None:
    s = (s or "").strip()
    if not s or not dateparser: return None
    try:
        dt = dateparser.parse(s, fuzzy=True)
        if dt and (dt.hour or dt.minute):
            return dt.isoformat()
    except Exception:
        return None
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_enrollware.py docs/data/enrollware-schedule.html", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # Core containers
    root = soup.select_one("#maincontent_sched #enraccordion") or soup

    sections = []                # [{id, title, index}]
    section_index_by_title = {}  # lower(title) -> index

    courses = []                 # [{id, title, section_id, brand, first_seen_index, description_html}]
    course_index_by_title = {}   # lower(title) -> index

    sessions = []                # [{course_id, title, start_text, start_iso, location, url, id}]

    # Strategy:
    # - Walk each .enrpanel as a "course panel"
    # - Extract: <a name="ctNNNNNN"> (course id), heading text, body html
    # - Remove the <ul.enrclass-list> from body to form clean description_html
    # - For each <li><a href="...enroll?id=####">, push a session row
    for panel in root.select(".enrpanel"):
        # Section detection by scanning previous siblings for heading-like text
        # (If not found, default to "Other Programs")
        def find_nearest_section_title(node):
            cur = node
            for _ in range(200):
                if not cur: break
                # previous siblings
                sib = cur.previous_sibling
                while sib:
                    if getattr(sib, "get_text", None):
                        txt = normspace(sib.get_text(" ", strip=True))
                        if looks_like_section(txt):
                            return txt
                    sib = getattr(sib, "previous_sibling", None)
                cur = getattr(cur, "parent", None)
            return None

        section_title = find_nearest_section_title(panel) or "Other Programs"
        st_key = normspace(section_title).lower()
        if st_key not in section_index_by_title:
            sid = "bls" if "bls" in st_key else "acls" if "acls" in st_key else "pals" if "pals" in st_key else "faid"
            srec = { "id": sid, "title": section_title, "index": len(sections) }
            section_index_by_title[st_key] = srec["index"]
            sections.append(srec)

        anchor_name = None
        a_name = panel.select_one("a[name]")
        if a_name and a_name.get("name"):
            anchor_name = a_name.get("name").strip()

        heading_a = panel.select_one(".enrpanel-heading .enrpanel-title a.enrtrigger")
        title = normspace(heading_a.get_text(" ", strip=True)) if heading_a else None
        if not title:
            # fallback: first link with enroll?id in panel
            first_enroll = panel.select_one('a[href*="enroll?id="]')
            title = normspace(first_enroll.get("title") or first_enroll.get_text(" ", strip=True)) if first_enroll else ""
            if not title:
                title = "Untitled Course"

        course_id = anchor_name if anchor_name else slug(title)
        course_brand = brand_from_title(title)

        # description_html = panel body without the session UL
        body = panel.select_one(".enrpanel-body")
        description_html = ""
        if body:
            body_clone = BeautifulSoup(str(body), "lxml")
            # remove list of sessions
            for ul in body_clone.select(".enrclass-list"):
                ul.decompose()
            # drop wrapper div class to keep inner HTML only
            body_inner = body_clone.select_one(".enrpanel-body")
            description_html = "".join(str(x) for x in (body_inner.contents if body_inner else body_clone.contents)).strip()

        ct_key = normspace(title).lower()
        if ct_key not in course_index_by_title:
            courses.append({
                "id": course_id,
                "title": title,
                "section_id": sections[ section_index_by_title[st_key] ]["id"],
                "brand": course_brand,
                "first_seen_index": len(courses),
                "description_html": description_html or None
            })
            course_index_by_title[ct_key] = len(courses) - 1

        # sessions under this course
        for li in panel.select(".enrclass-list li"):
            a = li.select_one("a[href*='enroll?id=']")
            if not a: continue
            href = a.get("href") or ""
            url = to_abs_url(href)
            idm = re.search(r"id=(\d+)", url)
            sess_id = int(idm.group(1)) if idm else None

            # "start_text" is the visible link text; location lives in a nested <span>
            start_text = normspace(a.get_text(" ", strip=True))
            # find the span text as location hint
            sp = a.select_one("span")
            loc_guess = normspace(sp.get_text(" ", strip=True)) if sp else ""
            if not loc_guess:
                m = re.search(CITY_HINTS, start_text, re.I)
                loc_guess = m.group(0) if m else ""

            start_iso = guess_start_iso(start_text)

            sessions.append({
                "course_id": course_id,
                "title": title,
                "start_text": start_text,
                "start_iso": start_iso,
                "location": loc_guess,
                "url": url,
                "id": sess_id
            })

    out = {
        "meta": {
            "source": html_path,
            "fetched_at": datetime.utcnow().isoformat()+"Z",
            "panel_count": len(root.select(".enrpanel"))
        },
        "sections": sections,
        "courses": courses,
        "sessions": sessions
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
