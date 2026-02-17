# TrustBot — WhatsApp Forward-Check (Risk-First)

Forward suspicious messages → get RISKY/UNSURE verdict + evidence prompts. Risk-first scam verification for forwarded messages (links, text, screenshots).

## Design goal (risk-first)
TrustBot is optimized for real usage: people forward messages they suspect are fake/spam.
So outputs are intentionally **RISKY/UNSURE-first** and **SAFE is rare** (only with strong positive evidence).

## Disclaimer
TrustBot is an independent research/evaluation project and is **not affiliated with, endorsed by, or sponsored by WhatsApp or Meta**.
“WhatsApp” is used **descriptively** to indicate the intended workflow (users forwarding suspicious messages for verification).
No warranties are provided. Use at your own risk.

## Examples (risk-first)

TrustBot is optimized for the real workflow: people forward messages they suspect are fake/spam.
So outputs are intentionally **RISKY/UNSURE-first** and **SAFE is rare**.

> Tip: Use the helper script for images/PDFs so you don’t have to deal with base64.

---

### Example 1 — Classic OTP / KYC scam (expected: **RISKY**)
```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"URGENT: Your KYC is pending. Click https://bit.ly/verify-kyc and share OTP to avoid account block." }'

**### Example 2 - Suspicious shortened link (expected: RISKY or UNSURE)**

curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"link", "url":"http://bit.ly/otp-reset" }'

**## Example 3 — Neutral forward (expected: UNSURE, may ask for one more artifact)**

curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"Your bill is generated. Please pay by due date." }'

**## Example 4 — Screenshot/image forward (expected: UNSURE → “resend as document” if low signal)**

.\.venv\Scripts\python.exe tools\demo_local.py --image .\samples\some_screenshot.png

**## Example 5 — PDF/document forward (optional OCR)**

.\.venv\Scripts\python.exe tools\demo_local.py --file .\samples\some_notice.pdf


