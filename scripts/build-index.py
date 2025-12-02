#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build-index.py (verbose)

Generate docs/index.html by injecting updated schedule HTML into your template.
"""

import sys
from pathlib import Path

from bs4 import BeautifulSoup

DEFAULT_INPUT = Path("docs/data/enrollware-schedule.html")
DEFAULT_OUTPUT = Path("docs/index.html")


def log(msg: str) -> None:
    print(f"[build-index] {msg}", flush=True)


# YOUR FULL TEMPLATE GOES HERE — do not shorten or remove placeholders.
INDEX_TEMPLATE = """
<<< PASTE YOUR ACTUAL TEMPLATE EXACTLY AS-IS HERE >>>
"""


def parse_snapshot(path: Path) -> BeautifulSoup:
    log(f"Loading snapshot: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    log(f"Snapshot size: {len(html)} bytes.")
    return BeautifulSoup(html, "html.parser")


def extract_schedule_panel(soup: BeautifulSoup) -> str:
    log("Searching for #maincontent_schedPanel...")
    panel = soup.find(id="maincontent_schedPanel")
    if panel:
        log("Found schedule panel.")
        return str(panel)

    log("Panel not found; falling back to #enrmain or <body>.")
    fallback = soup.find(id="enrmain") or soup.body
    return str(fallback)


def build_index(input_path: Path, output_path: Path) -> None:
    log("Building index.html...")
    soup = parse_snapshot(input_path)
    panel_html = extract_schedule_panel(soup)

    html = INDEX_TEMPLATE.replace("{{SCHEDULE_PANEL}}", panel_html)

    output_path.write_text(html, encoding="utf-8")
    log(f"Index written: {output_path}")


def main():
    log("Starting build-index main().")
    args = sys.argv[1:]
    in_path = Path(args[0]) if len(args) else DEFAULT_INPUT
    out_path = Path(args[1]) if len(args) > 1 else DEFAULT_OUTPUT
    log(f"Input HTML: {in_path}")
    log(f"Output HTML: {out_path}")

    build_index(in_path, out_path)
    log("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
