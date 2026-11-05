# GitHub Workflow & Automation

## Mục Lục
- [Pull Request workflow](#pull-request-workflow)
- [Code review best practices](#code-review-best-practices)
- [GitHub repository settings](#github-repository-settings)
- [Automation Level 1: Manual](#automation-level-1-manual)
- [Automation Level 2: Basic CI](#automation-level-2-basic-ci)
- [Automation Level 3: Full testing](#automation-level-3-full-testing)

---

## Pull Request Workflow

### PR Là Gì?

**Pull Request (PR)** = Yêu cầu merge code từ branch này sang branch khác (thường là feature → main)

**Tại sao cần PR?**
- **Code review:** Team xem code trước khi merge
- **Discussion:** Comment, suggest changes
- **Quality gate:** Chỉ merge code đã review
- **Documentation:** Lịch sử rõ ràng về feature nào được merge

---

### Step-by-Step: Tạo PR

#### Step 1: Code và push branch

```bash
# Person A làm GPIO driver
git switch -c feature/gpio

# Code...
git add Core/Src/gpio.c Core/Inc/gpio.h
git commit -m "feat(gpio): implement LED control driver"

# Push lên GitHub
git push -u origin feature/gpio
```

#### Step 2: Tạo PR trên GitHub

**Trên GitHub:**

1. Vào repository
2. Click **Pull requests** tab
3. Click **New pull request**
4. Select branches:
   - **Base:** `main` (branch nhận code)
   - **Compare:** `feature/gpio` (branch muốn merge)
5. GitHub hiển thị **diff** (thay đổi)
6. Click **Create pull request**

#### Step 3: Điền PR information

**Title:**
```
feat(gpio): Add LED control driver
```

**Description template:**
```markdown
## Description
Implement GPIO driver for LED control on PA5.

## Changes
- Add `gpio.c` and `gpio.h`
- Implement `LED_Init()`, `LED_On()`, `LED_Off()`, `LED_Toggle()`
- Add HAL GPIO initialization in main.c

## Testing
- [x] Code compiles without errors
- [x] LED toggles correctly on board
- [x] No memory leaks (checked with static analysis)

## Checklist
- [x] Code follows project conventions
- [x] Comments added for complex logic
- [x] No debug code left (printf, etc.)
- [ ] Documentation updated (README.md) ← Need to do
```

**Assignees:** Chọn người review (Person B, Person C)

**Labels:** `feature`, `gpio`, `ready-for-review`

**Milestone:** Sprint 1

#### Step 4: Wait for review

**Reviewers nhận notification.**

---

### Step 5: Code Review

**Person B (reviewer) mở PR:**

1. Click **Files changed** tab
2. Xem từng file thay đổi
3. Comment nếu có vấn đề:

**Example comments:**

```c
// gpio.c line 25
void LED_Toggle(void)
{
-   HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
}
```

**Comment:**
```
💬 Person B:
"Should we add error handling here? What if GPIO is not initialized?"
```

**Person A reply:**
```
✅ Person A:
"Good point! I'll add a check."
```

4. **Request changes** hoặc **Approve**

---

### Step 6: Address review comments

**Person A fix code:**

```bash
# Sửa theo comments
vim Core/Src/gpio.c

# Add check
void LED_Toggle(void)
{
    if (GPIO_Initialized)
    {
        HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
    }
}

# Commit fix
git add Core/Src/gpio.c
git commit -m "fix(gpio): add initialization check in LED_Toggle"

# Push (tự động update PR)
git push origin feature/gpio
```

**PR tự động cập nhật với commit mới.**

---

### Step 7: Approval

**Person B review lại:**

1. Xem commit mới
2. Satisfied → Click **Approve**
3. Comment: "LGTM! (Looks Good To Me)"

---

### Step 8: Merge

**Person A (hoặc maintainer) merge PR:**

1. Click **Merge pull request**
2. Chọn merge strategy:
   - **Merge commit** (recommended cho team)
   - **Squash and merge** (nếu muốn 1 commit duy nhất)
   - **Rebase and merge** (linear history)
3. Click **Confirm merge**
4. **Delete branch** `feature/gpio` (recommended)

**Result:**
- Code từ `feature/gpio` đã vào `main`
- PR status: **Merged** ✅
- Branch `feature/gpio` trên GitHub: Deleted

---

### Step 9: Cleanup local

**Person A:**

```bash
# Update local main
git checkout main
git pull origin main

# Xóa branch local
git branch -d feature/gpio

# Done!
```

---

## Code Review Best Practices

### Reviewer Guidelines

#### What to check?

✅ **Correctness:**
- Code logic đúng không?
- Edge cases được handle chưa?
- Memory leaks?

✅ **Style:**
- Theo convention chưa?
- Naming clear không?
- Comments đủ chưa?

✅ **Testing:**
- Code tested chưa?
- Có break existing features không?

✅ **STM32 specific:**
- HAL functions dùng đúng không?
- Interrupt priority OK không?
- USER CODE sections đúng chưa?

#### How to comment?

**❌ BAD:**
```
"This code is wrong."
```

**✅ GOOD:**
```
"In `LED_Toggle()`, we should check if GPIO is initialized first to avoid 
hard fault. Consider adding:
```c
if (!GPIO_Initialized) return;
```
"
```

**Tips:**
- Be specific
- Suggest solution
- Be respectful
- Explain "why"

---

### Author Guidelines

#### Before creating PR

- [ ] Code compiles
- [ ] Code tested on hardware
- [ ] No debug code (`printf`, commented code)
- [ ] Follow conventions
- [ ] Write clear PR description

#### Responding to reviews

✅ **DO:**
- Respond to ALL comments
- Thank reviewers
- Explain your decisions
- Fix issues quickly

❌ **DON'T:**
- Ignore comments
- Argue defensively
- Force merge without addressing issues

---

## GitHub Repository Settings

### Protected Branches

**Setup:**

1. Go to **Settings** → **Branches**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Enable:
   - ☑ **Require pull request before merging**
   - ☑ **Require approvals:** 1 (hoặc 2 cho team lớn)
   - ☑ **Dismiss stale approvals** (khi có commit mới)
   - ☑ **Require status checks to pass** (nếu có CI)
   - ☑ **Require linear history** (optional)
   - ☑ **Include administrators** (recommended)

**Result:**
- Không ai push trực tiếp vào `main`
- Bắt buộc qua PR + review

---

### Branch Protection Strategy

```
main (protected)
  ↑
  PR + 1 approval required
  ↑
feature/gpio (unprotected)
  ↑
  Anyone can push
```

---

## Automation Level 1: Manual

**No CI/CD, pure Git workflow**

### Workflow

```
Developer:
1. Code locally
2. Test trên board
3. Push branch
4. Create PR
5. Wait review

Reviewer:
1. Pull branch
2. Build trong Keil
3. Test trên board
4. Approve PR

Maintainer:
5. Merge PR
```

### Pros & Cons

✅ **Pros:**
- Đơn giản
- Không cần setup CI
- Full control

❌ **Cons:**
- Chậm (manual test)
- Dễ quên test
- Không scale

**Recommended cho:** Team 2-3 người, project đơn giản

---

## Automation Level 2: Basic CI

**GitHub Actions chạy basic checks tự động**

### Setup GitHub Actions

**File: `.github/workflows/build-check.yml`**

```yaml
name: Build Check

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  lint-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check file structure
        run: |
          # Check required folders exist
          test -d Core/Src || exit 1
          test -d Core/Inc || exit 1
          test -f STM32_Project.ioc || exit 1
          echo "✅ File structure OK"
      
      - name: Check gitignore compliance
        run: |
          # Check no build artifacts committed
          if git ls-files | grep -E '\.o$|\.axf$|\.hex$'; then
            echo "❌ Build artifacts found!"
            exit 1
          fi
          echo "✅ No build artifacts"
      
      - name: Check commit messages
        run: |
          # Check commit message format
          git log --format=%s -1 | grep -E '^(feat|fix|docs|style|refactor|test|chore)\(' || exit 1
          echo "✅ Commit message format OK"

  # Keil build check (nếu có Keil license cloud)
  # Note: Keil không miễn phí, khó setup CI
  # Alternative: Cross-compile với arm-none-eabi-gcc
  
  gcc-build-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install ARM GCC
        run: |
          sudo apt-get update
          sudo apt-get install -y gcc-arm-none-eabi
      
      - name: Syntax check (không link)
        run: |
          arm-none-eabi-gcc -c Core/Src/*.c \
            -I Core/Inc \
            -I Drivers/STM32F1xx_HAL_Driver/Inc \
            -I Drivers/CMSIS/Device/ST/STM32F1xx/Include \
            -I Drivers/CMSIS/Include \
            -mcpu=cortex-m3 -mthumb \
            -Wall -Wextra
          echo "✅ Syntax check passed"
```

### Python Linting

**File: `.github/workflows/python-lint.yml`**

```yaml
name: Python Lint

on:
  pull_request:
    paths:
      - 'Python/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install flake8 black
      
      - name: Lint with flake8
        run: |
          flake8 Python/ --max-line-length=100
      
      - name: Check formatting with black
        run: |
          black --check Python/
```

### Workflow

```
Developer push:
  ↓
GitHub Actions auto-run:
  - File structure check ✅
  - Gitignore compliance ✅
  - Commit message format ✅
  - GCC syntax check ✅
  - Python lint ✅
  ↓
PR shows status:
  "All checks passed ✅"
  ↓
Reviewer approve
  ↓
Merge
```

### Pros & Cons

✅ **Pros:**
- Tự động check basic
- Catch lỗi sớm
- Free (GitHub Actions)

❌ **Cons:**
- Không test trên hardware
- Không test full build (Keil)

**Recommended cho:** Team 3-5 người, muốn automation nhẹ

---

## Automation Level 3: Full Testing

**Python scripts + Hardware-in-loop testing**

### Architecture

```
┌─────────────────────────────────────────┐
│  GitHub Actions                         │
│  ├─ Lint checks                         │
│  ├─ Build checks                        │
│  └─ Python unit tests (mock)           │
└─────────────────────────────────────────┘
              ↓ (PR merged)
┌─────────────────────────────────────────┐
│  Local CI Server (Raspberry Pi + Board)│
│  ├─ Flash firmware to board             │
│  ├─ Run Python hardware tests           │
│  │   ├─ Serial communication test       │
│  │   ├─ GPIO test                       │
│  │   └─ CAN/UART loopback test          │
│  └─ Report results to GitHub            │
└─────────────────────────────────────────┘
```

### Python Test Framework Setup

**Structure:**

```
Python/
├── tests/
│   ├── __init__.py
│   ├── test_gpio.py
│   ├── test_uart.py
│   └── test_can.py
├── tools/
│   ├── serial_comm.py
│   ├── flash_tool.py
│   └── logger.py
├── requirements.txt
└── README.md
```

**File: `Python/requirements.txt`**

```txt
pyserial==3.5
pytest==7.4.0
pytest-timeout==2.1.0
```

**File: `Python/tests/test_uart.py`**

```python
import pytest
import serial
import time

class TestUART:
    @pytest.fixture
    def serial_port(self):
        """Open serial connection to STM32 board"""
        port = serial.Serial('COM3', 115200, timeout=1)
        yield port
        port.close()
    
    def test_uart_echo(self, serial_port):
        """Test UART echo functionality"""
        # Send data
        test_msg = b"Hello STM32\r\n"
        serial_port.write(test_msg)
        time.sleep(0.1)
        
        # Read response
        response = serial_port.read(len(test_msg))
        
        # Verify echo
        assert response == test_msg, f"Expected {test_msg}, got {response}"
    
    def test_uart_throughput(self, serial_port):
        """Test UART throughput"""
        data_size = 1024
        test_data = b'A' * data_size
        
        start = time.time()
        serial_port.write(test_data)
        response = serial_port.read(data_size)
        duration = time.time() - start
        
        throughput = data_size / duration
        assert throughput > 10000, f"Throughput too low: {throughput} bytes/sec"
```

**File: `Python/tests/test_gpio.py`**

```python
import pytest
import serial
import time

class TestGPIO:
    @pytest.fixture
    def serial_port(self):
        port = serial.Serial('COM3', 115200, timeout=1)
        yield port
        port.close()
    
    def test_led_toggle(self, serial_port):
        """Test LED toggle via UART command"""
        # Send command to toggle LED
        serial_port.write(b"LED_ON\r\n")
        time.sleep(0.1)
        response = serial_port.readline()
        assert b"LED: ON" in response
        
        serial_port.write(b"LED_OFF\r\n")
        time.sleep(0.1)
        response = serial_port.readline()
        assert b"LED: OFF" in response
```

### Run Tests Locally

```bash
# Vào folder Python
cd Python

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Output:
# tests/test_uart.py::TestUART::test_uart_echo PASSED
# tests/test_uart.py::TestUART::test_uart_throughput PASSED
# tests/test_gpio.py::TestGPIO::test_led_toggle PASSED
```

### GitHub Actions with Hardware Tests

**Challenge:** GitHub Actions runners không có STM32 board connected.

**Solutions:**

**Option 1: Self-hosted runner**

Setup Raspberry Pi + STM32 board làm GitHub runner.

```yaml
# .github/workflows/hardware-test.yml
name: Hardware Tests

on:
  push:
    branches: [ main ]

jobs:
  hardware-test:
    runs-on: self-hosted  # ← Raspberry Pi
    steps:
      - uses: actions/checkout@v3
      
      - name: Flash firmware
        run: |
          st-flash write build/firmware.bin 0x8000000
      
      - name: Run Python tests
        run: |
          cd Python
          pytest tests/ -v
```

**Option 2: Mock tests on GitHub, real tests locally**

```yaml
# .github/workflows/python-test.yml
name: Python Tests (Mock)

on:
  pull_request:

jobs:
  mock-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-mock
      
      - name: Run mock tests
        run: |
          # Tests với mocked serial port
          pytest Python/tests/ -v -m "not hardware"
```

**Mark tests:**

```python
import pytest

@pytest.mark.hardware
def test_real_board(serial_port):
    """Requires real hardware"""
    pass

def test_mock_logic():
    """Mock test, no hardware needed"""
    pass
```

### Pros & Cons

✅ **Pros:**
- Full automation
- Hardware tested
- Catch bugs trước khi deploy

❌ **Cons:**
- Phức tạp setup
- Cần hardware dedicated
- Chi phí (Raspberry Pi, board)

**Recommended cho:** Team experienced, critical projects

---

## Summary: Which Level?

### Team 2 người, beginner

→ **Level 1: Manual**
- Đơn giản
- Tập trung học Git trước

### Team 3-5 người, intermediate

→ **Level 2: Basic CI**
- GitHub Actions free
- Auto-check lỗi cơ bản
- Không quá phức tạp

### Team experienced, production

→ **Level 3: Full testing**
- Automation hoàn chỉnh
- Quality assurance
- Scale được

---

## Checkpoint

- [ ] Hiểu Pull Request workflow
- [ ] Biết cách tạo và review PR
- [ ] Biết setup GitHub protected branches
- [ ] Hiểu 3 levels automation
- [ ] Biết setup GitHub Actions cơ bản
- [ ] Hiểu Python hardware test framework

---

**Next:** Part 8 - Troubleshooting & Common Errors

