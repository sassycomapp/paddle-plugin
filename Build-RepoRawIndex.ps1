# Build-RepoRawIndex.ps1
# Creates a complete, exact file list and raw.githubusercontent.com URL for each tracked file in the repo.
# Repo: sassycomapp/paddle-plugin  |  Branch: main

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# --- Config (hardcoded for immediate use) ---
$Owner = 'sassycomapp'
$Repo = 'paddle-plugin'
$Branch = 'main'

# --- Sanity checks: inside a Git repo? ---
$repoRoot = (& git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot) {
    throw "Not inside a Git repository. Open PowerShell in your local clone of '$Repo' and rerun."
}

# Optional: verify remote looks like expected repo
$originUrl = (& git remote get-url origin) 2>$null
if (-not $originUrl) {
    throw "No 'origin' remote found. Add it (git remote add origin <url>) or run in the correct repo."
}
if ($originUrl -notmatch [regex]::Escape("$Owner/$Repo")) {
    Write-Warning "Origin doesn't look like $Owner/$Repo (found: $originUrl). Continuing anyway..."
}

# Fetch latest branch info (quiet)
& git fetch --quiet origin $Branch

# --- Get authoritative file list from git's tree on origin/main ---
# This returns EVERY tracked file path as stored in git (no misses, no indexing quirks)
$paths = (& git ls-tree -r origin/$Branch --name-only)
if (-not $paths -or $paths.Count -eq 0) {
    throw "No files returned from 'git ls-tree'. Check that 'origin/$Branch' exists and has content."
}

# --- Prepare outputs ---
$outDir = Join-Path $repoRoot ".repo_access_index"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$fileListPath = Join-Path $outDir "repo_file_list.txt"
$rawListPath = Join-Path $outDir "repo_raw_urls.txt"
$csvPath = Join-Path $outDir "repo_index.csv"

# Clean previous outputs (ignore if open elsewhere)
foreach ($p in @($fileListPath, $rawListPath, $csvPath)) {
    if (Test-Path $p) {
        try { Remove-Item -Force $p } catch { Write-Warning "Could not remove '$p' (in use?). Will overwrite where possible." }
    }
}

# --- Helper: URL-encode each path segment but keep slashes ---
function Encode-PathForUrl([string]$relPath) {
    # Normalize any backslashes to forward slashes (git returns forward slashes already)
    $relPath = $relPath -replace '\\', '/'
    $segments = $relPath -split '/'
    $encodedSegments = $segments | ForEach-Object { [System.Uri]::EscapeDataString($_) }
    return ($encodedSegments -join '/')
}

# --- Build raw URLs and write outputs ---
$rawBase = "https://raw.githubusercontent.com/$Owner/$Repo/$Branch"
$rows = New-Object System.Collections.Generic.List[object]

# Initialize empty files to ensure writable handles
"" | Out-File -FilePath $fileListPath -Encoding UTF8
"" | Out-File -FilePath $rawListPath  -Encoding UTF8

foreach ($rel in $paths) {
    $encoded = Encode-PathForUrl $rel
    $rawUrl = "$rawBase/$encoded"

    # Append lines safely
    $rel    | Out-File -FilePath $fileListPath -Append -Encoding UTF8
    $rawUrl | Out-File -FilePath $rawListPath  -Append -Encoding UTF8

    # Collect for CSV
    $rows.Add([PSCustomObject]@{
            Path   = $rel
            RawUrl = $rawUrl
        })
}

# Write CSV (overwrite each run)
$rows | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "Done."
Write-Host "Outputs written to: $outDir"
Write-Host " - repo_file_list.txt  (all tracked repo paths)"
Write-Host " - repo_raw_urls.txt   (raw URLs, one per line)"
Write-Host " - repo_index.csv      (Path,RawUrl)"
Write-Host ""
Write-Host "Tip: share 'repo_raw_urls.txt' or 'repo_index.csv' with me and I can fetch any file reliably."
