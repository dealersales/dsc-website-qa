# Verifying a page you cannot see moving

A QA pass that only takes screenshots of pages at rest misses the failures customers report: flashes,
widgets that never paint, buttons that are there but unreadable. These are the checks that catch them.

## Scroll flashes

Run `scripts/scroll_probe.py <url> [outdir] [WxH]`. It drives headless Chrome over CDP, captures a frame
immediately after each scroll and another once settled, and prints mean brightness for both.

- A **consistent** instant-frame dip at one offset is a defect; random dips are capture noise. Run twice.
- Always run a control URL in the same pass — the control should never dip.
- On the evidence, chase in this order: a src-less `<iframe>` (lazy map or embed) painting black at its
  container's height; a dark `html{background-color}` showing through any repaint; a
  `background-attachment: fixed` layer forcing whole-viewport repaints.
- Do not diagnose from one enormous viewport either: rendering at `--window-size=1400,6000` can make a hero
  with `height:100%` cover the document and come back entirely black — an artefact of the capture, not the bug.

## Third-party widgets

- Test in a first-visit state: clear the consent key from `localStorage`, reload, wait 30–40s. Blank means
  gated, not slow. Gated widgets need a placeholder plus an *Enable cookies* path, and the plugin usually only
  initialises from a clean load — so accepting from the placeholder should reload.
- A widget iframe that reports as loaded can still be an empty box; confirm it **paints**, ideally after
  consent, and never trust `iframe.src` alone (these plugins often keep it empty).
- Provider failures print into the DOM: endpoint URL, status code, "Failed to authenticate". A raw error on a
  live page is worse than a missing widget — have a guard that swaps that text for a phone number.

## Looks-wrong controls

When a control renders as an empty outline or invisible label, read `getComputedStyle(el)` for `color`,
`backgroundColor` and `border` before editing CSS. A theme's `.btn-primary` variables and a utility class both
set colour; the computed value names the winner immediately, and `!important` in the override is often
load-bearing rather than lazy.

## Screenshots versus text

- `vision_analyze` loads a given image **once per session**, and crops of it count as the same image. OCR the
  file first with `macos-vision-ocr` (which costs nothing and survives compression), and spend the single
  visual look on something OCR cannot answer.
- Never quote OCR'd customer words. Where review text exists in a platform export or API, that is the only
  acceptable source; where it does not, say the text is unverified rather than publishing it.
