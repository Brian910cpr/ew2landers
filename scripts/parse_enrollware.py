#!/usr/bin/env python3

-- coding: utf-8 --

import sys, re, json
from bs4 import BeautifulSoup

ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com/
"

def guess_type(title: str) -> str:
t = (title or "").lower()
if "acls" in t: return "ACLS"
if "pals" in t: return "PALS"
if "bls" in t: return "BLS"
if "heartsaver" in t: return "Heartsaver"
if "hsi" in t: return "HSI"
return "Other"

def guess_start(text: str):
m = re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[^\n]{0,60}?\b\d{1,2}:\d{2}\s?(AM|PM)\b", text or "", re.I)
if not m:
m = re.search(r"\b\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}\b", text or "")
return m.group(0) if m else None

def find_location(text: str):
m = re.search(r"(Wilmington|Burgaw|Jacksonville|Shipyard|Sound Rd|Hinton Ave|Gum Branch)", text or "", re.I)
return m.group(0) if m else ""

def norm_space(s: str) -> str:
return re.sub(r"\s+", " ", (s or "")).strip()

def main():
if len(sys.argv) < 2:
print("Usage: parse_enrollware.py docs/data/enrollware-schedule.html", file=sys.stderr)
sys.exit(1)

html_path = sys.argv[1]
with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
    soup = BeautifulSoup(f.read(), "lxml")

out = []
for a in soup.select('a[href*="enroll?id="]'):
    href = a.get("href") or ""
    url  = href if href.startswith("http") else (ENROLLWARE_BASE + href.lstrip("./"))
    idm = re.search(r"id=(\d+)", url)
    sess_id = int(idm.group(1)) if idm else None

    row = a.find_parent(["tr","div"]) or a
    row_text = norm_space(row.get_text(" ", strip=True))
    title = norm_space(a.get("title") or a.get_text(" ", strip=True) or row_text)

    if len(row_text) > len(title) + 10:
        title = row_text

    start_attr = a.get("data-start")
    start = start_attr or guess_start(row_text)
    location = find_location(row_text)
    class_type = guess_type(title)

    out.append({
        "id": sess_id,
        "classType": class_type,
        "title": title,
        "start": start,
        "end": None,
        "location": location,
        "instructor": None,
        "seats": None,
        "url": url
    })

print(json.dumps(out, ensure_ascii=False, indent=2))


if name == "main":
main()