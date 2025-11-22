#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build-index.py

Generate docs/index.html for 910CPR with:
- Quick Select buttons (hard-coded)
- Family-colored accordion ("curtain") fed by data/schedule.json
- One accordion open at a time
- BLS family open by default
"""

from pathlib import Path

OUTPUT_PATH = Path("docs/index.html")

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>910CPR – Class Schedule & Quick Select</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <meta name="description" content="910CPR live CPR class schedule: BLS, ACLS, PALS, Heartsaver, HSI First Aid/CPR/AED and more. Fast, local classes in Wilmington, Holly Ridge, Burgaw, Jacksonville and onsite.">

  <style>
    :root {
      --cct-bg: #f5f7fb;
      --cct-bg-alt: #ffffff;
      --cct-border: #dde3ee;
      --cct-accent: #1456a3;
      --cct-accent-soft: #e1ecfb;
      --cct-text: #1f2933;
      --cct-muted: #5f6c80;
      --cct-danger: #b3261e;
      --cct-radius-lg: 16px;
      --cct-radius-md: 10px;
      --cct-shadow-soft: 0 8px 20px rgba(15, 23, 42, 0.12);
      --cct-shadow-tiny: 0 1px 3px rgba(15, 23, 42, 0.16);
      --cct-font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

      /* family colors */
      --cct-family-bls-main: #155e75;
      --cct-family-bls-soft: #e0f2fe;

      --cct-family-acls-main: #b91c1c;
      --cct-family-acls-soft: #fee2e2;

      --cct-family-pals-main: #166534;
      --cct-family-pals-soft: #dcfce7;

      --cct-family-heartsaver-main: #7c2d12;
      --cct-family-heartsaver-soft: #ffedd5;

      --cct-family-hsi-main: #4c1d95;
      --cct-family-hsi-soft: #ede9fe;

      --cct-family-other-main: #1f2937;
      --cct-family-other-soft: #e5e7eb;
    }

    * {
      box-sizing: border-box;
    }

    html, body {
      margin: 0;
      padding: 0;
      font-family: var(--cct-font);
      color: var(--cct-text);
      background: radial-gradient(circle at top left, #ffffff 0, #f0f4ff 40%, #edf0f7 100%);
      -webkit-font-smoothing: antialiased;
    }

    a {
      color: var(--cct-accent);
      text-decoration: none;
    }

    a:hover,
    a:focus-visible {
      text-decoration: underline;
    }

    .cct-page {
      min-height: 100vh;
      padding: 16px;
      display: flex;
      justify-content: center;
    }

    .cct-shell {
      max-width: 1120px;
      width: 100%;
      background: rgba(255, 255, 255, 0.96);
      border-radius: 24px;
      box-shadow: var(--cct-shadow-soft);
      padding: 20px 22px 32px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    @media (min-width: 768px) {
      .cct-shell {
        padding: 28px 32px 36px;
        margin: 12px 0 20px;
      }
    }

    /* Header */

    .cct-header {
      display: flex;
      flex-direction: column;
      gap: 16px;
      border-bottom: 1px solid var(--cct-border);
      padding-bottom: 18px;
    }

    .cct-header-top {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }

    .cct-logo {
      flex: 0 0 auto;
      text-align: center;
    }

    .cct-logo img {
      height: 48px;
      width: auto;
      max-width: 190px;
      display: block;
    }

    @media (min-width: 768px) {
      .cct-logo img {
        height: 52px;
        max-width: 220px;
      }
    }

    .cct-header-main {
      flex: 1 1 220px;
      min-width: 0;
    }

    .cct-title {
      margin: 0;
      font-size: 1.6rem;
      letter-spacing: 0.02em;
    }

    .cct-subtitle {
      margin: 4px 0 0;
      font-size: 0.95rem;
      color: var(--cct-muted);
      max-width: 520px;
    }

    .cct-header-right {
      flex: 0 0 auto;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
      margin-left: auto;
      min-width: 130px;
    }

    .cct-call-chip {
      font-size: 0.9rem;
      background: var(--cct-accent-soft);
      border-radius: 999px;
      padding: 3px 10px;
      border: 1px solid rgba(20, 86, 163, 0.12);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }

    .cct-call-chip strong {
      font-weight: 600;
    }

    .cct-call-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border-radius: 999px;
      padding: 6px 11px;
      font-size: 0.9rem;
      border: 1px solid var(--cct-accent);
      background: #ffffff;
      color: var(--cct-accent);
      box-shadow: var(--cct-shadow-tiny);
      text-decoration: none;
    }

    .cct-call-link:hover {
      background: #f4f7ff;
      text-decoration: none;
    }

    .cct-chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 2px;
    }

    .cct-chip {
      font-size: 0.8rem;
      border-radius: 999px;
      padding: 3px 8px;
      background: #f3f4f8;
      color: var(--cct-muted);
      border: 1px solid #e2e6f0;
      white-space: nowrap;
    }

    @media (max-width: 640px) {
      .cct-header-right {
        align-items: flex-start;
      }
    }

    .cct-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      font-size: 0.88rem;
      color: var(--cct-muted);
    }

    .cct-nav a {
      padding: 5px 9px;
      border-radius: 999px;
      border: 1px solid transparent;
      text-decoration: none;
    }

    .cct-nav a:hover {
      border-color: var(--cct-border);
      background: #f7f8fc;
      text-decoration: none;
    }

    .cct-nav a.cct-nav-primary {
      border-color: var(--cct-accent);
      background: #f4f7ff;
      color: var(--cct-accent);
    }

    /* Layout: Quick Select & Course List */

    .cct-main {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr);
      gap: 18px;
      align-items: flex-start;
    }

    @media (max-width: 900px) {
      .cct-main {
        grid-template-columns: minmax(0, 1fr);
      }
    }

    .cct-card {
      background: var(--cct-bg-alt);
      border-radius: var(--cct-radius-lg);
      border: 1px solid rgba(170, 184, 204, 0.7);
      box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
      padding: 14px 14px 16px;
    }

    .cct-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }

    .cct-card-title {
      font-size: 1.0rem;
      margin: 0;
    }

    .cct-card-subtitle {
      margin: 0;
      margin-top: 2px;
      font-size: 0.84rem;
      color: var(--cct-muted);
    }

    .cct-pill {
      font-size: 0.78rem;
      padding: 3px 7px;
      border-radius: 999px;
      background: #f4f7ff;
      color: var(--cct-accent);
      border: 1px solid rgba(20, 86, 163, 0.18);
      white-space: nowrap;
    }

    /* Quick Select buttons */

    .cct-quick-select-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 8px;
      margin-top: 8px;
    }

    .cct-quick-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.9);
      background: linear-gradient(135deg, #ffffff, #f4f7ff);
      font-size: 0.86rem;
      font-weight: 500;
      color: #111827;
      cursor: pointer;
      text-decoration: none;
      transition: background 140ms ease, box-shadow 140ms ease, transform 80ms ease, border-color 140ms ease;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
      min-height: 34px;
    }

    .cct-quick-button:hover,
    .cct-quick-button:focus-visible {
      background: linear-gradient(135deg, #eef3ff, #ffffff);
      border-color: var(--cct-accent);
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.18);
      text-decoration: none;
    }

    .cct-quick-button:active {
      transform: translateY(1px);
      box-shadow: 0 1px 4px rgba(15, 23, 42, 0.18);
    }

    .cct-quick-note {
      margin-top: 10px;
      font-size: 0.8rem;
      color: var(--cct-muted);
    }

    .cct-quick-note strong {
      font-weight: 600;
    }

    /* Course area */

    .cct-status {
      font-size: 0.84rem;
      color: var(--cct-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 2px 0 10px;
    }

    .cct-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #10b981;
      box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
    }

    .cct-status-dot.cct-status-loading {
      background: #f97316;
      box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.15);
    }

    .cct-status-dot.cct-status-error {
      background: var(--cct-danger);
      box-shadow: 0 0 0 4px rgba(179, 38, 30, 0.18);
    }

    .cct-fallback-box {
      border-radius: var(--cct-radius-md);
      border: 1px dashed rgba(148, 163, 184, 0.9);
      background: #fff7f5;
      padding: 10px 10px 11px;
      font-size: 0.86rem;
      color: #7c2d12;
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 4px;
    }

    .cct-fallback-title {
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .cct-fallback-actions {
      margin-top: 2px;
    }

    .cct-fallback-actions a {
      font-size: 0.82rem;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 5px 9px;
      background: #ffffff;
      border: 1px solid rgba(148, 163, 184, 0.9);
      text-decoration: none;
    }

    .cct-fallback-actions a:hover {
      border-color: var(--cct-accent);
      background: #f7f9ff;
      text-decoration: none;
    }

    .cct-footer-note {
      margin-top: 12px;
      font-size: 0.78rem;
      color: var(--cct-muted);
      text-align: right;
    }

    /* Accordion ("curtain") */

    .cct-accordion {
      border-radius: 14px;
      border: 1px solid rgba(203, 213, 225, 0.9);
      overflow: hidden;
      background: #f8fafc;
    }

    .cct-accordion-item {
      border-bottom: 1px solid rgba(203, 213, 225, 0.85);
    }

    .cct-accordion-item:last-child {
      border-bottom: none;
    }

    .cct-accordion-header {
      width: 100%;
      padding: 9px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      background: #ffffff;
      border: none;
      cursor: pointer;
      font: inherit;
      text-align: left;
      transition: background 120ms ease, box-shadow 120ms ease;
    }

    .cct-accordion-title-wrap {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }

    .cct-accordion-title {
      font-size: 0.95rem;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .cct-accordion-sub {
      font-size: 0.8rem;
      color: var(--cct-muted);
    }

    .cct-accordion-chevron {
      flex: 0 0 auto;
      font-size: 0.9rem;
      transition: transform 160ms ease;
    }

    .cct-accordion-item.cct-open .cct-accordion-chevron {
      transform: rotate(90deg);
    }

    .cct-accordion-item.cct-open .cct-accordion-header {
      box-shadow: inset 0 -1px 0 rgba(148, 163, 184, 0.6);
    }

    /* Family-color hooks: header + board share color */

    .cct-accordion-item.cct-family-bls .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-bls-soft), #ffffff);
      border-bottom-color: rgba(15, 118, 110, 0.4);
    }
    .cct-accordion-item.cct-family-bls .cct-accordion-title {
      color: var(--cct-family-bls-main);
    }

    .cct-accordion-item.cct-family-acls .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-acls-soft), #ffffff);
      border-bottom-color: rgba(185, 28, 28, 0.4);
    }
    .cct-accordion-item.cct-family-acls .cct-accordion-title {
      color: var(--cct-family-acls-main);
    }

    .cct-accordion-item.cct-family-pals .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-pals-soft), #ffffff);
      border-bottom-color: rgba(22, 101, 52, 0.4);
    }
    .cct-accordion-item.cct-family-pals .cct-accordion-title {
      color: var(--cct-family-pals-main);
    }

    .cct-accordion-item.cct-family-heartsaver .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-heartsaver-soft), #ffffff);
      border-bottom-color: rgba(124, 45, 18, 0.4);
    }
    .cct-accordion-item.cct-family-heartsaver .cct-accordion-title {
      color: var(--cct-family-heartsaver-main);
    }

    .cct-accordion-item.cct-family-hsi .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-hsi-soft), #ffffff);
      border-bottom-color: rgba(76, 29, 149, 0.4);
    }
    .cct-accordion-item.cct-family-hsi .cct-accordion-title {
      color: var(--cct-family-hsi-main);
    }

    .cct-accordion-item.cct-family-other .cct-accordion-header {
      background: linear-gradient(90deg, var(--cct-family-other-soft), #ffffff);
      border-bottom-color: rgba(55, 65, 81, 0.4);
    }
    .cct-accordion-item.cct-family-other .cct-accordion-title {
      color: var(--cct-family-other-main);
    }

    /* Board background tied to family color */

    .cct-accordion-panel {
      max-height: 0;
      overflow: hidden;
      transition: max-height 220ms ease;
    }

    .cct-accordion-item.cct-open .cct-accordion-panel {
      /* max-height set by JS to scrollHeight */
    }

    .cct-accordion-board {
      padding: 8px 10px 10px;
      background: #f9fafb;
    }

    .cct-accordion-item.cct-family-bls .cct-accordion-board {
      background: linear-gradient(180deg, rgba(8, 47, 73, 0.04), #f1f5f9);
    }
    .cct-accordion-item.cct-family-acls .cct-accordion-board {
      background: linear-gradient(180deg, rgba(185, 28, 28, 0.05), #fef2f2);
    }
    .cct-accordion-item.cct-family-pals .cct-accordion-board {
      background: linear-gradient(180deg, rgba(22, 101, 52, 0.05), #ecfdf5);
    }
    .cct-accordion-item.cct-family-heartsaver .cct-accordion-board {
      background: linear-gradient(180deg, rgba(124, 45, 18, 0.05), #fff7ed);
    }
    .cct-accordion-item.cct-family-hsi .cct-accordion-board {
      background: linear-gradient(180deg, rgba(76, 29, 149, 0.05), #f5f3ff);
    }
    .cct-accordion-item.cct-family-other .cct-accordion-board {
      background: linear-gradient(180deg, rgba(31, 41, 55, 0.03), #f3f4f6);
    }

    .cct-course-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 460px;
      overflow: auto;
      padding-right: 2px;
    }

    .cct-course-row {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 6px 7px;
      border-radius: var(--cct-radius-md);
      border: 1px solid rgba(203, 213, 225, 0.9);
      background: #fbfcff;
      font-size: 0.88rem;
    }

    .cct-course-row:nth-child(2n) {
      background: #f7f8fc;
    }

    .cct-course-name {
      font-weight: 500;
      margin-bottom: 1px;
      word-break: break-word;
    }

    .cct-course-meta {
      font-size: 0.78rem;
      color: var(--cct-muted);
    }

    .cct-course-meta span + span::before {
      content: " • ";
      margin: 0 2px;
    }

    .cct-course-actions {
      margin-left: auto;
      flex: 0 0 auto;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 3px;
    }

    .cct-small-link-btn {
      font-size: 0.78rem;
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.9);
      background: #ffffff;
      text-decoration: none;
      white-space: nowrap;
      box-shadow: var(--cct-shadow-tiny);
    }

    .cct-small-link-btn:hover {
      background: #f4f7ff;
      border-color: var(--cct-accent);
      text-decoration: none;
    }

    /* keep date/time simple text, not a pill */
    .cct-next-label {
      font-weight: 500;
    }

    @media (max-width: 480px) {
      .cct-course-row {
        flex-direction: column;
      }
      .cct-course-actions {
        align-items: flex-start;
      }
    }
  </style>
</head>
<body>
<div class="cct-page">
  <div class="cct-shell">

    <header class="cct-header">
      <div class="cct-header-top">
        <a class="cct-logo" href="/">
          <!-- Safe to change this src; layout uses flex + max-height, not image intrinsic size -->
          <img src="https://www.enrollware.com/sitefiles/coastalcprtraining/910CPR_wave.jpg" alt="910CPR logo">
        </a>

        <div class="cct-header-main">
          <h1 class="cct-title">Class Schedule</h1>
          <p class="cct-subtitle">
            Quick access to our most requested CPR classes, plus the full list of every Enrollware course we offer.
          </p>
          <div class="cct-chip-row">
            <div class="cct-chip">AHA · Red Cross · HSI</div>
            <div class="cct-chip">Wilmington · Holly Ridge · Burgaw</div>
            <div class="cct-chip">On-site group training available</div>
          </div>
        </div>

        <div class="cct-header-right">
          <div class="cct-call-chip">
            <span>Need help picking a class?</span>
          </div>
          <a class="cct-call-link" href="tel:+19103955193">
            Call 910-395-5193
          </a>
        </div>
      </div>

      <nav class="cct-nav">
        <a class="cct-nav-primary" href="#quick-select">Quick Select</a>
        <a href="#all-courses">All courses</a>
        <a href="https://coastalcprtraining.enrollware.com/schedule" target="_blank" rel="noopener">
          Backup Enrollware schedule
        </a>
      </nav>
    </header>

    <main class="cct-main">
      <!-- LEFT: Quick Select -->
      <section id="quick-select" class="cct-card" aria-labelledby="quick-select-heading">
        <div class="cct-card-header">
          <div>
            <h2 id="quick-select-heading" class="cct-card-title">Quick Select</h2>
            <p class="cct-card-subtitle">
              Tap a button to jump straight to the schedule for that class type.
            </p>
          </div>
          <div class="cct-pill">Most requested</div>
        </div>

        <!-- IMPORTANT: Keep these buttons / labels exactly as requested -->
        <div class="cct-quick-select-grid">
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/BLS-InPerson" target="_blank" rel="noopener">
            BLS
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/BLS-Online" target="_blank" rel="noopener">
            HeartCode BLS
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/ACLS" target="_blank" rel="noopener">
            ACLS ILT Renewal
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/ACLS" target="_blank" rel="noopener">
            HeartCode ACLS
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/PALS" target="_blank" rel="noopener">
            PALS ILT Renewal
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/PALS" target="_blank" rel="noopener">
            HeartCode PALS
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/HSI-FA-CPR-AED" target="_blank" rel="noopener">
            First Aid / CPR / AED (HSI)
          </a>
          <a class="cct-quick-button" href="https://www.enrollware.com/site/coastalcprtraining/class/AHA-Heartsaver-Online" target="_blank" rel="noopener">
            AHA Heartsaver Online
          </a>
        </div>

        <p class="cct-quick-note">
          <strong>Need a different day or class?</strong>
          Use the full course list on the right or open the backup Enrollware schedule to see every option.
        </p>
      </section>

      <!-- RIGHT: Full course list using ugly Enrollware names, in a family "curtain" -->
      <section id="all-courses" class="cct-card" aria-labelledby="all-courses-heading">
        <div class="cct-card-header">
          <div>
            <h2 id="all-courses-heading" class="cct-card-title">All Enrollware Courses</h2>
            <p class="cct-card-subtitle">
              Live list built from schedule.json, grouped by course family using the original Enrollware names.
            </p>
          </div>
          <div class="cct-pill">Live from schedule.json</div>
        </div>

        <div id="course-list-status" class="cct-status" aria-live="polite">
          <div class="cct-status-dot cct-status-loading"></div>
          <span>Loading live course list…</span>
        </div>

        <div id="course-families" class="cct-accordion" aria-label="All active Enrollware course families"></div>

        <!-- Fallback if schedule.json fails or is unusable -->
        <div id="course-list-fallback" class="cct-fallback-box" hidden>
          <div class="cct-fallback-title">
            <span>Live course list is temporarily unavailable.</span>
          </div>
          <div>
            We’re still teaching — this just means the JSON feed misbehaved.
            You can always see every active class directly on Enrollware.
          </div>
          <div class="cct-fallback-actions">
            <a href="https://coastalcprtraining.enrollware.com/schedule" target="_blank" rel="noopener">
              Open backup Enrollware schedule
            </a>
          </div>
        </div>

        <div class="cct-footer-note">
          Swapping logos or editing text here won’t break the JSON loader or the curtain behavior.
        </div>
      </section>
    </main>

  </div>
</div>

<script>
(function () {
  var STATUS_EL = document.getElementById("course-list-status");
  var FAMILIES_EL = document.getElementById("course-families");
  var FALLBACK_EL = document.getElementById("course-list-fallback");

  function setStatus(state, message) {
    if (!STATUS_EL) return;
    var dot = STATUS_EL.querySelector(".cct-status-dot");
    if (dot) {
      dot.classList.remove("cct-status-loading", "cct-status-error");
      if (state === "loading") dot.classList.add("cct-status-loading");
      if (state === "error") dot.classList.add("cct-status-error");
    }
    if (message) {
      var span = STATUS_EL.querySelector("span");
      if (span) span.textContent = message;
    }
  }

  function showFallback() {
    setStatus("error", "Showing backup link instead.");
    if (FAMILIES_EL) {
      FAMILIES_EL.innerHTML = "";
      FAMILIES_EL.style.display = "none";
    }
    if (FALLBACK_EL) {
      FALLBACK_EL.hidden = false;
    }
  }

  function getCourseName(course) {
    if (!course || typeof course !== "object") return "Untitled course";
    return (
      course.enrollware_name ||
      course.original_name ||
      course.html_title ||
      course.title ||
      course.name ||
      "Untitled course"
    );
  }

  function getCourseCode(course) {
    if (!course || typeof course !== "object") return "";
    return (
      course.enrollware_code ||
      course.code ||
      course.course_code ||
      ""
    );
  }

  function getFamilyName(course) {
    if (!course || typeof course !== "object") return "Other Courses";
    return (
      course.family ||
      course.course_family ||
      course.family_name ||
      "Other Courses"
    );
  }

  function getFamilyClass(family) {
    if (!family) return "cct-family-other";
    var f = String(family).toLowerCase();
    if (f.indexOf("bls") !== -1) return "cct-family-bls";
    if (f.indexOf("acls") !== -1) return "cct-family-acls";
    if (f.indexOf("pals") !== -1) return "cct-family-pals";
    if (f.indexOf("heartsaver") !== -1) return "cct-family-heartsaver";
    if (f.indexOf("hsi") !== -1) return "cct-family-hsi";
    return "cct-family-other";
  }

  function buildCourseRow(course) {
    var row = document.createElement("div");
    row.className = "cct-course-row";

    var main = document.createElement("div");

    var name = document.createElement("div");
    name.className = "cct-course-name";
    name.textContent = getCourseName(course);
    main.appendChild(name);

    var metaPieces = [];

    var code = getCourseCode(course);
    if (code) {
      metaPieces.push("Code: " + code);
    }

    if (Array.isArray(course.sessions) && course.sessions.length > 0) {
      var sessions = course.sessions.slice().sort(function (a, b) {
        var at = a.start_local || a.start || "";
        var bt = b.start_local || b.start || "";
        if (at < bt) return -1;
        if (at > bt) return 1;
        return 0;
      });
      var upcoming = sessions.find(function (s) {
        return s && s.is_past === false;
      }) || sessions[0];

      if (upcoming) {
        var when = upcoming.friendly_date || upcoming.start_local || upcoming.start;
        if (when) {
          metaPieces.push("Next: " + when);
        }
        var whereParts = [];
        if (upcoming.city) whereParts.push(upcoming.city);
        if (upcoming.state) whereParts.push(upcoming.state);
        if (whereParts.length > 0) {
          metaPieces.push(whereParts.join(", "));
        }
      }
    }

    if (metaPieces.length > 0) {
      var meta = document.createElement("div");
      meta.className = "cct-course-meta";

      var span = document.createElement("span");
      span.innerHTML = metaPieces
        .map(function (txt) {
          if (txt.indexOf("Next:") === 0) {
            return '<span class="cct-next-label">Next:</span> ' + txt.replace("Next:", "").trim();
          }
          return txt;
        })
        .join(" • ");
      meta.appendChild(span);
      main.appendChild(meta);
    }

    row.appendChild(main);

    var actions = document.createElement("div");
    actions.className = "cct-course-actions";

    var scheduleUrl = course.schedule_url || course.catalog_url || "";
    if (scheduleUrl) {
      var btn = document.createElement("a");
      btn.className = "cct-small-link-btn";
      btn.href = scheduleUrl;
      btn.target = "_blank";
      btn.rel = "noopener";
      btn.textContent = "See dates";
      actions.appendChild(btn);
    }

    var enrollUrl = "";
    if (Array.isArray(course.sessions) && course.sessions.length > 0) {
      var first = course.sessions[0];
      enrollUrl = first.enroll_url || first.register_url || "";
    }
    if (enrollUrl && enrollUrl.indexOf("enroll?") !== -1) {
      var btn2 = document.createElement("a");
      btn2.className = "cct-small-link-btn";
      btn2.href = enrollUrl;
      btn2.target = "_blank";
      btn2.rel = "noopener";
      btn2.textContent = "Register";
      actions.appendChild(btn2);
    }

    if (actions.children.length > 0) {
      row.appendChild(actions);
    }

    return row;
  }

  function buildFamilyItem(familyName, courses) {
    var item = document.createElement("div");
    item.className = "cct-accordion-item " + getFamilyClass(familyName);

    var header = document.createElement("button");
    header.type = "button";
    header.className = "cct-accordion-header";

    var wrap = document.createElement("div");
    wrap.className = "cct-accordion-title-wrap";

    var title = document.createElement("div");
    title.className = "cct-accordion-title";
    title.textContent = familyName;
    wrap.appendChild(title);

    var sub = document.createElement("div");
    sub.className = "cct-accordion-sub";
    sub.textContent = courses.length + " course" + (courses.length === 1 ? "" : "s");
    wrap.appendChild(sub);

    header.appendChild(wrap);

    var chev = document.createElement("div");
    chev.className = "cct-accordion-chevron";
    chev.textContent = "›";
    header.appendChild(chev);

    item.appendChild(header);

    var panel = document.createElement("div");
    panel.className = "cct-accordion-panel";

    var board = document.createElement("div");
    board.className = "cct-accordion-board";

    var list = document.createElement("div");
    list.className = "cct-course-list";

    courses
      .slice()
      .sort(function (a, b) {
        var an = getCourseName(a).toUpperCase();
        var bn = getCourseName(b).toUpperCase();
        if (an < bn) return -1;
        if (an > bn) return 1;
        return 0;
      })
      .forEach(function (course) {
        list.appendChild(buildCourseRow(course));
      });

    board.appendChild(list);
    panel.appendChild(board);
    item.appendChild(panel);

    // header click: only one open at a time
    header.addEventListener("click", function () {
      if (!FAMILIES_EL) return;

      var allItems = Array.prototype.slice.call(
        FAMILIES_EL.querySelectorAll(".cct-accordion-item")
      );
      var isOpen = item.classList.contains("cct-open");

      // close all
      allItems.forEach(function (it) {
        it.classList.remove("cct-open");
        var pan = it.querySelector(".cct-accordion-panel");
        if (pan) pan.style.maxHeight = "0px";
      });

      // open clicked, if it was closed
      if (!isOpen) {
        item.classList.add("cct-open");
        if (panel) {
          panel.style.maxHeight = panel.scrollHeight + "px";
        }
      }
    });

    return item;
  }

  function renderFamilies(data) {
    if (!FAMILIES_EL) return;
    FAMILIES_EL.innerHTML = "";

    var courses = null;
    if (Array.isArray(data)) {
      courses = data;
    } else if (data && Array.isArray(data.courses)) {
      courses = data.courses;
    }

    if (!courses || courses.length === 0) {
      throw new Error("schedule.json did not contain a courses array.");
    }

    var groups = {};
    courses.forEach(function (course) {
      var fam = getFamilyName(course);
      if (!groups[fam]) groups[fam] = [];
      groups[fam].push(course);
    });

    var familyNames = Object.keys(groups).sort(function (a, b) {
      return a.toUpperCase() < b.toUpperCase() ? -1 : a.toUpperCase() > b.toUpperCase() ? 1 : 0;
    });

    familyNames.forEach(function (famName) {
      var item = buildFamilyItem(famName, groups[famName]);
      FAMILIES_EL.appendChild(item);
    });

    // Open BLS family by default if present, otherwise first family
    var defaultItem =
      FAMILIES_EL.querySelector(".cct-accordion-item.cct-family-bls") ||
      FAMILIES_EL.querySelector(".cct-accordion-item");

    if (defaultItem) {
      defaultItem.classList.add("cct-open");
      var p = defaultItem.querySelector(".cct-accordion-panel");
      if (p) {
        p.style.maxHeight = p.scrollHeight + "px";
      }
    }

    setStatus("ok", "Loaded " + courses.length + " course types in " + familyNames.length + " families.");
  }

  function init() {
    try {
      if (!window.fetch) {
        showFallback();
        return;
      }
      setStatus("loading", "Loading live course list…");

      fetch("data/schedule.json", { cache: "no-store" })
        .then(function (resp) {
          if (!resp.ok) {
            throw new Error("HTTP " + resp.status);
          }
          return resp.json();
        })
        .then(function (data) {
          try {
            renderFamilies(data);
          } catch (e) {
            console.error("Error rendering schedule.json:", e);
            showFallback();
          }
        })
        .catch(function (err) {
          console.error("Error fetching schedule.json:", err);
          showFallback();
        });

    } catch (outerErr) {
      console.error("schedule.json loader crashed early:", outerErr);
      showFallback();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>

</body>
</html>
"""

def main():
  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  OUTPUT_PATH.write_text(INDEX_HTML, encoding="utf-8")
  print(f"Wrote homepage: {OUTPUT_PATH}")

if __name__ == "__main__":
  main()
