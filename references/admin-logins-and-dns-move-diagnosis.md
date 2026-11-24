# CMS/host admin logins and "the DNS change didn't work"

Learned on the dealer Motors (Nov 2026): a domain moved but the site stayed down, and the client's own
admin logins were the only way to settle it. Two separate lessons.

## 1. Driving someone else's admin panel from this machine

- **`browser_exec` with `local=true` works on the iMac** and drives Woody's real Chrome profile
  (cookies and all). Use it before falling back to curl when a task needs a logged-in session.
- **`browser_vault_fill` does not work here.** Handed the `browser_exec` tab it returns
  `page_session_unavailable` — reliably, even immediately after `ensure_real_tab()` and a fresh
  navigation. Do not build a plan around it. Credentials saved via `browser_vault_save_login` are
  stored correctly; it is the tab hand-off that fails.
- **Anything needing a human — password entry, Cloudflare/Turnstile, 2FA — has to happen on the
  machine Woody is sitting at.** He works across an iMac and a travel MacBook. Confirm which first:
  pre-filling a login form on the iMac is useless if he is on the MacBook, and his instructions to
  "type the password in the window" will read as nonsense. Ask which machine, or hand him the click
  path instead of driving it.

## 2. "I changed the A record and it's still not working"

Nine times out of ten the record points at the wrong server. Settle it by curling the **candidate
IP directly with the Host header**, never by waiting on propagation:

```bash
curl -sS -A "$UA" --resolve example.co.uk:80:203.0.113.10 http://example.co.uk/ -D - | head -12
curl -sSk -A "$UA" --resolve example.co.uk:443:203.0.113.10 https://example.co.uk/
echo | openssl s_client -connect 203.0.113.10:443 -servername example.co.uk 2>&1 | head -4
```

Three signatures that the IP is wrong, each seen live on the dealer:

| Symptom | Means |
|---|---|
| `Web Server's Default Page` on HTTP | a shared/virtual host with no vhost for this domain |
| `303 → /login.php`, or `/cpanel`, `/whm` | a hosting control panel, not a website |
| cert `subject=CN=<some other host>` | nothing on that box is configured for this domain |
| `tlsv1 alert internal error` (alert 80) | right box, **no certificate installed** yet |

Then check the *right* IP before telling anyone to change anything — confirm the expected site is
actually there (`platform: hostinger`, `panel: hpanel`, the expected `<title>`, the canonical). A
second, easily-missed failure sits behind the first: DNS corrected, but port 443 handshakes fail and
HTTP does not redirect, while the page's own canonical is `https://…`. Fix order is always
**DNS first, then issue the cert on the host** — the host usually cannot validate until the domain
resolves to it.

Also check for a leftover `_acme-challenge` CNAME aimed at the *old* provider's managed SSL. It is
inert for HTTP-01 but breaks DNS-01 issuance, so delete it when moving hosts.

## 3. Ecwid: the domain setting only works one way

Dealers on Ecwid believe the dashboard can "point the domain at the new server". It cannot.
Ecwid binds a domain **to Ecwid** (it hands you its IP and asks you to point an A record at it);
there is no inverse. Their help centre states it plainly: *"Connected domains are not transferred to
Ecwid. So all domain settings are located in your registrar's account."*

- **Custom domains need the Venture plan or above** — so on those accounts the option genuinely
  exists, which is why the dealer insists it does. Warn them explicitly: connecting it would serve
  the old Ecwid storefront instead of the new site.
- Path when you do need to release one: **Website → Domain** (`my.ecwid.com/#website-domain`) →
  Site address → **Manage** → *disconnect it from your store* → **Disconnect Domain**.
- The store ID is in the embed: `app.ecwid.com/script.js?<storeId>&data_platform=…`. An Ecwid
  "Instant Site" also exists at `store<id>.company.site` and is separately indexable — check it
  before closing a store, because it keeps publishing whatever the catalogue last said.

## 4. Moving a domain: check what else is on it

Before a nameserver move, `dig` the whole record set — **MX, SPF/TXT, and the mail A records**.
On the dealer the MX target was a hostname *inside the same zone* (`mx.dealer-site.co.uk`), so replacing the
zone would have silently killed the domain's email. Also confirm which registrar actually holds it:
a `TUCOWS-CA` tag can sit behind an **iPage** account (both Newfold), and Nominet redacts the
registrant — so "who owns it" usually has to be asked, not looked up.
