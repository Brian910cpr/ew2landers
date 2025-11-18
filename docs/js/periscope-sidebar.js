(function (window, document) {
"use strict";

// Internal state
var state = {
sidebar: null,
listEl: null,
scheduleUrl: null,
scheduleLink: null,
maxSessions: 6,
allSessions: [],
isLoading: false,
hasLoadedOnce: false
};

function getFilter() {
var f = window.PeriscopeFilter || {};
if (!f || !f.type || !f.value) {
return { type: null, value: null };
}
return { type: String(f.type), value: String(f.value) };
}

function normalizeIdList(value) {
var ids = String(value || "")
.split(",")
.map(function (s) { return parseInt(s.trim(), 10); })
.filter(function (n) { return !isNaN(n); });
return ids;
}

function normalizeStringList(value) {
return String(value || "")
.split(",")
.map(function (s) { return s.trim().toLowerCase(); })
.filter(function (s) { return s.length > 0; });
}

function filterSessions(sessions) {
var now = new Date();
var filtered = [];

var filter = getFilter();
var type = filter.type;
var value = filter.value;

var idList, strList, needle;

for (var i = 0; i < sessions.length; i++) {
  var s = sessions[i];

  // Future only
  var startDate = new Date(s.start);
  if (!(startDate instanceof Date) || isNaN(startDate.getTime())) {
    continue;
  }
  if (startDate.getTime() < now.getTime()) {
    continue;
  }

  var keep = true;

  if (type && value) {
    if (type === "course_id") {
      idList = idList || normalizeIdList(value);
      if (idList.length) {
        keep = idList.indexOf(Number(s.course_id)) !== -1;
      }
    } else if (type === "family") {
      strList = strList || normalizeStringList(value);
      if (strList.length) {
        var fam = (s.family || "").toLowerCase();
        keep = strList.indexOf(fam) !== -1;
      }
    } else if (type === "certBody") {
      strList = strList || normalizeStringList(value);
      if (strList.length) {
        var body = (s.certBody || "").toLowerCase();
        keep = strList.indexOf(body) !== -1;
      }
    } else if (type === "deliveryMode") {
      strList = strList || normalizeStringList(value);
      if (strList.length) {
        var mode = (s.deliveryMode || "").toLowerCase();
        keep = strList.indexOf(mode) !== -1;
      }
    } else if (type === "location_contains") {
      needle = (value || "").toLowerCase();
      if (needle) {
        var loc = (s.location || "").toLowerCase();
        keep = loc.indexOf(needle) !== -1;
      }
    }
  }

  if (keep) {
    filtered.push(s);
  }
}

// Sort by start time ascending
filtered.sort(function (a, b) {
  var ta = new Date(a.start).getTime();
  var tb = new Date(b.start).getTime();
  if (isNaN(ta) && isNaN(tb)) return 0;
  if (isNaN(ta)) return 1;
  if (isNaN(tb)) return -1;
  return ta - tb;
});

// Limit to maxSessions
if (state.maxSessions && filtered.length > state.maxSessions) {
  filtered = filtered.slice(0, state.maxSessions);
}

return filtered;


}

function formatDateTime(startIso) {
var d = new Date(startIso);
if (isNaN(d.getTime())) {
return { date: "", time: "" };
}

var weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

var dow = weekdayNames[d.getDay()];
var month = monthNames[d.getMonth()];
var day = d.getDate();
var hours = d.getHours();
var minutes = d.getMinutes();

var ampm = hours >= 12 ? "PM" : "AM";
var h12 = hours % 12;
if (h12 === 0) h12 = 12;

var minuteStr = minutes < 10 ? "0" + minutes : String(minutes);

return {
  date: dow + ", " + month + " " + day,
  time: h12 + ":" + minuteStr + " " + ampm
};


}

function seatsLabel(seats) {
if (seats == null || isNaN(Number(seats))) return "";
var n = Number(seats);
if (n <= 0) return "Class full";
if (n <= 2) return n + " seats left";
return n + " seats open";
}

function buildRegisterUrl(session) {
// Session-level enroll link
if (session.session_id) {
return "https://coastalcprtraining.enrollware.com/enroll?id=
" +
encodeURIComponent(session.session_id);
}
// Fallback: course schedule page (if you ever need it)
if (state.scheduleLink) {
return state.scheduleLink;
}
return "https://coastalcprtraining.enrollware.com/schedule
";
}

function renderMessage(text, cssClass) {
var listEl = state.listEl;
if (!listEl) return;
listEl.className = "periscope-list " + (cssClass || "");
listEl.innerHTML = text;
}

function renderSessions() {
var listEl = state.listEl;
if (!listEl) return;

listEl.className = "periscope-list";

if (!state.allSessions || !state.allSessions.length) {
  renderMessage(
    "No upcoming classes are currently listed. Please check back soon or open the full class schedule.",
    "periscope-empty"
  );
  return;
}

var sessions = filterSessions(state.allSessions);

if (!sessions.length) {
  renderMessage(
    "No upcoming classes matched this filter. Try another date or view the full schedule.",
    "periscope-empty"
  );
  return;
}

var htmlParts = [];
for (var i = 0; i < sessions.length; i++) {
  var s = sessions[i];
  var dt = formatDateTime(s.start);
  var seatText = seatsLabel(s.seats);
  var seatClass = "periscope-seats";
  if (s.seats != null && !isNaN(Number(s.seats))) {
    var n = Number(s.seats);
    if (n <= 0) {
      seatClass += " periscope-seats-full";
    } else if (n <= 2) {
      seatClass += " periscope-seats-low";
    }
  }

  var locationText = s.location || "";
  var titleText = s.cleanTitle || s.title || "";

  var regUrl = buildRegisterUrl(s);

  htmlParts.push(
    '<div class="periscope-card">' +
      '<div class="periscope-row-top">' +
        '<div class="periscope-date">' + escapeHtml(dt.date) + '</div>' +
        '<div class="periscope-time">' + escapeHtml(dt.time) + '</div>' +
      '</div>' +
      '<div class="periscope-location">' + escapeHtml(locationText) + '</div>' +
      '<div class="periscope-meta">' +
        '<div class="periscope-price">' + escapeHtml(titleText) + '</div>' +
        '<div class="' + seatClass + '">' + escapeHtml(seatText) + '</div>' +
      '</div>' +
      '<div class="periscope-card-actions">' +
        '<a class="periscope-button periscope-button-primary" target="_blank" rel="noopener" href="' + regUrl + '">' +
          'Register' +
        '</a>' +
      '</div>' +
    '</div>'
  );
}

listEl.innerHTML = htmlParts.join("");


}

function escapeHtml(str) {
if (str == null) return "";
return String(str)
.replace(/&/g, "&")
.replace(/</g, "<")
.replace(/>/g, ">")
.replace(/"/g, """);
}

function fetchSchedule() {
if (!state.scheduleUrl) return;
state.isLoading = true;
renderMessage("Loading live class times…", "periscope-loading");

fetch(state.scheduleUrl, { cache: "no-store" })
  .then(function (response) {
    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }
    return response.json();
  })
  .then(function (data) {
    var sessions = [];
    if (data && data.sessions && data.sessions.length) {
      sessions = data.sessions;
    } else if (data && data.session_count && data.sessions) {
      sessions = data.sessions;
    }
    state.allSessions = sessions || [];
    state.isLoading = false;
    state.hasLoadedOnce = true;
    renderSessions();
  })
  .catch(function () {
    state.isLoading = false;
    renderMessage(
      "Unable to load live class times. Please open the full class schedule.",
      "periscope-error"
    );
  });


}

function initSidebar() {
var sidebar = document.getElementById("periscope-sidebar");
if (!sidebar) return;

var listEl = sidebar.querySelector(".periscope-list");
if (!listEl) return;

var scheduleUrl = sidebar.getAttribute("data-schedule-url");
var maxSessionsAttr = sidebar.getAttribute("data-max-sessions");
var scheduleLink = sidebar.getAttribute("data-schedule-link");

var maxSessions = parseInt(maxSessionsAttr || "6", 10);
if (isNaN(maxSessions) || maxSessions <= 0) {
  maxSessions = 6;
}

state.sidebar = sidebar;
state.listEl = listEl;
state.scheduleUrl = scheduleUrl || "";
state.scheduleLink = scheduleLink || "https://coastalcprtraining.enrollware.com/schedule";
state.maxSessions = maxSessions;

// Initial load
fetchSchedule();


}

// Public API for the inline script to tell us "filter changed"
window.PeriscopeSidebar = {
refresh: function () {
if (state.isLoading && !state.hasLoadedOnce) {
return;
}
if (!state.hasLoadedOnce) {
fetchSchedule();
} else {
renderSessions();
}
}
};

if (document.readyState === "loading") {
document.addEventListener("DOMContentLoaded", initSidebar);
} else {
initSidebar();
}
})(window, document);