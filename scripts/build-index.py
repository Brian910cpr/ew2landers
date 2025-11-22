#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build-index.py

Generate a static docs/index.html for 910CPR using the hardened
layout shell that loads schedule.json via accordion.js.

Defaults:
input:  docs/data/enrollware-schedule.html  (currently unused, kept for compatibility)
output: docs/index.html
"""

import sys
from pathlib import Path
from textwrap import dedent

# BeautifulSoup and snapshot parsing kept here only for forward compatibility.
# Right now the index template does not inject the raw Enrollware schedule panel.
try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # fall back if bs4 is not installed


DEFAULT_INPUT = Path("docs/data/enrollware-schedule.html")
DEFAULT_OUTPUT = Path("docs/index.html")


INDEX_TEMPLATE = dedent("""\
<!DOCTYPE html>
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
          <span>Loading live course list&hellip;</span>
        </div>

        <div id="course-families" class="cct-accordion" aria-label="All active Enrollware course families"></div>

        <!-- Fallback if schedule.json fails or is unusable -->
        <div id="course-list-fallback" class="cct-fallback-box" hidden>
          <div class="cct-fallback-title">
            <span>Live course list is temporarily unavailable.</span>
          </div>
          <div>
            We&rsquo;re still teaching &mdash; this just means the JSON feed misbehaved.
            You can always see every active class directly on Enrollware.
          </div>
          <div class="cct-fallback-actions">
            <a href="https://coastalcprtraining.enrollware.com/schedule" target="_blank" rel="noopener">
              Open backup Enrollware schedule
            </a>
          </div>
        </div>

        <div class="cct-footer-note">
          Swapping logos or editing text here won&rsquo;t break the JSON loader or the curtain behavior.
        </div>
      </section>
    </main>

  </div>
</div>

<script src="js/accordion.js"></script>

</body>
</html>
""")


def parse_snapshot(path: Path):
    """
    Load the latest Enrollware snapshot and return a BeautifulSoup document.

    Currently kept only for forward compatibility; the hardened index.html
    shell does not inject the raw Enrollware HTML panel.
    """
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup (bs4) is not installed.")
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    html = path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser")


def extract_schedule_panel(soup) -> str:
    """
    Historically pulled the Enrollware schedule block from the snapshot.

    For this hardened version, we no longer inject the raw panel, so this
    returns an empty string. Left in place so old code paths don't explode.
    """
    return ""


def build_index(input_path: Path, output_path: Path) -> None:
    """
    Write docs/index.html using the hardened layout shell.

    input_path is accepted but currently unused (kept for CLI compatibility).
    """
    # If you ever want to revive snapshot parsing, this is where you would:
    #   soup = parse_snapshot(input_path)
    #   panel_html = extract_schedule_panel(soup)
    #   html = INDEX_TEMPLATE.replace("{{SCHEDULE_PANEL}}", panel_html)
    # For now, we just use INDEX_TEMPLATE as-is.
    html = INDEX_TEMPLATE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote homepage: {output_path}")


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
