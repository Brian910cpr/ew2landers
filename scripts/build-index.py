# build-index.py
# Rebuild 910CPR homepage from a base template + fresh Enrollware schedule panel.

from pathlib import Path
from bs4 import BeautifulSoup


# Paths (relative to repo root)
BASE_TEMPLATE_PATH = Path("docs/data/index-base.html")         # your saved "good" index
SNAPSHOT_PATH      = Path("docs/data/enrollware-schedule.html")  # fresh Enrollware schedule page
OUTPUT_PATH        = Path("docs/index.html")                   # final homepage


def load_soup(path: Path) -> BeautifulSoup:
    """Load an HTML file into BeautifulSoup, with a clear error if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser")


def extract_schedule_panel(snapshot_soup: BeautifulSoup) -> BeautifulSoup:
    """
    Pull the Enrollware schedule panel from the snapshot.
    We want the entire <div id="maincontent_schedPanel">...</div>.
    """
    panel = snapshot_soup.find("div", id="maincontent_schedPanel")
    if panel is None:
        raise RuntimeError(
            "Could not find <div id='maincontent_schedPanel'> "
            f"in snapshot {SNAPSHOT_PATH}"
        )
    return panel


def inject_schedule_panel(template_soup: BeautifulSoup,
                          schedule_panel: BeautifulSoup) -> BeautifulSoup:
    """
    Replace whatever is inside <div id="schedule-root"> in the template
    with the fresh Enrollware schedule panel.
    """
    root = template_soup.find("div", id="schedule-root")
    if root is None:
        # Fallback: some very early versions may not have schedule-root.
        # In that case, just append after the hero section.
        raise RuntimeError(
            "Template is missing <div id='schedule-root'>. "
            "Make sure index-base.html is the 'good' version you want to reuse."
        )

    # Clear anything currently inside schedule-root
    root.clear()

    # Important: we want the full panel div (not just its children)
    # so we append a copy of the <div id="maincontent_schedPanel"> tag.
    root.append(schedule_panel)

    return template_soup


def normalize_links(html: str) -> str:
    """
    Force coastalcprtraining.com links to use HTTP (not HTTPS),
    per your note.
    """
    html = html.replace("https://coastalcprtraining.com", "http://coastalcprtraining.com")
    html = html.replace("https://www.coastalcprtraining.com", "http://coastalcprtraining.com")
    return html


def build_index(
    base_template_path: Path = BASE_TEMPLATE_PATH,
    snapshot_path: Path = SNAPSHOT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    # 1) Load template (your “good” SEO-packed, styled index)
    template_soup = load_soup(base_template_path)

    # 2) Load fresh Enrollware schedule snapshot
    snapshot_soup = load_soup(snapshot_path)

    # 3) Extract the schedule panel from the snapshot
    schedule_panel = extract_schedule_panel(snapshot_soup)

    # 4) Inject that panel into the template’s #schedule-root
    updated_soup = inject_schedule_panel(template_soup, schedule_panel)

    # 5) Serialize HTML and normalize links
    html_out = str(updated_soup)
    html_out = normalize_links(html_out)

    # 6) Write final homepage
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote homepage: {output_path} (source: {snapshot_path})")


if __name__ == "__main__":
    build_index()
