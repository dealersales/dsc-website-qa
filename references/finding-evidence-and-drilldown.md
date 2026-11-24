# Finding evidence — retaining the crawl, and surviving the drill-down

A QA report is a distillation of ~100 fetched pages. Once it is with the client, every conversation about it is
about *evidence*: "what does that mean", "where is it", "show me". The report cannot answer those on its own,
and by then the live site may no longer be reachable.

## 1. Retain the crawl, not just the report

Write every page you fetch to `~/Documents/<project>/<client>/qa/crawl/` with a filename derived from the URL
(`sell_my_car.html`, `search_page_php_location_id_3.html`), alongside a `facts.json` / `summary.json` of the
head-layer data. Keep it after the report ships.

Why this is not optional:

- **Dealer sites sit behind bot protection.** A Click Dealer site behind Cloudflare answers `403` to `curl` —
  even with a full browser header set — and the automation browser gets "Attention Required! | Cloudflare".
  The crawl taken at audit time is then the only copy of the evidence that exists.
- Drill-down questions arrive days or weeks later, one finding at a time, and each one needs the exact tag,
  not the summary.
- Re-verifying a finding after a claimed fix needs the "before" markup to diff against.

The crawl also answers questions the report never asked, which is how a follow-up question becomes a new finding
rather than a shrug.

## 2. Answer "where is X" from the markup, never from the report

Grep the retained crawl for the literal thing the user named — a phone number, an asset path, a query
parameter — and quote the surrounding element with its file and tag:

```python
for f in sorted(glob.glob("qa/crawl/*.html")):
    c = open(f, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'<img[^>]*click_buy[^>]*>', c):
        print(os.path.basename(f), m.group(0))
```

Then give the answer in three parts: **the page and how a visitor reaches it** (nav label, not just the URL), **the
exact markup**, and **what it does**. "`/img/click_buy/car1.png` in the Vehicle Valuation block on `/sell-my-car`,
empty `alt`, decorative" is an answer; "one image lacks alt text" is a restatement of the finding.

**Count scope in code across every file.** A defect reported on one page is often on more, and the difference
changes the severity and the fix owner. Iterate the crawl and print `N of M` rather than sampling a handful of
pages — the same habit that stops a client answering "is it just that page?" with a guess.

## 3. Expect the drill-down to correct the report

Three shapes recur, and each changes what you tell the client:

| Shape | What it looks like | What to do |
|---|---|---|
| **Scope understated** | A fault logged against one page turns out to be on two, or on all 98 | Widen the finding, name every page, and say the report understated it |
| **Two findings, one root cause** | A second business in the nav *and* a duplicate URL under one title — the nav item is what generates the URL | Collapse them into one item and mark the second as counted once |
| **No action needed** | Empty `alt` on a decorative illustration; markup that is already correct | Defend it rather than fixing it |

- **Say it out loud when a finding shrinks.** Telling a dealer principal that one of the 26 findings needs nothing
  buys more credibility than a tidy-looking fix, and it is the moment he starts trusting the other 25.
- **A no-action finding is defensible in one sentence:** the heading and copy carry the meaning, so the image is
  ornament and an empty `alt` is the correct markup for ornament. Do not "fix" it by writing alt text that makes a
  screen reader read out a stock illustration.
- **When scope widens, the owner can change.** A parameter wrong on the dealer's own content page is ours; the same
  parameter baked into the template is the platform's. Check where the value is generated before assigning it.

## 4. Before a client walkthrough, reconcile the count

A report of 26 findings that collapses to 24 after reconciling same-root-cause pairs looks padded if the client
notices, and looks careless if he does not. Before the call:

1. Collapse same-root-cause findings, marking the absorbed one `(covered by N — counted once)`.
2. Mark no-action findings `No action` with the reason as the owner cell.
3. Keep the original numbering. Renumbering a document that has already gone out creates a second version of
the truth; the reconciliation lives in the call pack and the covering note.

## 5. Feed the corrections back

- If the report has **not** gone out, fix it at source and rebuild.
- If it **has**, do not silently reissue: put the correction in the call pack as an appendix, tell Woody which
  finding changed and why, and let him decide whether the client sees a revised copy.
- Update the drill-down into the call pack while it is fresh — an appendix with the real markup and the real
  count is what makes the finding a 30-second item on the call instead of an argument.
