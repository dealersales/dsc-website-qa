# Rendering and access pitfalls

Two ways a live-site QA produces confident, wrong evidence. Both are about the
distance between what you can fetch and what a customer actually sees.

## 1. A rendering fault is not a template fault until you have seen the page

**Read the screenshot the user has already sent before reasoning from CSS.** It is
usually the only rendered evidence you have, and it outranks any stylesheet
inference.

Worked correction: a vehicle gallery was reported as a 16:9 `cover` container
cropping ~25% off "every car". The CSS actually placed `object-fit: contain` on a
`<div>` — inert, because `object-fit` applies only to replaced elements
(`img`, `video`) — and the slides clipped at `overflow:hidden`. The client had
already said the fault was **not** on every car, and the screenshot they supplied
showed a severe crop on one vehicle only.

Rules:

- `object-fit` on a wrapper element is decoration. Check the element the rule
  lands on is the `<img>` itself before arguing from it.
- The page set is a cohort, not a template. Say what you measured — "the 4 of 11
  sampled", "confirmed on the Audi A3 (8189170)" — never "every car" / "all
  pages" unless you exercised all of them.
- Where one page renders correctly and another does not, **the difference between
  them is the diagnosis.** Ask for the working example. Identical markup plus
  divergent rendering means the variable is the asset (dimensions, EXIF rotation)
  or a load-state race — and those take different fixes from different owners.
- Over-scoping is the expensive error: "a template bug on every car" invites a
  platform ticket that one counter-example falsifies, and it costs credibility on
  the findings that are real.
- When you have to retract, quote the wrong claim and correct it where it was
  read (report, digest, client message). An earlier copy has already been seen.

## 2. Pacing, and the reader-proxy fallback

Dealer sites behind Cloudflare (Click Dealer / the platform estates among them) refuse
datacentre addresses. A fast sweep of sitemap URLs returns
`403 Attention Required! | Cloudflare` naming the platform host, and every browser
we can drive exits from the same class of address — so the site looks "down" when
it is only refusing us.

- Request at **2–3 s intervals from the first page**. The burst, not the total,
  triggers the block.
- When blocked, the reader proxy returns the real document:

  ```bash
  curl -sS -m 90 "https://r.jina.ai/https://www.example.co.uk/used-cars" \
       -H 'X-Return-Format: html' -o page.html
  ```

  `X-Return-Format: html` is the part that matters — without it you get markdown
  and lose head tags, form markup and JSON-LD. It is good enough for titles,
  meta, canonicals, schema, forms and image tags; it is not a renderer, so it
  cannot settle a layout question (see §1).
- Confirm the body is the page and not a challenge page before parsing, and keep
  a small retry with backoff — the proxy rate-limits (about 10–12 requests a
  minute), so batch and sleep rather than parallelising.
- Record the proxy in the report's method note: the page set was fetched by a
  third party, and the client should know the difference between "the site
  blocked our audit" and "the site is broken".

## 3. Never quote a number you did not measure

When PageSpeed/Lighthouse is unavailable — quota exhausted, or the runner cannot
reach the site — report what you did measure (page weight, image dimensions and
counts, render-blocking assets) and say in the method note that no lab score is
quoted. A fabricated "mobile score of 42" is the easiest number in a report for a
client to check, and losing that argument costs the findings that were real.
