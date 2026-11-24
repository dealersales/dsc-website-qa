# Evidence and scope discipline for a website QA

Rules that stop a QA report asserting something the evidence cannot carry. Each one cost a
retraction in a live client document.

## 1. A rendering finding needs a rendered view, not a stylesheet

Reading CSS tells you what *could* happen; it does not tell you what the browser did.

- **`object-fit` on a non-replaced element does nothing.** A gallery class carrying
  `object-fit: contain` on a `<div>` is inert — the property only applies to `img`, `video`,
  `canvas`. Finding it in the theme is not evidence of anything.
- **The clipping happens on an ancestor.** A slider wrapper (`overflow: hidden`, fixed or
  percentage height) clips an image that was never given a width, and the visible result is a
  crop of the image's natural size — which no image-side CSS property can override.
- **Aspect ratio alone rarely explains a dramatic crop.** Check it before blaming it: two cars
  with a 1.30 and 1.23 image ratio produce a ~5% difference in a fixed 1.26 frame, not a
  grille-only view. If the arithmetic does not produce the symptom, the mechanism is elsewhere.

**Order of proof:** look at the client's screenshot (or take one) and describe the symptom →
compare against a page that renders correctly → only then offer a mechanism, labelled as such.

### Settling a per-page render fault

1. Get a **control pair**: one URL that renders wrongly and one that does not.
2. Diff the markup of the two. If identical, the fault is not in the data or the template
   string — it is initialisation, viewport or load order.
3. Measure the source assets on both (dimensions, ratio, HTTP status). All 200 and comparable
   means the images are not the cause.
4. Note the viewport it was captured at. Ask the client to reset zoom with `⌘0` and confirm
   whether it still reproduces; `https://www.whatismyviewport.com/` reads out width and DPR in
   one visit if you need the number.
5. Only then write the finding, and give the developer the control pair rather than a theory.

A screenshot's pixel width ÷ DPR gives the CSS viewport (2988 px at DPR 2 = 1494 CSS px). That
is enough to rule a zoom artefact in or out without another request.

## 2. Scope: quote the denominator you actually measured

- Sample size is part of the finding. "Four vehicle pages" is not "every car".
- Write **N of M sampled** until the stock crawl has run, then reissue the finding and the count.
- A crawl that lands after the report went out is a **correction**, not a quiet edit: restate the
  number, say which earlier version said something else, and re-render every artefact.
- Separate a **page-level** fault from a **template-level** one in the same pass — the two have
  different owners and different fixes, and one number cannot describe both.

## 3. Getting the served HTML when the host refuses you

Managed hosts and CDN rules block datacentre IPs, which takes out the crawler and every browser
route at once while the site is perfectly fine for the client.

```bash
curl -sS -m 60 -H 'X-Return-Format: html' "https://r.jina.ai/https://www.example.co.uk/" -o home.html
```

- Returns the served markup, including `<head>`, form actions, tracking IDs and JSON-LD.
- Markdown extraction is fine for copy and useless for attributes — do not try to audit a form
  or a canonical from it.
- Pace requests a few seconds apart, retry once on a short or blocked body, and write every page
  to disk so a later failure does not cost the pass.
- Keep the block itself out of the report: it is our access problem, not a customer-facing defect.
  Say only that the page set was fetched through a proxy if the method matters to the reader.

## 4. When a measurement service is unavailable

If PageSpeed/Lighthouse quota is exhausted or the host is unreachable from the lab, do not skip
performance silently and do not imply a score was captured.

- Measure from the served markup: page weight, number of image elements and distinct files,
  `srcset` presence, `loading="lazy"`, render-blocking stylesheets and scripts, third-party tags.
- Measure images directly from the CDN (`curl` + `sips -g pixelWidth -g pixelHeight`) for true
  dimensions and file weight — that survives a blocked main domain because the image host is often
  separate.
- State in the report which measurement was and was not taken, and why.
