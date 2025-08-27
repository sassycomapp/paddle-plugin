# Git Simple Commands (PowerShell)

> Assumes you’re already in the repo folder and `origin` is set.

## Disable local hooks once (per repo)

```powershell
if (Test-Path .git\hooks) {
  if (Test-Path .git\hooks.disabled) { Remove-Item -Recurse -Force .git\hooks.disabled }
  Move-Item -Path .git\hooks -Destination .git\hooks.disabled
}
git config --unset core.hooksPath 2>$null
```

## Disable global hooks once (machine-wide)

```powershell
git config --global --unset core.hooksPath
```

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

## Push to feature branch `work_in_progress` (add → commit → push)

```powershell
git switch work_in_progress

# Optional: list files > 90MB
Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB } |
  Select-Object FullName, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}

git add -A
git commit -m "your message [skip ci]" --no-verify
git push -u origin HEAD
```

---

## Merge `work_in_progress` into `main`

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main
git merge work_in_progress
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

---

## Basics

```powershell
git status -sb
git add -A
git add path\to\file
git commit -m "feat: short summary"
git push -u origin HEAD   # first time; later: git push
git fetch origin
git branch -vv
git switch -c work_in_progress
git switch main
git branch -d work_in_progress
git push origin --delete work_in_progress
git log --oneline -n 10
git log --oneline --graph --decorate --all
git diff
git diff --staged
git diff main..work_in_progress
git stash
git stash list
git stash apply
git mv old\path new\path
git rm path\to\file
git restore --source=HEAD -- path\to\file
git remote -v
git remote show origin
git tag v0.1.0
git push origin v0.1.0
```

---

## Quick “Daily” sequences

**Start a new feature**

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main
git switch -c work_in_progress
```

**Save progress to feature**

```powershell
git add -A
git commit -m "docs: update notes"
git push -u origin HEAD
```

**Sync current branch (safe)**

```powershell
git fetch origin
git merge --ff-only origin/$(git rev-parse --abbrev-ref HEAD)
```

**Merge feature → main**

```powershell
git switch main
git fetch origin
git merge --ff-only origin/main
git merge work_in_progress
git push
```

---

## Open a Pull Request (simple)

Push your branch, then on GitHub click **“Compare & pull request”** (base: `main`, compare: `work_in_progress`).
