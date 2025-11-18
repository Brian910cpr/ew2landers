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

// Pre-process multi-value course_id filters
var courseIdList = null;
if (type === "course_id") {
courseIdList = String(value)
.split(",")
.map(function (v) { return v.trim(); })
.filter(function (v) { return v.length > 0; });
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
if (!courseIdList || !courseIdList.length) { return true; }
var sid = (s.course_id != null) ? String(s.course_id) : "";
return courseIdList.indexOf(sid) !== -1;
}
if (type === "location_contains") {
return (s.location || "").indexOf(value) !== -1;
}
// Unknown filter type → don’t exclude the class
return true;
});
}