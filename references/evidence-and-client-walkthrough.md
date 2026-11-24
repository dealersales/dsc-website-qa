# Evidence base, finding follow-through, and the client walkthrough

What happens after the report is written: where the evidence lives, how to answer a question about it weeks later,
how to widen a finding you only half-caught, and how to take a dealer principal through it.

## Keep the crawl — it is the evidence base, not scratch

Write every crawled page to a stable folder (`~/Documents/<project>/<client>/qa/crawl/`, one file per URL, name derived
from the path) and keep it beside the report. Three things depend on it:

- **Weeks later the site may refuse to answer.** A client site sitting behind a CDN will start returning a
  challenge to scripted fetches once it has been crawled a few times, from curl and from an automation browser
  alike. The retained crawl still holds the markup, so "where is the form?", "what exactly is in the footer?" and
  "which page passes that parameter?" stay answerable without re-fetching anything.
- **A finding needs its evidence quoted back**, verbatim, when the client or the supplier disputes it.
- **The crawl is the only way to count.** "On one page" and "on 98 of 98 pages" are different findings.

When a live fetch is needed for something the crawl cannot show (current stock count, a live price), it is a
fresh request, not a re-verification of the report.

## Find who owns the template before you assign fixes

`dig +short www.<domain>` revealing a CNAME such as `websites.<platform>.cloud` proves whose infrastructure serves
the site, and therefore whose file a template fix has to be made in. That single lookup decides the owner column
for most findings, and it is worth doing before writing "their web company need to…" into a client document.

## Widen a finding before you publish it

A template fault found on one page is almost never only on that page.

1. **Sweep the crawl for the sibling.** Grep every crawled file for the pattern and count: `N of M pages`.
2. **Look for a correct sibling.** The same component is often implemented properly elsewhere on the same site —
   four embedded enquiry forms where two pass the parameter correctly and two do not. That is the most useful
   thing you can hand a supplier: not "fix this", but "copy the working parameter from the other two forms".
3. **Re-open the severity.** A fault reported as Low because it looked like one page becomes a template finding
   once it is on many pages. Say so and correct the number rather than leaving an understated report in the
   client's hands — and where the report has already gone out, carry the correction in the next document and the
   call, not in silence.

## Answering "where is that?"

Give all three, in this order: the **navigation path** (the menu label as it appears), the **URL**, and the **exact
markup** with the offending value in it. A dealer or a supplier can act on that; a page name alone sends them
hunting.

## Taking the client through the report

Sequence by **consequence, never by finding number.** A dealer principal loses the thread by item four of a
numeric list, and the numbering belongs to the document, not the conversation.

| Order | Block | Why |
|---|---|---|
| 1 | The shape in one line | "26 findings: 2 compliance, 6 costing you enquiries, the rest housekeeping" |
| 2 | The compliance items | The only ones carrying risk rather than cost — front-load while attention is fresh |
| 3 | The items costing money | The commercial conversation, and the one the client engages with |
| 4 | Credibility errors | Cheap fixes that a customer notices |
| 5 | The plumbing | Group into one paragraph; no one wants 12 technical items individually |
| 6 | Privacy and data | Matters before any database or marketing work, which ties back to scope already agreed |

- **Leave with named decisions, not agreement in principle.** Two or three, each an answer only the client can
  give, written down before the call ends.
- **Keep regulated wording with the client.** Where a finding needs compliant wording (a representative example),
  say the dealer or their principal signs it off — an agency drafting it and publishing it takes on risk that is
  not theirs to take.
- **Have a line ready for "how much of this is my web company's fault?"** Mostly none of it: template defaults
  never configured for a dealership. That answer keeps the supplier cooperative, and you need them for most of
  the list.
- **Deflect anything that is a separate decision** — a domain move, a platform change — into writing rather than
  answering it live; it carries risk that deserves options, not a yes on a call.
