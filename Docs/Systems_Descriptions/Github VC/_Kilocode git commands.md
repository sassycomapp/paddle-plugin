# Git Simple Commands (PowerShell)

> Assumes you’re already in the repo folder and `origin` is set.

## Disable local hooks once and be done:

if (Test-Path .git\hooks) {
  if (Test-Path .git\hooks.disabled) { Remove-Item -Recurse -Force .git\hooks.disabled }
  Move-Item -Path .git\hooks -Destination .git\hooks.disabled
}
git config --unset core.hooksPath 2>$null



## Disable Global hooks once and be done:

if (Test-Path .git\hooks) {
  if (Test-Path .git\hooks.disabled) { Remove-Item -Recurse -Force .git\hooks.disabled }
  Move-Item -Path .git\hooks -Destination .git\hooks.disabled
}
git config --global --unset core.hooksPath


<<<Run those once per repo, not on every push.>>>

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

# Optional: list files > 90MB
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB } |
  Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}

git add -A
git commit -m "your message [skip ci]" --no-verify
git push
```

---

## Push to a feature branch `work_in_progress` (add → commit → push)

```powershell
git switch work_in_progress

# Optional: list files > 90MB
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB } |
  Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}

git add -A
git commit -m "your message [skip ci]" --no-verify
git push
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
------------------------------

Basics
# See what changed (short/clean)
git status -sb

# Stage everything (or a file)
git add -A
git add path/to/file

# Commit with a message
git commit -m "feat: short summary"

# First push for a new branch (sets upstream)
git push -u origin HEAD
# Later pushes (same branch)
git push

Update your local copy (safe)
# Fetch remote updates
git fetch origin

# Fast-forward only (won’t overwrite local work)
git merge --ff-only origin/main            # when on main
git merge --ff-only origin/work_in_progress

Branches
# List branches (local)
git branch
# List with tracking info
git branch -vv

# Create & switch
git switch -c work_in_progress
# Switch to existing
git switch main

# Delete local branch (after merge)
git branch -d work_in_progress
# Delete remote branch
git push origin --delete work_in_progress

Merge
git switch main
git fetch origin
git merge --ff-only origin/main   # update local main
git merge work_in_progress        # merge your feature in
git push

Open a Pull Request (simple)

Push your branch, then on GitHub click “Compare & pull request” (base: main, compare: your branch).

(Optional, with GitHub CLI if you use it)

gh pr create --base main --head work_in_progress --fill --web

Inspect & compare
# Recent commits (one line)
git log --oneline -n 10
# Graph view
git log --oneline --graph --decorate --all

# Diffs
git diff                    # unstaged changes
git diff --staged           # what’s about to be committed
git diff main..work_in_progress

Stash (quickly shelve work)
git stash            # save dirty state
git stash list
git stash apply      # re-apply latest

File ops
git mv old/path new/path     # rename/move and stage
git rm path/to/file          # delete and stage

# Restore a file from last commit
git restore --source=HEAD -- path/to/file

Remotes
git remote -v                # show origins
git remote show origin       # tracking info

Tags (optional)
git tag v0.1.0
git push origin v0.1.0

Quick “Daily” sequences

Start a new feature:

git switch main
git fetch origin
git merge --ff-only origin/main
git switch -c work_in_progress


Save progress to your feature branch:

git add -A
git commit -m "docs: update notes"
git push -u origin HEAD   # first time
# later: git push


Sync your current branch with remote (safe):

git fetch origin
git merge --ff-only origin/$(git rev-parse --abbrev-ref HEAD)

Caution (rare, destructive)
git reset --hard HEAD      # throws away local changes
git clean -fd              # removes untracked files/folders


Use those only if you’re sure.

If you want, I can bundle any subset of these into ready-to-run PowerShell snippets for your exact work_in_progress flow.

You said:
Yes that will be excellent
ChatGPT said:
Thought for 19s

Awesome—here are ready-to-run PowerShell shortcuts tailored to your repo and branch.
Paste these into a file (e.g. C:\_1mybizz\paddle-plugin\git-shortcuts.ps1) or your PS profile, then dot-source it:

. C:\_1mybizz\paddle-plugin\git-shortcuts.ps1

git-shortcuts.ps1
# --- Config ---
$RepoPath = "C:\_1mybizz\paddle-plugin"
$Feature  = "work_in_progress"

function Go-Repo {
  if (Test-Path $RepoPath) { Set-Location $RepoPath }
}

function Start-Feature {
  Go-Repo
  git switch main
  git fetch origin
  git merge --ff-only origin/main
  if (git rev-parse --verify $Feature 2>$null) {
    git switch $Feature
  } else {
    git switch -c $Feature
  }
}

function Push-Feature([string]$Message="wip") {
  Go-Repo
  git switch $Feature
  git add -A
  git commit -m "$Message [skip ci]" --no-verify
  git push -u origin HEAD
}

function Push-Main([string]$Message="update") {
  Go-Repo
  git switch main
  git add -A
  git commit -m "$Message [skip ci]" --no-verify
  git push
}

function Sync-Current {
  Go-Repo
  $b = (git rev-parse --abbrev-ref HEAD).Trim()
  git fetch origin
  git merge --ff-only origin/$b
}

function Merge-FeatureToMain {
  Go-Repo
  git switch main
  git fetch origin
  git merge --ff-only origin/main
  git merge $Feature
  git push
}

function Open-PR {
  Go-Repo
  $remote = (git remote get-url origin)
  if ($remote -match "github\.com[:/](.+?)/(.+?)(\.git)?$") {
    $owner=$matches[1]; $repo=$matches[2]
    $url = "https://github.com/$owner/$repo/compare/main...$Feature?expand=1"
    Write-Host "Open this to create the PR:" -f Cyan
    Write-Host $url -f Yellow
    Start-Process $url | Out-Null
  } else {
    Write-Host "Could not parse origin URL." -f Red
  }
}

function Git-Health {
  Go-Repo
  Write-Host "== Status ==" -f Cyan
  git status -sb
  Write-Host "`n== Branches ==" -f Cyan
  git branch -vv
  Write-Host "`n== HEAD vs origin ==" -f Cyan
  Write-Host "Local HEAD:   $(git rev-parse HEAD)"
  Write-Host "Origin main:  $(git rev-parse origin/main 2>$null)"
  Write-Host "Origin $Feature: $(git rev-parse origin/$Feature 2>$null)"
}

function Check-LargeFiles([int]$MB=90) {
  Go-Repo
  Get-ChildItem -Recurse -File |
    Where-Object { $_.Length -gt ($MB*1MB) } |
    Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}
}

How to use (super short)
# 1) Create/switch feature from up-to-date main
Start-Feature

# 2) Save progress to feature branch
Push-Feature "docs: update notes"

# 3) Open Pull Request in browser
Open-PR

# 4) Fast-forward sync the branch you’re on (safe)
Sync-Current

# 5) Merge feature into main (after PR or if you just want to do it locally)
Merge-FeatureToMain

# 6) Commit/push directly to main (if you need)
Push-Main "chore: tweak config"

# 7) Quick health snapshot
Git-Health

# 8) Optional: scan for big files (>90MB)
Check-LargeFiles 90


That’s it—one-liners for your exact work_in_progress flow, no extra noise.
