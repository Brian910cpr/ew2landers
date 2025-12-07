// docs/assets/js/theme-scheduler.js

(function () {
  // ---- 1) Define all themes in one place ----
  // You only edit THIS object to add/change themes.

  const THEMES = {
    default: {
      name: "default",
      images: {
        logo: "assets/images/910CPR_wave.jpg",
        divider: "assets/images/theme/default-divider.png",
        corner: "assets/images/theme/default-corner.png"
      },
      colors: {
        accentMain: "#0d47a1",
        accentSoft: "rgba(13, 71, 161, 0.08)",
        accentStrong: "#2563eb",
        bgPage: "#f4f6fb"
      }
    },

    // Example: October 20–31
    halloween: {
      name: "halloween",
      images: {
        logo: "assets/images/theme/logo-halloween.png",
        divider: "assets/images/theme/divider-halloween.png",
        corner: "assets/images/theme/corner-halloween.png"
      },
      colors: {
        accentMain: "#f97316",
        accentSoft: "rgba(249, 115, 22, 0.10)",
        accentStrong: "#ea580c",
        bgPage: "#111827"
      }
    },

    // Example: December (Christmas)
    christmas: {
      name: "christmas",
      images: {
        logo: "assets/images/theme/logo-christmas.png",
        divider: "assets/images/theme/divider-christmas.png",
        corner: "assets/images/theme/corner-christmas.png"
      },
      colors: {
        accentMain: "#16a34a",
        accentSoft: "rgba(22, 163, 74, 0.10)",
        accentStrong: "#15803d",
        bgPage: "#ecfdf3"
      }
    },

    // Example: Pancreatic Cancer Awareness – November
    pancreatic: {
      name: "pancreatic",
      images: {
        logo: "assets/images/theme/logo-pancreatic.png",
        divider: "assets/images/theme/divider-pancreatic.png",
        corner: "assets/images/theme/corner-pancreatic.png"
      },
      colors: {
        accentMain: "#7c3aed",
        accentSoft: "rgba(124, 58, 237, 0.10)",
        accentStrong: "#5b21b6",
        bgPage: "#f5f3ff"
      }
    }
  };

  // ---- 2) Decide which theme should be active today ----

  function pickThemeForToday() {
    const now = new Date();
    const month = now.getMonth() + 1; // 1–12
    const day = now.getDate();

    // November: pancreatic awareness example
    if (month === 11) return "pancreatic";

    // Dec 1–31: Christmas
    if (month === 12) return "christmas";

    // Oct 20–31: Halloween
    if (month === 10 && day >= 20 && day <= 31) return "halloween";

    // Fallback
    return "default";
  }

  const activeThemeName = pickThemeForToday();
  const activeTheme = THEMES[activeThemeName] || THEMES.default;

  // Expose for other scripts (index-desktop, index-mobile, etc.)
  window.ACTIVE_THEME = activeTheme.name;

  // ---- 3) Apply images once DOM is ready ----

  function applyImages() {
    const logoEl = document.getElementById("themeLogo");
    const dividerEl = document.getElementById("themeDivider");
    const cornerEl = document.getElementById("themeCorner");

    if (logoEl && activeTheme.images.logo) {
      logoEl.src = activeTheme.images.logo;
    }
    if (dividerEl && activeTheme.images.divider) {
      dividerEl.src = activeTheme.images.divider;
    }
    if (cornerEl && activeTheme.images.corner) {
      cornerEl.src = activeTheme.images.corner;
    }
  }

  // ---- 4) Apply color variables to match theme ----

  function applyColors() {
    const root = document.documentElement;
    if (!root || !activeTheme.colors) return;

    const c = activeTheme.colors;
    if (c.accentMain) root.style.setProperty("--accent-main", c.accentMain);
    if (c.accentSoft) root.style.setProperty("--accent-soft", c.accentSoft);
    if (c.accentStrong) root.style.setProperty("--accent-strong", c.accentStrong);
    if (c.bgPage) root.style.setProperty("--bg-page", c.bgPage);
  }

  function initTheme() {
    applyColors();
    applyImages();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTheme);
  } else {
    initTheme();
  }
})();
