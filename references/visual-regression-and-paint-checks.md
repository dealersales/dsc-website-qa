# Proving a paint or timing bug

"The page goes blank for a second", "the button is invisible", "it flashes when I scroll" all pass a 200
check and a screenshot taken at rest. They are timing and paint states, so measure them.

## Measure, do not look

`scripts/scroll_probe.py` walks a page: for each scroll offset it captures a frame **immediately** after
`scrollTo` and again ~1.2s later, then prints the mean brightness of both. A frame far from its settled
partner is the flash the user described.

- **Read `window.scrollY` back after every scroll.** A failed scroll leaves the page at 0, and every frame is
  then a clean capture of a page that never moved — a false pass that looks exactly like a fix.
- **Run it on every page carrying the suspect component.** A shared footer is on all of them; one clean page
  does not clear the rest.
- **A mean near 0, or near 240, across the whole frame is a full-viewport layer** — an element sized to the
  viewport, not a local glitch. Look for `height:100%` and padding-derived heights before a missing image.
- **Always probe a control page** (`example.com`) first. A probe that returns black for a plain page is a
  broken probe, and blaming the site for it wastes an afternoon.
- **Two colours, one bug.** If lifting a flash from black to light leaves the same delta at the same offset,
  the layer is still there: the cause is the element's geometry, not its background.

## Full-page capture

Headless Chrome CLI with a tall viewport, cropped afterwards:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --hide-scrollbars --window-size=1400,6000 --virtual-time-budget=20000 \
  --screenshot=/tmp/page.png <url>
```

Then check `Image.getextrema()`: a pure `(0, 0)` result means nothing painted at all. **A very tall viewport
can trigger layout a real visitor never sees** — a page that renders at 900, 1500 and 3000 but goes black at
6000 is telling you something has `height:100%` resolving against the viewport. Confirm that with the scroll
probe at a normal viewport before reporting it as a site fault.

## Style changes: read the computed style back

A screenshot shows a border exists; it does not show the label behind it went black-on-black. After any
class or CSS change, read the computed values back over CDP — `getComputedStyle(el)` for `color`,
`backgroundColor`, `boxShadow`, `borderTopWidth` — and for `:hover`, dispatch a real mouse move
(`Input.dispatchMouseEvent`, type `mouseMoved`, at the element's centre) and read again.

Compare the changed element against the one it is meant to match, field by field. That is the difference
between "the border is there" and "it is the same button".

Bootstrap-derived themes fight their own utilities: `.btn{border:none}` against `.border`, `--bs-btn-*`
variables overriding `color`, equal-specificity rules resolving by source order. "I added the class" is not
"it took effect". Where an element should match another, **give it the same class** rather than
reimplementing the effect, then delete the bespoke rule — two sources of truth for one button is how it goes
invisible again after the next change.

## When the interactive browser stalls

The browser harness has short IPC timeouts. Heavy pages (finance widgets, maps, long lists) can exceed them on
scroll or JS evaluation, and a timed-out `scrollTo` leaves the page at offset 0 while the next call still
reports success. For scroll position and paint timing, drive Chrome directly over CDP (the script above) and
confirm the interpreter can `import websocket` — one python on the machine may have it and another not.

## Reading tall report screenshots

`vision_analyze` loads each image **once per session**, and crops of the same file count as the same image. For
a tall dashboard or audit export, OCR it with the macOS Vision framework (`macos-vision-ocr`) or crop to
separate files on disk with PIL and load each as its own image. Never re-request a screenshot already supplied.
