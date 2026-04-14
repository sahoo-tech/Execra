# Changelog

All notable changes to **Execra** will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) and the [Conventional Commits](https://www.conventionalcommits.org/) specification.

> **Format:**
> - `[Added]` — New features
> - `[Changed]` — Changes in existing functionality
> - `[Deprecated]` — Features soon to be removed
> - `[Removed]` — Features that were removed
> - `[Fixed]` — Bug fixes
> - `[Security]` — Security fixes or improvements

---

## [Unreleased]

> Changes that are merged but not yet part of an official release.

### Added
- Initial project scaffold and architecture
- `README.md` with full system architecture and contributor guide
- `CONTRIBUTING.md` with step-by-step contribution workflow
- `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
- `SECURITY.md` with responsible disclosure policy
- `CHANGELOG.md` (this file)
- GitHub PR and Issue templates
- `docs/architecture.md` — deep-dive system design document
- `docs/api_reference.md` — FastAPI endpoint reference

---

## [0.1.0] — 2026-04-14

> 🎉 Initial public release — GSSoC 2026 kickoff

### Added
- Project structure with core module layout (`core/`, `api/`, `frontend/`, `tests/`)
- `core/perception/` — Screen capture, camera feed, and OCR engine scaffolds
- `core/intelligence/` — LLM client abstraction, context engine, consequence simulator, trust scorer scaffolds
- `core/digital/` — Code tracer, error detector, task decomposer scaffolds
- `core/physical/` — Object detector (YOLOv8), task recognizer, action validator scaffolds
- `core/hybrid/` — Mode manager, action logger, guidance dispatcher scaffolds
- `api/main.py` — FastAPI application entrypoint
- `docker-compose.yml` — Multi-service container setup
- `requirements.txt` — Python runtime dependencies
- `.env.example` — Environment variable template
- `scripts/download_models.py` — YOLO weight downloader

---

<!--
## [0.2.0] — YYYY-MM-DD

### Added
- 

### Changed
- 

### Fixed
- 

### Security
- 
-->

---

## 📌 Versioning Guide

```
v1.2.3
│ │ └── PATCH — Backward-compatible bug fixes
│ └──── MINOR — New backward-compatible features
└────── MAJOR — Breaking changes
```

| Version Jump | Trigger |
|-------------|---------|
| `PATCH` (0.0.X) | Bug fix, security patch, minor doc update |
| `MINOR` (0.X.0) | New feature, new module, new endpoint |
| `MAJOR` (X.0.0) | Breaking architecture change, API redesign |

---

<div align="center">

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
