# SiteGround SSH — connection limits and cooldowns

Companion to `siteground-ssh-wp-cli-access.md` (access recipe, key selection,
WP-CLI recipes). This file is about the **transport**, because it bit us mid-job.

## The behaviour: bursts get you firewalled

SiteGround firewalls SSH port **18765** after a rapid burst of
connect/disconnect cycles. The failure is not a key or auth error — the
connection simply stops being answered:

```
ssh: connect to host <account>.siteground.biz port 18765: Operation timed out
```

Once this fires, it stays locked for a cooldown period regardless of which key
you use. It clears on its own; retrying hard makes the wait no shorter.

**Symptom sequence seen in practice:** half a dozen successful, fast
authenticated commands, then every subsequent connect times out — including
plain TCP checks (`nc -z <host> 18765` → non-zero). Nothing about the account or
key changed.

## The discipline

- **One connection, one scripted payload.** Do all your reads/writes in a single
  SSH invocation (heredoc or a script you pipe over), not a loop that connects
  once per URL/field. A `for u in ...; do ssh ...; done` loop is the fastest way
  to trigger the firewall.
- **Do the key-discovery sweep once, early, then stick to the working key.**
  Testing three keys costs three connections; do it deliberately, not per task.
- **Batch follow-up verification too** — fold the "fetch the page from the
  server to confirm the render" step into the same session if you can.
- **If you do get locked out: wait.** Give it several minutes, check cheaply with
  `nc -z`, and only then retry. Do not re-run the same failing command in a tight
  loop.
- **Don't diagnose a timeout as an auth problem.** `Permission denied
  (publickey)` = key not registered; `Operation timed out` = firewall/cooldown.
  They need opposite responses (fix the key vs. wait).

## Fallback while locked out

The browser route (see `browser-access-to-client-wp-sites.md`) does not use port
18765 and can run while SSH is cooling down. Note that cua-driver reads
`computer_use.grant_existing_profile` **at startup** — if it was flipped on after
the app launched, the running app won't honour it until restarted.
