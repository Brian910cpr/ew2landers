#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build-index.py

Generate a static docs/index.html for 910CPR using the latest
Enrollware schedule snapshot.

Defaults:
  input:  docs/data/enrollware-schedule.html
  output: docs/index.html
"""

import sys
from pathlib import Path
from textwrap import dedent

from bs4 import BeautifulSoup

DEFAULT_INPUT = Path("docs/data/enrollware-schedule.html")
DEFAULT_OUTPUT = Path("docs/index.html")

INDEX_TEMPLATE = dedent("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>910CPR | CPR, BLS, ACLS &amp; PALS Classes in Wilmington &amp; Burgaw, NC</title>
<meta name="description" content="Book CPR, BLS, ACLS, PALS and First Aid classes in Wilmington, Burgaw, and surrounding NC areas. Small classes, fast cards, late options, and on-site training for offices.">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://www.910cpr.com/">

<style>
:root {
    --bg: #f5f7fb;
    --text: #212529;
    --muted: #6c757d;
    --card-bg: #ffffff;
    --border: #dee2e6;
}

/* ===== Base layout ===== */

* {
    box-sizing: border-box;
}

body {
    margin:0;
    padding:0;
    font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;
    background:var(--bg);
    color:var(--text);
}

#page-wrap {
    max-width:1200px;
    margin:auto;
    padding:16px;
}

/* Wrap the whole Enrollware block in a soft card */

#schedule-root > #maincontent_schedPanel {
    background:var(--card-bg);
    border-radius:10px;
    border:1px solid var(--border);
    padding:16px;
    box-shadow:0 3px 8px rgba(0,0,0,0.05);
}

/* ===== Filter / search controls ===== */

#searchPnl,
#maincontent_locationPnl,
#maincontent_coursePanel {
    margin-bottom:8px;
}

#searchPnl {
    margin-bottom:10px;
}

#searchInput,
#maincontent_locationList,
#maincontent_courseList {
    width:100%;
    max-width:320px;
    padding:6px 10px;
    font-size:0.9rem;
    border-radius:999px;
    border:1px solid var(--border);
}

#maincontent_locationList,
#maincontent_courseList {
    border-radius:8px;
}

#maincontent_loclbl,
#maincontent_courseLabel {
    display:block;
    font-size:0.85rem;
    color:var(--muted);
    margin:4px 0;
}

/* Hide course filter completely */
#maincontent_coursePanel {
    display:none !important;
}

@media (min-width: 768px) {
    #filters-row {
        display:flex;
        flex-wrap:wrap;
        gap:12px 24px;
        align-items:flex-end;
        margin-bottom:10px;
    }
    #filters-row > div {
        flex:0 0 auto;
    }
}

/* ===== Family headers (the big category pills) ===== */

#enraccordion .enrpanel.family-header .enrpanel-heading {
    margin:26px auto 0 auto;
    max-width:720px;
    border-radius:999px 999px 0 0;
    overflow:hidden;
    border:1px solid var(--border);
}

/* Keep family header text white on colored backgrounds */
#enraccordion .enrpanel.family-header .enrpanel-heading a.enrtrigger {
    display:block;
    text-decoration:none;
    cursor:default;
    color:#ffffff;
}

/* Family header body never opens */
#enraccordion .enrpanel.family-header .enrpanel-body {
    display:none !important;
}

/* ===== Course type panels under each family ===== */

.course-family-group {
    margin-top:0;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
    gap:12px;
    padding:16px 12px 18px;
    border-radius:0 0 40px 40px;
}

/* Colors that match each family pill */

.course-family-group.family-bls,
#enraccordion .enrpanel.family-header.family-bls .enrpanel-heading {
    background:#0b64a0;
}

.course-family-group.family-acls,
#enraccordion .enrpanel.family-header.family-acls .enrpanel-heading {
    background:#b5212f;
}

.course-family-group.family-pals,
#enraccordion .enrpanel.family-header.family-pals .enrpanel-heading {
    background:#6e3b9f;
}

.course-family-group.family-asls,
#enraccordion .enrpanel.family-header.family-asls .enrpanel-heading {
    background:#4b4b4b;
}

.course-family-group.family-cprfa,
#enraccordion .enrpanel.family-header.family-cprfa .enrpanel-heading {
    background:#6b6b6b;
}

.course-family-group.family-cpron,
#enraccordion .enrpanel.family-header.family-cpron .enrpanel-heading {
    background:#777777;
}

.course-family-group.family-instructor,
#enraccordion .enrpanel.family-header.family-instructor .enrpanel-heading {
    background:#555555;
}

.course-family-group.family-other,
#enraccordion .enrpanel.family-header.family-other .enrpanel-heading {
    background:#ffffff;
}

/* Grid cell shell */
.course-panel {
    border-radius:10px;
}

/* Inner pill that actually carries border and white background */
.course-inner {
    border-radius:10px;
    border:1px solid var(--border);
    background:#ffffff;
    overflow:hidden;
    height:100%;
}

/* Course heading pill */

.course-panel .enrpanel-heading {
    padding:0;
    background:transparent;
}

.course-panel .enrpanel-heading a.enrtrigger {
    display:block;
    padding:10px 12px;
    border-radius:0;
    background:transparent;
    text-decoration:none;
    font-weight:600;
    color:var(--text);
}

/* Under-title blurbs for SEO / guidance */

.course-blurb {
    font-size:0.85rem;
    font-style:italic;
    color:#555;
    padding:0 12px 6px 12px;
}

/* Description block */

.course-panel .enrpanel-body {
    display:none;
    padding:10px 16px 14px 24px;
    background:transparent;
}

/* ===== Date/Time/Location as “session buttons” ===== */

.course-panel .enrclass-list {
    list-style:none;
    margin:14px 0 0 0;
    padding:0;
}

.course-panel .enrclass-list li + li {
    margin-top:8px;
}

.course-panel .enrclass-list li a.session-link {
    display:block;
    padding:10px 12px;
    border-radius:8px;
    border:1px solid var(--border);
    background:#f8f9fa;
    text-decoration:none;
    font-size:0.95rem;
    font-weight:500;
}

.course-panel .enrclass-list li a.session-link span {
    display:block;
    margin-top:3px;
    font-size:0.85rem;
    color:var(--muted);
}

.course-panel .enrclass-list li a.session-link:hover {
    border-color:#0d6efd;
    box-shadow:0 0 0 1px rgba(13,110,253,0.2);
}

/* More-times pagination button */

.session-more-button {
    display:inline-block;
    margin:10px 0 4px 12px;
    padding:6px 14px;
    border-radius:999px;
    border:1px solid var(--border);
    background:#f5f7fb;
    font-size:0.85rem;
    font-weight:600;
    cursor:pointer;
    white-space:nowrap;
}

.session-more-button:hover {
    background:#e3e8f5;
}

/* ===== Responsive images inside schedule ===== */

#schedule-root img {
    max-width:100%;
    height:auto;
}
</style>

<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://code.jquery.com/jquery-migrate-3.5.2.min.js"></script>

<script>
jQuery(function($){

    var $accordion = $('#enraccordion');
    if (!$accordion.length) return;

    /* === Wrap filters in a flex row container on larger screens === */
    (function setupFiltersRow(){
        var $search = $('#searchPnl');
        var $loc = $('#maincontent_locationPnl');

        if ($search.length || $loc.length) {
            var $wrap = $('<div id="filters-row"></div>');
            var $first = $search[0] ? $search : $loc;
            $wrap.insertBefore($first.first());
            if ($search.length) $search.appendTo($wrap);
            if ($loc.length) $loc.appendTo($wrap);
        }
    })();

    // 1) Identify "family header" panels by the “Select a Program Below” text
    var familyPanels = [];
    $accordion.find('.enrpanel').each(function(){
        var $panel = $(this);
        var hasSelect = $panel.find('.enrclass-list a').filter(function(){
            return $(this).text().indexOf('Select a Program Below') !== -1;
        }).length > 0;

        if (hasSelect) {
            $panel.addClass('family-header');
            $panel.find('.enrpanel-body').hide();
            $panel.find('a.enrtrigger').off('click').css('cursor','default');
            familyPanels.push($panel);
        }
    });

    // 2) Group the course panels that come after each family header,
    //    and tag course panels by family type.
    familyPanels.forEach(function($family){
        var headerText = ($family.find('.enrpanel-heading a.enrtrigger').text() || '').toLowerCase();
        var familyType = '';

        if (headerText.indexOf('bls course') !== -1) {
            familyType = 'bls';
        } else if (headerText.indexOf('acls course') !== -1) {
            familyType = 'acls';
        } else if (headerText.indexOf('pals course') !== -1) {
            familyType = 'pals';
        } else if (headerText.indexOf('asls course') !== -1) {
            familyType = 'asls';
        } else if (headerText.indexOf('cpr / aed & first aid') !== -1 ||
                   headerText.indexOf('cpr / aed &amp; first aid') !== -1) {
            familyType = 'cprfa';
        } else if (headerText.indexOf('cpr / aed only') !== -1 ||
                   headerText.indexOf('cpr/aed only') !== -1) {
            familyType = 'cpron';
        } else if (headerText.indexOf('instructor') !== -1) {
            familyType = 'instructor';
        } else if (headerText.indexOf('other programs') !== -1) {
            familyType = 'other';
        }

        var $group = $('<div class="course-family-group"></div>');
        if (familyType) {
            $group.addClass('family-' + familyType);
            $family.addClass('family-' + familyType);
        }
        $group.insertAfter($family);

        var $next = $family.next();
        while ($next.length && !$next.hasClass('family-header')) {
            var $move = $next;
            $next = $next.next();
            $move.appendTo($group).addClass('course-panel');
            if (familyType) {
                $move.addClass('family-' + familyType);
            }
        }
    });

    // Any panels not tagged as family or moved yet are still course panels
    $accordion.find('.enrpanel').not('.family-header, .course-panel').addClass('course-panel');

    // 3) Add under-title blurbs for key course types,
    //    but skip Instructor, CPR/AED Only, and Other families.
    (function addCourseBlurbs(){
        $('.course-panel .enrpanel-heading a.enrtrigger').each(function(){
            var $a = $(this);
            var $panel = $a.closest('.course-panel');
            var headingText = ($a.text() || '').trim();
            var lower = headingText.toLowerCase();

            if ($panel.hasClass('family-instructor') ||
                $panel.hasClass('family-cpron') ||
                $panel.hasClass('family-other')) {
                return;
            }

            if ($a.closest('.enrpanel-heading').next('.course-blurb').length) {
                return;
            }

            var blurbText = null;

            if (lower.indexOf('aha') !== -1 && lower.indexOf('bls') !== -1) {
                blurbText = 'Common choice for CFCC, UNCW & SCC Nursing / Allied Health students.';
            } else if (lower.indexOf('aha') !== -1 && lower.indexOf('acls') !== -1) {
                blurbText = 'Ideal for hospital-based clinicians, advanced providers, and code team members.';
            } else if (lower.indexOf('aha') !== -1 && lower.indexOf('pals') !== -1) {
                blurbText = 'Commonly needed for pediatric ER/ICU nurses, paramedics, and providers who care for children.';
            } else if (lower.indexOf('heartsaver') !== -1) {
                blurbText = 'Popular with childcare providers, foster parents, coaches, and workplace responders.';
            } else if (lower.indexOf('hsi') !== -1 && lower.indexOf('first aid') !== -1) {
                blurbText = 'Great option for OSHA-focused workplace safety and industrial teams.';
            }

            if (blurbText) {
                var $blurb = $('<div class="course-blurb"></div>').text(blurbText);
                $a.closest('.enrpanel-heading').after($blurb);
            }
        });
    })();

    // 4) Wrap course-panel contents in .course-inner so the pill bg doesn't bleed
    $('.course-panel').each(function(){
        var $panel = $(this);
        if (!$panel.children('.course-inner').length) {
            $panel.wrapInner('<div class="course-inner"></div>');
        }
    });

    // 5) Collapse all course bodies by default
    $('.course-panel .enrpanel-body').hide();

    // 6) Accordion behavior: only one course panel open at a time,
    //    and when you open one, scroll so the title stays in view.
    $('.course-panel a.enrtrigger').on('click', function(){
        var $heading = $(this).closest('.enrpanel-heading');
        var $body = $heading.nextAll('.enrpanel-body').first();

        if ($body.is(':visible')) {
            $body.slideUp();
        } else {
            $('.course-panel .enrpanel-body:visible').slideUp();
            $body.slideDown(200, function(){
                var offset = $heading.offset().top - 80; // leave a little margin
                $('html, body').animate({scrollTop: offset}, 200);
            });
        }
        return false;
    });

    /* === Filters: search + location only === */
    function normalize(str) {
        return (str || '').toLowerCase().replace(/\\s+/g, ' ').trim();
    }

    function applyFilters() {
        var term = normalize($('#searchInput').val());

        var locText = '';
        var $locSel = $('#maincontent_locationList');
        if ($locSel.length) {
            locText = $locSel.find('option:selected').text();
        }
        var locFilter = normalize(locText);
        if (locFilter === 'all locations') locFilter = '';

        $('.course-panel').each(function(){
            var $panel = $(this);

            var headingText = ($panel.find('.enrpanel-heading a.enrtrigger').text() || '');
            var valueAttr = ($panel.attr('value') || '');
            var headingNorm = normalize(headingText);
            var valueNorm = normalize(valueAttr);
            var searchable = headingNorm + ' ' + valueNorm;

            var matchSearch = !term || searchable.indexOf(term) !== -1;

            var matchLoc = true;
            if (locFilter) {
                matchLoc = false;
                $panel.find('.enrclass-list li').each(function(){
                    var t = normalize($(this).text());
                    if (t.indexOf(locFilter) !== -1) {
                        matchLoc = true;
                        return false;
                    }
                });
            }

            if (matchSearch && matchLoc) {
                $panel.show();
            } else {
                $panel.hide();
            }
        });
    }

    $('#searchInput').on('input', applyFilters);
    $('#maincontent_locationList').on('change', applyFilters);

    // 7) Mark each date/time/location link as a "session button" for styling
    $('.course-panel .enrclass-list li a').addClass('session-link');

    // 8) Paginate long session lists: show first 10, "More times…" button for the rest
    (function paginateSessions(){
        var PAGE = 10;
        $('.course-panel').each(function(){
            var $panel = $(this);

            // Clean up any existing buttons if this ever runs twice
            $panel.find('.session-more-button').remove();

            var $lists = $panel.find('.enrclass-list');
            var $items = $lists.find('li');
            if ($items.length <= PAGE) return;

            $items.show();
            $items.slice(PAGE).hide();
            var shown = PAGE;

            var $btn = $('<button type="button" class="session-more-button">More times…</button>');
            $btn.on('click', function(){
                shown += PAGE;
                $items.slice(0, shown).show();
                if (shown >= $items.length) {
                    $btn.remove();
                }
            });

            $lists.last().after($btn);
        });
    })();

    // 9) Final safety: make all images responsive
    $('#schedule-root img').css({maxWidth:'100%', height:'auto'});
});
</script>
</head>

<body id="enrollware-reg">
<div id="page-wrap">

    <div id="schedule-root">
{{SCHEDULE_PANEL}}
    </div>

</div>
</body>
</html>
""")

def parse_snapshot(path: Path) -> BeautifulSoup:
    """Read and parse the Enrollware snapshot into BeautifulSoup."""
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser")

def extract_schedule_panel(soup: BeautifulSoup) -> str:
    """Return the HTML for <div id="maincontent_schedPanel">...</div>."""
    panel = soup.find(id="maincontent_schedPanel")
    if panel is not None:
        return str(panel)
    alt = soup.find(id="enrmain") or soup.body
    if alt is None:
        raise RuntimeError("Could not find #maincontent_schedPanel or #enrmain in snapshot.")
    return str(alt)

def build_index(input_path: Path, output_path: Path) -> None:
    """Build index.html by injecting the schedule panel into the template."""
    soup = parse_snapshot(input_path)
    panel_html = extract_schedule_panel(soup)

    html = INDEX_TEMPLATE.replace("{{SCHEDULE_PANEL}}", panel_html)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote homepage: {output_path} (source: {input_path})")

def main(argv=None):
    argv = argv or sys.argv[1:]
    in_path = Path(argv[0]) if len(argv) >= 1 else DEFAULT_INPUT
    out_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_OUTPUT
    build_index(in_path, out_path)

if __name__ == "__main__":
    main()
