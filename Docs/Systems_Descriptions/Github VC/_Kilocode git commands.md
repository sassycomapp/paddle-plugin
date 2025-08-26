# Git Simple Commands (PowerShell)

> Assumes you’re already in the repo folder and `origin` is set.

---

## Create a new branch (from up-to-date `main`)

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main
git switch -c work_in_progress
```

---

## Push to `origin/main` (add → commit → push)

```powershell
git switch main

# Disable local hooks safely (optional)
if (Test-Path .git\hooks) {
  if (Test-Path .git\hooks.disabled) { Remove-Item -Recurse -Force .git\hooks.disabled }
  Rename-Item .git\hooks .git\hooks.disabled
}
git config --unset core.hooksPath 2>$null

# Optional: list files > 90MB (GitHub hard limit is 100MB)
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB } |
  Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}

# Optional: disable CI on this commit (will be committed if you run it)
# if (Test-Path .github\workflows -and -not (Test-Path .github\workflows.off)) { git mv .github/workflows .github/workflows.off }

git add -A
git commit -m "your message [skip ci]" --no-verify
git push
```

---

## Push to a feature branch `work_in_progress` (add → commit → push)

```powershell
git switch work_in_progress

# Disable local hooks safely (optional)
if (Test-Path .git\hooks) {
  if (Test-Path .git\hooks.disabled) { Remove-Item -Recurse -Force .git\hooks.disabled }
  Rename-Item .git\hooks .git\hooks.disabled
}
git config --unset core.hooksPath 2>$null

# Optional: list files > 90MB
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB } |
  Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}

# Optional: disable CI on this branch commit (commits the rename)
# if (Test-Path .github\workflows -and -not (Test-Path .github\workflows.off)) { git mv .github/workflows .github/workflows.off }

git add -A
git commit -m "your message [skip ci]" --no-verify
git push -u origin HEAD
```

---

## Merge a branch into `main`

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main   # ensure local main is up to date
git merge work_in_progress        # resolve conflicts if prompted
git push
```

---

## Pull (safe, fast-forward only)

### Generic (current branch)

```powershell
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
git fetch origin
git merge --ff-only "origin/$branch"
```

### Main

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main
```

### Feature (`work_in_progress`)

```powershell
git switch work_in_progress
git fetch origin
git merge --ff-only origin/work_in_progress
```
