# Paint and render defects: blank flashes, invisible controls, wrong-looking buttons

For findings that are not content and not server-side: the page looks wrong on screen, or flashes,
while the HTML and status codes are all correct. These are the ones that survive a curl-based audit.

## Measure, do not eyeball

A screenshot proves what a control looked like for one frame, not what it resolved to. Read the computed
style before claiming a styling fix:

```python
cmd("Runtime.evaluate", expression="""(()=>[...document.querySelectorAll('a.btn')].map(a=>{
  const s=getComputedStyle(a);
  return [a.textContent.trim(), s.color, s.backgroundColor, s.boxShadow, s.borderTopWidth].join(' | ');
}))()""", returnByValue=True)
```

**A control can look "present" in a screenshot and be unusable.** A button carrying a white ring and a
`color: rgb(18,18,18)` label on a near-black section reads as an empty outlined box: the markup is right,
the class is right, the picture looks like a bordered button. Only the computed colour tells you the label
is invisible.

## Matching one control to another: share the class, do not copy the look

When asked to make button B match button A's border or hover, give B the **same class** A uses. Do not
hand-roll an equivalent rule.

- Theme component variables (`.btn-primary`, `.btn-outline-light`) beat a custom utility class on `color`
  and `background`, so a bespoke `.btn-outline-white` silently loses the cascade to whichever component
  class is still on the element.
- Two definitions for one control drift the moment either is touched; that is how the black-on-black state
  appeared in the first place.
- Verify by hovering each control with real input events (`Input.dispatchMouseEvent`, `type="mouseMoved"`)
  and comparing computed `background-color` and `box-shadow` on both. Identical values, not "looks the same".

If a bespoke rule is genuinely needed, `!important` on colour/background is load-bearing, not laziness —
`.btn { color: inherit }` and the colour utilities both compete.

## "The page goes blank / black for a second while scrolling"

Reproduce it and measure it; do not reason from the stylesheet alone. Run `scripts/scroll_probe.py <url>`:
for each scroll position it captures a frame immediately after the scroll and another 1.2s later, and prints
mean brightness for both. A real flash shows as a large **instant vs settled** delta at one specific
position, reproducibly, and never on a control page.

What the numbers mean:

- `instant 0.0`, settled normal → a full-viewport black frame. Something is painting the whole screen.
- `instant ~242`, settled normal → a full-viewport *light* frame. Same defect, different paint.
- instant and settled within a few points → clean at that position; keep scrolling, the fault is elsewhere.

### The usual cause: an element resolving to viewport size before layout settles

An iframe asking for `height: 100%` inside a wrapper whose height comes from `padding-bottom` has no
resolved parent height on first paint. That 100% falls back to the viewport, so the iframe paints a
full-screen rectangle until the provider answers.

```css
.map { position: relative; overflow: hidden; height: 100%; min-height: 360px; padding-bottom: 0 !important; }
.map > iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; background: #f0f3f5; }
```

Bind the child to its parent's box and give the parent an explicit height. That bounds the placeholder to
the space it actually occupies.

### Contributing factors worth fixing at the same time

- **An iframe with no `src` yet paints black**, and a lazyloaded iframe sits in that state until its loader
  fires. Give lazy iframes a light surface so the hole reads as a placeholder, not a void.
- **A dark page canvas turns every unpainted moment into a black flash.** `html { background-color:
  hsl(0,0%,12%) }` is common in these template kits; set it to the body's own colour so an unpainted frame
  is invisible rather than dramatic.
- **`background-attachment: fixed` on a hero** forces a whole-viewport repaint on every scroll frame.
  Dropping it costs a mild parallax nobody asked for and removes a repaint class.
- Do not put both the JS lazy loader **and** the native `loading="lazy"` attribute on the same iframe; the
  one that no longer has a `src` to work with leaves it blank for longer.

### The trap: fixing the colour is not fixing the cause

Changing a black flash to a white flash by lightening the placeholder leaves the *full-screen* paint in
place — the defect is the size, not the shade. Re-run the probe after the colour fix; if the instant frame
is still far from settled, the sizing is still wrong. Say so rather than reporting it fixed.

## Third-party integration includes

A template can ship **more than one** integration file, each carrying its own credential — a calculator
include and a separate application-form include, for example. Fixing the key in the one you found first
leaves the other returning 401 to real customers.

- Grep every include matching the provider's name before declaring the key correct.
- Compare credentials **by hash**, never by value, and prefer comparing against the live site's own working
  copy on the server over comparing against a template default: `sha256(key)[:16]` on both sides answers
  "is this the right key" without a secret entering the transcript.
- When the provider answers 401, their library often prints the raw API error into the page. Add a guard that
  swaps recognisable error text (`Status Code`, `Failed to authenticate`, `API URL`) for a customer-facing
  message with the dealership's phone number, so a broken integration never reads as a broken business.

## Reviews displayed on a client site

- Publish **verbatim** text only. Never transcribe a review from a screenshot: two OCR passes agreeing on
  most words still mangle names and numbers, and a misquote of a customer on a live site is worse than an
  empty reviews page. Prefer a provider export (CSV/JSON) or the site's own review feed.
- A rating-filtered list is a **selection**. Label it as one and link to the full profile — a five-star wall
  with no route to the rest is a misleading commercial practice, not a design choice.
- Dates: if the source carries none, show none. Do not infer a posting date from an entry date.
