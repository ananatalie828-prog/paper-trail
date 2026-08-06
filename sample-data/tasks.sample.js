/* Sample task data. Copy this file to data/tasks.js and make it yours —
   data/ is gitignored, so your real list never leaves your machine. */
window.PAPERTRAIL = {
  title: "Paper Trail",
  subtitle: "A local-first to-do dashboard where finished tasks melt away",
  storageKey: "sample",

  sections: [
    { id: "now",   name: "This week" },
    { id: "next",  name: "Next week" },
    { id: "later", name: "Someday" },
  ],

  tasks: [
    { id: "demo-1", s: "now", t: "Check something off",
      d: "Watch it strike through, sag, and melt off the list.",
      chips: [["red", "try me"]], re: "Getting started" },
    { id: "demo-2", s: "now", t: "Cut something with a note",
      d: "Hover the card and hit ✕ — deletions require a reason, so your ledger records the why, not just the what.",
      chips: [["amber", "try me too"]], re: "Getting started" },
    { id: "demo-3", s: "now", t: "Connect a ledger file",
      d: "Click the ledger pill in the toolbar. Every action auto-saves to a JSON file on disk (Chrome/Edge), or export manually anywhere else.",
      chips: [["blue", "durability"]] },
    { id: "demo-4", s: "next", t: "Add your own tasks",
      d: "Use the input at the top, or copy this file to data/tasks.js and edit.",
      chips: [["gray", "customize"]] },
    { id: "demo-5", s: "later", t: "Restore something from the drawers",
      d: "Done and Cut items collect at the bottom — nothing is ever truly lost.",
      chips: [["gray", "safety net"]] },
  ],
};
