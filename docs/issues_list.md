<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=160&section=header&text=Open%20Issues%20Board&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=40&desc=Pick%20an%20issue%20and%20start%20contributing%20to%20Execra%21&descAlignY=62&descAlign=50&descSize=16" width="100%" alt="Issues Board Banner"/>

[![GSSoC 2026](https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=for-the-badge&logo=girlscript&logoColor=white)](https://gssoc.girlscript.tech/)
&nbsp;
[![Issues](https://img.shields.io/github/issues/sahoo-tech/execra?style=for-the-badge&color=FF6B6B&labelColor=1a1a2e)](https://github.com/sahoo-tech/execra/issues)
&nbsp;
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](https://github.com/sahoo-tech/execra/pulls)

</div>

---

> 👋 **Welcome, contributor!** This is your starting point. Browse the issues below, pick one that matches your skill level, and follow the steps in [CONTRIBUTING.md](../CONTRIBUTING.md) to get started. Every issue here is officially open for the community to work on.

---

## 🗺️ How to Pick and Work on an Issue

```
 STEP 1          STEP 2           STEP 3           STEP 4          STEP 5
┌────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐    ┌─────────┐
│ Browse │────►│  Pick an │────►│  Go to   │────►│ Comment  │───►│  Fork,  │
│ this   │     │  issue   │     │  GitHub  │     │ "I'd like│    │  Branch │
│  list  │     │  below   │     │  Issues  │     │  to work │    │  & Code │
└────────┘     └──────────┘     └──────────┘     │  on this"│    └─────────┘
                                                  └──────────┘
```

> [!IMPORTANT]
> Always **comment on the GitHub Issue first** and wait to be assigned before you start coding. This prevents duplicate work.

---

## 🏷️ Points & Difficulty Guide

| Badge | Difficulty | Points | Best For |
|-------|-----------|--------|---------|
| ⭐ `good first issue` | Beginner | **10 pts** | First-time open source contributors |
| ⭐⭐ `easy` | Easy | **25 pts** | Some coding experience |
| ⭐⭐⭐ `medium` | Medium | **45 pts** | Intermediate developers |
| ⭐⭐⭐⭐ `hard` | Expert | **60 pts** | Advanced / experienced contributors |

---

## 📑 Jump to a Difficulty

- [⭐ Beginner Issues — 10 pts](#-beginner-issues--10-pts-each)
- [⭐⭐ Easy Issues — 25 pts](#-easy-issues--25-pts-each)
- [⭐⭐⭐ Medium Issues — 45 pts](#-medium-issues--45-pts-each)
- [⭐⭐⭐⭐ Hard / Expert Issues — 60 pts](#-hard--expert-issues--60-pts-each)

---

---

## ⭐ Beginner Issues — 10 pts each

> Perfect for **first-time contributors**. These are well-scoped, require no deep knowledge of the codebase, and are a great way to get familiar with the project.

---

### 🟢 #1 — Add Docstrings to `screen_capture.py`
**Labels:** `good first issue` `documentation` `gssoc-2026`

The `core/perception/screen_capture.py` module is missing docstrings. Your job is to add clear, Google-style docstrings to all public functions and the module itself.

**What you'll do:**
- Add a module-level docstring
- Add `Args`, `Returns`, and `Raises` to each public function
- Follow the Google Python style the project uses

**Skills needed:** Basic Python · Reading code

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #2 — Create a `.gitignore` for Python and Node.js
**Labels:** `good first issue` `chore` `gssoc-2026`

The repo has no `.gitignore`. This means files like `venv/`, `node_modules/`, `.env`, and `__pycache__/` might accidentally get committed.

**What you'll do:**
- Create `.gitignore` at the project root
- Cover Python, Node.js, OS files (`.DS_Store`, `Thumbs.db`), and IDE files
- Add project-specific ignores for model weight files and `.env`

**Skills needed:** Git basics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #3 — Create a Complete `.env.example` Template
**Labels:** `good first issue` `chore` `gssoc-2026`

New contributors need to know which API keys and settings to configure. A well-commented `.env.example` file makes setup fast and clear.

**What you'll do:**
- Create `.env.example` at the project root
- Add all required variables: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `LLM_BACKEND`, `API_PORT`, `SCREEN_CAPTURE_FPS`, `LOG_LEVEL`, `REDIS_URL`
- Write a clear comment above each variable explaining what it does

**Skills needed:** Reading code · Writing comments

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #4 — Add Type Hints to Utility Functions
**Labels:** `good first issue` `style` `gssoc-2026`

Several helper functions in `core/` are missing type hints. Adding them improves IDE support and catches bugs early.

**What you'll do:**
- Audit all functions in `core/` for missing type hints
- Add `param: type` and `-> return_type` to every function signature
- Use `Optional[T]` where parameters can be `None`
- Run `mypy` to verify

**Skills needed:** Intermediate Python · Type annotations

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #5 — Create a `CONTRIBUTORS.md` File
**Labels:** `good first issue` `documentation` `gssoc-2026`

Every great open-source project recognizes its contributors. Create a `CONTRIBUTORS.md` to celebrate everyone who helps build Execra.

**What you'll do:**
- Create `CONTRIBUTORS.md` at the root
- Add a table with `Name`, `GitHub`, `Contribution` columns
- Add the maintainer as the first entry
- Add a note that all merged PR contributors will be listed here

**Skills needed:** Markdown

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #6 — Fix Markdown Formatting in `docs/architecture.md`
**Labels:** `good first issue` `documentation` `gssoc-2026`

The architecture document has ASCII diagrams and tables that may not render perfectly on all Markdown viewers. Review and fix any issues.

**What you'll do:**
- Check every section of `docs/architecture.md` on GitHub's renderer
- Wrap ASCII diagrams in code blocks if missing
- Fix broken links, misaligned tables, and skipped heading levels

**Skills needed:** Markdown

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #7 — Create a `docs/FAQ.md` File
**Labels:** `good first issue` `documentation` `gssoc-2026`

New contributors frequently have the same questions. A well-written FAQ saves everyone time.

**What you'll do:**
- Create `docs/FAQ.md`
- Write at least 10 Q&A entries: setup problems, issue claiming, GSSoC points, running tests, API key setup
- Link to README/CONTRIBUTING where relevant
- Add a link to it in the README Table of Contents

**Skills needed:** Markdown · Understanding the project

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #8 — Add Python & Node Version Badges to README
**Labels:** `good first issue` `documentation` `gssoc-2026`

The README is missing version badges for core technologies. These badges help contributors check compatibility at a glance.

**What you'll do:**
- Add `Python 3.10+`, `Node.js 18+`, `FastAPI`, and `Docker` badges
- Match the existing `for-the-badge` style and `labelColor=1a1a2e`
- Place them in the existing badge row at the top of README

**Skills needed:** Markdown · Shields.io basics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #9 — Improve Windows Setup Instructions in README
**Labels:** `good first issue` `documentation` `gssoc-2026`

The Getting Started section lacks Windows-specific notes. Many contributors use Windows and get stuck on small differences like virtual environment activation.

**What you'll do:**
- Clarify `venv\Scripts\activate` is Windows-specific
- Add Windows notes for FFmpeg setup (via `winget` or Chocolatey)
- Add labeled code blocks for Windows vs Linux/macOS commands

**Skills needed:** Markdown · Windows development environment

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #10 — Make Code of Conduct Contact Visible in README
**Labels:** `good first issue` `documentation` `gssoc-2026`

The violation reporting email should be easy to find in the README, not only inside `CODE_OF_CONDUCT.md`.

**What you'll do:**
- Ensure the Code of Conduct section in README links correctly to `CODE_OF_CONDUCT.md`
- Add the maintainer email (`ss9830872697@gmail.com`) visibly in that section
- Add an encouraging sentence inviting people to report violations safely

**Skills needed:** Markdown

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐ Easy Issues — 25 pts each

> For contributors who are **comfortable with code but new to the project**. These involve writing real code — tests, small features, and configuration.

---

### 🔵 #11 — Write Unit Tests for `trust_scorer.py`
**Labels:** `easy` `test` `gssoc-2026`

The trust scoring module is critical and needs thorough unit tests. This is a great module to learn how Execra calculates confidence.

**What you'll do:**
- Create `tests/unit/test_trust_scorer.py`
- Test high, low, and boundary confidence values
- Test invalid inputs (`<0`, `>1`)
- Test all required keys in the return dict
- Achieve ≥80% code coverage

**Skills needed:** Python · pytest · Unit testing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #12 — Add Structured Logging to `screen_capture.py`
**Labels:** `easy` `enhancement` `gssoc-2026`

The screen capture module has no logging. Structured logging with Python's `logging` module makes debugging production issues much easier.

**What you'll do:**
- Add `logger = logging.getLogger(__name__)` to the module
- Log each captured frame at `DEBUG` level, dropped frames at `WARNING`, and errors at `ERROR`
- No `print()` statements — only the logger
- Write one unit test verifying the logger fires correctly on failure

**Skills needed:** Python · logging module

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #13 — Add CLI Argument Parser to `main.py`
**Labels:** `easy` `enhancement` `gssoc-2026`

Users should be able to configure Execra from the terminal without editing source code. Add a proper CLI using `argparse`.

**What you'll do:**
- Add `--mode` (passive/active/mixed), `--domain`, `--fps`, `--llm`, `--log-level` arguments
- Print a startup summary of all active settings
- Write tests for the argument parser

**Skills needed:** Python · argparse

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #14 — Build the Health Check Endpoint `GET /api/v1/status`
**Labels:** `easy` `enhancement` `gssoc-2026`

The status endpoint is documented in `docs/api_reference.md` and is critical for the frontend overlay and monitoring. Build it.

**What you'll do:**
- Create `api/routes/status.py`
- Return: `status`, `version`, `uptime_seconds`, `active_domain`, `active_mode`, `perception_fps`, `llm_backend`
- Register the router in `api/main.py`
- Write integration tests using FastAPI's `TestClient`

**Skills needed:** Python · FastAPI · REST APIs

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #15 — Create a `Makefile` with Dev Commands
**Labels:** `easy` `chore` `gssoc-2026`

Contributors should be able to run common tasks with short, memorable commands. A `Makefile` provides exactly that.

**What you'll do:**
- Add `make install`, `make run`, `make test`, `make lint`, `make format`, `make docker-up`, `make clean`
- Add a `help` target listing all commands with descriptions

**Skills needed:** Makefile basics · Shell commands

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #16 — Set Up Pre-commit Hooks
**Labels:** `easy` `chore` `gssoc-2026`

Pre-commit hooks automatically enforce code quality before every commit, ensuring no bad code ever reaches the repo.

**What you'll do:**
- Create `.pre-commit-config.yaml`
- Configure hooks: `black`, `isort`, `flake8`, `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`
- Add setup instructions to `CONTRIBUTING.md`
- Run `pre-commit run --all-files` and ensure it passes

**Skills needed:** Python tooling · YAML

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #17 — Write Unit Tests for `ocr_engine.py`
**Labels:** `easy` `test` `gssoc-2026`

The OCR engine needs unit tests that work without Tesseract actually being installed (using mocks), so the test suite runs on all CI environments.

**What you'll do:**
- Create `tests/unit/test_ocr_engine.py`
- Mock Tesseract calls with `unittest.mock`
- Test: valid image → string output; empty image → `""`; `None` input → `ValueError`; multi-language input handling
- Achieve ≥80% coverage

**Skills needed:** Python · pytest · unittest.mock

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #18 — Add Input Validation to `POST /api/v1/guidance/ask`
**Labels:** `easy` `enhancement` `gssoc-2026`

The guidance ask endpoint currently has no validation. Empty strings and excessively long questions should be rejected clearly.

**What you'll do:**
- Define a Pydantic model for the request body
- Reject empty `question` fields with `400 Bad Request`
- Reject questions over 500 characters with `400 Bad Request`
- Write integration tests for all failure cases
- Update `docs/api_reference.md` with validation rules

**Skills needed:** Python · FastAPI · Pydantic

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #19 — Add Docker Healthchecks to `docker-compose.yml`
**Labels:** `easy` `chore` `gssoc-2026`

Without healthchecks, Docker has no way to know if a service has started correctly. Add them so operators can see service health at a glance.

**What you'll do:**
- Add a healthcheck to `execra-api` (ping `GET /api/v1/status`)
- Add a healthcheck to the Redis service (`redis-cli ping`)
- Configure `interval`, `timeout`, `retries`, `start_period`
- Verify services show `(healthy)` in `docker-compose ps`

**Skills needed:** Docker · YAML

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #20 — Implement the Mode Switch Endpoints
**Labels:** `easy` `enhancement` `gssoc-2026`

`GET /api/v1/mode` and `PUT /api/v1/mode` are documented in `docs/api_reference.md`. Build them so the frontend can switch Execra's interaction mode.

**What you'll do:**
- Create `api/routes/mode.py`
- Implement `GET` → returns current mode + description
- Implement `PUT` → accepts `{"mode": "active"}`, validates, and switches
- Return `400` for invalid mode values
- Write integration tests for both endpoints

**Skills needed:** Python · FastAPI · REST APIs

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐⭐ Medium Issues — 45 pts each

> For **intermediate developers** who are comfortable owning a feature end-to-end. These involve designing and building entire modules.

---

### 🟠 #21 — Implement Screen Delta Detection Algorithm
**Labels:** `medium` `enhancement` `gssoc-2026`

Every frame is currently forwarded to the processing layer. A smart delta detection algorithm compares consecutive frames and only sends frames with real changes, dramatically reducing CPU load.

**What you'll do:**
- Compare frames using pixel-level difference with `numpy`
- Only forward frames where the changed pixel percentage exceeds `DELTA_THRESHOLD`
- Make the threshold configurable via `.env`
- Write unit tests with mock frames; document CPU benchmarks

**Skills needed:** Python · NumPy · Image processing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #22 — Build the Session Context Manager
**Labels:** `medium` `enhancement` `gssoc-2026`

The context engine tracks everything Execra needs to know about the user's current task — what step they're on, their error history, and their domain. It's the memory of Execra.

**What you'll do:**
- Implement the `SessionContext` class with all fields from `docs/api_reference.md`
- Implement `update_step()`, `log_error()`, `reset()` methods
- Persist to SQLite using `aiosqlite`
- Build `GET /api/v1/context` and `DELETE /api/v1/context` REST endpoints
- Write unit + integration tests

**Skills needed:** Python · SQLite · FastAPI · async

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #23 — Add Multi-Language OCR Support
**Labels:** `medium` `enhancement` `gssoc-2026`

Execra's OCR currently only reads English. Many users work in other languages. Add multi-language support using Tesseract's language packs and auto-detect the on-screen language.

**What you'll do:**
- Add a `language: str` parameter to OCR functions (default: `"eng"`)
- Implement auto-detection using `langdetect`
- Add graceful fallback to English if language pack missing
- Write unit tests for ≥3 languages and the fallback case

**Skills needed:** Python · Tesseract · NLP basics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #24 — Implement the Trust Score Formula
**Labels:** `medium` `enhancement` `gssoc-2026`

Implement the weighted trust score formula from `docs/architecture.md` that combines LLM confidence, rule validation, and execution trace matching into a single confidence score.

**What you'll do:**
- Implement the weighted formula (w1=0.5, w2=0.3, w3=0.2, configurable via `.env`)
- Return `score`, `level` (trusted/moderate/low/uncertain), and `reasoning`
- Raise `ValueError` for inputs outside `[0, 1]`
- Write tests for all four trust levels and edge cases

**Skills needed:** Python · Math · Unit testing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #25 — Build the Action Logger with SQLite
**Labels:** `medium` `enhancement` `gssoc-2026`

The action logger records every user action, powers the undo stack, and enables session replay. Build it with SQLite persistence.

**What you'll do:**
- Implement `log_action()`, `undo_last()`, `get_history(limit, offset)`
- Persist to SQLite; maintain an in-memory undo stack
- Build `GET /api/v1/actions` and `POST /api/v1/actions/undo` endpoints
- Write unit + integration tests

**Skills needed:** Python · SQLite · FastAPI

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #26 — Create the WebSocket Connection Handler
**Labels:** `medium` `enhancement` `gssoc-2026`

The WebSocket endpoint is the real-time channel between Execra's backend and the frontend overlay. It must handle both incoming user events and outgoing guidance broadcasts.

**What you'll do:**
- Implement `ws://localhost:8000/ws/guidance` using FastAPI WebSocket
- Handle client→server: `user_action`, `ask`, `mode_switch` events
- Handle server→client: `guidance`, `error_alert`, `step_complete` events
- Write integration tests using FastAPI's `WebSocketTestSession`

**Skills needed:** Python · FastAPI WebSocket · async

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #27 — Implement the Mode Manager Module
**Labels:** `medium` `enhancement` `gssoc-2026`

The mode manager controls which of Execra's three operating modes is active (Passive, Active, Mixed) and notifies all other modules when the mode changes.

**What you'll do:**
- Implement `ModeManager` class with mode state
- Implement `switch_mode()` with validation
- Implement an observer/event pattern to notify other modules
- Integrate with mode API endpoints
- Write unit tests for all transitions

**Skills needed:** Python · Design patterns (Observer)

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #28 — Build the Task Decomposer Module
**Labels:** `medium` `enhancement` `gssoc-2026`

The task decomposer uses the LLM to break a high-level user goal into an ordered, step-by-step action plan. It is the starting point of Execra's step-tracking system.

**What you'll do:**
- Implement `decompose_task(goal, context) -> list[str]` using the LLM client
- Design a consistent prompt template
- Store steps in `SessionContext`
- Handle LLM failures gracefully (1 retry then generic steps)
- Write unit tests mocking the LLM

**Skills needed:** Python · LLM prompting · async

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #29 — Integrate YOLOv8 Object Detector
**Labels:** `medium` `enhancement` `gssoc-2026`

YOLOv8 powers Execra's physical domain — detecting tools, objects, and hands in camera frames to guide real-world tasks.

**What you'll do:**
- Integrate Ultralytics YOLO library
- Implement `detect_objects(frame) -> list[Detection]` with `label`, `confidence`, `bounding_box`
- Only return detections above configurable `DETECTION_THRESHOLD` (default: 0.5)
- Write unit tests using mock model output (no real camera needed)
- Benchmark inference time per frame

**Skills needed:** Python · Computer vision · YOLOv8

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #30 — Build the Consequence Simulation Engine Stub
**Labels:** `medium` `enhancement` `gssoc-2026`

The consequence simulator predicts what will happen if the user takes their next action — before it happens. This issue builds the stub with 5 rule-based code consequence predictions.

**What you'll do:**
- Implement `simulate_consequences(current_state, next_action) -> list[Outcome]`
- Each `Outcome` has: `description`, `probability`, `severity`
- Implement ≥5 rules (missing null check, off-by-one, undefined variable, etc.)
- Sort outcomes by severity (critical first)
- Write unit tests for each rule

**Skills needed:** Python · Logic/rules design

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐⭐⭐ Hard / Expert Issues — 60 pts each

> For **advanced contributors** who want to tackle the core challenges of Execra. These require deep technical knowledge and end-to-end ownership of complex systems.

---

### 🔴 #31 — Implement Full Runtime Code Tracer with `sys.settrace`
**Labels:** `hard` `enhancement` `gssoc-2026`

This is the heart of Execra's digital domain. The code tracer hooks into Python's runtime to observe every function call, line execution, and exception as code runs live.

**What you'll do:**
- Implement `CodeTracer` using `sys.settrace`
- Track function calls, line-level execution, return values, exceptions
- Detect: infinite loops, unhandled exceptions, unexpected `None` returns, type mismatches
- Implement safe start/stop to avoid tracing Execra's own internals
- Benchmark: must add <5% CPU overhead

**Skills needed:** Advanced Python · Python internals · `sys.settrace`

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #32 — Build the LLM Abstraction Layer
**Labels:** `hard` `enhancement` `gssoc-2026`

Execra supports GPT-4o, Gemini 1.5 Pro, and Llama 3. One unified interface must make all three interchangeable — the rest of the codebase should never need to know which LLM is active.

**What you'll do:**
- Design abstract `BaseLLMClient` with `complete()` and `stream()` methods
- Implement `OpenAIClient`, `GeminiClient`, `LlamaClient` concrete classes
- Implement `LLMClientFactory` reading from `LLM_BACKEND` env var
- Add retry with exponential backoff (max 3) and configurable timeout (30s)
- Write unit tests mocking all three backends

**Skills needed:** Python · async · Design patterns · OpenAI/Gemini APIs

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #33 — Build the Always-on-Top Desktop Overlay UI
**Labels:** `hard` `enhancement` `gssoc-2026`

The frontend overlay is how users see Execra's guidance in real time — an always-on-top, semi-transparent panel rendered over their work. This is a high-impact, highly visible feature.

**What you'll do:**
- Build an Electron.js always-on-top, semi-transparent window in `frontend/overlay/`
- Connect to WebSocket (`ws://localhost:8000/ws/guidance`)
- Display: instruction, confidence bar, step progress, source tags, error alerts
- Add minimize/expand toggle and Active Mode text input
- Style with a dark glass-morphism design

**Skills needed:** JavaScript / TypeScript · Electron.js · WebSocket · UI/UX

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #34 — Wire the End-to-End Real-Time Guidance Streaming Pipeline
**Labels:** `hard` `enhancement` `gssoc-2026`

Connect every module together: Perception → Processing → Intelligence → Trust Scorer → WebSocket broadcast. This is the core runtime loop that makes Execra actually work.

**What you'll do:**
- Build an async pipeline using asyncio and bounded producer-consumer queues
- Connect all modules from frame capture to WebSocket broadcast
- Target latency: ≤500ms from screen change to delivered instruction
- Implement backpressure handling and guidance deduplication
- Write end-to-end integration tests and benchmark latency

**Skills needed:** Python · asyncio · Systems design · Performance engineering

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #35 — Build the Physical Domain CV Pipeline
**Labels:** `hard` `enhancement` `gssoc-2026`

Integrate YOLO, OCR, and spatial analysis into a unified computer vision pipeline that classifies physical tasks (cooking, repairs, form-filling) from camera frames and generates step guidance.

**What you'll do:**
- Build `PhysicalDomainPipeline` integrating `object_detector.py`, `ocr_engine.py`, `task_recognizer.py`
- Implement spatial analysis of detected object positions
- Support ≥3 task types: `cooking`, `hardware_repair`, `form_filling`
- Run at ≥5 FPS; write end-to-end tests with sample frames

**Skills needed:** Python · Computer vision · YOLOv8 · NumPy

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #36 — Implement the Hybrid Rule-Based + LLM Reasoning System
**Labels:** `hard` `enhancement` `gssoc-2026`

Execra's intelligence core isn't just an LLM — it combines LLM reasoning, a deterministic rule engine, and the consequence simulator. Build the orchestration layer that runs all three and merges their outputs.

**What you'll do:**
- Implement `IntelligenceCore` orchestrating all three sources with `asyncio.gather()`
- Build a rule engine with ≥10 deterministic validation rules
- Implement rule engine **veto** (rule engine can block any instruction regardless of LLM confidence)
- Pass merged output to `TrustScorer`
- Write unit tests for all 10 rules and the full orchestration flow

**Skills needed:** Python · async · Design patterns · Rules engines

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #37 — Build Redis Hot-Cache for the Context Engine
**Labels:** `hard` `enhancement` `gssoc-2026`

The guidance pipeline reads context data on every frame. To achieve <10ms context reads, implement a Redis hot-cache layer in front of SQLite using a dual-store read-through pattern.

**What you'll do:**
- Implement `ContextCache` writing to both Redis (hot) and SQLite (persistent)
- Read-through: Redis first, fall back to SQLite on cache miss
- Implement TTL: context expires from Redis after 30 min inactivity
- Implement `invalidate(session_id)` on session reset
- Benchmark: verify context reads complete in ≤10ms

**Skills needed:** Python · Redis · aioredis · Caching patterns

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #38 — Optimize Screen Capture for Low CPU Footprint
**Labels:** `hard` `performance` `gssoc-2026`

Screen capture runs 24/7 in the background. Users cannot tolerate it eating their CPU. Optimize the pipeline using multiprocessing, shared memory, and adaptive FPS.

**What you'll do:**
- Move screen capture to a separate `multiprocessing.Process` (bypasses GIL)
- Implement adaptive FPS (slow down on idle, speed up on activity)
- Use `multiprocessing.shared_memory` for zero-copy frame passing
- Add JPEG compression for frames in shared memory
- Target: ≤3% CPU on idle screen; ≤15% on active coding screen
- Document benchmarks in `docs/architecture.md`

**Skills needed:** Python · multiprocessing · Performance profiling · Systems programming

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #39 — Implement the Full Digital Domain Pipeline
**Labels:** `hard` `enhancement` `gssoc-2026`

Wire together every digital domain module into a single cohesive `DigitalDomainPipeline` — from screen capture, through code tracing and error detection, all the way to delivering step-by-step guidance.

**What you'll do:**
- Build `DigitalDomainPipeline` integrating all digital modules
- Implement domain auto-detection (detect when user is in an IDE/editor)
- Handle pipeline errors without crashing the main process
- Deliver guidance within 500ms of error detection
- Write an end-to-end test with a sample buggy Python script

**Skills needed:** Python · async · System integration · Software architecture

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #40 — Build the Full Undo and Replay System
**Labels:** `hard` `enhancement` `gssoc-2026`

Beyond just logging, Execra needs a full undo system where users can reverse guided actions, and a replay system to review their sessions. This is a complex, multi-component feature.

**What you'll do:**
- Extend `ActionRecord` with `is_undoable` and `undo_instruction` fields
- Implement `undo_last()` — executes the undo instruction, removes from stack
- Implement `replay_session(session_id)` — replays all actions in order
- Build `POST /api/v1/actions/undo` and `POST /api/v1/actions/replay` REST endpoints
- Implement `Ctrl+Z` keyboard shortcut hook in passive mode
- Ensure undo/replay are safe and idempotent

**Skills needed:** Python · FastAPI · Keyboard hooks · Complex state management

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

<div align="center">

## 📊 Quick Stats

| Level | Count | Points Each | Total Possible |
|-------|-------|------------|---------------|
| ⭐ Beginner | 10 issues | 10 pts | 100 pts |
| ⭐⭐ Easy | 10 issues | 25 pts | 250 pts |
| ⭐⭐⭐ Medium | 10 issues | 45 pts | 450 pts |
| ⭐⭐⭐⭐ Hard/Expert | 10 issues | 60 pts | 600 pts |
| **Total** | **40 issues** | | **1,400 pts** |

---

> 💡 **Tip:** Start with a beginner issue to learn the codebase, then graduate to harder ones as you grow more confident!

**[⭐ Star the repo](https://github.com/sahoo-tech/execra) · [📋 View Live Issues](https://github.com/sahoo-tech/execra/issues) · [📖 Read the Contribution Guide](../CONTRIBUTING.md)**

---

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer&text=Happy%20Contributing%21&fontSize=30&fontColor=ffffff&animation=fadeIn" width="100%" alt="Footer"/>

*Built with ❤️ for GirlScript Summer of Code 2026 · Execra — Execute without boundaries.*

</div>
