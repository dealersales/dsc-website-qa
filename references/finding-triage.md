# Tracing, verifying and settling a finding

How to move a finding from "a line in the report" to "a number and an owner", before it is put in front of a client.

## Trace from the retained crawl, not the live site

A dealer site behind Cloudflare returns a 403 challenge page to `curl` and to the automation browser, so a live
re-fetch of a page you already crawled is wasted time. QA runs save the crawl (typically `<project>/qa/crawl/`, one
HTML file per URL, 90–100 pages) — grep that instead. It is the same evidence the report was built from, so quotes
and markup match exactly.

```
ls <project>/qa/crawl/ | wc -l                      # how many pages the crawl actually holds
```

If the page genuinely is not in the crawl, say so and fetch it fresh; do not paraphrase the report's description of
the markup.

## Quantify every finding across the whole crawl

**A finding named against one URL is usually template-wide.** Extract the defect from every crawled page and quote
the count — "on 98 of 98 pages" is a template fix for Click Dealer; "on one page" is a copy edit. The count changes
who owns it and what it costs.

What this catches, repeatedly:

- An insecure `url=http://…` parameter present on 98/98 pages, of which only 2 of 4 embedded third-party iframes
  actually pass it — and one of those two was a second form the report never named.
- Sibling forms that already implement the correct pattern. When two of four embeds are right, the fix is "copy the
  good one", which is a one-line request instead of a design discussion.
- A phone number printed in two formats, with a third placement nobody had listed (header icon, sticky mobile bar,
  body copy, footer list, contact box — count them all, do not stop at the first hit).

## Compare page classes before calling a defect structural

Before writing "every vehicle and category page", open one of each class. They can fail differently: vehicle titles
being raw feed strings while category titles have the right shape and are wrong only on town and brand. Report them
separately — a client who is told 100 URLs are wrong, then finds one class is fine, discounts the rest of the report.

Also check title against H1. Identical title and H1 on every page means one phrase doing two jobs: the title is the
search-facing string (it truncates around 60 characters) and the H1 is the human heading. Feed strings as titles
also lose the year, the town and the dealer name — the three things that make a car page findable.

## Merge findings that share a root cause

Two numbered findings are often one fault seen from two angles — a nav item pointing at a query-string location
selector produces both "a second business wired into the menu" and "two URLs serving one page under one title".
Collapse them into a single row, mark the second as *covered*, and say so when presenting: the count is honest and a
client cannot accuse you of padding it.

Sometimes they are only *partly* the same fault, and the pairing is the insight: the canonical tag means no
duplicate-content harm, but it also means the sub-brand can never rank for anything. Lead with the consequence the
client cares about, not the mechanism.

## Be prepared to downgrade a finding to "no action"

If the markup is correct as written — an empty `alt` on a decorative illustration whose meaning is carried by the
heading and copy beside it — record it as **no action needed** and say why. Recommending a change that makes a
screen reader announce a description of stock artwork is worse than recommending nothing.

Telling a client that a finding is not worth doing buys more credibility than a tidy-looking fix, and it protects
the findings that do matter. Never manufacture work to make the count look thorough; publish the honest number of
things that actually need doing.

## Always check the machine-readable layer too

When a finding concerns visible copy, NAP or contact details, open the structured data as well — JSON-LD
`telephone`, `url`, `name`, `addressLocality`, and any microdata. A visible fix without a schema fix leaves Google
reading the wrong value, which is the opposite of the point of the exercise.

- `"telephone": "+44 <phone>"` is not a phone number. E.164 needs the trunk `0` dropped and no spaces:
  `+441706360257`.
- `"url": "www.example.co.uk"` with no scheme is not a URL.
- Two JSON-LD blocks (`Organization` and `AutomotiveBusiness`) carrying different values is itself a finding.

## Answering "where is it?"

Give the navigation label, the URL, the exact markup and the asset path — not a restatement of the report line.

```
Nav label  →  https://site.example/page.php
<iframe src="https://vendor.example/forms/x.php?url=http://site.example">
```

Then say what the visitor experiences and what the fix is in the vendor's terms ("copy the booking form's
parameter"). That is the difference between an expert walkthrough and reading the report back to them.
