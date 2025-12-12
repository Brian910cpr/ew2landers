# refresh-schedule.ps1
# Location: D:\Users\ten77\Documents\GitHub\ew2landers\refresh-schedule.ps1
#
# Run (bypass policy just for this run):
#   powershell -ExecutionPolicy Bypass -File .\refresh-schedule.ps1
#
# If you want to run it normally after setting RemoteSigned:
#   Unblock-File .\refresh-schedule.ps1
#   .\refresh-schedule.ps1

$ErrorActionPreference = "Stop"

# Repo root = folder containing THIS script (NOT the parent of that folder)
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

Write-Host "Repo: $repo"

# Ensure folders exist
New-Item -ItemType Directory -Force -Path ".\docs\data" | Out-Null
New-Item -ItemType Directory -Force -Path ".\docs\classes" | Out-Null

# Ensure Python prints UTF-8 (prevents emoji/Unicode crashes on Windows)
$env:PYTHONIOENCODING = "utf-8"

$enrollHtml = ".\docs\data\enrollware-schedule.html"

Write-Host "1) Scraping Enrollware schedule -> $enrollHtml"
Invoke-WebRequest "https://coastalcprtraining.enrollware.com/schedule" -OutFile $enrollHtml

Write-Host "2) Building schedule.json (scripts\enrollware_to_schedule.py)"
python .\scripts\enrollware_to_schedule.py

Write-Host "3) Building class landers (docs\classes\...)"
python .\scripts\build_class_landers.py

Write-Host "4) Building index.html (docs\index.html)"
python .\scripts\build-index.py .\docs\data\enrollware-schedule.html .\docs\index.html

Write-Host "5) OPTIONAL: course images (if generate_course_images.py exists)"
if (Test-Path ".\generate_course_images.py") {
  try {
    python .\generate_course_images.py
  } catch {
    Write-Host "generate_course_images.py failed (optional step)."
  }
} else {
  Write-Host "generate_course_images.py not found; skipping."
}

Write-Host ""
Write-Host "Done. Next (if you want this live on GitHub Pages):"
Write-Host "  git status"
Write-Host "  git add -A"
Write-Host "  git commit -m ""Refresh schedule + landers"""
Write-Host "  git push"
