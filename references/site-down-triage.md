# When a client site is unreachable

A live client site being down is an emergency: the client is losing enquiries by the hour and every
further action has to be deliberate. Work the probes in order, record the codes, then work the
restore levers in order.

Two shapes, and they need different ladders:

- **The server answers with an error** (`500`, a white screen) — the site is up and failing. Work the
  triage table below, then the restore levers.
- **Nothing answers because the name has no address** — the domain does not resolve at all. No PHP
  lever will touch that; go straight to *When the domain itself does not resolve* below.

## Triage — read the shape of the failure before touching anything

| Probe | Result seen | What it tells you |
|---|---|---|
| `curl -sI https://CLIENT/` | `500`, `x-httpd-modphp: 1` | PHP is fataling at runtime — not DNS, not a hosting outage, not cache |
| `curl -s -o /dev/null -w '%{http_code}' https://CLIENT/readme.html` | `200` | A static file at the site root still serves, so the web server and the WordPress file tree are intact — the fault is purely PHP-side at runtime. Rules out a host outage, a broken deploy and a missing document root in one request |
| `curl -s -o /dev/null -w '%{http_code}' https://CLIENT/wp-admin/` | `500`, or `403` on a bot-gated host | `500` means the fatal happens during bootstrap or plugin load and wp-admin is dead too, so **you cannot log in to fix this from the browser**. A `403` here is *not* a second, milder fault — on SiteGround the WAF answers `/wp-admin/` before PHP runs (response carries `x-proxy-cache-info`, no `x-httpd-modphp`), so do not read it as "wp-admin survived" or chase it as a separate problem. Judge health from the frontend |
| `curl -s -o /dev/null -w '%{http_code}' https://CLIENT/wp-json/` | `500` | Confirms it is the site, not your tooling — and rules REST out as a rescue route for now |
| `curl -s -o /dev/null -w '%{http_code}' https://CLIENT/wp-content/debug.log` | `403`, not `404` | The log **exists** but is not web-servable. 403 vs 404 is the tell. You must read it over SSH or via the host file manager — curl will never return its contents |
| `curl -s https://CLIENT/wp-login.php?action=recovery_mode` | the same error page | The bare action is not the recovery URL. WordPress mails a per-site keyed link to `admin_email` |
| The **keyed** link from that email, fetched by anything other than a browser | `Recovery Mode not initialized` | The link initialises a restricted session through wp-login, so a bare `curl` or page-extraction fetch can never bring it up — and it is a one-shot credential. **Open it in the browser that holds the wp-login session; never spend it on a scripted fetch to "see if it works"** |

Frontend **and** wp-admin failing together is the signature of a bootstrap-level fatal. One page
failing while the rest return 200 is a template or widget problem — a different, much smaller job.

## When the domain itself does not resolve

Two failure shapes, and the difference is the whole diagnosis:

- **NXDOMAIN** — the name does not exist in the zone. The record was never created, or the
  registration has lapsed.
- **NOERROR with an empty answer (NODATA)** — the zone exists, the record is missing. This is the
  handover and migration signature: the delegation and the SOA both survive while every address
  record is gone, which is what a zone reset or a failed records import looks like.

Work the ladder in order. Each step rules out a cause closer to you than the last, so do not skip to
the end and do not stop at the first empty answer:

```bash
# 1. Local resolver — usually a cache, never evidence on its own
dig +short www.DOMAIN A

# 2. Public resolvers — three agreeing empties rules out one resolver's cache
for r in 8.8.8.8 1.1.1.1 9.9.9.9; do dig +short @$r www.DOMAIN A; done

# 3. DoH JSON — reads the answer CODE, which `dig +short` hides.
#    "Status":3 is NXDOMAIN; "Status":0 with no Answer key is NODATA.
#    This is also the vantage point that survives a VPN egress or a bot wall.
curl -s -H 'accept: application/dns-json' \
  "https://cloudflare-dns.com/dns-query?name=www.DOMAIN&type=A"

# 4. The authoritative nameservers, queried directly — THE step that proves the
#    zone itself is empty rather than your resolver being wrong
Ns=$(dig +short NS DOMAIN | head -2); for ns in $Ns; do dig +short @$ns www.DOMAIN A; done

# 5. Read the SOA. An SOA that answers while every other type is empty means the
#    zone is live at the nameservers and has been emptied of records
dig +short @$ns DOMAIN SOA

# 6. Registration — ACTIVE with a future expiry rules out a lapsed domain
whois DOMAIN | grep -i 'status\|expir\|registrar'
```

**Sweep for what else is broken, so you can report the blast radius rather than only the headline:**

```bash
for t in A AAAA MX TXT CAA; do dig +short @$ns DOMAIN $t; done
for s in mail ftp cpanel webmail autodiscover smtp pop imap; do dig +short @$ns $s.DOMAIN; done
```

**An empty MX means the domain's email is down as well.** Report that as a second casualty in its
own right — it is a different consequence from the website being unreachable, and the dealer may
never notice until an enquiry bounces.

### Dating the change before you describe it

"Your website is down" and "someone is changing this right now, stop them" are different messages
and get different responses. Compare the current state against any earlier successful fetch from the
same session: a domain that returned `200` an hour ago and resolves to nothing now is being worked
on live. Take the timestamp from `date`, and re-confirm resolution at write-up time — the state moved
between the probe and the message on one build, and the alert has to match the moment it is sent.

### Fixing it

Where the nameservers are a managed DNS provider (Cloudflare and similar), **the audit log is the
fastest route to what was deleted, when, and by whom.** You cannot read it from here: name the log,
tell Woody, and let him or the account holder open it. Do not guess at the records that were there —
restoring a wrong address costs another TTL of downtime.

**Sequence the rebuild, not just the restore.** Do not point a go-live domain at a new build until
the build's canonical base and its staging `noindex` are fixed — otherwise you trade a clean outage
for a site that de-indexes itself on day one (see `dsc-seo-audit` §4). Fixing DNS first and the build
second is the order that leaves the client worse off.

## When the name resolves but nothing is listening

The third shape, and the one a DNS check reports as healthy: the domain resolves, public resolvers
agree, the nameservers answer — and the machine at that address is gone. A DNS-only check says "all
resolving, all good" while the client has nothing at all.

The discriminator is the **TCP connect time**, not the status code:

```bash
curl -sS -o /dev/null -m 20 -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" -A "$UA" "https://DOMAIN/"
```

- **`http=000` with `connect=0.000000s`** — the connection never opened. Dead or firewalled host.
- **`http=000` with `connect` burning seconds** — reachable but unresponsive, or a path problem.
  Re-test from a second vantage before believing it.

**Sweep the ports before calling a host dead.** A mail server legitimately has 143/993 closed to the
public; a host with *nothing* open on `22 25 80 143 443 465 587 993` is a stopped or removed instance.
That difference decides whether you are looking at a firewall or a dead machine:

```bash
python3 - <<'EOF'
import socket
ip = "IP"
for p in [22, 25, 80, 143, 443, 465, 587, 993]:
    s = socket.socket(); s.settimeout(6)
    try: s.connect((ip, p)); print(p, "OPEN")
    except Exception: print(p, "closed/timeout")
    finally: s.close()
EOF
```

**Classify a batch of alerts by host before generalising.** The estate spans several providers, so a
run of DOWN monitors is usually one or two server faults wearing many names. Test every distinct
address, not a sample — a few healthy domains exonerate only the server those few sit on, and
reporting a real outage as a monitoring glitch is the failure that matters here. All the DOWNs on one
IP and all the UPs on another means the alert list is correct and the fault is that server; DOWNs and
UPs interleaved on the *same* host points at the checker or a WAF instead.

## The mail layer: an accepting MX proves less than it looks

`250 Accepted` from the MX means the **filter** is alive and willing to take the message. It says
nothing about whether a mailbox exists behind it — the anti-spam front end accepts at the edge and
decides later, so a dead mailbox server still greets you with 250.

Test the client's own hostname, not just the MX, because that is what their mail client is configured
against:

```bash
dig +short mail.DOMAIN A    # what the client's Outlook/phone connects to
dig +short DOMAIN MX        # the filter in front of it
# then sweep 25/143/993/465/587 on the mail. host
```

- **MX answers, `mail.DOMAIN` does not** — inbound mail is queuing at the filter and nobody can
  collect it. The client's symptom is "email has stopped" and the website may be perfectly fine.
  This is a dead mail server, not a mail-configuration fault: do not go looking at SPF, DKIM or the
  client's password.
- **Both answer** — the mail path is alive at the edge; anything still failing is authentication,
  quota or spam quarantine, which needs mailbox credentials to diagnose.

**Confirm mail is queued, not lost.** A RCPT probe is a standard deliverability check and sends
nothing; a `250` tells the user their messages are being held rather than refused, which changes how
urgent the call they are about to make really is:

```python
import smtplib
s = smtplib.SMTP("mx10.antispam.mailspamprotection.com", 25, timeout=25)
s.ehlo("dsc-check.sales-consultants.com")
s.mail("someone@example.com")
print(s.rcpt("user@DOMAIN"))   # (250, b'Accepted') = queued, not refused
```

**Web and mail fail together when one machine serves both.** A domain's A record and its `mail.`
hostname frequently point at the same VM, so when a client reports email trouble, check the web
address in the same breath — often it is the same dead host, and the report should name both
casualties rather than only the one they happened to notice.

## Restore levers, cheapest and least destructive first

1. **Read `wp-content/debug.log` first** (`tail -100` over SSH). The fatal names the file and the
   line. Guess-and-check while a client site is down is worse than the outage.
2. **Rename the suspect plugin directory** — `wp-content/plugins/<slug>` → `<slug>.off`. WordPress
   silently deactivates a plugin whose folder is missing, so the site boots without it, and renaming
   back restores the previous state with no database edit. Fastest route back to "site up" when the
   offending change is not yet identified.
3. **No SSH and no file access? The client's host control panel is self-serve and faster than
   waiting on support.** SiteGround's Site Tools *Dev Tools* section carries both a File Manager
   (edit `wp-config.php`) and the PHP settings that hold `memory_limit`. Turning the generic white
   screen into a readable error is a two-line paste into `wp-config.php`, above the
   `/* That's all, stop editing! */` line:

   ```php
   define('WP_DEBUG', true);
   define('WP_DISABLE_FATAL_ERROR_HANDLER', true);
   ```

   Give the user the exact click path and the lines to paste — say plainly whether it is a terminal
   command or a web form. Host support is the fallback, not the first ask.
4. **Recovery-mode link from `admin_email`** — check `wp option get admin_email` over SSH rather than
   assuming it is the mailbox you have open; on client sites it frequently is not. The link boots a
   restricted session that can deactivate the offending plugin from wp-admin.
5. **WP-CLI over SSH for everything else** — `wp plugin list`, `wp plugin deactivate <slug>`,
   `wp post meta get <id> _elementor_data` to diff against your snapshot and roll a bad write back
   with `wp post meta update`. **No snapshot? Existing revisions still hold their own
   `_elementor_data`, so a wrecked payload is recoverable** — recipe in
   `references/applying-fixes-via-in-session-rest.md` → "When a payload is already destroyed".

Restore from the snapshot you took before the edit, not from what you believe the original value was.

## Do not

- **Do not keep re-requesting the broken site**, and do not loop on `/wp-json`. On bot-protected hosts
  (SiteGround `sgcaptcha`) repeated requests from one IP escalate to an IP-level challenge that also
  blocks your headless browser — you lose the tools you need for the fix, and the fix window with it.
  Probe once, record the codes, stop.
- **Do not open the Elementor editor on a site that is already 500ing** to "see what changed". It is
  the heaviest operation available and a likely cause.
- **Do not state a cause you have not read in `debug.log`.** "There has been a critical error on this
  website" is WordPress's generic fatal text; on both frontend and wp-admin it is a symptom, not a
  diagnosis. Say what you know and what you still need.
- **Do not probe a 500 with a bare curl User-Agent** — bot-walled hosts 403 that. Use a browser UA and
  read the status code, not just "it failed".

## Documenting it

Log the outage in the client's QA/fix record with the exact probe results, the cause once found, the
lever used, and break-to-restore times. Woody needs that sequence: an unexplained window of downtime
on a client site is a conversation he will have, and the times plus the cause are what make it short.
