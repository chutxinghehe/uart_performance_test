# Git/GitHub Workflow cho Team STM32 - Hướng Dẫn Đọc

## 📚 Tổng Quan

Đây là bộ tài liệu hoàn chỉnh về Git/GitHub workflow cho team 2-5 người làm project STM32 sử dụng:
- **Keil MDK-ARM** (IDE)
- **STM32CubeMX** (Code generator)
- **Git + GitHub** (Version control)
- **Python** (Test scripts - optional)

---

## 📖 Danh Sách Files

### Core Tutorial (Đọc theo thứ tự)

1. **`git_01_fundamentals.md`** ⭐ BẮT ĐẦU Ở ĐÂY
   - Git là gì? Tại sao cần dùng?
   - Mental model: Working Directory → Staging → Commit → Remote
   - Các khái niệm cơ bản: repository, commit, branch, remote
   - **Đọc trước tiên nếu chưa biết Git**

2. **`git_02_daily_workflow.md`**
   - Setup Git lần đầu (config, SSH key)
   - Clone repository
   - Workflow hàng ngày: add, commit, push, pull
   - Branch operations: tạo, switch, delete
   - Remote operations: fetch, pull, push
   - **Đọc để biết lệnh Git cơ bản hàng ngày**

3. **`git_03_teamwork_cases.md`** ⭐ QUAN TRỌNG
   - Case A: Hai người làm hai branch riêng
   - Case B: Hai người sửa hai file khác nhau
   - Case C: Hai người sửa cùng file, khác vùng
   - Case D: Hai người sửa cùng đoạn code (CONFLICT!)
   - Case E: Branch bị outdated (merge vs rebase)
   - Case F: Chưa commit khi main thay đổi (stash)
   - Case G: Push bị rejected
   - **Đọc để hiểu teamwork như thế nào**

4. **`git_04_stm32_cubemx.md`** ⭐ ĐẶC BIỆT CHO STM32
   - Project structure STM32 + CubeMX
   - Files nào NÊN commit, files nào KHÔNG nên
   - CubeMX workflow (regenerate code, USER CODE sections)
   - Keil project files (.uvprojx vs .uvoptx)
   - CubeMX conflict resolution
   - **ĐỌC NẾU LÀM PROJECT STM32!**

5. **`git_05_conflict_resolution.md`**
   - Conflict là gì? Khi nào xảy ra?
   - Anatomy of conflict (<<<, ===, >>>)
   - Resolve conflict step-by-step
   - Tools: VS Code, mergetool
   - Conflict trong STM32 project (.ioc, .uvprojx, generated code)
   - **Đọc khi gặp conflict**

6. **`git_06_advanced.md`**
   - Merge vs Rebase (chi tiết, khi nào dùng)
   - Stash (cất code tạm thời)
   - Undo operations (restore, reset, revert, amend)
   - Tags (version numbering)
   - Cherry-pick
   - **Đọc khi cần operations nâng cao**

7. **`git_07_github_workflow.md`**
   - Pull Request workflow (tạo PR, review, merge)
   - Code review best practices
   - GitHub repository settings (protected branches)
   - Automation Level 1: Manual workflow
   - Automation Level 2: Basic CI (GitHub Actions)
   - Automation Level 3: Full testing (Python + hardware)
   - **Đọc để setup GitHub workflow cho team**

8. **`git_08_troubleshooting.md`** ⭐ KHI GẶP LỖI
   - Push rejected errors
   - Merge conflict errors
   - Branch errors
   - Detached HEAD
   - Uncommitted changes errors
   - Remote errors
   - STM32 specific issues
   - **Tra cứu khi gặp lỗi Git**

### Quick Reference

9. **`git_09_quick_reference.md`** ⭐ CHEAT SHEET
   - Tất cả lệnh Git cơ bản
   - Workflow diagrams
   - Command reference nhanh
   - **In ra dán tường, tra cứu hàng ngày**

### Conventions & Standards

10. **`git_conventions.md`** ⭐ TEAM PHẢI ĐỌC
    - Branch naming convention
    - Commit message format
    - Pull Request template
    - Code review guidelines
    - CubeMX coordination protocol
    - **Team đọc cùng nhau và agree**

### Configuration

11. **`.gitignore`** ✅ ĐÃ CẬP NHẬT
    - File ignore tối ưu cho STM32 + Keil + Python
    - Comment giải thích từng section
    - **Copy vào project của bạn**

---

## 🎯 Làm Thế Nào Để Học?

### Nếu Bạn Beginner Git (Chưa Biết Gì)

**Tuần 1: Fundamentals**
1. Đọc `git_01_fundamentals.md` - Hiểu Git là gì
2. Đọc `git_02_daily_workflow.md` - Setup và học lệnh cơ bản
3. Thực hành:
   ```bash
   git clone <repo>
   git switch -c test-branch
   # Edit file
   git add .
   git commit -m "test: learning git"
   git push origin test-branch
   ```

**Tuần 2: Teamwork**
1. Đọc `git_03_teamwork_cases.md` - Hiểu các case teamwork
2. Đọc `git_04_stm32_cubemx.md` - Hiểu STM32 workflow
3. Thực hành với teammate: Mỗi người làm branch riêng, merge vào main

**Tuần 3: Advanced**
1. Đọc `git_05_conflict_resolution.md` - Khi gặp conflict
2. Đọc `git_06_advanced.md` - Stash, undo operations
3. Đọc `git_07_github_workflow.md` - Setup PR workflow
4. Practice: Tạo PR, review lẫn nhau

**Tuần 4: Production**
1. Đọc `git_conventions.md` - Team agree conventions
2. Setup protected branches trên GitHub
3. Setup PR template
4. Apply workflow vào project thật

---

### Nếu Bạn Đã Biết Git Cơ Bản

**Focus vào:**
1. ⭐ `git_03_teamwork_cases.md` - Teamwork scenarios
2. ⭐ `git_04_stm32_cubemx.md` - STM32-specific workflow
3. ⭐ `git_conventions.md` - Standards cho team
4. `git_07_github_workflow.md` - GitHub automation

**Skip (hoặc skim):**
- `git_01_fundamentals.md` (đã biết)
- `git_02_daily_workflow.md` (đã biết)

---

### Nếu Team Đã Dùng Git Nhưng Hay Conflict

**Focus vào:**
1. ⭐ `git_04_stm32_cubemx.md` - CubeMX coordination
2. ⭐ `git_05_conflict_resolution.md` - Resolve conflicts
3. `git_conventions.md` - CubeMX protocol
4. Setup **CubeMX Coordinator** (xem git_conventions.md)

---

## 🔍 Tra Cứu Nhanh

### Tôi muốn...

| Mục đích | File cần đọc |
|----------|--------------|
| Học Git từ đầu | `git_01_fundamentals.md` |
| Biết lệnh Git hàng ngày | `git_02_daily_workflow.md`, `git_09_quick_reference.md` |
| Hiểu teamwork Git | `git_03_teamwork_cases.md` |
| Làm project STM32 | `git_04_stm32_cubemx.md` |
| Resolve conflict | `git_05_conflict_resolution.md` |
| Undo commit / stash | `git_06_advanced.md` |
| Setup GitHub PR workflow | `git_07_github_workflow.md` |
| Fix lỗi Git | `git_08_troubleshooting.md` |
| Cheat sheet nhanh | `git_09_quick_reference.md` |
| Team conventions | `git_conventions.md` |

---

### Tôi gặp vấn đề...

| Problem | Solution |
|---------|----------|
| Conflict khi merge | `git_05_conflict_resolution.md` |
| Push bị rejected | `git_08_troubleshooting.md` → Push rejected |
| CubeMX conflict | `git_04_stm32_cubemx.md` → CubeMX conflict |
| Branch outdated | `git_03_teamwork_cases.md` → Case E |
| Uncommitted changes khi pull | `git_03_teamwork_cases.md` → Case F |
| Detached HEAD | `git_08_troubleshooting.md` → Detached HEAD |
| Xóa nhầm file/commit | `git_08_troubleshooting.md` → Recovery |

---

## 📋 Checklist Cho Team

### Lần Đầu Setup Project

- [ ] Tạo repository trên GitHub
- [ ] Add `.gitignore` (copy từ file này)
- [ ] Setup protected branches (main)
- [ ] Create PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
- [ ] Đọc và agree `git_conventions.md`
- [ ] Designate CubeMX Coordinator (nếu dùng Option 1)
- [ ] Tạo README.md với build instructions

### Mỗi Developer Phải Làm

- [ ] Đọc `git_01_fundamentals.md` (nếu beginner)
- [ ] Đọc `git_02_daily_workflow.md`
- [ ] Đọc `git_03_teamwork_cases.md`
- [ ] Đọc `git_04_stm32_cubemx.md`
- [ ] Đọc `git_conventions.md`
- [ ] Setup Git config (name, email)
- [ ] Setup SSH key
- [ ] Clone repository
- [ ] Test workflow: tạo branch → commit → push → PR

### Hàng Ngày

- [ ] Pull main trước khi code
- [ ] Code trên feature branch (không code trực tiếp trên main)
- [ ] Commit thường xuyên với message chuẩn
- [ ] Push cuối ngày
- [ ] Tạo PR khi feature xong
- [ ] Review PR của teammate

---

## 🎓 Tips Học Hiệu Quả

### 1. Đọc + Thực Hành

**❌ Sai:**
Đọc hết 10 files một lúc → Quên hết

**✅ Đúng:**
Đọc 1 file → Thực hành ngay → Đọc file tiếp theo

### 2. Tạo Test Repository

```bash
# Tạo repo test để thực hành
mkdir git-practice
cd git-practice
git init

# Practice các lệnh
git add test.txt
git commit -m "test"
# ...
```

### 3. Pair Programming

- 2 người cùng làm, cùng gặp conflict
- Cùng resolve conflict
- Học nhanh hơn học một mình

### 4. Bookmark Cheat Sheet

- In `git_09_quick_reference.md` ra giấy
- Hoặc save vào bookmark
- Tra cứu thường xuyên

---

## 🚀 Workflow Recommended Cho Team Beginner

### Phase 1: Manual (Week 1-2)

**Setup:**
- Git + GitHub basic
- Protected main branch
- PR workflow

**Không dùng:**
- GitHub Actions
- Automation

**Focus:**
- Học Git cơ bản
- Thực hành teamwork
- Hiểu conflict resolution

### Phase 2: Basic CI (Week 3-4)

**Add:**
- GitHub Actions (file structure check, commit format)
- Python linting (nếu có Python scripts)

**Benefit:**
- Catch lỗi sớm
- Enforce conventions

### Phase 3: Full Automation (Month 2+)

**Add:**
- Hardware testing với Python
- Self-hosted runner (nếu cần)

**Benefit:**
- Full confidence before merge
- Production-ready workflow

---

## 📞 Support & Questions

### Khi Gặp Vấn Đề

1. **Đọc troubleshooting:** `git_08_troubleshooting.md`
2. **Tra quick reference:** `git_09_quick_reference.md`
3. **Google error message:** Copy exact error, search
4. **Ask teammate:** Conflict thường do communication
5. **GitHub Issues/Discussions:** Post question với screenshot

### Team Discussion Topics

**Weekly meeting discuss:**
- Conflict nào hay gặp tuần này?
- Workflow có cần improve không?
- Convention có cần update không?
- Ai cần help về Git?

---

## 📈 Progress Tracking

### Checklist: Bạn Đã Master Git Khi...

**Basic:**
- [ ] Clone, commit, push không cần tra cứu
- [ ] Tạo branch và switch tự nhiên
- [ ] Hiểu git status output
- [ ] Biết pull trước khi push

**Intermediate:**
- [ ] Resolve conflict một mình được
- [ ] Hiểu merge vs rebase
- [ ] Dùng stash thành thạo
- [ ] Tạo PR và review code

**Advanced:**
- [ ] Setup GitHub Actions
- [ ] Coordinate CubeMX trong team
- [ ] Recover từ mọi Git disasters
- [ ] Teach người khác

---

## 🎁 Bonus Resources

### Bên Ngoài Tutorial Này

**Interactive Learning:**
- [Learn Git Branching](https://learngitbranching.js.org/) - Visual Git tutorial
- [GitHub Skills](https://skills.github.com/) - GitHub official tutorials

**Books:**
- Pro Git (free online) - https://git-scm.com/book/en/v2

**Videos:**
- Git & GitHub Crash Course (YouTube)

**Tools:**
- GitKraken (GUI cho Git)
- GitHub Desktop (simple GUI)

---

## 📝 Contribution

Nếu phát hiện lỗi hoặc có suggestions:

1. Tạo issue trên GitHub
2. Hoặc tạo PR với fix/improvement
3. Hoặc discuss với team lead

---

## ⚖️ License & Usage

- Tài liệu này được tạo cho educational purposes
- Free to use cho team của bạn
- Modify tùy ý cho phù hợp workflow team

---

## 🙏 Credits

Tài liệu được tạo dựa trên:
- Git official documentation
- STM32 development best practices
- GitHub workflow recommendations
- Real-world team experiences

---

**Chúc team học Git hiệu quả và code vui vẻ! 🚀**

---

**Quick Start:**
1. Đọc `git_01_fundamentals.md`
2. Thực hành với `git_02_daily_workflow.md`
3. Bookmark `git_09_quick_reference.md`
4. Bắt đầu code!

**Questions?**
- Read troubleshooting first
- Ask teammate second
- Google third

**Remember:**
- Commit thường xuyên
- Pull trước khi push
- Communicate với team
- Đừng sợ làm sai - Git có thể undo gần như mọi thứ!
