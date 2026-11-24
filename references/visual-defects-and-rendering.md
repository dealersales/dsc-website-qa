# Visual defects: diagnose from the render, not the markup

For findings where the client says a page *looks* wrong — images cropped or zoomed, text over a photo,
layout overflowing, a logo in the wrong place. These are the findings most likely to be confidently
got wrong, because CSS and markup are readable and a rendered page is not.

## The rule

**A visual fault is diagnosed from the render.** A rule present in the stylesheet proves the selector
exists, not that it takes effect:

- `object-fit` only applies to **replaced elements**. Declared on a `<div>` it does nothing — and a
gallery class sitting on a div is a common pattern, so the declared `contain` proves nothing.
- A declared `aspect-ratio` is routinely overridden by a slider library's own sizing or a
  `max-height`, and the winning rule is not the one you read first.
- A class in the markup plus a rule in the CSS is not a rendering. It is a hypothesis with citations.

**Open the screenshot the client already sent first.** It is usually on disk, it is the actual
evidence, and reasoning around it is how a confident wrong mechanism gets written into a delivered
report. Read it before opening the stylesheet, not after the theory stops working.

## Never generalise from one page

Identical markup renders differently on different pages of the same site: image dimensions, slider
initialisation, load order, viewport. The client will know it is not universal, and "every car is
affected" is a claim that collapses the moment they open a good one.

**Establish a control pair before scoping severity:**

1. Ask for — or find — one URL that fails and one that renders correctly.
2. Diff the two pages' markup for the component. Identical means the difference is data or runtime.
3. Compare the source assets: dimensions, aspect ratio, file size, HTTP status. Measure with
   `sips -g pixelWidth -g pixelHeight` after downloading from the CDN.
4. Only then write a mechanism, and scope the finding to what the pair proves.

A defect confirmed on one page and absent on another is a **High** with a control pair, not a
**Critical** on every page — and the pair is what makes the supplier ticket actionable.

## Get the capture conditions

A screenshot without its viewport is not evidence of a rendering fault, because zoom and window
width change the layout:

- **Derive the CSS width from the file:** pixel width ÷ device pixel ratio. A 2× capture of a
  1,494 px window is 2,988 px wide — the numbers look enormous and mean a normal desktop.
- **Ask the client:** press ⌘0 (reset zoom), then read `whatismyviewport.com` — width, height, DPR.
  Chrome shows the current zoom in the ⋮ menu; Safari in View → Actual Size.
- **Re-check at 100%.** A fault that survives normal zoom at a normal width is real; one that
  disappears was a capture artefact and must not ship as a finding.
- **Put the confirmed viewport in the finding.** Otherwise the supplier tests at their own window
  size, cannot reproduce it, and closes the ticket.

A short viewport is a genuine cause worth naming: an element capped at `max-height: 75vw` is taller
than the screen on a wide, short window, and slider height calculations are where that surfaces.

## Reporting a fault to the template owner

Give the supplier a ticket that can be acted on without re-deriving your work:

- one failing URL and one working URL, side by side;
- the evidence the markup and data are identical between them (same container, same image tag,
  counts);
- the measurements already taken — image dimensions, how many assets return 200;
- the reproduction viewport and zoom;
- **what you have eliminated**, explicitly, so they do not repeat it.

Keep it narrow. Do not attach the full QA report to a support ticket: it turns a twenty-minute fix
into a project. "These two pages, one works" is a ticket; "twenty-six findings, one of which is
images" is a negotiation.

When the fault cannot be pinned from outside (identical markup, identical data, no broken assets),
say so plainly and ask them for a browser console on the failing URL — slider initialisation is not
visible in a static fetch, and guessing at it in a client document is how a finding gets retracted.

## Retracting one of these

If a mechanism turns out to be wrong, correct it in place and mark the earlier version as superseded
wherever it was circulated — the digest, the report, the copy already staged. The corrected finding
keeps the evidence that survives (measured dimensions, the control pair, status codes) and says
which explanation was withdrawn. A reader who saw the earlier version must be able to tell which
one they are holding.

## Fetching when a WAF blocks every client

A Cloudflare rule against datacentre addresses can block the crawler, the managed browser **and** the
local browser profile at once, while the client views the site normally. Fallbacks that worked:

- `r.jina.ai/<url>` with header `X-Return-Format: html` returns the served HTML (not markdown), which
  is what the head-layer, form and image checks need. Space requests ~2 s apart and handle retries.
- Image CDNs are frequently on a separate host that is *not* behind the same rule — check there
  before concluding the asset side is unavailable.
- State in the report's method note that the page set was fetched through a proxy, and that the WAF
  is not something a customer experiences.
- `web_extract` still works for content-level checks (it renders), but it is rate-limited per minute
  and returns markdown, so it cannot answer head-tag or markup questions.
