from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import requests


def _artifact_from_args(args: argparse.Namespace) -> dict:
    if args.text:
        return {"type": args.type or "text", "text": args.text}
    if args.url:
        return {"type": "link", "url": args.url}
    if args.image:
        raw = Path(args.image).read_bytes()
        return {"type": "image", "image_b64": base64.b64encode(raw).decode("ascii")}
    if args.file:
        path = Path(args.file)
        raw = path.read_bytes()
        return {
            "type": "document",
            "file_b64": base64.b64encode(raw).decode("ascii"),
            "file_name": path.name,
            "file_mime": args.file_mime,
        }
    raise SystemExit("Provide --text, --url, --image, or --file")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://127.0.0.1:8000")
    ap.add_argument("--investigation-id", default=None)
    ap.add_argument("--user-id", default=None)
    ap.add_argument("--channel", default="api")
    ap.add_argument("--locale", default="en_IN")
    ap.add_argument("--type", choices=["text", "context"], default=None, help="Use context for follow-up notes")
    ap.add_argument("--text", default=None)
    ap.add_argument("--url", default=None)
    ap.add_argument("--image", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--file-mime", default=None)
    ap.add_argument("--get", action="store_true", help="Fetch an existing investigation")
    args = ap.parse_args()

    base = args.host.rstrip("/")
    if args.get:
        if not args.investigation_id:
            raise SystemExit("--investigation-id is required with --get")
        response = requests.get(f"{base}/v2/investigations/{args.investigation_id}", timeout=30)
    else:
        artifact = _artifact_from_args(args)
        if args.investigation_id:
            payload = {"artifact": artifact}
            response = requests.post(
                f"{base}/v2/investigations/{args.investigation_id}/artifacts",
                json=payload,
                timeout=30,
            )
        else:
            payload = {
                "artifact": artifact,
                "user_id": args.user_id,
                "channel": args.channel,
                "locale": args.locale,
            }
            response = requests.post(f"{base}/v2/investigations/analyze", json=payload, timeout=30)

    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
