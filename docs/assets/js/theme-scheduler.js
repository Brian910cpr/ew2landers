// docs/assets/js/theme-scheduler.js
// Safe theme scheduler: decides ACTIVE_THEME + colors,
// but does NOT touch any <img> src or hide elements.

(function () {
  function pickThemeName(today) {
    // Simple MM-DD string for easy checks
    var m = String(today.getMonth() + 1).padStart(2, "0");
    var d = String(today.getDate()).padStart(2, "0");
    var mmdd = m + "-" + d;

    // Example: Christmas window
    if (mmdd >= "11-25" && mmdd <= "12-31") {
      return "christmas";
    }

    // Add more ranges here if you want:
    // if (mmdd >= "07-01" && mmdd <= "07-07") return "july4";

    return "default";
  }

  function applyThemeToDocument(themeName) {
    // Expose for index.html (desktop) to read
    window.ACTIVE_THEME = themeName;

    // Optional: set some CSS vars – your CSS can use these
    var root = document.documentElement;

    switch (themeName) {
      case "christmas":
        root.style.setProperty("--season-accent", "#b91c1c");
        root.style.setProperty("--season-bg", "#fef2f2");
        break;

      // Add other cases here if you add more themes above

      default:
        root.style.setProperty("--season-accent", "");
        root.style.setProperty("--season-bg", "");
        break;
    }
  }

  function initThemeScheduler() {
    var today = new Date();
    var themeName = pickThemeName(today);
    applyThemeToDocument(themeName);
    // IMPORTANT:
    // We do NOT touch images here.
    // Desktop index.html already has a THEME_IMAGES map and
    // will call applyThemeImages(window.ACTIVE_THEME || "default")
    // to handle logos/dividers/corners on its own.
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeScheduler);
  } else {
    initThemeScheduler();
  }
})();
