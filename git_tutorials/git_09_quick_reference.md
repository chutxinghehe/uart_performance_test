# Git Quick Reference - Cheat Sheet

## Mục Lục
- [Daily commands](#daily-commands)
- [Branch operations](#branch-operations)
- [Remote operations](#remote-operations)
- [Undo operations](#undo-operations)
- [Information commands](#information-commands)
- [Workflow cheat sheets](#workflow-cheat-sheets)

---

## Daily Commands

### Setup & Clone

```bash
# Configure Git (one-time)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Clone repository
git clone git@github.com:user/repo.git
cd repo

# Check config
git config --list
```

### Status & Diff

```bash
# Check status
git status
git status -s  # Short format

# Check changes
git diff                 # Unstaged changes
git diff --staged        # Staged changes
git diff main feature    # Compare branches
```

### Add & Commit

```bash
# Stage files
git add file.c                # Add specific file
git add Core/Src/*.c          # Add multiple files
git add .                     # Add all changes

# Unstage
git restore --staged file.c   # Unstage file

# Commit
git commit -m "feat(gpio): add LED driver"
git commit --amend            # Fix last commit

# Discard changes
git restore file.c            # Discard unstaged changes
```

---

## Branch Operations

### Create & Switch

```bash
# Create and switch
git switch -c feature/gpio    # New command
git checkout -b feature/gpio  # Old command

# Switch branch
git switch main
git checkout main

# List branches
git branch                    # Local branches
git branch -a                 # All branches (local + remote)
git branch -r                 # Remote branches only
```

### Merge & Delete

```bash
# Merge branch
git checkout main
git merge feature/gpio
git merge --no-ff feature/gpio  # Force merge commit

# Delete branch
git branch -d feature/gpio    # Safe delete (merged only)
git branch -D feature/gpio    # Force delete

# Delete remote branch
git push origin --delete feature/gpio
```

---

## Remote Operations

### Fetch, Pull, Push

```bash
# Check remotes
git remote -v

# Fetch (download, don't merge)
git fetch origin
git fetch origin main

# Pull (fetch + merge)
git pull origin main
git pull --rebase origin main  # Pull with rebase

# Push
git push origin feature/gpio
git push -u origin feature/gpio  # Set upstream
git push --force origin feature/gpio  # Force push (DANGEROUS!)
git push --tags                  # Push tags
```

### Add/Remove Remote

```bash
# Add remote
git remote add origin git@github.com:user/repo.git

# Change remote URL
git remote set-url origin git@github.com:user/new-repo.git

# Remove remote
git remote remove origin
```

---

## Undo Operations

### Restore & Reset

```bash
# Discard unstaged changes
git restore file.c
git restore .

# Unstage file
git restore --staged file.c

# Reset commit (keep changes)
git reset HEAD~1              # Mixed (default)
git reset --soft HEAD~1       # Keep in staging
git reset --hard HEAD~1       # DISCARD changes

# Reset to specific commit
git reset --hard a3f5d2c
```

### Revert & Amend

```bash
# Revert commit (create new commit)
git revert a3f5d2c
git revert HEAD               # Revert last commit

# Amend last commit
git commit --amend -m "New message"
git commit --amend --no-edit  # Keep message
```

---

## Stash Operations

```bash
# Stash changes
git stash
git stash save "WIP: message"

# List stashes
git stash list

# Apply stash
git stash pop                 # Apply and delete
git stash apply               # Apply and keep
git stash apply stash@{1}     # Apply specific stash

# Delete stash
git stash drop stash@{0}
git stash clear               # Clear all
```

---

## Information Commands

### Log & History

```bash
# View commits
git log
git log --oneline
git log --oneline --graph --all
git log --oneline -10         # Last 10 commits

# View commit details
git show a3f5d2c
git show HEAD

# View file history
git log -- Core/Src/gpio.c
git log -p Core/Src/gpio.c    # With diff

# Search commits
git log --grep="fix"          # Search message
git log --author="John"       # By author
```

### Diff & Blame

```bash
# Compare commits
git diff a3f5d2c b8e2a1f
git diff HEAD~1 HEAD

# Compare branches
git diff main feature/gpio

# Who changed this line?
git blame Core/Src/gpio.c
git blame -L 10,20 Core/Src/gpio.c  # Specific lines
```

---

## Workflow Cheat Sheets

### Workflow 1: Feature Development

```bash
# 1. Update main
git checkout main
git pull origin main

# 2. Create feature branch
git switch -c feature/gpio

# 3. Code...
vim Core/Src/gpio.c

# 4. Commit
git add Core/Src/gpio.c Core/Inc/gpio.h
git commit -m "feat(gpio): add LED control"

# 5. Push
git push -u origin feature/gpio

# 6. Create PR on GitHub

# 7. After merge, cleanup
git checkout main
git pull origin main
git branch -d feature/gpio
```

---

### Workflow 2: Update Outdated Branch

```bash
# Your branch: feature/gpio
# Main has new commits

# Check status
git fetch origin
git log --oneline --graph --all

# Option 1: Merge
git checkout feature/gpio
git merge origin/main
# Resolve conflicts if any
git push origin feature/gpio

# Option 2: Rebase
git checkout feature/gpio
git rebase origin/main
# Resolve conflicts if any
git push --force origin feature/gpio
```

---

### Workflow 3: Fix Merge Conflict

```bash
# 1. Pull or merge → CONFLICT
git pull origin main
# CONFLICT in gpio.c

# 2. Check status
git status
# both modified: gpio.c

# 3. Open file, resolve
vim gpio.c
# Remove <<<<<<, ======, >>>>>> markers

# 4. Mark resolved
git add gpio.c

# 5. Commit
git commit -m "merge: resolve gpio.c conflict"

# 6. Push
git push origin feature/gpio
```

---

### Workflow 4: Emergency Bug Fix

```bash
# You're coding on feature/gpio
# Urgent bug in main!

# 1. Stash current work
git stash save "WIP: GPIO driver"

# 2. Switch to main
git checkout main
git pull origin main

# 3. Create hotfix branch
git switch -c hotfix/critical-bug

# 4. Fix bug
vim Core/Src/main.c
git add Core/Src/main.c
git commit -m "hotfix: fix critical bug"

# 5. Push and merge quickly
git push -u origin hotfix/critical-bug
# Create PR, merge

# 6. Back to feature
git checkout feature/gpio
git stash pop

# 7. Merge hotfix into feature
git merge main
```

---

## Git Aliases (Optional Speed Boost)

### Setup Aliases

```bash
# Status
git config --global alias.st status
git config --global alias.s 'status -s'

# Branch
git config --global alias.br branch
git config --global alias.co checkout
git config --global alias.sw switch

# Commit
git config --global alias.ci commit
git config --global alias.cm 'commit -m'

# Log
git config --global alias.lg 'log --oneline --graph --all'
git config --global alias.last 'log -1 HEAD'

# Diff
git config --global alias.df diff
git config --global alias.dfs 'diff --staged'
```

### Usage

```bash
# Instead of:
git status

# Use:
git st

# Instead of:
git log --oneline --graph --all

# Use:
git lg
```

---

## Commit Message Convention

### Format

```
type(scope): subject

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code restructure (no functional change)
- `test`: Add/update tests
- `chore`: Maintenance (build, tools, etc.)
- `config`: Configuration changes (CubeMX, Keil settings)

### Examples

```bash
# Feature
git commit -m "feat(gpio): add LED toggle function"

# Bug fix
git commit -m "fix(uart): resolve buffer overflow in RX handler"

# CubeMX config
git commit -m "config(cubemx): enable CAN1 peripheral"

# Documentation
git commit -m "docs(readme): add build instructions"

# Multiple lines
git commit -m "feat(can): implement CAN driver

- Add CAN_Init() function
- Add CAN_Transmit() function
- Add interrupt handler
- Tested with 500kbps bitrate"
```

---

## Branch Naming Convention

### Format

```
type/description
```

### Types

- `feature/` - New feature
- `bugfix/` - Bug fix
- `hotfix/` - Critical bug fix
- `refactor/` - Code refactor
- `test/` - Experimental code
- `config/` - CubeMX configuration

### Examples

```bash
feature/gpio-driver
feature/uart-dma
bugfix/can-timeout
hotfix/memory-leak
config/enable-tim2
test/new-algorithm
```

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't push (rejected) | `git pull origin <branch>` |
| Merge conflict | Edit file, remove markers, `git add`, `git commit` |
| Can't switch branch (uncommitted) | `git stash` or `git commit` |
| Deleted wrong file | `git checkout HEAD -- file.c` |
| Wrong commit message | `git commit --amend` |
| Pushed wrong code | `git revert <commit>` |
| Detached HEAD | `git switch main` |
| Lost commits | `git reflog`, find commit, `git cherry-pick` |

---

## Essential Git Commands Summary

### Top 20 Commands You'll Use Daily

```bash
# 1. Status
git status

# 2-3. Add & Commit
git add .
git commit -m "message"

# 4-5. Branch
git switch -c feature/new
git switch main

# 6-8. Remote
git fetch origin
git pull origin main
git push origin feature/new

# 9-10. Log
git log --oneline
git diff

# 11-12. Merge
git merge feature/new
git merge --abort

# 13-14. Stash
git stash
git stash pop

# 15-16. Undo
git restore file.c
git reset HEAD~1

# 17-18. Info
git branch -a
git remote -v

# 19-20. Recovery
git reflog
git checkout HEAD -- file.c
```

---

## Git Workflow Diagram

```
┌─────────────────────────────────────────────────────┐
│  Working Directory (Your files)                     │
│  ├── Edit code in Keil                              │
│  └── git status → Shows modified files              │
└──────────────────┬──────────────────────────────────┘
                   │ git add
                   ↓
┌─────────────────────────────────────────────────────┐
│  Staging Area (Index)                               │
│  ├── Files ready to commit                          │
│  └── git diff --staged → Preview                    │
└──────────────────┬──────────────────────────────────┘
                   │ git commit
                   ↓
┌─────────────────────────────────────────────────────┐
│  Local Repository (.git/)                           │
│  ├── Commit history on your machine                 │
│  └── git log → View history                         │
└──────────────────┬──────────────────────────────────┘
                   │ git push
                   ↓
┌─────────────────────────────────────────────────────┐
│  Remote Repository (GitHub)                         │
│  ├── Shared with team                               │
│  └── Pull Request → Code review                     │
└─────────────────────────────────────────────────────┘
```

---

## Checkpoint

- [ ] Đã save page này vào bookmark
- [ ] Biết tìm command cần dùng nhanh chóng
- [ ] Hiểu workflow diagrams
- [ ] Có thể tra cứu khi gặp lỗi

---

**Tip:** In ra cheat sheet này và dán lên tường! 📄

