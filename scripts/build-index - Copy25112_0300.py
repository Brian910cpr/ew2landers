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
<title>CPR, BLS, ACLS &amp; First Aid Classes in Wilmington &amp; Burgaw, NC | 910CPR Class Schedule</title>
<meta name="description" content="910CPR offers AHA and HSI CPR, BLS, ACLS, PALS and First Aid classes in Wilmington, Burgaw and onsite across southeastern North Carolina. Same-day cards, small classes, and flexible schedules for healthcare providers, workplaces, and the community.">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://www.910cpr.com/">

<!-- Basic 910CPR structured data (LocalBusiness + core Courses) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "LocalBusiness",
      "@id": "https://www.910cpr.com/#business",
      "name": "910CPR \u2013 Coastal CPR Training",
      "url": "https://www.910cpr.com/",
      "telephone": "+1-910-395-5193",
      "image": [
        "https://www.910cpr.com/images/910cpr_round.png"
      ],
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "4018 Shipyard Blvd, Unit #2",
        "addressLocality": "Wilmington",
        "addressRegion": "NC",
        "postalCode": "28403",
        "addressCountry": "US"
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
      "name": "AHA BLS Provider \u2013 CPR for Healthcare Providers in Wilmington & Burgaw, NC",
      "description": "American Heart Association Basic Life Support (BLS) CPR course for nurses, nursing students, EMS professionals, and other healthcare providers. Meets CPR requirements for CFCC, UNCW, and SCC nursing and allied health programs.",
      "provider": {
        "@type": "Organization",
        "name": "910CPR \u2013 Coastal CPR Training",
        "sameAs": "https://www.910cpr.com/"
      }
    },
    {
      "@type": "Course",
      "name": "AHA ACLS Provider \u2013 Advanced Cardiac Life Support in Wilmington & Burgaw, NC",
      "description": "Advanced Cardiac Life Support (ACLS) training for hospital and EMS clinicians who manage adult cardiac arrest, peri-arrest conditions, and post-resuscitation care.",
      "provider": {
        "@type": "Organization",
        "name": "910CPR \u2013 Coastal CPR Training",
        "sameAs": "https://www.910cpr.com/"
      }
    },
    {
      "@type": "Course",
      "name": "AHA PALS Provider \u2013 Pediatric Advanced Life Support in Wilmington & Burgaw, NC",
      "description": "Pediatric Advanced Life Support (PALS) course for nurses, physicians, and paramedics who care for critically ill or injured infants and children.",
      "provider": {
        "@type": "Organization",
        "name": "910CPR \u2013 Coastal CPR Training",
        "sameAs": "https://www.910cpr.com/"
      }
    },
    {
      "@type": "Course",
      "name": "CPR, AED & First Aid Training for Workplaces, Schools & the Community",
      "description": "CPR, AED and First Aid courses for workplaces, schools, childcare, coaches and the general public. Options include AHA Heartsaver and HSI First Aid/CPR/AED.",
      "provider": {
        "@type": "Organization",
        "name": "910CPR \u2013 Coastal CPR Training",
        "sameAs": "https://www.910cpr.com/"
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

/* Keep main content narrower and centered for cleaner look */
#hero,
#schedule-section,
#schedule-root {
    max-width:900px;
    margin:0 auto;
}

/* ===== Header / nav ===== */

.site-header {
    max-width:900px;
    margin:0 auto 16px auto;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:16px;
}

.site-header .logo-wrap img {
    max-height:56px;
    width:auto;
}

.main-nav ul {
    list-style:none;
    display:flex;
    flex-wrap:wrap;
    gap:10px 18px;
    margin:0;
    padding:0;
    font-size:0.9rem;
}

.main-nav a {
    text-decoration:none;
    color:var(--text);
    font-weight:500;
}

.main-nav a:hover {
    color:var(--accent);
    text-decoration:underline;
}

/* ===== Hero / intro ===== */

#hero {
    margin-bottom:18px;
    background:#ffffff;
    border-radius:10px;
    border:1px solid var(--border);
    padding:14px 16px;
}

#hero h1 {
    font-size:1.4rem;
    margin:0 0 6px 0;
    text-align:center;
}

#hero p {
    margin:4px 0;
    font-size:0.95rem;
}

#hero .hero-highlight {
    font-weight:600;
}

/* ===== Content sections ===== */

.section {
    margin-top:20px;
    margin-bottom:8px;
}

.section h2 {
    font-size:1.1rem;
    margin:0 0 6px 0;
}

.section p,
.section li {
    font-size:0.95rem;
}

.section ul {
    padding-left:18px;
}

/* ===== Screen reader utility ===== */

.sr-only {
    position:absolute;
    width:1px;
    height:1px;
    padding:0;
    margin:-1px;
    overflow:hidden;
    clip:rect(0,0,0,0);
    white-space:nowrap;
    border:0;
}

/* Wrap the whole Enrollware block in a soft card and center it */

#schedule-root #maincontent_schedPanel {
    background:var(--card-bg);
    border-radius:10px;
    border:1px solid var(--border);
    padding:16px 16px 20px 16px;
    box-shadow:0 3px 8px rgba(0,0,0,0.05);
}

/* Tighten the three header/quick-menu tables at the top */
#maincontent_schedPanel > table {
    margin:0 auto 10px auto !important;
}

/* Center text in contact paragraphs under the buttons */
#maincontent_schedPanel > p {
    text-align:center;
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

/* Filters row: center everything under the hero */
@media (min-width: 768px) {
    #filters-row {
        display:flex;
        flex-wrap:wrap;
        gap:12px 24px;
        align-items:flex-end;
        justify-content:center;
        margin:6px auto 10px auto;
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
    cursor:pointer;
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
            var $first = $search.length ? $search : $loc;
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
            $panel.find('a.enrtrigger').off('click'); // we'll handle clicks ourselves
            familyPanels.push($panel);
        }
    });

    // 2) Group the course panels that come after each family header,
    //    and tag course panels by family type.
    for (var i = 0; i < familyPanels.length; i++) {
        var $family = familyPanels[i];
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
    }

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

    // 6) Course accordion: only one course open at a time,
    //    and when you open one, scroll so the title stays in view.
    $('.course-panel a.enrtrigger').on('click', function(e){
        e.preventDefault();
        var $heading = $(this).closest('.enrpanel-heading');
        var $body = $heading.nextAll('.enrpanel-body').first();

        if ($body.is(':visible')) {
            $body.slideUp();
        } else {
            $('.course-panel .enrpanel-body:visible').slideUp();
            $body.slideDown(200, function(){
                var offset = $heading.offset().top - 80;
                $('html, body').animate({scrollTop: offset}, 200);
            });
        }
        return false;
    });

    // 7) FAMILY accordion: all family groups closed by default, only one open at a time
    $('.course-family-group').hide();

    $('.enrpanel.family-header a.enrtrigger').on('click', function(e){
        e.preventDefault();
        var $header = $(this).closest('.enrpanel.family-header');
        var $group = $header.next('.course-family-group');
        if (!$group.length) return;

        if ($group.is(':visible')) {
            $group.slideUp();
        } else {
            $('.course-family-group:visible').slideUp();
            $group.slideDown(200, function(){
                var offset = $header.offset().top - 80;
                $('html, body').animate({scrollTop: offset}, 200);
            });
        }
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

    // 8) Mark each date/time/location link as a "session button" for styling
    $('.course-panel .enrclass-list li a').addClass('session-link');

    // 9) Paginate long session lists: show first 10, "More times…" button for the rest
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

            var $btn = $('<button type="button" class="session-more-button">More times\u2026</button>');
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

    // 10) Final safety: make all images responsive
    $('#schedule-root img').css({maxWidth:'100%', height:'auto'});
});
</script>
</head>

<body id="enrollware-reg">
<div id="page-wrap">

    <header class="site-header">
        <div class="logo-wrap">
            <a href="https://www.910cpr.com/">
                <img src="https://coastalcprtraining.enrollware.com/sitefiles/coastalcprtraining/910cpr_round.png" alt="910CPR logo">
            </a>
        </div>
        <nav class="main-nav" aria-label="Primary navigation">
            <ul>
                <li><a href="https://www.910cpr.com/">Class Schedule</a></li>
                <li><a href="https://coastalcprtraining.com/classes" target="_blank" rel="noopener">Classes Overview</a></li>
                <li><a href="https://coastalcprtraining.com/on-site-training" target="_blank" rel="noopener">On-Site Training</a></li>
                <li><a href="https://coastalcprtraining.com/2025-price-list" target="_blank" rel="noopener">2025 Price List</a></li>
                <li><a href="https://coastalcprtraining.com/about" target="_blank" rel="noopener">About 910CPR</a></li>
                <li><a href="tel:+19103955193">Call 910-395-5193</a></li>
            </ul>
        </nav>
    </header>

    <section id="hero">
        <h1>CPR, BLS, ACLS, PALS &amp; First Aid Classes in Wilmington &amp; Burgaw, NC</h1>
        <p class="hero-highlight">
            Live and blended CPR training for healthcare providers, workplaces, schools, and families across southeastern North Carolina.
        </p>
        <p>
            910CPR is an American Heart Association, American Red Cross, and HSI training center providing small classes, fast certificate delivery,
            and realistic practice in our Wilmington and Burgaw classrooms or at your location.
        </p>
        <p>
            Use the schedule below to find the class, date, and location that works best for you. If you need help choosing the right course,
            call or text <strong>910-395-5193</strong> during business hours.
        </p>
    </section>

    <main>
        <section id="schedule-section" class="section">
            <h2 class="sr-only">Live CPR &amp; First Aid Class Schedule</h2>
            <div id="schedule-root">
{{SCHEDULE_PANEL}}
            </div>
        </section>

        <section id="why-910cpr" class="section">
            <h2>Why choose 910CPR for your CPR &amp; BLS class?</h2>
            <ul>
                <li><strong>Trusted locally.</strong> We have provided CPR, BLS, ACLS, PALS and First Aid training for hospitals, clinics, schools, dental offices, and small businesses throughout southeastern North Carolina.</li>
                <li><strong>Same-day or fast cards.</strong> Most students receive their eCard shortly after class, so you can start a new job or clinical rotation without waiting weeks.</li>
                <li><strong>Flexible options.</strong> In-person, blended/online + skills, and onsite group training are all available so you can match your schedule and learning style.</li>
                <li><strong>Small, hands-on classes.</strong> Our instructors keep class sizes reasonable and focus on real-world scenarios, not just PowerPoint slides.</li>
                <li><strong>Easy parking &amp; clear directions.</strong> Our Wilmington and Burgaw classrooms are easy to find, and we bring the class to you for onsite or group bookings.</li>
            </ul>
        </section>

        <section id="faq" class="section">
            <h2>Common questions about CPR classes at 910CPR</h2>
            <h3>Which CPR class do I need for nursing or healthcare programs?</h3>
            <p>
                Most nursing, respiratory therapy, and allied health programs at <strong>CFCC</strong>, <strong>UNCW</strong>, and <strong>SCC</strong> require
                the <strong>AHA BLS Provider</strong> course. If you are unsure, choose BLS or contact your school for their exact requirement and then match it to
                the course titles on this page.
            </p>

            <h3>Do you offer onsite CPR training for offices and groups?</h3>
            <p>
                Yes. 910CPR provides onsite AHA, HSI and Red Cross classes for medical practices, construction companies, schools, churches and other groups.
                Use the “On-Site Training” link above or call us to request a quote and available dates.
            </p>

            <h3>How quickly will I receive my CPR card?</h3>
            <p>
                Most students receive their eCard the same day or within a few business days after successful completion of class.
                If you are on a deadline for a job or clinical rotation, let your instructor know at the beginning of class.
            </p>
        </section>
    </main>

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
    # Fallback: older or alternate markup
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
