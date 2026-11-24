# Deploy-window recheck & live-vs-index checks

Written up from the a dealer Car Sales QA (<dealer-domain>, Sep 2026) — a
the platform/DSC dealer build that was still being pushed to Hostinger while the audit
ran. The findings changed under the auditor, which is the whole lesson.

## The problem: auditing through a deployment

The developer was uploading code and switching DNS while the pass was in flight.
Facts that were true at 10:00 were false by 12:00:

| Fact | First check | Later check |
|------|-------------|-------------|
| HTTPS | TLS handshake failed (alert 80), no cert | Let's Encrypt cert valid, HTTP→HTTPS 301 |
| Canonical / `og:url` / JSON-LD `@id` | `http://` | `https://` |
| Vehicle prices | e.g. £7899 | £7499 |
| robots.txt `Sitemap:` line | pointed at an `https://` sitemap that didn't resolve | matched the live scheme |

None of these were fixed *by* the auditor — they were the developer landing
changes. Reporting the 10:00 snapshot would have produced a report full of
already-false findings.

## The discipline

1. **Record the verification timestamp** for anything deploy-sensitive and put it
   in the report ("HTTPS verified 07 Sep, 15:52 BST").
2. **Re-check these three at the END of every pass**, cheaply, in one batch:
   - `curl -sI https://<domain>/` → status + `%{ssl_verify_result}` (0 = OK)
   - canonical / `og:url` scheme on the homepage + one inner page
   - a price spot-check on 2–3 listings vs the same listings in the feed/footer
3. **Prefer the local clock + a stated timezone.** Server clocks on shared
   hosting can read a different date from the Mac — don't compare raw timestamps
   across machines to reason about "what changed when".
4. **Fetch twice if the site is mid-push.** A single fetch is a point sample; two
   fetches minutes apart expose churn (prices, counts, schemes).

## Live HTML vs the search index — they disagree

The live About page was clean, but Google's snippet for a **legacy permalink**
still carried another dealership's name ("…At Blakewater Cars, our mission is
simple…"). The old WordPress-style URLs had been replaced by flat `.php` pages:

```
/about-us/        → 404   (live page is /about.php)
/sell-your-car/   → 404   (live page is /sell.php)
/wp-json/         → 404
```

So a "wrong dealership name" finding can be entirely in the index. Sequence:

1. Grep the live HTML for known wrong names — rule them in/out on the live site.
2. Check the search engine (`site:<domain>` style queries, plus the exact legacy
   URL) for snippets carrying the wrong name.
3. Check whether legacy permalink patterns still resolve or 404 **without a 301**.
4. Recommend: 301s from old → new URLs, then a GSC URL-inspection / re-crawl
   request. Flag it to the client — a competitor's name in your snippet is a
   brand problem, not just a rankings one.

## Dead-CTA sweep

`href="#"` on an action button is easy to miss because the button *looks* fine.
On this build every car card had a **Finance** button pointing at `href="#"` —
no finance route existed anywhere. The listing was otherwise correct, so a
page-level read passed it.

```bash
# from the saved homepage HTML
grep -o 'href="[^"]*"' page.html | sort | uniq -c | sort -rn | head -30
# then confirm each named destination actually exists
```

Check the theme/nav CTAs (View Showroom, Contact, Finance, Get a Valuation) and
verify the target page returns 200.

## NAP — cross-check against AutoTrader, not just on-site

On-site NAP was internally consistent (footer, JSON-LD, llms.txt all agreed), so
an on-site-only check passes. But the AutoTrader dealer page listed a different
street number for the same postcode:

- Website: `Unit 4, 10 Chancellor Street, Leeds, LS6 2TE`
- AutoTrader: `5 Chancellor Street, Leeds, LS6 2TE`
- Companies House registered office: a different address entirely (often the
  legal office, which legitimately differs from the trading address)

Treat each external source as its own finding. Registered office ≠ trading
address — don't raise the Companies House entry as a discrepancy without
checking whether it's just the legal address.
