# Reaching the site, and proving what it renders

Two failure modes that produce wrong findings before any analysis starts: you cannot reach the site, or you reason about its rendering instead of looking at it.

## 1. A 403 from our crawler is usually a datacentre block, not a broken site

On the Click Dealer platform (`clickdealer.cloud`) Cloudflare answered *"Sorry, you have been blocked / You are unable to access clickdealer.cloud"* to all three of: Python `requests`, the managed browser, and the local-profile browser. The client, on an ordinary residential IP, loaded the same pages normally.

Rules:

- **Do not report the site as down.** Test the client's own access before writing anything about availability.
- **Do not burn a pass on user-agent, cookie or header variations.** A Cloudflare block is IP/ASN-based; changing the UA will not clear it.
- **Fetch through a reader proxy:** `https://r.jina.ai/<full-url>` with header `X-Return-Format: html`. It returns the real served HTML — title, meta, canonical, JSON-LD, form markup, inline CSS — from a different exit. Pace it at roughly one page per 2.5 s; it rate-limits under load, so retry with backoff.
- **The image CDN is usually still reachable directly** (`images.clickdealer.co.uk` on this platform). Use it to measure true pixel dimensions and file weights with `sips -g pixelWidth -g pixelHeight`; this is how you prove a resolution or aspect-ratio claim rather than inferring it.
- **Google's PageSpeed API has a small anonymous daily quota** that exhausts quickly (`Quota exceeded … Queries per day`). When it does, measure page weight from the markup and image files, and say in the report that no Lighthouse score is quoted rather than implying one was measured.
- **State the method in the report**: the page set was fetched through a third party rather than directly, and the block is not something a customer experiences.

## 2. Never diagnose a cropping or layout fault from CSS alone

A real sequence, to show how much a small unchecked inference costs: a vehicle-detail gallery was reported as *"a 16:9 `cover` container crops ~25% of every photo"*, inferred from a stylesheet while the client's screenshot sat unopened in `attachments/`. The client corrected the scope (*"not on every car"*). Checking the CSS properly showed the class carrying `object-fit: contain` was applied to a `<div>`, where `object-fit` has no effect at all. Comparing a bad page with a good one showed **identical** gallery markup, the same lazy-loader, and comparable 1024 px-wide source images. Opening the source JPEG showed a clean full-car shot. Three explanations, two of them wrong, and every correction forced a rebuild of the report, the PDF and the digest.

Procedure before writing any rendering finding:

1. **Open the screenshot the client already sent.** It is direct evidence of the rendered state, and asking again for a file already on disk reads as not having looked.
2. **Get a control pair** — one affected URL and one working URL of the same template. Ask the client if they have not supplied both; a client reporting "some cars look wrong" usually knows which ones.
3. **Diff the markup** of the two pages before forming a theory. Identical markup means the cause is not the page's data or template.
4. **Measure the assets** (dimensions, aspect ratio, file size) rather than reasoning from CSS declarations. An `object-fit` or `aspect-ratio` rule on a non-replaced element is inert; a rule can also be overridden by a later selector.
5. **Look at the source image itself.** If the crop is in the file, no template change will fix it.
6. **Name both URLs in the finding** and state which one the verdict came from.

Never generalise a per-page symptom to "every page" without counting it across the cohort. A client who spots the overreach will correct it, and every correction is a full rebuild of each rendered artefact plus a visible correction notice in the digest.
