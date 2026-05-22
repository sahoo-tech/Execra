# Hardware Repair Domain

## Overview

The `HardwareEngine` analyses a single perception frame (CV detections,
hand landmarks, OCR text) and returns a `GuidanceInstruction` with
safety-critical warnings and contextual step guidance for hardware repair tasks.

---

## Component Dictionary

Raw CV detection class names are mapped to human-readable component labels:

| Detection Class  | Component Mapping          | Description                          |
|:-----------------|:---------------------------|:-------------------------------------|
| `screwdriver`    | Tool: Screwdriver          | General hand tool for fasteners.     |
| `m3_screw`       | Fastener: M3 Screw         | Common M3 hardware fastener.         |
| `heat_sink`      | Component: Heat Sink       | Cooling element for CPUs/chips.      |
| `circuit_board`  | Component: Circuit Board   | Motherboards or logic boards.        |
| `esd_strap`      | Safety: ESD Strap          | Anti-static wrist strap.             |
| `soldering_iron` | Tool: Soldering Iron       | High-heat soldering tool.            |
| `power_tool`     | Tool: Power Tool           | Drills, electric screwdrivers, etc.  |
| `safety_glasses` | Safety: Safety Glasses     | Protective eyewear.                  |

Unknown detection classes are returned as `"Unknown: <class_name>"`.

---

## Step Templates

The engine automatically selects the most relevant repair template by counting
keyword matches between detected component classes and each template's keyword list.
The winning template is returned in `GuidanceInstruction.active_template`.

| Template Name          | Trigger Keywords                                          |
|:-----------------------|:----------------------------------------------------------|
| PC assembly            | `circuit_board`, `heat_sink`, `screwdriver`, `m3_screw`  |
| circuit board repair   | `circuit_board`, `soldering_iron`, `esd_strap`           |
| appliance disassembly  | `screwdriver`, `power_tool`, `safety_glasses`            |
| cable management       | `screwdriver`                                             |

---

## Safety Rules

Rules are evaluated **independently** — all hazards present in a frame are
reported in a single combined message, separated by ` | `.

### Rule 1 — ESD Protection (CRITICAL)

**Trigger:** `circuit_board` detected and `esd_strap` not in frame.

**Message:** `CRITICAL: Circuit board detected without an ESD strap — wear an ESD strap immediately to prevent static damage.`

### Rule 2 — Soldering Iron Proximity (WARNING)

**Trigger:** `soldering_iron` detected.

- If the soldering iron bounding box centre is within **150 px** of any
  non-target component (ESD strap, screwdriver, M3 screw, heat sink,
  power tool, safety glasses), a proximity-specific warning is emitted.
- If no bounding box data is available, a generic caution message is emitted.

**Message (proximity breach):** `WARNING: Soldering iron is within 150px of '<component>' — move iron away from non-target components.`

**Message (no bbox / no breach):** `WARNING: Soldering iron active — keep it away from non-target components and wires.`

### Rule 3 — Power Tool Safety (CRITICAL)

**Trigger:** `power_tool` detected and `safety_glasses` not in frame.

**Message:** `CRITICAL: Power tool detected without safety glasses — put on safety glasses before proceeding.`

---

## Status Codes

| Status            | Meaning                                          |
|:------------------|:-------------------------------------------------|
| `OK`              | All safety checks passed; safe to proceed.       |
| `WARNING`         | Proceed with caution; hazard present but not critical. |
| `CRITICAL_WARNING`| Stop immediately; safety equipment is missing.   |

---

## OCR Integration

If `ocr_text` is non-empty, the engine attempts to extract:

- **Step numbers** — e.g. `"Step 3:"` → `"OCR detected repair step 3 in frame."`
- **Part numbers** — e.g. `"P/N: AB-5678"` → `"OCR detected part number: AB-5678."`

Extracted notes are appended as `WARNING` level messages so they appear
alongside (but never override) safety-critical guidance.

---

## GuidanceInstruction fields

| Field                | Type           | Description                                      |
|:---------------------|:---------------|:-------------------------------------------------|
| `status`             | `str`          | `"OK"`, `"WARNING"`, or `"CRITICAL_WARNING"`     |
| `message`            | `str`          | Full human-readable guidance; hazards joined by ` | ` |
| `critical_warning`   | `bool`         | `True` if any CRITICAL rule triggered            |
| `detected_components`| `List[str]`    | Deduplicated mapped component names              |
| `active_template`    | `Optional[str]`| Best-matching step template, or `None`           |