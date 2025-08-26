Manual quick checklist (copy/paste one line at a time)
# 1) Be in the repo & fetch latest
Set-Location C:\_1mybizz\paddle-plugin
git fetch origin --prune

# 2) Confirm current branch + tracking
git status -sb
git branch -vv

# 3) Confirm local main matches origin/main
git switch main
git pull
git rev-parse main
git rev-parse origin/main   # numbers should match

# 4) Switch back to your feature branch
git switch work_in_progress

# 5) Working tree clean?
git status --porcelain      # no output == clean

# 6) Upstream for your branch set? (should be origin/work_in_progress)
git branch -vv              # if not, do: git push -u origin HEAD

# 7) Any accidental submodules left?
git ls-files -s | Select-String " 160000 "  # should output nothing

# 8) Remote default branch is 'main'?
git remote show origin      # look for: "HEAD branch: main"

# 9) (Optional) LFS ok?
git lfs status              # if installed; should not show errors

What “OK” looks like

git status -sb on work_in_progress shows something like:
## work_in_progress...origin/work_in_progress (no changes listed)

git branch -vv shows work_in_progress tracking origin/work_in_progress.

git rev-parse main equals git rev-parse origin/main.

No output from the submodule check.

git remote show origin says HEAD branch: main.

git push and git pull run without errors.

If any line in A) or B) shows a problem and the suggested command doesn’t fix it, paste that exact error/output here and I’ll give you the next command to run.