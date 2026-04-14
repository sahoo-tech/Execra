# Security Policy

<div align="center">

[![Security](https://img.shields.io/badge/Security-Responsible%20Disclosure-red?style=for-the-badge&logo=shieldsdotio)](https://github.com/yourusername/execra/security)
&nbsp;
[![Response Time](https://img.shields.io/badge/Response%20Time-48%20Hours-blue?style=for-the-badge)](mailto:youremail@example.com)

</div>

---

## 🔐 Supported Versions

We actively maintain and apply security patches to the following versions:

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ Active — all security patches applied |
| `v1.x` (stable) | ✅ Critical security fixes only |
| `< v1.0` | ❌ No longer supported |

---

## 🚨 Reporting a Vulnerability

> [!CAUTION]
> **NEVER open a public GitHub Issue for a security vulnerability.** Doing so exposes users before a fix is available.

### How to Report

If you discover a security issue in Execra, please report it **privately and responsibly**:

**1. Email us directly:**

```
To:      youremail@example.com
Subject: [SECURITY] <Brief description of vulnerability>
```

**2. Include in your report:**

| Field | Description |
|-------|-------------|
| **Vulnerability Type** | e.g., injection, data exposure, privilege escalation |
| **Affected Component** | Which module/endpoint/file is affected |
| **Severity Estimate** | Low / Medium / High / Critical |
| **Steps to Reproduce** | Exact steps or proof-of-concept code |
| **Potential Impact** | What an attacker could gain or do |
| **Suggested Fix** | If you have one — not required |
| **Your Contact** | Name/handle (or anonymous if preferred) |

**3. Encrypt your report (optional but recommended):**

For highly sensitive reports, request our PGP key by emailing first, and we will respond with our public key.

---

## ⏱️ Response Timeline

| Stage | Timeframe |
|-------|-----------|
| **Acknowledgement** | Within 48 hours |
| **Initial assessment** | Within 5 business days |
| **Patch development** | Within 7–14 days (based on severity) |
| **Public disclosure** | After fix is released and users are protected |

---

## 🏅 Responsible Disclosure & Recognition

We deeply appreciate responsible disclosure. If you report a valid security vulnerability:

- ✅ You will receive a **personal thank-you** from the maintainers
- ✅ You will be **credited by name/handle** in our security advisory (unless anonymity is preferred)
- ✅ Your report will be acknowledged in the relevant `CHANGELOG.md` release notes

We are currently a volunteer-maintained open-source project and do not operate a formal bug bounty program. However, significant contributions to our security will be recognized prominently.

---

## 🔒 Security Best Practices for Contributors

If you are contributing code, please follow these security guidelines:

```
✅  NEVER hardcode API keys, tokens, or secrets in source code
✅  ALWAYS use environment variables via .env (see .env.example)
✅  NEVER commit .env files or model weights to the repository
✅  ALWAYS validate and sanitize external inputs (camera, screen, user text)
✅  ALWAYS use parameterized queries — never concatenate SQL strings
✅  Keep all dependencies updated (check for CVEs in requirements.txt)
✅  Avoid storing sensitive user data beyond the current session
✅  Use HTTPS for all external API calls
```

---

## 🔍 Known Security Considerations

Given Execra's nature as a **screen-capture and camera-based AI system**, we take these concerns seriously:

| Risk Area | Our Mitigation |
|-----------|---------------|
| **Screen data privacy** | All captured data is processed locally; never sent to cloud without explicit consent |
| **Camera feed privacy** | Camera access is explicitly user-initiated; no background recording |
| **LLM prompt injection** | Input sanitization layer before any data reaches the LLM |
| **API key exposure** | Keys stored in `.env` only; `.env` is in `.gitignore` |
| **Dependency vulnerabilities** | Regular `pip audit` and `npm audit` checks in CI |

---

<div align="center">

*Built with ❤️ for GirlScript Summer of Code 2026*

*Execra — Execute without boundaries.*

</div>
