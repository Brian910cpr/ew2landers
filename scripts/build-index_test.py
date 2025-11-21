#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build-index.py

Rebuild docs/index.html for 910CPR using:
- Base HTML template (SEO, header, CSS, JS) from oldindex.html
- Fresh Enrollware schedule snapshot (docs/data/enrollware-schedule.html)

This script:
- Reads docs/data/enrollware-schedule.html
- Extracts #maincontent_schedPanel
- Strips Enrollware <script> tags and hidden inputs
- Injects the cleaned panel into <div id="schedule-root"> in the template
- Writes docs/index.html

You can keep editing the template HTML below, and the Python
will continue to swap in the live schedule each run.
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup

DEFAULT_SNAPSHOT = Path("docs/data/enrollware-schedule.html")
DEFAULT_OUTPUT = Path("docs/index.html")

# ---------------------------------------------------------------------
# HTML template: this is your oldindex.html with the schedule-root
# contents replaced by the placeholder {{SCHEDULE_PANEL}}.
# ---------------------------------------------------------------------
INDEX_TEMPLATE = '''<!DOCTYPE html>

<html lang="en">
<head>
<meta charset="utf-8"/>
<title>CPR, BLS, ACLS &amp; First Aid Classes in Wilmington &amp; Burgaw, NC | 910CPR Class Schedule</title>
<meta name="description" content="910CPR offers AHA and HSI CPR, BLS, ACLS, PALS, First Aid and more in Wilmington, Burgaw and surrounding SE North Carolina. Live and blended schedules for healthcare providers, workplaces, and the community."/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="canonical" href="https://www.910cpr.com/"/>

<!-- Basic 910CPR structured data (LocalBusiness + core Courses) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "LocalBusiness",
      "@id": "https://www.910cpr.com/#localbusiness",
      "name": "910CPR | Coastal CPR Training",
      "description": "AHA, HSI and Red Cross CPR, BLS, ACLS, PALS and First Aid classes in Wilmington and Burgaw, NC. Live and blended training for healthcare, workplaces, EMS and the community.",
      "url": "https://www.910cpr.com/",
      "telephone": "+1-910-395-5193",
      "image": "https://www.enrollware.com/sitefiles/coastalcprtraining/910CPR_wave.jpg",
      "priceRange": "$$",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "4018 Shipyard Blvd",
        "addressLocality": "Wilmington",
        "addressRegion": "NC",
        "postalCode": "28403",
        "addressCountry": "US"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 34.184,
        "longitude": -77.915
      },
      "areaServed": [
        "Wilmington NC",
        "Burgaw NC",
        "Jacksonville NC",
        "New Hanover County NC",
        "Pender County NC",
        "Brunswick County NC"
      ],
      "sameAs": [
        "https://coastalcprtraining.com/",
        "https://www.facebook.com/CoastalCPRTraining",
        "https://maps.app.goo.gl/",
        "tel:+19103955193"
      ]
    },
    {
      "@type": "Course",
      "@id": "https://www.910cpr.com/#course-bls",
      "name": "AHA BLS Provider – CPR for Healthcare Providers in Wilmington & Burgaw, NC",
      "description": "American Heart Association Basic Life Support (BLS) Provider course for nurses, physicians, EMTs, students and other healthcare providers. Meets CPR requirements for CFCC, UNCW and SCC nursing / allied health programs when they specify AHA BLS.",
      "provider": {
        "@id": "https://www.910cpr.com/#localbusiness"
      }
    },
    {
      "@type": "Course",
      "@id": "https://www.910cpr.com/#course-acls",
      "name": "AHA ACLS Provider – Advanced Cardiovascular Life Support in Wilmington & Burgaw, NC",
      "description": "American Heart Association ACLS for hospital and critical-care providers. Offered as both full initial courses and renewal options with HeartCode blended learning.",
      "provider": {
        "@id": "https://www.910cpr.com/#localbusiness"
      }
    },
    {
      "@type": "Course",
      "@id": "https://www.910cpr.com/#course-pals",
      "name": "AHA PALS Provider – Pediatric Advanced Life Support in Wilmington & Burgaw, NC",
      "description": "American Heart Association PALS for providers caring for infants and children in emergency, critical care or acute care settings.",
      "provider": {
        "@id": "https://www.910cpr.com/#localbusiness"
      }
    }
  ]
}
</script>

<style>
:root {
    --bg: #f5f7fb;
    --text: #212529;
    --muted: #6c757d;
    --card-bg: #ffffff;
    --border: #dee2e6;
    --accent: #0b64a0;
}

/* ===== Base layout ===== */

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    background: linear-gradient(to bottom, #ffffff 0%, #f0f6ff 40%, #e1ecff 100%);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* ===== Top nav (borrowed from coastalCPR) ===== */

.top-bar {
    background: #ffffff;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    position: sticky;
    top: 0;
    z-index: 100;
}

.top-bar-inner {
    max-width: 1100px;
    margin: 0 auto;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand-block {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-block img {
    height: 52px;
}

.brand-text {
    line-height: 1.1;
}

.brand-text .name {
    font-weight: 700;
    font-size: 1.1rem;
}

.brand-text .tagline {
    font-size: 0.8rem;
    color: var(--muted);
}

.nav-links {
    display: flex;
    gap: 14px;
    font-size: 0.9rem;
}

.nav-links a {
    text-decoration: none;
    color: var(--accent);
    padding: 6px 10px;
    border-radius: 999px;
    transition: background 0.15s ease, color 0.15s ease;
}

.nav-links a:hover {
    background: rgba(13, 110, 253, 0.06);
    color: #063b64;
}

/* ===== Hero ===== */

.hero {
    max-width: 1100px;
    margin: 22px auto 10px;
    padding: 0 16px;
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
    gap: 20px;
}

.hero-main h1 {
    font-size: 2rem;
    margin: 0 0 8px;
}

.hero-main p {
    margin: 4px 0;
    color: var(--muted);
    font-size: 0.95rem;
}

.hero-meta {
    margin-top: 10px;
    font-size: 0.9rem;
}

.hero-meta span {
    display: inline-block;
    margin-right: 12px;
    color: var(--muted);
}

.hero-meta b {
    color: #0b4f82;
}

.hero-side {
    background: linear-gradient(135deg, #0b64a0, #2274b6);
    color: #ffffff;
    border-radius: 18px;
    padding: 14px 18px;
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.25);
}

.hero-side h2 {
    font-size: 1.1rem;
    margin: 0 0 6px;
}

.hero-side p {
    margin: 4px 0;
    font-size: 0.9rem;
}

/* ===== Popular quick buttons ===== */

.popular-row {
    max-width: 1100px;
    margin: 10px auto 0;
    padding: 0 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.popular-pill {
    border-radius: 999px;
    padding: 8px 14px;
    font-size: 0.85rem;
    border: 1px solid rgba(13, 110, 253, 0.25);
    color: #0b4f82;
    background: rgba(13, 110, 253, 0.04);
    cursor: pointer;
}

/* ===== Search / filters row ===== */

.filters-wrapper {
    max-width: 1100px;
    margin: 14px auto 10px;
    padding: 0 16px;
}

#filters-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px 14px;
    align-items: center;
    justify-content: flex-start;
}

#searchPnl {
    flex: 1 1 230px;
}

.enrsearchbox input {
    width: 100%;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--border);
    font-size: 0.9rem;
}

#maincontent_locationPnl {
    flex: 0 0 210px;
}

#maincontent_locationList {
    width: 100%;
    padding: 6px 10px;
    font-size: 0.9rem;
    border-radius: 999px;
    border: 1px solid var(--border);
}

/* ===== Schedule wrapper ===== */

#schedule-section {
    max-width: 1100px;
    margin: 14px auto 40px;
    padding: 0 16px 40px;
}

#schedule-header {
    text-align: left;
    margin-bottom: 10px;
}

#schedule-header h2 {
    margin: 0 0 4px;
    font-size: 1.4rem;
}

#schedule-header p {
    margin: 2px 0;
    color: var(--muted);
    font-size: 0.9rem;
}

/* Base Enrollware accordion container styling */
#enraccordion {
    max-width: 900px;
    margin: 16px auto 0 auto;
}

#enraccordion .enrpanel {
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 10px;
    border: 1px solid rgba(13, 110, 253, 0.08);
    background: #ffffff;
}

/* Panel headings */
#enraccordion .enrpanel-heading {
    padding: 10px 14px;
    background: #ffffff;
}

/* Panel trigger link */
a.enrtrigger {
    cursor: pointer;
    text-decoration: none;
    display: block;
    color: var(--text);
    font-weight: 600;
}

/* Panel body */
#enraccordion .enrpanel-body {
    padding: 0;
}

/* Class list styling */
ul.enrclass-list {
    list-style: none;
    margin: 0;
    padding: 0;
}

ul.enrclass-list > li {
    border-top: 1px solid rgba(222, 226, 230, 0.7);
    padding: 10px 14px;
}

ul.enrclass-list > li:nth-child(odd) {
    background: #f9fbff;
}

/* Date/time row inside each li */
.enrclass-datetime {
    font-weight: 600;
}

/* Location and instructor line */
.enrclass-location,
.enrclass-instructor {
    font-size: 0.85rem;
    color: var(--muted);
}

/* Register button row */
.enrclass-register {
    margin-top: 6px;
}

.enrclass-register a {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.85rem;
    border: 1px solid var(--accent);
    color: var(--accent-dark);
    text-decoration: none;
    background: #ffffff;
}

/* "More times" button */
.more-times-btn {
    display: inline-block;
    margin-top: 8px;
    margin-left: 14px;
    margin-bottom: 10px;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 0.8rem;
    border: 1px dashed var(--accent);
    color: var(--accent-dark);
    background: rgba(13, 110, 253, 0.04);
    cursor: pointer;
}

/* Hide extra rows by default; JS will reveal them */
li.enrclass-hidden {
    display: none;
}

/* ===== Family headers (the big category pills) ===== */

#enraccordion .enrpanel.family-header .enrpanel-heading {
    margin: 26px auto 0 auto;
    max-width: 720px;
    border-radius: 999px 999px 0 0;
    overflow: hidden;
    border: 1px solid var(--border);
}

/* Keep family header text white on colored backgrounds */
#enraccordion .enrpanel.family-header .enrpanel-heading a.enrtrigger {
    display: block;
    text-decoration: none;
    cursor: pointer;
    color: #ffffff;
}

/* Family header body never opens */
#enraccordion .enrpanel.family-header .enrpanel-body {
    display: none !important;
}

/* Color sets per family type */
#enraccordion .enrpanel.family-bls .enrpanel-heading {
    background: linear-gradient(135deg, #0b64a0, #1182cf);
}

#enraccordion .enrpanel.family-acls .enrpanel-heading {
    background: linear-gradient(135deg, #b32025, #d63a3f);
}

#enraccordion .enrpanel.family-pals .enrpanel-heading {
    background: linear-gradient(135deg, #593b88, #7b54b2);
}

#enraccordion .enrpanel.family-asls .enrpanel-heading {
    background: linear-gradient(135deg, #363638, #505158);
}

#enraccordion .enrpanel.family-cprfa .enrpanel-heading {
    background: linear-gradient(135deg, #707070, #8e8e8e);
}

#enraccordion .enrpanel.family-cpron .enrpanel-heading {
    background: linear-gradient(135deg, #7a7a7a, #969696);
}

#enraccordion .enrpanel.family-instructor .enrpanel-heading {
    background: linear-gradient(135deg, #363638, #4a4a4f);
}

#enraccordion .enrpanel.family-other .enrpanel-heading {
    background: linear-gradient(135deg, #d1d1d1, #e0e0e0);
}

/* "Family" wrapper around each group of courses */
.family-block {
    border-radius: 22px;
    margin: 8px auto 24px auto;
    max-width: 900px;
    overflow: hidden;
    border: 1px solid rgba(13, 110, 253, 0.12);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
    padding-bottom: 8px;
}

/* Inner course panels inside a family container */
.family-block .enrpanel {
    border-radius: 0;
    border-left: none;
    border-right: none;
    box-shadow: none;
}

/* When a panel is open, give subtle accent shadow */
.family-block .enrpanel.open {
    box-shadow: 0 0 0 1px rgba(13, 110, 253, 0.08), 0 10px 25px rgba(15, 23, 42, 0.15);
}

/* Extra blurb line below certain course titles */
.course-blurb {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 2px;
}

/* ===== Responsive tweaks ===== */

@media (max-width: 900px) {
    .hero {
        grid-template-columns: minmax(0, 1fr);
    }
    .hero-side {
        order: -1;
    }
    #enraccordion {
        max-width: 100%;
    }
    .family-block {
        margin: 12px auto 20px;
        border-radius: 16px;
    }
}

@media (max-width: 640px) {
    .top-bar-inner {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
    }

    .nav-links {
        flex-wrap: wrap;
        gap: 6px;
    }

    #filters-row {
        flex-direction: column;
        align-items: stretch;
    }

    #filters-row > div {
        width: 100%;
    }
}
</style>
</head>

<body>

<div class="top-bar">
  <div class="top-bar-inner">
    <div class="brand-block">
      <img src="https://www.enrollware.com/sitefiles/coastalcprtraining/910CPR_wave.jpg" alt="910CPR logo"/>
      <div class="brand-text">
        <div class="name">910CPR / Coastal CPR Training</div>
        <div class="tagline">CPR, BLS, ACLS, PALS &amp; First Aid in Wilmington &amp; Burgaw, NC</div>
      </div>
    </div>
    <nav class="nav-links">
      <a href="http://coastalcprtraining.com/">Home</a>
      <a href="http://coastalcprtraining.com/about">About</a>
      <a href="http://coastalcprtraining.com/classes">Classes</a>
      <a href="http://coastalcprtraining.com/onsite">On-Site Training</a>
      <a href="http://coastalcprtraining.com/2025-price-list">2025 Price List</a>
    </nav>
  </div>
</div>

<section class="hero">
  <div class="hero-main">
    <h1>910CPR Class Schedule – Wilmington &amp; Burgaw, NC</h1>
    <p>Find AHA BLS, ACLS, PALS, First Aid and more. Live classroom and blended online options with same-day or fast card delivery.</p>
    <div class="hero-meta">
      <span><b>Locations:</b> Wilmington &amp; Burgaw</span>
      <span><b>Audience:</b> Healthcare, workplace, students &amp; community</span>
      <span><b>Brands:</b> AHA, HSI, Red Cross</span>
    </div>
    <p style="margin-top:10px; font-size:0.9rem; color:#555;">
      Many CFCC, UNCW and SCC nursing / allied-health programs require <b>AHA BLS</b>. If you are unsure which CPR you need, we can help you choose.
    </p>
  </div>
  <aside class="hero-side">
    <h2>Questions about the right class?</h2>
    <p>Text or call <b>(910) 395-5193</b> for help matching your school or employer requirements.</p>
    <p style="margin-top:6px; font-size:0.85rem;">
      We do not cancel low-enrollment classes, and we keep late-evening options on the calendar whenever possible.
    </p>
  </aside>
</section>

<div class="popular-row">
  <div class="popular-pill">BLS for Healthcare Providers (AHA)</div>
  <div class="popular-pill">HeartCode BLS (Online + Skills)</div>
  <div class="popular-pill">ACLS Renewal</div>
  <div class="popular-pill">PALS Renewal</div>
  <div class="popular-pill">HSI First Aid / CPR / AED</div>
</div>

<section id="schedule-section">
  <div id="schedule-header">
    <h2>Live &amp; Blended CPR Class Calendar</h2>
    <p>Use the search box or location dropdown to narrow results. Click a course name to see dates and register.</p>
  </div>

  <!-- The Enrollware panel will be injected here -->
  <div id="schedule-root">
    {{SCHEDULE_PANEL}}
  </div>
</section>

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
            var $first = $search.length ? $search : $loc;
            $wrap.insertBefore($first.first());
            if ($search.length) $search.appendTo($wrap);
            if ($loc.length) $loc.appendTo($wrap);
        }
    })();

    /* === Convert certain panels into "family headers" and group related courses === */
    var familyBlocks = {};

    function normalizeText(txt) {
        return $.trim(txt || '').toLowerCase();
    }

    $accordion.find('.enrpanel').each(function(){
        var $panel = $(this);
        var $heading = $panel.find('.enrpanel-heading').first();
        var headerText = normalizeText($heading.text());

        // Identify "family" headers by keywords
        var familyType = null;
        if (headerText.indexOf('healthcare provider: bls course') !== -1) {
            familyType = 'bls';
        } else if (headerText.indexOf('healthcare provider: acls course') !== -1) {
            familyType = 'acls';
        } else if (headerText.indexOf('healthcare provider: pals course') !== -1) {
            familyType = 'pals';
        } else if (headerText.indexOf('healthcare provider: asls course') !== -1) {
            familyType = 'asls';
        } else if (headerText.indexOf('cpr / aed & first aid') !== -1 ||
                   headerText.indexOf('cpr / aed &amp; first aid') !== -1) {
            familyType = 'cprfa';
        } else if (headerText.indexOf('cpr / aed only') !== -1 ||
                   headerText.indexOf('cpr/aed only') !== -1) {
            familyType = 'cpron';
        } else if (headerText.indexOf('instructor programs') !== -1 ||
                   headerText.indexOf('instructor program') !== -1) {
            familyType = 'instructor';
        } else if (headerText.indexOf('other programs') !== -1) {
            familyType = 'other';
        }

        if (familyType) {
            // This is a family header panel
            $panel.addClass('family-header family-' + familyType);

            // Create or get a block wrapper for this family
            if (!familyBlocks[familyType]) {
                var $block = $('<div class="family-block family-' + familyType + '"></div>');
                familyBlocks[familyType] = $block;
                $accordion.append($block);
            }

            familyBlocks[familyType].append($panel);
        }
    });

    // Move all "child" course panels directly after their family header blocks
    $accordion.find('.enrpanel').each(function(){
        var $panel = $(this);
        if ($panel.hasClass('family-header')) return;

        var $prevHeader = $panel.prevAll('.family-header').first();
        if ($prevHeader.length) {
            var classes = ($prevHeader.attr('class') || '').split(/\\s+/);
            var famClass = null;
            $.each(classes, function(i, cls){
                if (cls.indexOf('family-') === 0 && cls !== 'family-header') {
                    famClass = cls.replace('family-','');
                    return false;
                }
            });
            if (famClass && familyBlocks[famClass]) {
                familyBlocks[famClass].append($panel);
            }
        }
    });

    /* === Add blurbs under specific course titles (BLS / ACLS / PALS families only) === */
    $accordion.find('.enrpanel').each(function(){
        var $panel = $(this);
        var $heading = $panel.find('.enrpanel-heading .enrtrigger').first();
        var text = normalizeText($heading.text());

        var blurb = null;

        if (text.indexOf('bls provider') !== -1) {
            blurb = 'Common choice for CFCC, UNCW & SCC nursing / allied health programs when AHA BLS is required.';
        } else if (text.indexOf('acls provider') !== -1) {
            blurb = 'Recommended for ER, ICU, anesthesia, and hospital-based providers.';
        } else if (text.indexOf('pals provider') !== -1) {
            blurb = 'Typical for pediatric / ED providers and some EMS agencies.';
        }

        if (blurb) {
            $('<div class="course-blurb"></div>').text(blurb).insertAfter($heading);
        }
    });

    /* === Collapse behavior: only one open at a time, default BLS open === */

    var $allCourses = $accordion.find('.enrpanel').not('.family-header');

    // Start with everything closed
    $allCourses.removeClass('open');
    $allCourses.find('.enrpanel-body').hide();

    // Map triggers
    $allCourses.each(function(){
        var $panel = $(this);
        var $trigger = $panel.find('.enrpanel-heading .enrtrigger').first();
        $trigger.on('click', function(e){
            e.preventDefault();
            var isOpen = $panel.hasClass('open');

            $allCourses.removeClass('open').find('.enrpanel-body').slideUp(120);

            if (!isOpen) {
                $panel.addClass('open');
                $panel.find('.enrpanel-body').slideDown(140);
            }
        });
    });

    // Default: open the first BLS course panel (if present)
    var $firstBLS = $accordion.find('.family-bls .enrpanel').not('.family-header').first();
    if ($firstBLS.length) {
        $firstBLS.addClass('open');
        $firstBLS.find('.enrpanel-body').show();
    }

    /* === "More times..." every 10 sessions within a course === */

    $accordion.find('ul.enrclass-list').each(function(){
        var $list = $(this);
        var $items = $list.children('li');
        if ($items.length <= 10) return;

        $items.each(function(i){
            if (i >= 10) $(this).addClass('enrclass-hidden');
        });

        var $btn = $('<button type="button" class="more-times-btn">More times…</button>');
        $btn.insertAfter($list);

        $btn.on('click', function(){
            var $hidden = $list.children('li.enrclass-hidden').slice(0, 10);
            $hidden.removeClass('enrclass-hidden');
            if (!$list.children('li.enrclass-hidden').length) {
                $btn.remove();
            }
        });
    });

});
</script>

</body>
</html>
'''

def load_snapshot(path: Path) -> BeautifulSoup:
    if not path.is_file():
        raise FileNotFoundError(f"Snapshot HTML not found: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(text, "html.parser")

def extract_and_clean_panel(soup: BeautifulSoup) -> str:
    panel = soup.find(id="maincontent_schedPanel")
    if panel is None:
        # fall back to entire body
        panel = soup.body
    if panel is None:
        raise RuntimeError("Could not find #maincontent_schedPanel or <body> in snapshot HTML")

    # Remove Enrollware scripts & hidden inputs so they can't hijack layout
    for s in panel.find_all("script"):
        s.decompose()
    for inp in panel.find_all("input"):
        if inp.get("type") in ("hidden", "submit"):
            inp.decompose()
    for frm in panel.find_all("form"):
        frm.decompose()

    return str(panel)

def build_index(snapshot_path: Path = DEFAULT_SNAPSHOT, output_path: Path = DEFAULT_OUTPUT) -> None:
    snap_soup = load_snapshot(snapshot_path)
    panel_html = extract_and_clean_panel(snap_soup)

    if "{{SCHEDULE_PANEL}}" not in INDEX_TEMPLATE:
        raise RuntimeError("Template is missing the {{SCHEDULE_PANEL}} placeholder")

    html = INDEX_TEMPLATE.replace("{{SCHEDULE_PANEL}}", panel_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote homepage: {output_path} (source: {snapshot_path})")

def main(argv=None):
    argv = argv or sys.argv[1:]
    snap = Path(argv[0]) if len(argv) >= 1 else DEFAULT_SNAPSHOT
    out = Path(argv[1]) if len(argv) >= 2 else DEFAULT_OUTPUT
    build_index(snap, out)

if __name__ == "__main__":
    main()
