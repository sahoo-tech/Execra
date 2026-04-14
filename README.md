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

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         E X E C R A   SYSTEM                            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        INPUT LAYER                              │   ║
║   │                                                                 │   ║
║   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │   ║
║   │   │ Screen Capture│   │  Camera Feed │   │  User Text Input │   │   ║
║   │   │  (Digital AI) │   │ (Physical AI)│   │  (Active Mode)   │   │   ║
║   │   └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘   │   ║
║   └──────────┼──────────────────┼────────────────────┼─────────────┘   ║
║              │                  │                     │                  ║
║              ▼                  ▼                     ▼                  ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                      PROCESSING LAYER                           │   ║
║   │                                                                 │   ║
║   │ ┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐  │   ║
║   │ │  Code Runtime  │  │ Computer Vision   │  │  Context Engine  │  │   ║
║   │ │  Trace Engine  │  │ (OCR + Detection) │  │ (Task Detector)  │  │   ║
║   │ └───────┬───────┘  └────────┬─────────┘  └────────┬─────────┘  │   ║
║   └─────────┼───────────────────┼────────────────────┼─────────────┘   ║
║             │                   │                     │                  ║
║             ▼                   ▼                     ▼                  ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                     INTELLIGENCE LAYER                          │   ║
║   │                                                                 │   ║
║   │ ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐   │   ║
║   │ │     LLM      │  │  Rule-Based       │  │  Prediction       │   │   ║
║   │ │  (Reasoning) │  │  Validator        │  │  & Simulation     │   │   ║
║   │ └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘   │   ║
║   │        │                   │                      │              │   ║
║   │        └───────────────────┴──────────────────────┘             │   ║
║   │                            │                                    │   ║
║   │              ┌─────────────▼──────────────┐                    │   ║
║   │              │   TRUST & CONFIDENCE SCORER │                    │   ║
║   │              │   (Score + Explanation)      │                    │   ║
║   │              └─────────────────────────────┘                    │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                │                                         ║
║                                ▼                                         ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        OUTPUT LAYER                             │   ║
║   │                                                                 │   ║
║   │   ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐ │   ║
║   │   │  Real-Time │  │ Error Alerts │  │  Confidence Indicators  │ │   ║
║   │   │ Instruction│  │  & Warnings  │  │  + Reasoning Display   │ │   ║
║   │   └────────────┘  └──────────────┘  └────────────────────────┘ │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

### Subsystem Communication Flow

```
                          USER ACTION
                              │
                    ┌─────────▼─────────┐
                    │   Perception Bus   │◄──────────────────────────┐
                    │ (Screen + Camera)  │                           │
                    └─────────┬─────────┘                           │
                              │                                      │
              ┌───────────────┼───────────────┐                     │
              │               │               │                     │
    ┌─────────▼────┐  ┌───────▼──────┐  ┌────▼──────────┐          │
    │  Code Engine │  │  CV Engine   │  │ Intent Engine │          │
    │  (Digital)   │  │  (Physical)  │  │ (Context)     │          │
    └─────────┬────┘  └───────┬──────┘  └────┬──────────┘          │
              │               │               │                     │
              └───────────────▼───────────────┘                     │
                              │                                      │
                    ┌─────────▼─────────┐                           │
                    │  Intelligence Core │                           │
                    │  (LLM + Rules +   │                           │
                    │   Prediction)     │                           │
                    └─────────┬─────────┘                           │
                              │                                      │
                    ┌─────────▼─────────┐                           │
                    │   Trust Scorer    │                           │
                    │ Confidence > 80%? │                           │
                    └──┬────────────┬───┘                           │
                       │            │                               │
               Yes ────┘            └──── No                       │
                  │                          │                      │
     ┌────────────▼──────────┐  ┌────────────▼─────────────┐       │
     │  Deliver Instruction  │  │  Flag Uncertainty +       │       │
     │  + Confidence Score   │  │  Request Clarification    │       │
     └────────────┬──────────┘  └────────────┬─────────────┘       │
                  │                           │                     │
                  └─────────────┬─────────────┘                     │
                                │                                   │
                      ┌─────────▼─────────┐                        │
                      │   Action Logger   │────────────────────────┘
                      │  (Undo / Replay)  │   Feedback loop
                      └───────────────────┘
```

---

### Dual-Domain Architecture (Digital + Physical)

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXECRA CORE                              │
│                                                                 │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐  │
│  │   DIGITAL DOMAIN (IDE)  │   │   PHYSICAL DOMAIN (Camera)  │  │
│  │                         │   │                             │  │
│  │  📺 Screen Capture      │   │  📷 Live Camera Feed        │  │
│  │  🔤 Code Parser         │   │  🔍 Object Detection        │  │
│  │  ⚙️  Runtime Tracer     │   │  📐 Spatial Analysis        │  │
│  │  🐞 Logic Debugger      │   │  🏷️  OCR (Text in Scene)    │  │
│  │  📈 Execution Flow Map  │   │  🔄 Action Recognition      │  │
│  │                         │   │                             │  │
│  │  Examples:              │   │  Examples:                  │  │
│  │  • Code debugging       │   │  • Hardware repair          │  │
│  │  • Form completion      │   │  • Cooking guidance         │  │
│  │  • Software navigation  │   │  • Physical form filling    │  │
│  │  • API integration      │   │  • Device assembly          │  │
│  └────────────┬────────────┘   └──────────────┬──────────────┘  │
│               │                               │                  │
│               └───────────────┬───────────────┘                  │
│                               │                                  │
│                  ┌────────────▼────────────┐                     │
│                  │   UNIFIED CONTEXT MODEL  │                     │
│                  │   • Current Task State   │                     │
│                  │   • Step Tracker         │                     │
│                  │   • Error History        │                     │
│                  │   • User Profile         │                     │
│                  └─────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECRA USER JOURNEY                          │
└─────────────────────────────────────────────────────────────────┘

    ①                         ②                         ③
┌─────────┐             ┌──────────────┐           ┌───────────────┐
│  User   │  ────────►  │   Execra     │  ──────►  │  Task Model   │
│ Starts  │             │  Detects     │           │  Built        │
│  Task   │             │  Context     │           │  Internally   │
└─────────┘             └──────────────┘           └───────────────┘
                                                          │
    ⑧                         ⑦                          ④
┌─────────┐             ┌──────────────┐           ┌─────▼─────────┐
│ Task    │  ◄────────  │  Adapts to   │  ◄──────  │  Step-by-Step │
│Complete │             │  Progress    │           │  Guidance     │
│ ✅      │             │  Dynamically │           │  Begins       │
└─────────┘             └──────────────┘           └───────────────┘
                                │
    ⑨                          ⑤                         ⑥
┌─────────┐             ┌──────────────┐           ┌───────────────┐
│  User   │  ────────►  │  Execution   │  ──────►  │  Errors       │
│ can ask │             │  Monitored   │           │  Detected &   │
│  Text Q │             │  Continuously│           │  Consequences │
└─────────┘             └──────────────┘           │  Simulated    │
                                                   └───────────────┘
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

```
BEFORE User Presses "Run" / "Submit" / Performs Action:

┌─────────────────────────────────────────────────────┐
│            CONSEQUENCE SIMULATOR                    │
│                                                     │
│  Current State  ──►  Possible Outcomes              │
│                                                     │
│  ✅ Outcome A: Code compiles, loop exits at n=10    │
│  ⚠️  Outcome B: Off-by-one error causes overflow    │
│  ❌ Outcome C: Infinite loop if condition missing   │
│                                                     │
│  Recommendation: Adjust line 14 condition           │
│  Confidence: 91% │ Source: Runtime Trace + Rules    │
└─────────────────────────────────────────────────────┘
```

### Layer 2 — Trust & Confidence Scoring

```
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

### Layer 3 — Hybrid Interaction System

```
                    ┌─────────────────────────┐
                    │  HYBRID INTERACTION      │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
  ┌────────▼───────┐  ┌──────────▼────────┐  ┌────────▼──────┐
  │  PASSIVE MODE  │  │   ACTIVE MODE     │  │  MIXED MODE   │
  │                │  │                  │  │               │
  │ Auto-observe   │  │ User asks text   │  │ Both modes    │
  │ Auto-guide     │  │ questions        │  │ simultaneously│
  │ No prompts     │  │ Context auto-    │  │               │
  │ needed         │  │ remembered       │  │               │
  └────────────────┘  └──────────────────┘  └───────────────┘
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
cd execra

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate         # Linux/Mac
venv\Scripts\activate            # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys (OpenAI / Gemini)

# 6. Download YOLO model weights
python scripts/download_models.py

# 7. Run Execra
python main.py
```

### Quick Start (Docker)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Execra will be running at:
# API:      http://localhost:8000
# Frontend: http://localhost:3000
```

---

## 📂 Project Structure

```
execra/
│
├── 📁 core/
│   ├── perception/
│   │   ├── screen_capture.py        # Screen capture engine
│   │   ├── camera_feed.py           # Camera input handler
│   │   └── ocr_engine.py            # Text recognition (Tesseract)
│   │
│   ├── intelligence/
│   │   ├── llm_client.py            # LLM abstraction layer
│   │   ├── context_engine.py        # Session context manager
│   │   ├── consequence_sim.py       # Outcome prediction engine
│   │   └── trust_scorer.py          # Confidence scoring
│   │
│   ├── digital/
│   │   ├── code_tracer.py           # Runtime execution tracer
│   │   ├── error_detector.py        # Logical error identification
│   │   └── task_decomposer.py       # Goal → Step converter
│   │
│   ├── physical/
│   │   ├── object_detector.py       # YOLO-based detection
│   │   ├── task_recognizer.py       # Physical task classifier
│   │   └── action_validator.py      # Real-world action checker
│   │
│   └── hybrid/
│       ├── mode_manager.py          # Passive/Active mode switcher
│       ├── action_logger.py         # Undo/Recovery stack
│       └── guidance_dispatcher.py  # Instruction delivery
│
├── 📁 frontend/
│   ├── overlay/                     # Desktop overlay UI
│   ├── panel/                       # Main guidance panel
│   └── components/                  # Reusable UI components
│
├── 📁 api/
│   ├── main.py                      # FastAPI application
│   ├── routes/                      # API endpoints
│   └── websockets/                  # Real-time WebSocket handlers
│
├── 📁 models/
│   ├── yolo/                        # Object detection weights
│   └── custom/                      # Domain-specific classifiers
│
├── 📁 tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── 📁 docs/
│   ├── architecture.md
│   ├── api_reference.md
│   └── contributing_guide.md
│
├── 📁 scripts/
│   └── download_models.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── main.py
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

```
                    YOUR CONTRIBUTION JOURNEY
                    
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │  FIND   │───►│  FORK   │───►│  CODE   │───►│  PR     │
    │ an Issue│    │  Repo   │    │  & Test │    │Submitted│
    └─────────┘    └─────────┘    └─────────┘    └────┬────┘
                                                       │
                   ┌───────────────────────────────────┘
                   │
    ┌──────────────▼──┐    ┌─────────────┐    ┌──────────────┐
    │  Review Process  │───►│   Approved  │───►│  MERGED! 🎉  │
    │  (Maintainer)    │    │             │    │  Points Added│
    └──────────────────┘    └─────────────┘    └──────────────┘
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
