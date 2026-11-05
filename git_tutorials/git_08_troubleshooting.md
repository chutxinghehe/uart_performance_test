# Git Troubleshooting - Common Errors

## Mục Lục
- [Push rejected errors](#push-rejected-errors)
- [Merge conflict errors](#merge-conflict-errors)
- [Branch errors](#branch-errors)
- [Detached HEAD](#detached-head)
- [Uncommitted changes errors](#uncommitted-changes-errors)
- [Remote errors](#remote-errors)
- [STM32 specific issues](#stm32-specific-issues)

---

## Push Rejected Errors

### Error 1: Non-fast-forward

```bash
git push origin feature/gpio

# Output:
! [rejected]  feature/gpio -> feature/gpio (non-fast-forward)
error: failed to push some refs to 'origin'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart.
```

**Nguyên nhân:**
- Remote có commits mới mà local chưa có
- Không thể fast-forward

**Giải pháp:**

```bash
# Option 1: Pull và merge
git pull origin feature/gpio
# Resolve conflicts nếu có
git push origin feature/gpio

# Option 2: Pull với rebase
git pull --rebase origin feature/gpio
# Resolve conflicts nếu có
git push origin feature/gpio

# Option 3: Force push (NGUY HIỂM!)
git push --force origin feature/gpio  # ⚠️ Chỉ nếu chắc chắn!
```

---

### Error 2: Protected branch

```bash
git push origin main

# Output:
remote: error: GH006: Protected branch update failed
remote: error: Cannot push to main
```

**Nguyên nhân:**
- Branch `main` được protect
- Không cho push trực tiếp

**Giải pháp:**

```bash
# Tạo feature branch
git checkout -b feature/your-feature

# Push feature branch
git push origin feature/your-feature

# Tạo Pull Request trên GitHub
```

---

### Error 3: Permission denied (SSH)

```bash
git push origin main

# Output:
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Nguyên nhân:**
- SSH key chưa setup
- SSH key không có quyền

**Giải pháp:**

```bash
# Check SSH key
ssh -T git@github.com

# Nếu lỗi, generate SSH key mới
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
type C:\Users\YourName\.ssh\id_ed25519.pub

# Add vào GitHub: Settings → SSH keys
```

---

## Merge Conflict Errors

### Error 4: Merge conflict

```bash
git merge feature/gpio

# Output:
Auto-merging Core/Src/gpio.c
CONFLICT (content): Merge conflict in Core/Src/gpio.c
Automatic merge failed; fix conflicts and then commit the result.
```

**Giải pháp:**

```bash
# 1. Check conflicted files
git status

# 2. Open and resolve conflicts
vim Core/Src/gpio.c
# Remove <<<<<<, ======, >>>>>> markers

# 3. Mark resolved
git add Core/Src/gpio.c

# 4. Commit
git commit -m "merge: resolve gpio conflict"

# Or abort
git merge --abort
```

---

### Error 5: Merge conflict in binary file

```bash
git merge feature/docs

# Output:
warning: Cannot merge binary files: docs/diagram.png (HEAD vs. feature/docs)
Auto-merging docs/diagram.png
CONFLICT (content): Merge conflict in docs/diagram.png
```

**Giải pháp:**

```bash
# Choose one version

# Option 1: Keep YOUR version
git checkout --ours docs/diagram.png
git add docs/diagram.png

# Option 2: Keep THEIR version
git checkout --theirs docs/diagram.png
git add docs/diagram.png

# Then commit
git commit -m "merge: resolve binary conflict, use theirs"
```

---

## Branch Errors

### Error 6: Branch already exists

```bash
git switch -c feature/gpio

# Output:
fatal: A branch named 'feature/gpio' already exists.
```

**Giải pháp:**

```bash
# Just switch to existing branch
git switch feature/gpio

# Or delete and recreate
git branch -d feature/gpio
git switch -c feature/gpio
```

---

### Error 7: Cannot delete current branch

```bash
git branch -d feature/gpio

# Output:
error: Cannot delete branch 'feature/gpio' checked out at '...'
```

**Giải pháp:**

```bash
# Switch to another branch first
git switch main
git branch -d feature/gpio
```

---

### Error 8: Branch not fully merged

```bash
git branch -d feature/gpio

# Output:
error: The branch 'feature/gpio' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/gpio'.
```

**Nguyên nhân:**
- Branch có commits chưa merge vào main

**Giải pháp:**

```bash
# Option 1: Merge first
git checkout main
git merge feature/gpio
git branch -d feature/gpio

# Option 2: Force delete (mất commits!)
git branch -D feature/gpio
```

---

## Detached HEAD

### Error 9: Detached HEAD state

```bash
git checkout a3f5d2c

# Output:
You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.
```

**Giải thích:**
- HEAD đang trỏ vào commit cụ thể, không phải branch
- Commits mới sẽ "lạc" (orphaned)

**Giải pháp:**

```bash
# Option 1: Quay về branch
git switch main

# Option 2: Tạo branch mới từ detached HEAD
git switch -c feature/new-branch

# Option 3: Discard changes
git switch main  # Changes will be lost
```

---

## Uncommitted Changes Errors

### Error 10: Overwrite uncommitted changes

```bash
git checkout main

# Output:
error: Your local changes to the following files would be overwritten by checkout:
    Core/Src/gpio.c
Please commit your changes or stash them before you switch branches.
```

**Giải pháp:**

```bash
# Option 1: Commit
git add Core/Src/gpio.c
git commit -m "WIP: save progress"
git checkout main

# Option 2: Stash
git stash
git checkout main
# Later: git stash pop

# Option 3: Discard (mất code!)
git restore Core/Src/gpio.c
git checkout main
```

---

### Error 11: Cannot pull with uncommitted changes

```bash
git pull origin main

# Output:
error: Your local changes to the following files would be overwritten by merge:
    Core/Src/main.c
Please commit your changes or stash them before you merge.
```

**Giải pháp:**

```bash
# Option 1: Commit first
git add .
git commit -m "WIP"
git pull origin main

# Option 2: Stash
git stash
git pull origin main
git stash pop
```

---

## Remote Errors

### Error 12: Remote not found

```bash
git push origin main

# Output:
fatal: 'origin' does not appear to be a git repository
fatal: Could not read from remote repository.
```

**Giải pháp:**

```bash
# Check remotes
git remote -v

# If empty, add remote
git remote add origin git@github.com:user/repo.git

# Verify
git remote -v
```

---

### Error 13: Remote branch not found

```bash
git pull origin feature/gpio

# Output:
fatal: couldn't find remote ref feature/gpio
```

**Nguyên nhân:**
- Branch không tồn tại trên remote

**Giải pháp:**

```bash
# Fetch all branches
git fetch origin

# List remote branches
git branch -r

# If branch doesn't exist, create and push
git push -u origin feature/gpio
```

---

### Error 14: Repository not found

```bash
git clone git@github.com:user/wrong-repo.git

# Output:
ERROR: Repository not found.
fatal: Could not read from remote repository.
```

**Nguyên nhân:**
- URL sai
- Repository private và không có quyền
- Repository bị xóa

**Giải pháp:**

```bash
# Check URL
# Copy correct URL from GitHub

# Check permissions
# Ensure you have access to repository

# Re-clone với URL đúng
git clone git@github.com:user/correct-repo.git
```

---

## STM32 Specific Issues

### Issue 1: CubeMX .ioc conflict

**Problem:**
```
<<<<<<< HEAD
Mcu.Pin5=PB6
=======
Mcu.Pin5=PB8
>>>>>>> feature/can
```

**Giải pháp:**

```bash
# NEVER manually edit .ioc conflict!

# Abort merge
git merge --abort

# Coordinate with teammate
# One person re-configure in CubeMX
# Regenerate code
# Commit and push
```

---

### Issue 2: Generated code lost after pull

**Problem:**
```
Pull main → CubeMX generated code bị thay đổi
→ Code trong USER CODE sections bị mất?
```

**Root cause:**
- Teammate regenerate code với config khác
- Code ngoài USER CODE bị overwrite

**Prevention:**

```bash
# ✅ LUÔN viết code trong USER CODE sections
/* USER CODE BEGIN 2 */
// Your code here
/* USER CODE END 2 */

# ❌ KHÔNG viết code ngoài USER CODE
void MX_GPIO_Init(void)
{
    // Don't add code here! Will be overwritten!
}
```

**Recovery:**

```bash
# If code lost, check git history
git log --oneline --all -- Core/Src/main.c

# Checkout old version
git show a3f5d2c:Core/Src/main.c > main_old.c

# Copy lost code from main_old.c
```

---

### Issue 3: Keil project won't build after pull

**Problem:**
```
Pull main → Keil báo lỗi compile
→ File not found, missing symbols
```

**Possible causes:**

1. **Missing files in project**

```bash
# Check if files exist
ls Core/Src/can.c

# If exists but not in Keil:
# → Manually add to Keil project
# Right-click project → Add Existing Files
```

2. **Wrong include paths**

```bash
# Check .uvprojx for include paths
# Ensure paths match your folder structure
```

3. **Conflicted .uvprojx**

```bash
# Check for conflict markers
grep -r "<<<<<<" MDK-ARM/*.uvprojx

# If found, resolve carefully
```

**Giải pháp:**

```bash
# Rebuild project
# Clean build
# Close and reopen Keil
```

---

### Issue 4: Accidentally committed build artifacts

**Problem:**
```bash
git status
# Output:
#   new file:   MDK-ARM/Objects/gpio.o
#   new file:   MDK-ARM/STM32_Project.axf
```

**Giải pháp:**

```bash
# If not committed yet
git restore --staged MDK-ARM/Objects/
git clean -fd MDK-ARM/Objects/

# If already committed
git rm --cached MDK-ARM/Objects/*.o
git rm --cached MDK-ARM/*.axf
git commit -m "chore: remove build artifacts"

# Update .gitignore
echo "*.o" >> .gitignore
echo "*.axf" >> .gitignore
git add .gitignore
git commit -m "chore: update gitignore"
```

---

## Diagnostic Commands

### Check Status

```bash
# Overall status
git status

# Detailed diff
git diff

# Staged changes
git diff --staged

# Branch info
git branch -vv

# Remote info
git remote -v

# Log
git log --oneline --graph --all -10
```

### Check History

```bash
# Who changed this file?
git log -- Core/Src/gpio.c

# Show commit details
git show a3f5d2c

# Find when bug introduced
git bisect start
```

### Check Remote

```bash
# Fetch without merge
git fetch origin

# Compare local vs remote
git diff main origin/main

# List remote branches
git branch -r
```

---

## Recovery Commands

### Undo Last Commit

```bash
# Undo commit, keep changes
git reset --soft HEAD~1

# Undo commit, keep changes unstaged
git reset HEAD~1

# Undo commit, discard changes (NGUY HIỂM!)
git reset --hard HEAD~1
```

### Recover Deleted File

```bash
# Find commit where file existed
git log --all --full-history -- Core/Src/deleted.c

# Restore from that commit
git checkout a3f5d2c -- Core/Src/deleted.c
```

### Recover Lost Commits

```bash
# Show reflog (all HEAD movements)
git reflog

# Output:
#   a3f5d2c HEAD@{0}: reset: moving to HEAD~1
#   b8e2a1f HEAD@{1}: commit: feat(gpio): add driver
#   c9d4f3e HEAD@{2}: commit: init project

# Recover lost commit
git cherry-pick b8e2a1f

# Or reset to it
git reset --hard b8e2a1f
```

---

## Emergency Procedures

### "I messed up everything!"

```bash
# If you haven't pushed:

# Option 1: Abort ongoing operation
git merge --abort
git rebase --abort
git cherry-pick --abort

# Option 2: Reset to last good state
git reset --hard origin/main

# Option 3: Re-clone (nuclear option)
cd ..
mv project project_backup
git clone <url> project
```

### "I force pushed to main!"

```bash
# If JUST happened, reflog might save you
git reflog

# Find commit before force push
git reset --hard <commit-hash>
git push --force origin main

# If others already pulled:
# → Announce team
# → Everyone needs to reset their main
```

### "I deleted wrong branch!"

```bash
# Reflog to rescue
git reflog

# Find branch tip commit
# Output:
#   a3f5d2c HEAD@{10}: commit: feat(gpio): final

# Recreate branch
git branch feature/gpio a3f5d2c
```

---

## Prevention Checklist

**Before Every Push:**
- [ ] `git status` - Check what you're pushing
- [ ] `git log --oneline -5` - Check commits
- [ ] `git diff origin/main` - Review changes
- [ ] Build and test locally

**Before Every Merge:**
- [ ] `git pull origin main` - Update main first
- [ ] `git merge --no-ff --no-commit main` - Dry run
- [ ] Resolve conflicts carefully
- [ ] Test after merge

**Before Force Push:**
- [ ] **STOP AND THINK!**
- [ ] Is this my personal branch?
- [ ] Have I communicated with team?
- [ ] Is there a better way?

---

## Checkpoint

- [ ] Biết troubleshoot push rejected
- [ ] Biết resolve merge conflicts
- [ ] Biết handle detached HEAD
- [ ] Biết recover deleted files/commits
- [ ] Biết STM32-specific issues
- [ ] Có emergency procedures

---

**Next:** Part 9 - Quick Reference & Cheat Sheet

