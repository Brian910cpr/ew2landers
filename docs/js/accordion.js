/* 910CPR Accordion Loader – Clean JS File */

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
    if (message) STATUS_EL.querySelector("span").textContent = message;
  }

  function showFallback() {
    setStatus("error", "Showing backup link instead.");
    FAMILIES_EL.innerHTML = "";
    FAMILIES_EL.style.display = "none";
    FALLBACK_EL.hidden = false;
  }

  function getCourseName(course) {
    return (
      course.enrollware_name ||
      course.html_title ||
      course.title ||
      course.name ||
      "Untitled"
    );
  }

  function getFamilyName(course) {
    return (
      course.family ||
      course.course_family ||
      "Other Courses"
    );
  }

  function getFamilyClass(fam) {
    var f = fam.toLowerCase();
    if (f.includes("bls")) return "cct-family-bls";
    if (f.includes("acls")) return "cct-family-acls";
    if (f.includes("pals")) return "cct-family-pals";
    if (f.includes("heartsaver")) return "cct-family-heartsaver";
    if (f.includes("hsi")) return "cct-family-hsi";
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

    row.appendChild(main);
    return row;
  }

  function buildFamilyItem(famName, courses) {
    var item = document.createElement("div");
    item.className = "cct-accordion-item " + getFamilyClass(famName);

    var header = document.createElement("button");
    header.type = "button";
    header.className = "cct-accordion-header";

    var wrap = document.createElement("div");
    wrap.className = "cct-accordion-title-wrap";

    var title = document.createElement("div");
    title.className = "cct-accordion-title";
    title.textContent = famName;

    wrap.appendChild(title);
    header.appendChild(wrap);

    var chev = document.createElement("div");
    chev.className = "cct-accordion-chevron";
    chev.textContent = "›";
    header.appendChild(chev);

    var panel = document.createElement("div");
    panel.className = "cct-accordion-panel";

    var board = document.createElement("div");
    board.className = "cct-accordion-board";

    courses.forEach(function (c) {
      board.appendChild(buildCourseRow(c));
    });

    panel.appendChild(board);
    item.appendChild(header);
    item.appendChild(panel);

    header.addEventListener("click", function () {
      var all = FAMILIES_EL.querySelectorAll(".cct-accordion-item");
      var open = item.classList.contains("cct-open");

      all.forEach(function (it) {
        it.classList.remove("cct-open");
        it.querySelector(".cct-accordion-panel").style.maxHeight = "0px";
      });

      if (!open) {
        item.classList.add("cct-open");
        panel.style.maxHeight = panel.scrollHeight + "px";
      }
    });

    return item;
  }

  function renderFamilies(data) {
    FAMILIES_EL.innerHTML = "";
    var groups = {};

    data.courses.forEach(function (course) {
      var fam = getFamilyName(course);
      if (!groups[fam]) groups[fam] = [];
      groups[fam].push(course);
    });

    Object.keys(groups).forEach(function (fam) {
      FAMILIES_EL.appendChild(buildFamilyItem(fam, groups[fam]));
    });

    // >>> Open BLS first <<<
    var blsItem = FAMILIES_EL.querySelector(".cct-family-bls");
    var firstItem = blsItem || FAMILIES_EL.querySelector(".cct-accordion-item");

    if (firstItem) {
      firstItem.classList.add("cct-open");
      var p = firstItem.querySelector(".cct-accordion-panel");
      p.style.maxHeight = p.scrollHeight + "px";
    }

    setStatus("ok", "Loaded");
  }

  function init() {
    fetch("data/schedule.json?t=" + Date.now())
      .then(r => r.json())
      .then(renderFamilies)
      .catch(showFallback);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
