# scripts/parse_enrollware.py
# Usage:
#   python scripts/parse_enrollware.py docs/data/enrollware-schedule.html > docs/data/schedule.json
# Produces a robust JSON with sessions[], keeping stable course_id (ct######) and course_title.

import sys, json, re, hashlib
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"

WEEKDAY = r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
TIME12  = r"\d{1,2}:\d{2}\s*(?:AM|PM)"
ISO_DT  = r"\d{4}-\d{2}-\d{2}.*?\d{1,2}:\d{2}"

LOC_HINT = re.compile(r"Wilmington|Burgaw|Jacksonville|Shipyard|Sound Rd|Hinton Ave|Gum Branch|Merlot|Wright St", re.I)

def slug(s: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", (s or "").lower()))

def guess_date(text: str):
    if not text:
        return None
    # try direct parse
    try:
        d = datetime.fromisoformat(text)
        return d.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        pass
    # leave as raw; browser will localize
    return None

def is_section_header(txt: str) -> bool:
    x = (txt or "").strip().lower()
    heads = (
        "healthcare provider: bls",
        "healthcare provider: acls",
        "healthcare provider: pals",
        "healthcare provider: asls",
        "cpr / aed & first aid",
        "cpr / aed only",
        "instructor programs",
        "other programs",
    )
    return any(x.startswith(h) for h in heads) or x in heads

def parse(html: str):
    soup = BeautifulSoup(html, "lxml")
    body = soup.body or soup

    # collect section markers in order
    sections = []
    for el in body.find_all(True):
        txt = " ".join((el.get_text(separator=" ") or "").split())
        if is_section_header(txt):
            sections.append(el)

    def nearest_section(el):
        # walk backwards to find last header before el
        node = el
        while node:
            prev = node.find_previous()
            if prev is None:
                break
            txt = " ".join((prev.get_text(separator=" ") or "").split())
            if is_section_header(txt):
                return txt
            node = prev
        return None

    out = []
    for a in soup.select('a[href*="enroll?id="]'):
        href = a.get("href") or ""
        if not href:
            continue
        url = href if href.startswith("http") else ENROLLWARE_BASE + href.lstrip("/")
        m = re.search(r"id=(\d+)", url)
        id_num = int(m.group(1)) if m else None

        panel = a.find_parent(class_="enrpanel")
        if not panel:
            continue

        # title preference: enrpanel @value (strip tags) > heading
        raw_title = panel.get("value") or ""
        raw_title = re.sub(r"<[^>]+>", "", raw_title or "")
        if not raw_title:
            t1 = panel.select_one(".enrpanel-heading .enrpanel-title")
            t2 = panel.select_one(".enrpanel-heading a.enrtrigger, .enrpanel-heading a")
            raw_title = " ".join(((t1.get_text() if t1 else "") or (t2.get_text() if t2 else "")).split())
        course_title = " ".join((raw_title or "").split())
        if not course_title:
            continue

        anchor = panel.select_one('a[name^="ct"]')
        course_id = anchor.get("name") if anchor else slug(course_title)

        row = a.find_parent(["li", "tr"]) or a.parent
        text = " ".join(((row.get_text() if row else a.get_text()) or "").split())

        when = None
        m1 = re.search(rf"{WEEKDAY}.*?{TIME12}", text, flags=re.I)
        if m1:
            when = m1.group(0)
        else:
            m2 = re.search(ISO_DT, text)
            if m2:
                when = m2.group(0)

        location = ""
        span_loc = row.select_one("span") if hasattr(row, "select_one") else None
        if span_loc and span_loc.get_text(strip=True):
            location = span_loc.get_text(strip=True)
        else:
            mloc = LOC_HINT.search(text)
            if mloc:
                location = mloc.group(0)

        start = a.get("data-start") or guess_date(when)

        out.append({
            "id": id_num,
            "url": url,
            "start": start,
            "end": None,
            "location": location,
            "title": course_title,       # keep for compatibility
            "course_title": course_title,
            "course_id": course_id,      # stable key (ct###### or slug)
            "section": nearest_section(panel) or "",
            "classType": infer_type(course_title),
            "instructor": None,
            "seats": None
        })

    return {
        "meta": {
            "source": sys.argv[1] if len(sys.argv) > 1 else "",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "panel_count": len(soup.select(".enrpanel"))
        },
        "sessions": out
    }

def infer_type(title: str) -> str:
    t = (title or "").lower()
    if "acls" in t: return "ACLS"
    if "pals" in t: return "PALS"
    if "bls" in t: return "BLS"
    if "heartsaver" in t: return "Heartsaver"
    if "hsi" in t: return "HSI"
    return "Other"

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_enrollware.py <snapshot.html>", file=sys.stderr)
        sys.exit(2)
    html_path = Path(sys.argv[1])
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    data = parse(html)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
