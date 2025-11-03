# tools/build.ps1  (PowerShell 5.1–compatible: no ternary, no dot-chaining line breaks)
$ErrorActionPreference = "Stop"

# Determine repo root whether the script is RUN from a file or PASTED
$scriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($scriptPath)) {
  $root = (Get-Location).Path
} else {
  $root = Split-Path -Parent $scriptPath
}

$docs = Join-Path $root "docs"
$data = Join-Path $docs "data"
$snapshot = Join-Path $data "enrollware-schedule.html"
if (-not (Test-Path $snapshot)) { throw "Missing $snapshot" }

function Read-Template($name){ Get-Content -Raw -Encoding UTF8 (Join-Path $root "tools\templates\$name") }
$tplBase     = Read-Template "base.html"
$tplCourse   = Read-Template "course.html"
$tplSession  = Read-Template "session.html"
$tplLocation = Read-Template "location.html"

function Slug($s){
  $s -replace '[^\p{L}\p{Nd}]+' , '-' -replace '[-]+' , '-' -replace '^-|-$','' |
  ForEach-Object { $_.ToLowerInvariant() }
}

# Org for JSON-LD
$orgPath = Join-Path $data "org.json"
$org = $null
if (Test-Path $orgPath) { $org = Get-Content -Raw -Encoding UTF8 $orgPath | ConvertFrom-Json }

# Read snapshot
$html = Get-Content -Raw -Encoding UTF8 $snapshot

# Find panels
$panelRegex = [regex]'(?s)<div class="enrpanel".*?<\/div>\s*<\/div>\s*'
$panels = @()
$matches = $panelRegex.Matches($html)
foreach($m in $matches){ $panels += $m.Value }

# Extract course info
$courses = @()
foreach($p in $panels){
  $id = [regex]::Match($p,'(?:id|name)="(ct\d+)"').Groups[1].Value
  $title = ([regex]::Match($p,'(?s)<(?:div class="enrpanel-heading"|h1|h2|h3|h4)[^>]*>(.*?)</(?:div|h1|h2|h3|h4)>')).Groups[1].Value.Trim()
  if(-not $title){ continue }

  $bodyHtml = ([regex]::Match($p,'(?s)<div class="enrpanel-body">(.*?)</div>')).Groups[1].Value
  $descHtml = [regex]::Replace($bodyHtml,'(?s)<ul class="enrclass-list">.*?</ul>','').Trim()
  $ulHtml = ([regex]::Match($p,'(?s)<ul class="enrclass-list">(.*?)</ul>')).Groups[0].Value
  if(-not $ulHtml){ continue }

  $courses += [pscustomobject]@{
    Id = $id
    Title = $title
    DescHtml = $descHtml
    UlHtml = $ulHtml
  }
}

# Output dirs
$coursesDir  = Join-Path $docs "courses"
$sessionsDir = Join-Path $docs "sessions"
$locationsDir= Join-Path $docs "locations"
New-Item -ItemType Directory -Force -Path $coursesDir, $sessionsDir, $locationsDir | Out-Null

function Write-Page($outPath, $title, $innerHtml){
  $htmlOut = $tplBase.Replace("{{TITLE}}",$title).Replace("{{BODY}}",$innerHtml)
  $dir = Split-Path -Parent $outPath
  if(-not (Test-Path $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $htmlOut | Out-File -Encoding UTF8 $outPath
}

# Build course pages & collect sessions
$sessions = @()
foreach($c in $courses){
  $courseSlug = Slug($c.Title)
  $courseDir = Join-Path $coursesDir $courseSlug
  New-Item -ItemType Directory -Force -Path $courseDir | Out-Null

  $courseUrl = "https://coastalcprtraining.enrollware.com/schedule#$($c.Id)"
  $courseInner = $tplCourse.Replace("{{COURSE_TITLE}}",$c.Title).Replace("{{COURSE_DESC_HTML}}",$c.DescHtml).Replace("{{COURSE_DATES_UL}}",$c.UlHtml).Replace("{{COURSE_CT_URL}}",$courseUrl)
  Write-Page (Join-Path $courseDir "index.html") $c.Title $courseInner

  # Pull li/a -> sessions
  $liRegex = [regex]'(?s)<li>\s*<a[^>]*href="([^"]+enroll\?id=(\d+))"[^>]*>(.*?)</a>\s*</li>'
  $lim = $liRegex.Matches($c.UlHtml)
  foreach($m in $lim){
    $href = $m.Groups[1].Value
    $enrollId = $m.Groups[2].Value
    $text = ($m.Groups[3].Value -replace '<span>',' | ' -replace '</span>','' -replace '<.*?>','').Trim()

    # Split date vs location (no ternary; PS 5.1 safe)
    $parts   = $text -split '\|'
    $dateStr = $parts[0].Trim()
    $locStr  = ""
    if ($parts.Count -ge 2) { $locStr = $parts[1].Trim() }

    # Parse date -> folder path
    $dt = $null
    try{ $dt = [datetime]::Parse($dateStr) }catch{}
    if($dt -ne $null){
      $y = $dt.ToString('yyyy'); $mth = $dt.ToString('MM'); $d = $dt.ToString('dd')
      $sessSlug = (Slug("$($c.Title) $locStr $dateStr")) + "-$enrollId"
      $outDir = Join-Path (Join-Path (Join-Path $sessionsDir $y) $mth) $d
      New-Item -ItemType Directory -Force -Path $outDir | Out-Null

      # JSON-LD Event
      $eventObj = @{
        "@context" = "https://schema.org"
        "@type"    = "Event"
        "name"     = $c.Title
        "startDate"= $dt.ToString("s")
        "eventAttendanceMode" = "https://schema.org/OfflineEventAttendanceMode"
        "location" = @{
          "@type" = "Place"
          "name"  = $locStr
          "address" = $locStr
        }
        "offers" = @{
          "@type" = "Offer"
          "url"   = $href
          "availability" = "https://schema.org/InStock"
        }
      }
      if ($org) {
        $eventObj["organizer"] = @{
          "@type" = "Organization"
          "name"  = $org.name
          "url"   = $org.url
          "telephone" = $org.telephone
        }
      }
      $event = $eventObj | ConvertTo-Json -Depth 6

      $inner = $tplSession.Replace("{{COURSE_TITLE}}",$c.Title).Replace("{{DATE_STR}}",$dateStr).Replace("{{LOCATION_STR}}",$locStr).Replace("{{ENROLL_URL}}",$href).Replace("{{EVENT_JSON}}",$event)

      $outFile = Join-Path $outDir ($sessSlug + ".html")
      Write-Page $outFile $c.Title $inner

      # Track for location rollups
      if($locStr){
        $cityState = $locStr
        if($locStr -match '([A-Z]{2})\s*-\s*([^:]+)'){ $cityState = ($Matches[2].Trim() + ", " + $Matches[1]) }
        $sessions += [pscustomobject]@{
          CityState = $cityState
          Url = ($outFile.Replace($docs,'') -replace '\\','/').TrimStart('/')
        }
      }
    }
  }
}

# Simple location pages
$sessionsByLoc = $sessions | Group-Object CityState
foreach($g in $sessionsByLoc){
  if([string]::IsNullOrWhiteSpace($g.Name)){ continue }
  $locSlug = Slug($g.Name)
  $locDir = Join-Path $locationsDir $locSlug
  New-Item -ItemType Directory -Force -Path $locDir | Out-Null
  $list = ""
  foreach($s in $g.Group){
    $list += "<li><a href=""/ew2landers/$($s.Url)"">$($s.Url)</a></li>`n"
  }
  $inner = $tplLocation.Replace("{{CITY_STATE}}",$g.Name).Replace("{{CLASS_LIST}}",$list)
  Write-Page (Join-Path $locDir "index.html") "Classes in $($g.Name)" $inner
}

# Sitemap
$sitemap = @()
$sitemap += "https://brian90cpr.github.io/ew2landers/"
Get-ChildItem -Path $docs -Filter *.html -Recurse | ForEach-Object {
  $rel = $_.FullName.Replace($docs,'').Replace('\','/').TrimStart('/')
  if($rel -eq "index.html"){ return }
  $sitemap += "https://brian90cpr.github.io/ew2landers/$rel"
}
$siteXml = "<?xml version=""1.0"" encoding=""UTF-8""?>`n<urlset xmlns=""http://www.sitemaps.org/schemas/sitemap/0.9"">`n"
foreach($u in $sitemap){ $siteXml += "  <url><loc>$u</loc></url>`n" }
$siteXml += "</urlset>`n"
$siteXml | Out-File -Encoding UTF8 (Join-Path $docs "sitemap.xml")

Write-Host "Build complete."
