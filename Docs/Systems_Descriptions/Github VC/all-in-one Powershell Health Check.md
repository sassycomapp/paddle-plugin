all-in-one PowerShell health check

Paste the block below into your terminal (PowerShell):
***************************
# --- Git/GitHub quick health check for sassycomapp/paddle-plugin ---
$ErrorActionPreference = "SilentlyContinue"
$repoPath = "C:\_1mybizz\paddle-plugin"
Set-Location $repoPath

Write-Host "`n[1/9] Fetch & prune remotes..." -ForegroundColor Cyan
git fetch origin --prune | Out-Null

Write-Host "[2/9] Current branch & upstream..." -ForegroundColor Cyan
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$upstream = (git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null).Trim()
if ($LASTEXITCODE -ne 0 -or -not $upstream) {
  Write-Host "  ✗ No upstream set for '$branch' (first push should use: git push -u origin HEAD)" -ForegroundColor Red
} else {
  Write-Host "  ✔ On '$branch' tracking '$upstream'" -ForegroundColor Green
}

Write-Host "[3/9] Working tree clean?" -ForegroundColor Cyan
$wt = git status --porcelain
if (-not $wt) { Write-Host "  ✔ Clean" -ForegroundColor Green } else {
  Write-Host "  ✗ Uncommitted changes present:" -ForegroundColor Yellow
  $wt | ForEach-Object { "    $_" }
}

Write-Host "[4/9] Local main == origin/main?" -ForegroundColor Cyan
$localMain  = (git rev-parse main 2>$null).Trim()
$remoteMain = (git rev-parse origin/main 2>$null).Trim()
if ($localMain -and $remoteMain -and $localMain -eq $remoteMain) {
  Write-Host "  ✔ main is up to date with origin/main" -ForegroundColor Green
} else {
  Write-Host "  ✗ main differs from origin/main — run: git switch main; git pull" -ForegroundColor Yellow
}

Write-Host "[5/9] Any lingering submodules?" -ForegroundColor Cyan
$subs = git ls-files -s | Select-String " 160000 "
if ($subs) { Write-Host "  ✗ Found submodule entries. Investigate:" -ForegroundColor Red; $subs } else { Write-Host "  ✔ No submodules" -ForegroundColor Green }

Write-Host "[6/9] Remote default branch (HEAD) ..." -ForegroundColor Cyan
$remoteShow = git remote show origin 2>$null
if ($remoteShow -match "HEAD branch: main") {
  Write-Host "  ✔ origin default branch is main" -ForegroundColor Green
} else {
  Write-Host "  ✗ origin default branch is not 'main' (check GitHub → Settings → Branches)" -ForegroundColor Yellow
}

Write-Host "[7/9] LFS status (if installed)..." -ForegroundColor Cyan
$lfs = git lfs status 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Host "  ✔ Git LFS reachable. Summary:" -ForegroundColor Green
  ($lfs -split "`n" | Select-Object -First 3) | ForEach-Object { "    $_" }
} else {
  Write-Host "  (info) Git LFS not installed/used here." -ForegroundColor DarkGray
}

Write-Host "[8/9] Hooks present?" -ForegroundColor Cyan
$hooks = Get-ChildItem -File .git\hooks 2>$null | Where-Object { $_.Name -notlike "*.sample" }
if ($hooks) {
  Write-Host "  ⚠ Hooks found (may block commits):" -ForegroundColor Yellow
  $hooks | ForEach-Object { "    " + $_.Name }
  Write-Host "    Tip: bypass once with: git commit -m \"...\" --no-verify" -ForegroundColor DarkGray
} else {
  Write-Host "  ✔ No active hooks" -ForegroundColor Green
}

Write-Host "[9/9] Ahead/behind vs origin for current branch..." -ForegroundColor Cyan
$tracking = (git rev-list --left-right --count "$upstream...HEAD" 2>$null).Trim()
if ($tracking) {
  $parts = $tracking -split "\s+"
  Write-Host ("  ✔ Ahead by {0}, behind by {1}" -f $parts[1], $parts[0]) -ForegroundColor Green
} else {
  Write-Host "  (info) No upstream to compare." -ForegroundColor DarkGray
}

Write-Host "`nDone."
**********************************

How to read it

All green checks → you’re good to go.

Yellow/Red lines will tell you exactly which command to run to fix each item.