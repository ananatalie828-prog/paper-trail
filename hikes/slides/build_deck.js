// Builds the Glacier National Park three-day hiking deck.
//
//   node hikes/slides/build_deck.js
//
// Expects the cropped map panels in hikes/slides/img/ (produced by
// hikes/build/render.sh followed by hikes/build/crop_maps.py).

const path = require("path");
const PptxGenJS = require("pptxgenjs");

const HERE = __dirname;
const IMG = (n) => path.join(HERE, "img", n);

/* ---------------------------------------------------------------- palette */

const INK = "22201D";
const INK_2 = "2E2B27";
const PAPER = "F4F1EA";
const PAPER_2 = "E9E4D9";
const CORAL = "E2574C";
const TEAL = "2E7D8A";
const BLUE = "3D6EA5";
const MOSS = "6E7B52";
const MUTED = "6B665E";
const FAINT = "9A948A";
const PAPER_DIM = "A9A296";

const SANS = "Arial";
const W = 13.333;
const H = 7.5;

/* ------------------------------------------------------------------- data */

const DAYS = [
  {
    n: "1",
    title: "Avalanche Lake",
    date: "TUE · AUG 25",
    where: "Lake McDonald Valley",
    kicker: "ONE TRAIL · OUT & BACK",
    img: "day1-avalanche-lake-map.png",
    blurb:
      "An easy grade the whole way, up Avalanche Gorge through old cedar to a lake " +
      "with waterfalls coming off the headwall behind it.",
    stats: [
      ["5.9", "mi", "Round trip"],
      ["757", "ft", "Gain"],
      ["3–4", "hr", "Moving"],
    ],
    note: "Stopping at the foot of the lake makes it 4.6 mi.",
    legs: [
      ["D", MOSS, "Drive", "to Avalanche Creek on Going-to-the-Sun Road."],
      ["H", CORAL, "Hike", "out and back. The car stays at the trailhead."],
      ["D", MOSS, "Drive", "back the way you came."],
    ],
  },
  {
    n: "2",
    title: "Summit Group & Lakes Group",
    date: "WED · AUG 26",
    where: "Logan Pass",
    kicker: "TWO GROUPS · BOTH START AT LOGAN PASS",
    img: "day2-logan-pass-map.png",
    options: [
      {
        tag: "SUMMIT GROUP",
        color: CORAL,
        name: "Highline → The Loop",
        stats: [
          ["11.8", "mi", "One way"],
          ["2,300", "ft", "Down"],
          ["6–8", "hr", "Moving"],
        ],
      },
      {
        tag: "LAKES GROUP",
        color: TEAL,
        name: "Hidden Lake Overlook",
        stats: [
          ["2.7", "mi", "Round trip"],
          ["550", "ft", "Gain"],
          ["1½–2", "hr", "Moving"],
        ],
      },
    ],
    legs: [
      ["P", MOSS, "Park at Apgar", ". The car stays there all day."],
      ["B", BLUE, "Bus from Apgar", ", transferring at Avalanche Creek."],
      ["B", BLUE, "Shuttle to Logan Pass", " — both groups start here and split."],
      ["B", BLUE, "Shuttle back", " — summit at The Loop, lakes at Logan Pass."],
    ],
  },
  {
    n: "3",
    title: "Grinnell Glacier & Grinnell Lake",
    date: "THU · AUG 27",
    where: "Many Glacier",
    kicker: "OUT & BACK · TURN AROUND ANY TIME",
    img: "day3-grinnell-map.png",
    blurb:
      "Climbs the wall above Lake Josephine and ends at Upper Grinnell Lake, below " +
      "the glacier. Good views most of the way up, so anyone can stop early and " +
      "head back.",
    stats: [
      ["11.0", "mi", "On foot"],
      ["7.6", "mi", "With boat"],
      ["2,181", "ft", "Gain"],
    ],
    note: "The Grinnell Lake spur adds 1.8 mi round trip and is flat.",
    legs: [
      ["D", MOSS, "Drive", "to Many Glacier and park by the hotel."],
      ["H", CORAL, "Hike", "out and back as far as the group wants."],
      ["~", BLUE, "Boat", " (optional) saves 1.7 mi each way."],
    ],
  },
];

/* -------------------------------------------------------------- utilities */

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.author = "Glacier trip planning";
pres.title = "Glacier National Park — Three Days of Hiking";

// Small filled circle carrying a letter or number. The deck's one motif.
function badge(slide, x, y, d, fill, label, labelColor, fontSize) {
  slide.addShape(pres.ShapeType.ellipse, {
    x, y, w: d, h: d, fill: { color: fill },
  });
  slide.addText(label, {
    x, y, w: d, h: d,
    align: "center", valign: "middle", margin: 0,
    fontFace: SANS, fontSize: fontSize || 11, bold: true,
    color: labelColor || "FFFFFF",
  });
}

// Big number + unit with a small uppercase label beneath.
function stat(slide, x, y, w, value, unit, label, color, valueSize) {
  slide.addText(
    [
      { text: value, options: { fontSize: valueSize || 24, bold: true, color } },
      { text: " " + unit, options: { fontSize: (valueSize || 24) * 0.46, bold: true, color } },
    ],
    { x, y, w, h: 0.38, margin: 0, fontFace: SANS, valign: "bottom" }
  );
  slide.addText(label.toUpperCase(), {
    x, y: y + 0.38, w, h: 0.2, margin: 0,
    fontFace: SANS, fontSize: 8.5, color: FAINT, charSpacing: 1.2, valign: "top",
  });
}

/* --------------------------------------------------------- 1 · title slide */

function titleSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };

  s.addText("GLACIER NATIONAL PARK", {
    x: 0.85, y: 1.15, w: 8, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 13, bold: true, color: CORAL, charSpacing: 3.4,
  });

  s.addText("Three Days,\nThree Trails", {
    x: 0.82, y: 1.62, w: 8.4, h: 2.3, margin: 0,
    fontFace: SANS, fontSize: 54, bold: true, color: PAPER, lineSpacing: 60,
  });

  s.addText(
    "Tuesday 25 to Thursday 27 August  ·  Avalanche Lake, Logan Pass, Many Glacier",
    {
      x: 0.85, y: 4.05, w: 9.6, h: 0.4, margin: 0,
      fontFace: SANS, fontSize: 15, color: PAPER_DIM,
    }
  );

  // three day chips along the bottom
  const cw = 3.55, gap = 0.42;
  DAYS.forEach((d, i) => {
    const x = 0.85 + i * (cw + gap);
    const y = 5.05;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cw, h: 1.42, rectRadius: 0.06, fill: { color: INK_2 },
    });
    badge(s, x + 0.26, y + 0.28, 0.34, CORAL, d.n, "FFFFFF", 12);
    s.addText("DAY " + d.n, {
      x: x + 0.7, y: y + 0.27, w: cw - 0.95, h: 0.24, margin: 0,
      fontFace: SANS, fontSize: 9.5, bold: true, color: FAINT, charSpacing: 2.2,
      valign: "middle",
    });
    s.addText(d.title, {
      x: x + 0.26, y: y + 0.68, w: cw - 0.5, h: 0.6, margin: 0,
      fontFace: SANS, fontSize: 13.5, bold: true, color: PAPER, valign: "top",
    });
  });

  s.addNotes(
    "Three hiking days in Glacier. Day 2 splits into two groups and is the only day " +
    "that depends on the shuttle."
  );
  return s;
}

/* ------------------------------------------------------ 2 · at-a-glance grid */

function overviewSlide() {
  const s = pres.addSlide();
  s.background = { color: PAPER };

  s.addText("The three days", {
    x: 0.6, y: 0.5, w: 8, h: 0.6, margin: 0,
    fontFace: SANS, fontSize: 38, bold: true, color: INK,
  });
  s.addText("Distances are round trip unless noted.", {
    x: 0.62, y: 1.14, w: 8, h: 0.3, margin: 0,
    fontFace: SANS, fontSize: 12.5, color: MUTED,
  });

  const cards = [
    {
      n: "1", name: "Avalanche Lake", sub: "Tuesday 25 · Lake McDonald Valley",
      rows: [["5.9 mi", "757 ft"], ["3–4 hr", "out & back"]],
      move: "Drive there and back.", moveColor: MOSS,
      body: "Stop at the foot of the lake, or keep going along the shore to the head for another 0.65 mi each way.",
    },
    {
      n: "2", name: "Summit & Lakes groups", sub: "Wednesday 26 · Logan Pass",
      rows: [["11.8 mi", "summit group"], ["2.7 mi", "lakes group"]],
      move: "Bus and shuttle, no car.", moveColor: BLUE,
      body: "The summit group finishes at The Loop rather than back at Logan Pass, so the shuttle has to line up.",
    },
    {
      n: "3", name: "Grinnell Glacier", sub: "Thursday 27 · Many Glacier",
      rows: [["11.0 mi", "2,181 ft"], ["7.6 mi", "with boat"]],
      move: "Drive there, drive back.", moveColor: MOSS,
      body: "Out and back, so anyone can turn around at a viewpoint. Grinnell Lake adds a flat 1.8 mi.",
    },
  ];

  const cw = 3.84, gap = 0.4, y = 1.78, ch = 5.1;
  cards.forEach((c, i) => {
    const x = 0.6 + i * (cw + gap);
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cw, h: ch, rectRadius: 0.05, fill: { color: PAPER_2 },
    });

    badge(s, x + 0.32, y + 0.34, 0.4, CORAL, c.n, "FFFFFF", 13);
    s.addText("DAY " + c.n, {
      x: x + 0.84, y: y + 0.34, w: cw - 1.1, h: 0.4, margin: 0,
      fontFace: SANS, fontSize: 9.5, bold: true, color: FAINT, charSpacing: 2.2,
      valign: "middle",
    });

    s.addText(c.name, {
      x: x + 0.32, y: y + 0.9, w: cw - 0.64, h: 0.6, margin: 0,
      fontFace: SANS, fontSize: 18, bold: true, color: INK, valign: "top",
    });
    s.addText(c.sub, {
      x: x + 0.32, y: y + 1.48, w: cw - 0.64, h: 0.26, margin: 0,
      fontFace: SANS, fontSize: 11, color: MUTED,
    });

    c.rows.forEach((r, ri) => {
      const ry = y + 2.0 + ri * 0.46;
      s.addText(r[0], {
        x: x + 0.32, y: ry, w: 1.5, h: 0.36, margin: 0,
        fontFace: SANS, fontSize: 16, bold: true, color: INK, valign: "middle",
      });
      s.addText(r[1], {
        x: x + 1.84, y: ry, w: cw - 2.16, h: 0.36, margin: 0,
        fontFace: SANS, fontSize: 11, color: MUTED, valign: "middle",
      });
    });

    s.addText(c.body, {
      x: x + 0.32, y: y + 3.06, w: cw - 0.64, h: 1.1, margin: 0,
      fontFace: SANS, fontSize: 11.5, color: MUTED, lineSpacing: 15, valign: "top",
    });

    badge(s, x + 0.32, y + 4.42, 0.26, c.moveColor, "→", "FFFFFF", 9);
    s.addText(c.move, {
      x: x + 0.68, y: y + 4.38, w: cw - 0.98, h: 0.34, margin: 0,
      fontFace: SANS, fontSize: 11.5, bold: true, color: INK, valign: "middle",
    });
  });

  s.addNotes("Day 2 is the one to plan around, because it depends on shuttle timing.");
  return s;
}

/* ------------------------------------------------------------ 3–5 · day slides */

function daySlide(d) {
  const s = pres.addSlide();
  s.background = { color: PAPER };

  // map panel on the right, square-ish
  const mh = 6.3, mw = mh * 1.01;
  s.addImage({ path: IMG(d.img), x: W - 0.55 - mw, y: (H - mh) / 2, w: mw, h: mh });

  const x = 0.6, tw = 5.4;

  badge(s, x, 0.62, 0.42, CORAL, d.n, "FFFFFF", 14);
  s.addText("DAY " + d.n + "  ·  " + d.date + "  ·  " + d.where.toUpperCase(), {
    x: x + 0.56, y: 0.62, w: tw - 0.56, h: 0.42, margin: 0,
    fontFace: SANS, fontSize: 10.5, bold: true, color: FAINT, charSpacing: 2.2,
    valign: "middle",
  });

  s.addText(d.title, {
    x, y: 1.22, w: tw, h: 1.02, margin: 0,
    fontFace: SANS, fontSize: 28, bold: true, color: INK, lineSpacing: 33, valign: "top",
  });

  s.addText(d.kicker, {
    x, y: 2.32, w: tw, h: 0.26, margin: 0,
    fontFace: SANS, fontSize: 9.5, bold: true, color: CORAL, charSpacing: 1.8,
  });

  let cursor = 2.74;

  if (d.options) {
    // two-option day: a compact block per option
    d.options.forEach((o) => {
      s.addText(o.tag, {
        x, y: cursor, w: tw, h: 0.22, margin: 0,
        fontFace: SANS, fontSize: 9, bold: true, color: o.color, charSpacing: 1.6,
      });
      s.addText(o.name, {
        x, y: cursor + 0.19, w: tw, h: 0.32, margin: 0,
        fontFace: SANS, fontSize: 15.5, bold: true, color: INK, valign: "middle",
      });
      o.stats.forEach((st, i) => {
        stat(s, x + i * 1.62, cursor + 0.56, 1.55, st[0], st[1], st[2], INK, 19);
      });
      cursor += 1.26;
    });
  } else {
    d.stats.forEach((st, i) => {
      stat(s, x + i * 1.72, cursor, 1.65, st[0], st[1], st[2], INK, 25);
    });
    cursor += 0.9;
    s.addText(d.blurb, {
      x, y: cursor, w: tw, h: 0.95, margin: 0,
      fontFace: SANS, fontSize: 12, color: MUTED, lineSpacing: 16, valign: "top",
    });
    cursor += 1.02;
    s.addText(d.note, {
      x, y: cursor, w: tw, h: 0.3, margin: 0,
      fontFace: SANS, fontSize: 11, italic: true, color: FAINT,
    });
  }

  // Getting there & back is pinned to the same baseline on every day slide, so a
  // title that wraps to two lines can never push the legs off the bottom.
  const GETTING_Y = 5.55;
  s.addText("GETTING THERE & BACK", {
    x, y: GETTING_Y, w: tw, h: 0.26, margin: 0,
    fontFace: SANS, fontSize: 9, bold: true, color: FAINT, charSpacing: 2,
  });

  let ly = GETTING_Y + 0.32;
  d.legs.forEach((lg) => {
    badge(s, x + 0.02, ly + 0.03, 0.24, lg[1], lg[0], "FFFFFF", 8.5);
    s.addText(
      [
        { text: lg[2], options: { bold: true, color: INK } },
        // A continuation that opens with punctuation joins straight onto the
        // bold lead-in; anything else needs a space first.
        { text: /^[,.;:!?—]|^\s/.test(lg[3]) ? lg[3] : " " + lg[3],
          options: { color: MUTED } },
      ],
      {
        x: x + 0.36, y: ly, w: tw - 0.36, h: 0.32, margin: 0,
        fontFace: SANS, fontSize: 11.5, valign: "middle",
      }
    );
    ly += 0.34;
  });

  s.addNotes(d.title + " — " + d.kicker.toLowerCase() + ".");
  return s;
}

/* -------------------------------------------------------- 6 · logistics slide */

function logisticsSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };

  s.addText("How we get to each one", {
    x: 0.7, y: 0.62, w: 10, h: 0.66, margin: 0,
    fontFace: SANS, fontSize: 36, bold: true, color: PAPER,
  });
  s.addText(
    "Two driving days and one that runs entirely on the park shuttle.",
    {
      x: 0.72, y: 1.3, w: 10, h: 0.32, margin: 0,
      fontFace: SANS, fontSize: 13, color: PAPER_DIM,
    }
  );

  const rows = [
    {
      n: "1", name: "Avalanche Lake",
      chain: [["Drive", MOSS], ["Hike out & back", CORAL], ["Drive", MOSS]],
      note: "The car sits at the Avalanche Creek lot all day. Nothing to catch and nothing to book.",
    },
    {
      n: "2", name: "Summit & lakes groups",
      chain: [
        ["Park at Apgar", MOSS], ["Bus", BLUE], ["Shuttle to Logan Pass", BLUE],
        ["Hike", CORAL], ["Shuttle back", BLUE],
      ],
      note: "Transfer at Avalanche both directions. We should be long gone by then, but the summit group has to be down at The Loop before the last westbound bus.",
    },
    {
      n: "3", name: "Grinnell Glacier",
      chain: [["Drive", MOSS], ["Hike out & back", CORAL], ["Drive", MOSS]],
      note: "An optional boat across Swiftcurrent and Josephine saves 1.7 mi each way, in either direction or both.",
    },
  ];

  let y = 1.95;
  rows.forEach((r) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: 0.7, y, w: W - 1.4, h: 1.56, rectRadius: 0.05, fill: { color: INK_2 },
    });

    badge(s, 1.0, y + 0.3, 0.38, CORAL, r.n, "FFFFFF", 13);
    s.addText(r.name, {
      x: 1.5, y: y + 0.26, w: 3.5, h: 0.46, margin: 0,
      fontFace: SANS, fontSize: 16, bold: true, color: PAPER, valign: "middle",
    });

    // transport chain as small pills
    let cx = 5.1;
    r.chain.forEach((step, i) => {
      const label = step[0];
      const pw = 0.26 + label.length * 0.088;
      s.addShape(pres.ShapeType.roundRect, {
        x: cx, y: y + 0.3, w: pw, h: 0.38, rectRadius: 0.19,
        fill: { color: step[1] },
      });
      s.addText(label, {
        x: cx, y: y + 0.3, w: pw, h: 0.38, margin: 0,
        align: "center", valign: "middle",
        fontFace: SANS, fontSize: 10, bold: true, color: "FFFFFF",
      });
      cx += pw;
      if (i < r.chain.length - 1) {
        s.addText("›", {
          x: cx, y: y + 0.3, w: 0.24, h: 0.38, margin: 0,
          align: "center", valign: "middle",
          fontFace: SANS, fontSize: 13, bold: true, color: FAINT,
        });
        cx += 0.24;
      }
    });

    s.addText(r.note, {
      x: 1.5, y: y + 0.82, w: W - 2.4, h: 0.56, margin: 0,
      fontFace: SANS, fontSize: 11.5, color: PAPER_DIM, lineSpacing: 15, valign: "top",
    });

    y += 1.72;
  });

  s.addNotes(
    "Day 2 is the only day the car is left behind, and it depends on the last " +
    "westbound shuttle from The Loop."
  );
  return s;
}

/* ------------------------------------------------------------------- build */

titleSlide();
overviewSlide();
DAYS.forEach(daySlide);
logisticsSlide();

const out = path.join(HERE, "glacier-hikes.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
