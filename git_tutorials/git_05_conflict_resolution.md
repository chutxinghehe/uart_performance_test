# Git Conflict Resolution - Giải Quyết Xung Đột

## Mục Lục
- [Conflict là gì?](#conflict-là-gì)
- [Khi nào conflict xảy ra?](#khi-nào-conflict-xảy-ra)
- [Anatomy of a conflict](#anatomy-of-a-conflict)
- [Resolve conflict step-by-step](#resolve-conflict-step-by-step)
- [Tools để resolve conflict](#tools-để-resolve-conflict)
- [Conflict trong STM32 project](#conflict-trong-stm32-project)
- [Prevention strategies](#prevention-strategies)

---

## Conflict Là Gì?

**Conflict** = Git không thể tự động merge code vì có 2 phiên bản khác nhau của cùng một đoạn code.

### Ví Dụ Đơn Giản

**File `gpio.c` ban đầu:**
```c
void LED_Init(void)
{
    // Empty
}
```

**Person A sửa:**
```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}
```

**Person B sửa (cùng lúc):**
```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
}
```

**Git thắc mắc:**
- LED ở PA5 hay PC13?
- SET hay RESET?
- **Không thể quyết định** → **CONFLICT!**

---

## Khi Nào Conflict Xảy Ra?

### ✅ Không Conflict

#### Case 1: Sửa 2 file khác nhau
```
Person A: gpio.c
Person B: uart.c
→ Git auto-merge ✅
```

#### Case 2: Cùng file, khác vùng (cách xa)
```c
Person A sửa dòng 10-15
Person B sửa dòng 50-55
→ Git auto-merge ✅
```

### ⚠️ Có Conflict

#### Case 1: Cùng dòng code
```c
Person A: GPIOA->CRL = 0x00;
Person B: GPIOA->CRL = 0xFF;
→ CONFLICT ⚠️
```

#### Case 2: Vùng gần nhau (Git không chắc chắn)
```c
Person A thêm dòng 10-12
Person B thêm dòng 11-13
→ CONFLICT ⚠️ (overlap)
```

#### Case 3: Một người xóa, một người sửa
```c
Person A: Xóa function LED_Init()
Person B: Sửa function LED_Init()
→ CONFLICT ⚠️
```

---

## Anatomy of a Conflict

### Conflict Markers

Khi conflict, Git sẽ thêm markers vào file:

```c
void LED_Init(void)
{
<<<<<<< HEAD
    // Đây là CODE CỦA BẠN (local, chưa push)
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
=======
    // Đây là CODE CỦA NGƯỜI KHÁC (remote, đã push)
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
>>>>>>> a3f5d2c (feat(gpio): init LED on PA5)
}
```

### Giải Thích Markers

```
<<<<<<< HEAD
    Code của BẠN
=======
    Code của NGƯỜI KHÁC
>>>>>>> commit-hash (commit message)
```

**Phân tích:**

1. **`<<<<<<< HEAD`**
   - Bắt đầu conflict
   - `HEAD` = branch hiện tại của bạn

2. **`=======`**
   - Phân cách 2 phiên bản

3. **`>>>>>>> commit-hash`**
   - Kết thúc conflict
   - `commit-hash` = commit từ remote

### Trạng Thái File Khi Conflict

```bash
git status

# Output:
Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   Core/Src/gpio.c
```

**`both modified`** = Cả 2 bên đều sửa file này → conflict

---

## Resolve Conflict Step-by-Step

### Step 1: Detect Conflict

```bash
# Bạn đang pull hoặc merge
git pull origin main

# Output:
Auto-merging Core/Src/gpio.c
CONFLICT (content): Merge conflict in Core/Src/gpio.c
Automatic merge failed; fix conflicts and then commit the result.
```

### Step 2: Check Status

```bash
git status

# Output:
On branch feature/gpio
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   Core/Src/gpio.c
```

**Git báo:**
- Conflict ở file `gpio.c`
- Cần resolve rồi commit
- Hoặc abort để hủy bỏ merge

### Step 3: Open Conflict File

Mở `Core/Src/gpio.c` trong editor (Keil, VS Code, Notepad++):

```c
void LED_Init(void)
{
<<<<<<< HEAD
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
=======
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
>>>>>>> a3f5d2c (feat(gpio): init LED on PA5)
}
```

### Step 4: Decide Resolution

**Option 1: Giữ YOUR version (HEAD)**

```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
}
```

**Option 2: Giữ THEIR version (remote)**

```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}
```

**Option 3: Merge cả hai**

```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
}
```

**Option 4: Viết lại hoàn toàn**

```c
void LED_Init(void)
{
    // After discussion, use new approach
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_2, GPIO_PIN_SET);
}
```

### Step 5: Remove Conflict Markers

**Xóa tất cả markers:**

```
<<<<<<< HEAD
=======
>>>>>>> commit-hash
```

**File sau khi resolve (ví dụ giữ version A):**

```c
void LED_Init(void)
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
}
```

**⚠️ Lưu ý:** File KHÔNG được còn markers `<<<<`, `====`, `>>>>`!

### Step 6: Mark Resolved

```bash
# Add file (đánh dấu đã resolve)
git add Core/Src/gpio.c

# Check status
git status
# Output:
#   All conflicts fixed but you are still merging.
#   (use "git commit" to conclude merge)
```

### Step 7: Commit Merge

```bash
# Commit merge (Git tự động tạo merge message)
git commit

# Hoặc custom message:
git commit -m "merge: resolve LED_Init conflict, use PA5"
```

### Step 8: Push

```bash
git push origin feature/gpio
```

### Step 9: Verify

**Test code:**
- Build trong Keil → Đảm bảo compile được
- Flash vào board → Test chạy đúng
- Review logic → Đảm bảo merge đúng

---

## Abort Merge

Nếu resolve khó quá hoặc muốn bỏ qua:

```bash
# Abort merge, quay về trạng thái trước khi pull
git merge --abort

# File quay về version cũ (trước khi conflict)
git status
# Output: nothing to commit, working tree clean
```

**Sau abort:**
- File không còn conflict markers
- Code quay về version trước khi pull
- Có thể discuss với teammate rồi pull lại

---

## Tools Để Resolve Conflict

### 1. Text Editor (Manual)

**Pros:**
- Kiểm soát hoàn toàn
- Hiểu rõ conflict

**Cons:**
- Chậm
- Dễ sót markers

**Recommended cho:** Conflict đơn giản, ít dòng

### 2. VS Code (Built-in)

VS Code detect conflict và show UI:

```
Current Change (Your change)
[Accept Current Change] [Accept Incoming Change] [Accept Both Changes] [Compare Changes]

<<<<<<< HEAD
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
=======
Incoming Change (Change from main)
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
>>>>>>> a3f5d2c
```

**Click button:**
- **Accept Current Change:** Giữ YOUR code
- **Accept Incoming Change:** Giữ THEIR code
- **Accept Both Changes:** Giữ cả 2
- **Compare Changes:** Xem diff side-by-side

**Pros:**
- Nhanh
- Visual
- Tự động xóa markers

**Cons:**
- Không phù hợp conflict phức tạp (cần custom logic)

### 3. Git Mergetool

```bash
# Launch merge tool
git mergetool

# Git sẽ mở tool (KDiff3, Meld, P4Merge, etc.)
```

**3-way merge:**
```
┌─────────────────┬─────────────────┬─────────────────┐
│   BASE          │    LOCAL        │    REMOTE       │
│   (original)    │    (yours)      │    (theirs)     │
├─────────────────┴─────────────────┴─────────────────┤
│              RESULT (output)                        │
└─────────────────────────────────────────────────────┘
```

**Recommended tool:** VS Code (đủ cho 90% cases)

### 4. Command Line (Advanced)

```bash
# Accept all YOUR changes
git checkout --ours Core/Src/gpio.c
git add Core/Src/gpio.c

# Accept all THEIR changes
git checkout --theirs Core/Src/gpio.c
git add Core/Src/gpio.c
```

**⚠️ Cẩn thận:** Không review từng line!

---

## Conflict Trong STM32 Project

### 1. Conflict trong `main.c`

**Scenario:** 2 người viết code trong cùng USER CODE section

**Person A:**
```c
/* USER CODE BEGIN 2 */
uint8_t msgA[] = "Hello from A\r\n";
HAL_UART_Transmit(&huart2, msgA, sizeof(msgA), 100);
/* USER CODE END 2 */
```

**Person B:**
```c
/* USER CODE BEGIN 2 */
uint8_t msgB[] = "Hello from B\r\n";
HAL_UART_Transmit(&huart2, msgB, sizeof(msgB), 100);
/* USER CODE END 2 */
```

**Conflict:**
```c
/* USER CODE BEGIN 2 */
<<<<<<< HEAD
uint8_t msgB[] = "Hello from B\r\n";
HAL_UART_Transmit(&huart2, msgB, sizeof(msgB), 100);
=======
uint8_t msgA[] = "Hello from A\r\n";
HAL_UART_Transmit(&huart2, msgA, sizeof(msgA), 100);
>>>>>>> feature/uart
/* USER CODE END 2 */
```

**Resolution:** Giữ cả 2 (thường logic cho phép)

```c
/* USER CODE BEGIN 2 */
uint8_t msgA[] = "Hello from A\r\n";
HAL_UART_Transmit(&huart2, msgA, sizeof(msgA), 100);

uint8_t msgB[] = "Hello from B\r\n";
HAL_UART_Transmit(&huart2, msgB, sizeof(msgB), 100);
/* USER CODE END 2 */
```

---

### 2. Conflict trong `.ioc` File

**⚠️ NGUY HIỂM! File XML phức tạp!**

**Example conflict:**
```xml
<<<<<<< HEAD
Mcu.Pin5=PB6
Mcu.Pin6=PB7
=======
Mcu.Pin5=PB8
Mcu.Pin6=PB9
>>>>>>> feature/can
```

**⛔ KHÔNG Resolve Thủ Công!**

**Best practice:**

```bash
# Abort merge
git merge --abort

# Announce team
"Conflict ở .ioc file, mình sẽ abort và coordinate với Person A."

# Coordination:
# 1. One person pull the other's code
# 2. That person manually re-configure in CubeMX
# 3. Generate code
# 4. Commit
```

---

### 3. Conflict trong `.uvprojx` (Keil Project)

**Scenario:** 2 người cùng add files vào Keil project

**Person A adds `app_can.c`:**
```xml
<File>
  <FileName>app_can.c</FileName>
  <FilePath>User\Src\app_can.c</FilePath>
</File>
```

**Person B adds `app_uart.c`:**
```xml
<File>
  <FileName>app_uart.c</FileName>
  <FilePath>User\Src\app_uart.c</FilePath>
</File>
```

**Conflict:**
```xml
<<<<<<< HEAD
<File>
  <FileName>app_uart.c</FileName>
  <FilePath>User\Src\app_uart.c</FilePath>
</File>
=======
<File>
  <FileName>app_can.c</FileName>
  <FilePath>User\Src\app_can.c</FilePath>
</File>
>>>>>>> feature/can
```

**Resolution:** Giữ CẢ HAI files

```xml
<File>
  <FileName>app_uart.c</FileName>
  <FilePath>User\Src\app_uart.c</FilePath>
</File>
<File>
  <FileName>app_can.c</FileName>
  <FilePath>User\Src\app_can.c</FilePath>
</File>
```

**⚠️ Lưu ý:** XML phải đúng format (đóng mở tag đúng)

**Test:**
```bash
# Sau resolve, build trong Keil
# Đảm bảo cả 2 files đều được compile
```

---

### 4. Conflict trong Generated Code

**Scenario:** CubeMX regenerate code khác nhau

**Person A regenerate:**
```c
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    // ... A's clock config
}
```

**Person B regenerate (khác config):**
```c
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_OscInitStruct.HSEState = RCC_HSE_BYPASS;
    // ... B's clock config
}
```

**Resolution:**

```bash
# Discuss với team: Clock config nào đúng?
# Option 1: Giữ A's version
# Option 2: Giữ B's version
# Option 3: A hoặc B re-configure CubeMX với clock đúng
```

**⚠️ Clock config quan trọng!** Sai có thể làm MCU không chạy!

---

## Prevention Strategies

### 1. Frequent Sync

```bash
# Mỗi ngày:
git checkout main
git pull origin main
git checkout feature/your-branch
git merge main
```

**Tại sao?**
- Conflict nhỏ dần → dễ resolve
- Catch conflict sớm

### 2. Small Commits

```bash
# ❌ BAD: Commit lớn
git commit -m "Complete entire CAN driver with 10 files"

# ✅ GOOD: Commit nhỏ
git commit -m "feat(can): add CAN_Init function"
# ... code thêm ...
git commit -m "feat(can): add CAN_Transmit function"
```

**Benefit:** Conflict nhỏ, dễ resolve

### 3. Communication

```
Team chat:
"Mình đang sửa gpio.c line 50-100,
ai đang làm GPIO thì ping mình nhé."
```

### 4. File Organization

```
Thay vì cả team sửa main.c:
→ Mỗi người làm file riêng:

Person A: User/Src/app_can.c
Person B: User/Src/app_uart.c
Person C: User/Src/app_gpio.c
```

### 5. Code Review

PR review giúp:
- Catch conflict trước khi merge
- Discuss logic trước khi resolve

---

## Quick Reference

### Conflict Workflow

```bash
# 1. Detect
git pull origin main
# → CONFLICT!

# 2. Check files
git status

# 3. Open conflicted files, resolve manually

# 4. Remove markers (<<<, ===, >>>)

# 5. Test code (compile + run)

# 6. Mark resolved
git add <file>

# 7. Commit
git commit -m "merge: resolve conflict in gpio.c"

# 8. Push
git push
```

### Abort Merge

```bash
git merge --abort
```

### Check Conflict Tools

```bash
# VS Code (recommended)
code Core/Src/gpio.c

# Command line
git diff

# Mergetool
git mergetool
```

---

## Checkpoint

- [ ] Hiểu conflict là gì và khi nào xảy ra
- [ ] Biết đọc conflict markers
- [ ] Biết resolve conflict step-by-step
- [ ] Biết abort merge nếu cần
- [ ] Biết dùng VS Code để resolve
- [ ] Hiểu conflict đặc thù trong STM32 project
- [ ] Biết strategies để prevent conflict

---

**Next:** Part 6 - Advanced Operations (Merge, Rebase, Stash, Undo)

