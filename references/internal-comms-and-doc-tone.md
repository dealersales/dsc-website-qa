# Internal comms and document tone

Woody's house style for anything that goes to the platform owner at the platform or the coordinator at DSC — work summaries,
handovers, status updates, covering messages. It is **not** the style for client-facing reports,
which stay more formal and avoid file paths and jargon.

## The rules

- **First names only.** "For: the platform owner and the coordinator", not "Prepared for: the platform owner (the platform Systems) and
  the client coordinator (Digital Sales Consultants)". No surnames, no job titles in the header.
- **Team voice.** "We got Moorside live", "what we did", "we checked it". First person singular is
  fine for your own actions ("I rolled one change back"). Avoid passive corporate constructions.
- **No blame framing.** Describe the build's state, not anyone's failure: *"the fix list hadn't made
  it onto the build"* rather than *"almost none of the pre-launch fixes had been applied"*. The
  facts carry the point; the reader knows whose build it is.
- **Own your own slips.** Say *"I broke something and fixed it"* where that happened — a document in
  which nothing ever went wrong reads as less trustworthy, not more.
- **Column headers go informal too:** "Owner" → "Who's on it"; "Client / lender" → "Moorside /
  lender"; "DSC" → "Us".
- **Soften the framing, never the facts.** A finding keeps its severity and its numbers; only the
  wording around it changes. Do not drop a finding to make the document read better.
- **Anchor to dates, not relative time.** "live since 29 October", not "live since last week" — the
  document gets forwarded days after it is written.

## Shape that works

Six sections, in this order:

1. **Where we're at** — three short paragraphs: what went live, the one thing that was doing real
   damage, and that it is now fixed and checked.
2. **What wasn't right on launch** — a two-column table (what we found / why it mattered), with the
   consequence in plain terms rather than the mechanism.
3. **What we did** — two columns (what we changed / where it's landed), each row ending in something
   countable.
4. **Still open** — what / who's on it. Never leave this out; a summary with no open items reads as
   either finished or evasive.
5. **For <name>** — the technical annex: host, docroot, files changed, backup location, and the two
   or three gotchas the next person needs. This is the only section with paths and commands.
6. **How we checked it** — the harness score, how the measurements were taken, and what was *not*
   tested. Naming the untested items is what makes the tested ones credible.

## Delivery

- Ship a rendered **PDF and DOCX** plus a **short paste-ready message** in chat and saved as
  `<CLIENT>-message-to-<names>.md`. Woody trims the message hard before sending, so keep it to five
  short paragraphs: what was live, what we fixed, what's still open, the one ask of the platform owner, and
  "summary attached".
- The message and the document are different documents. The message is the nudge; the PDF is the
  record.
- When the recipient is both technical and non-technical, one document is fine **provided** the
  technical material sits in its own numbered section rather than threaded through the narrative.

## Pitfalls

- **Do not let informality drift into vagueness.** "Sorted now" is fine as a lead; every claim in
  the tables still needs a number (29 URLs, 434 redirects, 22 of 22).
- **A softening pass is a rewrite, not a find-and-replace.** Re-read each changed sentence — replacing
  "was applied" with "hadn't made it across" leaves the rest of the sentence needing agreement.
