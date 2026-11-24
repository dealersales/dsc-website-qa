# Faults that pass every status code check

QA findings that a fetch, a 200 and a full-page screenshot all miss. Run these
checks before signing a build off, not after a customer reports them.

## The "page goes blank for a second" flash

Symptom: scrolling down makes the whole page — or a large rectangle of it — go
blank, black or white for under a second, then settle.

It is a **paint-order race**, so it is invisible to curl, to a status code, and to
a full-page screenshot (which captures the settled state). Sampling frames out of
the customer's own screen recording usually misses it too: at 4 fps a 300 ms flash
falls between frames.

Reproduce it instead:

```bash
python3 scripts/scroll-flash-probe.py https://example.co.uk/ --step 700
```

The probe captures a frame **immediately** after each scroll step and again ~1.2 s
later, then compares mean brightness. A flash shows as a gap between the two; a
fully black frame reads 0.0, a fully white one about 242. Exit code 1 if any step
flashes, so it can gate a deploy.

### Causes, in the order worth checking

1. **An `<iframe>` with no `src` until a lazy loader fires.** A src-less iframe
   paints black at its container's height; if that height resolved against the
   viewport before layout settled, the whole screen goes black. Seen on a footer
   map: wrapper height came from `padding-bottom: 360px` while the iframe asked
   for `height: 100%`.
2. **A dark `html` canvas.** `html{background-color:hsl(0,0%,12%)}` means any
   unpainted moment reads as black. Set it to the page's own background.
3. **`background-attachment: fixed`** on a hero — forces a full-viewport repaint
   on every scroll frame.

### Fix the sizing, not the colour

Giving the iframe a light surface turns a black flash into a **white** one and
leaves the cause in place. Bind the element to its own box instead:

```css
.map { position: relative; overflow: hidden; height: 100%; min-height: 360px; padding-bottom: 0 !important; }
.map > iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
```

Re-run the probe after the fix and quote the before/after numbers — "0.0 vs 163.6
before, 182.8 vs 183.6 after" is the evidence; "it looks fine now" is not.

## Did the checker actually run?

A loop that lints every PHP file reports **every file as broken** when the
interpreter is not on `PATH` — the same output as a genuine tree-wide syntax
error. Before believing a mass failure, prove the tool ran: `command -v php`, or
lint one file you know is good. The same applies to any bulk checker (a
`pytest` that collects nothing, a `grep` against a path that does not exist).
A checker's verdict is only worth as much as the evidence it executed.

## Prove the page renders, not just that it returns 200

After deploying a template change, fetch the page and assert on the **rendered**
markup for the thing that changed — the button order, the date inside the card,
the key's absence. Two silent regressions from one session:

- a review card's markup was rewritten and the section rendered empty; the page
  still returned 200 with a full header and footer, so only a text assertion
  caught it;
- a stylesheet edit left a button with its border but a **black label on a black
  fill** — the screenshot showed an empty box. Read the computed style
  (`getComputedStyle(el).color` / `.backgroundColor`) rather than trusting the
  markup or a visual glance.

## Compose the check with the control

When a probe says something is broken, run it once against a page that certainly
works (a plain page, or the same template on another site). A control run is what
tells you whether you have found a site defect or a bug in your own harness —
without it you will "fix" a phantom and miss the real one.
