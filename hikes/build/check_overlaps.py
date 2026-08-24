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
import io
import os
import pathlib
import sys

from PIL import Image

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS = ROOT / "hikes" / "maps"

MIN_AREA = 8.0      # px^2 at 1x — ignore antialiasing-scale slivers
CLIP_SLACK = 1.0    # px a glyph box may poke past its clipping column
CLEARANCE = 7.0     # px two unrelated labels must keep from each other

# --- text-over-line detection -------------------------------------------------
# Flat fills a label may legitimately sit on: the paper, the two terrain washes,
# lake water, glacier ice. Anything far from all of these is a drawn line — a
# trail, road, creek, boat route or map furniture — and a label sitting on one
# is hard to read.
BG_COLORS = [
    (0xF4, 0xF1, 0xEA),   # paper
    (0xEA, 0xE5, 0xDA),   # terrain wash
    (0xEF, 0xEB, 0xE2),   # terrain wash, lighter
    (0xCB, 0xDE, 0xE9),   # lake fill
    (0xE4, 0xEE, 0xF3),   # glacier fill
]
BG_TOLERANCE = 40     # RGB distance; antialiased blends of two fills stay under
LINE_PIXELS = 10      # line pixels inside a label box (at 2x) before it counts

MEASURE_JS = r"""
() => {
  /* ---- map: every SVG <text> as an oriented quad ---- */
  const labels = [];
  // .t-mark is a number inside a waypoint circle; it is meant to sit on it.
  for (const el of document.querySelectorAll('.map svg text:not(.t-mark)')) {
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


def crowding(a, b):
    """How close two labels sit, and whether they are a deliberate pair.

    A place name over its own detail line is set at the same anchor a dozen px
    below and is meant to read as one block. Two *unrelated* labels that drift
    that close read as one block too, which is the bug. Telling them apart is
    what the alignment test is for: a real pair shares an edge or a centre.

    Returns (gap, is_pair). gap is the larger of the two axis gaps, negative
    where the boxes overlap on that axis.
    """
    def bounds(q):
        xs = [p["x"] for p in q]
        ys = [p["y"] for p in q]
        return min(xs), max(xs), min(ys), max(ys)

    ax0, ax1, ay0, ay1 = bounds(a)
    bx0, bx1, by0, by1 = bounds(b)

    gap_x = max(bx0 - ax1, ax0 - bx1)
    gap_y = max(by0 - ay1, ay0 - by1)

    aligned = (abs(ax0 - bx0) < 3                       # same left edge
               or abs(ax1 - bx1) < 3                    # same right edge
               or abs((ax0 + ax1) - (bx0 + bx1)) < 6)   # same centre
    is_pair = aligned and 0 <= gap_y <= 10 and gap_x < 0

    return max(gap_x, gap_y), is_pair


def count_line_pixels(px, w, h, quad, scale, origin):
    """Line pixels under a label, using the map rendered with all text hidden.

    The label is tested as its true oriented quad, so a rotated label only
    samples the slanted ribbon it actually occupies.
    """
    pts = [((p["x"] - origin[0]) * scale, (p["y"] - origin[1]) * scale) for p in quad]

    def area(poly):
        s = 0.0
        for i in range(len(poly)):
            j = (i + 1) % len(poly)
            s += poly[i][0] * poly[j][1] - poly[j][0] * poly[i][1]
        return s / 2.0

    if area(pts) < 0:
        pts = pts[::-1]

    def inside(x, y):
        for i in range(4):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % 4]
            if (bx - ax) * (y - ay) - (by - ay) * (x - ax) < 0:
                return False
        return True

    x0 = max(0, int(min(p[0] for p in pts)))
    x1 = min(w - 1, int(max(p[0] for p in pts)) + 1)
    y0 = max(0, int(min(p[1] for p in pts)))
    y1 = min(h - 1, int(max(p[1] for p in pts)) + 1)

    hits = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not inside(x + 0.5, y + 0.5):
                continue
            r, g, b = px[x, y][:3]
            best = min((r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
                       for c in BG_COLORS)
            if best > BG_TOLERANCE * BG_TOLERANCE:
                hits += 1
    return hits


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

            # Re-shoot the map with every label hidden, so what remains is only
            # the drawn lines. Then look under each label's box.
            on_lines = []
            if labels:
                box = page.evaluate(
                    "() => { const m = document.querySelector('.map')"
                    ".getBoundingClientRect(); return {x: m.x, y: m.y}; }"
                )
                page.add_style_tag(content=".map svg text { visibility: hidden !important }")
                page.wait_for_timeout(80)
                shot = page.locator(".map").screenshot()
                page.reload()
                page.wait_for_timeout(150)

                im = Image.open(io.BytesIO(shot)).convert("RGB")
                px = im.load()
                scale = im.width / page.evaluate(
                    "() => document.querySelector('.map').getBoundingClientRect().width"
                )
                for lb in labels:
                    n = count_line_pixels(px, im.width, im.height, lb["quad"],
                                          scale, (box["x"], box["y"]))
                    if n >= LINE_PIXELS:
                        on_lines.append((n, lb["text"]))
                on_lines.sort(key=lambda t: -t[0])

            hits, tight = [], []
            for i in range(len(labels)):
                for j in range(i + 1, len(labels)):
                    a, b = labels[i], labels[j]
                    ar = clip_area(a["quad"], b["quad"])
                    if ar >= MIN_AREA:
                        hits.append((ar, a["text"], b["text"]))
                    elif ar == 0:
                        gap, is_pair = crowding(a["quad"], b["quad"])
                        if not is_pair and gap < CLEARANCE:
                            tight.append((gap, a["text"], b["text"]))
            hits.sort(key=lambda h: -h[0])
            tight.sort(key=lambda t: t[0])

            clip = [c for c in clipped if c["by"] > CLIP_SLACK]
            sw, sh = data["sheet"]["w"], data["sheet"]["h"]
            bad_size = abs(sw - 1056) > 1 or abs(sh - 816) > 1

            ok = (not hits and not clip and not bad_size
                  and not on_lines and not tight)
            faults += (len(hits) + len(clip) + len(on_lines) + len(tight)
                       + (1 if bad_size else 0))
            print(f"{'OK ' if ok else '!! '}{sheet.name}   "
                  f"{len(labels)} map labels, {len(clipped)} clip candidates")

            if bad_size:
                print(f"     sheet is {sw:.0f}x{sh:.0f}px, expected 1056x816")
            for ar, t1, t2 in hits:
                print(f"     overlap {ar:6.0f}px²   {t1!r}\n{'':22}x  {t2!r}")
            for c in clip:
                print(f"     clipped {c['by']:5.1f}px {c['side']:>6} of .{c['container']}"
                      f"   {c['text']!r}")
            for gap, t1, t2 in tight:
                print(f"     crowded {gap:5.1f}px gap    {t1!r}\n{'':22}~  {t2!r}")
            for n, t in on_lines:
                print(f"     on-line {n:5d}px        {t!r}")

        browser.close()

    print()
    print("clean" if faults == 0 else f"{faults} problem(s)")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
