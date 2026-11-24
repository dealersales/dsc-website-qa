# Defects you cannot see with curl

A dealer site can return 200 on every URL, pass an HTML diff, and still look broken to a customer.
These are the faults that only appear in a rendered browser, and how to prove each one instead of
guessing at it.

## 1. Blank or black flash while scrolling

Symptom, as the client reports it: "the page goes blank for a second when you scroll down". Named
per page, intermittent-sounding, invisible to any HTTP check.

Three causes, in the order they bite:

1. **An iframe with no `src` paints black.** A `data-src` plus JS lazy-loader leaves the element
   empty until it fires; browsers render that as a black rectangle at whatever height it claims.
   Give lazy iframes a light background (`#f0f3f5`) so the pre-paint matches the page.
2. **`height:100%` on an iframe whose wrapper is sized by padding.** A wrapper like
   `.map { padding-bottom: 360px }` has zero content height, so the iframe's `height:100%` can
   resolve against the **viewport** before layout settles — the flash covers the whole screen, not
   the map. Bind the iframe to its wrapper instead (`.map{position:relative}`,
   `.map>iframe{position:absolute;inset:0}`) and give the wrapper a `min-height`, not padding.
3. **A near-black page canvas.** `html { background-color: hsl(0,0%,12%) }` turns every unpainted or
   repainted moment into a black screen. Set the canvas to the page's own background colour.
   Related: `background-attachment: fixed` forces a whole-viewport repaint on every scroll frame —
   drop it on a long page.

**Measure it with `scripts/scroll_flash_probe.py <url>`**, which captures a frame immediately after
each scroll and again 1.2s later. A healthy page differs by a point or two; a defect shows a large
gap in either direction (dark = cause 1, near-white = cause 2). Sample a control URL once to prove
the probe itself is sane.

Do not try to prove this from a screen recording: at 4 fps a 300 ms flash falls between frames, and
difference analysis over the video finds page transitions instead.

## 2. Third-party widgets that fail in public

Finance calculators and application forms print their own errors straight into the page —
`API URL: … Status Code: 401 Error: Failed to authenticate`. A customer reads internal plumbing.

- **Keep a guard that rewrites that text.** Observe the widget container for
  `Status Code|Failed to authenticate|API URL` and swap in a human message with the dealer's phone
  number. The integration can fail again for reasons outside your control.
- **Consent can gate them to nothing at all.** A widget may occupy 1,400px of empty space until
  cookies are accepted and only then render. Clear the consent key and wait 30–40s to tell "gated"
  from "slow" before blaming load time. Fix with a placeholder in the widget's place that hides
  once consent is stored; if enabling consent mid-page does not reinitialise the widget, accept and
  reload, returning to the page with the `#anchor` so the visitor lands back at the calculator.

## 3. Template imagery that misrepresents the dealer

Page heroes come from a shared library (`assets/img/hero/webp/hero-N-1920.webp`). A small family
dealer inherits a forecourt holding hundreds of cars, or a marque they do not sell — and it is
often the client who spots it first.

- Let the hero helper accept a **path** as well as a library name so the dealer's own photograph can
  be used. When a real photo is passed, omit `width`/`height`/`srcset` rather than asserting
  1920×800: the browser reserves the wrong box and the layout shifts as the image loads.
- Audit stock images before launch. Unreferenced hero and splash files still ship as bytes; deleting
  nine unused images took 1.9MB off one mobile-first build.

## 4. Per-page sections that duplicate a global one

A page-level map plus the footer map on the same page is two identical maps, one above the other.
Count iframes on any page you touch (`grep -c 'google.com/maps'`) and remove the page-level one, so
the rest of the site keeps the global element.
