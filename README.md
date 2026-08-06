# paper trail 🧾

A local-first to-do dashboard that keeps a record of what *happened* to every
task — not just what's left. Finished tasks melt off the list; removing a task
requires a written reason; and every action lands in a timestamped, replayable
JSON ledger. At the end of a project, your summary writes itself from
evidence instead of memory.

No build step, no server, no accounts. One HTML file.

## Why

Most to-do apps only track the present. Paper Trail treats history as the
product:

- **Complete** a task → strikethrough sweeps across, the card melts off the list.
- **Cut** a task → requires a note ("traded against X", "handed to teammate",
  "no longer relevant"). Cuts are first-class citizens, not silent deletions —
  when you write your end-of-project summary, a conscious cut with a reason
  reads very differently from a miss.
- Everything lands in an **append-only event ledger** (`done`, `cut`,
  `restored`, `added`), each event timestamped and tagged with the task's
  section and category.

## Quick start

1. Clone, then open `index.html` in a browser. It runs with the demo tasks in
   `sample-data/`.
2. Copy `sample-data/tasks.sample.js` to `data/tasks.js` and edit — title,
   sections, tasks, deadline chips, category tags. `data/` is gitignored, so
   your real list stays private even in a public fork.
3. Click the **ledger pill** in the toolbar and pick where `ledger.json`
   should live (e.g. `data/ledger.json`). From then on every action
   auto-saves to disk.

## Durability model

| Layer | What it holds | Survives |
|---|---|---|
| `localStorage` | live board state | reloads, restarts |
| `ledger.json` on disk | full event history + current state snapshot | browser data wipes |
| git commits of your data dir (private fork) | everything, versioned | your laptop |

**Import ledger** replays an event log to rebuild the whole board — restoring
on a new machine is: clone, copy `data/`, import.

Auto-save uses the File System Access API (Chrome / Edge). Safari and Firefox
fall back to a one-click export; the toolbar pill tells you how many changes
are pending either way.

## Task format

```js
{
  id: "unique-slug",
  s: "section-id",
  t: "Title",
  d: "Optional detail line.",
  chips: [["red", "by Friday"], ["blue", "commitment"]],  // red | amber | blue | gray
  re: "Optional category tag",  // outlined chip; carried into ledger events
}
```

The `re` tag is meant for mapping tasks to an external framework — OKRs, a
roles-and-expectations doc, a quarter plan — so the ledger can be grouped by
that framework later.

## License

MIT
