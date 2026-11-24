# Evidence, true scope, and presenting the findings

Three failure modes that make a QA report weaker than the crawl behind it: a finding evidenced from memory rather
than markup, a finding scoped to the page it was noticed on, and findings counted twice because one root cause threw
two symptoms.

## Retain the crawl — it is the evidence

Run the QA from a saved crawl (`~/Documents/<project>/<client>/qa/crawl/`, one `.html` per URL, plus `summary.json` and
`facts.json`) and keep it after the report is issued. Live re-fetching is often unavailable later: dealership sites
are commonly behind Cloudflare with bot protection, so a scripted `curl` returns 403 and a headless browser gets the
"Attention Required" interstitial — while the client still expects you to answer "where exactly is that?" weeks
later. The retained crawl answers it instantly and reproducibly.

Query it rather than re-fetching:

- Title/H1 inventory: regex `<title>(.*?)</title>` and `<h1[^>]*>(.*?)</h1>` per file, strip tags, report lengths.
- Embeds: `<iframe[^>]+src="([^"]+)"` and form/action attributes; count **which pages** carry each distinct src.
- Parameters: `url=https?://…` and similar, then count files matching to get the true blast radius.
- Nav labels: `<a[^>]+href="([^"]*PAGE[^"]*)"[^>]*>(.*?)</a>` gives the menu wording a client recognises.

A page that will not load on demand is not a blocker to answering a question about it, and saying "I can't reach
the site" when 98 saved pages are on disk reads as not having looked.

## Check the scope before rating severity

Grep the **whole** crawl for the defect before deciding how bad it is, and report both numbers: how many pages are
affected, and how many of the relevant components are actually wrong. A parameter appearing in 98 of 98 files can
turn out to be in 4 embedded forms, of which 2 are wrong — that is a Low, and named precisely. The same grep often
finds the defect is broader than the page it was first seen on (a second form, a second template), which raises the
count and changes who has to fix it.

State the count in the finding: "2 of 4 forms" is auditable; "the sourcing form" is not, and invites a dispute about
whether the others matter.

## Cite the correct pattern already in the estate

When some instances of a component are right and others wrong, say which are right and why. Two forms URL-encoding
`https%3A%2F%2F…` while two pass plain `http://…` turns the recommendation into "copy the parameter from the booking
form into these two" — a one-line change a third party cannot argue with, instead of a specification they must
interpret. Always look for a working example on the same site before writing the fix.

## Dedupe findings that share a root cause

Two findings can be one fault seen from two angles — a second business wired into the navigation, and a duplicate
URL under the same title, are the same template location-record. Before issuing:

- Group findings by **root cause**, not by page or by symptom.
- Keep both IDs but mark the secondary one as covered by the primary, and say so in the client-facing artefacts.
  A dealer who spots two rows for one problem discounts the whole count.
- Treat the dedupe as part of the finding text, e.g. "one root cause: X loads the stock page under a different
  number" — not a footnote the reader has to assemble.

## Presenting the findings on a call

When the client asks to "go through the audit", do not read the report in order — item four is where attention dies.
Sequence by consequence, roughly 45 minutes:

1. The one-liner: how many findings, how many are compliance, how many cost enquiries, the rest housekeeping.
2. Compliance items — risk, while they are fresh.
3. The handful that cost money — this is where they engage.
4. Credibility errors — small, but the things a customer notices.
5. The plumbing — grouped into one paragraph, not twelve items.
6. Privacy/data — tie it to whatever they have already agreed to do with their database.
7. Decisions and owners, last, so the call ends with commitments.

For each finding the call needs four things: what it is in their words, why it costs them, who fixes it, and what
the fix looks like. Have the before/after on screen using their own pages — a live example beats a description.

Prepare a **decisions to leave with** list (5–8 items, each answerable yes/no or with one fact), and a **do not**
list: no next-phase pricing, no supplier timescales, nothing regulated that belongs to another party, and no
answering an architectural question (domain moves, platform changes) live — "I'll put the options in writing" is
the answer.

## Fairness checks that keep the report credible

- **Judge each page on its own.** Where a group of pages shares a template flaw, say so; where a group is the right
  shape and only has the estate-wide naming/town error, say that instead. A verdict applied to 100 URLs reads as
  automated.
- **Name the one item the supplier must own** (a rendering fault reproducible only on their template) and let the
  rest sit with whoever holds the file.
- **Prefer "separate piece of work" for anything outside the QA's scope** — a rebrand discovered mid-audit is not
  included in the report the client has been handed, and the owner column must not imply it is.
