# Keeping an audit honest once the fixes start

An audit is written once and then lives for days or weeks — re-cut for a colleague, forwarded to a
dealer, re-dated. The failure mode is a document that still describes the world as it was on the day
of the audit, and reads to its recipient as either an accusation ("this is still broken") or a false
claim ("this is fixed").

## The ownership column becomes a status column

A first draft assigns every item to someone — `Build (the platform owner)`, `DSC`, `the dealer`. That framing is
wrong in two ways the moment we start doing the work ourselves:

- it puts an item on a third party we have the access and ability to fix, which changes the
timeline the recipient plans against; and
- it says nothing about whether anything has actually been **deployed**, so a reader reasonably
  assumes a prepared patch is live.

Re-cut the summary as **finding → where it stands**, with three values that are worth distinguishing
in words rather than a tick:

| Value | Use it for |
|---|---|
| `fixed in the branch, not yet live` | written, committed and verified locally |
| `ours once <X> confirms` | blocked on one fact only the client holds |
| `the dealer's` | genuinely not ours to decide |

Then add **one sentence that says nothing in the document has been fixed on the live site**, with the
timestamp of the re-check that proves it (`re-verified at 14:30 on 29 October 2026`). Without it,
"fixed in the branch" reads as "fixed".

Split the fix list on the same axis — done / still to do / theirs — and put **what verified it** in a
column beside each completed line (the status code returned, the string that disappeared, the count
that changed). A reader can then check the claim instead of trusting it, which is the whole value of
the document.

## Re-verify before re-dating, and again before re-rendering

Every finding still reproducing is the precondition for a new date on the cover. Fetch the handful of
facts that decide the state — the form count, the status code on a junk path, the sitemap entry count,
the title string — and confirm they are unchanged. This costs one minute and is the only thing standing
between a re-dated report and an embarrassing retraction.

**A live site can change during the session that is writing about it.** The defect a dealer complained
about can be repaired between two passes, and a document that then states a fault which no longer
exists hands the reader a reason to distrust everything else in it. Re-measure immediately before the
final render, not only when the date on the cover changes.

## When a finding's status changes materially, rewrite the finding

An unsupported claim that the client then confirms is false has not been *softened* — it has got worse,
and it needs different language in the body, not a new status line bolted above the old text. Edit the
heading, the status paragraph and the fix in place; never leave "we cannot check this" standing above
"the client has confirmed it is untrue".

## Do not copy a value out of tool output into the document

The transport redacts and mangles strings that look like secrets. A phone number echoed back by a shell
or extraction tool can arrive masked (`+447****0314`), and that masked form pastes straight into a
report table, where it reads as a broken link and becomes the published contact number in a client
deliverable. Type identifiers from the source you actually fetched — the config file, the saved HTML,
the page — never from what the tool printed back, and after rendering grep the artefact for `****`,
alongside the digits you expect to see. Same family as mojibake and JSON-LD that looks mangled in
console output: the corruption is in the transport, not in the site.

## A note-to-colleague is a different document from the audit

When the report is going to someone internal (a coordinator, the platform owner), the first line they
need is not a verdict — it is **what we can do tonight without them**, followed by the short list that
needs their answer. Keep that to a handful of lines: the findings live in the attachment, and the
message exists to get a decision.
