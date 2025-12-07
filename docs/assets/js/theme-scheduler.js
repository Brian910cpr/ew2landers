document.addEventListener("DOMContentLoaded", function () {
  var body = document.body;
  if (!body) return;

  var today = new Date();
  var month = today.getMonth() + 1; // 1–12
  var day = today.getDate();        // 1–31

  // Default theme if nothing matches
  var chosenTheme = "theme-default";

  // Simple rule set: edit THIS, not index.html
  // You can add/remove rules here easily.
  var THEME_RULES = [
    {
      theme: "theme-pancreatic",
      dates: [
        // Example: Pancreatic Cancer Awareness Day – Nov 19
        { month: 11, day: 19 }
      ]
    },
    {
      theme: "theme-halloween",
      range: {
        // Halloween week
        start: { month: 10, day: 25 },
        end:   { month: 10, day: 31 }
      }
    },
    {
      theme: "theme-christmas",
      range: {
        // Rough Thanksgiving → Dec 26 window
        start: { month: 11, day: 25 },
        end:   { month: 12, day: 26 }
      }
    }
    // Example EMS Week or Nurses Week can be added later:
    // {
    //   theme: "theme-ems-week",
    //   range: { start: {month: 5, day: 19}, end: {month: 5, day: 25} }
    // }
  ];

  function isSameDate(m, d, ruleDate) {
    return m === ruleDate.month && d === ruleDate.day;
  }

  function toOrdinal(m, d) {
    // helper for range compare (MMDD)
    return m * 100 + d;
  }

  function isInRange(m, d, range) {
    var cur  = toOrdinal(m, d);
    var sVal = toOrdinal(range.start.month, range.start.day);
    var eVal = toOrdinal(range.end.month, range.end.day);
    return cur >= sVal && cur <= eVal;
  }

  for (var i = 0; i < THEME_RULES.length; i++) {
    var rule = THEME_RULES[i];

    if (rule.dates && Array.isArray(rule.dates)) {
      for (var j = 0; j < rule.dates.length; j++) {
        if (isSameDate(month, day, rule.dates[j])) {
          chosenTheme = rule.theme;
          break;
        }
      }
      if (chosenTheme === rule.theme) break;
    }

    if (rule.range) {
      if (isInRange(month, day, rule.range)) {
        chosenTheme = rule.theme;
        break;
      }
    }
  }

  // Apply theme class on top of whatever is already there (family-BLS, etc.)
  body.classList.add(chosenTheme);

  // Optional dev logging:
  // console.log("Using theme:", chosenTheme, "for", month + "/" + day);
});
