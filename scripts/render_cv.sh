#!/usr/bin/env bash
# Render "Ziad Hares CV.pdf" from profile.json and keep it to two A4 pages:
# build at compact level 0, render with headless Chrome/Chromium, and if the PDF
# exceeds two pages rebuild at a tighter level (max 2). Works on macOS and the runner.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-python3}"
for c in chromium chromium-browser google-chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then CHROME="$c"; break; fi
done
[ -n "${CHROME:-}" ] || { echo "render_cv.sh: no Chrome/Chromium found" >&2; exit 1; }
OUT="$PWD/Ziad Hares CV.pdf"
for level in 0 1 2; do
  "$PY" scripts/build.py --compact=$level >/dev/null
  "$CHROME" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$OUT" "file://$PWD/cv.html" >/dev/null 2>&1
  pages=$(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/{print $2}')
  echo "compact=$level pages=${pages:-?}"
  [ "${pages:-3}" -le 2 ] && exit 0
done
echo "render_cv.sh: CV still exceeds two pages at compact=2; lower cv_max_bullets in profile.json" >&2
exit 1
