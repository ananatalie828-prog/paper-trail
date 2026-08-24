#!/usr/bin/env python3
"""Crop the map panel out of each rendered sheet, for use in the slide deck.

Each sheet is 11x8.5in with a 3.35in info column on the left and a 0.92in
header on top; the deck reprints that information in its own type, so the
slides use only the map panel.

    python3 hikes/build/crop_maps.py
"""

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "hikes" / "preview"
MAPS = ROOT / "hikes" / "maps"
DST = ROOT / "hikes" / "slides" / "img"

DPI = 96
SCALE = 2          # preview PNGs are rendered at 2x
SIDE_IN = 3.35     # width of the sheet's left info column
HEAD_IN = 0.92     # height of the sheet's header band


def main() -> int:
    sheets = sorted(SRC.glob("day*.png"))
    if not sheets:
        print(f"no sheets in {SRC} — run hikes/build/render.sh first", file=sys.stderr)
        return 1

    DST.mkdir(parents=True, exist_ok=True)
    left, top = round(SIDE_IN * DPI * SCALE), round(HEAD_IN * DPI * SCALE)

    for src in sheets:
        # Not every sheet has a map — the trail-practices sheet is two columns
        # of text, so there is nothing to crop out of it.
        html = MAPS / f"{src.stem}.html"
        if not html.exists() or 'class="map"' not in html.read_text():
            print(f"  {src.name:32s} -- no map panel, skipped")
            continue

        im = Image.open(src)
        crop = im.crop((left, top, im.width, im.height))
        out = DST / f"{src.stem}-map.png"
        crop.save(out, optimize=True)
        print(f"  {src.name:32s} -> {out.relative_to(ROOT)}  {crop.width}x{crop.height}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
