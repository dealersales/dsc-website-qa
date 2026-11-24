# Domain migration and IPS tags

A dealer leaving one web company for another brings a **domain estate**, not a domain. The
build can be finished and still be unable to launch because nobody has mapped who holds what,
or because the instruction sent to the dealer describes the wrong kind of change. Work the
estate out before a canonical domain is chosen, because every URL on the site derives from it.

## 1. Get the client's own list, not just the handover list

The brief names the domains DSC intends to point. The dealer's own reply names the domains
they actually own, which is routinely a superset — a handover listing three grew to seven once
the client replied, including a pair registered only weeks earlier. Pull the client's own
message out of the thread and diff it against the brief before planning anything.

## 2. Enumerate the estate and its registrars

```bash
whois -h whois.nic.uk example.co.uk     # .uk — name the Nominet server
whois example.com                       # .com — the default whois server is correct
dig +short A  example.co.uk             # is it resolving, and to which host?
dig +short NS example.co.uk             # who runs its DNS?
dig +short MX example.co.uk             # does it carry mail? (a GBP-verification dependency)
```

**On macOS a bare `whois example.co.uk` returns only the IANA TLD stub** — a block of
Nominet's own address and nothing about the domain, which reads as "no record". For `.uk`,
address the registry directly with `-h whois.nic.uk`. Third-party RDAP aggregators are
inconsistent for the `.uk` registry; go straight to `whois`.

The output gives you the **Registrar** and, in the same field, its **Tag** — the IPS tag. That
tag is the whole migration plan for a `.uk` domain.

**The tag is the only answer to "has it moved?" — not anyone's message, including yours.** A
coordinator relaying "the URL is now available" or "AutoTrader have released it" is repeating what
he was told; the register is what happened. Check before drafting a reply that depends on it, and
say which you checked. Two independent reads, because whois output is easy to misread:

```bash
whois -h whois.nic.uk example.co.uk | grep -iE "tag =|last updated"
curl -sS https://rdap.nominet.uk/uk/domain/example.co.uk | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(d['status'], [e.get('handle') for e in d['entities'] if 'registrar' in e.get('roles',[])])
print([(e['eventAction'], e['eventDate']) for e in d['events']])"
```

RDAP gives the events as a list rather than a date line, so it is the cleaner evidence for a report.
**`last changed` is the proof of action.** A record whose last change predates the notice has had
nothing done to it, whatever the thread says — a tag change, a transfer or a nameserver edit each
move that date. Quote it with the check date ("last changed 14 Sep 2025, checked 26 Oct 2026") and
the claim that the domain is ready stops being arguable. The same read confirms the cutover
later: the tag becomes `NAMECHEAP-INC` and `last changed` moves to that day.

**A released tag is not a pointed domain.** After the tag changes, the nameservers still have to
move, and until they do `www` keeps CNAMEing to the outgoing provider. Verify the whole chain —
tag, NS, A/CNAME, and both apex and `www` — before telling anyone the site is live.

**A wildcard makes every invented subdomain resolve, so do not read a hit as a real host.**
Where `*.example.co.uk` is set, `shop.`, `store.` and `zzz-not-a-real-subdomain` all answer with
the apex IP — which looks like a hidden store or a second site and is neither. Test with a label
that cannot exist before recording a subdomain:

```bash
dig +short qwerty12345.example.co.uk      # any answer = wildcard, not a host
```

Same trap one layer up: `www` answering is not evidence of a separate site either — check whether
it is a CNAME to the apex, and whether each host self-canonicalises, before calling it a
duplicate-content finding.

## 3. IPS tag versus nameservers — they are different instructions

| | .uk domains | .com / .net domains |
|---|---|---|
| Move between registrars | **IPS tag** change, requested by the gaining registrar | **Registrar transfer** with an EPP/auth code from the losing registrar |
| Point the site at a host | Nameserver change | Nameserver change |

The two are separate, separately authorised steps, and conflating them is the commonest reason
a dealer stalls. **`NAMECHEAP-INC` is an IPS tag, not a nameserver.** Instructions that tell the
dealer to "point the URL to our nameserver" and then name a tag are unactionable — the dealer
asks their host, the host says that is not a nameserver, and nothing moves. Send it as two
lines: change the IPS tag to `<TAG>`, and once the registration has moved, set the nameservers
to the values you give.

`.com`/`.net` domains have no IPS tag at all, so a notice to the outgoing company will not
move them: the client must trigger a registrar transfer and supply the auth code. A dealer
cannot delegate this.

## 4. A batch usually spans several registrars

One dealer's seven domains sat with three registrars (Tucows, eNom, GoDaddy/Wild West). Each
needs its own authorisation from the client, so "we have given notice to the existing company"
moves none of them by itself. Tabulate domain → registrar → tag → expiry, and mark which need
the client to act.

Watch the **expiry dates** while you are in there. A domain that has just been registered
(weeks old, expiry in twelve months) is a new registration, often bought for the new site by
the outgoing supplier — worth confirming who the registrant actually is before it becomes
dependent infrastructure.

**The registrant is not readable from public whois, and the registrar of record is often not the
account you need.** Nominet redacts the registrant name and address for `.uk`, so whois gives you
the tag and the dates and nothing about ownership. That single unknown decides the whole plan:
whether the client can authorise the tag change themselves, or whether the outgoing agency has to
release it — and an agency that has just been dismissed is not a reliable release mechanism. Get
the answer from the client ("is the domain in your own hosting account, or theirs?") or from the
host, not from a whois lookup.

**Check whether the registrar of record is wholesale before you look for a login.** Tucows and
eNom are wholesale registrars: their tag appears in whois, but the domain sits in a *reseller's*
account and there is no Tucows login to find. Follow the nameservers and the hosting IP to the
reseller — `ns1/ns2.ipage.com` with an A record inside Newfold Digital's range means an **iPage**
account, tagged through Tucows. Name the reseller in the handover, because that is who the client
has to ring.

## 5. Choose the canonical host before building on it

N domains cannot all be the site's home. Pick **one canonical** and 301 the rest to it, or the
launch splits its signals across the whole estate.

Prefer, in order:

1. the domain the client calls their main address;
2. the one with the longest registration history (age, and any links already pointing at it);
3. the one that is currently live and in use — but treat that as a risk, not a vote: the domain
   carrying real nameservers and a working store is the migration's single point of breakage,
   so it is the one to touch last and to have a rollback for.

Settle the apex-vs-`www` question at the same time and make the non-canonical form 301, not a
200 copy: two hosts each self-canonicalising is a duplicate-content finding in its own right.

The canonical choice is a client decision, not an agent guess — surface it as the one blocking
question, with a recommendation, and hold the sitemap/canonical build until it is answered.

## 6. Keep the estate out of the client-facing report

Registrar tags, EPP codes and nameserver values are build/server material for the handover
message, not copy for the dealer. The dealer-facing line is which domains move, who they have
to authorise, and by when.

**The instruction usually travels through a coordinator, so write it for the relay.** An account
manager forwards it to the dealer, and the dealer acts on it — so a WhatsApp or email draft needs
two things a technical note does not:

- **Lead with the consequence, not the mechanism.** "Don't connect the domain in Ecwid — it would
  replace the new website with the old shop" lands. "It binds the domain to the platform's IP" does
  not. The dealer needs to know what happens to his business, not how DNS works.
- **Supply the forward-ready version as well as the message to the coordinator** — a short block
  addressed to the dealer, in his language, that can be pasted on without editing. Keep it to three
  numbered actions, each with an owner and a deadline.

**One action can double as the ownership test.** Asking the client to request the change from the
current host *in his own name* either starts the clock, or fails — and a host refusing a request
from the registrant is itself the answer to "whose account is this", obtained without putting an
awkward question to an agency that has just been dismissed. Build the request that way rather than
asking about ownership separately.


## 7. A SaaS store is a separate control point, not the host

When the client or the handover brief says "the current URL is through <platform>" — Ecwid,
Shopify, Wix, Squarespace, BigCommerce — **verify what actually answers on the domain before
planning around it.** A merchant dashboard is where the *catalogue* is managed; it is often not
where the *site* is served. On one dealer the domain resolved to a hosting company's shared IP
serving an Adobe Muse site, with the shop platform embedded into one page by a plugin — so
"change the URL in the dashboard", which the platform's own support had advised, would have
moved nothing.

Identify the store and its binding from the live page, not the dashboard:

```bash
dig +noall +answer A example.co.uk && dig +noall +answer CNAME www.example.co.uk
curl -sS -A "$UA" https://example.co.uk/ | grep -oiE "(ecwid|shopify|wix|squarespace|bigcommerce)[^\"'<> ]{0,60}" | sort -u
# the platform's script include usually carries the account id:
#   app.ecwid.com/script.js?<STORE_ID>&data_platform=…
#   cdn.shopify.com/s/files/…/<SHOP_ID>/
```

The store id is the thing the client needs in order to act, and it is worth recording even when
the platform is being retired.

**Map every control point separately.** A migration with a store in it has four, and each has a
different owner:

| Control point | What lives there | Who can change it |
|---|---|---|
| DNS registrar | IPS tag (`.uk`) or EPP transfer (`.com`), then the A/CNAME record | the client, via the losing registrar |
| The site host | the pages actually served on the domain | the outgoing agency |
| The SaaS store | catalogue, and the store's **own domain binding** | whoever holds the merchant login |
| The platform's free hostname | a live public storefront, e.g. `<storeid>.company.site` | the same merchant login |

**Release the store's domain binding before the DNS moves, not after.** The binding is a
setting in the merchant dashboard and it is not a nameserver record: leaving it pointed at the
dealer's domain while the new site is pointed at the same hostname makes the two contend for
it. Sequence the cutover as: release the binding → change the IPS tag / registrar → repoint the
A record → upload.

**The setting is one-way, and the dealer must not be left to experiment in it.** A merchant
dashboard can bind a domain *to* the platform; it cannot point a domain *away* to somebody else's
server. The platform's own connection instructions tell you to create an A record pointing at
**its** IP — so a well-meaning client trying to "point it at the new server" from that screen
will succeed in pointing it at the old storefront instead, replacing the new site with a stale
catalogue. Say this explicitly to whoever is relaying instructions to the dealer.

**If the domain screen is missing entirely, suspect the plan tier before the permissions.** Custom
domains are gated on the paid tiers of most of these platforms (Ecwid: Venture/Business/Unlimited),
so a free or embedded store shows no domain section to find. That is a different answer from "you
do not have access", and it is worth stating both when the client reports they cannot see it.

**Treat the platform's free hostname as an indexable duplicate site in its own right.** Fetch
it, read its `sitemap.xml` and `meta robots`, and audit its products the way you would the main
site. They are frequently stale in a way the main site is not: one live instant-site carried
eleven products, six of them named "Now Sold" and still published at `£0.00` inside `Product`
structured data with `"availability": "http://schema.org/InStock"` — Google-eligible rich
results offering a sold car at nothing. That is a consumer-protection finding against the
*outgoing* site, so raise it rather than only planning its retirement.

**Two stock sources is a data-integrity risk, not just a migration step.** The store's
catalogue and the new site's feed are independent. If the dealer keeps adding cars in the old
merchant panel after cutover, the new site silently will not show them. Agree a cutover date
and confirm in writing that stock moves to the new admin in one direction only.

**Carry both URL shapes into the redirect map.** The embedded store's links are query-string
forms on the host page (`used-cars.html?store-page=…&category=0`) while the instant site's
products are path forms on the platform hostname (`/<Product>-p<id>`). Both are indexable now,
so both need 301s to the stock page, not one family.

**Before the store closes, check where its free hostname is linked.** It dies with the account,
and it is commonly sitting in the Google Business Profile website field, a marketplace dealer
page, or a social profile. Sweep those first.

## 8. The mail layer moves with the nameserver zone

A nameserver change does not just repoint the website. It replaces the whole zone, and any MX or
SPF record that is not recreated in the new one stops existing at the moment of cutover.

```bash
dig +short MX  example.co.uk
dig +short TXT example.co.uk | grep spf
```

Two traps make this worse than it looks:

- **An in-zone mail host disappears with the zone.** `MX 30 mx.example.co.uk` where `mx` is a
  record *inside the same domain* resolves only because the old zone is live. Change the
  nameservers and the exchanger has no address — mail fails even if you remembered to copy the MX
  line, because the A record it points at is gone too.
- **The mailbox may live in the hosting account being cancelled.** Where mail is served by the
  same host as the site (iPage/Newfold, cPanel hosts), closing the hosting account as part of the
  switch-off takes the mailboxes with it. The website move and the email decision are the same
  decision, and the email half is the one nobody raises.

So before the tag changes: establish whether any address on the domain is in use (`info@`,
`sales@`, `accounts@`) and **where it is published** — AutoTrader, Companies House, invoices, the
GBP. A dealer whose day-to-day address is a Gmail proves nothing about the domain. Then either
recreate MX/SPF/DKIM at the new registrar and migrate the mailboxes deliberately, or move the
address to a provider first and only then cut over. Recreate the records in the same change as
A/CNAME rather than after it, and tighten a `?all` SPF policy to `-all` while you are in there —
`?all` means anyone can spoof the domain.
