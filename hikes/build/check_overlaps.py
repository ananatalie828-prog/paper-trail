#!/usr/bin/env python3
"""Report overlapping or clipped text on the hike sheets.

    python3 hikes/build/check_overlaps.py            # all sheets
    python3 hikes/build/check_overlaps.py day2       # just the matching one

Exits non-zero if anything is wrong, so it can gate a build.

Two different checks, because the two halves of a sheet fail differently:

* The map is absolutely-positioned SVG, so its labels can collide. Each
  <text> element is measured as a true oriented box — getBBox() corners pushed
  through getScreenCTM() — so a rotated label like "GARDEN WALL" is tested as
  the slanted ribbon it actually is, not as the much larger upright box around
  it. Overlap area comes from clipping one quad against the other.

* The left column is normal document flow, where stacked text cannot overlap;
  what it can do is overflow the fixed-height column and get cut off by
  `overflow: hidden`. So that half is checked for clipping instead.

Text crossing a trail line or a terrain wash is intentional and not reported.
"""

import glob
import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS = ROOT / "hikes" / "maps"

MIN_AREA = 8.0      # px^2 at 1x — ignore antialiasing-scale slivers
CLIP_SLACK = 1.0    # px a glyph box may poke past its clipping column

MEASURE_JS = r"""
() => {
  /* ---- map: every SVG <text> as an oriented quad ---- */
  const labels = [];
  for (const el of document.querySelectorAll('.map svg text')) {
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none') continue;
    const txt = el.textContent.replace(/\s+/g, ' ').trim();
    if (!txt) continue;

    const b = el.getBBox();
    const m = el.getScreenCTM();
    if (!m) continue;
    const pt = (x, y) => ({
      x: m.a * x + m.c * y + m.e,
      y: m.b * x + m.d * y + m.f,
    });
    labels.push({
      text: txt.length > 44 ? txt.slice(0, 44) + '…' : txt,
      quad: [pt(b.x, b.y), pt(b.x + b.width, b.y),
             pt(b.x + b.width, b.y + b.height), pt(b.x, b.y + b.height)],
      rotated: Math.abs(m.b) > 1e-6 || Math.abs(m.c) > 1e-6,
    });
  }

  /* ---- flow columns: is any text clipped by its container? ----
     Every container that clips its overflow gets checked, so a new sheet
     layout is covered as soon as its column carries one of these classes. */
  const clipped = [];
  for (const col of document.querySelectorAll('.side, .rules, .sheet')) {
    if (getComputedStyle(col).overflow !== 'hidden') continue;
    const cr = col.getBoundingClientRect();
    const walk = document.createTreeWalker(col, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walk.nextNode())) {
      if (!n.textContent.trim()) continue;
      // SVG map labels are measured as quads above; skip them here.
      if (n.parentElement && n.parentElement.closest('svg')) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) {
        if (r.width < 1 || r.height < 1) continue;
        const over = {
          bottom: r.bottom - cr.bottom,
          right: r.right - cr.right,
          left: cr.left - r.left,
          top: cr.top - r.top,
        };
        const worst = Object.entries(over).sort((a, b) => b[1] - a[1])[0];
        if (worst[1] > 0) {
          clipped.push({
            text: n.textContent.replace(/\s+/g, ' ').trim().slice(0, 44),
            side: worst[0],
            by: worst[1],
            container: col.className.split(' ')[0],
          });
        }
      }
    }
  }

  /* ---- does the sheet itself fit one page? ---- */
  const sheet = document.querySelector('.sheet').getBoundingClientRect();
  return { labels, clipped, sheet: { w: sheet.width, h: sheet.height } };
}
"""


def clip_area(subject, clipper):
    """Area of the intersection of two convex quads (Sutherland-Hodgman)."""
    def inside(p, a, b):
        return (b["x"] - a["x"]) * (p["y"] - a["y"]) - (b["y"] - a["y"]) * (p["x"] - a["x"]) >= 0

    def cross(a, b, c, d):
        x1, y1, x2, y2 = a["x"], a["y"], b["x"], b["y"]
        x3, y3, x4, y4 = c["x"], c["y"], d["x"], d["y"]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return b
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return {"x": x1 + t * (x2 - x1), "y": y1 + t * (y2 - y1)}

    # both quads must wind the same way
    def area(poly):
        s = 0.0
        for i in range(len(poly)):
            j = (i + 1) % len(poly)
            s += poly[i]["x"] * poly[j]["y"] - poly[j]["x"] * poly[i]["y"]
        return s / 2.0

    if area(clipper) < 0:
        clipper = clipper[::-1]
    out = subject[::-1] if area(subject) < 0 else list(subject)

    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        src, out = out, []
        for j in range(len(src)):
            cur, prv = src[j], src[j - 1]
            if inside(cur, a, b):
                if not inside(prv, a, b):
                    out.append(cross(prv, cur, a, b))
                out.append(cur)
            elif inside(prv, a, b):
                out.append(cross(prv, cur, a, b))
        if not out:
            return 0.0
    return abs(area(out))


def find_chrome() -> str:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/usr/bin/chromium", "/usr/bin/google-chrome"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise SystemExit("no chromium found; set CHROME=/path/to/chrome")


def main() -> int:
    filt = sys.argv[1] if len(sys.argv) > 1 else ""
    sheets = [p for p in sorted(MAPS.glob("day*.html")) if filt in p.stem]
    if not sheets:
        print("no sheets matched", file=sys.stderr)
        return 1

    faults = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=find_chrome(), args=["--no-sandbox", "--hide-scrollbars"]
        )
        page = browser.new_page(viewport={"width": 1056, "height": 816})

        for sheet in sheets:
            page.goto(sheet.as_uri())
            page.wait_for_timeout(200)
            data = page.evaluate(MEASURE_JS)
            labels, clipped = data["labels"], data["clipped"]

            hits = []
            for i in range(len(labels)):
                for j in range(i + 1, len(labels)):
                    a, b = labels[i], labels[j]
                    ar = clip_area(a["quad"], b["quad"])
                    if ar >= MIN_AREA:
                        hits.append((ar, a["text"], b["text"]))
            hits.sort(key=lambda h: -h[0])

            clip = [c for c in clipped if c["by"] > CLIP_SLACK]
            sw, sh = data["sheet"]["w"], data["sheet"]["h"]
            bad_size = abs(sw - 1056) > 1 or abs(sh - 816) > 1

            ok = not hits and not clip and not bad_size
            faults += len(hits) + len(clip) + (1 if bad_size else 0)
            print(f"{'OK ' if ok else '!! '}{sheet.name}   "
                  f"{len(labels)} map labels, {len(clipped)} clip candidates")

            if bad_size:
                print(f"     sheet is {sw:.0f}x{sh:.0f}px, expected 1056x816")
            for ar, t1, t2 in hits:
                print(f"     overlap {ar:6.0f}px²   {t1!r}\n{'':22}x  {t2!r}")
            for c in clip:
                print(f"     clipped {c['by']:5.1f}px {c['side']:>6} of .{c['container']}"
                      f"   {c['text']!r}")

        browser.close()

    print()
    print("clean" if faults == 0 else f"{faults} problem(s)")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
