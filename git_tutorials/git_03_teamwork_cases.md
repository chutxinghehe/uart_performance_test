# Git Teamwork Cases - Các Tình Huống Làm Việc Nhóm

## Mục Lục
- [Case A: Hai người làm hai branch riêng](#case-a-hai-người-làm-hai-branch-riêng)
- [Case B: Hai người sửa hai file khác nhau](#case-b-hai-người-sửa-hai-file-khác-nhau)
- [Case C: Hai người sửa cùng file, khác vùng](#case-c-hai-người-sửa-cùng-file-khác-vùng)
- [Case D: Hai người sửa cùng đoạn code (CONFLICT)](#case-d-hai-người-sửa-cùng-đoạn-code-conflict)
- [Case E: Branch bị outdated](#case-e-branch-bị-outdated)
- [Case F: Chưa commit khi main thay đổi](#case-f-chưa-commit-khi-main-thay-đổi)
- [Case G: Push bị rejected](#case-g-push-bị-rejected)

---

## Case A: Hai Người Làm Hai Branch Riêng

### Tình Huống

Team có 2 người:
- **Person A** làm GPIO driver → branch `feature/gpio`
- **Person B** làm UART driver → branch `feature/uart`

Hai người làm **module hoàn toàn độc lập**, không chạm vào file của nhau.

```
main
 │
 ├─── feature/gpio  (Person A)
 └─── feature/uart  (Person B)
```

### Workflow Chi Tiết

#### Person A: Setup và code GPIO

```bash
# 1. Clone repository
git clone git@github.com:team/stm32-project.git
cd stm32-project

# 2. Check branch hiện tại
git branch
# Output: * main

# 3. Tạo branch feature/gpio
git switch -c feature/gpio
# Output: Switched to a new branch 'feature/gpio'

# 4. Viết code GPIO trong Keil
# File: Core/Src/gpio.c, Core/Inc/gpio.h

# 5. Check status
git status
# Output:
#   modified:   Core/Src/gpio.c
#   modified:   Core/Inc/gpio.h

# 6. Add files
git add Core/Src/gpio.c Core/Inc/gpio.h

# 7. Commit
git commit -m "feat(gpio): implement GPIO initialization for LED"

# 8. Push lên GitHub (lần đầu)
git push -u origin feature/gpio
# Output: Branch 'feature/gpio' set up to track remote branch 'feature/gpio' from 'origin'.

# 9. Tiếp tục code thêm
# ... edit gpio.c ...

# 10. Commit tiếp
git add Core/Src/gpio.c
git commit -m "feat(gpio): add LED toggle function"

# 11. Push (lần sau không cần -u)
git push
```

#### Person B: Setup và code UART (song song với A)

```bash
# 1. Clone repository
git clone git@github.com:team/stm32-project.git
cd stm32-project

# 2. Tạo branch feature/uart
git switch -c feature/uart

# 3. Viết code UART
# File: Core/Src/uart.c, Core/Inc/uart.h

# 4. Commit
git add Core/Src/uart.c Core/Inc/uart.h
git commit -m "feat(uart): implement UART driver"

# 5. Push lên GitHub
git push -u origin feature/uart
```

### Trạng Thái Trên GitHub

Sau khi cả 2 push:

```
GitHub Repository:
├── main (branch chính, vẫn là code ban đầu)
├── feature/gpio (Person A)
│   ├── Core/Src/gpio.c ✅
│   └── Core/Inc/gpio.h ✅
└── feature/uart (Person B)
    ├── Core/Src/uart.c ✅
    └── Core/Inc/uart.h ✅
```

**Quan trọng:**
- Branch `main` **chưa** có code GPIO hay UART
- Mỗi branch tồn tại **độc lập**
- Không có conflict vì 2 người làm file khác nhau

### Merge vào Main

#### Person A: Tạo Pull Request (PR)

**Trên GitHub:**
1. Mở repository
2. Click **Pull requests** → **New pull request**
3. Chọn:
   - Base: `main`
   - Compare: `feature/gpio`
4. Click **Create pull request**
5. Điền description: "Add GPIO driver for LED control"
6. Assign reviewer (Person B)
7. Create

**Person B review code:**
1. Mở PR
2. Xem Files changed
3. Comment nếu cần sửa
4. Click **Approve** (nếu OK)

**Merge:**
1. Click **Merge pull request**
2. Click **Confirm merge**
3. **Delete branch** `feature/gpio` (optional, nên xóa để gọn)

**Kết quả:**
```
main branch giờ có:
├── Core/Src/gpio.c ✅
└── Core/Inc/gpio.h ✅
```

#### Person B: Merge UART (tương tự)

1. Tạo PR: `feature/uart` → `main`
2. Review
3. Merge
4. Delete branch

**Kết quả cuối:**
```
main branch giờ có:
├── Core/Src/gpio.c ✅
├── Core/Inc/gpio.h ✅
├── Core/Src/uart.c ✅
└── Core/Inc/uart.h ✅
```

### Cleanup Local Branches

**Person A:**
```bash
# Update main local
git checkout main
git pull origin main
# Giờ main local có cả GPIO + UART code

# Xóa branch feature/gpio local
git branch -d feature/gpio
```

**Person B:**
```bash
git checkout main
git pull origin main
git branch -d feature/uart
```

### Kết Luận Case A

✅ **Hai người làm module riêng → Không conflict**  
✅ **Workflow:** Create branch → Code → Commit → Push → PR → Review → Merge  
✅ **Main luôn stable**, chỉ merge code đã review  

---

## Case B: Hai Người Sửa Hai File Khác Nhau

### Tình Huống

Cả 2 người đều code trên **cùng branch** (hoặc merge vào main), nhưng sửa **2 file hoàn toàn khác nhau**.

**Person A:**
```c
// File: Core/Src/gpio.c
void GPIO_Init(void)
{
    // Person A viết code ở đây
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}
```

**Person B:**
```c
// File: Core/Src/uart.c
void UART_Init(void)
{
    // Person B viết code ở đây
    HAL_UART_Transmit(&huart2, "Hello", 5, 100);
}
```

### Workflow

**Person A:**
```bash
# A làm trước
git checkout main
vim Core/Src/gpio.c    # Sửa gpio.c
git add Core/Src/gpio.c
git commit -m "feat(gpio): update GPIO init"
git push origin main
```

**Person B:**
```bash
# B làm sau (lúc này main đã có commit của A)
git checkout main
vim Core/Src/uart.c    # Sửa uart.c
git add Core/Src/uart.c
git commit -m "feat(uart): update UART init"

# Push → BỊ REJECT
git push origin main
# Output:
#   ! [rejected]  main -> main (fetch first)
#   error: failed to push some refs
```

**Tại sao bị reject?**
- GitHub có commit của A mà B chưa có
- B phải **pull trước** để lấy code của A

**Person B fix:**
```bash
# Pull code của A
git pull origin main

# Git auto-merge
# Output:
#   Updating a3f5d2c..b8e2a1f
#   Fast-forward
#    Core/Src/gpio.c | 3 +++
#    1 file changed, 3 insertions(+)

# Giờ push được
git push origin main
```

### Tại Sao Không Conflict?

Git merge **theo file và theo dòng**:

```
Person A thay đổi:
  Core/Src/gpio.c (dòng 10-15)

Person B thay đổi:
  Core/Src/uart.c (dòng 5-10)

→ Hai file khác nhau
→ Git tự động merge được
→ KHÔNG conflict
```

### Kết Luận Case B

✅ **Sửa 2 file khác nhau → Git auto-merge thành công**  
✅ **Luôn pull trước khi push** nếu có người khác commit trước  
✅ **Fast-forward merge** = không tạo merge commit  

---

## Case C: Hai Người Sửa Cùng File, Khác Vùng

### Tình Huống

Cả 2 sửa **cùng file** `gpio.c`, nhưng sửa **khác hàm** (khác vùng code).

**Person A sửa hàm 1:**
```c
// File: Core/Src/gpio.c

void GPIO_Init(void)
{
    // Person A thêm code ở đây
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}

void GPIO_Toggle(void)
{
    // Chưa sửa
}
```

**Person B sửa hàm 2:**
```c
// File: Core/Src/gpio.c

void GPIO_Init(void)
{
    // Chưa sửa
}

void GPIO_Toggle(void)
{
    // Person B thêm code ở đây
    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
}
```

### Workflow

**Person A:**
```bash
git checkout main
vim Core/Src/gpio.c    # Sửa GPIO_Init()
git add Core/Src/gpio.c
git commit -m "feat(gpio): implement GPIO_Init"
git push origin main
```

**Person B:**
```bash
git checkout main
vim Core/Src/gpio.c    # Sửa GPIO_Toggle()
git add Core/Src/gpio.c
git commit -m "feat(gpio): implement GPIO_Toggle"

git push origin main
# → BỊ REJECT (vì A đã push trước)

# Pull để merge
git pull origin main
```

### Git Auto-Merge

```bash
# Output:
Auto-merging Core/Src/gpio.c
Merge made by the 'recursive' strategy.
 Core/Src/gpio.c | 3 +++
 1 file changed, 3 insertions(+)
```

**Git đã merge tự động!** Tại sao?

Git phân tích:
```
Person A thay đổi gpio.c:
  Dòng 10-12 (trong GPIO_Init)

Person B thay đổi gpio.c:
  Dòng 20-22 (trong GPIO_Toggle)

→ Khác vùng (không overlap)
→ Git merge được
```

**File sau khi merge:**
```c
// Core/Src/gpio.c

void GPIO_Init(void)
{
    // Person A thêm
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}

void GPIO_Toggle(void)
{
    // Person B thêm
    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
}
```

**Person B push:**
```bash
git push origin main
# → Thành công
```

### Kết Luận Case C

✅ **Cùng file nhưng khác vùng → Git auto-merge**  
✅ **Git merge theo "hunk"** (đoạn code)  
✅ **Tạo merge commit** (không phải fast-forward)  

**Lưu ý:** Đôi khi Git merge được nhưng **logic bị sai** (compile được nhưng chạy lỗi). Cần test kỹ sau merge!

---

## Case D: Hai Người Sửa Cùng Đoạn Code (CONFLICT)

### Tình Huống

Cả 2 sửa **cùng đoạn code** trong cùng file.

**Person A:**
```c
// File: Core/Src/gpio.c
void GPIO_Init(void)
{
    GPIOA->CRL = 0x00000000;  // A set = 0x00
}
```

**Person B:**
```c
// File: Core/Src/gpio.c
void GPIO_Init(void)
{
    GPIOA->CRL = 0xFFFFFFFF;  // B set = 0xFF
}
```

Git **không biết lấy phiên bản nào** → **CONFLICT**

### Workflow

**Person A:**
```bash
git checkout main
vim Core/Src/gpio.c
# Sửa: GPIOA->CRL = 0x00000000;

git add Core/Src/gpio.c
git commit -m "feat(gpio): set CRL to 0x00"
git push origin main
```

**Person B:**
```bash
git checkout main
vim Core/Src/gpio.c
# Sửa: GPIOA->CRL = 0xFFFFFFFF;

git add Core/Src/gpio.c
git commit -m "feat(gpio): set CRL to 0xFF"

git push origin main
# → REJECT

git pull origin main
# → CONFLICT!
```

### Git Báo Conflict

```bash
git pull origin main

# Output:
Auto-merging Core/Src/gpio.c
CONFLICT (content): Merge conflict in Core/Src/gpio.c
Automatic merge failed; fix conflicts and then commit the result.
```

### Kiểm Tra File Conflict

```bash
git status
# Output:
#   Unmerged paths:
#     (use "git add <file>..." to mark resolution)
#           both modified:   Core/Src/gpio.c
```

**Mở file `gpio.c` trong editor:**

```c
void GPIO_Init(void)
{
<<<<<<< HEAD
    GPIOA->CRL = 0xFFFFFFFF;  // Person B (local)
=======
    GPIOA->CRL = 0x00000000;  // Person A (remote)
>>>>>>> a3f5d2c (feat(gpio): set CRL to 0x00)
}
```

### Ý Nghĩa Conflict Markers

```
<<<<<<< HEAD
    Code của BẠN (local, chưa push)
=======
    Code của NGƯỜI KHÁC (remote, đã push)
>>>>>>> commit-hash
```

**Git báo:**
- Đây là vùng code conflict
- Có 2 phiên bản khác nhau
- **BẠN phải chọn** giữ phiên bản nào (hoặc merge thủ công)

### Resolve Conflict

**Option 1: Giữ phiên bản của Person B (local)**

```c
void GPIO_Init(void)
{
    GPIOA->CRL = 0xFFFFFFFF;  // Giữ phiên bản B
}
```

**Option 2: Giữ phiên bản của Person A (remote)**

```c
void GPIO_Init(void)
{
    GPIOA->CRL = 0x00000000;  // Giữ phiên bản A
}
```

**Option 3: Merge cả hai (nếu logic cho phép)**

```c
void GPIO_Init(void)
{
    GPIOA->CRL = 0x00FF00FF;  // Kết hợp logic
}
```

**Option 4: Viết lại hoàn toàn**

```c
void GPIO_Init(void)
{
    // Discussion với A, viết lại theo thiết kế mới
    GPIOA->CRL = 0x33333333;
}
```

### Sau Khi Resolve

**Xóa conflict markers:**
```c
// XÓA các dòng:
// <<<<<<< HEAD
// =======
// >>>>>>> a3f5d2c

// Chỉ giữ code cuối cùng:
void GPIO_Init(void)
{
    GPIOA->CRL = 0x00000000;  // Quyết định giữ phiên bản A
}
```

**Mark resolved và commit:**
```bash
# Add file (đánh dấu resolved)
git add Core/Src/gpio.c

# Check status
git status
# Output: All conflicts fixed but you are still merging.

# Commit merge
git commit -m "merge: resolve GPIO_Init conflict, use 0x00 value"

# Push
git push origin main
```

### Nếu Resolve Sai, Muốn Abort

```bash
# Abort merge, quay lại trạng thái trước khi pull
git merge --abort

# Giờ file gpio.c trở về phiên bản của B (trước khi pull)
# Có thể thảo luận với A rồi pull lại
```

### Kết Luận Case D

⚠️ **Conflict xảy ra khi:** Cùng sửa cùng vùng code  
⚠️ **Git không tự merge được** → Phải resolve thủ công  
✅ **Workflow:** Pull → Detect conflict → Edit file → Remove markers → Add → Commit  
✅ **Communication:** Nên discuss với teammate trước khi resolve  

---

## Case E: Branch Bị Outdated

### Tình Huống

```
Trạng thái ban đầu:
main: A---B
           \
feature:    C---D

Person X merge feature khác vào main:
main: A---B---E---F
           \
feature:    C---D  ← outdated! Thiếu E và F
```

**Person A** đang code trên branch `feature/can`.  
Trong khi đó, **Person B** đã merge branch `feature/uart` vào `main`.  
Giờ branch `feature/can` của A **bị outdated** (thiếu code mới từ main).

### Tại Sao Cần Update?

1. **Tránh conflict lớn:** Merge sớm = conflict nhỏ
2. **Test với code mới:** Đảm bảo CAN hoạt động với UART mới
3. **Dễ merge sau này:** Branch gần main = dễ merge

### Workflow: Update Branch Bằng Merge

**Person A check trạng thái:**
```bash
# Đang ở feature/can
git branch
# Output: * feature/can

# Check xem main có gì mới
git fetch origin

git log --oneline --graph --all
# Output:
#   * e5f6g7h (origin/main) feat(uart): add UART driver  ← Main mới
#   | * c3d4e5f (HEAD -> feature/can) feat(can): add CAN driver
#   |/
#   * a1b2c3d Initial commit
```

**Update branch:**
```bash
# Đảm bảo code hiện tại đã commit
git status
# Output: nothing to commit, working tree clean

# Fetch code mới từ GitHub
git fetch origin

# Merge main vào feature/can
git merge origin/main

# Nếu không conflict:
# Output:
#   Merge made by the 'recursive' strategy.
#   Core/Src/uart.c | 50 +++++++++++++++++++++++++++++++++++
#   1 file changed, 50 insertions(+)

# Nếu có conflict → Resolve (như Case D)
```

**Sau merge:**
```
main: A---B---E---F
           \       \
feature:    C---D---G  ← G là merge commit (có code E, F)
```

**Push updated branch:**
```bash
git push origin feature/can
```

### Workflow: Update Branch Bằng Rebase

**Rebase = "Đặt lại base của branch"**

```
Trước rebase:
main: A---B---E---F
           \
feature:    C---D

Sau rebase:
main: A---B---E---F
                   \
feature:            C'---D'  ← C và D được "replay" lên F
```

**Commands:**
```bash
# Đang ở feature/can
git fetch origin

# Rebase lên main
git rebase origin/main

# Nếu có conflict:
# 1. Resolve conflict trong file
# 2. git add <file>
# 3. git rebase --continue

# Nếu muốn abort:
# git rebase --abort

# Sau rebase thành công, push
# ⚠️ Phải force push vì history thay đổi
git push --force origin feature/can
```

### Merge vs Rebase - Chọn Cái Nào?

| | Merge | Rebase |
|---|---|---|
| **Lịch sử** | Giữ nguyên, có merge commit | Viết lại lịch sử, linear |
| **Conflict** | Resolve 1 lần | Resolve từng commit (nhiều lần) |
| **Push** | `git push` bình thường | Cần `git push --force` |
| **Safety** | An toàn hơn | Nguy hiểm nếu dùng sai |
| **Khi nào dùng** | Branch đã push, có người khác dùng | Branch cá nhân, chưa ai dùng |

**Recommendation cho beginner:**
✅ **Dùng Merge** - An toàn, dễ hiểu, dễ undo  
⚠️ **Tránh Rebase** - Dễ làm mất code nếu không hiểu rõ  

### Case: Chưa Commit Khi Pull

**Person A:**
```bash
# Đang code can.c, chưa commit
vim Core/Src/can.c

# Muốn pull main mới
git pull origin main
# Output:
#   error: Your local changes to the following files would be overwritten by merge:
#       Core/Src/can.c
#   Please commit your changes or stash them before you merge.
```

**Option 1: Commit trước**
```bash
git add Core/Src/can.c
git commit -m "WIP: CAN driver in progress"
git pull origin main
```

**Option 2: Stash (xem Part 6)**
```bash
git stash
git pull origin main
git stash pop
```

### Kết Luận Case E

✅ **Thường xuyên sync với main** để tránh outdated  
✅ **Dùng merge** cho beginner (an toàn)  
✅ **Rebase** chỉ dùng khi hiểu rõ và branch chưa share  
✅ **Luôn commit hoặc stash** trước khi pull/merge  

---

## Case F: Chưa Commit Khi Main Thay Đổi

### Tình Huống

```
Person A đang code trên feature/can
↓
A chưa commit code (còn ở Working Directory)
↓
Person B merge code vào main
↓
A muốn pull main mới nhưng có uncommitted changes
```

### Workflow

**Person A:**
```bash
# Đang code can.c
vim Core/Src/can.c

# Check status
git status
# Output: modified:   Core/Src/can.c

# Muốn pull main
git checkout main
# Output:
#   error: Your local changes would be overwritten by checkout
```

### Option 1: Commit Code

```bash
# Commit code hiện tại
git add Core/Src/can.c
git commit -m "WIP: CAN driver work in progress"

# Giờ có thể switch
git checkout main
git pull origin main

# Quay lại feature branch
git checkout feature/can
```

### Option 2: Stash (Cất Code Tạm)

**Stash = "Cất code vào ngăn kéo"**

```bash
# Stash uncommitted changes
git stash
# Output: Saved working directory and index state WIP on feature/can

# Giờ Working Directory clean
git status
# Output: nothing to commit, working tree clean

# Pull main
git checkout main
git pull origin main

# Quay lại feature branch
git checkout feature/can

# Lấy code ra khỏi stash
git stash pop
# Output: Changes reapplied from stash

# Code can.c quay lại
```

**Stash commands:**
```bash
# Cất code vào stash
git stash

# Xem danh sách stash
git stash list
# Output:
#   stash@{0}: WIP on feature/can
#   stash@{1}: WIP on feature/gpio

# Lấy stash gần nhất (và xóa khỏi stash list)
git stash pop

# Lấy stash gần nhất (KHÔNG xóa)
git stash apply

# Xóa stash
git stash drop stash@{0}

# Xóa tất cả stash
git stash clear
```

### Option 3: Discard Changes (XÓA CODE)

⚠️ **Nguy hiểm! Code sẽ mất!**

```bash
# Xóa tất cả uncommitted changes
git restore Core/Src/can.c
# hoặc
git checkout -- Core/Src/can.c

# Code can.c quay về version đã commit
```

### Khi Nào Dùng Gì?

| Situation | Solution |
|-----------|----------|
| Code quan trọng, muốn giữ | Commit |
| Code chưa xong, giữ tạm | Stash |
| Code test, không cần | Restore (discard) |

### Kết Luận Case F

✅ **Commit** = Giữ code vĩnh viễn trong history  
✅ **Stash** = Cất code tạm thời, lấy ra sau  
⚠️ **Restore** = XÓA code (cẩn thận!)  

---

## Case G: Push Bị Rejected

### Tình Huống

```bash
git push origin feature/can
# Output:
#   ! [rejected]  feature/can -> feature/can (non-fast-forward)
#   error: failed to push some refs
#   hint: Updates were rejected because the tip of your current branch is behind
```

### Nguyên Nhân

```
Remote (GitHub):
feature/can: A---B---C---D

Local (your computer):
feature/can: A---B---E

→ Remote có D, local không có
→ Git reject push để tránh mất D
```

**Tại sao lại xảy ra?**
- Có người khác push lên `feature/can` trước bạn
- Hoặc bạn push từ máy khác
- Hoặc bạn đã force push trước đó

### Fix: Pull Trước Rồi Push

```bash
# Pull code mới từ GitHub
git pull origin feature/can

# Nếu không conflict:
# Output: Merge made by the 'recursive' strategy.

# Nếu có conflict → Resolve như Case D

# Push lại
git push origin feature/can
```

**Sau pull:**
```
Local:
feature/can: A---B---E---F  (F = merge commit, có cả D và E)
```

### Fix: Rebase (Alternative)

```bash
git pull --rebase origin feature/can
# = git fetch + git rebase

# Nếu conflict → Resolve rồi:
git add <file>
git rebase --continue

# Push
git push origin feature/can
```

### Force Push (NGUY HIỂM!)

⚠️ **Chỉ dùng khi:**
- Branch là của bạn, không ai dùng
- Bạn chắc chắn muốn ghi đè remote

```bash
git push --force origin feature/can
# → Remote sẽ mất commit D!
```

**NEVER force push to `main`!** Sẽ làm mất code của team.

### Kết Luận Case G

✅ **Push rejected = Remote có commit mới**  
✅ **Fix:** Pull → Merge/Resolve → Push  
⚠️ **Force push:** Chỉ dùng khi chắc chắn  

---

## Summary - Quy Tắc Vàng Teamwork

### 1. **Branch Strategy**
```
main (protected)
  ├── feature/<module>  (mỗi người một branch)
  ├── bugfix/<issue>
  └── hotfix/<urgent>
```

### 2. **Workflow Checklist**

**Bắt đầu ngày:**
- [ ] `git checkout main`
- [ ] `git pull origin main`
- [ ] `git checkout feature/your-branch`
- [ ] `git merge main` (update branch)

**Coding:**
- [ ] Code in Keil
- [ ] `git status` (check changes)
- [ ] `git add <files>`
- [ ] `git commit -m "type(scope): description"`
- [ ] `git push origin feature/your-branch`

**End of day:**
- [ ] Đảm bảo code đã commit
- [ ] Push lên GitHub
- [ ] Tạo PR nếu feature xong

### 3. **Conflict Prevention**

✅ **DO:**
- Thường xuyên pull main
- Commit nhỏ, commit thường xuyên
- Communicate trước khi sửa file chung
- Review code của nhau

❌ **DON'T:**
- Để branch outdated quá lâu
- Commit quá lớn (nhiều file, nhiều thay đổi)
- Sửa code generated của CubeMX trực tiếp
- Force push lên main

### 4. **Communication Protocol**

**Trước khi configure CubeMX:**
```
Team chat:
"Mình sẽ configure CubeMX để enable CAN peripheral lúc 2pm,
ai cần merge code vào main thì làm trước đó nhé."
```

**Khi gặp conflict:**
```
"Mình đang resolve conflict ở gpio.c,
có vẻ cả 2 đều sửa GPIO_Init().
A có thể discuss logic không?"
```

---

## Checkpoint

- [ ] Hiểu workflow: Create branch → Code → PR → Merge
- [ ] Biết case nào Git auto-merge, case nào conflict
- [ ] Biết cách resolve conflict
- [ ] Biết update branch khi outdated
- [ ] Biết dùng stash khi chưa commit
- [ ] Biết fix push rejected

---

**Next:** Part 4 - STM32 + CubeMX Specific Workflow

