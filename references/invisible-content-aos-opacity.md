# Invisible-but-present content (animate-on-scroll at `opacity: 0`)

A QA-pass finding class that is easy to miss and easy to misdiagnose. Confirmed
live in Sep 2026 on a dealer homepage whose entire above-the-fold area was
invisible on load.

## Symptom

The hero (or any section) is a plain black / empty block in your screenshot, but
`document.querySelector` finds the content, it's styled, and its images are
already downloaded. It looks like "still lazy-loading" — it isn't. The content is
in the DOM at **`opacity: 0`** because the scroll-animation library (AOS or
similar) never faded it in: a JS error, a consent gate, or an init that ran
before the elements existed.

## How to confirm (don't guess)

```js
// after wait_for_load() + a few seconds' settle
js("(() => Array.from(document.querySelectorAll('[data-aos]')).slice(0,4)"
   ".map(e => getComputedStyle(e).opacity))()")        // ["0","0","0","0"]

// nudge with a real scroll, then re-read
js("window.dispatchEvent(new Event('scroll'))")
cdp("Input.dispatchMouseEvent", type="mouseWheel", x=600, y=400, deltaX=0, deltaY=400)
// still all "0" -> it never appears
```

Then describe what the visitor actually sees, using the container's own box
rather than the invisible content:

```js
js("(() => { const h = document.querySelector('.hero-video') || document.querySelector('header');"
   "return h ? getComputedStyle(h).backgroundColor + ' h=' + "
   "Math.round(h.getBoundingClientRect().height) : null; })()")   // "rgb(20,20,20) h=892"
```

Related: a hero still showing a **loading spinner after ~8 seconds** never
resolved either — dark-and-spinning after 8s is broken, not slow.

## How to log it

**Severity:** High (Critical if it's the hero — the page has no visible first
impression). **Expected:** above-the-fold content visible on first paint.
**Actual:** `[data-aos]` container at `opacity: 0` on load, unchanged after a
scroll event; the visitor sees an Npx solid block. **Recommendation:** confirm the
animation library initialises after DOM ready and fires for in-view elements on
load, or drop the animation on the hero. Include the opacity probe output as
evidence — a screenshot alone reads as a rendering artefact to a developer.

## Why it matters for our own reports

If a QA pass skips this, the report implies the site's homepage is fine when a
first-time visitor gets a blank screen — the kind of finding that costs a client
confidence in the whole report. Apply the same check to any client site where a
screenshot looks emptier than the page source suggests.

(Fuller write-up of the same technique, plus how it interacts with
reference-site benchmarking and PDF verification: `dsc-seo-audit` →
`references/render-and-artefact-verification.md`.)
