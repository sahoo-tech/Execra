<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=Execra%20Architecture&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=40&desc=System%20Design%20%26%20Subsystem%20Guide&descAlignY=62&descAlign=50&descSize=18" width="100%" alt="Architecture Banner"/>

</div>

---

## 📑 Table of Contents

<details open>
<summary><b>Click to expand / collapse</b></summary>

- [🌐 System Overview](#-system-overview)
- [🏗️ High-Level Architecture](#️-high-level-architecture)
- [📦 Core Subsystems](#-core-subsystems)
  - [1. Perception Layer](#1-perception-layer)
  - [2. Processing Layer](#2-processing-layer)
  - [3. Intelligence Layer](#3-intelligence-layer)
  - [4. Output Layer](#4-output-layer)
- [🖥️ Digital Domain](#️-digital-domain)
- [📷 Physical Domain](#-physical-domain)
- [🔁 Hybrid Mode System](#-hybrid-mode-system)
- [🛡️ Trust & Confidence Scoring](#️-trust--confidence-scoring)
- [💾 Data Flow & Storage](#-data-flow--storage)
- [🔗 Inter-Service Communication](#-inter-service-communication)
- [🐳 Deployment Architecture](#-deployment-architecture)
- [⚡ Performance Considerations](#-performance-considerations)
- [🗺️ Future Roadmap](#️-future-roadmap)

</details>

---

## 🌐 System Overview

**Execra** is a **multimodal, real-time execution intelligence layer**. Unlike a chatbot that responds to prompts, Execra runs continuously in the background, observing a user's digital and physical actions, building an internal model of their current task, and proactively delivering guidance *before mistakes happen*.

```
Core Philosophy:
  OBSERVE → UNDERSTAND → GUIDE → CORRECT

Core Loop:
  Perception Bus → Processing Engines → Intelligence Core → Trust Scorer → Output Layer
       ↑___________________ Feedback (Action Logger) __________________________|
```

---

## 🏗️ High-Level Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         E X E C R A   SYSTEM                            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        INPUT LAYER                              │   ║
║   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │   ║
║   │   │ Screen Capture│   │  Camera Feed │   │  User Text Input │   │   ║
║   │   └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘   │   ║
║   └──────────┼──────────────────┼────────────────────┼─────────────┘   ║
║              ▼                  ▼                     ▼                  ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                      PROCESSING LAYER                           │   ║
║   │ ┌───────────────┐  ┌──────────────────┐  ┌──────────────────┐  │   ║
║   │ │  Code Runtime  │  │ Computer Vision   │  │  Context Engine  │  │   ║
║   │ │  Trace Engine  │  │ (OCR + Detection) │  │ (Task Detector)  │  │   ║
║   │ └───────┬───────┘  └────────┬─────────┘  └────────┬─────────┘  │   ║
║   └─────────┼───────────────────┼────────────────────┼─────────────┘   ║
║             ▼                   ▼                     ▼                  ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                     INTELLIGENCE LAYER                          │   ║
║   │ ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐   │   ║
║   │ │     LLM      │  │  Rule-Based       │  │  Consequence      │   │   ║
║   │ │  (Reasoning) │  │  Validator        │  │  Simulator        │   │   ║
║   │ └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘   │   ║
║   │        └───────────────────┴──────────────────────┘             │   ║
║   │                            ▼                                    │   ║
║   │              ┌─────────────────────────────┐                    │   ║
║   │              │   TRUST & CONFIDENCE SCORER  │                    │   ║
║   │              └─────────────────────────────┘                    │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                ▼                                         ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        OUTPUT LAYER                             │   ║
║   │   ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐ │   ║
║   │   │  Real-Time │  │ Error Alerts │  │  Confidence Indicators  │ │   ║
║   │   │ Instruction│  │  & Warnings  │  │  + Reasoning Display   │ │   ║
║   │   └────────────┘  └──────────────┘  └────────────────────────┘ │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 📦 Core Subsystems

### 1. Perception Layer

The entry point of all information into Execra.

| Module | File | Responsibility |
|--------|------|----------------|
| Screen Capture | `core/perception/screen_capture.py` | Continuous screen frame capture using `mss` / `PyAutoGUI` |
| Camera Feed | `core/perception/camera_feed.py` | Real-time camera input via `OpenCV` |
| OCR Engine | `core/perception/ocr_engine.py` | Extract text from frames using `Tesseract` |

```
Screen Frame ──► Delta Detection ──► Frame Queue ──► Processing Layer
Camera Frame ──► Object Detection Hook ──► Frame Queue ──► Processing Layer
User Text ───► Active Mode Handler ──► Context Engine
```

**Key Design Decisions:**
- **Frame Delta Detection**: Only frames with sufficient change are forwarded to avoid flooding the processing layer
- **Async Producer-Consumer Queue**: Perception runs in a separate thread, pushing to a bounded queue consumed by processing engines
- **Configurable FPS**: Screen capture rate is configurable (default: 2 FPS to balance responsiveness vs. CPU load)

---

### 2. Processing Layer

Transforms raw input (frames, text) into structured, meaningful signals.

| Module | File | Responsibility |
|--------|------|----------------|
| Code Tracer | `core/digital/code_tracer.py` | Hooks into Python runtime using `sys.settrace` |
| CV Engine | `core/physical/object_detector.py` | YOLOv8-based object detection and spatial analysis |
| Context Engine | `core/intelligence/context_engine.py` | Maintains the dynamic session context model |
| Task Recognizer | `core/physical/task_recognizer.py` | Classifies physical task type from visual input |

---

### 3. Intelligence Layer

The decision-making core of Execra — determines what guidance to deliver.

```
Structured Signals
       │
       ├──► LLM Client (GPT-4o / Gemini 1.5 Pro / Llama 3)
       │         └── Generates reasoning and natural language instruction
       │
       ├──► Rule-Based Validator (Drools / Python rules engine)
       │         └── Deterministic checks: schema validation, safety rules
       │
       └──► Consequence Simulator
                 └── Predicts outcomes before the user commits to an action
```

**Hybrid Reasoning:** All three sources vote on the instruction. The Trust Scorer combines their outputs into a final confidence-weighted recommendation.

---

### 4. Output Layer

Delivers instructions and alerts to the user in real time.

| Output Type | Description |
|------------|-------------|
| **Real-Time Instruction** | Step-by-step guidance shown in the overlay panel |
| **Error Alert** | Pre-emptive warning before a destructive action |
| **Confidence Indicator** | Visual confidence bar (0–100%) with source reasoning |
| **OS Notification** | Background alerts via `Plyer` when overlay is minimized |

---

## 🖥️ Digital Domain

The **Digital Domain** handles all screen-based, code-based, and software-nav scenarios.

```
┌─────────────────────────────────────────────────────────┐
│                 DIGITAL DOMAIN ENGINE                    │
│                                                         │
│  📺 Screen Capture ──► Code Parser ──► AST Analyzer     │
│                                              │           │
│                              ┌───────────────┘           │
│                              ▼                           │
│                     Runtime Trace Engine                 │
│                     (sys.settrace hook)                  │
│                              │                           │
│              ┌───────────────┼────────────────┐          │
│              ▼               ▼                 ▼          │
│       Error Detector   Task Decomposer   Context Update  │
│       (logic bugs)     (goal → steps)   (step tracker)  │
└─────────────────────────────────────────────────────────┘
```

**Supported Use Cases:**
- Live code debugging with runtime trace analysis
- Software navigation guidance (form filling, UI flows)
- API integration steps
- Terminal command guidance

---

## 📷 Physical Domain

The **Physical Domain** uses the camera to guide real-world tasks.

```
┌─────────────────────────────────────────────────────────┐
│                PHYSICAL DOMAIN ENGINE                    │
│                                                         │
│  📷 Camera Feed ──► Frame Preprocessor                  │
│                              │                           │
│              ┌───────────────┼────────────────┐          │
│              ▼               ▼                 ▼          │
│       YOLOv8 Detector   OCR Engine      Spatial Analyzer │
│       (objects/tools)   (text in scene) (positions)     │
│              │               │                 │          │
│              └───────────────▼─────────────────┘          │
│                       Task Recognizer                    │
│                    (what is the user doing?)             │
│                              │                           │
│                       Action Validator                   │
│                    (is the next step correct?)           │
└─────────────────────────────────────────────────────────┘
```

**Supported Use Cases:**
- Hardware/device repair guidance
- Cooking step-by-step assistance
- Physical form filling with OCR
- Device assembly and component identification

---

## 🔁 Hybrid Mode System

Execra supports three interaction modes, managed by `core/hybrid/mode_manager.py`:

```
                    ┌─────────────────────────┐
                    │  HYBRID MODE MANAGER     │
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

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Passive** | Default at startup | Observes actions and delivers proactive guidance |
| **Active** | User types a question | Responds to explicit user queries with full session context |
| **Mixed** | Both simultaneously | Continues passive guidance while also accepting text input |

---

## 🛡️ Trust & Confidence Scoring

Every instruction delivered by Execra carries a **Trust Score** — a composite confidence metric.

```
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

**Scoring Formula:**

```
trust_score = (
    w1 * llm_confidence +
    w2 * rule_validation_score +
    w3 * execution_trace_match
) / (w1 + w2 + w3)
```

| Component | Weight | Source |
|-----------|--------|--------|
| LLM Confidence | 0.5 | Self-reported confidence from LLM |
| Rule Validation | 0.3 | Binary pass/fail from deterministic rule engine |
| Execution Trace Match | 0.2 | Similarity to known safe execution patterns |

**Score Levels:**

| Score Range | Level | Action |
|------------|-------|--------|
| ≥ 0.85 | ✅ Trusted | Deliver instruction directly |
| 0.65 – 0.84 | ⚠️ Moderate | Deliver with visible reasoning |
| 0.50 – 0.64 | 🟡 Low | Flag uncertainty, invite user confirmation |
| < 0.50 | ❌ Uncertain | Flag + request clarification, do not auto-suggest |

---

## 💾 Data Flow & Storage

```
[Captured Frame / User Input]
         │
         ▼
[Action Logger] ──► SQLite (local session log)
         │
         ▼
[Undo Stack] ──► Redis (in-memory, hot cache for fast undo/replay)
         │
         ▼
[Long-term Session Archive] ──► S3 (cold storage, opt-in)
```

| Store | Technology | Data Kept |
|-------|-----------|-----------|
| **Session Log** | SQLite | Current session's action history and step tracker |
| **Hot Cache** | Redis | Last N actions for fast undo/replay |
| **Cold Archive** | AWS S3 *(opt-in)* | Long-term user session data (requires explicit consent) |

> **Privacy First:** No screen or camera data is ever persisted beyond the current session by default.

---

## 🔗 Inter-Service Communication

```
Frontend (Electron/Tauri)
    │
    │  REST (JSON)
    ▼
FastAPI Application (api/main.py)
    │
    ├── REST Routes (api/routes/)
    │        └── /status, /context, /mode, /action-log
    │
    └── WebSocket (api/websockets/)
             └── ws://localhost:8000/ws/guidance
                     ← real-time instruction stream
                     → user action events
```

**WebSocket Message Format:**

```json
{
  "event": "guidance",
  "payload": {
    "instruction": "Add null check before line 42",
    "confidence": 0.87,
    "source": ["llm", "rule_engine", "trace"],
    "reasoning": "Variable `config` returns None in 3 edge cases.",
    "mode": "safe",
    "step": 4,
    "total_steps": 9
  }
}
```

---

## 🐳 Deployment Architecture

```
┌──────────────────────────────────────────────┐
│              Docker Compose Stack             │
│                                              │
│  ┌──────────────┐    ┌──────────────────┐    │
│  │  execra-core │    │  execra-api      │    │
│  │  (Python)    │◄──►│  (FastAPI :8000) │    │
│  └──────────────┘    └──────────────────┘    │
│         │                    │               │
│  ┌──────▼──────────────────▼─────────────┐  │
│  │              execra-db                 │  │
│  │   SQLite (dev) / Redis (hot cache)     │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  execra-frontend (Node :3000)          │  │
│  │  Electron / Tauri overlay app          │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

---

## ⚡ Performance Considerations

| Concern | Strategy |
|---------|---------|
| **Frame rate vs. CPU** | Configurable FPS (default 2/s); delta-only processing |
| **LLM latency** | Async calls; rule engine provides instant fallback |
| **Memory (camera)** | Frame buffer with fixed max size; oldest frames dropped |
| **Startup time** | Lazy model loading; YOLO weights loaded only when physical domain activates |
| **WebSocket throughput** | Message batching for low-priority guidance updates |

---

## 🗺️ Future Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| **v0.1** | Project scaffold + architecture | ✅ Done |
| **v0.2** | Screen capture + OCR engine | 🔄 In Progress |
| **v0.3** | Digital domain (code tracer + error detector) | 📋 Planned |
| **v0.4** | LLM integration + context engine | 📋 Planned |
| **v0.5** | Trust & confidence scoring | 📋 Planned |
| **v0.6** | Physical domain (YOLOv8 + camera feed) | 📋 Planned |
| **v0.7** | Frontend overlay (Electron/Tauri) | 📋 Planned |
| **v0.8** | Consequence simulation engine | 📋 Planned |
| **v1.0** | Full system integration + stable release | 🎯 Milestone |

---

<div align="center">

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
