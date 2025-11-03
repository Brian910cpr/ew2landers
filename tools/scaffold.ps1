# tools/scaffold.ps1
$ErrorActionPreference = "Stop"

# Repo root
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
function Mk($p){ $full = Join-Path $root $p; if(-not (Test-Path $full)){ New-Item -ItemType Directory -Path $full | Out-Null } }
function WriteIfMissing($rel,$content){ $full=Join-Path $root $rel; if(-not (Test-Path $full)){ $content | Out-File -Encoding UTF8 $full } }

# Core skeleton
Mk "docs"; Mk "docs\data"; Mk "docs\assets\css"; Mk "docs\assets\js"
Mk "docs\courses"; Mk "docs\sessions"; Mk "docs\locations"; Mk "docs\ooh"
Mk ".github\workflows"; Mk "tools\templates"

# 404 + robots
WriteIfMissing "docs\404.html" @"
<!doctype html><meta charset='utf-8'><title>Not found</title>
<h1>Page not found</h1><p>Try the <a href='/ew2landers/'>home page</a>.</p>
"@

WriteIfMissing "docs\robots.txt" @"
User-agent: *
Allow: /
Sitemap: https://brian90cpr.github.io/ew2landers/sitemap.xml
"@

# Org (for later JSON-LD)
WriteIfMissing "docs\data\org.json" @"
{
  "name": "910CPR LLC",
  "url": "https://brian90cpr.github.io/ew2landers/",
  "telephone": "+1-910-395-5193",
  "logo": "https://www.enrollware.com/sitefiles/coastalcprtraining/910cpr_round.png",
  "address": "4902 Merlot Court, Wilmington, NC 28409"
}
"@

# Addresses privacy list (can edit later)
WriteIfMissing "docs\data\addresses.json" @"
[
  "325 Sound Rd",
  "111 S Wright St",
  "115-3 Hinton Ave",
  "4018 Shipyard Blvd",
  "809 Gum Branch Rd",
  "4902 Merlot Ct"
]
"@

# Optional mapping files
WriteIfMissing "docs\data\course-aliases.json" "{}"
WriteIfMissing "docs\data\course-images.json" "{}"
WriteIfMissing "docs\data\ooh-map.json" "{}"

# Minimal CSS
WriteIfMissing "docs\assets\css\site.css" @"
body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#f6f9fc;color:#0a1b2b}
.wrap{max-width:1000px;margin:auto;padding:20px}
a{color:#0b66c3}
"@

# Placeholder sitemap (will be overwritten by build)
WriteIfMissing "docs\sitemap.xml" @"
<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
  <url><loc>https://brian90cpr.github.io/ew2landers/</loc></url>
</urlset>
"@

# TEMPLATES (for generator)
WriteIfMissing "tools\templates\base.html" @"
<!doctype html>
<html lang='en'><head>
<meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>{{TITLE}}</title>
<link rel='stylesheet' href='/ew2landers/assets/css/site.css'/>
<script async src='https://www.googletagmanager.com/gtag/js?id=G-45PBWBK7KR'></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config','G-45PBWBK7KR');</script>
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f)})(window,document,'script','dataLayer','GTM-K58Z4XD');</script>
</head><body><div class='wrap'>
{{BODY}}
</div></body></html>
"@

WriteIfMissing "tools\templates\course.html" @"
<h1>{{COURSE_TITLE}}</h1>
<div class='desc'>{{COURSE_DESC_HTML}}</div>
<ul class='enrclass-list'>
{{COURSE_DATES_UL}}
</ul>
<p><a href='{{COURSE_CT_URL}}'>See all dates on Enrollware</a></p>
"@

WriteIfMissing "tools\templates\session.html" @"
<h1>{{COURSE_TITLE}}</h1>
<p><strong>{{DATE_STR}}</strong></p>
<p>{{LOCATION_STR}}</p>
<p><a href='{{ENROLL_URL}}'>Register now</a></p>
<script type='application/ld+json'>
{{EVENT_JSON}}
</script>
"@

WriteIfMissing "tools\templates\location.html" @"
<h1>Classes in {{CITY_STATE}}</h1>
<ul>{{CLASS_LIST}}</ul>
"@

WriteIfMissing "tools\templates\ooh.html" @"
<h1>{{OOH_TITLE}}</h1>
<p>{{OOH_BLURB}}</p>
<h2>Recommended certifications</h2>
<ul>{{COURSE_LINKS}}</ul>
<h2>Upcoming sessions</h2>
<ul>{{SESSION_LINKS}}</ul>
"@

Write-Host "Scaffold complete.

NEXT:
1) Put your hub at docs\index.html (use the HTML file I sent).
2) Save Enrollware schedule to docs\data\enrollware-schedule.html
3) Run tools\build.ps1 to generate landers and sitemap."
