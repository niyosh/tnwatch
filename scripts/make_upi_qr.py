"""Draws the UPI QR code for the Support card from the UPI ID in js/config.js.

Run when the site is published (needs: pip install qrcode). With no UPI ID set, nothing is drawn and the
page hides the Support card. The code holds the same payment link as the "Pay with a UPI app" button.

    python scripts/make_upi_qr.py [output.svg]
"""

import os
import re
import sys
import urllib.parse

import qrcode
import qrcode.image.svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPI_ID = re.compile(r"^[\w.-]{2,256}@[a-z][a-z0-9]{1,63}$", re.I)  # same check as js/app.js


def setting(text, name):
    m = re.search(rf'\b{name}\s*:\s*"([^"]*)"', text)
    return m.group(1).strip() if m else ""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "upi-qr.svg")
    config = open(os.path.join(ROOT, "js", "config.js"), encoding="utf-8").read()
    upi, name = setting(config, "upiId"), setting(config, "upiName") or "Tamil Nadu Watch"
    if not upi:
        print("No UPI ID in js/config.js: no QR code drawn")
        return
    if not UPI_ID.match(upi):
        sys.exit(f"js/config.js: {upi!r} doesn't look like a UPI ID (name@bank)")
    q = lambda v: urllib.parse.quote(v, safe="@")  # noqa: E731 — UPI apps read "@" as is
    link = f"upi://pay?pa={q(upi)}&pn={q(name)}&cu=INR&tn={q('Support Tamil Nadu Watch')}"
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2,
                         image_factory=qrcode.image.svg.SvgPathImage)
    code.add_data(link)
    code.make(fit=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    code.make_image().save(out)
    print(f"UPI QR code for {upi} written to {out}")


if __name__ == "__main__":
    main()
