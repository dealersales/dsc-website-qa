# Who owns a fix, and what to do when the client disagrees

Three situations that decide whether a fix is ours to make, someone else's to authorise, or nobody's to touch. Getting this wrong costs more than the defect does: a fix applied over the top of a client's stated position gets reverted, and the credibility lost is not recoverable by being right.

## 1. Sort every finding into an owner before drafting anything

Before writing the fix list, assign each item one of four owners:

| Owner | Test |
|---|---|
| **Us — template/build** | It is in a channel we control and needs no new facts (forms, routing, titles, redirects, headers, meta, markup). |
| **Us — platform** | It is in a shared component the client's build inherits, so a fix here is a platform change with a blast radius. Say which other sites a fix touches before touching it. |
| **The dealer** | It needs a fact, a licence, a rate, a policy or a preference only they hold. Publishing a placeholder on their behalf is not a fix. |
| **Nobody** | It is working as designed. A stock counter that is site-wide, an intentional `noindex`, a template decision. Ask before reporting it as a defect. |

A finding that is really a missing fact from the client (an APR, an FRN, opening hours) must not be written as a build ticket — that produces a fix list the build owner cannot action, which is how these lists get quietly ignored.

## 2. Copy that reads as a bad practice is often the client's instruction

A blanket "no refunds" clause, a fee nobody would defend, an aggressive availability claim: these look like template debris and are frequently hand-written to the dealer's brief. Deleting one silently overrides a commercial position the business chose.

Procedure:

1. **Establish authorship before editing.** Is the wording boilerplate carried from the template, or specific enough that somebody typed it? Ask the account contact if it is not obvious.
2. **If it is the client's, leave it live and make it an agenda item.** Removing it the day before you sit down with them is the wrong call even when the legal reasoning is sound.
3. **Take the risk *and* a replacement that achieves the same aim.** The dealer's real objective is usually narrower than the wording: protection against time-wasters holding a car off sale becomes a reservation fee that comes off the purchase price and is refundable less costs actually incurred (HPI, valet, MOT), confirmed in writing at the point of payment. A draft they can accept or reject on the spot converts a confrontation into a decision.
4. **Record it as a client decision in the report**, with the finding's severity untouched. "Left in place deliberately at the client's instruction, advised against" is a defensible record; a silent deletion is not.

Related: an unenforceable term is still a finding even after the client confirms they asked for it — the record should carry the advice whether or not they take it.

## 3. When the client says they cannot find something on their own site

Treat it as a navigation question first, not as an error by the person looking. Two causes account for most of these:

- **The page is live but nothing links to it.** An orphaned page (no menu entry, absent from the sitemap) reads to the owner as "it has been deleted". Confirm reachability from the rendered navigation or the link graph before answering.
- **A two-template build puts the item on only some pages.** One footer carries the clause and the other does not, so "it is not on the homepage" and "it does not exist" are indistinguishable to the person looking.

Answer with:

1. the **exact click path** — which menu item, then how far down the page ("Warranty, then the very bottom right-hand column");
2. a **URL they can paste**, as a fallback, not as the only route;
3. a **screenshot with the element outlined** — inject an outline and a highlight in the page's own coordinates before capturing, so the proof needs no interpretation;
4. the **find-in-page string** ("press Ctrl+F and type deposit") as the fastest route of all.

Then explain *why* it was hidden, because that reason is usually itself a finding worth fixing (no navigation link, broken footer block, a page on the wrong template).
