<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=160&section=header&text=Open%20Issues%20Board&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=40&desc=Pick%20an%20issue%20and%20start%20building%20Execra%20from%20scratch%21&descAlignY=62&descAlign=50&descSize=16" width="100%" alt="Issues Board Banner"/>

[![GSSoC 2026](https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=for-the-badge&logo=girlscript&logoColor=white)](https://gssoc.girlscript.tech/)
&nbsp;
[![Issues](https://img.shields.io/github/issues/sahoo-tech/execra?style=for-the-badge&color=FF6B6B&labelColor=1a1a2e)](https://github.com/sahoo-tech/execra/issues)
&nbsp;
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](https://github.com/sahoo-tech/execra/pulls)

</div>

---

> 👋 **Welcome, contributor!**
> Execra is being built **from scratch** — there is no existing code. Every single issue here is about **writing real code** for the first time. Pick an issue that matches your skill level, get assigned, and build something that becomes a permanent part of Execra.

---

## 🗺️ How to Get Started

```
 STEP 1            STEP 2           STEP 3          STEP 4          STEP 5
┌──────────┐     ┌──────────┐     ┌──────────┐    ┌──────────┐    ┌─────────┐
│  Browse  │────►│  Pick an │────►│ Go to    │───►│ Comment  │───►│  Fork,  │
│ this list│     │  issue   │     │  GitHub  │    │ to claim │    │  Code & │
│  below   │     │  below   │     │  Issues  │    │  it first│    │   PR    │
└──────────┘     └──────────┘     └──────────┘    └──────────┘    └─────────┘
```

> [!IMPORTANT]
> **Comment on the GitHub Issue first** and wait to be assigned before writing any code. Do NOT open a PR for an unassigned issue.

> [!NOTE]
> Since nothing is coded yet, **read `docs/architecture.md`** and **`docs/api_reference.md`** before picking any issue. They describe exactly what each module must do and how data flows through the system.

---

## 🏷️ Points & Difficulty Guide

| Badge | Difficulty | Points | Best For |
|-------|-----------|--------|---------|
| ⭐ `good first issue` | Beginner | **10 pts** | Comfortable with Python basics, setting up boilerplate and config |
| ⭐⭐ `easy` | Easy | **25 pts** | Can write a module/file independently with some guidance |
| ⭐⭐⭐ `medium` | Medium | **45 pts** | Comfortable designing and building a full feature |
| ⭐⭐⭐⭐ `hard` | Expert | **60 pts** | Can architect complex systems, integrate multiple components |

---

## 📑 Jump to a Section

- [⭐ Beginner — Project Setup & Boilerplate](#-beginner-issues--10-pts-each)
- [⭐⭐ Easy — Core Modules (First Implementation)](#-easy-issues--25-pts-each)
- [⭐⭐⭐ Medium — Feature Modules (Complex Implementation)](#-medium-issues--45-pts-each)
- [⭐⭐⭐⭐ Hard — System Integration & Advanced Engines](#-hard--expert-issues--60-pts-each)

---

---

## ⭐ Beginner Issues — 10 pts each

> These are **foundational coding tasks** — scaffolding, configuration, and boilerplate that every other module depends on. Even as a beginner, your work here directly unblocks all other contributors.

---

### 🟢 #1 — Set Up the Python Project Structure & `requirements.txt`

**Labels:** `good first issue` `setup` `gssoc-2026`

The project has no Python dependencies file yet. Create the base project layout and the initial `requirements.txt` so other contributors can install dependencies and start working.

**What you'll code:**
- Create all empty `__init__.py` files to make every `core/` subdirectory a proper Python package: `core/`, `core/perception/`, `core/intelligence/`, `core/digital/`, `core/physical/`, `core/hybrid/`, `api/`, `api/routes/`, `api/websockets/`, `tests/unit/`, `tests/integration/`, `tests/e2e/`
- Create `requirements.txt` with all production dependencies:
  ```
  fastapi, uvicorn, pyautogui, mss, pillow, opencv-python,
  pytesseract, ultralytics, openai, google-generativeai,
  langchain, aiosqlite, redis, plyer, python-dotenv, numpy, pydantic
  ```
- Create `requirements-dev.txt` with dev dependencies:
  ```
  pytest, pytest-asyncio, pytest-cov, black, isort, flake8, mypy, pre-commit, httpx
  ```

**Skills needed:** Python packaging basics · pip · project structure

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #2 — Create the Config Loader Module

**Labels:** `good first issue` `setup` `gssoc-2026`

All Execra modules need to read configuration from `.env`. Build a central config module so every other module imports settings from one place — no scattered `os.getenv()` calls.

**What you'll code:**
- Create `core/config.py`
- Use `python-dotenv` to load `.env`
- Define a `Settings` dataclass/class with typed fields for:
  - `LLM_BACKEND: str` (default: `"gpt-4o"`)
  - `OPENAI_API_KEY: str`
  - `GEMINI_API_KEY: str`
  - `SCREEN_CAPTURE_FPS: int` (default: `2`)
  - `DETECTION_THRESHOLD: float` (default: `0.5`)
  - `DELTA_THRESHOLD: float` (default: `0.05`)
  - `API_HOST: str` (default: `"0.0.0.0"`)
  - `API_PORT: int` (default: `8000`)
  - `LOG_LEVEL: str` (default: `"INFO"`)
  - `REDIS_URL: str` (default: `"redis://localhost:6379"`)
  - `TRUST_SCORE_W1: float` (default: `0.5`)
  - `TRUST_SCORE_W2: float` (default: `0.3`)
  - `TRUST_SCORE_W3: float` (default: `0.2`)
- Expose a single `settings = Settings()` instance to be imported everywhere
- Write 3 unit tests: correct defaults, overriding via env vars, missing required key raises error

**Skills needed:** Python · `python-dotenv` · dataclasses

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #3 — Create the Logging Setup Module

**Labels:** `good first issue` `setup` `gssoc-2026`

Every module in Execra needs consistent, structured logging. Build a central logging configurator so all modules get properly formatted log output with the correct level.

**What you'll code:**
- Create `core/logger.py`
- Configure Python's `logging` module with:
  - Format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
  - Log level read from `settings.LOG_LEVEL`
  - A `StreamHandler` for console output
  - A rotating `FileHandler` writing to `logs/execra.log` (create `logs/` dir if missing)
- Expose `get_logger(name: str) -> logging.Logger` — every module calls this instead of `logging.getLogger()` directly
- Write 2 unit tests: logger returns correct name, log level matches config

**Skills needed:** Python · `logging` module

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #4 — Create the FastAPI Application Skeleton

**Labels:** `good first issue` `setup` `gssoc-2026`

The API layer needs a base FastAPI app with the correct structure, middleware, and startup/shutdown hooks — before any routes are added.

**What you'll code:**
- Create `api/main.py` with:
  - A `FastAPI` app instance with metadata: `title="Execra API"`, `version="0.1.0"`, `description`
  - CORS middleware allowing all origins (development config)
  - A `startup` event handler that logs "Execra API starting..."
  - A `shutdown` event handler that logs "Execra API shutting down..."
  - A root `GET /` endpoint returning `{"message": "Execra is running", "version": "0.1.0"}`
  - Placeholder router imports (commented out, to be uncommented as routes are built)
- Verify the app starts: `uvicorn api.main:app --reload` should show the Swagger UI at `http://localhost:8000/docs`

**Skills needed:** Python · FastAPI basics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #5 — Create `main.py` — The Application Entry Point

**Labels:** `good first issue` `setup` `gssoc-2026`

`main.py` is what users run to start Execra. It needs to parse CLI arguments, load config, set up logging, and launch the API server.

**What you'll code:**
- Create `main.py` at the project root
- Use `argparse` to accept:
  - `--mode`: `passive` / `active` / `mixed` (default: `passive`)
  - `--domain`: `digital` / `physical` / `hybrid` (default: `digital`)
  - `--fps`: integer (default: `2`)
  - `--llm`: `gpt-4o` / `gemini` / `llama` (default: `gpt-4o`)
  - `--log-level`: `DEBUG` / `INFO` / `WARNING` / `ERROR` (default: `INFO`)
- Import and call `core/logger.py` setup
- Print a styled startup banner to the console listing all active settings
- Start the FastAPI server with `uvicorn` programmatically

**Skills needed:** Python · argparse · subprocess/uvicorn

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #6 — Set Up `pytest` Configuration

**Labels:** `good first issue` `setup` `gssoc-2026`

All tests in Execra use `pytest`. Set up the test configuration so that `python -m pytest` works correctly from the project root with proper settings for async tests and coverage.

**What you'll code:**
- Create `pytest.ini` (or `pyproject.toml` `[tool.pytest.ini_options]`) with:
  - `testpaths = ["tests"]`
  - `asyncio_mode = "auto"` (for async tests)
  - `python_files = "test_*.py"`
  - `python_functions = "test_*"`
- Create `conftest.py` in the `tests/` root with:
  - A `@pytest.fixture` named `sample_frame` — returns a small dummy `numpy` array representing a blank screen frame
  - A `@pytest.fixture` named `mock_settings` — returns a `Settings` object with test values
- Create one placeholder test `tests/unit/test_placeholder.py` that asserts `True` to verify the setup runs
- Run `python -m pytest tests/ -v` and confirm it passes

**Skills needed:** Python · pytest · fixtures

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #7 — Create the `docker-compose.yml` for Local Development

**Labels:** `good first issue` `setup` `gssoc-2026`

Contributors need to be able to spin up all Execra services with one command. Build the Docker Compose file that defines all services.

**What you'll code:**
- Create `docker-compose.yml` with these services:
  - `execra-api`: build from `Dockerfile`, port `8000:8000`, depends on `execra-db`, mounts `.env`
  - `execra-db`: uses `redis:7-alpine` image, port `6379:6379`
  - `execra-frontend`: build from `frontend/Dockerfile` (placeholder), port `3000:3000`
- Add `healthcheck` for `execra-api` (ping `GET /`) and `execra-db` (`redis-cli ping`)
- Create a minimal `Dockerfile` for the Python API:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["python", "main.py"]
  ```
- Verify `docker-compose config` validates without errors

**Skills needed:** Docker · Docker Compose · YAML

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #8 — Build the `scripts/download_models.py` Script

**Labels:** `good first issue` `setup` `gssoc-2026`

The physical domain needs YOLOv8 model weights. Contributors should be able to download them with one command without hunting for download links.

**What you'll code:**
- Create `scripts/download_models.py`
- Use the `ultralytics` library to download `yolov8n.pt` (nano model — smallest/fastest)
- Save it to `models/yolo/yolov8n.pt`, creating the `models/yolo/` directory if needed
- Print progress: "Downloading YOLOv8 nano model..." and "✅ Model saved to models/yolo/yolov8n.pt"
- Add a `--model` argument to choose between `yolov8n`, `yolov8s`, `yolov8m` (default: `yolov8n`)
- Handle the case where the model already exists: print "Model already exists, skipping download." and exit cleanly
- Verify: `python scripts/download_models.py` downloads the file successfully

**Skills needed:** Python · argparse · Ultralytics API

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #9 — Create the Base Data Models

**Labels:** `good first issue` `setup` `gssoc-2026`

All the shared Pydantic data models used across the API, WebSocket, and core modules need to be defined in one place before other code can use them.

**What you'll code:**
- Create `core/models.py` with these Pydantic models (refer to `docs/api_reference.md` for all fields):
  - `Detection` — YOLO detection result: `label: str`, `confidence: float`, `bounding_box: list[int]`
  - `ErrorRecord` — logged error: `step: int`, `error: str`, `resolved: bool`
  - `ActionRecord` — logged action: `id`, `timestamp`, `type`, `description`, `domain`, `was_guided`, `guidance_confidence`
  - `Outcome` — consequence simulation result: `description`, `probability`, `severity` (Literal: "info"/"warning"/"critical")
  - `GuidanceInstruction` — full guidance output: `instruction`, `confidence`, `source`, `reasoning`, `mode`, `step`, `total_steps`, `generated_at`
  - `SessionContext` — current session state: all fields from `docs/api_reference.md`
- Write unit tests verifying: each model instantiates correctly, required fields raise `ValidationError` when missing, field types are enforced

**Skills needed:** Python · Pydantic v2

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟢 #10 — Create the SQLite Database Initializer

**Labels:** `good first issue` `setup` `gssoc-2026`

Two modules (context engine and action logger) write to SQLite. Create the database initialization script that sets up both tables when Execra first runs.

**What you'll code:**
- Create `core/database.py`
- Use `aiosqlite` for async SQLite access
- Define and run `CREATE TABLE IF NOT EXISTS` for:
  - `session_context` table: `session_id`, `task_type`, `current_step`, `total_steps`, `step_description`, `domain`, `started_at`
  - `error_history` table: `id`, `session_id`, `step`, `error`, `resolved`, `logged_at`
  - `action_log` table: `id`, `session_id`, `timestamp`, `type`, `description`, `domain`, `was_guided`, `guidance_confidence`
- Expose `async def init_db()` — called once at startup from `api/main.py`
- Expose `async def get_db_connection()` — async context manager returning an `aiosqlite` connection
- Write unit tests using an in-memory SQLite DB (`:memory:`) to verify tables are created correctly

**Skills needed:** Python · SQLite · `aiosqlite` · async/await

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐ Easy Issues — 25 pts each

> These are **first implementations of real modules**. Each one produces a working, tested Python file that other contributors can immediately build on top of.

---

### 🔵 #11 — Implement `screen_capture.py` — Screen Frame Capture Engine

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that continuously captures the user's screen as a stream of frames. This is the primary input source for the digital domain.

**What you'll code:**
- Create `core/perception/screen_capture.py`
- Implement `ScreenCapture` class:
  - `__init__(fps: int)` — configures capture rate
  - `capture_frame() -> np.ndarray` — captures one screenshot using `mss`, returns as NumPy array (RGB)
  - `start_capture_loop(queue: asyncio.Queue)` — continuously captures frames at the configured FPS and puts them in the queue, runs in a separate thread
  - `stop()` — cleanly stops the capture loop
- Add structured logging at `DEBUG` (each frame) and `ERROR` (capture failure)
- Write unit tests mocking `mss.mss()` to avoid needing a real screen

**Skills needed:** Python · `mss` · NumPy · threading

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #12 — Implement `ocr_engine.py` — Text Extraction from Frames

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that extracts text from screen or camera frames using Tesseract OCR. This powers text recognition in both the digital and physical domains.

**What you'll code:**
- Create `core/perception/ocr_engine.py`
- Implement `OCREngine` class:
  - `__init__(language: str = "eng")` — configures Tesseract language
  - `extract_text(frame: np.ndarray) -> str` — converts frame to PIL Image, runs `pytesseract.image_to_string()`, returns cleaned text
  - `extract_text_with_boxes(frame: np.ndarray) -> list[dict]` — returns word-level bounding boxes using `pytesseract.image_to_data()`
- Raise `ValueError` if `frame` is `None`
- Return `""` for blank/empty frames gracefully (no exception)
- Write unit tests **mocking Tesseract** so tests pass without it installed

**Skills needed:** Python · `pytesseract` · PIL · NumPy

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #13 — Implement `camera_feed.py` — Live Camera Input Handler

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that captures frames from the user's webcam for the physical domain. It should work the same way as `screen_capture.py` — producing frames into a queue.

**What you'll code:**
- Create `core/perception/camera_feed.py`
- Implement `CameraFeed` class:
  - `__init__(camera_index: int = 0, fps: int = 5)` — connects to the webcam
  - `read_frame() -> np.ndarray | None` — reads one frame from the camera, returns `None` if camera unavailable
  - `start_feed_loop(queue: asyncio.Queue)` — continuously reads frames at the configured FPS and puts them in the queue, runs in a separate thread
  - `stop()` — cleanly releases the camera and stops the loop
- Handle camera not found gracefully: log a warning and keep retrying every 5 seconds
- Write unit tests mocking `cv2.VideoCapture` so tests pass without a camera

**Skills needed:** Python · OpenCV (`cv2`) · threading

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #14 — Implement `trust_scorer.py` — Confidence Score Calculator

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that calculates a trust score for every instruction Execra delivers. This is one of the most important quality-control mechanisms in the system.

**What you'll code:**
- Create `core/intelligence/trust_scorer.py`
- Implement `calculate_trust_score(llm_confidence: float, rule_validation: bool, execution_trace_match: float) -> dict`
- Use the weighted formula from `docs/architecture.md`:
  `score = (w1 * llm_confidence + w2 * (1.0 if rule_validation else 0.0) + w3 * execution_trace_match) / (w1 + w2 + w3)`
- Read weights from `settings` (w1=0.5, w2=0.3, w3=0.2)
- Return: `{"score": float, "level": str, "reasoning": str}`
- Level thresholds: `trusted` ≥0.85, `moderate` 0.65–0.84, `low` 0.50–0.64, `uncertain` <0.50
- Raise `ValueError` for inputs outside `[0, 1]`
- Write unit tests covering all four levels, all boundary values, and invalid inputs

**Skills needed:** Python · arithmetic · Pydantic · unit testing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #15 — Implement `mode_manager.py` — Interaction Mode Controller

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that controls which mode Execra is operating in — Passive (auto-observe), Active (user Q&A), or Mixed (both). It must notify other modules when the mode changes.

**What you'll code:**
- Create `core/hybrid/mode_manager.py`
- Implement `ModeManager` class:
  - `current_mode: str` — starts as `"passive"`
  - `switch_mode(mode: str)` — validates mode is one of `["passive", "active", "mixed"]`, raises `ValueError` otherwise, then triggers callbacks
  - `get_current_mode() -> dict` — returns `{"mode": str, "description": str}`
  - `on_mode_change(callback: Callable)` — registers a callback function to be called on every mode change (Observer pattern)
  - `_notify_observers()` — calls all registered callbacks with the new mode
- Write unit tests for all valid mode switches, invalid mode input, and callback registration/firing

**Skills needed:** Python · Observer pattern · callbacks

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #16 — Implement `GET /api/v1/status` and `GET /api/v1/mode` Endpoints

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the two read-only REST endpoints that the frontend overlay will poll to display system status and current mode.

**What you'll code:**
- Create `api/routes/status.py`:
  - `GET /api/v1/status` — returns `{"status": "running", "version": "0.1.0", "uptime_seconds": int, "active_domain": str, "active_mode": str, "perception_fps": int, "llm_backend": str}`
  - Track `start_time` using `time.time()` at startup to compute uptime
- Create `api/routes/mode.py`:
  - `GET /api/v1/mode` — returns current mode from `ModeManager`
  - `PUT /api/v1/mode` — accepts `{"mode": "active"}`, validates, calls `ModeManager.switch_mode()`, returns updated mode
  - Returns `400` for invalid mode values
- Register both routers in `api/main.py` under `prefix="/api/v1"`
- Write integration tests using FastAPI's `TestClient`

**Skills needed:** Python · FastAPI · REST API design

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #17 — Implement `action_logger.py` — Action Recording & Undo Stack

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module that records every user action to SQLite and maintains an in-memory undo stack. This powers session history and the undo feature.

**What you'll code:**
- Create `core/hybrid/action_logger.py`
- Implement `ActionLogger` class:
  - `log_action(action: ActionRecord) -> None` — saves to SQLite `action_log` table AND an in-memory `deque` (max size: 50)
  - `undo_last() -> ActionRecord | None` — pops last action from the stack, returns it (caller handles the actual undo)
  - `get_history(limit: int = 20, offset: int = 0) -> list[ActionRecord]` — async query from SQLite with pagination
  - `clear_session(session_id: str) -> None` — deletes all actions for the session from SQLite and clears the in-memory stack
- Write unit tests mocking SQLite operations

**Skills needed:** Python · SQLite · `aiosqlite` · `collections.deque`

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #18 — Implement `GET /api/v1/actions` and `POST /api/v1/actions/undo` Endpoints

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the REST endpoints for the action log so the frontend can display session history and trigger undos.

**What you'll code:**
- Create `api/routes/actions.py`:
  - `GET /api/v1/actions` — accepts `?limit=20&offset=0` query params, returns `{"total": int, "actions": list[ActionRecord]}`
  - `POST /api/v1/actions/undo` — calls `ActionLogger.undo_last()`, returns the undone action, or `409 Conflict` if nothing to undo
- Add `POST /api/v1/context` and `DELETE /api/v1/context` endpoints in `api/routes/context.py`:
  - `GET /api/v1/context` — returns the current `SessionContext` from SQLite
  - `DELETE /api/v1/context` — calls `ActionLogger.clear_session()`, resets context, returns `{"message": "Session context cleared."}`
- Register all routers in `api/main.py`
- Write integration tests for all endpoints including the `409` case

**Skills needed:** Python · FastAPI · REST API design · async

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #19 — Implement `guidance_dispatcher.py` — Instruction Delivery Module

**Labels:** `easy` `enhancement` `gssoc-2026`

Build the module responsible for formatting and dispatching `GuidanceInstruction` objects to whatever output channel is active (WebSocket, OS notification, or console in development mode).

**What you'll code:**
- Create `core/hybrid/guidance_dispatcher.py`
- Implement `GuidanceDispatcher` class:
  - `dispatch(instruction: GuidanceInstruction) -> None` — routes the instruction to all registered output channels
  - `register_channel(channel: Callable[[GuidanceInstruction], None]) -> None` — registers an output channel (e.g., WebSocket broadcaster, OS notifier)
  - `dispatch_error_alert(message: str, severity: str, confidence: float) -> None` — convenience method to format and dispatch an error alert
- Use `plyer.notification` to send OS-level desktop notifications as one channel
- Log all dispatched instructions at `INFO` level
- Write unit tests verifying callbacks are called with correct data

**Skills needed:** Python · `plyer` · callbacks · Observer pattern

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔵 #20 — Write Unit Tests for All Beginner-Tier Modules

**Labels:** `easy` `test` `gssoc-2026`

Now that the beginner issues (#1–#10) are complete, their unit tests need to be written to ensure correctness before medium-level modules are built on top of them.

**What you'll code:**
- `tests/unit/test_config.py` — test correct defaults, env var overrides, validation
- `tests/unit/test_logger.py` — test logger name, level, output format
- `tests/unit/test_database.py` — test table creation using in-memory SQLite
- `tests/unit/test_models.py` — test all Pydantic models: correct instantiation, required field validation, type enforcement
- Each test file must have ≥5 meaningful test functions
- Run `python -m pytest tests/unit/ --cov=core --cov-report=term-missing` and achieve ≥80% coverage across all tested modules

**Skills needed:** Python · pytest · unittest.mock · Pydantic

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐⭐ Medium Issues — 45 pts each

> These require **designing and building a complete feature** — including the core logic, integration with other modules, and tests. Read `docs/architecture.md` carefully before picking one.

---

### 🟠 #21 — Implement Screen Delta Detection in `screen_capture.py`

**Labels:** `medium` `enhancement` `gssoc-2026`

Without delta detection, the system processes every captured frame even if nothing changed on screen. Add intelligent delta detection so only frames with meaningful changes are forwarded.

**What you'll code:**
- Extend `ScreenCapture` in `core/perception/screen_capture.py`
- Add `DeltaDetector` helper class:
  - `__init__(threshold: float)` — configurable change threshold (from `settings.DELTA_THRESHOLD`)
  - `has_changed(prev_frame: np.ndarray, curr_frame: np.ndarray) -> bool` — computes pixel-level difference using `numpy`, returns `True` if changed pixels exceed threshold percentage
  - `get_change_percentage(prev_frame, curr_frame) -> float` — returns exact % of changed pixels
- Integrate into `start_capture_loop()`: only enqueue frames where `has_changed()` returns `True`
- Add frame metrics: `frames_captured`, `frames_forwarded`, `frames_dropped` — accessible via a `get_stats() -> dict` method
- Write unit tests with synthetic frame pairs (blank frames, partially changed frames, fully changed frames)
- Benchmark: measure and log CPU usage difference with and without delta detection

**Skills needed:** Python · NumPy · image processing · performance benchmarking

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #22 — Build the Full Session Context Engine

**Labels:** `medium` `enhancement` `gssoc-2026`

The context engine is Execra's memory — it tracks what task the user is doing, which step they're on, and their error history. Build it fully with SQLite persistence.

**What you'll code:**
- Create `core/intelligence/context_engine.py`
- Implement `ContextEngine` class:
  - `create_session(domain: str) -> SessionContext` — generates UUID session ID, saves to SQLite, returns context
  - `update_step(session_id: str, step: int, description: str) -> None` — updates current step in DB
  - `log_error(session_id: str, error: ErrorRecord) -> None` — appends to `error_history` table
  - `get_context(session_id: str) -> SessionContext | None` — reads full context from SQLite
  - `reset_session(session_id: str) -> None` — deletes from DB, resets all state
  - `detect_task_type(screen_text: str, detected_objects: list[str]) -> str` — heuristic function that guesses task type from OCR text keywords (e.g., "def ", "import" → `"code_debugging"`)
- Write unit tests using in-memory SQLite; write integration tests for the REST endpoints

**Skills needed:** Python · SQLite · aiosqlite · async · heuristics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #23 — Build the LLM Client for GPT-4o

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the first concrete LLM client — for OpenAI GPT-4o. This is step one of the larger LLM abstraction issue (#32). The module must be clean and well-abstracted so Gemini and Llama clients can be added later.

**What you'll code:**
- Create `core/intelligence/llm_client.py`
- Define abstract base class `BaseLLMClient` (using `abc.ABC`):
  - `async def complete(self, prompt: str) -> str` — abstract
  - `async def stream(self, prompt: str) -> AsyncIterator[str]` — abstract
  - `def extract_confidence(self, response) -> float` — abstract, returns 0.5 if unavailable
- Implement `OpenAIClient(BaseLLMClient)`:
  - Uses `openai.AsyncOpenAI` client
  - Reads `OPENAI_API_KEY` from settings
  - Implements `complete()` and `stream()` using `gpt-4o` model
  - Adds retry with exponential backoff (max 3 retries) on `RateLimitError` or `APIError`
  - Adds 30s timeout on all requests
- Write unit tests **mocking** the OpenAI client — do NOT make real API calls in tests

**Skills needed:** Python · OpenAI SDK · async · abstract classes · mocking

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #24 — Build the Real-Time WebSocket Endpoint

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the WebSocket endpoint that is the real-time communication channel between the Execra backend and the frontend overlay. Refer to `docs/api_reference.md` for all event schemas.

**What you'll code:**
- Create `api/websockets/guidance.py`
- Implement `ConnectionManager` class:
  - `connect(websocket)` — accepts and registers WebSocket connection
  - `disconnect(websocket)` — removes from active connections
  - `broadcast(message: dict)` — sends JSON message to all connected clients
  - `send_personal(message: dict, websocket)` — sends to one specific client
- Implement the WebSocket route `ws://localhost:8000/ws/guidance`:
  - On connect: send a `{"event": "connected", "payload": {"status": "ok"}}` message
  - Listen for client messages: handle `user_action`, `ask`, `mode_switch` event types
  - For `mode_switch`: call `ModeManager.switch_mode()` and broadcast the change
  - On disconnect: clean up connection from manager
- Register the WebSocket route in `api/main.py`
- Write integration tests using FastAPI's `WebSocketTestSession`

**Skills needed:** Python · FastAPI WebSocket · async · JSON messaging

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #25 — Implement `object_detector.py` — YOLOv8 Object Detection

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the object detection module used by the physical domain to identify tools, objects, and context from camera frames.

**What you'll code:**
- Create `core/physical/object_detector.py`
- Implement `ObjectDetector` class:
  - `__init__(model_path: str, threshold: float)` — loads YOLOv8 model from `models/yolo/`
  - `detect(frame: np.ndarray) -> list[Detection]` — runs YOLO inference, filters by `threshold`, returns `Detection` objects
  - `draw_boxes(frame: np.ndarray, detections: list[Detection]) -> np.ndarray` — draws bounding boxes on the frame (for debug/visualization)
- Only return detections above `settings.DETECTION_THRESHOLD`
- Handle missing model file: raise `FileNotFoundError` with helpful message pointing to `scripts/download_models.py`
- Write unit tests **mocking** the YOLO model inference — no real model required for tests
- Benchmark: log inference time per frame at `DEBUG` level

**Skills needed:** Python · YOLOv8 (Ultralytics) · NumPy · OpenCV

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #26 — Implement `consequence_sim.py` — Outcome Prediction Engine

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the consequence simulation engine that predicts what will happen if the user takes their next action — before they commit to it.

**What you'll code:**
- Create `core/intelligence/consequence_sim.py`
- Implement `ConsequenceSimulator` class:
  - `simulate(current_state: dict, next_action: str) -> list[Outcome]` — returns a list of predicted outcomes sorted by severity (critical first)
- Implement at least **8 built-in rule-based patterns** (refer to `core/models.py` for `Outcome`):
  1. Missing null check before attribute access → critical
  2. Off-by-one error in loop bounds (`range(len(x))` with `x[i+1]`) → warning
  3. Undefined variable usage → critical
  4. Infinite loop (while True without break) → critical
  5. Mutable default argument (`def f(x=[])`) → warning
  6. Division without zero check → warning
  7. File open without context manager → info
  8. Comparing to None with `==` instead of `is` → info
- Write unit tests for every rule with a code snippet that triggers it

**Skills needed:** Python · rule-based logic · string pattern matching / AST basics

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #27 — Build the `task_decomposer.py` Module

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the module that takes a high-level user goal and breaks it into a concrete list of ordered steps using the LLM. This is what populates the step-tracker in `SessionContext`.

**What you'll code:**
- Create `core/digital/task_decomposer.py`
- Implement `TaskDecomposer` class:
  - `__init__(llm_client: BaseLLMClient)` — receives the LLM client via dependency injection
  - `async def decompose(goal: str, context: SessionContext) -> list[str]` — builds a prompt, calls the LLM, parses the numbered list response into a Python list
  - Prompt must include: goal, current domain, any known error context
  - Handle LLM failure: on exception, retry once; if still fails, return a generic 5-step fallback list
  - `async def suggest_next_step(context: SessionContext) -> str` — asks LLM what the next step should be given current progress
- Write unit tests **mocking** the LLM client to return controlled responses

**Skills needed:** Python · LLM prompting · async · response parsing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #28 — Implement `task_recognizer.py` — Physical Task Classifier

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the module that looks at detected objects and OCR text from camera frames and determines what real-world task the user is performing.

**What you'll code:**
- Create `core/physical/task_recognizer.py`
- Implement `TaskRecognizer` class:
  - `recognize(detected_objects: list[Detection], ocr_text: str) -> str` — returns a task type string
  - Implement keyword/object-based rules for at least 4 task types:
    - `"cooking"` — if objects include: `knife`, `bowl`, `stove`, `pot`, `pan`
    - `"hardware_repair"` — if objects include: `screwdriver`, `wrench`, `circuit_board`, `wire`
    - `"form_filling"` — if OCR text contains: `Name:`, `Date:`, `Signature`, `___`
    - `"document_reading"` — if OCR text exceeds 100 words and no tools detected
    - `"unknown"` — fallback when nothing matches
  - `get_step_guidance(task_type: str) -> list[str]` — returns a hardcoded step list for each known task type (no LLM needed here)
- Write unit tests for each task type with mock detections and OCR text

**Skills needed:** Python · rule-based classification · string processing

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #29 — Implement `error_detector.py` — Runtime Error Identification

**Labels:** `medium` `enhancement` `gssoc-2026`

Build the error detection module that takes runtime trace data from `code_tracer.py` and identifies logical errors, unexpected `None` returns, and type mismatches.

**What you'll code:**
- Create `core/digital/error_detector.py`
- Implement `ErrorDetector` class:
  - `analyze_trace(trace_events: list[dict]) -> list[dict]` — scans the trace for error patterns and returns a list of flagged errors, each with `type`, `description`, `line`, `severity`
  - Detect: unhandled exceptions (any event with `event_type == "exception"`), functions returning `None` unexpectedly (based on type hints if available), excessive recursion depth (>500 calls), loop iteration counts exceeding a configurable threshold (potential infinite loop)
  - `detect_from_exception(exc: Exception, traceback_str: str) -> dict` — formats a caught exception into an error dict for the guidance pipeline
- Write unit tests with synthetic trace event lists for each error pattern

**Skills needed:** Python · runtime analysis · tracebacks · data analysis

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🟠 #30 — Build the Perception Bus — Unified Input Router

**Labels:** `medium` `enhancement` `gssoc-2026`

The Perception Bus is the single entry point that receives frames from screen capture and camera feed and routes them to the correct processing engine based on the active domain.

**What you'll code:**
- Create `core/perception/perception_bus.py`
- Implement `PerceptionBus` class:
  - `__init__(domain: str)` — sets the active domain (`digital`, `physical`, or `hybrid`)
  - Holds references to `ScreenCapture` and `CameraFeed` instances
  - `async def start()` — starts the appropriate capture sources based on the domain; `digital` → screen only; `physical` → camera only; `hybrid` → both
  - `async def stop()` — cleanly stops all active capture sources
  - Maintains two output queues: `screen_queue: asyncio.Queue` and `camera_queue: asyncio.Queue`
  - In `hybrid` mode, runs both capture loops concurrently using `asyncio.gather()`
- Write integration tests verifying correct sources start for each domain

**Skills needed:** Python · async · asyncio.Queue · asyncio.gather · system design

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

## ⭐⭐⭐⭐ Hard / Expert Issues — 60 pts each

> These require **deep technical knowledge and end-to-end system thinking**. You will architect and build complex components that connect multiple modules together. Read all of `docs/architecture.md` before picking any of these.

---

### 🔴 #31 — Implement `code_tracer.py` — Full Python Runtime Tracer

**Labels:** `hard` `enhancement` `gssoc-2026`

This is the most technically complex module in the digital domain. The code tracer hooks into Python's runtime at the interpreter level to trace every line, call, and exception of user code as it runs.

**What you'll code:**
- Create `core/digital/code_tracer.py`
- Implement `CodeTracer` class using `sys.settrace`:
  - `start_trace(target_module_name: str)` — sets up the trace hook, scoped to the target module only (never trace Execra's own internals)
  - `stop_trace()` — removes the trace hook, finalizes the event log
  - Internal trace event handler: records `{"event_type": "call"/"line"/"return"/"exception", "function": str, "lineno": int, "args": dict, "return_value": any, "exception": str | None}`
  - `get_trace_log() -> list[dict]` — returns the full event log
  - `get_summary() -> dict` — returns: `total_calls`, `total_lines`, `exceptions_caught`, `max_recursion_depth`, `execution_path` (list of function names in call order)
- Built-in safeguards: stop tracing if recursion depth exceeds 1000; stop if event count exceeds 10,000 per run (prevents memory explosion)
- Benchmark: tracer overhead must be <5% on a 1000-line Python script
- Write unit tests tracing small test functions with known call/return/exception events

**Skills needed:** Python internals · `sys.settrace` · advanced Python · performance

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #32 — Build the Full LLM Abstraction Layer (All 3 Backends)

**Labels:** `hard` `enhancement` `gssoc-2026`

Extend the OpenAI client from issue #23 into a complete multi-backend LLM system supporting GPT-4o, Google Gemini, and Llama 3 through one unified interface.

**What you'll code:**
- Extend `core/intelligence/llm_client.py` (built in #23):
  - Add `GeminiClient(BaseLLMClient)` — using `google.generativeai` SDK, `gemini-1.5-pro` model
  - Add `LlamaClient(BaseLLMClient)` — using Ollama's local REST API (`http://localhost:11434/api/generate`)
  - Add `LLMClientFactory.create() -> BaseLLMClient` — reads `settings.LLM_BACKEND`, instantiates the correct client
  - Add a unified `PromptBuilder` class: `build_guidance_prompt(context, screen_text, trace_summary) -> str` — builds a context-aware prompt for any LLM
  - Add `extract_confidence()` for Gemini (from `safety_ratings`) and Llama (default 0.5 — unavailable)
- All three clients must have identical external behaviour from the caller's perspective
- Write unit tests mocking all three SDKs

**Skills needed:** Python · OpenAI SDK · Google Generative AI SDK · Ollama REST API · abstract design patterns

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #33 — Build the Hybrid Rule + LLM Intelligence Core

**Labels:** `hard` `enhancement` `gssoc-2026`

Build the `IntelligenceCore` — the orchestrator that runs the LLM, rule-based validator, and consequence simulator in parallel and merges their outputs into a single trust-scored `GuidanceInstruction`.

**What you'll code:**
- Create `core/intelligence/intelligence_core.py`
- Implement `IntelligenceCore` class:
  - `__init__(llm_client, rule_engine, consequence_sim, trust_scorer)`
  - `async def generate_guidance(context: SessionContext, screen_text: str, trace_summary: dict) -> GuidanceInstruction`
    - Runs LLM, rule validation, and consequence simulation **concurrently** using `asyncio.gather()`
    - Applies **rule engine veto**: if the rule engine's top rule returns `severity == "critical"`, return a warning instruction regardless of LLM output
    - Passes merged signals to `TrustScorer`
    - Returns a fully populated `GuidanceInstruction`
- Implement `RuleEngine` class with ≥10 deterministic Python rules (reuse/expand from `consequence_sim.py`)
- Write integration tests with mocked LLM and rules covering: normal flow, rule veto activation, LLM timeout fallback

**Skills needed:** Python · async · asyncio.gather · system integration · design patterns

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #34 — Build the End-to-End Real-Time Guidance Streaming Pipeline

**Labels:** `hard` `enhancement` `gssoc-2026`

Connect every module together into a single real-time loop: Perception Bus → Processing → Intelligence Core → Trust Scorer → WebSocket broadcast. This is the core runtime that makes Execra live.

**What you'll code:**
- Create `core/pipeline.py`
- Implement `ExecraPipeline` class:
  - `__init__(domain, mode)` — initialises all subsystems: `PerceptionBus`, `ContextEngine`, `IntelligenceCore`, `GuidanceDispatcher`, `ActionLogger`
  - `async def run()` — the main async loop: consumes frames from the perception bus queues, runs processing, calls intelligence core, dispatches guidance via WebSocket
  - Implement backpressure: if the processing queue is full, drop the oldest frame (never block perception)
  - Implement guidance deduplication: do not send the same instruction twice in a row
  - Target latency: ≤500ms from frame arrival to WebSocket broadcast
  - `async def stop()` — cleanly shuts down all subsystems
- Integrate pipeline startup into `main.py` and `api/main.py` startup event
- Write end-to-end integration tests with mocked perception and LLM
- Benchmark latency and document results

**Skills needed:** Python · asyncio · system design · performance engineering · integration

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #35 — Build the Physical Domain Pipeline (CV + Task Guidance)

**Labels:** `hard` `enhancement` `gssoc-2026`

Connect the camera feed, YOLO detector, OCR, spatial analysis, task recognizer, and LLM into a single physical domain pipeline that watches the camera and delivers real-world task guidance.

**What you'll code:**
- Create `core/physical/physical_pipeline.py`
- Implement `PhysicalPipeline` class:
  - Consumes frames from `CameraFeed` queue
  - For each frame: run `ObjectDetector.detect()` + `OCREngine.extract_text()` concurrently
  - Pass detections + OCR text to `TaskRecognizer.recognize()`
  - If task type changed: call `TaskDecomposer` via LLM to generate a new step list and reset `SessionContext`
  - If task type same: advance to the next step based on detected progress
  - Dispatch guidance via `GuidanceDispatcher`
- Implement `SpatialAnalyzer` helper in `core/physical/spatial_analyzer.py`:
  - `compute_relative_positions(detections: list[Detection]) -> dict` — returns relative positions (left-of, right-of, near, far) between detected object pairs
- Run at configurable FPS (default: 5); benchmark inference time
- Write end-to-end tests with sample frames for each supported task type

**Skills needed:** Python · Computer vision · YOLOv8 · async · system integration

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #36 — Build the Electron.js Frontend Overlay

**Labels:** `hard` `enhancement` `gssoc-2026`

Build the actual desktop UI — an always-on-top, semi-transparent overlay that displays Execra's guidance in real time over the user's screen while they work.

**What you'll code:**
- Set up Electron.js app in `frontend/overlay/`:
  - `main.js` — create the always-on-top, frameless, semi-transparent `BrowserWindow`
  - `preload.js` — expose WebSocket bridge to the renderer via `contextBridge`
  - `renderer/index.html` + `renderer/app.js` — the guidance UI
- UI must display:
  - Current instruction text (animated fade-in on new instruction)
  - Confidence bar (coloured: green ≥85%, orange 65–84%, red <65%)
  - Step counter: "Step 4 of 9"
  - Source tags: `LLM` `Rule Engine` `Trace` (pill badges)
  - Error alerts: red banner with severity icon
  - Mode indicator pill: `PASSIVE` / `ACTIVE` / `MIXED`
- Connect to `ws://localhost:8000/ws/guidance` and handle all server event types
- Add minimize/expand toggle button
- Add Active Mode text input (shown only in `active` or `mixed` mode)
- Style: dark glass-morphism — `background: rgba(10, 10, 20, 0.85)` with blur

**Skills needed:** JavaScript · Electron.js · WebSocket · CSS (glass-morphism) · UI/UX

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #37 — Implement Redis Hot-Cache for the Context Engine

**Labels:** `hard` `enhancement` `gssoc-2026`

The guidance pipeline reads session context on every frame. SQLite reads are too slow (<10ms target). Add Redis as a hot-cache layer with read-through and write-through caching.

**What you'll code:**
- Extend `core/intelligence/context_engine.py`:
  - Add `ContextCache` inner class using `aioredis`:
    - `write(session: SessionContext)` — serialize to JSON, store in Redis with key `context:{session_id}` and TTL of 1800s (30 min)
    - `read(session_id: str) -> SessionContext | None` — deserialize from Redis; return `None` on miss
    - `invalidate(session_id: str)` — delete from Redis
  - Modify all `ContextEngine` methods to: **write to both Redis and SQLite** on every update, **read from Redis first** and fall back to SQLite on cache miss
- Benchmark: measure context read latency with and without Redis; verify ≤10ms with Redis
- Write unit tests mocking both Redis and SQLite
- Graceful degradation: if Redis is unavailable, fall back to SQLite-only mode with a warning log

**Skills needed:** Python · Redis · `aioredis` · caching patterns · async · performance

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #38 — Optimize Screen Capture with Multiprocessing & Shared Memory

**Labels:** `hard` `performance` `gssoc-2026`

The screen capture module must run 24/7 without impacting the user's system. Move it to a separate process with shared memory and adaptive FPS to reach ≤3% CPU on idle screens.

**What you'll code:**
- Refactor `core/perception/screen_capture.py`:
  - Move the capture loop to a `multiprocessing.Process` (bypasses Python's GIL entirely)
  - Use `multiprocessing.shared_memory.SharedMemory` to pass frame data to the main process without copying
  - Implement `AdaptiveFPSController`:
    - Tracks the rolling average delta percentage over the last 10 frames
    - If average delta <1%: reduce FPS to 1 (almost nothing happening)
    - If average delta 1–10%: use configured FPS (default: 2)
    - If average delta >10%: increase to 5 FPS (lots of activity)
  - Apply JPEG compression to frames stored in shared memory to reduce bandwidth
- Benchmark and document: CPU usage on idle screen, CPU usage on active coding session
- Target: ≤3% CPU idle, ≤15% CPU active
- Write unit tests mocking `multiprocessing.Process` and `SharedMemory`

**Skills needed:** Python · multiprocessing · shared memory · performance profiling · systems programming

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #39 — Build the Full Digital Domain Pipeline

**Labels:** `hard` `enhancement` `gssoc-2026`

Wire all digital domain modules into a single `DigitalPipeline` that watches the screen, traces code, detects errors, and delivers step-by-step guidance completely autonomously.

**What you'll code:**
- Create `core/digital/digital_pipeline.py`
- Implement `DigitalPipeline` class:
  - Consumes frames from `PerceptionBus.screen_queue`
  - For each frame: run `OCREngine.extract_text()` to get screen text
  - Implement IDE/editor detection: check if OCR text contains Python/JS syntax patterns → set domain as confirmed `digital`
  - Trigger `CodeTracer` when a "Run" / "Execute" action is detected on screen (keyword matching in OCR)
  - Pass trace log to `ErrorDetector.analyze_trace()`
  - Route detected errors to `IntelligenceCore.generate_guidance()`
  - Dispatch result via `GuidanceDispatcher`
  - Update `SessionContext` step on each guidance delivery
- Handle pipeline crashes with a watchdog: auto-restart the pipeline if it crashes, log the exception
- Write end-to-end integration tests with a synthetic buggy Python script as input — verify guidance is produced within 500ms

**Skills needed:** Python · asyncio · system integration · error handling · watchdog pattern

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

### 🔴 #40 — Build the Full Undo and Session Replay System

**Labels:** `hard` `enhancement` `gssoc-2026`

Build a complete undo system where users can reverse the last guided action, plus a full session replay feature that re-runs a past session's actions for review or debugging.

**What you'll code:**
- Extend `core/hybrid/action_logger.py`:
  - Add `is_undoable: bool` and `undo_instruction: str | None` to `ActionRecord`
  - Add `Undoable` mixin class: `def get_undo_instruction(self) -> str` — returns the human-readable undo instruction
  - Implement `undo_last(dispatcher: GuidanceDispatcher) -> ActionRecord | None` — pops the last undoable action, dispatches the undo instruction via the guidance dispatcher, returns the undone action record
  - Implement `replay_session(session_id: str, speed: float = 1.0)` — async generator that yields `ActionRecord` objects in order, with `asyncio.sleep(action.interval / speed)` between each
- Extend REST API in `api/routes/actions.py`:
  - Add `POST /api/v1/actions/undo` — calls `undo_last()`, returns `409` if stack is empty
  - Add `POST /api/v1/actions/replay` — accepts `{"session_id": str, "speed": float}`, streams replay via WebSocket `replay_action` events
- Implement keyboard shortcut listener using `pynput`: `Ctrl+Z` in Passive mode triggers `undo_last()` automatically
- Ensure all operations are idempotent (double-undo is safe)
- Write integration tests for undo, double-undo safety, and replay streaming

**Skills needed:** Python · async generators · `pynput` · keyboard hooks · REST API · complex state management

**👉 [Claim this issue on GitHub →](https://github.com/sahoo-tech/execra/issues)**

---

---

<div align="center">

## 📊 Issues at a Glance

| Level | Count | Points Each | Total Possible |
|-------|-------|------------|---------------|
| ⭐ Beginner | 10 issues | 10 pts | 100 pts |
| ⭐⭐ Easy | 10 issues | 25 pts | 250 pts |
| ⭐⭐⭐ Medium | 10 issues | 45 pts | 450 pts |
| ⭐⭐⭐⭐ Hard/Expert | 10 issues | 60 pts | 600 pts |
| **Total** | **40 issues** | | **1,400 pts** |

---

> 💡 **Tip:** Start with **#1 (project structure)** or **#2 (config loader)** — these are the foundation every other issue depends on!

**[📋 View Live GitHub Issues](https://github.com/sahoo-tech/execra/issues) · [📖 Read CONTRIBUTING.md](../CONTRIBUTING.md) · [🏗️ Read Architecture Docs](./architecture.md)**

---

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer&text=Happy%20Contributing%21&fontSize=30&fontColor=ffffff&animation=fadeIn" width="100%" alt="Footer"/>

*Built with ❤️ for GirlScript Summer of Code 2026 · Execra — Execute without boundaries.*

</div>
