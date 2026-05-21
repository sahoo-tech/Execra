# Execra User Guide

Welcome! This guide is written for everyday users — no coding experience required. It will walk you through everything you need to know to install and use Execra confidently.

---

## Table of Contents

1. [What is Execra?](#1-what-is-execra)
2. [System Requirements](#2-system-requirements)
3. [Installation](#3-installation)
   - [Windows](#windows-installation)
   - [Linux](#linux-installation)
4. [Starting Execra](#4-starting-execra)
5. [Understanding the Overlay UI](#5-understanding-the-overlay-ui)
6. [How to Ask Questions in Active Mode](#6-how-to-ask-questions-in-active-mode)
7. [How to Undo an Action](#7-how-to-undo-an-action)
8. [Privacy Mode](#8-privacy-mode)
9. [FAQ](#9-faq)

---

## 1. What is Execra?

Execra is an AI assistant that watches what you are doing on your screen (or through your webcam) and gives you step-by-step guidance in real time — before you make a mistake.

Think of it like having a knowledgeable friend sitting next to you while you work. You do not need to stop and search the internet, watch tutorials, or guess what to do next. Execra watches, understands, and speaks up the moment it sees you heading in the wrong direction.

**What can Execra help with?**

- Writing or debugging code
- Navigating software you are unfamiliar with
- Filling out forms correctly
- Real-world tasks captured through your webcam (cooking, repairs, assembly)
- Preventing errors before they happen

**How is it different from a chatbot?**

A regular chatbot only responds when you ask it something. Execra runs continuously in the background, observing your actions and offering guidance automatically — no prompting needed.

---

## 2. System Requirements

Before installing Execra, check that your computer meets the following requirements.

### Windows

| Requirement | Minimum |
|---|---|
| Operating System | Windows 10 or newer |
| Python | Version 3.10 or newer |
| Node.js | Version 18 or newer |
| RAM | 8 GB recommended |
| Webcam | Optional (required for physical task guidance) |
| Internet | Required for AI features |

### Linux

| Requirement | Minimum |
|---|---|
| Operating System | Ubuntu 22.04 or newer (or equivalent) |
| Python | Version 3.10 or newer |
| Node.js | Version 18 or newer |
| RAM | 8 GB recommended |
| Webcam | Optional (required for physical task guidance) |
| Internet | Required for AI features |

### Additional Tools (Both Platforms)

- **FFmpeg** — used for processing camera video streams
- **Git** — used to download the Execra source code
- **An API key** from OpenAI (GPT-4o) or Google (Gemini) — Execra uses one of these AI services to power its intelligence

> **Note:** You need at least one AI API key to use Execra. You can get one for free (with usage limits) from [OpenAI](https://platform.openai.com/) or [Google AI Studio](https://aistudio.google.com/).

---

## 3. Installation

### Windows Installation

Follow these steps in order. Each step builds on the previous one.

**Step 1 — Install Python**

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest Python 3.10+ installer
3. Run the installer
4. **Important:** On the first screen, check the box that says **"Add Python to PATH"** before clicking Install

To confirm Python is installed, open Command Prompt and run:
```
python --version
```
You should see something like `Python 3.11.4`.

---

**Step 2 — Install Node.js**

1. Go to [https://nodejs.org/](https://nodejs.org/)
2. Download the **LTS** (Long Term Support) version
3. Run the installer with default settings

To confirm Node.js is installed:
```
node --version
```

---

**Step 3 — Install FFmpeg**

1. Go to [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Download a Windows build (e.g., from gyan.dev)
3. Extract the zip file and add the `bin` folder to your system PATH

> **Tip:** Search "how to add FFmpeg to PATH on Windows" if you are unsure how to do this step.

---

**Step 4 — Install Git**

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and run the installer with default settings

---

**Step 5 — Download Execra**

Open **Command Prompt** and run:

```
git clone https://github.com/sahoo-tech/execra.git
cd execra
```

---

**Step 6 — Create a Virtual Environment**

A virtual environment keeps Execra's dependencies separate from the rest of your computer.

```
python -m venv .venv
.venv\Scripts\activate
```

> You will see `(.venv)` appear at the start of your command line. This means the virtual environment is active.

---

**Step 7 — Install Python Dependencies**

```
pip install -r requirements.txt
```

This may take a few minutes.

---

**Step 8 — Install Frontend Dependencies**

```
cd frontend
npm install
cd ..
```

---

**Step 9 — Set Up Your Configuration File**

```
copy .env.example .env
```

Now open the `.env` file in any text editor (like Notepad) and fill in your API key:

```
LLM_BACKEND=gpt-4o
OPENAI_API_KEY=your-actual-openai-key-here
```

Or if you are using Google Gemini:

```
LLM_BACKEND=gemini
GEMINI_API_KEY=your-actual-gemini-key-here
```

Save and close the file.

---

**Step 10 — Download AI Model Files**

```
python scripts/download_models.py
```

---

**Step 11 — Start Execra**

```
python main.py
```

Execra is now running. The overlay UI will appear on your screen.

---

### Linux Installation

**Step 1 — Install System Dependencies**

Open a terminal and run:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm ffmpeg git -y
```

To confirm versions:
```bash
python3 --version
node --version
```

---

**Step 2 — Download Execra**

```bash
git clone https://github.com/sahoo-tech/execra.git
cd execra
```

---

**Step 3 — Create a Virtual Environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> You will see `(.venv)` at the start of your terminal prompt when the environment is active.

---

**Step 4 — Install Python Dependencies**

```bash
pip install -r requirements.txt
```

---

**Step 5 — Install Frontend Dependencies**

```bash
cd frontend
npm install
cd ..
```

---

**Step 6 — Set Up Your Configuration File**

```bash
cp .env.example .env
nano .env
```

Fill in your API key (use arrow keys to navigate, `Ctrl+O` to save, `Ctrl+X` to exit):

```
OPENAI_API_KEY=your-actual-openai-key-here
```

---

**Step 7 — Download AI Model Files**

```bash
python scripts/download_models.py
```

---

**Step 8 — Start Execra**

```bash
python main.py
```

---

## 4. Starting Execra

When you run `python main.py`, Execra starts up and you will be prompted to make two choices.

### Choose a Domain

A "domain" tells Execra what kind of task you are working on.

| Domain | What it does | Use it when... |
|---|---|---|
| **Digital** | Watches your screen | You are coding, using software, or filling out forms on your computer |
| **Physical** | Uses your webcam | You are doing a real-world task like cooking, repairing something, or assembling a device |

### Choose a Mode

A "mode" controls how Execra interacts with you.

| Mode | How it works |
|---|---|
| **Passive Mode** | Execra watches silently and shows guidance automatically. You do not need to ask anything. |
| **Active Mode** | Execra waits for you to type a question. It uses your current screen or camera context to answer. |
| **Mixed Mode** | Both at the same time — Execra guides you automatically AND accepts your questions. |

> **Recommended for beginners:** Start with **Mixed Mode** in the **Digital Domain** so you get automatic guidance and can also ask questions when confused.

### Grant Permissions

If prompted, allow Execra to:
- Access your screen (for Digital domain)
- Access your webcam (for Physical domain)

These permissions are required for Execra to observe your work and provide guidance.

---

## 5. Understanding the Overlay UI

Once Execra is running, a small panel appears on your screen. Here is what each part means.

---

### Main Guidance Panel

> 📸 _Screenshot placeholder — Main overlay panel showing a guidance message_

This is the main area where Execra displays its suggestions. It shows:
- What you should do next
- Warnings if it detects a potential mistake
- A brief explanation of why it is making the suggestion

---

### Confidence Indicator

> 📸 _Screenshot placeholder — Confidence bar showing 87%_

The confidence bar (shown as a percentage) tells you how certain Execra is about its suggestion.

| Confidence Level | What it means |
|---|---|
| 80% – 100% | Execra is very confident. Follow the suggestion. |
| 50% – 79% | Execra has a reasonable suggestion but recommends double-checking. |
| Below 50% | Execra is uncertain. Use your own judgment. |

---

### Mode Indicator

> 📸 _Screenshot placeholder — Mode badge showing "Passive Mode"_

A small badge in the corner shows which mode is currently active:
- **Passive** — Execra is guiding you automatically
- **Active** — Execra is waiting for your questions
- **Mixed** — Both are active

You can switch modes at any time from the overlay controls.

---

### Warning / Alert Banner

> 📸 _Screenshot placeholder — Red warning banner saying "Potential error detected"_

When Execra detects that you are about to make a mistake, a colored banner appears:
- **Yellow** — Caution, something looks unusual
- **Red** — High risk of error, stop and review before continuing

---

### Action History Button

> 📸 _Screenshot placeholder — History icon in the overlay_

Clicking this shows a list of recent actions Execra has logged. You can use this to review what happened or trigger an undo.

---

## 6. How to Ask Questions in Active Mode

In Active Mode (or Mixed Mode), you can type questions directly to Execra. It already knows what is on your screen or camera, so you do not need to explain the context.

**How to ask a question:**

1. Click the text input box in the overlay panel
2. Type your question in plain language
3. Press **Enter**

**Example questions you can ask:**

- `Why is my code not working?`
- `What should I do next?`
- `Is this the right way to do this?`
- `Explain what just happened`
- `What does this error mean?`

> **Tip:** You do not need to copy-paste your code or describe your screen. Execra already sees it. Just ask your question naturally.

Execra will respond in the overlay panel with a plain-language answer and a confidence score.

---

## 7. How to Undo an Action

Execra keeps a log of up to 50 recent actions during your session. If something went wrong, you can undo the last action.

**To undo:**

1. Look for the **Undo** button in the overlay panel (or press the keyboard shortcut shown in the UI)
2. Click it once to reverse the most recent logged action
3. You can click it multiple times to step back through recent actions

> **Important:** Undo works for actions that Execra has logged and can reverse. Not all actions (for example, saving a file externally) can be undone through Execra. When an action cannot be undone, Execra will tell you.

> **Note:** The undo stack is cleared when you close Execra or start a new session.

---

## 8. Privacy Mode

Privacy Mode protects sensitive information while Execra is running. When enabled, Execra automatically hides or blurs certain content before it is processed.

**What Privacy Mode does:**

- Automatically detects and redacts sensitive text such as email addresses, credit card numbers, and API keys
- Blacks out or blurs screen regions you have marked as private
- Prevents sensitive data from being included in AI requests

**How to enable Privacy Mode:**

1. Open the `.env` file in your Execra folder
2. Find the line:
   ```
   PRIVACY_MASKING_ENABLED=true
   ```
   Make sure it is set to `true` (it is enabled by default)
3. Save the file and restart Execra

**To mark specific screen regions as private:**

In your `.env` file, you can define rectangular areas of your screen to always be blacked out. This is useful if you have a password manager or sensitive panel visible while working.

> **Tip:** Even with Privacy Mode enabled, avoid working with highly sensitive data (like banking credentials) while Execra is running, as a general best practice.

---

## 9. FAQ

### Is my screen data sent to the cloud?

**It depends on your configuration.**

Execra uses an AI service (OpenAI GPT-4o or Google Gemini) to understand what is on your screen and generate guidance. When Execra processes a screen capture or camera frame, a description or excerpt of that content is sent to the AI service you have configured in your `.env` file.

Here is what that means in practice:

| Scenario | What gets sent to the cloud |
|---|---|
| You are using OpenAI GPT-4o | Processed screen/camera data is sent to OpenAI's servers |
| You are using Google Gemini | Processed screen/camera data is sent to Google's servers |
| Privacy Mode is ON | Sensitive patterns (emails, keys, etc.) are redacted **before** being sent |
| Privacy Mode is OFF | Raw extracted text may be included in the AI request |

**To minimize data exposure:**
1. Keep `PRIVACY_MASKING_ENABLED=true` in your `.env` file
2. Review the privacy policies of your chosen AI provider
3. Avoid using Execra while sensitive documents (passwords, financial data) are visible on screen

---

### Do I need an internet connection?

Yes, for the AI guidance features. Execra sends context to an external AI service (OpenAI or Gemini) to generate its suggestions. A stable internet connection is required.

---

### Can I use Execra without a webcam?

Yes. The webcam is only needed for the **Physical Domain** (real-world task guidance). If you are only using Execra for screen-based tasks (coding, software, forms), no webcam is needed.

---

### Execra is not starting. What should I check?

1. Make sure your virtual environment is activated (you should see `(.venv)` in your terminal)
2. Confirm your `.env` file exists and contains a valid API key
3. Make sure all dependencies installed without errors (`pip install -r requirements.txt`)
4. Check that Python 3.10+ is being used (`python --version`)

---

### How do I stop Execra?

Press `Ctrl+C` in the terminal where Execra is running, or close the terminal window.

---

### Where can I get help?

- Open a bug report: [GitHub Issues](https://github.com/sahoo-tech/execra/issues/new?template=bug_report.md)
- Start a discussion: [GitHub Discussions](https://github.com/sahoo-tech/execra/discussions)
- Email the maintainer: ss9830872697@gmail.com
