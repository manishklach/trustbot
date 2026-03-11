# TrustBot

Risk-first scam triage for forwarded messages, links, screenshots, and documents.

TrustBot started as a small heuristic API for answering a practical question:

"I got this forwarded on chat. Should I trust it?"

The project now has two layers:

- `v1`: a simple single-pass analyzer
- `v2`: an investigation-oriented API that stores artifacts, collects structured evidence, and supports multi-turn follow-up

## Why this exists

Most suspicious forwards are incomplete:

- cropped screenshots
- shortened links
- partial copied text
- messages missing sender context

That makes scam detection a poor fit for a one-shot "safe or unsafe" classifier.

TrustBot is intentionally opinionated:

- it is risk-first
- it treats "safe" as rare
- it prefers asking for one precise follow-up artifact over bluffing confidence

## Current product shape

### V1

`/v1/analyze` routes a single artifact through heuristic pipelines and returns:

- `RISKY`
- `UNSURE`
- `SAFE` (rare)

This is the original MVP surface.

### V2

`/v2/investigations/*` treats analysis as an investigation:

- create or continue a case
- store artifacts
- collect evidence from providers
- aggregate weighted evidence
- return `RISKY`, `NEED_MORE`, or `LIKELY_SAFE`

This is the new direction for the project.

## What TrustBot analyzes

- text forwards
- links
- screenshots/images
- PDFs and image-like documents
- small context notes added by the user in V2

## How TrustBot thinks

TrustBot is designed around a few product rules:

1. Strong scam signals should dominate weak neutral signals.
2. `LIKELY_SAFE` should require positive evidence, not merely absence of red flags.
3. If confidence is low, the response should request one next-best artifact.
4. User-facing explanations should be plain-language and operational.

## Features

### V1 capabilities

- scam-text pattern matching for urgency, OTP, KYC, payment, and callback lures
- URL static checks for shorteners, IP literals, no TLS, punycode, and suspicious TLDs
- URL provenance checks via redirect following and shallow landing-page inspection
- image quality heuristics for compression and low-signal screenshots
- document text extraction and optional OCR-backed text analysis

### V2 capabilities

- first-class investigations
- first-class artifacts
- structured evidence items
- weighted decision engine
- multi-turn artifact continuation
- heuristic impersonation checks
- heuristic domain reputation hints
- SQLite-backed persistence for local development

## Disclaimer

TrustBot is an independent research/evaluation project and is not affiliated with, endorsed by, or sponsored by WhatsApp or Meta.

"WhatsApp" is used descriptively to indicate the intended workflow of forwarding suspicious content for verification.

No warranties are provided. Use at your own risk.

## Quickstart

### Requirements

- Python 3.10+
- Windows PowerShell examples are shown below, but the app is plain Python/FastAPI

### Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Server:

- `http://127.0.0.1:8000`

Docs:

- `http://127.0.0.1:8000/docs`

## Optional OCR support

If you want OCR for screenshots or documents when plain extraction is insufficient:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

Notes:

- you may need to install Tesseract OCR separately
- if OCR is unavailable, TrustBot degrades toward uncertainty rather than pretending confidence

## API overview

### V1 endpoint

- `POST /v1/analyze`

### V2 endpoints

- `POST /v2/investigations/analyze`
- `GET /v2/investigations/{investigation_id}`
- `POST /v2/investigations/{investigation_id}/artifacts`

## V1 request examples

### Text scam example

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"URGENT: Your KYC is pending. Click https://bit.ly/verify-kyc and share OTP to avoid account block." }'
```

### Link example

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"link", "url":"http://bit.ly/otp-reset" }'
```

### Neutral text example

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"Your bill is generated. Please pay by due date." }'
```

### Local helper for image or document input

```powershell
.\.venv\Scripts\python.exe tools\demo_local.py --image .\samples\some_screenshot.png
.\.venv\Scripts\python.exe tools\demo_local.py --file .\samples\some_notice.pdf
```

### V2 local helper

Start an investigation:

```powershell
.\.venv\Scripts\python.exe tools\demo_v2.py --text "URGENT: Your KYC is pending. Click https://bit.ly/verify-kyc and share OTP now."
```

Continue an investigation:

```powershell
.\.venv\Scripts\python.exe tools\demo_v2.py --investigation-id inv_123 --type context --text "This came from a forwarded group and claims to be from my bank."
```

Fetch an investigation:

```powershell
.\.venv\Scripts\python.exe tools\demo_v2.py --investigation-id inv_123 --get
```

## V2 request examples

### Start an investigation from text

```powershell
curl -X POST http://127.0.0.1:8000/v2/investigations/analyze `
  -H "Content-Type: application/json" `
  -d '{ "artifact": { "type":"text", "text":"URGENT: Your KYC is pending. Share OTP now." }, "locale":"en_IN", "channel":"whatsapp" }'
```

Example response:

```json
{
  "investigation_id": "inv_123",
  "status": "RESOLVED",
  "verdict": "RISKY",
  "confidence": 0.63,
  "headline": "This looks like a likely OTP scam.",
  "reasons": [
    "Asks for an OTP — a common scam pattern.",
    "Uses urgent/threatening language designed to rush you."
  ],
  "recommended_action": "Do not click links, share OTPs, send money, or call numbers from the message. Verify through an official channel you open yourself.",
  "next_best_artifact": null,
  "artifacts_seen": 1,
  "trace": {
    "risk_score": 0.775,
    "trust_score": 0.0,
    "quality_penalty": 0.0,
    "coverage_score": 0.25,
    "contradiction_score": 0.0
  }
}
```

### Continue an investigation with another artifact

```powershell
curl -X POST http://127.0.0.1:8000/v2/investigations/inv_123/artifacts `
  -H "Content-Type: application/json" `
  -d '{ "artifact": { "type":"context", "text":"This came from a forwarded family group and claims to be from my bank." } }'
```

### Fetch a case

```powershell
curl http://127.0.0.1:8000/v2/investigations/inv_123
```

## Response semantics

### V1 verdicts

- `RISKY`: strong scam signals found
- `UNSURE`: not enough evidence
- `SAFE`: low-risk with better-than-neutral evidence, but still not a guarantee

### V2 verdicts

- `RISKY`: strong risk evidence exists
- `NEED_MORE`: current artifacts are insufficient or low quality
- `LIKELY_SAFE`: positive evidence supports legitimacy, with low contradiction

## Architecture

### V1 architecture

V1 is intentionally small:

- route request by content type
- run relevant pipelines
- fuse heuristic signals
- return verdict and next step

Core files:

- `app/main.py`
- `app/router.py`
- `app/fusion.py`
- `app/evidence.py`
- `app/pipelines/`

### V2 architecture

V2 separates concerns more explicitly:

- `app/api/` for FastAPI routes
- `app/domain/` for models, enums, and decisioning
- `app/providers/` for evidence collectors
- `app/services/` for orchestration
- `app/repositories/` for persistence
- `app/schemas/` for request/response models

The full V2 design rationale is documented in:

- `V2_ARCHITECTURE.md`

## Repository layout

```text
app/
  api/            # v2 routes
  domain/         # v2 enums, models, decision engine
  pipelines/      # v1 heuristic analyzers reused by v2 providers
  providers/      # v2 evidence collectors
  repositories/   # SQLite-backed local persistence for v2
  schemas/        # v2 API request/response models
  services/       # v2 orchestration services
  evidence.py     # v1 evidence-request logic
  fusion.py       # v1 signal fusion
  main.py         # FastAPI app entrypoint
  models.py       # v1 request/response models
  router.py       # v1 routing/orchestration
  storage.py      # v1 ephemeral storage helpers
tools/
  demo_local.py   # helper script for local image/document analysis
  demo_v2.py      # helper script for creating/continuing v2 investigations
samples/          # sample inputs
V2_ARCHITECTURE.md
README.md
```

## Local persistence in V2

V2 uses SQLite by default for local development.

- default DB path: `trustbot_v2.db`
- override with: `TRUSTBOT_DB_PATH`

Example:

```powershell
$env:TRUSTBOT_DB_PATH = "data\trustbot_v2.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Known limitations

- V1 and current V2 are still heuristic-first, not evaluation-calibrated
- V2 domain reputation is intentionally lightweight today
- impersonation detection is rule-based, not model-backed
- V2 does not yet auto-promote URLs extracted from text into linked child artifacts
- OCR quality depends on the environment and Tesseract availability
- there is not yet a formal benchmark dataset committed in-repo

## Suggested next steps

- add URL extraction into linked V2 artifacts
- add a regression/evaluation harness with labeled cases
- strengthen impersonation and brand/domain consistency checks
- improve response composition for richer plain-language explanations
- add a simple UI or CLI flow for multi-turn investigations

## License

MIT
