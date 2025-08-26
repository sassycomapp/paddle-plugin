Great—here’s the exact **Markdown** you can paste into a file (e.g. `Docs/Git-Commands.md`).
It’s split into the two sections you asked for.

---

# Daily Flow Commands

**Repo:** `sassycomapp/paddle-plugin`
**Local path:** `C:\_1mybizz\paddle-plugin`
**Feature branch:** `work_in_progress`

## One-time setup (per machine)

```powershell
Set-Location C:\_1mybizz\paddle-plugin
git remote -v          # origin should point to GitHub
git fetch origin
git switch main
git pull
```

## Start / switch to your feature branch

```powershell
# first time (create it)
git switch -c work_in_progress

# later (just switch)
git switch work_in_progress
```

## Stage → Commit → Push (to the remote branch)

```powershell
git add -A
git commit -m "type: short summary"   # e.g., docs:, feat:, fix:, chore:
git push -u origin HEAD               # first push sets upstream
# later pushes on same branch:
git push
```

## Open a Pull Request (PR)

* **Web:** on GitHub click **Compare & pull request**

  * Base: `main`, Compare: `work_in_progress`, then **Create pull request**.
* **(Optional CLI):**

```powershell
gh pr create --base main --head work_in_progress --fill --web
```

## Keep your branch current before merging

```powershell
git fetch origin
git merge origin/main
git push
# OR (clean history):
git rebase origin/main
# resolve conflicts → 
git push --force-with-lease
```

## Merge the PR

* When checks pass: **Merge pull request** (Squash or Merge).
* (Optional) Enable **Auto-merge** on the PR.

## After merge: sync `main` and clean up

```powershell
git switch main
git pull
git branch -d work_in_progress
git push origin --delete work_in_progress
```

---

# Special Commands

## Useful status & history

```powershell
git status -sb            # compact status + tracking
git branch -vv            # see which remote branch each local branch tracks
git log --oneline -n 5    # short recent history
```

## Skip hooks / unblock a commit (one-off)

```powershell
git commit -m "message" --no-verify         # bypass local pre-commit once
$env:HUSKY="0"; git commit -m "message"; Remove-Item Env:\HUSKY   # bypass Husky for one commit
```

## Undo / fix mistakes

```powershell
git commit --amend -m "better message"      # edit last message
git reset --soft HEAD~1                     # undo last commit, keep staged
git reset --mixed HEAD~1                    # undo last commit, keep files modified
git reset --hard HEAD~1                     # drop last commit & changes (danger)
git restore --staged .                      # unstage everything
git restore --source origin/main -- path\to\file          # get file from main
git restore --worktree --staged -- path\to\file           # discard local changes (danger)
```

## Stash in-progress work

```powershell
git stash -u -m "wip"
git stash list
git stash pop
```

## See how far ahead/behind you are

```powershell
git fetch origin
git rev-list --left-right --count origin/main...main
git rev-list --left-right --count origin/work_in_progress...work_in_progress
```

## Open repo in VS Code

```powershell
code C:\_1mybizz\paddle-plugin
```

## Remote/Upstream helpers

```powershell
git remote -v
git push -u origin work_in_progress   # set upstream if needed
```

---

That’s it—drop this into `/Docs/Git-Commands.md` (or any name you like).

## other Commands

Disable hooks so they stop running & showing up

Run in PowerShell from your repo:

Set-Location C:\_1mybizz\paddle-plugin

# Point Git to an empty hooks dir (repo-local)
New-Item -ItemType Directory -Force .git\no-hooks | Out-Null
git config --local core.hooksPath .git/no-hooks

# Backup any non-sample hooks so health checks don't find them
$bk = ".git\hooks_backup_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Force $bk | Out-Null
Get-ChildItem -File .git\hooks | Where-Object { $_.Name -notlike "*.sample" } | Move-Item -Destination $bk

# Quick verify (these should show an empty/non-sample state)
git config --get core.hooksPath
Get-ChildItem -File .git\hooks | Where-Object { $_.Name -notlike "*.sample" }