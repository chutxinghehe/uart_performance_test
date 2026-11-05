# Git Advanced Operations

## Mục Lục
- [Merge vs Rebase](#merge-vs-rebase)
- [Stash - Cất code tạm thời](#stash---cất-code-tạm-thời)
- [Undo Operations](#undo-operations)
- [Tags - Version numbering](#tags---version-numbering)
- [Cherry-pick](#cherry-pick)

---

## Merge vs Rebase

### Merge - Hợp nhất branches

**Merge** = Tạo **merge commit** để kết hợp 2 branches

#### Visualize Merge

**Trước merge:**
```
main:    A---B---C
              \
feature:       D---E
```

**Sau merge:**
```
main:    A---B---C-------F  (F = merge commit)
              \         /
feature:       D---E----
```

**Command:**
```bash
git checkout main
git merge feature/gpio
```

**Kết quả:**
- Commit F có **2 parents**: C và E
- Lịch sử giữ nguyên (nonlinear)
- Dễ trace được branch history

#### Merge Types

**1. Fast-forward merge:**

```
main:    A---B
              \
feature:       C---D

# Merge:
git merge feature
→ main:    A---B---C---D  (no merge commit)
```

Git chỉ **di chuyển pointer** của main, không tạo merge commit.

**Khi nào xảy ra:** Main không có commit mới sau khi branch ra.

**2. Three-way merge (có merge commit):**

```
main:    A---B---C  (C là commit mới)
              \
feature:       D---E

# Merge:
git merge feature
→ main:    A---B---C---F  (F = merge commit)
                \     /
                 D---E
```

**Khi nào xảy ra:** Main có commit mới sau khi branch ra.

---

### Rebase - Viết lại lịch sử

**Rebase** = "Đặt lại base" của branch

#### Visualize Rebase

**Trước rebase:**
```
main:    A---B---C---D
              \
feature:       E---F
```

**Sau rebase:**
```
main:    A---B---C---D
                     \
feature:              E'---F'  (E', F' = commits mới)
```

**Commits E và F được "replay" lên D.**

**Command:**
```bash
git checkout feature/gpio
git rebase main
```

**Kết quả:**
- Lịch sử **linear** (thẳng hàng)
- Commits E, F được **tạo lại** (hash mới)
- Giống như feature được code **sau** D

#### Rebase Step-by-Step

```bash
# 1. Checkout feature branch
git checkout feature/gpio

# 2. Rebase onto main
git rebase main

# Output:
#   First, rewinding head to replay your work on top of it...
#   Applying: feat(gpio): add GPIO init
#   Applying: feat(gpio): add LED toggle
```

**Git làm gì:**
1. Checkout commit D (tip of main)
2. Apply commit E → tạo E'
3. Apply commit F → tạo F'
4. Di chuyển `feature/gpio` pointer đến F'

**Nếu conflict:**
```bash
# Resolve conflict trong file
vim Core/Src/gpio.c

# Add resolved file
git add Core/Src/gpio.c

# Continue rebase
git rebase --continue

# Hoặc abort
git rebase --abort
```

**⚠️ After rebase, force push required:**
```bash
git push --force origin feature/gpio
```

---

### Merge vs Rebase - So Sánh

| Aspect | Merge | Rebase |
|--------|-------|--------|
| **History** | Nonlinear, có merge commits | Linear, clean |
| **Commits** | Giữ nguyên hash | Tạo lại commits (hash mới) |
| **Conflict** | Resolve 1 lần | Resolve từng commit |
| **Safety** | An toàn | Nguy hiểm nếu dùng sai |
| **Undo** | Dễ (revert merge commit) | Khó (history changed) |
| **Push** | `git push` | `git push --force` |
| **Traceability** | Dễ trace branches | Khó trace (linear) |

### Khi Nào Dùng Merge?

✅ **Merge khi:**
- Branch đã push lên remote
- Có người khác dùng branch này
- Muốn giữ lịch sử branches
- Team beginner Git

**Example:**
```bash
# Feature branch đã push, có PR
git checkout main
git merge feature/gpio  # ✅ SAFE
```

### Khi Nào Dùng Rebase?

✅ **Rebase khi:**
- Branch **chưa push** hoặc chỉ bạn dùng
- Muốn lịch sử clean, linear
- Chuẩn bị tạo PR (rebase với main trước)

**Example:**
```bash
# Local branch, chưa push
git checkout feature/gpio
git rebase main  # ✅ OK (chưa ai dùng)
```

⚠️ **KHÔNG rebase khi:**
- Branch đã push và có người khác dùng
- Đang ở main branch (public branch)

### Golden Rule of Rebase

**⚠️ NEVER rebase commits đã push lên public branch (main, develop)**

**Tại sao?**
```
Bạn rebase main:
main (before): A---B---C
main (after):  A---B'---C'  (hash changed!)

Teammate pull:
→ Conflict nightmare! (history diverged)
```

**Safe rebase:**
```
feature/gpio (local, chưa ai dùng):
→ Rebase thoải mái ✅

main (public, cả team dùng):
→ NEVER rebase ⛔
```

---

## Stash - Cất Code Tạm Thời

### Stash Là Gì?

**Stash** = "Ngăn kéo" để cất code tạm thời mà không cần commit.

**Use case:**
```
Bạn đang code trên feature/gpio
↓
Chưa xong, chưa muốn commit
↓
Cần switch sang main để fix bug urgent
↓
Git không cho switch (uncommitted changes)
↓
→ Dùng stash!
```

### Basic Stash Commands

```bash
# Save uncommitted changes vào stash
git stash

# Hoặc với message
git stash save "WIP: GPIO LED toggle"

# Xem danh sách stash
git stash list
# Output:
#   stash@{0}: WIP: GPIO LED toggle
#   stash@{1}: WIP: UART driver
#   stash@{2}: On feature/can: CAN init

# Apply stash gần nhất (KHÔNG xóa khỏi stash list)
git stash apply

# Apply stash cụ thể
git stash apply stash@{1}

# Apply và XÓA khỏi stash list
git stash pop

# Xóa stash
git stash drop stash@{0}

# Xóa tất cả stash
git stash clear
```

### Workflow Example

**Scenario: Urgent bug fix**

```bash
# Đang code GPIO
vim Core/Src/gpio.c

# Check status
git status
# modified:   Core/Src/gpio.c

# Urgent bug ở main!
git checkout main  # ← GIT REJECT!
# error: Your local changes would be overwritten

# Stash changes
git stash save "WIP: GPIO driver"
# Saved working directory and index state

# Giờ Working Directory clean
git status
# nothing to commit, working tree clean

# Switch to main
git checkout main
git pull origin main

# Fix bug
vim Core/Src/main.c
git add Core/Src/main.c
git commit -m "hotfix: fix critical bug"
git push origin main

# Quay lại feature branch
git checkout feature/gpio

# Lấy code từ stash
git stash pop
# Code gpio.c quay lại!

# Continue coding
```

### Stash Options

```bash
# Stash including untracked files
git stash -u

# Stash including ignored files
git stash -a

# Xem nội dung stash
git stash show stash@{0}

# Xem diff
git stash show -p stash@{0}

# Apply stash nhưng không xóa
git stash apply

# Tạo branch từ stash
git stash branch feature/new-branch stash@{0}
```

### Stash vs Commit

| | Stash | Commit |
|---|---|---|
| **Purpose** | Temporary save | Permanent save |
| **History** | Không vào lịch sử commit | Vào lịch sử commit |
| **Khi nào dùng** | Code chưa xong, WIP | Code chạy được, ready |
| **Recover** | `git stash pop` | `git checkout <commit>` |

---

## Undo Operations

### 1. Restore - Xóa uncommitted changes

**Restore = Quay file về trạng thái đã commit (XÓA thay đổi chưa commit)**

```bash
# Restore một file (XÓA changes)
git restore Core/Src/gpio.c

# Restore tất cả files
git restore .
```

**⚠️ Cẩn thận:** Code chưa commit sẽ **MẤT VĨ NH VIỄN**!

**Example:**
```bash
# Sửa gpio.c
vim Core/Src/gpio.c

git status
# modified:   Core/Src/gpio.c

# Muốn hủy thay đổi
git restore Core/Src/gpio.c

# File quay về version đã commit
git status
# nothing to commit
```

**Restore staged file:**
```bash
# File đã git add
git status
# Changes to be committed:
#   modified:   gpio.c

# Unstage (move from Staging → Working Directory)
git restore --staged gpio.c

# Giờ file ở Working Directory (modified, chưa stage)
```

---

### 2. Reset - Di chuyển HEAD

**Reset** = Di chuyển HEAD (và branch pointer) đến commit khác

#### Reset Modes

**1. Soft Reset (giữ changes ở Staging)**

```bash
git reset --soft HEAD~1
```

**Effect:**
- HEAD di chuyển về commit trước
- Changes của commit bị undo **giữ lại ở Staging Area**
- Có thể re-commit ngay

**Use case:** Sửa commit message hoặc thêm files vào commit cuối

```bash
# Vừa commit sai message
git commit -m "fix bug"  # Uh oh, message không rõ

# Soft reset
git reset --soft HEAD~1

# Files vẫn ở staging, re-commit với message đúng
git commit -m "fix(gpio): resolve LED initialization bug"
```

**2. Mixed Reset (default - giữ changes ở Working Directory)**

```bash
git reset HEAD~1
# hoặc
git reset --mixed HEAD~1
```

**Effect:**
- HEAD di chuyển về commit trước
- Changes **giữ lại ở Working Directory** (chưa stage)
- Phải `git add` lại

**Use case:** Undo commit, sửa code, rồi commit lại

```bash
# Commit nhưng phát hiện thiếu một file
git commit -m "feat(gpio): add LED driver"

# Reset
git reset HEAD~1

# Add file thiếu
git add Core/Inc/gpio.h

# Commit lại
git add .
git commit -m "feat(gpio): add LED driver with header"
```

**3. Hard Reset (XÓA changes hoàn toàn)**

```bash
git reset --hard HEAD~1
```

**Effect:**
- HEAD di chuyển về commit trước
- Changes **BỊ XÓA HOÀN TOÀN**
- Working Directory = commit đích

**⚠️ NGUY HIỂM! Code sẽ mất!**

**Use case:** Undo commit và KHÔNG muốn giữ code

```bash
# Commit test code, muốn xóa hết
git commit -m "test: experimental code"

# Hard reset (XÓA)
git reset --hard HEAD~1

# Code test biến mất!
```

#### Reset Syntax

```bash
# Reset về commit trước 1 commit
git reset HEAD~1

# Reset về commit trước 3 commits
git reset HEAD~3

# Reset về commit cụ thể
git reset a3f5d2c

# Reset về commit của main
git reset origin/main
```

---

### 3. Revert - Tạo commit đảo ngược

**Revert** = Tạo **commit mới** để undo commit cũ (không xóa lịch sử)

```bash
git revert <commit-hash>
```

**Example:**

```
History:
A---B---C---D  (D có bug)

git revert D:
A---B---C---D---E  (E = undo D)
```

**Commit E:**
- Đảo ngược tất cả changes của D
- Lịch sử giữ nguyên (D vẫn còn)

**Use case:** Undo commit đã push (public)

```bash
# Commit có bug đã push lên main
git log --oneline
# a3f5d2c (HEAD -> main) feat(gpio): add LED toggle  ← BUG!
# b8e2a1f feat(uart): add UART driver
# c9d4f3e Initial commit

# Revert commit a3f5d2c
git revert a3f5d2c

# Git tạo commit mới:
# d4e5f6a Revert "feat(gpio): add LED toggle"

# Push
git push origin main
```

**Revert vs Reset:**

| | Revert | Reset |
|---|---|---|
| **History** | Giữ nguyên, tạo commit mới | Xóa commits |
| **Safety** | An toàn | Nguy hiểm (nếu đã push) |
| **Khi nào** | Commit đã push (public) | Commit chưa push (local) |
| **Undo** | Có thể revert lại revert | Khó recover |

---

### 4. Amend - Sửa commit cuối

```bash
# Sửa commit message cuối
git commit --amend -m "New message"

# Thêm file vào commit cuối
git add forgotten_file.c
git commit --amend --no-edit  # Giữ nguyên message
```

**⚠️ Chỉ amend commit chưa push!**

**Use case:**
```bash
# Commit thiếu file
git add Core/Src/gpio.c
git commit -m "feat(gpio): add LED driver"

# Uh oh, quên file header
git add Core/Inc/gpio.h
git commit --amend --no-edit

# Commit cuối giờ có cả .c và .h
```

---

### Undo Cheat Sheet

| Situation | Command | Effect |
|-----------|---------|--------|
| Sửa file, chưa stage | `git restore <file>` | Xóa changes |
| Đã stage, chưa commit | `git restore --staged <file>` | Unstage |
| Đã commit (local) | `git reset HEAD~1` | Undo commit, giữ code |
| Đã commit (local), muốn xóa code | `git reset --hard HEAD~1` | Undo commit, XÓA code |
| Đã push | `git revert <commit>` | Tạo commit đảo ngược |
| Sửa commit cuối | `git commit --amend` | Sửa message/thêm file |

---

## Tags - Version Numbering

### Tag Là Gì?

**Tag** = Đánh dấu một commit quan trọng (thường là version release)

```
A---B---C---D---E
        ↑       ↑
      v1.0    v2.0
```

### Tạo Tag

```bash
# Lightweight tag
git tag v1.0.0

# Annotated tag (recommended - có metadata)
git tag -a v1.0.0 -m "Release version 1.0.0"

# Tag commit cụ thể
git tag -a v0.9.0 a3f5d2c -m "Beta release"
```

### Xem Tags

```bash
# List tags
git tag
# Output:
#   v0.9.0
#   v1.0.0
#   v2.0.0

# Xem tag info
git show v1.0.0
```

### Push Tags

```bash
# Push một tag
git push origin v1.0.0

# Push tất cả tags
git push --tags
```

### Checkout Tag

```bash
# Checkout code ở version v1.0.0
git checkout v1.0.0
# → Detached HEAD state
```

### Delete Tag

```bash
# Delete local
git tag -d v1.0.0

# Delete remote
git push origin --delete v1.0.0
```

### Semantic Versioning

**Format:** `vMAJOR.MINOR.PATCH`

```
v1.2.3
│ │ │
│ │ └─ PATCH: Bug fixes (backward compatible)
│ └─── MINOR: New features (backward compatible)
└───── MAJOR: Breaking changes
```

**Examples:**
- `v1.0.0` - First stable release
- `v1.1.0` - Add new feature (UART driver)
- `v1.1.1` - Fix bug in UART
- `v2.0.0` - Breaking change (change API)

---

## Cherry-pick

**Cherry-pick** = Lấy một commit cụ thể từ branch khác

### Use Case

```
main:       A---B
                 \
feature:          C---D---E
                      ↑
                   Need D only!
```

**Muốn lấy commit D (không lấy C, E):**

```bash
git checkout main
git cherry-pick <hash-of-D>

# Result:
main:       A---B---D'  (D' = copy of D)
                 \
feature:          C---D---E
```

### Example

```bash
# Trên feature/uart có commit fix bug critical
git log --oneline
# d4e5f6a fix(uart): fix buffer overflow  ← Need this!
# c3d4e5f feat(uart): add new feature  ← Don't need

# Switch to main
git checkout main

# Cherry-pick commit
git cherry-pick d4e5f6a

# Push
git push origin main
```

---

## Checkpoint

- [ ] Hiểu merge vs rebase (khi nào dùng)
- [ ] Biết dùng stash để cất code tạm
- [ ] Biết undo operations: restore, reset, revert
- [ ] Biết tạo và push tags cho versioning
- [ ] Hiểu cherry-pick

---

**Next:** Part 7 - GitHub Workflow & Automation

