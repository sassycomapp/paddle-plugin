param([string]$Message = "Update [skip ci]")

# --- settings ---
$limit = 95MB
$ignores = @("*.log", "*.tmp", "*.bak", ".DS_Store", "Thumbs.db", "node_modules/", "dist/", "build/", "__pycache__/")
$defaults = @("*.zip", "*.7z", "*.rar", "*.tar", "*.tar.gz", "*.tgz", "*.bz2", "*.mp4", "*.mov", "*.mkv", "*.avi", "*.wav", "*.mp3", "*.pdf", "*.iso", "*.dll", "*.exe", "*.db", "*.sqlite", "*.parquet")

# --- helpers ---
function Ensure-Ignores {
    if (!(Test-Path .gitignore)) { New-Item -ItemType File .gitignore | Out-Null }
    $gi = Get-Content .gitignore -ErrorAction SilentlyContinue
    ($ignores | ? { $gi -notcontains $_ }) | % { Add-Content .gitignore $_ }
}

function Ensure-LFS {
    git lfs install | Out-Null
    if (!(Test-Path .gitattributes)) { New-Item -ItemType File .gitattributes | Out-Null }
    $tracked = (git lfs track --list) 2>$null
    $defaults | % { if ($tracked -notmatch [regex]::Escape($_)) { git lfs track $_ | Out-Null } }
}

function Ensure-Lfs-ForBig-Staged {
    $staged = (& git diff --cached --name-only -z) -split "`0" | ? { $_ }
    foreach ($p in $staged) {
        if (Test-Path $p) {
            $fi = Get-Item $p
            if ($fi.Length -gt $limit) {
                $rel = (Resolve-Path -Relative $fi.FullName)
                $ext = [IO.Path]::GetExtension($rel)
                $attr = & git check-attr filter -- $rel 2>$null
                if ($attr -notmatch "filter:\s*lfs") {
                    if ($ext) {
                        $pat = "*$ext"; if ((git lfs track --list) -notmatch [regex]::Escape($pat)) { git lfs track "$pat" | Out-Null }
                    }
                    else { git lfs track "$rel" | Out-Null }
                    git add .gitattributes; git add "$rel"
                }
            }
        }
    }
}

# --- flow (main) ---
git switch main
Ensure-Ignores
Ensure-LFS
git add -A
Ensure-Lfs-ForBig-Staged

if ((git diff --cached --quiet) -and (git diff --quiet)) { Write-Host "Nothing to commit. Pushing main..." }
else { git commit -m $Message --no-verify }

git push -u origin main
Write-Host "Pushed to origin/main."
