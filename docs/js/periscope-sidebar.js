/* ============================================================
   910CPR Periscope Sidebar
   Mode Picker + Filtering Engine + Renderer
   ------------------------------------------------------------
   Expects schedule.json with fields:
   - courseId
   - family
   - deliveryMode
   - certBody
   - location
   - date
   - time
   - seats
   - price
   - registerUrl
   ============================================================ */

window.PeriscopeSidebar = (function(){

  let sessions = [];
  let loaded = false;
  const listEl = document.getElementById("periscope-session-list");
  const modePickerEl = document.getElementById("periscope-mode-picker");
  const scheduleUrl = listEl.getAttribute("data-schedule-url");

  /* ===================================================
     Fetch JSON once on first drawer open
  =================================================== */
  async function loadData() {
    if (loaded) return sessions;

    try {
      const resp = await fetch(scheduleUrl, { cache: "no-store" });
      sessions = await resp.json();
      loaded = true;
      return sessions;
    } catch (e) {
      listEl.innerHTML = `<div class="periscope-error">Error loading schedule.</div>`;
      return [];
    }
  }

  /* ===================================================
     Utility: unique delivery modes per family
  =================================================== */
  function getModesForFamily(family) {
    const modes = new Set();
    sessions.forEach(s => {
      if (s.family === family) {
        if (s.deliveryMode) modes.add(s.deliveryMode);
      }
    });
    return Array.from(modes);
  }

  /* ===================================================
     Mode Labels (Option B)
  =================================================== */
  const MODE_LABELS = {
    ILT: {
      title: "In-Person (Instructor-Led)",
      desc: "Full instructor-led class delivered on-site at 910CPR."
    },
    HEARTCODE: {
      title: "AHA HeartCode (Online + Skills Test)",
      desc: "Complete the official AHA online course, then attend a short, hands-on skills session."
    },
    BLENDED: {
      title: "Blended Learning (ARC/HSI)",
      desc: "Online coursework followed by an in-person skills check. Great for workplace requirements."
    },
    ONLINE: {
      title: "Online-Only (No Skills Check)",
      desc: "Self-paced online training. Not all employers accept online-only."
    }
  };

  /* ===================================================
     Step 1: Build Mode Picker UI for selected family
  =================================================== */
  function buildModes() {
    const family = window.PeriscopeFilter.family;
    if (!family) return;

    modePickerEl.innerHTML = `<div class="periscope-loading">Loading formats...</div>`;

    const modes = getModesForFamily(family);

    if (modes.length === 0) {
      modePickerEl.innerHTML = `
        <div class="periscope-empty">
          No available delivery modes for this course.
        </div>`;
      return;
    }

    let html = "";
    modes.forEach(mode => {
      const label = MODE_LABELS[mode] ? MODE_LABELS[mode].title : mode;
      const desc  = MODE_LABELS[mode] ? MODE_LABELS[mode].desc  : "";

      html += `
        <div class="periscope-mode-card"
             data-mode="${mode}"
             onclick="PeriscopeController.applyMode('${mode}', '${label}')">
          <div class="periscope-mode-title">${label}</div>
          <div class="periscope-mode-desc">${desc}</div>
        </div>
      `;
    });

    modePickerEl.innerHTML = html;
  }

  /* ===================================================
     Step 2: Filter Sessions
  =================================================== */
  function applyFilters() {
    const f = window.PeriscopeFilter;

    return sessions.filter(s => {
      /* Filter by family */
      if (f.family && s.family !== f.family)
        return false;

      /* Filter by deliveryMode */
      if (f.deliveryMode && s.deliveryMode !== f.deliveryMode)
        return false;

      /* Filter by cert body */
      if (f.certBody && s.certBody !== f.certBody)
        return false;

      /* Filter by courseIds (multi) */
      if (f.courseIds && Array.isArray(f.courseIds)) {
        if (!f.courseIds.includes(s.courseId)) return false;
      }

      return true;
    });
  }

  /* ===================================================
     Render session cards
  =================================================== */
  function renderSessions() {
    listEl.classList.remove("periscope-loading");

    const filtered = applyFilters();

    if (filtered.length === 0) {
      listEl.innerHTML = `
        <div class="periscope-empty">No upcoming classes found.</div>
      `;
      return;
    }

    /* Sort by date ascending */
    filtered.sort((a,b) => {
      const d1 = new Date(a.date + " " + a.time);
      const d2 = new Date(b.date + " " + b.time);
      return d1 - d2;
    });

    let html = "";
    filtered.forEach(s => {
      const seatsClass =
        s.seats === 0 ? "periscope-seats-full" :
        s.seats <= 2 ? "periscope-seats-low" : "periscope-seats";

      const modeLabel = MODE_LABELS[s.deliveryMode]
        ? MODE_LABELS[s.deliveryMode].title
        : s.deliveryMode;

      html += `
        <div class="periscope-card">
          <div class="periscope-row-top">
            <div class="periscope-date">${s.date}</div>
            <div class="periscope-time">${s.time}</div>
          </div>

          <div class="periscope-location">${s.location}</div>
          <div class="periscope-mode">${modeLabel}</div>

          <div class="periscope-meta">
            <div class="periscope-price">$${s.price}</div>
            <div class="${seatsClass}">
              ${s.seats === 0 ? "Full" : s.seats + " seats"}
            </div>
          </div>

          <div class="periscope-card-actions">
            <a class="periscope-button-primary"
               href="${s.registerUrl}"
               target="_blank">
               Register
            </a>
          </div>
        </div>
      `;
    });

    listEl.innerHTML = html;
  }

  /* ===================================================
     PUBLIC API
  =================================================== */
  return {
    refresh: function(){
      loadData().then(renderSessions);
    },
    buildModes: function(){
      loadData().then(buildModes);
    }
  };

})();
