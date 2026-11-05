# Git Conventions for STM32 Team

## Mục Lục
- [Branch naming](#branch-naming)
- [Commit messages](#commit-messages)
- [Pull Request template](#pull-request-template)
- [Code review guidelines](#code-review-guidelines)
- [CubeMX coordination](#cubemx-coordination)

---

## Branch Naming

### Convention

```
<type>/<description>
```

### Types

| Type | Purpose | Example |
|------|---------|---------|
| `feature/` | New feature development | `feature/gpio-driver` |
| `bugfix/` | Fix non-critical bugs | `bugfix/uart-rx-error` |
| `hotfix/` | Emergency production fixes | `hotfix/memory-leak` |
| `config/` | CubeMX configuration changes | `config/enable-can` |
| `refactor/` | Code restructure (no new feature) | `refactor/uart-cleanup` |
| `test/` | Experimental code | `test/new-algorithm` |
| `docs/` | Documentation only | `docs/update-readme` |

### Rules

✅ **DO:**
- Use lowercase
- Use hyphens (`-`) for spaces
- Be descriptive but concise
- Max 30 characters

❌ **DON'T:**
- Use spaces
- Use special characters (`@`, `#`, `$`)
- Use underscores (prefer hyphens)

### Examples

```bash
# ✅ GOOD
feature/gpio-led-control
feature/uart-dma-tx
bugfix/can-timeout-error
config/enable-tim2-pwm
hotfix/critical-null-pointer

# ❌ BAD
feature/GPIO_LED          # Don't use uppercase/underscore
new-feature               # No type prefix
feature/implement_the_entire_gpio_driver_with_dma  # Too long
feature/gpio led          # No spaces
```

---

## Commit Messages

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type

**Mandatory** type prefix:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactor (no functional change)
- `test`: Add/update tests
- `chore`: Maintenance tasks
- `config`: CubeMX/Keil configuration
- `merge`: Merge branches (conflict resolution)

### Scope

**Optional** module/component affected:

- `gpio`, `uart`, `can`, `spi`, `i2c`, `timer`
- `cubemx`, `keil`, `build`
- `docs`, `test`, `ci`

### Subject

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- Max 50 characters

### Body

- Optional detailed description
- Wrap at 72 characters
- Explain **what** and **why**, not **how**
- Separate from subject with blank line

### Footer

- Optional metadata
- Breaking changes: `BREAKING CHANGE: description`
- Issue references: `Closes #123`

---

### Examples

#### Simple Feature

```bash
git commit -m "feat(gpio): add LED toggle function"
```

#### Bug Fix

```bash
git commit -m "fix(uart): resolve RX buffer overflow

The receive buffer was only 64 bytes, causing overflow
when receiving large packets. Increased to 256 bytes.

Closes #42"
```

#### CubeMX Configuration

```bash
git commit -m "config(cubemx): enable CAN1 on PB8/PB9

- Configure CAN1 at 500kbps
- Enable CAN1 RX0 interrupt
- Assign PB8 (RX) and PB9 (TX)"
```

#### Merge Commit

```bash
git commit -m "merge: resolve conflict in gpio.c

Conflict between feature/gpio-pwm and feature/gpio-input.
Kept both implementations in separate functions."
```

#### Breaking Change

```bash
git commit -m "refactor(uart): change API function signatures

BREAKING CHANGE: UART_Transmit() now returns error code instead of void.
All calling code needs to handle return value.

Migration guide:
- Old: UART_Transmit(data, len);
- New: if (UART_Transmit(data, len) != HAL_OK) { ... }"
```

---

### Commit Message Template

Create template file: `~/.gitmessage`

```
# <type>(<scope>): <subject>
# |<----  Max 50 chars  ---->|

# [optional body]
# |<----  Wrap at 72 characters  ---->|

# [optional footer]

# Type: feat, fix, docs, style, refactor, test, chore, config, merge
# Scope: gpio, uart, can, timer, cubemx, keil, etc.
# Subject: imperative mood, lowercase, no period
#
# Body: explain what and why, not how
#
# Footer: BREAKING CHANGE, Closes #issue
```

**Set template:**

```bash
git config --global commit.template ~/.gitmessage
```

---

## Pull Request Template

### Create PR Template

**File:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Description

<!-- Briefly describe what this PR does -->

## Type of Change

- [ ] 🚀 New feature (non-breaking change which adds functionality)
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ⚙️ Configuration change (CubeMX, Keil settings)
- [ ] 📚 Documentation update
- [ ] ♻️ Refactor (code restructure, no functional change)
- [ ] ⚠️ Breaking change (fix or feature that causes existing functionality to change)

## Changes Made

<!-- List the main changes -->

- 
- 
- 

## Testing

<!-- Describe how you tested this -->

- [ ] Code compiles without errors
- [ ] Code compiles without warnings
- [ ] Tested on hardware (STM32 board)
- [ ] No debug code left (printf, commented code, etc.)
- [ ] Memory usage acceptable (check .map file)

### Test Results

<!-- Paste test results, screenshots, serial output, etc. -->

```
// Example:
LED toggle: ✅ OK
UART TX: ✅ OK
UART RX: ✅ OK
CAN transmit: ✅ OK
```

## Impact

<!-- What parts of the system are affected? -->

- [ ] Core functionality
- [ ] Peripheral drivers (specify: GPIO / UART / CAN / etc.)
- [ ] CubeMX configuration
- [ ] Keil project settings
- [ ] Build system
- [ ] Documentation

## Checklist

- [ ] My code follows the project's coding style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Related Issues

<!-- Link related issues -->

Closes #
Related to #

## Screenshots / Videos (if applicable)

<!-- Add screenshots or videos demonstrating the feature/fix -->

## Additional Notes

<!-- Any additional information for reviewers -->
```

---

## Code Review Guidelines

### For Reviewers

#### What to Check

##### 1. **Correctness**

- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] No potential crashes (null pointers, buffer overflows)
- [ ] Error handling adequate

##### 2. **STM32 Specific**

- [ ] HAL functions used correctly
- [ ] Interrupts configured properly
- [ ] DMA settings correct (if used)
- [ ] Clock frequencies match requirements
- [ ] GPIO pins configured correctly
- [ ] CubeMX USER CODE sections used

##### 3. **Code Quality**

- [ ] Naming clear and consistent
- [ ] Comments explain "why" not "what"
- [ ] No magic numbers (use #define)
- [ ] Functions are focused (single responsibility)
- [ ] Complexity manageable

##### 4. **Testing**

- [ ] Code tested on hardware
- [ ] Test results documented
- [ ] No known bugs

##### 5. **Repository Hygiene**

- [ ] No build artifacts committed (`.o`, `.axf`, `.bin`)
- [ ] No user-specific files (`.uvoptx`, `.uvguix`)
- [ ] Gitignore rules followed
- [ ] Commit messages follow convention

---

#### How to Give Feedback

**Levels:**

1. **💡 Suggestion:** Nice-to-have improvement
2. **❓ Question:** Asking for clarification
3. **⚠️ Issue:** Should be addressed
4. **🚨 Blocker:** Must be fixed before merge

**Examples:**

```markdown
💡 **Suggestion:** Consider using a const for this magic number
```c
-   HAL_Delay(500);
+   #define LED_TOGGLE_DELAY_MS 500
+   HAL_Delay(LED_TOGGLE_DELAY_MS);
```

```markdown
❓ **Question:** Why did we choose 500kbps for CAN bitrate? Is this documented?
```

```markdown
⚠️ **Issue:** This function doesn't check if UART is initialized
```c
void UART_Transmit(uint8_t *data, uint16_t len)
{
+   if (!UART_Initialized) return HAL_ERROR;
    HAL_UART_Transmit(&huart2, data, len, 100);
}
```

```markdown
🚨 **Blocker:** This will cause buffer overflow
```c
-   char buffer[64];
-   strcpy(buffer, input);  // input can be > 64 bytes!
+   char buffer[256];
+   strncpy(buffer, input, sizeof(buffer) - 1);
+   buffer[sizeof(buffer) - 1] = '\0';
```

---

#### Review Template Comment

```markdown
## Review Summary

**Overall:** Approve / Request Changes / Comment

**Highlights:**
- ✅ Well-tested GPIO driver implementation
- ✅ Clear code structure

**Issues:**
- ⚠️ Missing error handling in line 45
- 💡 Consider extracting magic numbers

**Testing:**
- Did you test with invalid GPIO pins?
- What happens if called before initialization?

**Next Steps:**
- [ ] Fix error handling
- [ ] Add defensive checks
- [ ] Update documentation

---

Let me know if you have questions!
```

---

### For Authors

#### Before Requesting Review

- [ ] Self-review code
- [ ] Test on hardware
- [ ] Check commit messages
- [ ] Update documentation
- [ ] Clean up debug code
- [ ] Fill PR template completely

#### Responding to Reviews

**DO:**
- ✅ Thank the reviewer
- ✅ Address ALL comments
- ✅ Explain your decisions
- ✅ Ask questions if unclear
- ✅ Mark resolved threads

**DON'T:**
- ❌ Ignore comments
- ❌ Get defensive
- ❌ Merge without approval
- ❌ Leave threads unresolved

**Example Response:**

```markdown
> ⚠️ **Issue:** Missing error handling

✅ Fixed in commit a3f5d2c. Added check:
```c
if (!GPIO_Initialized) return HAL_ERROR;
```
Thanks for catching this!
```

---

## CubeMX Coordination

### Protocol

#### Option 1: Coordinator System (Recommended for Beginners)

**Rules:**
1. One person designated as **CubeMX Coordinator**
2. Only coordinator opens CubeMX
3. Others request configuration via issue/message

**Process:**

```markdown
**Person B (needs CAN):**
@coordinator Can you enable CAN1 on PB8/PB9?
- Bitrate: 500kbps
- Mode: Normal
- Enable RX0 interrupt

**Coordinator:**
✅ Done in PR #123. Please pull and test.
```

---

#### Option 2: Self-Service (For Experienced Teams)

**Rules:**
1. **Announce** 30min before configuring
2. **Pull latest main** before opening CubeMX
3. **Merge quickly** after regenerating (< 1 hour)
4. **Never** configure simultaneously

**Process:**

```markdown
**10:00 AM - Person B:**
🔧 Will configure CubeMX to enable CAN at 10:30.
Anyone needs to merge before that?

**10:15 AM - Person C:**
✅ Merged my UART PR.

**10:30 AM - Person B:**
🔧 Configuring CubeMX now...

**10:45 AM - Person B:**
✅ Done! CAN enabled in PR #124. Please pull main.
```

---

#### Emergency: CubeMX Conflict

**If `.ioc` conflict happens:**

```bash
# STOP! Don't manually edit .ioc

# Step 1: Abort
git merge --abort

# Step 2: Communicate
# Message team: "CubeMX conflict with @person"

# Step 3: Coordinate
# One person pulls the other's branch
# That person manually re-applies their config in CubeMX
# Regenerate and commit

# Step 4: Verify
# Both test the final configuration
```

---

## File Organization Best Practices

### Structure

```
Project/
├── Core/              # Generated by CubeMX
│   ├── Src/          # Minimize edits here
│   └── Inc/          # Minimize edits here
│
├── User/              # Custom code (most edits here)
│   ├── Src/
│   │   ├── app_gpio.c
│   │   ├── app_uart.c
│   │   └── app_can.c
│   └── Inc/
│       ├── app_gpio.h
│       ├── app_uart.h
│       └── app_can.h
│
├── Drivers/           # Don't edit (generated)
├── MDK-ARM/          # Keil project
└── Python/           # Test scripts
```

### Naming Conventions (C Code)

**Files:**
```
app_<module>.c / app_<module>.h
```

**Functions:**
```c
// Public API (in header)
void GPIO_Init(void);
void GPIO_Toggle(GPIO_Pin_t pin);

// Private (static in .c)
static void GPIO_ConfigurePin(uint8_t pin);
```

**Variables:**
```c
// Global
extern uint8_t g_UartBuffer[256];

// Static global
static bool s_GPIOInitialized = false;

// Local
uint16_t ledDelay = 500;
```

**Constants:**
```c
#define LED_PIN GPIO_PIN_5
#define UART_BUFFER_SIZE 256
#define CAN_BITRATE_500K 500000
```

---

## Documentation Standards

### README.md

**Required sections:**

```markdown
# Project Name

## Description
Brief description of the project.

## Hardware
- MCU: STM32F103C8T6
- Board: Blue Pill
- Peripherals: CAN, UART, GPIO

## Software Requirements
- Keil MDK-ARM 5.x
- STM32CubeMX 6.x
- Python 3.10+ (for testing)

## Build Instructions
1. Open `MDK-ARM/Project.uvprojx` in Keil
2. Build (F7)
3. Flash to board

## Testing
```bash
cd Python
python tests/test_uart.py
```

## Team Members
- Person A: GPIO, LED control
- Person B: UART driver
- Person C: CAN protocol

## Git Workflow
See [git_conventions.md](git_conventions.md)
```

---

## Checkpoint

- [ ] Team has agreed on conventions
- [ ] PR template created
- [ ] README documented
- [ ] CubeMX coordination protocol defined
- [ ] Everyone understands commit message format

---

**Note:** Print and share this document with your team!

