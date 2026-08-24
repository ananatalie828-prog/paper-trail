# Glacier National Park — three days of hiking 🥾

Trip materials for three hiking days in Glacier: a one-page map sheet per day
(print-ready PDF) and a slide deck that reuses the same maps.

## What's here

| File | What it is |
|---|---|
| `pdf/day1-avalanche-lake.pdf` | Day 1 sheet — Avalanche Lake |
| `pdf/day2-logan-pass.pdf` | Day 2 sheet — Highline Trail **or** Hidden Lake Overlook |
| `pdf/day3-grinnell.pdf` | Day 3 sheet — Grinnell Glacier & Grinnell Lake |
| `slides/glacier-hikes.pptx` | 6-slide deck covering all three days |
| `maps/*.html` | The sheets themselves — edit these, then re-render |
| `preview/*.png` | 2x PNG of each sheet, for quick review |

Each PDF is a single US Letter page, landscape: hike stats and the
getting-there-and-back plan down the left, a hand-drawn-style route map on the
right.

## The three days

| Day | Hike | Distance | Gain | Transport |
|---|---|---|---|---|
| 1 | Avalanche Lake | 5.9 mi round trip | 757 ft | Drive both ways |
| 2 | Highline Trail → The Loop | 11.8 mi one way | +1,000 / −2,300 ft | Bus + shuttle, no car |
| 2 | *or* Hidden Lake Overlook | 2.7 mi round trip | 550 ft | Bus + shuttle, no car |
| 3 | Grinnell Glacier | 11.0 mi (7.6 with boat) | 2,181 ft | Drive both ways |
| 3 | *plus* Grinnell Lake spur | +1.8 mi | flat | — |

Day 2 is the one that needs planning: the Highline is point-to-point and
finishes at The Loop, so it only works if you catch the last westbound shuttle.

## ⚠️ Verify the numbers before printing

Distances, elevation gains, and times were written from general knowledge of
these trails — **they were not pulled from AllTrails or nps.gov**, because both
domains are blocked by this environment's network policy. They are in the right
ballpark and good enough to plan around, but check them against the current
AllTrails and NPS listings before anyone prints these and heads out.

Same goes for anything operational, which changes season to season:

- whether a Going-to-the-Sun Road **vehicle reservation** is required
- current **shuttle routes and last-departure times** (Day 2 depends on this)
- **boat schedules and ticket availability** at Many Glacier (Day 3)
- **trail status** — snow keeps the Highline and the Grinnell traverse closed
  well into summer some years

The maps are deliberately schematic — route shape, junctions, and relative
distances, not survey geometry. Every sheet says so. Carry a real map.

## Rebuilding

```bash
./build/render.sh              # all sheets -> pdf/ + preview/
./build/render.sh day2         # just the matching sheet

python3 build/crop_maps.py     # preview PNGs -> slides/img/
npm install pptxgenjs          # once
node slides/build_deck.js      # -> slides/glacier-hikes.pptx
```

`render.sh` drives headless Chromium. It finds the Playwright-managed build
automatically; otherwise set `CHROME=/path/to/chrome`.

### Editing a sheet

Everything lives in one self-contained HTML file per day (`maps/dayN-*.html`)
plus the shared `maps/map.css`. Text and stats are in the `.side` column; the
map is inline SVG on a `0 0 765 758` viewBox. Change it, re-render, look at the
PNG.

Two things to keep in mind when moving map labels:

- Anything past the viewBox edge is clipped — keep text roughly inside
  `x ∈ [20, 750]`.
- The sheet must stay exactly one page. `map.css` clamps `html`/`body` to the
  page box and uses `minmax(0, 1fr)` grid tracks to stop an over-tall column
  from spilling onto page two. `render.sh` prints nothing if that breaks, so
  check the page count if you change the layout.
