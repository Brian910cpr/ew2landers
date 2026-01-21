import json
from pathlib import Path

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} – 910CPR</title>
  <meta name="description" content="{description}" />
  <style>
    /* Same CSS as the single-file example, trimmed slightly for generator use */
    :root{{--brand:#0b5fa5;--brand2:#083d6b;--bg1:#fff;--bg2:#eef6ff;--text:#0b1220;--muted:#5b677a;--card:#fff;--border:#d7e4f5;--shadow:0 10px 30px rgba(0,0,0,.08);--radius:18px}}
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--text);background:linear-gradient(180deg,var(--bg1),var(--bg2));min-height:100vh}}
    .wrap{{max-width:980px;margin:0 auto;padding:22px 16px 48px}}
    header{{display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:18px}}
    .brand{{display:flex;gap:12px;align-items:center}}
    .logo{{width:44px;height:44px;border-radius:12px;background:radial-gradient(circle at 30% 30%,#2aa7ff,var(--brand2));box-shadow:var(--shadow)}}
    .titleblock h1{{font-size:1.35rem;margin:0;line-height:1.15}}
    .titleblock .sub{{margin-top:4px;color:var(--muted);font-size:.98rem}}
    .call{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
    .pill{{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border:1px solid var(--border);border-radius:999px;background:rgba(255,255,255,.8);text-decoration:none;color:var(--text);box-shadow:0 6px 18px rgba(0,0,0,.05)}}
    .pill strong{{color:var(--brand2)}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);padding:18px;margin-top:14px}}
    .hero{{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;align-items:start}}
    @media (max-width:860px){{.hero{{grid-template-columns:1fr}}}}
    .hero h2{{margin:0 0 8px;font-size:1.15rem}}
    .hero p{{margin:0 0 10px;color:var(--muted);line-height:1.4}}
    .btnGrid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:10px}}
    @media (max-width:620px){{.btnGrid{{grid-template-columns:1fr}}}}
    .bigBtn{{display:flex;flex-direction:column;gap:8px;padding:18px 16px;border-radius:18px;border:2px solid rgba(11,95,165,.25);background:linear-gradient(180deg,rgba(11,95,165,.08),rgba(11,95,165,.03));text-decoration:none;color:var(--text);cursor:pointer;transition:transform .08s ease,border-color .15s ease,background .15s ease;min-height:86px}}
    .bigBtn:hover{{transform:translateY(-1px);border-color:rgba(11,95,165,.55);background:linear-gradient(180deg,rgba(11,95,165,.12),rgba(11,95,165,.04))}}
    .bigBtn .kicker{{color:var(--brand2);font-weight:800;font-size:1.05rem}}
    .bigBtn .desc{{color:var(--muted);font-size:.95rem;line-height:1.35}}
    .stepTitle{{display:flex;align-items:center;gap:10px;margin:0 0 10px;font-size:1.05rem}}
    .badge{{width:28px;height:28px;border-radius:10px;background:rgba(11,95,165,.12);display:grid;place-items:center;color:var(--brand2);font-weight:900}}
    .locations{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px}}
    @media (max-width:720px){{.locations{{grid-template-columns:1fr}}}}
    .locBtn{{padding:14px 14px;border-radius:16px;border:1px solid var(--border);background:#fff;cursor:pointer;text-align:left;box-shadow:0 6px 16px rgba(0,0,0,.05);transition:transform .08s ease,border-color .15s ease}}
    .locBtn:hover{{transform:translateY(-1px);border-color:rgba(11,95,165,.55)}}
    .locBtn .locName{{font-weight:800}}
    .locBtn .locMeta{{color:var(--muted);font-size:.92rem;margin-top:4px}}
    .muted{{color:var(--muted);font-size:.92rem}}
    .divider{{height:1px;background:var(--border);margin:14px 0}}
    footer{{margin-top:18px;color:var(--muted);font-size:.9rem;line-height:1.4}}
  </style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="logo" aria-hidden="true"></div>
      <div class="titleblock">
        <h1>{title}</h1>
        <div class="sub">{subtitle}</div>
      </div>
    </div>
    <div class="call">
      <a class="pill" href="tel:+19103955193"><strong>Call</strong> (910) 395-5193</a>
      <a class="pill" href="https://coastalcprtraining.enrollware.com/schedule"><strong>All Dates</strong> Enrollware Schedule</a>
    </div>
  </header>

  <div class="card">
    <div class="hero">
      <div>
        <h2>Choose your option</h2>
        <p>{intro}</p>
        <div class="btnGrid" id="formatButtons"></div>
        <div class="divider"></div>
        <div id="locationStep" style="display:none;">
          <div class="stepTitle"><span class="badge">2</span> Where do you want to take it?</div>
          <div class="locations" id="locationButtons"></div>
          <p class="muted" style="margin-top:10px;">Bookmark this page — it’s designed for phone calls and quick booking.</p>
        </div>
      </div>
      <div>
        <h2>Fast routing</h2>
        <p class="muted">This page routes you to the correct Enrollware filter for inventory + checkout.</p>
      </div>
    </div>

    <footer>
      910CPR • Router lander → Enrollware schedule filter
    </footer>
  </div>
</div>

<script>
const CONFIG = {config_json};

let selectedFormat = null;

function buildUrl(locationId, courseId){{
  const u = new URL(CONFIG.enrollwareBase);
  u.searchParams.set("location", locationId);
  u.searchParams.set("course", courseId);
  return u.toString();
}}

function escapeHtml(s){{
  return String(s ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll("\\"","&quot;")
    .replaceAll("'","&#039;");
}}

function renderFormats(){{
  const box = document.getElementById("formatButtons");
  box.innerHTML = "";
  CONFIG.formats.forEach(fmt => {{
    const btn = document.createElement("button");
    btn.className = "bigBtn";
    btn.type = "button";
    btn.innerHTML = `
      <div class="kicker">${{escapeHtml(fmt.label)}}</div>
      <div class="desc">${{escapeHtml(fmt.desc)}}</div>
    `;
    btn.addEventListener("click", () => onPickFormat(fmt));
    box.appendChild(btn);
  }});
}}

function onPickFormat(fmt){{
  selectedFormat = fmt;
  const availableLocationIds = Object.keys(fmt.courseByLocation || {{}})
    .filter(locId => CONFIG.locations[locId] && fmt.courseByLocation[locId]);

  if(availableLocationIds.length === 1){{
    const locId = availableLocationIds[0];
    const courseId = fmt.courseByLocation[locId];
    window.location.href = buildUrl(locId, courseId);
    return;
  }}

  document.getElementById("locationStep").style.display = "block";
  renderLocations(availableLocationIds);
}}

function renderLocations(locationIds){{
  const box = document.getElementById("locationButtons");
  box.innerHTML = "";

  locationIds.forEach(locId => {{
    const loc = CONFIG.locations[locId];
    const courseId = selectedFormat.courseByLocation[locId];
    const url = buildUrl(locId, courseId);

    const b = document.createElement("button");
    b.className = "locBtn";
    b.type = "button";
    b.innerHTML = `
      <div class="locName">${{escapeHtml(loc.name)}}</div>
      <div class="locMeta">${{escapeHtml(loc.meta || "")}}</div>
    `;
    b.addEventListener("click", () => window.location.href = url);
    box.appendChild(b);
  }});
}}

renderFormats();
</script>
</body>
</html>
"""

def main():
  config_path = Path("landers.config.json")
  out_root = Path("docs/landers")
  out_root.mkdir(parents=True, exist_ok=True)

  cfg = json.loads(config_path.read_text(encoding="utf-8"))

  for lander in cfg["landers"]:
    slug = lander["slug"].strip().lower()
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build per-lander JS config
    js_cfg = {
      "enrollwareBase": lander.get("enrollwareBase", "https://coastalcprtraining.enrollware.com/schedule"),
      "formats": lander["formats"],
      "locations": lander["locations"]
    }

    html = TEMPLATE.format(
      title=lander["title"],
      description=lander.get("description", lander["title"] + " – 910CPR"),
      subtitle=lander.get("subtitle", "Pick your option → pick your location → book"),
      intro=lander.get("intro", "Choose the option that matches what you need, then book on Enrollware."),
      config_json=json.dumps(js_cfg, ensure_ascii=False)
    )

    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote: {out_dir / 'index.html'}")

if __name__ == "__main__":
  main()
