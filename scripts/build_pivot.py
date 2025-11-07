#!/usr/bin/env python3
import sys, re, json
from bs4 import BeautifulSoup, Tag
from datetime import datetime
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

CITY_HINTS = re.compile(r"(Wilmington|Burgaw|Jacksonville|Shipyard|Sound Rd|Hinton Ave|Gum Branch|Merlot|Wright St)", re.I)

def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def slug(s: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", (s or "").lower()))

def brand_from_title(t: str) -> str:
    x = (t or "").lower()
    if x.startswith("arc") or "american red cross" in x or "arc -" in x: return "Red Cross"
    if "hsi" in x: return "HSI"
    if "aha" in x or "american heart" in x: return "AHA"
    return "Other"

def section_id_from_text(t: str) -> str:
    x = (t or "").lower()
    if "bls" in x: return "bls"
    if "acls" in x: return "acls"
    if "pals" in x: return "pals"
    return "faid"

def looks_like_section(text: str) -> bool:
    if not text: return False
    x = text.strip().lower()
    if x in SECTION_HINTS: return True
    return any(x.startswith(h) for h in SECTION_HINTS)

def to_abs_url(href: str) -> str:
    href = href or ""
    return href if href.startswith("http") else (ENROLLWARE_BASE + href.lstrip("./"))

def guess_start_iso(text: str):
    txt = (text or "").strip()
    if not txt:
        return None
    try:
        dt = dateparser.parse(txt, fuzzy=True)
        if dt and (dt.hour or dt.minute):
            return dt.isoformat()
    except Exception:
        return None
    return None

def build_pivot_from_enrollware(html_text: str) -> dict:
    soup = BeautifulSoup(html_text, "lxml")

    # Use Enrollware accordion structure when present
    root = soup.select_one("#maincontent_sched #enraccordion") or soup

    sections = []
    section_index_by_title = {}
    courses  = []
    course_index_by_title  = {}
    sessions = []

    # Primary path: div.enrpanel blocks (Enrollware accordion)
    panels = root.select("div.enrpanel")
    if panels:
        for idx, pnl in enumerate(panels):
            # panel course number
            anchor_named = pnl.select_one("a[name]")  # <a name='ct######'>
            course_name_anchor = (anchor_named.get("name") if anchor_named else "") or ""
            # heading title (HTML text)
            heading_a = pnl.select_one(".enrpanel-heading .enrpanel-title a.enrtrigger")
            course_title_html = heading_a.decode_contents() if heading_a else ""
            course_title_text = normspace(BeautifulSoup(course_title_html, "lxml").get_text(" ", strip=True))
            # infer section by scanning upward/backward for a section-like label (fallback)
            section_title = "Other Programs"
            # if panel has data-section attr or nearby heading we could use it; fallback to heuristics on title
            # Using heuristics:
            guess = course_title_text.lower()
            if "bls" in guess: section_title = "Healthcare Provider: BLS"
            elif "acls" in guess: section_title = "Healthcare Provider: ACLS"
            elif "pals" in guess: section_title = "Healthcare Provider: PALS"
            elif "heartsaver" in guess or "first aid" in guess: section_title = "CPR / AED & First Aid"

            st_key = section_title.lower()
            if st_key not in section_index_by_title:
                sections.append({
                    "id": section_id_from_text(section_title),
                    "title": section_title,
                    "index": len(sections)
                })
                section_index_by_title[st_key] = len(sections)-1

            # ensure course
            ct_key = course_title_text.lower()
            if ct_key not in course_index_by_title:
                courses.append({
                    "id": course_name_anchor or slug(course_title_text),
                    "title": course_title_text,
                    "title_html": course_title_html,
                    "section_id": sections[section_index_by_title[st_key]]["id"],
                    "brand": brand_from_title(course_title_text),
                    "first_seen_index": len(courses),
                    "description_html": "",  # fill below
                })
                course_index_by_title[ct_key] = len(courses)-1

            # description_html (full inner HTML of the body, minus the UL of sessions)
            body = pnl.select_one(".enrpanel-body")
            desc_html = ""
            if body:
                body_clone = BeautifulSoup(str(body), "lxml")
                ul = body_clone.select_one(".enrclass-list")
                if ul: ul.extract()
                # unwrap outer container if present
                desc_html = "".join(str(child) for child in body_clone.contents)

            courses[course_index_by_title[ct_key]]["description_html"] = desc_html

            # sessions list
            for a in pnl.select(".enrpanel-body ul.enrclass-list li a[href*='enroll?id=']"):
                href = a.get("href") or ""
                url = to_abs_url(href)
                idm = re.search(r"id=(\d+)", url)
                sess_id = int(idm.group(1)) if idm else None

                start_text = normspace(a.get_text(" ", strip=True))
                # Enrollware shows location in <span> inside the anchor; capture if present
                span = a.find("span")
                loc_text = normspace(span.get_text(" ", strip=True)) if span else ""
                start_iso = guess_start_iso(start_text)

                sessions.append({
                    "course_id": courses[course_index_by_title[ct_key]]["id"],
                    "title": course_title_text,  # tie back to readable course title
                    "start_text": start_text,
                    "start_iso": start_iso,
                    "location": loc_text or "",
                    "url": url,
                    "id": sess_id
                })

    else:
        # Fallback path: no enrpanel structure; scan all enroll anchors in DOM order
        for a in soup.select('a[href*="enroll?id="]'):
            href = a.get("href") or ""
            url = to_abs_url(href)
            idm = re.search(r"id=(\d+)", url)
            sess_id = int(idm.group(1)) if idm else None

            row = a.find_parent(["li","tr","div","section","article"]) or a
            row_text = normspace(row.get_text(" ", strip=True))
            # Use row context to approximate course title
            title = normspace(a.get("title") or a.get_text(" ", strip=True) or row_text)

            # infer section
            section_title = "Other Programs"
            lower = title.lower()
            if "bls" in lower: section_title = "Healthcare Provider: BLS"
            elif "acls" in lower: section_title = "Healthcare Provider: ACLS"
            elif "pals" in lower: section_title = "Healthcare Provider: PALS"
            elif "heartsaver" in lower or "first aid" in lower: section_title = "CPR / AED & First Aid"

            st_key = section_title.lower()
            if st_key not in section_index_by_title:
                sections.append({
                    "id": section_id_from_text(section_title),
                    "title": section_title,
                    "index": len(sections)
                })
                section_index_by_title[st_key] = len(sections)-1

            ct_key = title.lower()
            if ct_key not in course_index_by_title:
                courses.append({
                    "id": slug(title),
                    "title": title,
                    "title_html": title,
                    "section_id": sections[section_index_by_title[st_key]]["id"],
                    "brand": brand_from_title(title),
                    "first_seen_index": len(courses),
                    "description_html": ""
                })
                course_index_by_title[ct_key] = len(courses)-1

            start_text = normspace(a.get_text(" ", strip=True)) or row_text[:140]
            start_iso = guess_start_iso(start_text)
            locm = CITY_HINTS.search(row_text)
            location = locm.group(0) if locm else ""

            sessions.append({
                "course_id": courses[course_index_by_title[ct_key]]["id"],
                "title": title,
                "start_text": start_text,
                "start_iso": start_iso,
                "location": location,
                "url": url,
                "id": sess_id
            })

    out = {
        "meta": {
            "source": "docs/data/enrollware-schedule.html",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "panel_count": len(panels),
            "session_count": len(sessions)
        },
        "sections": sections,
        "courses": courses,
        "sessions": sessions
    }
    return out

def main():
    if len(sys.argv) < 2:
        print("Usage: build_pivot.py docs/data/enrollware-schedule.html", file=sys.stderr)
        sys.exit(1)
    html_path = sys.argv[1]
    html_text = open(html_path, "r", encoding="utf-8", errors="ignore").read()
    pivot = build_pivot_from_enrollware(html_text)
    print(json.dumps(pivot, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
