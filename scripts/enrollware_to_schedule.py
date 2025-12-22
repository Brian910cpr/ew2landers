#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/"
LOCAL_TZ_NAME = "America/New_York"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME) if ZoneInfo else None

# Match ct id anywhere
CT_RE = re.compile(r"#ct(\d+)", re.IGNORECASE)

# Match enroll links (various forms)
# Examples:
#   enroll?id=123
#   enroll.aspx?id=123
#   /enroll?id=123&x=y
ENROLL_RE = re.compile(r"(?:^|/)(enroll(?:\.aspx)?)\?[^\"']*?\bid=(\d+)", re.IGNORECASE)


def log(msg: str) -> None:
    sys.stderr.write(str(msg).rstrip() + "\n")


def normalize_ws(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.replace("\xa0", " ").split())


def extract_ct(text: str | None) -> str | None:
    if not text:
        return None
    m = CT_RE.search(text)
    return m.group(1) if m else None


def find_ct_in_panel(panel) -> str | None:
    if panel is None:
        return None

    # 1) hrefs
    for a in panel.find_all("a", href=True):
        cn = extract_ct(a.get("href"))
        if cn:
            return cn

    # 2) any attribute values
    for tag in panel.find_all(True):
        for _, v in (tag.attrs or {}).items():
            if v is None:
                continue
            vals = v if isinstance(v, (list, tuple)) else [v]
            for item in vals:
                cn = extract_ct(str(item))
                if cn:
                    return cn

    # 3) raw HTML
    return extract_ct(str(panel))


def build_schedule_url(ct: str | None) -> str | None:
    if not ct:
        return None
    return urljoin(ENROLLWARE_BASE, f"schedule#ct{ct}")


def extract_enroll_rel(text: str | None) -> tuple[str, str] | None:
    """Return (rel_url, id) like ('enroll?id=123', '123')"""
    if not text:
        return None
    m = ENROLL_RE.search(text)
    if not m:
        return None
    path = m.group(1)  # enroll or enroll.aspx
    sid = m.group(2)
    return (f"{path}?id={sid}", sid)


def find_enrolls_in_panel(panel):
    """Return list of (abs_url, sid, context_text)"""
    found = []
    seen = set()

    # A) anchors
    for a in panel.find_all("a", href=True):
        rel = extract_enroll_rel(a.get("href"))
        if not rel:
            continue
        rel_url, sid = rel
        absu = urljoin(ENROLLWARE_BASE, rel_url)
        ctx = normalize_ws(a.parent.get_text(" ", strip=True) if a.parent else a.get_text(" ", strip=True))
        key = (absu, sid)
        if key not in seen:
            seen.add(key)
            found.append((absu, sid, ctx))

    # B) any tag attributes (onclick/data-href/etc.)
    for tag in panel.find_all(True):
        attrs = tag.attrs or {}
        for _, v in attrs.items():
            if v is None:
                continue
            vals = v if isinstance(v, (list, tuple)) else [v]
            for item in vals:
                rel = extract_enroll_rel(str(item))
                if not rel:
                    continue
                rel_url, sid = rel
                absu = urljoin(ENROLLWARE_BASE, rel_url)
                ctx = normalize_ws(tag.get_text(" ", strip=True) or (tag.parent.get_text(" ", strip=True) if tag.parent else ""))
                key = (absu, sid)
                if key not in seen:
                    seen.add(key)
                    found.append((absu, sid, ctx))

    # C) raw panel HTML fallback (rare but helps)
    html = str(panel)
    for m in ENROLL_RE.finditer(html):
        path = m.group(1)
        sid = m.group(2)
        rel_url = f"{path}?id={sid}"
        absu = urljoin(ENROLLWARE_BASE, rel_url)
        key = (absu, sid)
        if key not in seen:
            seen.add(key)
            found.append((absu, sid, ""))

    return found


def parse_start(text: str | None):
    if not text:
        return (None, None, None)

    s = normalize_ws(text)

    fmts = [
        "%A, %B %d, %Y at %I:%M %p",
        "%A, %B %d, %Y at %I %p",
        "%B %d, %Y at %I:%M %p",
        "%B %d, %Y at %I %p",
    ]

    dt = None
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            break
        except Exception:
            pass

    if not dt:
        return (None, None, None)

    if LOCAL_TZ:
        dt = dt.replace(tzinfo=LOCAL_TZ)

    start_iso = dt.isoformat()
    start_ms = int(dt.timestamp() * 1000)

    now = datetime.now(tz=LOCAL_TZ) if LOCAL_TZ else datetime.now()
    is_past = dt < now

    return (start_iso, start_ms, is_past)


def html_to_rows(html_text: str):
    soup = BeautifulSoup(html_text, "html.parser")
    panels = soup.select(".enrpanel")
    log(f"[enrollware_to_schedule] Found {len(panels)} enrpanel blocks.")

    course_meta = {}

    # course meta
    for panel in panels:
        pid = (panel.get("id") or "").strip()
        cid = pid.replace("enrpanel", "").strip()
        if not cid:
            continue

        title_el = panel.select_one(".enrtitle") or panel.select_one("h2") or panel.select_one("h3")
        title = normalize_ws(title_el.get_text(" ", strip=True) if title_el else "")

        ct = find_ct_in_panel(panel)
        schedule_url = build_schedule_url(ct)

        course_meta[cid] = {"title": title, "course_number": ct, "schedule_url": schedule_url}

    rows = []

    for panel in panels:
        pid = (panel.get("id") or "").strip()
        cid = pid.replace("enrpanel", "").strip()
        if not cid:
            continue

        meta = course_meta.get(cid, {})
        title = meta.get("title") or ""
        ct = meta.get("course_number")
        schedule_url = meta.get("schedule_url")

        enrolls = find_enrolls_in_panel(panel)
        if not enrolls:
            continue

        for reg_url, sid, ctx in enrolls:
            start_iso, start_ms, is_past = parse_start(ctx)

            rows.append({
                "id": sid,
                "course_id": cid,
                "course_number": ct,
                "title": title,
                "date": ctx,
                "time": None,
                "location": None,
                "url": reg_url,
                "register_url": reg_url,
                "schedule_url": schedule_url,
                "start_iso": start_iso,
                "start_ms": start_ms,
                "is_past": is_past,
                "end_iso": None,
            })

    log(f"[enrollware_to_schedule] Built {len(rows)} schedule rows.")
    return rows


def main():
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / "docs" / "data" / "enrollware-schedule.html"
    output_path = repo_root / "docs" / "data" / "schedule.json"

    html_text = input_path.read_text(encoding="utf-8", errors="ignore")
    rows = html_to_rows(html_text)

    # SAFETY NET: do NOT overwrite schedule.json with an empty list
    if len(rows) == 0:
        log("ERROR: Built 0 rows. Not writing schedule.json (keeping previous).")
        return 2

    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Wrote {len(rows)} rows to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
