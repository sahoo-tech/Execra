<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=Execra%20API%20Reference&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=40&desc=FastAPI%20REST%20%26%20WebSocket%20Documentation&descAlignY=62&descAlign=50&descSize=18" width="100%" alt="API Reference Banner"/>

</div>

---

## 📑 Table of Contents

<details open>
<summary><b>Click to expand / collapse</b></summary>

- [🌐 Base URL & Versioning](#-base-url--versioning)
- [🔑 Authentication](#-authentication)
- [📡 REST Endpoints](#-rest-endpoints)
  - [System](#system-endpoints)
  - [Context](#context-endpoints)
  - [Mode](#mode-endpoints)
  - [Guidance](#guidance-endpoints)
  - [Action Log](#action-log-endpoints)
- [🔁 WebSocket API](#-websocket-api)
- [📦 Data Models](#-data-models)
- [⚠️ Error Handling](#️-error-handling)
- [📋 Response Codes](#-response-codes)
- [🧪 Testing the API](#-testing-the-api)

</details>

---

## 🌐 Base URL & Versioning

| Environment | Base URL |
|------------|---------|
| **Local Development** | `http://localhost:8000` |
| **Docker** | `http://localhost:8000` |
| **Interactive Docs (Swagger)** | `http://localhost:8000/docs` |
| **Alternative Docs (ReDoc)** | `http://localhost:8000/redoc` |

All REST endpoints are prefixed with `/api/v1/`.

**Current API Version:** `v1`

---

## 🔑 Authentication

> [!NOTE]
> In the current `v0.x` development build, authentication is **not enforced** for local use. API key support is planned for `v1.0`.

For future authenticated endpoints, include the API key in the request header:

```http
Authorization: Bearer <your_api_key>
```

---

## 📡 REST Endpoints

---

### System Endpoints

#### `GET /api/v1/status`

Returns the current health and status of the Execra system.

**Request:**
```http
GET /api/v1/status
```

**Response `200 OK`:**
```json
{
  "status": "running",
  "version": "0.1.0",
  "uptime_seconds": 3421,
  "active_domain": "digital",
  "active_mode": "passive",
  "perception_fps": 2,
  "llm_backend": "gpt-4o"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | `"running"` \| `"idle"` \| `"error"` |
| `version` | `string` | Current Execra version |
| `uptime_seconds` | `integer` | Seconds since last startup |
| `active_domain` | `string` | `"digital"` \| `"physical"` \| `"hybrid"` |
| `active_mode` | `string` | `"passive"` \| `"active"` \| `"mixed"` |
| `perception_fps` | `integer` | Current screen/camera capture rate |
| `llm_backend` | `string` | Active LLM provider |

---

#### `POST /api/v1/system/restart`

Restarts all Execra subsystems and clears the current session context.

**Request:**
```http
POST /api/v1/system/restart
Content-Type: application/json

{
  "clear_session": true
}
```

**Response `200 OK`:**
```json
{
  "message": "System restarted successfully.",
  "session_cleared": true
}
```

---

### Context Endpoints

#### `GET /api/v1/context`

Returns the current session context — task model, current step, and action history.

**Request:**
```http
GET /api/v1/context
```

**Response `200 OK`:**
```json
{
  "session_id": "sess_abc123",
  "task_type": "code_debugging",
  "current_step": 4,
  "total_steps": 9,
  "step_description": "Identify root cause of IndexError on line 42",
  "error_history": [
    {
      "step": 2,
      "error": "NameError: variable 'config' used before assignment",
      "resolved": true
    }
  ],
  "domain": "digital",
  "started_at": "2026-04-14T10:22:00Z"
}
```

---

#### `DELETE /api/v1/context`

Clears the current session context and resets Execra's task model.

**Request:**
```http
DELETE /api/v1/context
```

**Response `200 OK`:**
```json
{
  "message": "Session context cleared."
}
```

---

### Mode Endpoints

#### `GET /api/v1/mode`

Returns the current interaction mode.

**Response `200 OK`:**
```json
{
  "mode": "passive",
  "description": "Execra is observing and guiding automatically. No prompts needed."
}
```

---

#### `PUT /api/v1/mode`

Switches between interaction modes.

**Request:**
```http
PUT /api/v1/mode
Content-Type: application/json

{
  "mode": "active"
}
```

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `mode` | `string` | ✅ Yes | `"passive"` \| `"active"` \| `"mixed"` |

**Response `200 OK`:**
```json
{
  "mode": "active",
  "message": "Switched to Active Mode. You can now ask questions."
}
```

---

### Guidance Endpoints

#### `GET /api/v1/guidance/current`

Returns the most recently generated instruction from Execra.

**Response `200 OK`:**
```json
{
  "instruction": "Add a null check for `config` before accessing its keys on line 42.",
  "confidence": 0.87,
  "source": ["llm", "rule_engine", "execution_trace"],
  "reasoning": "Variable `config` returns None in 3 out of 5 traced call paths.",
  "mode": "safe",
  "step": 4,
  "total_steps": 9,
  "generated_at": "2026-04-14T10:25:31Z"
}
```

---

#### `POST /api/v1/guidance/ask`

Submits a user question (Active Mode). Execra responds using the current session context.

**Request:**
```http
POST /api/v1/guidance/ask
Content-Type: application/json

{
  "question": "Why is it showing an IndexError on line 42?"
}
```

**Response `200 OK`:**
```json
{
  "answer": "The IndexError occurs because `items` is an empty list when `config` is None. Adding a null check and a length guard before line 42 will resolve this.",
  "confidence": 0.92,
  "source": ["llm", "execution_trace"],
  "reasoning": "Traced from 3 recent function calls where `config` was None.",
  "follow_up_suggestion": "Would you like me to show the corrected code snippet?"
}
```

---

### Action Log Endpoints

#### `GET /api/v1/actions`

Returns the current session's action history.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `integer` | `20` | Max number of actions to return |
| `offset` | `integer` | `0` | Pagination offset |

**Response `200 OK`:**
```json
{
  "total": 42,
  "actions": [
    {
      "id": "act_001",
      "timestamp": "2026-04-14T10:23:10Z",
      "type": "code_edit",
      "description": "Modified line 42 in main.py",
      "domain": "digital",
      "was_guided": true,
      "guidance_confidence": 0.87
    }
  ]
}
```

---

#### `POST /api/v1/actions/undo`

Triggers an undo of the last logged action (if undoable).

**Response `200 OK`:**
```json
{
  "message": "Last action undone successfully.",
  "action_undone": {
    "id": "act_042",
    "description": "Modified line 42 in main.py"
  }
}
```

---

## 🔁 WebSocket API

The primary real-time channel for receiving guidance and sending user events.

### Connection

```
ws://localhost:8000/ws/guidance
```

### Client → Server Events

Send JSON messages to Execra over the WebSocket:

```json
{
  "event": "user_action",
  "payload": {
    "action_type": "key_press",
    "key": "Enter",
    "context": "terminal"
  }
}
```

```json
{
  "event": "ask",
  "payload": {
    "question": "What should I do next?"
  }
}
```

```json
{
  "event": "mode_switch",
  "payload": {
    "mode": "active"
  }
}
```

### Server → Client Events

Execra pushes events to the client:

```json
{
  "event": "guidance",
  "payload": {
    "instruction": "Add a null check before line 42.",
    "confidence": 0.87,
    "source": ["llm", "rule_engine", "execution_trace"],
    "reasoning": "Null config causes failure in 3 code paths.",
    "mode": "safe",
    "step": 4,
    "total_steps": 9
  }
}
```

```json
{
  "event": "error_alert",
  "payload": {
    "severity": "high",
    "message": "Infinite loop detected — missing exit condition.",
    "line": 78,
    "confidence": 0.95
  }
}
```

```json
{
  "event": "step_complete",
  "payload": {
    "step": 4,
    "next_step": "Run tests to verify the null check resolves the error."
  }
}
```

---

## 📦 Data Models

### `GuidanceInstruction`

```python
class GuidanceInstruction(BaseModel):
    instruction: str              # Human-readable guidance text
    confidence: float             # 0.0 – 1.0 trust score
    source: list[str]             # e.g., ["llm", "rule_engine"]
    reasoning: str                # Explanation for the instruction
    mode: Literal["safe", "expert"]
    step: int                     # Current step number
    total_steps: int              # Total steps in the task model
    generated_at: datetime
```

### `SessionContext`

```python
class SessionContext(BaseModel):
    session_id: str
    task_type: str                # e.g., "code_debugging", "cooking"
    current_step: int
    total_steps: int
    step_description: str
    error_history: list[ErrorRecord]
    domain: Literal["digital", "physical", "hybrid"]
    started_at: datetime
```

### `ActionRecord`

```python
class ActionRecord(BaseModel):
    id: str
    timestamp: datetime
    type: str                     # e.g., "code_edit", "key_press"
    description: str
    domain: Literal["digital", "physical"]
    was_guided: bool
    guidance_confidence: float | None
```

---

## ⚠️ Error Handling

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "CONTEXT_NOT_FOUND",
    "message": "No active session context found. Start Execra first.",
    "status": 404
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `CONTEXT_NOT_FOUND` | `404` | No active session context |
| `INVALID_MODE` | `400` | Unknown mode value provided |
| `LLM_UNAVAILABLE` | `503` | LLM backend is unreachable |
| `PERCEPTION_ERROR` | `500` | Screen/camera capture failure |
| `UNDO_UNAVAILABLE` | `409` | Nothing in the undo stack |
| `RATE_LIMITED` | `429` | Too many guidance requests |

---

## 📋 Response Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `204 No Content` | Success, no body (e.g., DELETE) |
| `400 Bad Request` | Invalid request parameters |
| `401 Unauthorized` | Missing or invalid API key |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | State conflict (e.g., undo unavailable) |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |
| `503 Service Unavailable` | LLM or external dependency is down |

---

## 🧪 Testing the API

### Using the interactive Swagger UI

Start Execra and open:
```
http://localhost:8000/docs
```

### Using `curl`

```bash
# Check system status
curl -X GET http://localhost:8000/api/v1/status

# Switch to active mode
curl -X PUT http://localhost:8000/api/v1/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "active"}'

# Ask a question in Active Mode
curl -X POST http://localhost:8000/api/v1/guidance/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is there an IndexError on line 42?"}'
```

### Using Python `requests`

```python
import requests

BASE = "http://localhost:8000/api/v1"

# Get current guidance
response = requests.get(f"{BASE}/guidance/current")
print(response.json())

# Ask a question
response = requests.post(f"{BASE}/guidance/ask", json={
    "question": "What should I do next?"
})
print(response.json())
```

### Running the Test Suite

```bash
# Run all API integration tests
python -m pytest tests/integration/ -v

# Run only API route tests
python -m pytest tests/integration/test_api_routes.py -v
```

---

<div align="center">

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
