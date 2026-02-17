from __future__ import annotations

import argparse
import json
import base64
from pathlib import Path
import requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://127.0.0.1:8000")
    ap.add_argument("--text", default=None)
    ap.add_argument("--url", default=None)
    ap.add_argument("--image", default=None, help="Path to image file (jpg/png)")
    ap.add_argument("--file", default=None, help="Path to file (pdf/png/jpg)")
    args = ap.parse_args()

    if args.text:
        payload = {"content_type": "text", "text": args.text, "locale": "en_IN"}
    elif args.url:
        payload = {"content_type": "link", "url": args.url, "locale": "en_IN"}
    elif args.image:
        b = Path(args.image).read_bytes()
        payload = {"content_type": "image", "image_b64": base64.b64encode(b).decode("ascii"), "locale": "en_IN"}
    elif args.file:
        p = Path(args.file)
        b = p.read_bytes()
        payload = {"content_type": "document", "file_b64": base64.b64encode(b).decode("ascii"), "file_name": p.name, "locale": "en_IN"}
    else:
        raise SystemExit("Provide --text or --url or --image or --file")

    r = requests.post(args.host.rstrip("/") + "/v1/analyze", json=payload, timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    main()
