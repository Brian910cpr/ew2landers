(function (window, document) {
"use strict";

function initSidebar() {
var sidebar = document.getElementById("periscope-sidebar");
if (!sidebar) { return; }

var listEl = sidebar.querySelector(".periscope-list");

var scheduleUrl   = sidebar.getAttribute("data-schedule-url");
var maxSessions   = parseInt(sidebar.getAttribute("data-max-sessions"), 10) || 4;
var scheduleLink  = sidebar.getAttribute("data-schedule-link") || "";

var state = {
  allSessions: [],
  lastFilter: { type: null, value: null }
};

function setLoading() {
  if (!listEl) { return; }
  listEl.className = "periscope-list periscope-loading";
  listEl.textContent = "Loading live class times…";
}

function setError(message) {
  if (!listEl) { return; }
  listEl.className = "periscope-list periscope-error";
  listEl.textContent = message || "Unable to load live class times. Please open the full class schedule.";
}

function setEmpty(message) {
  if (!listEl) { return; }
  listEl.className = "periscope-list periscope-empty";
  listEl.textContent = message || "No upcoming classes are currently listed.";
}

function getCurrentFilter() {
  var f = window.PeriscopeFilter || {};
  var type = f.type || null;
  var value = f.value || null;

  if (state.lastFilter.type === type && state.lastFilter.value === value) {
    return { type: type, value: value, changed: false };
  }

  state.lastFilter = { type: type, value: value };
  return { type: type, value: value, changed: true };
}

function filterSessions() {
  if (!state.allSessions.length) { return []; }

  var now = new Date();
  var upcoming = state.allSessions.filter(function (s) {
    if (!s.start) { return false; }
    var d = new Date(s.start);
    return !isNaN(d.getTime()) && d >= now;
  });

  var f = window.PeriscopeFilter || {};
  var type = f.type || null;
  var value = f.value || null;

  if (!type || !value) {
    return upcoming;
  }

  return upcoming.filter(function (s) {
    if (type === "family") {
      return s.family === value;
    }
    if (type === "certBody") {
      return s.certBody === value;
    }
    if (type === "delivery") {
      return s.deliveryMode === value;
    }
    if (type === "course_id") {
      return String(s.course_id) === String(value);
    }
    if (type === "location_contains") {
      return (s.location || "").indexOf(value) !== -1;
    }
    // Default: if we don’t recognize the filter, don’t exclude the class
    return true;
  });
}

function formatDateTime(iso) {
  var d = new Date(iso);
  if (isNaN(d.getTime())) {
    return { date: "Date TBA", time: "" };
  }
  var date = d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric"
  });
  var time = d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit"
  });
  return { date: date, time: time };
}

function escapeHtml(str) {
  if (!str) { return ""; }
  return String(str).replace(/[&<>"']/g, function (ch) {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;"
    }[ch];
  });
}

function buildCardHtml(session) {
  var dt = formatDateTime(session.start);
  var title = session.cleanTitle || session.title || session.family || "CPR Class";
  var location = session.location || "Location TBA";

  var url = scheduleLink;
  if (session.session_id) {
    // Direct link to that exact Enrollware class instance
    url = "https://coastalcprtraining.enrollware.com/enroll?id=" + session.session_id;
  }

  var seatsLabel = "Open seats";
  var seatsClass = "periscope-seats";

  if (typeof session.seats === "number") {
    if (session.seats <= 0) {
      seatsLabel = "Class full";
      seatsClass += " periscope-seats-full";
    } else if (session.seats <= 2) {
      seatsLabel = session.seats + (session.seats === 1 ? " seat left" : " seats left");
      seatsClass += " periscope-seats-low";
    } else {
      seatsLabel = session.seats + " seats open";
    }
  }

  var htmlParts = [];

  htmlParts.push('<div class="periscope-card">');

  htmlParts.push('<div class="periscope-row-top">');
  htmlParts.push('<div>');
  htmlParts.push('<div class="periscope-date">' + dt.date + "</div>");
  htmlParts.push('<div class="periscope-time">' + dt.time + "</div>");
  htmlParts.push("</div>");
  htmlParts.push('<div class="periscope-location">' + escapeHtml(title) + "</div>");
  htmlParts.push("</div>");

  htmlParts.push('<div class="periscope-location">' + escapeHtml(location) + "</div>");

  htmlParts.push('<div class="periscope-meta">');
  htmlParts.push('<div class="periscope-price"></div>');
  htmlParts.push('<div class="' + seatsClass + '">' + seatsLabel + "</div>");
  htmlParts.push("</div>");

  htmlParts.push('<div class="periscope-card-actions">');
  htmlParts.push('<a class="periscope-button periscope-button-primary" href="' + url + '">Register</a>');
  htmlParts.push("</div>");

  htmlParts.push("</div>");

  return htmlParts.join("");
}

function render() {
  if (!listEl) { return; }

  var sessions = filterSessions();

  if (!sessions.length) {
    setEmpty("No upcoming classes match this filter. Try another class type or open the full schedule.");
    return;
  }

  sessions.sort(function (a, b) {
    var da = a.start ? new Date(a.start) : 0;
    var db = b.start ? new Date(b.start) : 0;
    return da - db;
  });

  var limited = sessions.slice(0, maxSessions);
  var htmlParts = [];
  for (var i = 0; i < limited.length; i++) {
    htmlParts.push(buildCardHtml(limited[i]));
  }

  listEl.className = "periscope-list";
  listEl.innerHTML = htmlParts.join("");
}

function load() {
  if (!scheduleUrl) {
    setError("No schedule URL configured.");
    return;
  }

  setLoading();

  fetch(scheduleUrl, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      var sessions = data && data.sessions ? data.sessions : [];
      if (!Array.isArray(sessions)) {
        sessions = [];
      }
      state.allSessions = sessions;
      getCurrentFilter(); // initialize filter cache
      render();
    })
    .catch(function () {
      setError("Unable to load live class times. Please open the full class schedule.");
    });
}

// Expose API used by the inline GoDaddy script
window.PeriscopeSidebar = window.PeriscopeSidebar || {};
window.PeriscopeSidebar.refresh = function () {
  // If we've already pulled the schedule, just re-render with the new filter
  if (state.allSessions && state.allSessions.length) {
    getCurrentFilter();
    render();
  } else {
    load();
  }
};

// Initial load
load();


}

if (document.readyState === "loading") {
document.addEventListener("DOMContentLoaded", initSidebar);
} else {
initSidebar();
}
})(window, document);