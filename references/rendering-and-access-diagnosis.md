# Diagnosing rendering faults, and reaching a site that blocks you

Two things that go wrong on almost every visual QA and cost more time than the findings themselves.

## 1. A visual fault is diagnosed from a screenshot and a control page

**CSS is not evidence of what the browser painted.** It records intent. A gallery class carrying
`object-fit:contain` sat on a `<div>`, where the property does nothing, while the slides clipped their
contents with `overflow:hidden` — the rule that looked like the answer was inert, and a confident
write-up of it as the mechanism was wrong in front of the client.

Procedure, in this order:

1. **Read the screenshot the client already sent before forming a theory.** It is normally the only
   render you have, and it is often sitting in the same thread while the agent reasons from source.
2. **Fetch the source photograph separately and look at it.** If the image is a clean full-frame shot
   and the page shows a corner of it, the crop is in the rendering; if the file is already a close-up,
   it is the photography and no template change fixes it.
3. **Ask for one page that displays correctly and compare the pair.** This is the single highest-value
   question: identical markup on a good page and a bad one eliminates the template, the data and the
   asset pipeline in one step; different markup localises it immediately.
4. **Check the asset itself is not the fault** — every image on both pages should return 200 before
   blaming initialisation, because a broken file can stop a slider dead.
5. **Only then write the mechanism**, and mark it as a hypothesis if it still is one.

**Never generalise scope from one example.** "Every vehicle page crops the hero" was written from a
single failing page on a site where the same template rendered fine elsewhere; the correction cost more
than the original finding was worth. Say "some pages" until the cohort has been measured, and if the
build is small enough to check all of them, check all of them and give the ratio.

**Separate "it looks wrong" from "it looks wrong at my zoom level".** Ask for the viewport width and
zoom, or read them off the capture: a 2988-pixel-wide screenshot on a 2× display is a 1,494 CSS-pixel
window at 100%. A fault that reproduces at normal zoom is a defect; one that only appears zoomed is a
capture artefact, and writing the second up as the first wastes a developer's afternoon.

**When the client says a fault is not universal, they are usually right and you are usually generalising.**
Re-read the evidence with that correction in mind before defending the finding.

## 2. Reaching a site whose edge refuses you

A WAF that blocks datacentre IPs (Cloudflare's "Sorry, you have been blocked") takes out `requests`,
the managed browser *and* the local-profile browser — retrying from another tool on the same host proves
nothing. The page set is still auditable through a reader proxy:

```bash
curl -sS -H 'X-Return-Format: html' "https://r.jina.ai/https://example.co.uk/page" -o page.html
```

- **Pace it.** ~3 seconds between fetches, and retry with a longer backoff; a burst gets rate-limited.
- **It returns the served document**, so head tags, JSON-LD, form markup and inline CSS are all
  readable — exactly what a QA needs and what a markdown extractor throws away.
- **Strip and verify as normal.** The proxy is a transport, not a renderer: mojibake, a decorated
  `<title>` or a masked secret in *tool output* are still transport artefacts until confirmed against
  the saved bytes.
- **Say so in the method note.** "The site's firewall refused our crawler, so pages were fetched through
  a reader proxy" is a measurement caveat; it is not a finding, because no customer experiences it.
- **The same trick does not fetch images.** For a dealer's logo or a stylesheet, an image proxy
  (`https://images.weserv.nl/?url=<host><path>`) returns the binary even when the page requests are
  blocked.

When the browser and the proxy both fail, say the page could not be read and name what was tried — a
report with a known gap is recoverable; one built on assumed page content is not.
