# Report ownership, and what happens to an item Woody routes himself

Two conventions that decide whether a delivered audit gets acted on, and one mechanical
trap that catches a withdrawal done by hand.

## 1. Every finding carries an owner, and there are three of them

DSC dealer work is done by three parties, and the report says which is which on every item:

| Label | Owns | Tell |
|---|---|---|
| **Paul** | the audit, the copy, the reference patch and its verification — **and every fix that lives in a file we can reach** | the change is an edit to a template, `.htaccess`, CSS, sitemap or filter we hold a copy of |
| **the platform owner** | deployment, and the work that is not a file at all: an API key pair issued from an account, a third-party endpoint's field mapping, the stock feed's per-record values | there is no file to edit, or the change only counts once it is on their host |
| **the coordinator** | anything dealer-end — decisions, content supply, stock records, hours, reviews, and any word with the dealership | the fix needs an answer we cannot give |

**Label the person, never a bucket.** "Us — DSC" is not an owner; "Paul" is. These documents read as
notes between colleagues, and he asked for the first name explicitly — a company or team label gets
corrected on sight.

**Ownership follows access, not authorship.** A first draft of one of these reports put fourteen
build items on the platform owner and was challenged on it — "can we not do any of these?" — and twelve of them
were ours. We hold a local copy of every template, the `.htaccess`, the sitemap generator and the
CSS, plus a local Apache to prove a change against, so a defect in their code is ours to **write**
and theirs only to **deploy**. Check the files before assigning, reserve the platform owner's column for what
genuinely is not a file, and say which items already have a patch so his list reads as
review-and-deploy rather than investigation.

**Anything needing a client decision is the coordinator's by default** — do not park a client decision on the platform owner
because he is named in the same sentence, and do not label an item "Client" when the reader needs
to know *who* chases the client. Woody names the people precisely so the reader stops asking.

- **Straddling items carry both names, in the order they are needed:** "the coordinator — confirm the rate
  · the platform owner to render one fixed example". Order is the sequence of dependency, not seniority.
- **Open the document with a who-does-what table** — one row per owner, the item count, the item
  IDs and a phrase of what they cover. The first question every reader asks is how much of this
  is theirs, and a document that answers it on page two has already been triaged by hand.
- **Say which items are already built.** Where a patch exists, the owner's job is to review and
  deploy, not to investigate — that distinction belongs in the table, not only in the findings.

## 2. Withdrawal for routing is not a change of severity

When Woody says he will take a compliance or relationship question up with the dealer himself
("I'll take this up with Martin"), the item comes **out of the client-facing document** and stays
in the internal record. Three things follow, and only the first is obvious:

1. Remove the finding section, and any checklist line, table row or summary sentence that
   depends on it.
2. **Prove the removal by absence across the rendered artefacts.** The number, entity or status
   wording reappears inside the *evidence* of other findings — a quotation of the live site's
   footer, a probe result, a status-board row. Grep the source `.md`, then the extracted text of
   the PDF and the `.docx`, for the value itself and hold until the count is zero in all three.
   A finding withdrawn while its FRN still prints two pages later is worse than one left in,
   because the reader cannot tell whether it was withdrawn or missed.
3. Record the withdrawal where it will be found again: the digest, with the reason ("routing, not
   severity") and the fact that is being kept off the client's copy. If the item later returns,
   its severity is unchanged.

Expect the same handling for a company number, an ICO number or an individual's name, and expect
the instruction to be about the *conversation* rather than about the evidence.

## 3. Client-facing review sections

A dealer's reviews block is a recurring ask: the finding is always that the quotes are
unattributable (no name, date, rating or platform link), and the predictable question back is
"can we not use Google reviews?". Yes — the platform is not the defect. Give the three routes:

1. **A hand-maintained block** — the five or six most recent reviews copied verbatim, each with
the reviewer's display name, the date, the star rating and a link to the profile. No API key, no
third-party script, nothing to add to the CSP. It needs refreshing by hand, which is the dealer's.
2. **Google's own embed or a reviews widget** — refreshes itself, but the host goes into the
`Content-Security-Policy` `script-src` and `frame-src`. That is a build change, so it is the platform owner's.
3. **Remove the section** until either of the above is ready.

Two constraints to state at the same time, because the dealer will otherwise choose route 1 and
paraphrase:

- **A paraphrase of a real review is the same defect as an invented one.** Verbatim or nothing.
- **Pulled through the Places API rather than copied by hand**, Google's terms require the
  attribution to stay and the content to be refreshed inside 30 days. A copied block carries the
  same obligation in practice — a review section that is two years stale is its own finding.
- "Verified Buyer" goes unless the dealer can say what verified it and by whom; an unearned badge
  is the assertion that turns a copy nit into a consumer-law problem.

The mechanism by which invented reviews actually reach a live page — a bundled fallback array that
renders only when the service is empty, and a platform whose "sample payload" is itself seeded
content — plus the field mapping and the empty-state test: `references/review-feed-and-fabricated-seed.md`.
