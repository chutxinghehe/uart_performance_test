# Git Fundamentals - Hiểu Git từ Gốc

## Mục Lục
- [Git là gì?](#git-là-gì)
- [Tại sao cần Git cho team STM32?](#tại-sao-cần-git-cho-team-stm32)
- [Mental Model của Git](#mental-model-của-git)
- [Các khái niệm cơ bản](#các-khái-niệm-cơ-ản)

---

## Git là gì?

**Git** là một **Distributed Version Control System** (hệ thống quản lý phiên bản phân tán).

### Giải thích đơn giản:

Tưởng tượng bạn đang viết code STM32:
- Ngày 1: Bạn viết GPIO driver → **hoạt động tốt**
- Ngày 2: Bạn sửa GPIO → **code bị lỗi**
- Bây giờ bạn muốn **quay lại code ngày 1**

**Không có Git:**
- Bạn phải Ctrl+Z nhiều lần (mất công)
- Hoặc copy paste file backup `GPIO_v1.c`, `GPIO_v2_final.c`, `GPIO_v2_final_REAL.c` (rối loạn)
- Làm việc nhóm = gửi file qua email/USB (nightmare)

**Có Git:**
- Mỗi lần code chạy tốt, bạn **commit** (lưu snapshot)
- Khi lỗi, **quay lại commit trước** trong 1 giây
- Team làm việc song song, Git **tự động merge** code
- Ai sửa gì, khi nào, tại sao → **có lịch sử đầy đủ**

---

## Tại sao cần Git cho team STM32?

### Problem: Team làm project STM32 không dùng Git

**Kịch bản 1: Conflict Code**
```
Person A: Sửa UART.c
Person B: Cũng sửa UART.c
→ Ai gửi sau bị ghi đè code người kia
→ Mất công sửa
```

**Kịch bản 2: CubeMX Regenerate**
```
Person A: Configure CubeMX, regenerate code
Person B: Đang code trong main.c
→ A regenerate → Code của B bị mất
```

**Kịch bản 3: Rollback**
```
Code chạy tốt hôm qua
Hôm nay sửa → lỗi không tìm ra
Muốn quay lại phiên bản hôm qua nhưng không có backup
```

### Solution: Dùng Git

✅ **Mỗi người code trên branch riêng** → không đụng nhau  
✅ **Git detect conflict** → bắt resolve trước khi merge  
✅ **CubeMX regenerate được track** → biết ai đổi gì  
✅ **Rollback dễ dàng** → `git checkout <commit>` quay lại bất kỳ thời điểm nào  
✅ **Code review qua Pull Request** → team review code trước khi merge  

---

## Mental Model của Git

Git hoạt động theo **5 tầng**:

```
┌─────────────────────────────────────────────┐
│  5. REMOTE (GitHub)                         │  ← Team share code
│     origin/main, origin/feature/gpio        │
└─────────────────────────────────────────────┘
                    ↑ git push
                    ↓ git fetch/pull
┌─────────────────────────────────────────────┐
│  4. LOCAL REPOSITORY (Branch)               │  ← Lịch sử commit
│     main, feature/gpio, feature/uart        │
└─────────────────────────────────────────────┘
                    ↑ git commit
┌─────────────────────────────────────────────┐
│  3. STAGING AREA (Index)                    │  ← Chuẩn bị commit
│     Files đã git add                        │
└─────────────────────────────────────────────┘
                    ↑ git add
┌─────────────────────────────────────────────┐
│  2. WORKING DIRECTORY (Modified Files)      │  ← Đang code
│     GPIO.c (modified), UART.c (modified)    │
└─────────────────────────────────────────────┘
                    ↑ edit code
┌─────────────────────────────────────────────┐
│  1. FILE SYSTEM (Project Folder)            │  ← Folder STM32 của bạn
│     Core/, Drivers/, MDK-ARM/, .git/        │
└─────────────────────────────────────────────┘
```

### Giải thích từng tầng:

#### 1. **FILE SYSTEM** - Folder Project
- Là folder STM32 trên máy bạn: `C:\Projects\STM32_Project\`
- Chứa tất cả file: `.c`, `.h`, `.ioc`, Keil project, etc.

#### 2. **WORKING DIRECTORY** - Nơi bạn code
- Khi bạn mở Keil và sửa `GPIO.c` → file đang ở **Working Directory**
- Git detect file bị **modified** (thay đổi)
- Chạy `git status` để xem file nào đã sửa

#### 3. **STAGING AREA** - Khu vực chuẩn bị commit
- Sau khi sửa `GPIO.c`, bạn chạy `git add GPIO.c`
- File được đưa vào **Staging Area** = chuẩn bị commit
- Tại sao cần Staging? → Để chọn commit những file nào (không phải commit hết mọi thứ)

**Ví dụ:**
```bash
# Bạn sửa 3 file:
GPIO.c       (feature mới)
UART.c       (feature mới)
debug.c      (code test tạm)

# Bạn chỉ muốn commit GPIO và UART, không commit debug.c:
git add GPIO.c UART.c    # Chỉ add 2 file vào Staging
git commit -m "Add GPIO and UART drivers"
```

#### 4. **LOCAL REPOSITORY** - Lịch sử commit trên máy bạn
- Sau khi `git commit`, snapshot của code được lưu vào **Local Repository**
- Đây là **database Git** trên máy bạn (trong folder `.git/`)
- Chứa toàn bộ lịch sử: ai commit gì, khi nào, thay đổi gì
- Có nhiều **branch**: `main`, `feature/gpio`, `feature/uart`

#### 5. **REMOTE** - Server GitHub
- Sau khi `git push`, code từ **Local Repository** được đẩy lên **GitHub**
- Team khác có thể `git pull` để lấy code của bạn
- Remote thường có tên là `origin`
- Branch trên remote: `origin/main`, `origin/feature/gpio`

---

## Các Khái Niệm Cơ Bản

### 1. Repository (Repo)

**Repository** = Project folder có Git quản lý

```
STM32_Project/         ← Repository
├── .git/              ← Git database (KHÔNG XÓA folder này!)
├── Core/
├── Drivers/
├── MDK-ARM/
├── .gitignore
└── README.md
```

- Khi bạn `git init` hoặc `git clone` → tạo repository
- Folder `.git/` chứa toàn bộ lịch sử → **KHÔNG BAO GIỜ XÓA TAY**

### 2. Commit

**Commit** = Snapshot của code tại một thời điểm

```
Commit 1: "Init project"
  → Snapshot: main.c, GPIO.c, UART.c (version 1)

Commit 2: "Add CAN driver"
  → Snapshot: main.c, GPIO.c, UART.c, CAN.c (version 2)

Commit 3: "Fix UART bug"
  → Snapshot: main.c, GPIO.c, UART.c (fixed), CAN.c
```

Mỗi commit có:
- **Hash ID** (unique): `a3f5d2c` (7 ký tự đầu của SHA-1)
- **Author**: Người commit
- **Date**: Thời gian commit
- **Message**: Mô tả thay đổi
- **Changes**: File nào được thay đổi

**Ví dụ commit:**
```bash
commit a3f5d2c
Author: Nguyen Van A <a@example.com>
Date:   Mon Jan 15 10:30:00 2024 +0700

    feat(gpio): add GPIO initialization for LED control
    
    - Initialize GPIOA pin 5 for LED
    - Configure output push-pull mode
    - Set default state to LOW
```

### 3. Branch

**Branch** = Nhánh phát triển song song

```
main (branch chính)
  │
  ├─── A ─── B ─── C ─── D (main timeline)
  │         │
  │         └─── E ─── F (feature/gpio branch)
  │
  └─── G ─── H (feature/uart branch)
```

**Tại sao cần branch?**
- **Main branch** = code stable, chạy được
- **Feature branch** = code mới đang phát triển, có thể lỗi
- Mỗi người làm feature riêng → không ảnh hưởng nhau
- Khi feature xong, **merge** vào main

**Quy tắc:**
- `main`: Code production-ready, luôn stable
- `feature/gpio`: Code GPIO driver (Person A)
- `feature/uart`: Code UART driver (Person B)
- `bugfix/can-timeout`: Fix bug CAN timeout

### 4. Remote

**Remote** = Repository trên server (GitHub)

```
┌──────────────────────┐         ┌──────────────────────┐
│   Your Computer      │         │      GitHub          │
│   (Local Repo)       │ ←─────→ │   (Remote Repo)      │
│                      │  push   │   origin             │
│   main               │  pull   │   origin/main        │
│   feature/gpio       │  fetch  │   origin/feature/gpio│
└──────────────────────┘         └──────────────────────┘
```

- `origin` = tên mặc định của remote
- `origin/main` = branch main trên GitHub
- Local branch và remote branch **không tự động sync**

### 5. Working Directory vs Staging vs Repository

**Workflow chuẩn:**

```
Working Directory → Staging Area → Local Repository → Remote
(sửa code)           (git add)     (git commit)       (git push)
```

**Ví dụ thực tế:**

```bash
# 1. Sửa code GPIO
vim Core/Src/gpio.c          # File ở Working Directory (modified)

# 2. Check status
git status
# Output:
#   modified:   Core/Src/gpio.c

# 3. Add vào Staging
git add Core/Src/gpio.c      # File vào Staging Area

# 4. Commit vào Local Repo
git commit -m "feat(gpio): add LED toggle function"

# 5. Push lên GitHub
git push origin feature/gpio  # Đẩy lên Remote
```

---

## File States trong Git

Mỗi file có thể ở một trong 4 trạng thái:

### 1. **Untracked** - Chưa được Git quản lý
```bash
# Ví dụ: Tạo file mới
touch test.c

git status
# Output: Untracked files: test.c
```

### 2. **Unmodified** - Đã commit, chưa sửa
```bash
# File đã commit, chưa động gì
git status
# Output: nothing to commit, working tree clean
```

### 3. **Modified** - Đã sửa nhưng chưa add
```bash
# Sửa file
vim gpio.c

git status
# Output: Changes not staged for commit:
#         modified:   gpio.c
```

### 4. **Staged** - Đã add, chuẩn bị commit
```bash
git add gpio.c

git status
# Output: Changes to be committed:
#         modified:   gpio.c
```

**Diagram:**

```
Untracked ──┐
            ├─→ git add ─→ Staged ─→ git commit ─→ Unmodified
Modified ───┘                                           │
     ↑                                                  │
     └──────────────── edit file ─────────────────────┘
```

---

## Git vs GitHub - Khác nhau thế nào?

### **Git** = Tool trên máy tính
- Phần mềm command-line
- Quản lý code **local** (trên máy bạn)
- Không cần internet

### **GitHub** = Website hosting Git repos
- Server lưu trữ code
- Cho phép team **collaborate**
- Có thêm features: Pull Request, Issues, Actions, etc.

**Analogy:**
```
Git = Microsoft Word (phần mềm viết văn bản)
GitHub = Google Drive (nơi lưu trữ và share file Word)
```

**Alternatives to GitHub:**
- GitLab
- Bitbucket
- Azure DevOps
- Self-hosted Git server

---

## Tóm Tắt Mental Model

Nhớ workflow này:

```
1. Sửa code (Working Directory)
        ↓
2. git add (Staging Area)
        ↓
3. git commit (Local Repository)
        ↓
4. git push (Remote Repository / GitHub)
```

**Lấy code từ team:**

```
1. git fetch (Tải thông tin từ Remote)
        ↓
2. git merge hoặc git pull (Merge vào Local)
        ↓
3. Code của team xuất hiện trong Working Directory
```

**Key Points:**
- **Working Directory** = nơi bạn code (Keil, VS Code)
- **Staging Area** = chọn file nào commit
- **Local Repository** = lịch sử commit trên máy bạn
- **Remote** = GitHub, nơi team share code
- **Branch** = timeline phát triển song song
- **Commit** = snapshot của code

---

## Next Steps

Sau khi hiểu fundamentals, đọc tiếp:
- **Part 2: Daily Workflow** - Các lệnh Git hàng ngày
- **Part 3: Teamwork Cases** - Làm việc nhóm như thế nào
- **Part 4: STM32 + CubeMX** - Workflow đặc thù cho STM32

---

**Checkpoint:**

- [ ] Hiểu Git là gì và tại sao cần dùng
- [ ] Hiểu 5 tầng: Working Directory → Staging → Local → Remote
- [ ] Hiểu commit, branch, remote là gì
- [ ] Biết phân biệt Git vs GitHub
- [ ] Hiểu file states: Untracked, Modified, Staged, Unmodified

---

_Tài liệu này được viết cho team STM32 sử dụng Keil + CubeMX + GitHub_
