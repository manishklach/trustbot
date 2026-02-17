# TrustBot — WhatsApp Forward-Check (Risk-First)

Forward suspicious messages → get a **RISKY/UNSURE** verdict plus a minimal **“what to send next”** prompt (link, screenshot, resend-as-document, etc.).

TrustBot supports:
- **Text** (forwarded messages)
- **Links** (redirect + provenance checks)
- **Screenshots / PDFs** (text extraction; optional OCR)

---

## Design goal (risk-first)

TrustBot is optimized for real usage: people forward messages they suspect are fake/spam.

- Outputs are intentionally **RISKY/UNSURE-first**
- **SAFE is rare** (only with strong positive evidence)
- When uncertain, TrustBot asks for **one minimal extra artifact** to resolve the case

---

## Disclaimer

TrustBot is an independent research/evaluation project and is **not affiliated with, endorsed by, or sponsored by WhatsApp or Meta**.  
“WhatsApp” is used **descriptively** to indicate the intended workflow (users forwarding suspicious messages for verification).  
No warranties are provided. Use at your own risk.

---

## Quickstart (Windows PowerShell)

> If PowerShell script execution is restricted, you can run Python directly via the venv path (shown below) without activation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Service will run at:
- `http://127.0.0.1:8000`

---

## Examples

### 1) Classic OTP/KYC scam (expected: **RISKY**)

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"URGENT: Your KYC is pending. Click https://bit.ly/verify-kyc and share OTP to avoid account block." }'
```

### Sample output (Example 1)

```json
{
  "verdict": "RISKY",
  "confidence": 0.623,
  "reasons": [
    "Uses urgent/threatening language designed to rush you.",
    "Asks for an OTP — a common scam pattern.",
    "Threatens account action tied to KYC — common social-engineering tactic.",
    "Link uses a URL shortener, which often hides the true destination."
  ],
  "reason_codes": [
    "SCAM_URGENT_LANGUAGE",
    "SCAM_OTP_REQUEST",
    "SCAM_KYC_THREAT",
    "URL_SHORTENER"
  ],
  "next_step": "Do not act on this. Avoid clicking links or sharing OTP. Verify via official channels.",
  "evidence_request": null,
  "debug": {
    "risk": 0.71,
    "pipelines": [
      {
        "name": "scam_text",
        "len": 98,
        "urls": ["https://bit.ly/verify-kyc"]
      },
      {
        "name": "url_checks",
        "host": "bit.ly",
        "scheme": "https"
      },
      {
        "name": "provenance",
        "fetch": {
          "ok": true,
          "final_domain": "irs.gov",
          "status": 403,
          "chain": [
            "https://bit.ly/verify-kyc",
            "(redirected to a final domain; path redacted)"
          ],
          "content_type": "text/html"
        }
      }
    ]
  }
}
}

### 2) Suspicious shortened link (expected: **RISKY** or **UNSURE**)

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"link", "url":"http://bit.ly/otp-reset" }'
```

### 3) Neutral forward (expected: **UNSURE** → may ask for one more artifact)

```powershell
curl -X POST http://127.0.0.1:8000/v1/analyze `
  -H "Content-Type: application/json" `
  -d '{ "content_type":"text", "text":"Your bill is generated. Please pay by due date." }'
```

### 4) Screenshot / image forward (helper script)

> Tip: use the helper script for images/PDFs so you don’t have to deal with base64.

```powershell
.\.venv\Scripts\python.exe tools\demo_local.py --image .\samples\some_screenshot.png
```

### 5) PDF / document forward (optional OCR)

```powershell
.\.venv\Scripts\python.exe tools\demo_local.py --file .\samples\some_notice.pdf
```

If OCR is not installed, TrustBot will typically return **UNSURE** and request a resend-as-document or text.

---

## Interpreting results

- **RISKY**: Strong scam signals detected (OTP request, urgency, suspicious redirects, credential forms, etc.).  
  → Do not click links, do not share OTP, verify via official channels.

- **UNSURE**: Not enough evidence. TrustBot will request **one minimal extra artifact**  
  (paste the URL, resend as document, or add 1–2 lines of context).

- **SAFE (rare)**: Only used when risk is very low and evidence quality is good.  
  → Not a guarantee; still verify if money/OTP is involved.

---

## Optional: OCR support

If you want OCR for image/PDF text extraction (when normal extraction isn’t enough):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

Notes:
- You may need to install **Tesseract OCR** separately on Windows and ensure it is on PATH.
- If OCR is unavailable, TrustBot will degrade gracefully to **UNSURE**.

---

## Repository layout

- `app/` — API + scoring pipeline
- `scoring/` — heuristics and risk fusion
- `provenance/` — URL redirect + content-type checks
- `tools/` — local demo helpers (files/images)
- `samples/` — put your test screenshots/PDFs here (not required)

---

## License

MIT (see `LICENSE`).
