# Git Daily Workflow - Lệnh Hàng Ngày

## Mục Lục
- [Setup lần đầu](#setup-lần-đầu)
- [Clone project](#clone-project)
- [Workflow hàng ngày](#workflow-hàng-ngày)
- [Branch operations](#branch-operations)
- [Remote operations](#remote-operations)
- [Xem lịch sử](#xem-lịch-sử)

---

## Setup Lần Đầu

### 1. Cài đặt Git

**Windows:**
- Download: https://git-scm.com/download/win
- Chạy installer, chọn default options
- Check installation: `git --version`

**Verify:**
```bash
git --version
# Output: git version 2.43.0.windows.1
```

### 2. Config Git Identity

**Bắt buộc làm trước khi commit:**

```bash
# Set tên (hiển thị trong commit)
git config --global user.name "Nguyen Van A"

# Set email (khớp với GitHub email)
git config --global user.email "nguyenvana@example.com"

# Check config
git config --list
```

**Output:**
```
user.name=Nguyen Van A
user.email=nguyenvana@example.com
```

### 3. Config Editor (Optional)

```bash
# Dùng VS Code làm editor mặc định
git config --global core.editor "code --wait"

# Hoặc Notepad nếu không có VS Code
git config --global core.editor "notepad"
```

### 4. Config Line Ending (Windows)

**Quan trọng cho team đa nền tảng:**

```bash
# Windows: Tự động convert CRLF ↔ LF
git config --global core.autocrlf true
```

**Giải thích:**
- **Windows** dùng CRLF (`\r\n`) để xuống dòng
- **Linux/Mac** dùng LF (`\n`)
- `autocrlf true` = tự động convert để tránh conflict vô nghĩa

### 5. Config Default Branch Name

```bash
# Đặt tên default branch là "main" (thay vì "master")
git config --global init.defaultBranch main
```

### 6. SSH Key cho GitHub (Recommended)

**Tại sao cần SSH?**
- Không cần nhập password mỗi lần push
- Bảo mật hơn HTTPS

**Tạo SSH key:**

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "nguyenvana@example.com"

# Nhấn Enter 3 lần (không đặt passphrase cho đơn giản)
# File được tạo tại: C:\Users\YourName\.ssh\id_ed25519.pub

# Copy public key
type C:\Users\Admin\.ssh\id_ed25519.pub
```

**Add vào GitHub:**
1. Mở GitHub → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste nội dung file `.pub`
4. Save

**Test connection:**
```bash
ssh -T git@github.com
# Output: Hi username! You've successfully authenticated...
```

---

## Clone Project

### Scenario 1: Team lead đã tạo repo, bạn join vào

**Step 1: Lấy URL repository**
- Mở GitHub repo
- Click nút **Code**
- Copy URL (SSH hoặc HTTPS)

```
SSH:   git@github.com:username/stm32-project.git
HTTPS: https://github.com/username/stm32-project.git
```

**Step 2: Clone về máy**

```bash
# Di chuyển đến thư mục muốn clone
cd C:\Projects

# Clone repository
git clone git@github.com:username/stm32-project.git

# Git sẽ tạo folder stm32-project/ và download code
```

**Output:**
```
Cloning into 'stm32-project'...
remote: Enumerating objects: 145, done.
remote: Counting objects: 100% (145/145), done.
remote: Compressing objects: 100% (98/98), done.
Receiving objects: 100% (145/145), 2.5 MiB | 1.2 MiB/s, done.
```

**Step 3: Vào folder project**

```bash
cd stm32-project

# Check branches
git branch -a
# Output:
#   * main
#   remotes/origin/main
```

### Scenario 2: Tạo repo mới từ project STM32 có sẵn

**Step 1: Tạo repo trên GitHub**
1. Mở GitHub → New Repository
2. Đặt tên: `stm32-project`
3. **KHÔNG tick** "Initialize with README" (vì đã có code local)
4. Create repository

**Step 2: Init Git trong folder STM32**

```bash
# Vào folder STM32 project
cd C:\Projects\STM32_Project

# Init Git
git init

# Check status
git status
```

**Step 3: Add remote**

```bash
# Add remote URL (copy từ GitHub)
git remote add origin git@github.com:username/stm32-project.git

# Verify
git remote -v
# Output:
#   origin  git@github.com:username/stm32-project.git (fetch)
#   origin  git@github.com:username/stm32-project.git (push)
```

**Step 4: Commit code hiện tại**

```bash
# Add tất cả file (trừ file trong .gitignore)
git add .

# Commit
git commit -m "Initial commit: STM32 project setup"

# Rename branch sang main (nếu đang là master)
git branch -M main

# Push lên GitHub
git push -u origin main
```

---

## Workflow Hàng Ngày

### Morning: Bắt đầu làm việc

```bash
# 1. Vào folder project
cd C:\Projects\stm32-project

# 2. Check branch hiện tại
git branch
# Output: * feature/gpio

# 3. Pull code mới nhất từ GitHub (cập nhật main)
git checkout main
git pull origin main

# 4. Quay lại branch đang làm
git checkout feature/gpio

# 5. Merge code mới từ main vào branch của bạn (nếu cần)
git merge main
```

### Coding: Viết code

```bash
# Mở Keil, viết code...

# Check file nào đã sửa
git status
# Output:
#   modified:   Core/Src/gpio.c
#   modified:   Core/Inc/gpio.h
```

### Mid-work: Save progress (commit)

```bash
# Add file vào staging
git add Core/Src/gpio.c Core/Inc/gpio.h

# Hoặc add tất cả
git add .

# Check staging area
git status
# Output: Changes to be committed:
#           modified:   Core/Src/gpio.c
#           modified:   Core/Inc/gpio.h

# Commit
git commit -m "feat(gpio): implement LED toggle function"
```

### Evening: Push code lên GitHub

```bash
# Push branch lên GitHub
git push origin feature/gpio
```

**Nếu lần đầu push branch mới:**
```bash
# Set upstream (tracking branch)
git push -u origin feature/gpio

# Lần sau chỉ cần:
git push
```

### Before Leaving: Check status

```bash
# Đảm bảo không có uncommitted changes
git status
# Output: nothing to commit, working tree clean

# Check log
git log --oneline -5
# Output:
#   a3f5d2c feat(gpio): implement LED toggle function
#   b8e2a1f feat(gpio): add GPIO initialization
#   c9d4f3e Initial commit
```

---

## Branch Operations

### Xem các branch

```bash
# List local branches
git branch
# Output:
#   * feature/gpio  (dấu * = branch hiện tại)
#     feature/uart
#     main

# List tất cả branches (local + remote)
git branch -a
# Output:
#   * feature/gpio
#     main
#   remotes/origin/main
#   remotes/origin/feature/uart
```

### Tạo branch mới

**Cách 1: Tạo và chuyển ngay**
```bash
git switch -c feature/can
# hoặc (cũ hơn)
git checkout -b feature/can
```

**Cách 2: Tạo riêng, chuyển sau**
```bash
# Tạo branch
git branch feature/timer

# Chuyển sang branch
git switch feature/timer
# hoặc
git checkout feature/timer
```

**Branch naming convention:**
```
feature/<module>   → feature/gpio, feature/uart
bugfix/<issue>     → bugfix/can-timeout
hotfix/<urgent>    → hotfix/memory-leak
test/<experiment>  → test/new-algorithm
```

### Chuyển branch

```bash
# Chuyển sang main
git switch main
# hoặc
git checkout main

# Chuyển sang feature branch
git switch feature/gpio
```

**⚠️ Warning:**
```bash
# Nếu có uncommitted changes, Git sẽ cảnh báo:
# error: Your local changes to the following files would be overwritten by checkout
#        gpio.c
# Please commit your changes or stash them before you switch branches.
```

**Giải pháp:**
```bash
# Option 1: Commit trước
git add .
git commit -m "WIP: temporary save"
git switch main

# Option 2: Stash (xem Part 6)
git stash
git switch main
```

### Xóa branch

```bash
# Xóa branch local (sau khi đã merge)
git branch -d feature/gpio
# Output: Deleted branch feature/gpio (was a3f5d2c)

# Force delete (chưa merge nhưng muốn xóa)
git branch -D feature/old-experiment
```

**⚠️ Lưu ý:**
- Không thể xóa branch đang đứng
- Phải chuyển sang branch khác trước

```bash
# SAI:
git branch -d feature/gpio  # Đang đứng ở feature/gpio → lỗi

# ĐÚNG:
git switch main
git branch -d feature/gpio
```

### Rename branch

```bash
# Rename branch hiện tại
git branch -m new-name

# Rename branch khác
git branch -m old-name new-name

# Ví dụ:
git branch -m feature/gpio feature/gpio-driver
```

---

## Remote Operations

### Check remote

```bash
# Xem remote URL
git remote -v
# Output:
#   origin  git@github.com:username/stm32-project.git (fetch)
#   origin  git@github.com:username/stm32-project.git (push)
```

### Fetch - Lấy thông tin từ GitHub

```bash
# Fetch all branches
git fetch origin

# Fetch một branch cụ thể
git fetch origin main
```

**Fetch làm gì?**
- Download commits mới từ GitHub
- Cập nhật `origin/main`, `origin/feature/uart`
- **KHÔNG** thay đổi branch local của bạn

**Sau khi fetch:**
```bash
# Check xem main trên GitHub có gì mới
git log origin/main

# So sánh local vs remote
git diff main origin/main
```

### Pull - Lấy code và merge ngay

```bash
# Pull main branch
git pull origin main
# = git fetch origin main + git merge origin/main
```

**Khi nào dùng pull?**
- Muốn cập nhật branch hiện tại với code mới từ GitHub
- Ví dụ: Đang ở `main`, muốn lấy code team vừa merge

**⚠️ Warning: Pull có thể gây conflict**
```bash
git pull origin main
# Output:
#   Auto-merging gpio.c
#   CONFLICT (content): Merge conflict in gpio.c
#   Automatic merge failed; fix conflicts and then commit the result.
```

### Push - Đẩy code lên GitHub

```bash
# Push branch hiện tại lên GitHub
git push origin feature/gpio

# Lần đầu push branch mới, set upstream
git push -u origin feature/gpio

# Lần sau chỉ cần
git push
```

**Push bị reject:**
```bash
git push origin feature/gpio
# Output:
#   ! [rejected]  feature/gpio -> feature/gpio (non-fast-forward)
#   error: failed to push some refs
```

**Nguyên nhân:**
- GitHub có commit mới mà local chưa có
- Phải pull trước, merge, rồi mới push được

**Fix:**
```bash
git pull origin feature/gpio
# Resolve conflict nếu có
git push origin feature/gpio
```

---

## Xem Lịch Sử

### git log - Xem commit history

```bash
# Log đầy đủ
git log
# Output:
#   commit a3f5d2c (HEAD -> feature/gpio, origin/feature/gpio)
#   Author: Nguyen Van A <a@example.com>
#   Date:   Mon Jan 15 10:30:00 2024 +0700
#   
#       feat(gpio): implement LED toggle function

# Log ngắn gọn (1 dòng / commit)
git log --oneline
# Output:
#   a3f5d2c feat(gpio): implement LED toggle function
#   b8e2a1f feat(gpio): add GPIO initialization
#   c9d4f3e Initial commit

# Log với graph (visualize branches)
git log --oneline --graph --all
# Output:
#   * a3f5d2c (HEAD -> feature/gpio) feat(gpio): implement LED toggle
#   * b8e2a1f feat(gpio): add GPIO initialization
#   | * d5e6f7a (feature/uart) feat(uart): add UART driver
#   |/  
#   * c9d4f3e (main) Initial commit

# Log 5 commit gần nhất
git log --oneline -5
```

### git show - Xem chi tiết commit

```bash
# Xem commit cuối
git show

# Xem commit cụ thể
git show a3f5d2c

# Output:
#   commit a3f5d2c
#   Author: Nguyen Van A <a@example.com>
#   Date:   Mon Jan 15 10:30:00 2024 +0700
#   
#       feat(gpio): implement LED toggle function
#   
#   diff --git a/Core/Src/gpio.c b/Core/Src/gpio.c
#   +void GPIO_ToggleLED(void)
#   +{
#   +    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
#   +}
```

### git diff - So sánh thay đổi

```bash
# So sánh Working Directory vs Staging
git diff
# → File đã sửa nhưng chưa git add

# So sánh Staging vs Last Commit
git diff --staged
# → File đã git add nhưng chưa commit

# So sánh 2 commits
git diff c9d4f3e a3f5d2c

# So sánh 2 branches
git diff main feature/gpio

# So sánh với remote
git diff main origin/main
```

### git status - Check trạng thái

```bash
git status

# Output example:
On branch feature/gpio
Your branch is up to date with 'origin/feature/gpio'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   gpio.c

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   uart.c

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        can.c
```

---

## Workflow Summary

### Quick Reference

| Task | Command |
|------|---------|
| Clone repo | `git clone <url>` |
| Check status | `git status` |
| Check branch | `git branch` |
| Create & switch branch | `git switch -c feature/gpio` |
| Switch branch | `git switch main` |
| Stage files | `git add .` |
| Commit | `git commit -m "message"` |
| Push | `git push origin feature/gpio` |
| Pull | `git pull origin main` |
| Fetch | `git fetch origin` |
| Log | `git log --oneline --graph --all` |
| Diff | `git diff` |

### Typical Daily Flow

```bash
# Morning
git checkout main
git pull origin main
git checkout feature/gpio
git merge main

# Coding
# ... edit files in Keil ...

# Save progress
git add .
git commit -m "feat(gpio): add new feature"

# End of day
git push origin feature/gpio
```

---

## Common Mistakes

### ❌ Forget to commit before switching branch
```bash
git checkout main
# error: Your local changes would be overwritten
```
**Fix:** Commit hoặc stash trước

### ❌ Commit vào sai branch
```bash
# Đang ở main, commit nhầm
git commit -m "feat(gpio): new feature"
```
**Fix:** 
```bash
# Undo commit (giữ changes)
git reset --soft HEAD~1

# Switch to correct branch
git checkout feature/gpio

# Commit lại
git commit -m "feat(gpio): new feature"
```

### ❌ Push force lên main
```bash
git push --force origin main  # ← NGUY HIỂM!
```
**Never force push to main!** Làm mất code của team.

---

## Checkpoint

- [ ] Đã config Git identity (name, email)
- [ ] Đã setup SSH key cho GitHub
- [ ] Biết clone repository
- [ ] Biết workflow: edit → add → commit → push
- [ ] Biết tạo và switch branch
- [ ] Biết fetch vs pull
- [ ] Biết xem log và diff

---

**Next:** Part 3 - Teamwork Cases (làm việc nhóm như thế nào)

