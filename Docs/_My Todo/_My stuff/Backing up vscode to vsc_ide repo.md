Create a new private repo on GitHub called vsc_ide.

Clone it locally:

git clone https://github.com/sassycomapp/vsc_ide C:\vsc_ide


Create a new file C:\vsc_ide\run_audit.ps1 and paste in the full script below:

# ==== CONFIG ====
$AuditRepo = "C:\vsc_ide"
$Roots = @(
  "C:\_1mybizz\paddle-plugin"
)

# ==== PREP ====
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $AuditRepo | Out-Null
New-Item -ItemType Directory -Force -Path "$AuditRepo\user" | Out-Null
New-Item -ItemType Directory -Force -Path "$AuditRepo\local_data" | Out-Null

# VS Code version + extensions
if (Get-Command code -ErrorAction SilentlyContinue) {
  code --version | Out-File -Encoding utf8 "$AuditRepo\vscode-version.txt"
  code --list-extensions | Sort-Object -Unique | Out-File -Encoding ascii "$AuditRepo\extensions.txt"
}

# VS Code User settings snapshot
$cfg = Join-Path $env:APPDATA "Code\User"
robocopy $cfg "$AuditRepo\user" /MIR /XD Workspaces workspaceStorage History Backups GlobalStorage `
  /XF storage.json state.vscdb state.vscdb-wal state.vscdb-shm | Out-Null

# Targeted copy of extension local data
$gs = Join-Path $cfg "globalStorage"
$targets = @("*kilocode*","*cline*","*ag2*","*orchestrator*","*memory*","*mcp*","*chromadb*")
foreach ($pat in $targets) {
  Get-ChildItem -Path $gs -Directory -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
    robocopy $_.FullName (Join-Path "$AuditRepo\local_data" $_.Name) /E | Out-Null
  }
}

# Build file manifest
$excludeDirs = @(".git","node_modules",".venv","venv","dist","build","__pycache__",".mypy_cache",".pytest_cache",".ruff_cache",".idea",".vscode",".cache")
$rows = New-Object System.Collections.Generic.List[Object]
$now = Get-Date
$recentDays = 21

function GitRootStatus($root) {
  if (Test-Path (Join-Path $root ".git")) {
    $tracked = git -C $root ls-files 2>$null
    $untracked = git -C $root ls-files -o --exclude-standard 2>$null
    $modified = git -C $root status --porcelain 2>$null | Where-Object { $_ -match "^\s*M\s" } | ForEach-Object { ($_ -split "\s+",3)[-1] }
    return [pscustomobject]@{
      Tracked = $tracked
      Untracked = $untracked
      Modified = $modified
    }
  }
  return $null
}

$gitCache = @{}
foreach ($root in $Roots) {
  if (-not (Test-Path $root)) { continue }
  $gitCache[$root] = GitRootStatus $root

  Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
      $rel = $_.FullName.Substring($root.Length).TrimStart('\','/')
      -not ($excludeDirs | ForEach-Object { $rel -split '[\\/]' | Where-Object { $_ -ieq $_ } } )
    } |
    ForEach-Object {
      $relPath = $_.FullName.Substring($root.Length).TrimStart('\','/')
      $ext = $_.Extension.ToLower()
      $sizeKB = [math]::Round($_.Length/1KB,2)
      $created = $_.CreationTime
      $modified = $_.LastWriteTime

      $tracked = $false; $untracked = $false; $modifiedFlag = $false
      $gitInfo = $gitCache[$root]
      if ($gitInfo) {
        if ($gitInfo.Tracked -contains $relPath) { $tracked = $true }
        if ($gitInfo.Untracked -contains $relPath) { $untracked = $true }
        if ($gitInfo.Modified -contains $relPath) { $modifiedFlag = $true }
      }

      $name = $_.Name.ToLower()
      $suspectName = ($name -match '(^|[_\-])(tmp|temp|scratch|draft|copy|old|backup|bak|test|experiment|sample|junk)([_\-]|\.|$)')
      $suspectExt  = $ext -in @(".ipynb",".md",".txt",".json",".http",".rest",".log")
      $recent = ($modified -ge $now.AddDays(-$recentDays))
      $large = $_.Length -gt 2MB

      $suspect = ($untracked -and $recent -and ($suspectName -or $suspectExt)) -or ($untracked -and $large -and $recent)

      $rows.Add([pscustomobject]@{
        Root        = $root
        RelPath     = $relPath
        Ext         = $ext
        SizeKB      = $sizeKB
        Created     = $created
        Modified    = $modified
        Tracked     = $tracked
        Untracked   = $untracked
        ModifiedGit = $modifiedFlag
        Suspect     = $suspect
      })
    }
}

$csv = Join-Path $AuditRepo "kilocode_audit_report.csv"
$rows | Sort-Object Root, Suspect -Descending, Modified -Descending | Export-Csv -NoTypeInformation -Encoding UTF8 $csv

# Summary
$summary = Join-Path $AuditRepo "kilocode_summary.md"
$total = $rows.Count
$sus = ($rows | Where-Object Suspect).Count
$untrackedCount = ($rows | Where-Object Untracked).Count
$modifiedCount = ($rows | Where-Object ModifiedGit).Count
@"
# KiloCode Audit Summary

- Total files scanned: $total
- Suspect (untracked & recent & name/ext heuristic): $sus
- Untracked files: $untrackedCount
- Modified tracked files: $modifiedCount
- Roots:
$(($Roots | ForEach-Object {"  - $_"}) -join "`n")

## Next steps
1) Review kilocode_audit_report.csv (filter by `Suspect = True`).
"@ | Out-File -Encoding utf8 $summary

Write-Host "Audit complete → $AuditRepo"


Run PowerShell as Administrator:

Set-ExecutionPolicy RemoteSigned -Scope Process
cd C:\vsc_ide
.\run_audit.ps1


Commit and push results:

cd C:\vsc_ide
git add .
git commit -m "IDE audit snapshot"
git push origin main


Enable the GitHub connector here and grant access to sassycomapp/vsc_ide.

Notify me once done.