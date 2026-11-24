# Rendering claims, control pairs and proxy access

How to diagnose "it looks wrong on screen" reports, and how to keep crawling when a
WAF refuses you. Read this before writing up any finding whose evidence is a
screenshot, a CSS rule, or a single page.

## 1. The screenshot is primary evidence; the stylesheet is not

When a client says a page renders wrongly, open the capture they supplied
**before** reading the markup. A stylesheet tells you what was requested, not
what the browser did with it, and two separate diagnoses failed here by naming a
mechanism the page never used.

- **Confirm which element carries the class before quoting its rule.**
  `object-fit`, `aspect-ratio` and `overflow` behave differently on a replaced
element and on a wrapper. A rule like
  `.gallery { object-fit: contain }` on a `<div>` is a no-op, so it proves
  nothing about the `<img>` inside it. Print the element that carries the class
  (`.outerHTML` of the matching node) and read the child tag before reasoning
  from the CSS.
- **Then explain the rendered result from the markup**, not the reverse. If the
  markup and the capture disagree, the capture wins and the markup is what you
  have failed to read properly.

## 2. Ask for a control pair before theorising

When a fault is reported as intermittent, per-vehicle, per-page or
"not on every one", the fastest route is two URLs: one that fails and one that
works.

Diff the two pages and read the result:

| What the diff shows | What it rules out |
|---|---|
| Identical markup, same template, comparable images | The template and the per-record data. Points at rendering conditions: viewport width, browser zoom, image load order, slider initialisation |
| A markup or data difference | Names the field immediately — chase that |

State the control pair in the finding's Evidence line. "Confirmed on X, which
fails, against Y, which renders correctly" is far stronger than a description of
the symptom, and it is what the platform owner needs to reproduce.

**Never generalise one page to the estate.** "Every vehicle is affected" is a
cohort claim and needs a cohort measurement. The same applies to a fault seen on
one browser at one window size.

## 3. When the crawler is refused: fetch the served HTML through a reader proxy

Cloudflare (and some hosts) reject datacentre IPs with "Sorry, you have been
blocked / unable to access <host>". That can include the managed browser, so
the site looks unreachable when it is fine for every real customer.

```bash
curl -sS -H 'X-Return-Format: html' "https://r.jina.ai/<full-url>"
```

That returns the real served markup — head tags, forms, JSON-LD, inline CSS and
all — which is what a QA pass needs. Two things to check while you are there:

- **Image CDNs are usually a separate host and stay reachable.** Measure the
  real pixel dimensions and byte weights directly from them; do not infer
  resolution from a filename or a `width` attribute.
- **Say so in the report's method note.** Name the proxy and the reason: the
  block is not something a customer experiences, and a reader is entitled to
  know the page set was fetched through a third party rather than direct.

Pace the requests (a few seconds apart) and retry with backoff; a proxy has its
own rate limit and will return empty bodies under load.

## 4. Cohort counts only from a finished crawl

A report built on a partial crawl has to be reissued when the crawl completes,
and a reissued report is a credibility cost. Either wait for the crawl to finish
before writing any "N of M pages" sentence, or write the sample size into the
sentence itself ("19 templates and 4 vehicle pages examined") and raise it later.

When a headline count does move, remember it usually exists as a **separate
literal in each renderer** — the `.docx` builder and the HTML/PDF template each
carry their own copy. Patch the content data, not one rendered string, then
rebuild and re-verify **both** artefacts with their own parsers. A count
corrected in the Word file and left stale in the PDF is the failure this catches.
