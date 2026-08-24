# Glacier National Park — three days of hiking 🥾

Trip materials for three hiking days in Glacier: a one-page map sheet per day
(print-ready PDF) and a slide deck that reuses the same maps.

## What's here

| File | What it is |
|---|---|
| `pdf/day1-avalanche-lake.pdf` | Day 1 sheet — Avalanche Lake |
| `pdf/day2-logan-pass.pdf` | Day 2 sheet — Highline **or** Hidden Lake |
| `pdf/day3-grinnell.pdf` | Day 3 sheet — Grinnell Glacier & Grinnell Lake |
| `pdf/day4-trail-rules.pdf` | On the trail — food, trash, bears, bathroom |
| `slides/glacier-hikes.pptx` | 6-slide deck covering all three days |
| `maps/*.html` | The sheets themselves — edit these, then re-render |
| `preview/*.png` | 2x PNG of each sheet, for quick review |

Each PDF is a single US Letter page, landscape. The three day sheets put hike
stats and the getting-there-and-back plan down the left and a schematic route
map on the right. The fourth has no map — it is a pack list plus four reference
panels, meant to be printed once and carried.

## The three days

| Date | Day | Hike | Distance | Gain | Transport |
|---|---|---|---|---|---|
| Tue 25 Aug | 1 | Avalanche Lake | 5.9 mi round trip | 757 ft | Drive both ways |
| Wed 26 Aug | 2 | **Summit group** — Highline → The Loop | 11.8 mi one way | +1,000 / −2,300 ft | Bus + shuttle, no car |
| Wed 26 Aug | 2 | **Lakes group** — Hidden Lake Overlook | 2.7 mi round trip | 550 ft | Bus + shuttle, no car |
| Thu 27 Aug | 3 | Grinnell Glacier | 11.0 mi (7.6 with boat) | 2,181 ft | Drive both ways |
| Thu 27 Aug | 3 | *plus* Grinnell Lake spur | +1.8 mi | flat | — |

The party splits on day 2: the **summit group** takes the Highline and finishes
somewhere else, the **lakes group** does Hidden Lake and comes back to Logan
Pass. Both start from the same visitor center.

`day4-trail-rules.pdf` applies to all three days — what food to carry, packing
out every scrap of trash, bear safety in grizzly country (make noise, hike as a
group of three or more, and what to do at each stage of an encounter), and how
to go to the bathroom without leaving a mess or getting caught out alone.

## ⚠️ Verify the numbers before printing

Distances, elevation gains, and times were written from general knowledge of
these trails — **they were not pulled from AllTrails or nps.gov**, because both
domains are blocked by this environment's network policy. They are in the right
ballpark and good enough to plan around, but check them against the current
AllTrails and NPS listings before anyone prints these and heads out.

Same goes for anything operational, which changes season to season:

- **the 7:30 pm last bus out of The Loop** printed on the day 2 sheet. That
  time came from the trip planner, not from a source this environment could
  reach — re-check it against the season's timetable, because if the summit
  group misses that bus there is no other way back to the car.
- current **shuttle routes and departure times** generally
- **boat schedules** at Many Glacier (day 3)
- **trail status** — snow keeps the Highline and the Grinnell traverse closed
  well into summer some years
- whether a Going-to-the-Sun Road **vehicle reservation** is required

The maps are deliberately schematic — route shape, junctions, and relative
distances, not survey geometry. Every sheet says so. Carry a real map.

The bear-safety guidance on sheet 4 follows standard NPS practice for grizzly
country, but it is a printed reminder, not training. Read the park's own bear
page before the trip, and check the trailhead board on the day.

## Rebuilding

```bash
./build/render.sh                  # all sheets -> pdf/ + preview/
./build/render.sh day2             # just the matching sheet
python3 build/check_overlaps.py    # fails on overlapping, clipped or on-line text

python3 build/crop_maps.py         # preview PNGs -> slides/img/
npm install pptxgenjs              # once
node slides/build_deck.js          # -> slides/glacier-hikes.pptx
```

`check_overlaps.py` is the guard on layout edits. It runs five checks:

- **Label vs label.** Each map `<text>` is measured as a true oriented box —
  `getBBox()` corners pushed through `getScreenCTM()` — and any two whose quads
  intersect are reported with the overlap area. A rotated label like
  `GARDEN WALL` is tested as the slanted ribbon it actually is, not the much
  larger upright box around it.
- **Label vs drawn line.** The map is re-shot with every label hidden, leaving
  only trails, roads, creeks and boat routes. Pixels under each label are then
  classified against the flat fills a label may legitimately sit on (paper,
  terrain wash, lake, glacier); anything else is a line, and enough of them
  fails the label. Numbers inside waypoint circles carry `class="t-mark"` and
  are skipped, since sitting on their marker is the point.
- **Clipping.** Flow columns can't overlap but they can overflow, so `.side`
  and `.rules` are checked for text cut off by `overflow: hidden`.
- **Page size.** The sheet must still render 1056×816px, which catches a
  regression onto a second printed page.

- **Crowding.** Two labels that stop just short of touching still read as one
  block. Any two that come within 7px are failed — unless they are a deliberate
  pair, which is detected by alignment: a place name and its detail line share
  a left edge, a right edge or a centre and sit within 10px vertically.
  Everything else has to keep its distance.

`render.sh` drives headless Chromium. It finds the Playwright-managed build
automatically; otherwise set `CHROME=/path/to/chrome`.

### Editing a sheet

Everything lives in one self-contained HTML file per day (`maps/dayN-*.html`)
plus the shared `maps/map.css`. Text and stats are in the `.side` column; the
map is inline SVG on a `0 0 765 758` viewBox. Change it, re-render, look at the
PNG.

The trail-practices sheet (`day4-trail-rules.html`) uses the same header and
left column, but swaps the map for a `.rules` grid of two text columns.

Three things to keep in mind when editing:

- Anything past the viewBox edge is clipped — keep map text roughly inside
  `x ∈ [20, 750]`.
- The sheet must stay exactly one page. `map.css` clamps `html`/`body` to the
  page box and uses `minmax(0, 1fr)` grid tracks to stop an over-tall column
  from spilling onto page two.
- Run `check_overlaps.py` after any layout change. It exits non-zero on a
  collision, a label sitting on a drawn line, a clip, or a page-size change.
