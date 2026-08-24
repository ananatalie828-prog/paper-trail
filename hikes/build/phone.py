#!/usr/bin/env python3
"""Build phone-shaped sheets from the Letter ones.

    python3 hikes/build/phone.py           # all sheets
    python3 hikes/build/phone.py day2      # just the matching one

The Letter sheets are 11x8.5in landscape, which on a phone is a postage stamp
you have to pinch and pan. These are 4in wide and as tall as the content needs,
so a phone viewer fits the width and you scroll — one column, big type.

Nothing is re-authored. The header, the left column and the map SVG are lifted
straight out of the Letter file and re-flowed by phone.css, so there is still
one place to edit any of it. The map keeps its geometry but drops its furniture
(peaks, legend, scale bar, north arrow) and all its small labels, which cannot
survive being scaled to a quarter of the width; what is left is the route, the
numbered stops and one anchoring lake name.

Page height is measured from the rendered content rather than guessed, so a
sheet can never be cut off at the bottom.
"""

import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS = ROOT / "hikes" / "maps"
OUT_HTML = ROOT / "hikes" / "build" / "phone"
OUT_PDF = ROOT / "hikes" / "pdf" / "phone"
OUT_PNG = ROOT / "hikes" / "preview" / "phone"

PAGE_W_IN = 4.0
PAD_IN = 0.12          # breathing room below the last element


def block(html: str, opening: str) -> str:
    """Inner HTML of the first <div> matching `opening`, brace-matched."""
    start = html.index(opening)
    i = start + len(opening)
    depth = 1
    while depth:
        m = re.compile(r"</?div\b").search(html, i)
        if not m:
            raise ValueError(f"unbalanced div after {opening!r}")
        depth += 1 if m.group() == "<div" else -1
        i = m.end()
    return html[start + len(opening):i - len("</div>")]


def grab(pattern: str, html: str, default: str = "") -> str:
    m = re.search(pattern, html, re.S)
    return m.group(1).strip() if m else default


# Union bbox of everything the map still draws, ignoring the background rect
# and the flat terrain washes (which run to the edge of the Letter viewBox and
# are happy to be cropped).
CROP_JS = r"""
() => {
  const svg = document.querySelector('.pmap svg');
  if (!svg) return null;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const el of svg.querySelectorAll('path[stroke], ellipse, circle, text, line')) {
    if (!el.getClientRects().length) continue;          // hidden
    let b;
    try { b = el.getBBox(); } catch (e) { continue; }
    if (!b.width && !b.height) continue;
    x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y);
    x1 = Math.max(x1, b.x + b.width); y1 = Math.max(y1, b.y + b.height);
  }
  if (!isFinite(x0)) return null;
  const pad = 26;
  x0 = Math.max(0, x0 - pad); y0 = Math.max(0, y0 - pad);
  x1 = Math.min(765, x1 + pad); y1 = Math.min(758, y1 + pad);
  return `${Math.round(x0)} ${Math.round(y0)} ${Math.round(x1 - x0)} ${Math.round(y1 - y0)}`;
}
"""

PIN_CLASS = {"S": "ink", "E": "ink", "○": "hollow", "◆": "alt"}
PIN_TEXT = {"●": "", "○": "", "◆": ""}


def stops_list(svg: str) -> str:
    """Turn the map's tagged waypoint labels into a readable list.

    Each stop is tagged on the map itself, so the list can never drift out of
    step with the pins: the name is the tagged <text>, the detail is the
    <text> that follows it.
    """
    rows = []
    for m in re.finditer(r'<text\b[^>]*data-stop="([^"]+)"[^>]*>(.*?)</text>', svg, re.S):
        pin, name = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        nxt = re.search(r"<text\b[^>]*>(.*?)</text>", svg[m.end():], re.S)
        detail = ""
        if nxt and "data-stop" not in svg[m.end():m.end() + nxt.start()]:
            detail = re.sub(r"\s+", " ", nxt.group(1)).strip()
        cls = PIN_CLASS.get(pin, "")
        glyph = PIN_TEXT.get(pin, pin)
        rows.append((pin,
            f'<li><span class="pin {cls}">{glyph}</span>'
            f'<span><b>{name}</b>'
            + (f'<span class="det"> — {detail}</span>' if detail else "")
            + "</span></li>"
        ))
    if not rows:
        return ""
    # Numbered stops go in walking order, not the order they happen to be
    # written in the SVG. Lettered/symbol pins keep their document order.
    if all(p.isdigit() for p, _ in rows):
        rows.sort(key=lambda r: int(r[0]))
    return ('<div class="blk"><h2>Stops On The Map</h2>'
            '<ul class="stops">' + "".join(html for _, html in rows) + "</ul></div>")


def build_page(src: pathlib.Path) -> str:
    html = src.read_text()

    day = grab(r'<span class="day">(.*?)</span>', html)
    when = grab(r'<span class="when">(.*?)</span>', html)
    title = grab(r"<h1>(.*?)</h1>", html)
    sub = grab(r'<div class="sub">(.*?)</div>', html)
    loc = re.sub(r"<br\s*/?>", " · ", sub).strip()

    side = block(html, '<div class="side">')
    svg = grab(r"(<svg\b.*?</svg>)", html)
    rules = block(html, '<div class="rules">') if 'class="rules"' in html else ""

    parts = [
        '<!doctype html>', '<meta charset="utf-8">',
        f"<title>{re.sub(r'<[^>]+>', '', title)} — phone</title>",
        '<link rel="stylesheet" href="../../maps/map.css">',
        '<link rel="stylesheet" href="../../maps/phone.css">',
        '<style id="pagesize">@page { size: 4in 40in; margin: 0; }</style>',
        '<div class="psheet">',
        '  <div class="phd">',
        f'    <div class="chips"><span class="day">{day}</span>'
        + (f'<span class="when">{when}</span>' if when else "") + '</div>',
        f"    <h1>{title}</h1>",
        f'    <div class="loc">{loc}</div>',
        '  </div>',
    ]
    if svg:
        parts += ['  <div class="map pmap">', svg, "  </div>"]
    parts += ['  <div class="pbody">']
    if svg:
        parts.append(stops_list(svg))
    parts.append(side)
    if rules:
        parts += ['<div class="rules">', rules, "</div>"]
    parts += ["  </div>", "</div>"]
    return "\n".join(parts)


def main() -> int:
    filt = sys.argv[1] if len(sys.argv) > 1 else ""
    sheets = [p for p in sorted(MAPS.glob("day*.html")) if filt in p.stem]
    if not sheets:
        print("no sheets matched", file=sys.stderr)
        return 1

    for d in (OUT_HTML, OUT_PDF, OUT_PNG):
        d.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=str(next(pathlib.Path("/opt/pw-browsers").glob(
                "chromium-*/chrome-linux/chrome"))),
            args=["--no-sandbox", "--hide-scrollbars"],
        )
        page = browser.new_page(viewport={"width": 384, "height": 1200})

        for sheet in sheets:
            out = OUT_HTML / f"{sheet.stem}.html"
            out.write_text(build_page(sheet))

            # Crop the map to what it actually draws. The Letter viewBox leaves
            # room for labels and furniture that the phone sheet hides, so
            # without this the route floats in a third of the width.
            page.goto(out.as_uri())
            page.wait_for_timeout(220)
            vb = page.evaluate(CROP_JS)
            if vb:
                html_txt = out.read_text()
                html_txt = html_txt.replace('viewBox="0 0 765 758"',
                                            f'viewBox="{vb}"', 1)
                out.write_text(html_txt)

            # measure, then set the page box to the content
            page.goto(out.as_uri())
            page.wait_for_timeout(220)
            h_px = page.evaluate(
                "() => Math.ceil(document.querySelector('.psheet')"
                ".getBoundingClientRect().height)"
            )
            h_in = round(h_px / 96 + PAD_IN, 2)
            out.write_text(out.read_text().replace(
                "@page { size: 4in 40in; margin: 0; }",
                f"@page {{ size: {PAGE_W_IN}in {h_in}in; margin: 0; }}"))

            page.goto(out.as_uri())
            page.wait_for_timeout(220)
            page.pdf(path=str(OUT_PDF / f"{sheet.stem}.pdf"),
                     width=f"{PAGE_W_IN}in", height=f"{h_in}in",
                     print_background=True, margin={"top": "0", "bottom": "0",
                                                    "left": "0", "right": "0"})
            page.set_viewport_size({"width": 384, "height": min(h_px, 4000)})
            page.screenshot(path=str(OUT_PNG / f"{sheet.stem}.png"), full_page=True)

            print(f"  {sheet.stem:28s} -> 4 x {h_in}in"
                  f"   pdf/phone/{sheet.stem}.pdf")

        browser.close()
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
