<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=Contributing%20to%20Execra&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=40&desc=Your%20Guide%20to%20Open%20Source%20Contribution&descAlignY=62&descAlign=50&descSize=18" width="100%" alt="Contributing Banner"/>

<br/>

[![GirlScript Summer of Code](https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=for-the-badge&logo=girlscript&logoColor=white)](https://gssoc.girlscript.tech/)
&nbsp;
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge&logo=git)](https://github.com/yourusername/execra/pulls)
&nbsp;
[![Open Source](https://img.shields.io/badge/Open%20Source-❤️%20Love-red?style=for-the-badge)](https://opensource.org/)

<br/>

> *"Great software is built by great communities. Welcome to ours."*

</div>

---

## 📑 Table of Contents

<details open>
<summary><b>Click to expand / collapse</b></summary>

- [👋 Welcome](#-welcome)
- [📋 Before You Start](#-before-you-start)
- [🧭 Ways to Contribute](#-ways-to-contribute)
- [⚙️ Development Environment Setup](#️-development-environment-setup)
- [🌿 Branching Strategy](#-branching-strategy)
- [💻 Coding Standards](#-coding-standards)
- [✅ Commit Message Convention](#-commit-message-convention)
- [🔁 Pull Request Process](#-pull-request-process)
- [🔍 Finding & Claiming Issues](#-finding--claiming-issues)
- [🏷️ Issue Labels & GSSoC Points](#️-issue-labels--gssoc-points)
- [🧪 Testing Guidelines](#-testing-guidelines)
- [📁 Project Structure Reference](#-project-structure-reference)
- [🚫 What NOT to Do](#-what-not-to-do)
- [🔐 Security Vulnerabilities](#-security-vulnerabilities)
- [📜 Code of Conduct](#-code-of-conduct)
- [💬 Community & Support](#-community--support)
- [🙏 Recognition](#-recognition)

</details>

---

## 👋 Welcome

Thank you for your interest in contributing to **Execra** — the Universal Execution Intelligence Layer! 🎉

Execra is an open-source, multimodal AI system designed to observe your actions in real time and guide you through correct execution **before mistakes happen**. It is proudly part of **GirlScript Summer of Code (GSSoC) 2026**, and we warmly welcome contributors of all backgrounds, experience levels, and skill sets.

Whether you're fixing a typo, writing a test, building a new feature, or improving documentation — **every contribution matters**.

```
┌────────────────────────────────────────────────────────────┐
│                  THE EXECRA PHILOSOPHY                      │
│                                                             │
│   Observe → Understand → Guide → Correct                    │
│                                                             │
│   Apply this to your contributions too:                     │
│   Read → Understand the issue → Code the fix → PR it       │
└────────────────────────────────────────────────────────────┘
```

---

## 📋 Before You Start

Please read the following documents **before** making any contributions:

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview, architecture & setup |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community behavior expectations |
| [LICENSE](LICENSE) | MIT License terms |

> [!IMPORTANT]
> By contributing to Execra, you agree that your contributions will be licensed under the **MIT License**.

---

## 🧭 Ways to Contribute

There are many ways you can contribute to Execra, regardless of experience level:

<table>
<tr>
<td width="50%" valign="top">

### 🐛 Bug Reports
- Found something broken?
- Open a [Bug Report Issue](https://github.com/yourusername/execra/issues/new?template=bug_report.md)
- Include steps to reproduce, expected vs actual behavior, and screenshots if possible

### 💡 Feature Requests
- Have an idea to improve Execra?
- Open a [Feature Request Issue](https://github.com/yourusername/execra/issues/new?template=feature_request.md)
- Describe the problem it solves, not just the solution

### 📖 Documentation
- Improve existing docs or write new ones
- Fix typos, broken links, or outdated content
- Add usage examples, tutorials, or API references

</td>
<td width="50%" valign="top">

### 🔧 Code Contributions
- Fix bugs from the issues list
- Implement new features or modules
- Improve performance and efficiency
- Refactor or clean up existing code

### 🧪 Testing
- Write unit or integration tests
- Improve test coverage for untested modules
- Report flaky or failing tests

### 🎨 UI / UX
- Improve the frontend overlay or guidance panel
- Add accessibility improvements
- Design new visual components

</td>
</tr>
</table>

---

## ⚙️ Development Environment Setup

### System Prerequisites

Before cloning the project, ensure you have the following installed:

| Dependency | Minimum Version | Purpose |
|-----------|----------------|---------|
| Python | 3.10+ | Core backend runtime |
| Node.js | 18+ | Frontend / Overlay build |
| FFmpeg | Any recent | Camera stream processing |
| Git | 2.30+ | Version control |
| Docker *(optional)* | 20+ | Container-based setup |

### Step-by-Step Local Setup

```bash
# 1. Fork the repository on GitHub
#    Click the "Fork" button at https://github.com/yourusername/execra

# 2. Clone YOUR fork (replace YOUR_USERNAME)
git clone https://github.com/YOUR_USERNAME/execra.git
cd execra

# 3. Add the original repo as the upstream remote
git remote add upstream https://github.com/yourusername/execra.git

# 4. Verify remotes are configured correctly
git remote -v
# origin    https://github.com/YOUR_USERNAME/execra.git (fetch)
# upstream  https://github.com/yourusername/execra.git (fetch)

# 5. Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate         # Linux / macOS
venv\Scripts\activate            # Windows

# 6. Install all Python dependencies
pip install -r requirements.txt

# 7. Install development dependencies (linters, formatters, test tools)
pip install -r requirements-dev.txt

# 8. Install frontend dependencies
cd frontend
npm install
cd ..

# 9. Configure environment variables
cp .env.example .env
# Open .env and add your API keys (OpenAI / Gemini)

# 10. Download YOLO model weights
python scripts/download_models.py

# 11. Verify setup by running tests
python -m pytest tests/

# 12. Start Execra locally
python main.py
```

### Docker Setup (Alternative)

```bash
# Build and run all services with Docker Compose
docker-compose up --build

# Services will be available at:
# API Server   → http://localhost:8000
# Frontend     → http://localhost:3000
# API Docs     → http://localhost:8000/docs
```

### Keeping Your Fork Updated

Always sync your fork with upstream before starting new work:

```bash
# Fetch latest changes from upstream
git fetch upstream

# Switch to your local main branch
git checkout main

# Merge upstream changes into your local main
git merge upstream/main

# Push updated main to your fork
git push origin main
```

---

## 🌿 Branching Strategy

We follow a **feature-branch workflow**. Never commit directly to `main`.

```
main
 ├── feature/screen-delta-detection
 ├── feature/trust-scorer-v2
 ├── fix/camera-feed-memory-leak
 ├── fix/ocr-null-handling-88
 ├── docs/api-reference-update
 └── test/context-engine-coverage
```

### Branch Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| New Feature | `feature/short-description` | `feature/consequence-simulation-engine` |
| Bug Fix | `fix/issue-number-description` | `fix/88-camera-feed-memory-leak` |
| Documentation | `docs/what-you-are-documenting` | `docs/trust-scorer-api-reference` |
| Tests | `test/module-being-tested` | `test/context-engine-unit-tests` |
| Refactor | `refactor/component-name` | `refactor/llm-client-abstraction` |
| Chore | `chore/task-description` | `chore/update-yolo-dependencies` |

### Creating a Branch

```bash
# Always branch off from the latest main
git checkout main
git pull upstream main

# Create and switch to your new branch
git checkout -b feature/your-feature-name

# ... make your changes ...

# Push your branch to your fork
git push origin feature/your-feature-name
```

---

## 💻 Coding Standards

Consistent code is easier to review, maintain, and debug. Please follow these standards:

### Python Style (Backend)

- Follow **[PEP 8](https://pep8.org/)** — Python's official style guide
- Use **[Black](https://black.readthedocs.io/)** for auto-formatting (line length: 88)
- Use **[isort](https://pycqa.github.io/isort/)** for import ordering
- Use **[flake8](https://flake8.pycqa.org/)** for linting

```bash
# Format your code before committing
black .
isort .
flake8 .
```

#### Python Code Rules

```python
# ✅ GOOD — descriptive names, type hints, docstrings
def calculate_trust_score(
    llm_confidence: float,
    rule_validation: bool,
    execution_trace_match: float
) -> dict:
    """
    Calculate the overall trust score for an instruction.

    Args:
        llm_confidence: Confidence score from the LLM (0.0 - 1.0)
        rule_validation: Whether rule-based validator approved the instruction
        execution_trace_match: Similarity to known safe execution patterns

    Returns:
        dict: Contains 'score', 'level', and 'reasoning' keys
    """
    ...

# ❌ BAD — unclear names, no type hints, no docstring
def calc(a, b, c):
    ...
```

#### Key Python Rules

- **Always add type hints** to function signatures
- **Always add docstrings** to public functions, classes, and modules
- **Max line length**: 88 characters (Black default)
- **No unused imports** — use `isort` to clean up
- **No bare `except:`** — always catch specific exceptions
- **Use f-strings**, not `.format()` or `%`

### JavaScript / TypeScript Style (Frontend)

- Follow **[ESLint](https://eslint.org/)** rules defined in `.eslintrc`
- Use **[Prettier](https://prettier.io/)** for formatting
- Prefer `const` over `let`; avoid `var`
- Use descriptive component and variable names

```bash
# Lint and format frontend code
npm run lint
npm run format
```

### General Rules for All Code

- **No hardcoded secrets or API keys** — use environment variables via `.env`
- **No commented-out dead code** in PRs — remove it
- **Keep functions small and focused** — single responsibility principle
- **Write self-documenting code** — names should explain intent
- **Add comments only when the *why* is not obvious**, not the *what*

---

## ✅ Commit Message Convention

We follow the **[Conventional Commits](https://www.conventionalcommits.org/)** specification. All commit messages must adhere to this format:

```
<type>(<optional scope>): <short description>

[optional body]

[optional footer: e.g., Closes #42]
```

### Commit Types

| Type | When to Use | Example |
|------|------------|---------|
| `feat` | Adding a new feature | `feat: implement real-time screen delta detection` |
| `fix` | Fixing a bug | `fix(camera): resolve memory leak in feed handler (#88)` |
| `docs` | Documentation changes only | `docs: add API reference for context engine` |
| `style` | Code formatting (no logic change) | `style: reformat trust_scorer.py with black` |
| `refactor` | Code restructuring (no feature/bug) | `refactor: extract LLM client into abstraction layer` |
| `test` | Adding or updating tests | `test: add unit tests for consequence simulator` |
| `chore` | Build, tooling, or dependency changes | `chore: update YOLOv8 to v8.2.0` |
| `perf` | Performance improvement | `perf: optimize screen capture frame rate` |
| `ci` | CI/CD configuration changes | `ci: add Python 3.12 to test matrix` |
| `build` | Build system changes | `build: add docker multi-stage build` |

### Commit Rules

```
✅  feat: add OCR support for multi-language text detection (#42)
✅  fix(perception): handle null frame in screen_capture.py
✅  docs: update README getting started section
✅  test: add edge case coverage for trust scorer

❌  fixed stuff
❌  WIP
❌  update
❌  changes
❌  asdfgh
```

> [!NOTE]
> Keep the subject line under **72 characters**. Use the body to explain **why** the change was made, not what — the diff shows that.

---

## 🔁 Pull Request Process

### PR Workflow

```
YOUR CONTRIBUTION JOURNEY

 ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
 │  Claim   │──►│  Branch  │──►│  Code &   │──►│  Open    │
 │  Issue   │   │  Created │   │   Test    │   │   PR     │
 └──────────┘   └──────────┘   └───────────┘   └────┬─────┘
                                                     │
              ┌──────────────────────────────────────┘
              │
 ┌────────────▼───┐   ┌──────────────┐   ┌───────────────┐
 │  Code Review   │──►│   Changes    │──►│   MERGED! 🎉  │
 │  (Maintainer)  │   │  Requested?  │   │  Points Added │
 └────────────────┘   └──────────────┘   └───────────────┘
```

### Before Opening a PR

- [ ] I have read and followed the contribution guidelines
- [ ] My branch is up to date with `upstream/main`
- [ ] All existing tests pass (`python -m pytest tests/`)
- [ ] I have written tests for my changes (where applicable)
- [ ] My code follows the coding standards (Black, isort, flake8 pass)
- [ ] I have added/updated docstrings for all public functions I touched
- [ ] I have updated documentation if my changes affect behavior
- [ ] I have linked the relevant GitHub issue in my PR
- [ ] My PR title follows the Conventional Commits format

### PR Title Format

```
feat(perception): add multi-language OCR support (#42)
fix(camera): resolve memory leak in frame handler (#88)
docs: update API reference for context engine
```

### PR Description Template

When opening a PR, fill out the provided template completely:

```markdown
## 🔗 Related Issue
Closes #<issue-number>

## 📝 Summary of Changes
Brief description of what was changed and why.

## 🔍 Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test addition
- [ ] Refactor / Code cleanup

## 🧪 How Was This Tested?
Describe the tests you ran and how to reproduce them.

## 📸 Screenshots (if applicable)
Add screenshots or screen recordings if this affects the UI.

## ✅ Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Docstrings and comments added/updated
- [ ] Documentation updated if needed
```

### Review Process

1. **Auto-checks run** — CI will lint, test, and format-check your code
2. **Maintainer review** — A maintainer will review within 3–5 business days
3. **Address feedback** — If changes are requested, push new commits to the same branch
4. **Approval & merge** — Once approved, a maintainer will merge your PR
5. **GSSoC points** — Points are assigned after successful merge

> [!WARNING]
> Do NOT force-push to a branch that has an open PR — it makes reviewing harder. Instead, add new commits.

---

## 🔍 Finding & Claiming Issues

### Step-by-Step: Claiming an Issue

```
1. Go to → https://github.com/yourusername/execra/issues

2. Filter by labels:
   - "good first issue" → for beginners
   - "help wanted"      → open for all
   - "gssoc-2026"       → GSSoC specific tasks

3. READ the full issue description before commenting

4. Comment: "I'd like to work on this! [brief plan of approach]"

5. Wait for a maintainer to assign it to you (usually within 24–48h)

6. Once assigned, create a branch and start working
```

> [!IMPORTANT]
> **Do NOT submit a PR for an issue that is not assigned to you.** This prevents duplicate work and ensures fair contribution tracking.

### Issue Assignment Rules

- Each contributor may have **up to 2 issues assigned** at a time
- If no progress is made within **7 days**, the issue may be unassigned and reopened
- Do not ask to be assigned to multiple issues at once before completing existing ones

---

## 🏷️ Issue Labels & GSSoC Points

> Points are awarded by GSSoC 2026 based on issue difficulty and contribution quality.

<table>
<thead>
<tr>
<th>Label</th>
<th>Points</th>
<th>Difficulty</th>
<th>Typical Tasks</th>
</tr>
</thead>
<tbody>
<tr>
<td><img src="https://img.shields.io/badge/good%20first%20issue-4CAF50?style=flat-square"/> <code>good first issue</code></td>
<td><b>10 pts</b></td>
<td>⭐ Beginner</td>
<td>Fixing typos, adding docstrings, small UI tweaks, writing examples</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/easy-66BB6A?style=flat-square"/> <code>easy</code></td>
<td><b>25 pts</b></td>
<td>⭐⭐ Easy</td>
<td>Adding unit tests, small bug fixes, minor feature additions</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/medium-FF9800?style=flat-square"/> <code>medium</code></td>
<td><b>45 pts</b></td>
<td>⭐⭐⭐ Medium</td>
<td>Feature modules, integration tasks, significant bug fixes</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/hard-F44336?style=flat-square"/> <code>hard</code></td>
<td><b>60 pts</b></td>
<td>⭐⭐⭐⭐ Hard</td>
<td>Core architecture, new domain engines, performance optimization</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/documentation-1976D2?style=flat-square"/> <code>documentation</code></td>
<td><b>10–25 pts</b></td>
<td>Any</td>
<td>Guides, API docs, tutorials, diagrams</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/help%20wanted-blueviolet?style=flat-square"/> <code>help wanted</code></td>
<td>Varies</td>
<td>Varies</td>
<td>Any contributor, check issue details</td>
</tr>
</tbody>
</table>

### Additional Label Reference

| Label | Meaning |
|-------|---------|
| `bug` | Confirmed bug that needs fixing |
| `enhancement` | Improvement to existing feature |
| `question` | Needs clarification before work begins |
| `wip` | Work in progress — do not pick up |
| `duplicate` | Issue already reported elsewhere |
| `invalid` | Not a valid bug/feature |
| `blocked` | Waiting on another issue/dependency |
| `gssoc-2026` | Officially part of GSSoC 2026 program |

---

## 🧪 Testing Guidelines

All contributions to core modules **must include tests**. We use `pytest` for Python testing.

### Running Tests

```bash
# Run the full test suite
python -m pytest tests/

# Run specific test file
python -m pytest tests/unit/test_trust_scorer.py

# Run with verbose output
python -m pytest tests/ -v

# Run and show coverage report
python -m pytest tests/ --cov=core --cov-report=term-missing

# Run only tests matching a keyword
python -m pytest tests/ -k "trust_score"
```

### Test Structure

```
tests/
├── unit/               # Test individual functions/classes in isolation
│   ├── test_trust_scorer.py
│   ├── test_context_engine.py
│   ├── test_consequence_sim.py
│   └── test_ocr_engine.py
│
├── integration/        # Test interactions between modules
│   ├── test_perception_pipeline.py
│   └── test_intelligence_core.py
│
└── e2e/                # End-to-end workflows (full system tests)
    └── test_digital_domain_workflow.py
```

### Writing a Test

```python
# tests/unit/test_trust_scorer.py

import pytest
from core.intelligence.trust_scorer import calculate_trust_score


class TestCalculateTrustScore:
    """Unit tests for the trust score calculation function."""

    def test_high_confidence_returns_trusted(self):
        """Score above 0.8 should return 'trusted' level."""
        result = calculate_trust_score(
            llm_confidence=0.95,
            rule_validation=True,
            execution_trace_match=0.90
        )
        assert result["level"] == "trusted"
        assert result["score"] >= 0.80

    def test_low_confidence_returns_uncertain(self):
        """Score below 0.5 should return 'uncertain' level."""
        result = calculate_trust_score(
            llm_confidence=0.30,
            rule_validation=False,
            execution_trace_match=0.20
        )
        assert result["level"] == "uncertain"

    def test_returns_required_keys(self):
        """Result must always contain 'score', 'level', 'reasoning'."""
        result = calculate_trust_score(0.7, True, 0.6)
        assert "score" in result
        assert "level" in result
        assert "reasoning" in result

    def test_invalid_confidence_raises_error(self):
        """Confidence values outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_trust_score(1.5, True, 0.8)
```

### Test Coverage Requirements

- **New modules**: Minimum **80% test coverage** required
- **Bug fixes**: Must include a regression test proving the bug is fixed
- **Refactors**: All existing tests must continue to pass

---

## 📁 Project Structure Reference

Understanding the codebase before contributing is essential:

```
execra/
│
├── 📁 core/                          ← Main Python backend
│   ├── perception/
│   │   ├── screen_capture.py         # Screen capture engine
│   │   ├── camera_feed.py            # Camera input handler
│   │   └── ocr_engine.py             # Text recognition (Tesseract)
│   │
│   ├── intelligence/
│   │   ├── llm_client.py             # LLM abstraction (GPT-4o / Gemini)
│   │   ├── context_engine.py         # Session context manager
│   │   ├── consequence_sim.py        # Outcome prediction engine
│   │   └── trust_scorer.py           # Confidence scoring per instruction
│   │
│   ├── digital/
│   │   ├── code_tracer.py            # Runtime execution tracer (sys.settrace)
│   │   ├── error_detector.py         # Logical error identification
│   │   └── task_decomposer.py        # High-level goal → structured steps
│   │
│   ├── physical/
│   │   ├── object_detector.py        # YOLOv8-based object detection
│   │   ├── task_recognizer.py        # Physical task classifier from vision
│   │   └── action_validator.py       # Real-world action checker
│   │
│   └── hybrid/
│       ├── mode_manager.py           # Passive / Active / Mixed mode switcher
│       ├── action_logger.py          # Undo/Replay/Recovery stack
│       └── guidance_dispatcher.py   # Routes instructions to output layer
│
├── 📁 frontend/                      ← Desktop overlay & guidance panel (JS/TS)
│   ├── overlay/                      # Always-on-top overlay UI
│   ├── panel/                        # Main guidance panel
│   └── components/                   # Reusable UI components
│
├── 📁 api/                           ← FastAPI REST & WebSocket layer
│   ├── main.py                       # FastAPI application entrypoint
│   ├── routes/                       # REST API route handlers
│   └── websockets/                   # Real-time WebSocket communication
│
├── 📁 models/                        ← AI model weights (not committed to git)
│   ├── yolo/                         # YOLOv8 object detection weights
│   └── custom/                       # Domain-specific classifiers
│
├── 📁 tests/                         ← Test suite (unit + integration + e2e)
├── 📁 docs/                          ← Project documentation
├── 📁 scripts/                       ← Utility scripts
│
├── main.py                           ← Application entrypoint
├── requirements.txt                  ← Python runtime dependencies
├── requirements-dev.txt              ← Dev/test dependencies
├── docker-compose.yml
└── .env.example                      ← Template for environment variables
```

### Key Modules for New Contributors

| Module | Good Starting Points |
|--------|---------------------|
| `core/intelligence/trust_scorer.py` | Well-isolated, great for adding tests |
| `core/perception/ocr_engine.py` | Language/OCR improvements welcome |
| `api/routes/` | Add new REST endpoints following existing patterns |
| `frontend/components/` | UI improvements and new components |
| `tests/` | Writing missing unit tests for any core module |
| `docs/` | Documentation, guides, API references |

---

## 🚫 What NOT to Do

```
╔══════════════════════════════════════════════════════════════╗
║                       AVOID THESE                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ❌  Submitting empty, trivial or AI-dump PRs for points     ║
║  ❌  Spamming issues asking to be assigned without reading   ║
║  ❌  Claiming issues and going silent for 7+ days            ║
║  ❌  Pushing directly to main (your PR will be rejected)     ║
║  ❌  Committing .env files, API keys or secrets              ║
║  ❌  Committing model weights (use scripts/download_*.py)    ║
║  ❌  Making changes outside the scope of the assigned issue  ║
║  ❌  Force-pushing to a branch with an open PR               ║
║  ❌  Copying code without proper attribution                 ║
║  ❌  Ignoring reviewer feedback without explanation          ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                       ALWAYS DO THIS                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ✅  Read the full issue before asking questions             ║
║  ✅  Test your changes locally before submitting a PR        ║
║  ✅  Write clear, meaningful commit messages                 ║
║  ✅  Add docstrings and type hints to all new functions      ║
║  ✅  Respond to review feedback within 3 days                ║
║  ✅  Be respectful, patient, and kind with maintainers       ║
║  ✅  Ask questions in Discussions — not in issue comments    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🔐 Security Vulnerabilities

> [!CAUTION]
> **Do NOT open a public GitHub Issue for security vulnerabilities.**

If you discover a security vulnerability in Execra, please report it **privately** and responsibly:

1. **Email**: youremail@example.com with subject `[SECURITY] Vulnerability Report`
2. **Include**: Description, steps to reproduce, potential impact, and suggested fix (if known)
3. **Response time**: We aim to acknowledge within 48 hours and patch within 7 days
4. **Credit**: Responsible reporters will be credited in the security advisory (unless anonymity is preferred)

---

## 📜 Code of Conduct

This project is governed by the [Contributor Covenant Code of Conduct v2.1](CODE_OF_CONDUCT.md).

**In summary, we expect all contributors to:**
- 🤝 Be welcoming, inclusive, and respectful
- 🗣️ Use constructive and professional language
- 🌱 Support and uplift beginners — everyone starts somewhere
- 🚫 Avoid harassment, discrimination, or exclusionary behavior
- 🔍 Focus on the issue, not the person

**Violations** may be reported confidentially to **youremail@example.com**.

Maintainers have the right to remove, edit, or reject any comment, commit, code, or other contribution that violates this Code of Conduct.

---

## 💬 Community & Support

| Channel | Purpose | Link |
|---------|---------|------|
| 💬 **GitHub Discussions** | General questions, ideas, showcasing work | [Open Discussions](https://github.com/yourusername/execra/discussions) |
| 🐛 **Issues** | Bug reports and feature requests | [Open an Issue](https://github.com/yourusername/execra/issues/new/choose) |
| 📧 **Email** | Private or sensitive matters | youremail@example.com |
| 🌸 **GSSoC Portal** | Program updates and leaderboard | [gssoc.girlscript.tech](https://gssoc.girlscript.tech/) |

> [!TIP]
> Before asking for help, search existing issues and discussions first — your question may already be answered!

---

## 🙏 Recognition

We deeply appreciate every contribution, no matter how small.

- All contributors will be listed in the project's [Contributors section](https://github.com/yourusername/execra/graphs/contributors)
- GSSoC participants earn points towards the official leaderboard for merged PRs
- Exceptional contributions may be highlighted in release notes and project announcements
- First-time contributors earn a special **"First PR" recognition** in the community

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer&text=Happy%20Contributing!&fontSize=36&fontColor=ffffff&animation=fadeIn" width="100%" alt="Footer"/>

<br/>

**Thank you for making Execra better. 🚀**

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
