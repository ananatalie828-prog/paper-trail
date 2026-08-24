#!/usr/bin/env bash
# Render each hike sheet to a print-ready PDF and a preview PNG.
#
#   ./hikes/build/render.sh            # all sheets
#   ./hikes/build/render.sh day1       # just the matching one
#
# Sheets are US Letter landscape (11in x 8.5in), one page each.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MAPS="$ROOT/hikes/maps"
PDFS="$ROOT/hikes/pdf"
PNGS="$ROOT/hikes/preview"

# Chromium: prefer the Playwright-managed build, fall back to anything on PATH.
CHROME="${CHROME:-}"
if [[ -z "$CHROME" ]]; then
  for c in /opt/pw-browsers/chromium-*/chrome-linux/chrome \
           "$(command -v chromium || true)" \
           "$(command -v google-chrome || true)"; do
    [[ -n "$c" && -x "$c" ]] && { CHROME="$c"; break; }
  done
fi
[[ -n "$CHROME" ]] || { echo "no chromium found; set CHROME=/path/to/chrome" >&2; exit 1; }

FILTER="${1:-}"
mkdir -p "$PDFS" "$PNGS"

shopt -s nullglob
for html in "$MAPS"/day*.html; do
  name="$(basename "$html" .html)"
  [[ -n "$FILTER" && "$name" != *"$FILTER"* ]] && continue

  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --no-pdf-header-footer --print-to-pdf-no-header \
      --print-to-pdf="$PDFS/$name.pdf" "file://$html" 2>/dev/null

  # 2x preview for the slide deck and quick review.
  # Headless Chromium reserves some window height for chrome, so the usable
  # viewport comes back shorter than --window-size asks for. Render tall, then
  # crop down to the exact 11x8.5in sheet.
  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --force-device-scale-factor=2 --window-size=1056,940 \
      --screenshot="$PNGS/$name.png" "file://$html" 2>/dev/null

  python3 - "$PNGS/$name.png" <<'PY'
import sys
from PIL import Image
p = sys.argv[1]
im = Image.open(p).convert("RGB")
W, H = 2112, 1632          # 11in x 8.5in at 96dpi, 2x
if im.size != (W, H):
    im = im.crop((0, 0, W, H))
    im.save(p)
PY

  printf '  %-28s -> pdf/%s.pdf  preview/%s.png\n' "$name" "$name" "$name"
done

# the phone-shaped versions are generated from these same files
python3 "$ROOT/hikes/build/phone.py" "$FILTER"
