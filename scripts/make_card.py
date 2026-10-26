"""Draw data/card.png: the preview image shown when the site is shared on WhatsApp, X or Facebook.

Run after fetch_data.py:  python scripts/make_card.py   (needs Pillow: pip install pillow)
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
W, H = 1200, 630
NAVY, WHITE, BLUE, GREY = (11, 20, 38), (255, 255, 255), (74, 163, 255), (184, 194, 214)
RED, AMBER, TEAL = (224, 51, 74), (245, 179, 1), (32, 183, 176)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT_FILES = {
    True: ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    False: ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"],
}


def font(size, bold=False):
    for path in FONT_FILES[bold]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def main():
    with open(os.path.join(DATA, "auto.json"), encoding="utf-8") as f:
        d = json.load(f)
    crime30 = sum(r["count"] for r in d["crime"]["periods"]["month"])
    corr30 = sum(r["count"] for r in d["corruption"]["periods"]["month"])
    last24 = sum(h["crime"] for h in d.get("hourly", []))
    stamp = d.get("lastSuccess") or d["generatedAt"]  # e.g. 2026-10-26T14:17+05:30
    y, m, day = (int(x) for x in stamp[:10].split("-"))
    updated = f"Updated {day} {MONTHS[m - 1]} {y}, {stamp[11:16]} IST"

    img = Image.new("RGB", (W, H), NAVY)
    g = ImageDraw.Draw(img)
    for row in range(H):  # dusk gradient towards the bottom, like the site's hero
        k = max(0.0, (row - 330) / 300)
        g.line([(0, row), (W, row)], fill=(int(11 + 90 * k), int(20 + 45 * k), int(38 + 30 * k)))

    # temple logo (same shape as the site's)
    s, ox, oy = 2.0, 60, 44
    g.polygon([(ox + 24 * s, oy + 2 * s), (ox + 26 * s, oy + 6 * s), (ox + 22 * s, oy + 6 * s)], fill=WHITE)
    for x1, y1, x2, y2 in [(18, 8, 30, 13), (15, 15, 33, 21), (12, 23, 36, 30), (9, 32, 39, 40), (5, 42, 43, 54)]:
        g.rectangle([ox + x1 * s, oy + y1 * s, ox + x2 * s, oy + y2 * s], fill=WHITE)
    g.rectangle([ox + 20 * s, oy + 46 * s, ox + 28 * s, oy + 54 * s], fill=NAVY)
    g.text((170, 50), "TAMIL NADU", font=font(46, True), fill=WHITE)
    g.text((170 + g.textlength("TAMIL NADU ", font=font(46, True)), 50), "WATCH", font=font(46, True), fill=BLUE)
    g.text((172, 112), updated, font=font(24), fill=GREY)

    # three headline numbers
    blocks = [(f"{crime30:,}", "crime news reports", "last 30 days", RED),
              (f"{last24:,}", "crime news reports", "last 24 hours", TEAL),
              (f"{corr30:,}", "corruption reports", "last 30 days", AMBER)]
    for i, (value, label, period, colour) in enumerate(blocks):
        x = 60 + i * 370
        g.rounded_rectangle([x, 182, x + 340, 352], radius=16, fill=(20, 32, 58))
        g.rectangle([x, 182, x + 8, 352], fill=colour)
        g.text((x + 30, 196), value, font=font(64, True), fill=WHITE)
        g.text((x + 30, 278), label, font=font(24, True), fill=WHITE)
        g.text((x + 30, 312), period, font=font(22), fill=GREY)

    # 30-day bars of crime reports
    daily = d["crime"].get("daily", [])
    top = max([p["count"] for p in daily] + [1])
    bw = (W - 120) / max(len(daily), 1)
    for i, p in enumerate(daily):
        h = 150 * p["count"] / top
        colour = (120, 40, 58) if p.get("partial") else RED
        g.rectangle([60 + i * bw + 3, 540 - h, 60 + (i + 1) * bw - 3, 540], fill=colour)
    g.text((60, 556), "Crime news reports per day, last 30 days. News reports from public feeds, not official police data.",
           font=font(20), fill=GREY)
    g.text((60, 588), "niyosh.github.io/tnwatch", font=font(22, True), fill=BLUE)

    img.save(os.path.join(DATA, "card.png"), optimize=True)
    print(f"Wrote data/card.png ({updated})")


if __name__ == "__main__":
    main()
