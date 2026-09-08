"""Signed simulated-Twilio webhook probe for the inbound Function URL (P-05+)."""

import base64
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

URL = "https://qrqpu64krttrdqmumjl7dpv2du0dxrkk.lambda-url.us-east-1.on.aws/"


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()
    to_number = os.environ["TWILIO_NUMBER_B"].strip()
    from_number = sys.argv[1] if len(sys.argv) > 1 else "+1555010003"
    body = sys.argv[2] if len(sys.argv) > 2 else "Mom is confused and the lights keep flickering"
    params = {"To": to_number, "From": from_number, "Body": body}
    token = os.environ["TWILIO_AUTH_TOKEN"]
    sig = base64.b64encode(hmac.new(
        token.encode(), (URL + "".join(k + v for k, v in sorted(params.items()))).encode(),
        hashlib.sha1).digest()).decode()
    req = urllib.request.Request(
        URL, data=urllib.parse.urlencode(params).encode(),
        headers={"X-Twilio-Signature": sig,
                 "Host": "qrqpu64krttrdqmumjl7dpv2du0dxrkk.lambda-url.us-east-1.on.aws"})
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        print(f"http={resp.status} body=" + resp.read().decode()[:400])
    except urllib.error.HTTPError as exc:
        print(f"http={exc.code} body=" + exc.read().decode()[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
