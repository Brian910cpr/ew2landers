#!/usr/bin/env python3

-- coding: utf-8 --

"""
Parse docs/data/enrollware-schedule.html into an ordered pivot JSON:

{
"meta": {...},
"sections": [{"id":"bls","title":"Healthcare Provider: BLS","index":0}, ...],
"courses": [{"id":"aha-bls-provider-in-person-initial","title":"AHA - BLS Provider - In-person Initial","section_id":"bls","brand":"AHA","first_seen_index":7,"description_html":null}, ...],
"sessions": [{"course_id":"aha-bls-provider-in-person-initial","title":"AHA - BLS Provider - In-person Initial","start_text":"Mon Nov 10 1:00 PM","start_iso":"2025-11-10T13:00:00-05:00","location":"Wilmington","url":"https://coastalcprtraining.enrollware.com/enroll?id=10657559","id":10657559
}, ...]
}

• Order is preserved exactly as it appears on the HTML page.
• We detect sections by heading-like nodes and common section titles.
• Courses are inferred from the nearest text around each enroll link and grouped by title.
• Dates are best-effort parsed to ISO; raw text is kept as start_text.
"""

import sys, re, json, hashlib
from bs4 import BeautifulSoup, NavigableString, Tag
from datetime import datetime
from dateutil import parser as dateparser

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/
"

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
# Also accept lines that start with these phrases
return any(x.startswith(h) for h in SECTION_HINTS)

def normspace(s: str) -> str:
return re.sub(r"\s+", " ", (s or "")).strip()

def to_abs_url(href: str) -> str:
href = href or ""
return href if href.startswith("http") else (ENROLLWARE_BASE + href.lstrip("./"))

def find_nearest_section_title(node: Tag) -> str | None:
# Walk backwards through siblings and up to parents to find a heading-like label
cur = node
steps = 0
while cur and steps < 200:
steps += 1
# Check previous siblings
sib = cur.previous_sibling
while sib:
if isinstance(sib, Tag):
txt = normspace(sib.get_text(" ", strip=True))
if looks_like_section(txt):
return txt
sib = sib.previous_sibling
# climb up
cur = cur.parent if isinstance(cur, Tag) else None
if cur:
txt = normspace(cur.get_text(" ", strip=True))
# If the parent looks like a section container with a title at top, scanning siblings again will catch it next loop
# stop at body
if cur.name == "body":
break
return None

def guess_start_iso(s: str) -> str | None:
s = (s or "").strip()
if not s:
return None
# Try parsing liberally with dateutil; if fails, return None
try:
dt = dateparser.parse(s, fuzzy=True)
# If parser guessed a date without time (rare), leave as None to avoid lying
if dt and (dt.hour or dt.minute):
return dt.isoformat()
except Exception:
return None
return None

def find_row_text(anchor: Tag) -> str:
row = anchor.find_parent(["tr","li","div","section","article"]) or anchor
# Prefer row text (often contains time/location)
return normspace(row.get_text(" ", strip=True))

def extract_title(anchor: Tag, row_text: str) -> str:
# Prefer explicit anchor title attr; else visible anchor text; else fall back to trimmed row text.
at = normspace(anchor.get("title"))
if at: return at
atext = normspace(anchor.get_text(" ", strip=True))
if atext: return atext
# Sometimes row_text is huge; try to collapse to something course-like by stripping time fragments
# If nothing better, return row_text
return row_text

def main():
if len(sys.argv) < 2:
print("Usage: parse_enrollware.py docs/data/enrollware-schedule.html", file=sys.stderr)
sys.exit(1)

html_path = sys.argv[1]
with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
    soup = BeautifulSoup(f.read(), "lxml")

enroll_anchors = soup.select('a[href*="enroll?id="]')

sections = []              # ordered
section_index_by_title = {}# title(lower) -> index
courses = []               # ordered by first appearance
course_index_by_title = {} # title(lower) -> index
sessions = []              # all sessions
# We walk anchors in DOM order, assigning them to the closest previously seen section title
for a in enroll_anchors:
    href = a.get("href") or ""
    url = to_abs_url(href)
    idm = re.search(r"id=(\d+)", url)
    sess_id = int(idm.group(1)) if idm else None

    row_text = find_row_text(a)
    title = extract_title(a, row_text)
    section_title = find_nearest_section_title(a) or "Other Programs"

    # ensure section exists
    st_key = normspace(section_title).lower()
    if st_key not in section_index_by_title:
        sid = section_id_from_text(section_title)
        srec = {
            "id": sid,
            "title": section_title,
            "index": len(sections)
        }
        section_index_by_title[st_key] = srec["index"]
        sections.append(srec)

    # ensure course exists (by exact title)
    ct_key = normspace(title).lower()
    if ct_key not in course_index_by_title:
        c_id = slug(title)
        brand = brand_from_title(title)
        courses.append({
            "id": c_id,
            "title": title,
            "section_id": sections[ section_index_by_title[st_key] ]["id"],
            "brand": brand,
            "first_seen_index": len(courses),
            "description_html": None
        })
        course_index_by_title[ct_key] = len(courses) - 1

    # session details
    # Time text — search nearby text for a time; keep both raw and parsed ISO if possible.
    # We’ll try dateutil on the whole row_text, which commonly holds "Mon 11/10 1:00 PM ..." etc.
    start_text = None
    # Try common “1:00 PM” presence as a guard; otherwise we still feed the parser.
    tm = re.search(r"\b\d{1,2}:\d{2}\s?(AM|PM)\b", row_text, re.I)
    if tm:
        # pull a window around the time to give parser context
        start_text = row_text[max(0, tm.start()-30): tm.end()+40]
    else:
        # fallback to a smaller portion of row text
        start_text = row_text[:140]

    start_iso = guess_start_iso(start_text)

    # location hint
    locm = re.search(CITY_HINTS, row_text, re.I)
    location = locm.group(0) if locm else ""

    sessions.append({
        "course_id": courses[ course_index_by_title[ct_key] ]["id"],
        "title": title,
        "start_text": start_text.strip() if start_text else "",
        "start_iso": start_iso,
        "location": location,
        "url": url,
        "id": sess_id
    })

out = {
    "meta": {
        "source": html_path,
        "fetched_at": datetime.utcnow().isoformat()+"Z",
        "anchor_count": len(enroll_anchors)
    },
    "sections": sections,
    "courses": courses,
    "sessions": sessions
}
print(json.dumps(out, ensure_ascii=False, indent=2))


if name == "main":
main()