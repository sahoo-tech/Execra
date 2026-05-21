<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=EXECRA&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Universal%20Execution%20Intelligence%20Layer&descAlignY=60&descAlign=50&descSize=22" width="100%" alt="Execra Banner"/>

<br/>

<!-- Badges -->
<a href="https://github.com/sahoo-tech/execra/stargazers"><img src="https://img.shields.io/github/stars/sahoo-tech/execra?style=for-the-badge&logo=github&color=FFD700&labelColor=1a1a2e" alt="Stars"/></a>
<a href="https://github.com/sahoo-tech/execra/network/members"><img src="https://img.shields.io/github/forks/sahoo-tech/execra?style=for-the-badge&logo=github&color=00D4FF&labelColor=1a1a2e" alt="Forks"/></a>
<a href="https://github.com/sahoo-tech/execra/issues"><img src="https://img.shields.io/github/issues/sahoo-tech/execra?style=for-the-badge&logo=github&color=FF6B6B&labelColor=1a1a2e" alt="Issues"/></a>
<a href="https://github.com/sahoo-tech/execra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/sahoo-tech/execra?style=for-the-badge&color=00C896&labelColor=1a1a2e" alt="License"/></a>
<a href="https://github.com/sahoo-tech/execra/pulls"><img src="https://img.shields.io/github/issues-pr/sahoo-tech/execra?style=for-the-badge&color=A78BFA&labelColor=1a1a2e" alt="Pull Requests"/></a>
<img src="https://img.shields.io/badge/GSSoC-2026-orange?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgo=&labelColor=1a1a2e" alt="GSSoC 2026"/>
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&labelColor=1a1a2e" alt="Status"/>

<br/><br/>

> **"Don't learn to do it — just do it correctly, right now."**
>
> *Execra is not a chatbot. Not a tutorial. Not a coding assistant. It is your real-time execution partner — observing, understanding, and guiding every action you take, before mistakes happen.*

<br/>

[![GirlScript Summer of Code](https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=flat-square&logo=girlscript&logoColor=white)](https://gssoc.girlscript.tech/)
&nbsp;
[![Open Source](https://img.shields.io/badge/Open%20Source-❤️%20Love-red?style=flat-square)](https://opensource.org/)
&nbsp;
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square&logo=git)](https://github.com/sahoo-tech/execra/pulls)

</div>

---

## 📑 Table of Contents

<details open>
<summary><b>Click to expand / collapse</b></summary>

- [🌟 What is Execra?](#-what-is-execra)
- [🎯 Core Objective](#-core-objective)
- [🔥 The Problem We Solve](#-the-problem-we-solve)
- [✨ Core Capabilities](#-core-capabilities)
- [🏗️ System Architecture](#️-system-architecture)
- [🔄 User Workflow](#-user-workflow)
- [🧠 Intelligence Layers Explained](#-intelligence-layers-explained)
- [💻 Tech Stack](#-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [📂 Project Structure](#-project-structure)
- [🤝 Contributing (GSSoC 2026)](#-contributing-gssoc-2026)
- [🏷️ Issue Labels & Points](#️-issue-labels--points)
- [📜 Code of Conduct](#-code-of-conduct)
- [📄 License](#-license)
- [🙌 Acknowledgements](#-acknowledgements)
- [📬 Contact](#-contact)

</details>

---

## 🌟 What is Execra?

**Execra** *(Execution + Era)* is a **multimodal AI-powered Universal Execution Intelligence Layer** — a continuously running background system that observes your actions in real time across both **digital environments** (coding, software) and **physical environments** (real-world tasks via camera), and actively guides you through correct execution **before mistakes happen**.

> Unlike a chatbot that answers only when asked, Execra **acts like an expert sitting beside you**, watching your every step and speaking up the moment it predicts an error, inefficiency, or risk.

```
Traditional Workflow:        Execra Workflow:
┌──────────────────┐         ┌─────────────────────────────────┐
│  Search → Learn  │         │  Start Task → Execra Guides You │
│  → Practice      │   VS    │  in Real-Time → Execute         │
│  → Fail → Retry  │         │  Correctly → Done               │
└──────────────────┘         └─────────────────────────────────┘
```

### Real-Time Monitoring Dashboard

The SvelteKit dashboard provides a futuristic UI showing real-time telemetry, live action logs, active WebSocket connection status, and guidance feedback:

![Execra Monitoring Dashboard Preview](docs/images/dashboard_preview.png)

---

## 🎯 Core Objective

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   Build an AI that does NOT wait for prompts.                    ║
║                                                                  ║
║   It OBSERVES → UNDERSTANDS → GUIDES → CORRECTS                  ║
║   continuously, in real time, without user re-explanation.       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🔥 The Problem We Solve

| Pain Point | Current Reality | Execra's Solution |
|---|---|---|
| 🔍 **Searching** | Stop work → Google → read docs | Guidance appears in-context, zero search |
| 📚 **Learning Curve** | Spend hours learning before doing | Do directly with guided steps |
| ❌ **Trial & Error** | Make mistakes, debug, retry | Errors predicted before they happen |
| 🤖 **Generic AI** | Copy-pasted answers without context | Understands exactly what *you* are doing |
| 📷 **Physical Tasks** | No AI help for real-world work | Camera-based real-world guidance |
| 🔁 **Re-explaining AI** | Repeat yourself each session | Remembers full context of current session |

---

## ✨ Core Capabilities

<table>
<tr>
<td width="50%" valign="top">

### 👁️ 1. Multimodal Perception
- 🖥️ Screen capture (code, software UI)
- 📷 Camera feed (real-world tasks)
- 🔤 OCR — text recognition
- 🧩 Object detection & UI understanding
- ⚡ Continuous action tracking
- 🛡️ **Privacy Masking Engine (Local Redaction)**

### 🧭 2. Context & Intent Understanding
- 📌 Auto-detect task type (no prompt needed)
- 🎯 Infer user goal from observation
- 📋 Track current step in workflow
- 🔄 Maintain dynamic session context model

### ⚙️ 3. Execution Intelligence
- 📊 Decompose tasks into ordered steps
- 🔴 Real-time error detection
- 📡 Adapt instructions to user progress
- 🔮 Predict consequences before action

</td>
<td width="50%" valign="top">

### 💻 4. Coding System (Digital)
- 🪲 Runtime execution tracing
- 🔍 Logical error identification
- 💡 Explain errors from actual behavior (not just static analysis)
- 🏗️ Convert high-level goals → structured dev steps

### 🏠 5. Offline System (Physical)
- 🔧 Detect objects & tools via camera
- 🍳 Guide cooking, repairs, form filling
- 🚨 Intervene before incorrect actions
- 📍 Recognize task type from visual input

### 🛡️ 6. Trust & Authenticity Layer
- 📊 Confidence score on every instruction
- 🔍 Reasoning & explanation per suggestion
- 🔁 Multi-source validation (rules + model + data)
- ⚠️ Uncertainty flagging
- 🐢 Safe Mode | ⚡ Expert Mode

</td>
</tr>
</table>

---


## 🏗️ System Architecture

### High-Level Architecture Diagram

```mermaid
flowchart TD

A[Input Layer]

A1[Screen Capture]
A2[Camera Feed]
A3[User Text Input]

A --> A1
A --> A2
A --> A3

B[Processing Layer]

B1[Code Runtime Trace Engine]
B2[Computer Vision OCR + Detection]
B3[Context Engine Task Detector]

A1 --> B1
A2 --> B2
A3 --> B3

C[Intelligence Layer]

C1[LLM Reasoning]
C2[Rule-Based Validator]
C3[Prediction and Simulation]

B1 --> C1
B2 --> C2
B3 --> C3

D[Trust and Confidence Scorer]

C1 --> D
C2 --> D
C3 --> D

E[Output Layer]

E1[Real-Time Instructions]
E2[Error Alerts and Warnings]
E3[Confidence Indicators]

D --> E

E --> E1
E --> E2
E --> E3
```
### Subsystem Communication Flow

```mermaid
flowchart TD

A[User Action]

B[Perception Bus<br/>Screen + Camera]

C1[Code Engine<br/>Digital]
C2[CV Engine<br/>Physical]
C3[Intent Engine<br/>Context]

D[Intelligence Core<br/>LLM + Rules + Prediction]

E[Trust Scorer<br/>Confidence greater than 80%]

F1[Deliver Instruction<br/>+ Confidence Score]
F2[Flag Uncertainty<br/>+ Request Clarification]

G[Action Logger<br/>Undo / Replay]

A --> B

B --> C1
B --> C2
B --> C3

C1 --> D
C2 --> D
C3 --> D

D --> E

E -->|Yes| F1
E -->|No| F2

F1 --> G
F2 --> G

G -. Feedback Loop .-> B
```

---

### Real-Time WebSocket & API Architecture

Execra implements a decoupled, event-driven observer pattern to broadcast action events to connected clients in real time. The sequence below describes the handshake and notification lifecycle.

```mermaid
sequenceDiagram
    participant Frontend as SvelteKit Dashboard
    participant WS as WebSocket Router
    participant CM as Connection Manager
    participant AL as Action Logger (Observer)

    Frontend->>WS: ws://localhost:8000/ws
    WS->>CM: connect()
    CM->>CM: Add to active connections (set)
    CM-->>Frontend: {"event": "handshake", ...}
    
    Note over Frontend, AL: Real-time Event Broadcast Flow
    AL->>CM: notify(action)
    CM->>Frontend: {"event": "action_logged", "data": {...}}
```

#### WebSocket Event Schema

##### 1. Server Handshake Response
Sent immediately upon client connection:
```json
{
  "event": "handshake",
  "version": "1.0.0",
  "message": "Connected to ws://localhost:8000/ws"
}
```

##### 2. Action Logged Broadcast
Broadcasting payload to all active connections when a physical or digital action is recorded:
```json
{
  "event": "action_logged",
  "data": {
    "id": "act_1716200230",
    "session_id": "sess_9123",
    "timestamp": "2026-05-20T11:24:35.832Z",
    "type": "user_click",
    "description": "Clicked dashboard simulation button",
    "domain": "digital",
    "was_guided": true,
    "guidance_confidence": 0.95
  }
}
```

#### REST API Endpoints

| Method | Endpoint | Description | Payload Schema / Response |
|--------|----------|-------------|----------------------------|
| **GET** | `/api/v1/actions` | Retrieve recently recorded execution actions. | `{"actions": [...], "count": 2}` |
| **POST** | `/api/v1/actions` | Log a new action record and broadcast to WebSocket observers. | `ActionRecord` model |
| **POST** | `/api/v1/actions/undo` | Revert the last execution action from the log. | `{"message": "Action undone", "action_undone": {...}}` |

---

### Dual-Domain Architecture (Digital + Physical)

```mermaid
flowchart TD

A[EXECRA CORE]

B1[Digital Domain IDE]
B2[Physical Domain Camera]

A --> B1
A --> B2

C1[Screen Capture]
C2[Code Parser]
C3[Runtime Tracer]
C4[Logic Debugger]
C5[Execution Flow Map]

D1[Live Camera Feed]
D2[Object Detection]
D3[Spatial Analysis]
D4[OCR Text in Scene]
D5[Action Recognition]

B1 --> C1
B1 --> C2
B1 --> C3
B1 --> C4
B1 --> C5

B2 --> D1
B2 --> D2
B2 --> D3
B2 --> D4
B2 --> D5

E[Unified Context Model]

C1 --> E
D1 --> E

F1[Current Task State]
F2[Step Tracker]
F3[Error History]
F4[User Profile]

E --> F1
E --> F2
E --> F3
E --> F4
```

---

## 🔄 User Workflow

```mermaid
flowchart LR

A1["① User Starts Task"]
A2["② Execra Detects Context"]
A3["③ Task Model Built Internally"]
A4["④ Step-by-Step Guidance Begins"]
A5["⑤ Execution Monitored Continuously"]
A6["⑥ Errors Detected and Consequences Simulated"]
A7["⑦ Adapts to Progress Dynamically"]
A8["⑧ Task Complete"]
A9["⑨ User can ask Text Questions"]

A1 --> A2
A2 --> A3
A3 --> A4
A4 --> A5
A5 --> A6
A6 --> A7
A7 --> A8

A9 --> A5
```

---

### Step-by-Step Execution Detail

| Step | What Happens | Who Acts |
|------|-------------|----------|
| **1. Start** | User begins any task (opens editor, starts camera, opens form) | User |
| **2. Detection** | Execra auto-detects: task type, domain (digital/physical), current state | Execra |
| **3. Modeling** | Internal task model built: steps, dependencies, expected sequence | Execra |
| **4. Guidance** | Step-by-step instructions displayed in an overlay/panel | Execra |
| **5. Monitoring** | Every action tracked against expected behavior in real time | Execra |
| **6. Error Detection** | Deviations flagged; consequences simulated before commitment | Execra |
| **7. Adaptation** | Instructions updated dynamically based on user progress | Execra |
| **8. Completion** | Task completed with minimal trial-and-error | Both |
| **9. Active Mode** | At any time, user can type a question — context auto-remembered | User + Execra |

---

## 🧠 Intelligence Layers Explained

### Layer 1 — Consequence Simulation Engine

```mermaid
flowchart TD

A["User presses Run / Submit / Performs Action"]

B["Consequence Simulator"]

C["Current State Analysis"]

D["Possible Outcomes"]

E1["✅ Outcome A<br/>Code compiles successfully"]
E2["⚠️ Outcome B<br/>Off-by-one error causes overflow"]
E3["❌ Outcome C<br/>Infinite loop detected"]

F["Recommendation<br/>Adjust line 14 condition"]

G["Confidence: 91%<br/>Source: Runtime Trace + Rules"]

A --> B
B --> C
C --> D

D --> E1
D --> E2
D --> E3

E1 --> F
E2 --> F
E3 --> F

F --> G
```
### Layer 2 — Trust & Confidence Scoring

```mermaid
flowchart TD

A["Instruction Generated"]

B["Trust Scoring Engine"]

C1["LLM Validation"]
C2["Rule Engine Validation"]
C3["Execution Trace Analysis"]

D["Confidence Calculation"]

E["87% Confidence"]

F["Reasoning Generated"]

G["Instruction Delivered<br/>Safe Mode / Expert Mode"]

A --> B

B --> C1
B --> C2
B --> C3

C1 --> D
C2 --> D
C3 --> D

D --> E
E --> F
F --> G
```

```text
Every instruction delivered by Execra includes:

┌──────────────────────────────────────────────────────┐
│  📋 INSTRUCTION: "Add null check before line 42"     │
│                                                      │
│  🔵 Confidence:  ████████░░  87%                     │
│  📚 Source:      LLM + Rule Engine + Execution Trace │
│  💬 Reasoning:   "Variable `config` returns None     │
│                   in 3 edge cases detected."         │
│  🔘 Mode:        [Safe Mode] / Expert Mode           │
└──────────────────────────────────────────────────────┘
```

---

### Layer 3 — Hybrid Interaction System

```mermaid
flowchart TD

A["HYBRID INTERACTION"]

B1["PASSIVE MODE<br/>Auto-observe<br/>Auto-guide<br/>No prompts needed"]

B2["ACTIVE MODE<br/>User asks text questions<br/>Context auto-remembered"]

B3["MIXED MODE<br/>Both modes active simultaneously"]

A --> B1
A --> B2
A --> B3
```

---
## 💻 Tech Stack

<table>
<thead>
<tr>
<th>Layer</th>
<th>Technology</th>
<th>Purpose</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>👁️ Screen Capture</b></td>
<td>PyAutoGUI, mss, Pillow</td>
<td>Continuous screen recording & analysis</td>
</tr>
<tr>
<td><b>📷 Camera / CV</b></td>
<td>OpenCV, YOLOv8, Tesseract OCR</td>
<td>Real-world object detection & text reading</td>
</tr>
<tr>
<td><b>🧠 LLM Core</b></td>
<td>OpenAI GPT-4o / Gemini 1.5 Pro / Llama 3</td>
<td>Reasoning, explanation, task decomposition</td>
</tr>
<tr>
<td><b>⚙️ Code Engine</b></td>
<td>Python AST, sys.settrace, PyDebug</td>
<td>Runtime tracing & execution flow analysis</td>
</tr>
<tr>
<td><b>🗂️ Context Engine</b></td>
<td>LangChain, custom session manager</td>
<td>Maintaining dynamic session context model</td>
</tr>
<tr>
<td><b>🔁 Rule Validator</b></td>
<td>Drools / Python rule engine</td>
<td>Deterministic validation alongside LLM</td>
</tr>
<tr>
<td><b>📊 Trust Scorer</b></td>
<td>Custom scoring pipeline</td>
<td>Confidence scoring per instruction</td>
</tr>
<tr>
<td><b>🖥️ Frontend / Overlay</b></td>
<td>Electron.js / Tauri / Web Overlay</td>
<td>Real-time guidance UI overlaid on screen</td>
</tr>
<tr>
<td><b>🔔 Notification</b></td>
<td>Plyer / OS Notification APIs</td>
<td>Proactive alerts & guidance delivery</td>
</tr>
<tr>
<td><b>💾 Storage</b></td>
<td>SQLite / Redis (hot) + S3 (cold)</td>
<td>Action history, undo stack, session logs</td>
</tr>
<tr>
<td><b>🛡️ Privacy Engine</b></td>
<td>OpenCV, Regex (PII Patterns)</td>
<td>Local data sanitization & masking</td>
</tr>
<tr>
<td><b>🐳 Deployment</b></td>
<td>Docker, Kubernetes</td>
<td>Scalable microservice deployment</td>
</tr>
<tr>
<td><b>🔗 API Layer</b></td>
<td>FastAPI</td>
<td>REST + WebSocket endpoints for real-time I/O</td>
</tr>
</tbody>
</table>

---

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.10+
python --version

# Node.js 18+ (for overlay frontend)
node --version

# FFmpeg (for camera stream processing)
ffmpeg -version
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sahoo-tech/execra.git
cd execra/Execra

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate         # Linux/Mac
venv\Scripts\activate            # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install SvelteKit Dashboard dependencies
cd dashboard
npm install
cd ..
```

### Running the Services Locally

#### 1. Start the FastAPI Backend
From the `Execra` root directory:
```bash
# Windows
venv\Scripts\python.exe main.py

# Linux/Mac
./venv/bin/python main.py
```
The API server will run at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

#### 2. Start the SvelteKit Dashboard
From the `Execra/dashboard` directory:
```bash
npm run dev
```
The dashboard interface will run at `http://localhost:5173`.

### Quick Start (Docker)

```bash
# Build and run both backend and frontend with Docker Compose
docker-compose up --build

# Services will be running at:
# API Backend:      http://localhost:8000
# Svelte Dashboard: http://localhost:5173
```


---

## 📂 Project Structure

```text
execra/
│
├── core/
│   │
│   ├── perception/
│   │   ├── screen_capture.py        # Screen capture engine
│   │   ├── camera_feed.py           # Camera input handler
│   │   ├── ocr_engine.py            # Text recognition (Tesseract)
│   │   └── privacy_masker.py        # PII & geometric redaction
│   │
│   ├── intelligence/
│   │   ├── llm_client.py            # LLM abstraction layer
│   │   ├── context_engine.py        # Session/context manager
│   │   ├── consequence_sim.py       # Outcome prediction engine
│   │   └── trust_scorer.py          # Confidence scoring pipeline
│   │
│   ├── digital/
│   │   ├── code_tracer.py           # Runtime execution tracer
│   │   ├── error_detector.py        # Logical/runtime issue detector
│   │   └── task_decomposer.py       # Goal → execution steps
│   │
│   ├── physical/
│   │   ├── object_detector.py       # YOLO-based detection
│   │   ├── task_recognizer.py       # Physical task classification
│   │   └── action_validator.py      # Real-world action validator
│   │
│   └── hybrid/
│       ├── mode_manager.py          # Passive/Active mode manager
│       ├── action_logger.py         # Undo/replay tracking
│       └── guidance_dispatcher.py   # Instruction delivery system
│
├── api/
│   │
│   ├── main.py                      # FastAPI application entry
│   │
│   ├── routes/
│   │   ├── health.py                # Health check endpoints
│   │   ├── execution.py             # Execution guidance APIs
│   │   └── context.py               # Session/context APIs
│   │
│   └── websockets/
│       └── realtime.py              # Real-time communication layer
│
├── models/
│   │
│   ├── yolo/                        # YOLO model weights
│   └── custom/                      # Custom-trained classifiers
│
├── tests/
│   │
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── e2e/                         # End-to-end tests
│
├── docs/
│   ├── architecture.md              # System architecture docs
│   ├── api_reference.md             # API documentation
│   └── contributing_guide.md        # Contributor onboarding guide
│
├── scripts/
│   ├── download_models.py           # Download AI model weights
│   └── setup_environment.py         # Local environment setup
│
├── .github/
│   ├── ISSUE_TEMPLATE/              # GitHub issue templates
│   ├── workflows/                   # GitHub Actions workflows
│   └── pull_request_template.md     # PR template
│
├── configs/
│   ├── development.yaml             # Development configuration
│   ├── production.yaml              # Production configuration
│   └── logging.yaml                 # Logging configuration
│
├── assets/
│   ├── logo/                        # Branding assets
│   ├── screenshots/                 # README screenshots
│   └── diagrams/                    # Architecture diagrams
│
├── docker-compose.yml               # Multi-container orchestration
├── Dockerfile                       # Docker image definition
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata/config
├── pytest.ini                       # Pytest configuration
├── .env.example                     # Environment variables template
├── .gitignore                       # Ignored files
├── LICENSE                          # MIT license
├── README.md                        # Project documentation
└── main.py                          # Main application entry point
```

---

## 🤝 Contributing (GSSoC 2026)

<div align="center">

### 🎉 Welcome, GirlScript Summer of Code 2026 Contributors! 🎉

<img src="https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=for-the-badge&logo=girlscript&logoColor=white" alt="GSSoC 2026"/>

</div>

We're thrilled to have you here! Execra is an **open project** built for and by the community. Whether you're a beginner or an expert, there's a place for you.

---

### 🛣️ Contribution Roadmap

```mermaid
flowchart LR

A["🔍 FIND<br/>an Issue"]

B["🍴 FORK<br/>Repository"]

C["💻 CODE<br/>& Test"]

D["📤 PR<br/>Submitted"]

E["🛠️ Review Process<br/>(Maintainer)"]

F["✅ Approved"]

G["🎉 MERGED!<br/>Points Added"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
```

---

### 📝 Step-by-Step Contribution Guide

```bash
# Step 1: Fork this repository on GitHub

# Step 2: Clone your fork
git clone https://github.com/YOUR_USERNAME/execra.git
cd execra

# Step 3: Create a new branch (NEVER work on main directly)
git checkout -b feature/your-feature-name
# OR for bug fixes:
git checkout -b fix/issue-number-short-description

# Step 4: Make your changes and test them
python -m pytest tests/

# Step 5: Commit with a clear message
git add .
git commit -m "feat: add OCR support for multi-language text detection (#42)"

# Step 6: Push to your fork
git push origin feature/your-feature-name

# Step 7: Open a Pull Request on GitHub
# Use the PR template provided in the repository
```

---

### ✅ Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use When |
|--------|----------|
| `feat:` | Adding a new feature |
| `fix:` | Fixing a bug |
| `docs:` | Documentation only changes |
| `style:` | Code formatting (no logic change) |
| `refactor:` | Code restructuring (no feature/bug) |
| `test:` | Adding or updating tests |
| `chore:` | Build process, tooling changes |

**Examples:**
```
feat: implement real-time screen delta detection
fix: resolve memory leak in camera feed handler (#88)
docs: add API reference for context engine
test: add unit tests for trust scorer module
```

---

### 🔍 Finding Good First Issues

Look for these labels on the [Issues page](https://github.com/sahoo-tech/execra/issues):

| Label | Difficulty | Good For |
|-------|-----------|----------|
| `good first issue` | ⭐ Beginner | First-time contributors |
| `easy` | ⭐⭐ Easy | Those with some experience |
| `medium` | ⭐⭐⭐ Medium | Intermediate contributors |
| `hard` | ⭐⭐⭐⭐ Hard | Advanced contributors |
| `documentation` | Any | Writers, tech writers |
| `help wanted` | Varies | Any contributor |

---

## 🏷️ Issue Labels & Points

> Points are awarded by GSSoC 2026 based on issue difficulty and contribution quality.

<table>
<thead>
<tr>
<th>Label</th>
<th>Points</th>
<th>Typical Tasks</th>
</tr>
</thead>
<tbody>
<tr>
<td><img src="https://img.shields.io/badge/Level%201-Easy-4CAF50?style=flat-square"/> <code>good first issue</code></td>
<td><b>10 pts</b></td>
<td>Fixing typos, adding docstrings, small UI tweaks, writing examples</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Level%202-Easy-66BB6A?style=flat-square"/> <code>easy</code></td>
<td><b>25 pts</b></td>
<td>Adding unit tests, small bug fixes, minor feature additions</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Level%203-Medium-FF9800?style=flat-square"/> <code>medium</code></td>
<td><b>45 pts</b></td>
<td>Feature modules, integration tasks, significant bug fixes</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/Level%204-Hard-F44336?style=flat-square"/> <code>hard</code></td>
<td><b>60 pts</b></td>
<td>Core architecture, new domain engines, performance optimization</td>
</tr>
</tbody>
</table>

---

### 🚫 What NOT to Do

```
❌  Do NOT submit empty or low-quality PRs just to collect points
❌  Do NOT spam issues asking to be assigned without reviewing
❌  Do NOT copy code from others without attribution
❌  Do NOT make changes outside the scope of the assigned issue
❌  Do NOT force-push to main or shared branches
✅  DO read the full issue before asking questions
✅  DO test your changes before submitting
✅  DO follow the code style guide (see CONTRIBUTING.md)
✅  DO be respectful and patient with maintainers
```

---

### 💬 Community & Support

| Channel | Link |
|---------|------|
| 💬 Discussion | [GitHub Discussions](https://github.com/sahoo-tech/execra/discussions) |
| 🐛 Bug Reports | [Open an Issue](https://github.com/sahoo-tech/execra/issues/new?template=bug_report.md) |
| 💡 Feature Requests | [Request Feature](https://github.com/sahoo-tech/execra/issues/new?template=feature_request.md) |
| 📧 Maintainer | ss9830872697@gmail.com |

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct v2.1](CODE_OF_CONDUCT.md).

**In summary:**
- 🤝 Be welcoming and inclusive
- 🗣️ Be respectful in all communications
- 🚫 No harassment, discrimination, or harmful behavior
- 🌱 Help beginners; everyone starts somewhere

Violations can be reported to **ss9830872697@gmail.com**.

---

## 📄 License

```
MIT License

Copyright (c) 2026 Execra Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

See [LICENSE](LICENSE) for the full text.

---

## 🙌 Acknowledgements

<div align="center">

**Powered By**

[![GirlScript Summer of Code](https://img.shields.io/badge/GirlScript%20Summer%20of%20Code-2026-FF6B35?style=for-the-badge)](https://gssoc.girlscript.tech/)
&nbsp;
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai)](https://openai.com)
&nbsp;
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=google)](https://gemini.google.com)
&nbsp;
[![YOLOv8](https://img.shields.io/badge/Ultralytics-YOLOv8-0099FF?style=for-the-badge)](https://ultralytics.com)

</div>

Special thanks to:
- 🌸 **GirlScript Foundation** — for organizing GSSoC and empowering open source contributors worldwide
- All first-time contributors who made this project possible
- The open source community for the foundational tools this project builds upon

---

## 📬 Contact

<div align="center">

| Maintainer | GitHub | Email |
|-----------|--------|-------|
| Sayantan Sahoo | [@sahoo-tech](https://github.com/sahoo-tech) | ss9830872697@gmail.com |

<br/>

**Found this project interesting? Give it a ⭐ — it helps us grow!**

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer&text=Happy%20Contributing%21&fontSize=40&fontColor=ffffff&animation=fadeIn" width="100%" alt="Footer"/>

</div>

---

<div align="center">

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
