# Git Workflow STM32 - Thực Chiến

## 🎯 Workflow Cơ Bản (Copy & Paste)

### 1. Setup Lần Đầu (1 lần duy nhất)

```bash
# Config Git
git config --global user.name "Tên Bạn"
git config --global user.email "email@example.com"

# Clone project
git clone git@github.com:team/stm32-project.git
cd stm32-project
```

---

### 2. Workflow Hàng Ngày

```bash
# ==== SÁNG: Bắt đầu làm việc ====
git checkout main
git pull origin main                    # Lấy code mới nhất
git checkout -b feature/ten-module      # Tạo branch mới

# ==== CODING trong Keil ====
# ... viết code ...

# ==== CHIỀU: Lưu code ====
git status                              # Xem file nào đã sửa
git add .                               # Add tất cả
git commit -m "feat(gpio): mô tả ngắn" # Commit
git push -u origin feature/ten-module   # Push lần đầu

# Lần sau chỉ cần:
git add .
git commit -m "feat(gpio): thêm feature"
git push
```

---

### 3. Merge Code Vào Main (Pull Request)

```bash
# Trên GitHub:
# 1. Tạo Pull Request
# 2. Đợi review
# 3. Merge

# Sau khi merge, cleanup:
git checkout main
git pull origin main
git branch -d feature/ten-module        # Xóa branch local
```

---

## 🔥 Commands Quan Trọng Nhất (Top 15)

| Command | Khi Nào Dùng | Example |
|---------|--------------|---------|
| `git status` | Check file nào đã sửa | `git status` |
| `git add .` | Chuẩn bị commit tất cả files | `git add .` |
| `git commit -m "..."` | Lưu snapshot code | `git commit -m "feat(gpio): add LED"` |
| `git push` | Đẩy code lên GitHub | `git push origin feature/gpio` |
| `git pull` | Lấy code mới từ GitHub | `git pull origin main` |
| `git checkout -b <branch>` | Tạo branch mới | `git checkout -b feature/uart` |
| `git checkout <branch>` | Chuyển sang branch khác | `git checkout main` |
| `git branch` | Xem tất cả branches | `git branch -a` |
| `git log --oneline` | Xem lịch sử commit | `git log --oneline -10` |
| `git stash` | Cất code tạm (chưa commit) | `git stash` |
| `git stash pop` | Lấy code đã cất ra | `git stash pop` |
| `git merge <branch>` | Merge branch vào branch hiện tại | `git merge main` |
| `git reset HEAD~1` | Undo commit cuối (giữ code) | `git reset HEAD~1` |
| `git restore <file>` | Hủy thay đổi file (XÓA CODE!) | `git restore gpio.c` |
| `git diff` | Xem thay đổi chưa commit | `git diff` |

---

## ⚡ Tình Huống Thường Gặp

### ❌ Push bị reject

```bash
# Lỗi: ! [rejected] feature/gpio -> feature/gpio (non-fast-forward)
# Nguyên nhân: GitHub có code mới, bạn chưa có

# Fix:
git pull origin feature/gpio
# Nếu conflict → resolve (xem phần sau)
git push origin feature/gpio
```

---

### ❌ Conflict khi merge/pull

```bash
# Lỗi: CONFLICT (content): Merge conflict in gpio.c

# Fix:
# 1. Mở file gpio.c
# 2. Tìm đoạn:
#    <<<<<<< HEAD
#    code của bạn
#    =======
#    code của người khác
#    >>>>>>> commit-hash
#
# 3. Xóa markers (<<<, ===, >>>), giữ code đúng
# 4. Chạy:
git add gpio.c
git commit -m "merge: resolve conflict in gpio.c"
git push
```

---

### ❌ Muốn switch branch nhưng có uncommitted changes

```bash
# Lỗi: error: Your local changes would be overwritten by checkout

# Fix Option 1: Commit trước
git add .
git commit -m "WIP: save progress"
git checkout main

# Fix Option 2: Stash (cất tạm)
git stash
git checkout main
# Sau đó lấy lại:
git checkout feature/gpio
git stash pop
```

---

### ❌ Commit nhầm, muốn undo

```bash
# Undo commit cuối, GIỮ code
git reset HEAD~1

# Undo commit cuối, XÓA code (NGUY HIỂM!)
git reset --hard HEAD~1
```

---

### ❌ Branch bị outdated (main có code mới)

```bash
# Update branch của bạn với code mới từ main:
git checkout feature/gpio
git fetch origin
git merge origin/main
# Nếu conflict → resolve
git push origin feature/gpio
```

---

## 🎨 Commit Message Format

```bash
# Format:
<type>(<scope>): <mô tả ngắn>

# Types:
feat     - Feature mới
fix      - Fix bug
config   - CubeMX configuration
docs     - Documentation
refactor - Refactor code
test     - Add test

# Examples:
git commit -m "feat(gpio): add LED toggle function"
git commit -m "fix(uart): resolve buffer overflow"
git commit -m "config(cubemx): enable CAN1 on PB8/PB9"
```

---

## 📁 Files Nào Commit? (.gitignore)

### ✅ NÊN COMMIT
- `*.c`, `*.h` - Source code
- `*.ioc` - CubeMX config
- `*.uvprojx` - Keil project file
- `Drivers/` - HAL drivers
- `README.md`, `docs/`

### ❌ KHÔNG COMMIT
- `*.o`, `*.axf`, `*.hex`, `*.bin` - Build output
- `*.uvoptx`, `*.uvguix.*` - User settings
- `Objects/`, `Listings/` - Build folders
- `.venv/`, `__pycache__/` - Python
- `.vscode/`, `.idea/` - IDE settings

**File `.gitignore` đã có sẵn trên Desktop!**

---

## 🔧 STM32 + CubeMX Đặc Biệt

### ⚠️ CubeMX Workflow

**Quy tắc vàng:**
- Chỉ **1 người** configure CubeMX (Coordinator)
- Người khác **không mở CubeMX**, chỉ viết code

**Nếu phải configure CubeMX:**

```bash
# 1. Announce team trước 30 phút
# "Mình sẽ configure CubeMX lúc 2pm"

# 2. Pull main mới nhất
git checkout main
git pull origin main

# 3. Configure CubeMX → Generate code

# 4. Commit và merge NGAY
git add .
git commit -m "config(cubemx): enable CAN1"
git push origin main

# 5. Announce team
# "Done! Mọi người pull main nhé"
```

---

### ⚠️ USER CODE Sections

**CHỈ viết code trong `/* USER CODE BEGIN */.../* USER CODE END */`**

```c
// ✅ ĐÚNG
void main(void)
{
    HAL_Init();
    
    /* USER CODE BEGIN 2 */
    uint8_t msg[] = "Hello";  // ← Viết ở đây, code sẽ được giữ khi regenerate
    /* USER CODE END 2 */
    
    while(1) { }
}

// ❌ SAI
void main(void)
{
    HAL_Init();
    uint8_t msg[] = "Hello";  // ← Viết ngoài USER CODE → BỊ MẤT khi regenerate!
}
```

---

## 🚀 Branch Naming

```bash
feature/gpio-driver
feature/uart-dma
bugfix/can-timeout
config/enable-tim2
hotfix/memory-leak
```

**Format:** `type/description-ngan-gon`

---

## 📊 Workflow Map (Nếu Muốn... Thì...)

| Tôi Muốn... | Command |
|-------------|---------|
| Tạo branch mới | `git checkout -b feature/new` |
| Xem file nào đã sửa | `git status` |
| Commit code | `git add . && git commit -m "..."` |
| Push lên GitHub | `git push` hoặc `git push -u origin <branch>` |
| Lấy code mới từ GitHub | `git pull origin main` |
| Switch sang branch khác | `git checkout <branch-name>` |
| Xem lịch sử | `git log --oneline --graph -10` |
| Undo commit (giữ code) | `git reset HEAD~1` |
| Undo thay đổi file (XÓA!) | `git restore <file>` |
| Cất code tạm | `git stash` |
| Lấy code đã cất | `git stash pop` |
| Merge branch | `git checkout main && git merge feature/x` |
| Update branch với main mới | `git merge origin/main` |
| Xóa branch | `git branch -d <branch-name>` |
| Xem diff | `git diff` |
| Resolve conflict | Edit file → xóa `<<<`, `===`, `>>>` → `git add` → `git commit` |

---

## 🆘 Emergency Commands

```bash
# Abort merge/conflict
git merge --abort

# Discard ALL uncommitted changes (NGUY HIỂM!)
git reset --hard HEAD

# Recover deleted commit
git reflog              # Tìm commit hash
git cherry-pick <hash>  # Restore commit

# Force pull (ghi đè local)
git fetch origin
git reset --hard origin/main
```

---

## ✅ Daily Checklist

**Morning:**
- [ ] `git checkout main`
- [ ] `git pull origin main`
- [ ] `git checkout -b feature/xyz` (hoặc checkout branch cũ)

**Coding:**
- [ ] Code trong Keil
- [ ] `git status` - check changes
- [ ] `git add .`
- [ ] `git commit -m "..."`

**Evening:**
- [ ] `git push`
- [ ] Tạo PR nếu xong feature
- [ ] Ensure code đã commit

---

## 🎯 Team Workflow

```
Developer A                    Developer B
     │                              │
     ├─ checkout main               ├─ checkout main
     ├─ pull                        ├─ pull
     ├─ branch feature/gpio         ├─ branch feature/uart
     │                              │
     ├─ code GPIO                   ├─ code UART
     ├─ commit                      ├─ commit
     ├─ push                        ├─ push
     │                              │
     ├─ Create PR                   ├─ Create PR
     │      ↓                       │      ↓
     │   Review ←──────────────────────→ Review
     │      ↓                              ↓
     └─ Merge to main            Merge to main
            │                              │
            └──────────┬───────────────────┘
                       ↓
                   main branch
                (code của cả team)
```

---

## 📖 Khi Cần Đọc Thêm

**Nếu gặp lỗi cụ thể:**
- Push rejected → Đọc file `git_08_troubleshooting.md`
- Conflict → Đọc file `git_05_conflict_resolution.md`

**Nếu muốn hiểu sâu:**
- Git fundamentals → `git_01_fundamentals.md`
- STM32 specific → `git_04_stm32_cubemx.md`

**Nhưng 90% cases, file này đủ dùng!**

---

## 🔑 Golden Rules

1. ✅ **Luôn pull trước khi push**
2. ✅ **Commit thường xuyên** (mỗi feature nhỏ = 1 commit)
3. ✅ **Chỉ 1 người configure CubeMX**
4. ✅ **Code trong USER CODE sections**
5. ❌ **KHÔNG push trực tiếp vào main** (dùng PR)
6. ❌ **KHÔNG force push** trừ khi chắc chắn
7. ❌ **KHÔNG sửa code ngoài USER CODE**

---

**Print file này ra và dán lên tường! 📄**

**Questions? Search file này (Ctrl+F) trước khi hỏi!**
