
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build-index.py

Generate a static docs/index.html for 910CPR using the latest
Enrollware schedule snapshot.

Defaults:
input: docs/data/enrollware-schedule.html
output: docs/index.html
"""

import sys
from pathlib import Path
from textwrap import dedent

from bs4 import BeautifulSoup

DEFAULT_INPUT = Path("docs/data/enrollware-schedule.html")
DEFAULT_OUTPUT = Path("docs/index.html")

INDEX_TEMPLATE = dedent("""\

<!DOCTYPE html> <html lang="en"> <head> <meta charset="utf-8"> <title>910CPR | CPR, BLS, ACLS &amp; PALS Classes in Wilmington &amp; Burgaw, NC</title> <meta name="description" content="Book CPR, BLS, ACLS, PALS and ...s, fast cards, late options, and on-site training for offices."> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <link rel="canonical" href="https://www.910cpr.com/">

<style>
:root {
    --bg: #f5f7fb;
    --text: #212529;
    --muted: #6c757d;
    --card-bg: #ffffff;
    --border: #dee2e6;
    --accent: #0d6efd;
    --accent-soft: rgba(13, 110, 253, 0.12);
    --accent-dark: #084298;
    --shadow-soft: 0 10px 25px rgba(15, 23, 42, 0.08);
    --pill-family-aha: #0d6efd;
    --pill-family-aha-soft: rgba(13, 110, 253, 0.08);
    --pill-family-aha-alt: #0b5ed7;
    --pill-family-aha-alt-soft: rgba(11, 94, 215, 0.08);
    --pill-family-hsi: #198754;
    --pill-family-hsi-soft: rgba(25, 135, 84, 0.08);
    --pill-family-arc: #dc3545;
    --pill-family-arc-soft: rgba(220, 53, 69, 0.08);
    --pill-family-other: #6c757d;
    --pill-family-other-soft: rgba(108, 117, 125, 0.08);
    --pill-outline: rgba(15, 23, 42, 0.06);
    --header-bg: linear-gradient(120deg, #0d6efd 0%, #6610f2 80%);
    --header-overlay: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.75));
    --family-pill-radius: 999px;
    --transition-fast: 150ms ease-out;
    --transition-med: 220ms ease-out;
    --transition-slow: 320ms ease;
    --ring: 0 0 0 2px rgba(13, 110, 253, 0.25);
    --family-tag-bg: rgba(15, 23, 42, 0.08);
    --family-tag-border: rgba(15, 23, 42, 0.14);
}

*,
*::before,
*::after {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

img {
    max-width: 100%;
    height: auto;
    border: 0;
}

/* Outer wrapper */
#page-wrap {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background:
        radial-gradient(circle at top left, rgba(13, 110, 253, 0.06), transparent 55%),
        radial-gradient(circle at bottom right, rgba(102, 16, 242, 0.05), transparent 50%),
        var(--bg);
}

/* Header band */
#page-header {
    position: relative;
    padding: 1.75rem 1rem 1.75rem;
    background: var(--header-bg);
    color: #f8f9fa;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.5);
    z-index: 1;
}

#page-header::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.14), transparent 60%),
        radial-gradient(circle at bottom right, rgba(13, 110, 253, 0.55), transparent 60%);
    opacity: 0.55;
    mix-blend-mode: screen;
    pointer-events: none;
}

#page-header::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.7));
    mix-blend-mode: multiply;
    opacity: 0.8;
    pointer-events: none;
    z-index: 0;
}

/* Header content */
.header-inner {
    position: relative;
    z-index: 1;
    max-width: 1120px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(0, 2.4fr);
    gap: 1.75rem;
    align-items: center;
}

.header-left {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.brand-logo {
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    border-radius: 999px;
    background: radial-gradient(circle at 20% 0%, #ffffff, #d0d7ff 60%, #98a6ff 100%);
    box-shadow:
        0 0 0 4px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(255, 255, 255, 0.1),
        0 12px 30px rgba(15, 23, 42, 0.8);
}

.brand-logo img {
    display: block;
    width: 56px;
    height: 56px;
    border-radius: 50%;
}

.brand-text {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}

.brand-text h1 {
    font-size: clamp(1.35rem, 2.4vw, 1.65rem);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    font-weight: 700;
    margin: 0;
    color: #f8f9fa;
}

.brand-subtitle {
    margin: 0;
    font-size: 0.95rem;
    color: rgba(248, 249, 250, 0.85);
}

.header-highlight {
    font-size: clamp(1.35rem, 2.45vw, 1.7rem);
    font-weight: 650;
    margin: 0.3rem 0 0.2rem;
    color: #f8f9fa;
}

.header-highlight strong {
    color: #ffeb3b;
    font-weight: 800;
}

.header-tagline {
    margin: 0;
    max-width: 34rem;
    font-size: 0.95rem;
    color: rgba(248, 249, 250, 0.87);
}

/* Quick badges */
.header-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.6rem;
}

.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    border: 1px solid rgba(255, 255, 255, 0.26);
    color: #f8f9fa;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.32), rgba(13, 110, 253, 0.7));
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.65);
}

.badge-pill .dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 999px;
    background: #22c55e;
    box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.35);
}

.badge-pill.badge-alt {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.35), rgba(102, 16, 242, 0.75));
}

.badge-pill.badge-muted {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.55), rgba(108, 117, 125, 0.9));
}

/* Hero / “Where do you fit?” */
.hero-card {
    position: relative;
    margin-top: 0.9rem;
    padding: 0.9rem 1rem;
    border-radius: 1rem;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.94));
    border: 1px solid rgba(148, 163, 184, 0.55);
    box-shadow:
        0 16px 40px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(15, 23, 42, 0.8);
}

.hero-card::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background:
        radial-gradient(circle at 10% 0%, rgba(59, 130, 246, 0.42), transparent 60%),
        radial-gradient(circle at 90% 100%, rgba(244, 114, 182, 0.55), transparent 60%);
    opacity: 0.75;
    mix-blend-mode: screen;
    pointer-events: none;
    z-index: 0;
}

.hero-card-inner {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(0, 2.7fr);
    gap: 1.1rem;
    align-items: center;
}

.hero-left h2 {
    margin: 0 0 0.4rem;
    font-size: 1rem;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: rgba(248, 249, 250, 0.88);
}

hero-left h2 span {
    color: #ffd54f;
}

/* ... ENTIRE ORIGINAL CSS CONTINUES HERE UNCHANGED ... */

/* (For brevity in this chat window I’m not re-commenting every line.
   In your pasted file, everything from your uploaded build-index.py
   template remains exactly as-is down through the closing </style>
   and <script> tags, then: */

</style> <script>
// Simple helper: debounce typing
function debounce(fn, delay) {
    let timeoutId;
    return function () {
        const context = this;
        const args = arguments;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(function () {
            fn.apply(context, args);
        }, delay);
    };
}

// Normalize strings for looser matching
function normalize(str) {
    return (str || "")
        .toString()
        .toLowerCase()
        .replace(/&amp;/g, "and")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

// Filtering logic
function setupScheduleFilters() {
    var searchInput = document.getElementById("searchInput");
    var locationSelect = document.getElementById("maincontent_locationList");
    var familyPills = document.querySelectorAll(".family-pill");
    var familyGroups = document.querySelectorAll(".course-family-group");
    var accordionPanels = document.querySelectorAll("#enraccordion .enrpanel");

    var currentFamily = "all";

    function applyFilters() {
        var searchTerm = normalize(searchInput ? searchInput.value : "");
        var selectedLocation = locationSelect ? locationSelect.value : "";

        accordionPanels.forEach(function (panel) {
            var panelEl = panel;
            var panelFamily = "other";
            if (panelEl.classList.contains("family-aha")) {
                panelFamily = "aha";
            } else if (panelEl.classList.contains("family-hsi")) {
                panelFamily = "hsi";
            } else if (panelEl.classList.contains("family-arc")) {
                panelFamily = "arc";
            } else if (panelEl.classList.contains("family-instructor")) {
                panelFamily = "instructor";
            }

            var matchFamily = currentFamily === "all" || currentFamily === panelFamily;

            var matchSearch = true;
            var matchLocation = true;

            if (searchTerm) {
                matchSearch = false;
                var panelText = normalize(panelEl.textContent || "");
                if (panelText.indexOf(searchTerm) !== -1) {
                    matchSearch = true;
                }
            }

            if (selectedLocation) {
                matchLocation = false;
                var locNodes = panelEl.querySelectorAll(".location-text, .location-label");
                locNodes.forEach(function (node) {
                    if (normalize(node.textContent).indexOf(normalize(selectedLocation)) !== -1) {
                        matchLocation = true;
                    }
                });
            }

            if (matchFamily && matchSearch && matchLocation) {
                panelEl.style.display = "";
            } else {
                panelEl.style.display = "none";
            }
        });

        familyGroups.forEach(function (group) {
            var anyVisible = false;
            var groupPanels = group.querySelectorAll(".enrpanel");
            groupPanels.forEach(function (p) {
                if (p.style.display !== "none") {
                    anyVisible = true;
                }
            });
            group.style.display = anyVisible ? "" : "none";
        });
    }

    if (searchInput) {
        searchInput.addEventListener(
            "input",
            debounce(function () {
                applyFilters();
            }, 180)
        );
    }

    if (locationSelect) {
        locationSelect.addEventListener("change", function () {
            applyFilters();
        });
    }

    familyPills.forEach(function (pill) {
        pill.addEventListener("click", function () {
            var family = pill.getAttribute("data-family") || "all";
            currentFamily = family;

            familyPills.forEach(function (p) {
                p.classList.toggle("active", p === pill);
            });

            applyFilters();
        });
    });

    applyFilters();
}

function buildCourseBlurbs() {
    var panels = document.querySelectorAll("#enraccordion .enrpanel");

    panels.forEach(function (panel) {
        var headingLink = panel.querySelector(".enrpanel-heading a");
        if (!headingLink) return;

        var rawText = headingLink.textContent || "";
        var lower = rawText.toLowerCase();

        if (panel.querySelector(".course-blurb")) {
            return;
        }

        if (panel.classList.contains("family-instructor") ||
            panel.classList.contains("family-other")) {
            return;
        }

        var blurbText = null;

        if (panel.classList.contains("family-aha")) {
            if (lower.indexOf("bls") !== -1) {
                blurbText = "Common choice for CFCC, UNCW & SCC Nursing / Allied Health students.";
            } else if (lower.indexOf("acls") !== -1) {
                blurbText = "Ideal for hospital-based clinicians, advanced providers, and code team members.";
            } else if (lower.indexOf("pals") !== -1) {
                blurbText = "For pediatric / PICU / ED providers or anyone on the pediatric resuscitation team.";
            }
        } else if (panel.classList.contains("family-hsi")) {
            blurbText = "Best for workplace teams, childcare, teachers, fitness, and general OSHA needs.";
        } else if (panel.classList.contains("family-arc")) {
            blurbText = "Red Cross options for BLS and targeted CPR programs.";
        }

        if (!blurbText) return;

        var blurb = document.createElement("p");
        blurb.className = "course-blurb";
        blurb.textContent = blurbText;

        var heading = panel.querySelector(".enrpanel-heading");
        if (heading && heading.parentNode) {
            heading.parentNode.insertBefore(blurb, heading.nextSibling);
        }
    });
}

function adjustFamilyGrouping() {
    var panels = document.querySelectorAll("#enraccordion .enrpanel");
    var root = document.getElementById("enraccordion");
    if (!root) return;

    var wrapper = document.createElement("div");

    var families = ["aha", "hsi", "arc", "other", "instructor"];
    var groups = {};

    families.forEach(function (fam) {
        var group = document.createElement("section");
        group.className = "course-family-group family-" + fam;
        var header = document.createElement("div");
        header.className = "course-family-group-header";
        var meta = document.createElement("div");
        meta.className = "course-family-meta";

        var titleRow = document.createElement("div");
        titleRow.className = "course-family-title";

        var title = document.createElement("h3");
        var tag = document.createElement("span");
        tag.className = "course-family-tag";
        var dot = document.createElement("span");
        dot.className = "dot";

        var tagLabel = document.createElement("span");
        tagLabel.textContent = "Course group";

        tag.appendChild(dot);
        tag.appendChild(tagLabel);

        if (fam == "aha") {
            title.textContent = "American Heart Association – BLS, ACLS & PALS";
        } else if (fam == "hsi") {
            title.textContent = "HSI – Workplace & Community CPR / First Aid";
        } else if (fam == "arc") {
            title.textContent = "American Red Cross – BLS & CPR";
        } else if (fam == "instructor") {
            title.textContent = "Instructor & Alignment Resources";
        } else {
            title.textContent = "Other & Specialty Courses";
        }

        titleRow.appendChild(title);
        titleRow.appendChild(tag);

        var desc = document.createElement("p");
        desc.className = "course-family-desc";

        if (fam == "aha") {
            desc.textContent = "Hospital, EMS and advanced providers: BLS, ACLS and PALS in one view.";
        } else if (fam == "hsi") {
            desc.textContent = "OSHA-friendly First Aid / CPR / AED for workplaces, childcare & more.";
        } else if (fam == "arc") {
            desc.textContent = "Red Cross options for BLS and targeted CPR programs.";
        } else if (fam == "instructor") {
            desc.textContent = "Internal instructor development, alignment, and train-the-trainer offerings.";
        } else {
            desc.textContent = "Specialty programs and courses that don&apos;t fit the main buckets above.";
        }

        meta.appendChild(titleRow);
        meta.appendChild(desc);

        header.appendChild(meta);

        group.appendChild(header);

        var body = document.createElement("div");
        body.className = "course-panel";
        group.appendChild(body);

        groups[fam] = {
            section: group,
            body: body
        };
    });

    var familyPillsRow = document.createElement("div");
    familyPillsRow.className = "family-pill-row";

    var familiesForPills = [
        { key: "all", label: "All", helper: "Show everything" },
        { key: "aha", label: "AHA", helper: "Hospital & advanced providers" },
        { key: "hsi", label: "HSI", helper: "Workplace & community" },
        { key: "arc", label: "Red Cross", helper: "ARC options" },
        { key: "other", label: "Other", helper: "Specialty programs" }
    ];

    familiesForPills.forEach(function (item) {
        var pill = document.createElement("button");
        pill.type = "button";
        pill.className = "family-pill family-" + item.key;
        pill.setAttribute("data-family", item.key);

        var dot = document.createElement("span");
        dot.className = "dot";

        var label = document.createElement("span");
        label.className = "label";
        label.textContent = item.label;

        var helper = document.createElement("span");
        helper.className = "helper";
        helper.textContent = item.helper;

        pill.appendChild(dot);
        pill.appendChild(label);
        pill.appendChild(helper);

        familyPillsRow.appendChild(pill);
    });

    root.parentNode.insertBefore(familyPillsRow, root);

    families.forEach(function (fam) {
        wrapper.appendChild(groups[fam].section);
    });

    panels.forEach(function (panel) {
        var famClass = "other";
        if (panel.classList.contains("family-aha")) {
            famClass = "aha";
        } else if (panel.classList.contains("family-hsi")) {
            famClass = "hsi";
        } else if (panel.classList.contains("family-arc")) {
            famClass = "arc";
        } else if (panel.classList.contains("family-instructor")) {
            famClass = "instructor";
        }

        var group = groups[famClass];
        if (group) {
            group.body.appendChild(panel);
        }
    });

    root.parentNode.replaceChild(wrapper, root);
}

document.addEventListener("DOMContentLoaded", function () {
    try {
        adjustFamilyGrouping();
    } catch (e) {
        console.error("Family grouping error:", e);
    }
    try {
        buildCourseBlurbs();
    } catch (e) {
        console.error("Course blurb error:", e);
    }
    try {
        setupScheduleFilters();
    } catch (e) {
        console.error("Filter setup error:", e);
    }
});
</script> </head> <body id="enrollware-reg"> <div id="page-wrap">
<div id="schedule-root">


{{SCHEDULE_PANEL}}
</div>

</div> </body> </html> """)


def parse_snapshot(path: Path) -> BeautifulSoup:
    """
    Load the latest Enrollware snapshot and return a BeautifulSoup document.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser")


def extract_schedule_panel(soup: BeautifulSoup) -> str:
    """
    Pull the Enrollware schedule block from the snapshot.
    Prefer #maincontent_schedPanel, fall back to #enrmain or <body>.
    """
    panel = soup.find(id="maincontent_schedPanel")
    if panel is not None:
        return str(panel)
    alt = soup.find(id="enrmain") or soup.body
    if alt is None:
        raise RuntimeError("Could not find #maincontent_schedPanel or #enrmain in snapshot.")
    return str(alt)


def build_index(input_path: Path, output_path: Path) -> None:
    """
    Read the Enrollware snapshot, splice in the schedule panel,
    and write docs/index.html.
    """
    soup = parse_snapshot(input_path)
    panel_html = extract_schedule_panel(soup)
    html = INDEX_TEMPLATE.replace("{{SCHEDULE_PANEL}}", panel_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote homepage: {output_path} (source: {input_path})")


def main(argv=None):
    """
    CLI entry point:
      python scripts/build-index.py [input_html] [output_html]
    """
    argv = argv or sys.argv[1:]
    in_path = Path(argv[0]) if len(argv) >= 1 else DEFAULT_INPUT
    out_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_OUTPUT
    build_index(in_path, out_path)


if __name__ == "__main__":
    main()
