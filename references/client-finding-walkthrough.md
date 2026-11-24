# Taking a client through the findings

An audit is not finished when the report ships — it is finished when the client has been taken through it. This is
the part that gets asked for later, usually days before a call, one question per finding.

## Answering "where is that finding?"

- **Keep the crawl on disk.** Save the fetched HTML for every audited URL under the project (`qa/crawl/`, one file
  per URL, filename = path with `/`→`_`). Live re-fetches of a Cloudflare-fronted dealer site return 403 or serve
  changed markup, so the retained copy is the only way to answer this weeks later. Grep it and answer in seconds.
- **Answer with the route, not the finding number.** Give the URL path, the visible nav label that reaches it, the
  exact markup, and how many pages carry it. The label matters most: `/car_locator.php` means nothing to a dealer,
  "Vehicle Sourcing, in the main menu" does.
- **Re-count the scope before repeating it.** A finding scoped to one page is often a template fault on several —
  check every page and every sibling form before quoting a number. If the report said one and it is two, say so and
  correct the pack; an understated count is the error a dealer finds for himself.

## What to do with what you find

- **Some findings resolve to no action, and that is worth saying.** An empty `alt` on a decorative illustration is
  correct markup; a second URL already consolidated by its canonical has done no SEO harm. Retire it honestly and
  defend it — one item truthfully closed buys more credibility than a tidy-looking fix, and a client told one thing
  needs nothing believes the rest.
- **Collapse findings that share a root cause** into one row on the client pack, the second marked "counted once".
  Two rows for one fault reads as padding once the client works it out.
- **Turn business questions into questions, not fix instructions.** A nav item for a second business, a fourth phone
  number, a "showroom" in the copy — these stay open until the dealer says which business they belong to. Put the
  question in the pack with both branches: it is yours → it needs its own page, NAP and profile; it is not → remove
  it and the finding disappears.
- **Say when the fault is bigger than the machine-readable layer.** A duplicated phone number is cosmetic; malformed
  `telephone` in JSON-LD (`+44 01706 …` with the trunk 0 still in) is not, because that is what Google reads for NAP.
  Fixing the visible copy without the schema leaves the real fault in place.

## Pack shape that survives the call

- **An owner column on every row** (Click Dealer / Us / Your decision). The first question a dealer asks is who he
  has to chase, and it makes the decision list self-evident when only two rows say "Your decision".
- **Sequence by consequence, not by finding number.** Going 1–26 loses the room by item four; open with the two
  compliance items, then the ones costing enquiries, then credibility, then plumbing.
- **Scope cells must not over-promise.** A rebrand item belongs to "separate rebrand work", not to us, or the client
  reasonably assumes it is included in what he has been given.
- **One-page summaries: set the type, then verify the page count.** Compose at 9 pt, render, and confirm with `fitz`
  that it is still one page. 9.3 pt spilled to a second page on a 26-row table; 8 pt fits but is unreadable in print.
  Never buy the fit by shrinking type below 9 pt — cut a sentence instead.
