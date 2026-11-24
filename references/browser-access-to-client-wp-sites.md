# Getting into a client WordPress site's admin

Learned on Four Plus 4 (SiteGround), Sep 2026. Establish **which route you actually have**
before promising a client changes — each fails differently and set-up time dominates.

## Ranked routes

| Route | How | Notes |
|-------|-----|-------|
| **SSH + WP-CLI** | `ssh -p 18765 -i ~/.ssh/<key> <user>@<server>.siteground.biz` | Most reliable, immune to bot protection. See `references/siteground-ssh-wp-cli-access.md`. |
| **REST from inside a logged-in browser tab** | `fetch('/wp-json/wp/v2/…', {headers:{'X-WP-Nonce': window.wpApiSettings.nonce}})` | The workhorse. Same-origin, so it rides the browser's own challenge cookie and works on hosts that block external REST entirely. |
| **The user's own logged-in Chrome, via the `computer_use` typed-browser rung** | bind `cua_browser_state` to the exact `(pid, window_id)` | Needs `computer_use.grant_existing_profile: true` — two traps below. |
| **The `browser_exec` harness** | `browser_exec` | Runs its **own** Chrome profile, so the user's existing logins are NOT available to it. Fine on unprotected sites; stalls on a bot-challenge page. |

Clients often assume "I'm logged in in my browser, just use that". It is worth saying
explicitly which of the four you are actually using, because only the third touches their
session.

## Two traps with the existing-profile grant

1. **It is per profile.** A plain `hermes config set computer_use.grant_existing_profile true`
   writes the *default* profile's config. For a session running profile `dsc`:
   ```bash
   HERMES_HOME=/Users/<user>/.hermes/profiles/dsc hermes config set computer_use.grant_existing_profile true
   ```
   Cross-check which config is in play with `hermes config get computer_use.grant_existing_profile`
   and `hermes config path` (run from the session, so it resolves the session's profile).
2. **It is read when the runtime starts.** Setting it has no effect until the Hermes
   app/runtime restarts — expect at least one refusal after the config change, and tell the
   user a restart is needed rather than letting them think the command failed.

**Never self-grant this permission.** It is the user's one-time opt-in; ask them to run the
command and explain the restart.

## The harness browser is shared

`browser_exec` sessions (`default`, and named ones) live in one persistent browser shared
across profiles and concurrent sessions, so a tab can change site underneath you. Diagnose
with:

```bash
/Users/<user>/.local/share/uv/tools/browser-use/bin/browser-harness --doctor
```

It lists each active connection and the page it is sitting on. If the daemon wedges
(`Runtime.evaluate timed out`, `TimeoutError` from `_ipc.request`), `pkill -f
browser_harness.daemon` and retry — the harness respawns. If Chrome then raises an
**"Allow remote debugging?"** sheet, that cannot be auto-accepted: the user clicks Allow, or
the app launching the harness needs macOS Accessibility permission (the harness's own
`mac-approve` command names the app that needs it).

## Order of operations worth following

1. Confirm the domain/admin you can reach, and note *which* route.
2. Make the changes.
3. Verify the rendered front end, not just the stored data.
4. Stop hitting the site with unrelated fetch/curl traffic — on hosts with bot protection
   your own verification volume can trip a challenge that locks you out mid-job.

## The user's Chrome is a moving target

Binding to the user's profile is not the same as pinning their browser. They keep working in it
while you do — switching tabs, opening another site — so the window you bound to can be showing
something else by your next action, and a click aimed at an element tree captured a turn earlier
lands on an unrelated page. Re-capture the current window and its element tree immediately before
each action, derive coordinates from the bounds that capture returns (native desktop space, not
screenshot pixels), and treat "the page moved under me" as the expected case rather than a bug.

Two consequences to plan around:

- **Reading is cheap; writing through the UI is not.** Locating a widget in a logged-in tab and
  printing its exact JSON costs a turn or two. Grinding the Elementor editor's UI, or driving the
  address bar with desktop keystrokes, costs many turns and can end with the site down — see
  `references/site-down-triage.md`.
- **When none of the four routes is available, the deliverable is a precise instruction, not more
  attempts.** Stop and hand Woody the pointer he can act on in one pass: the post ID and its type,
  the widget type and element id, the exact old and new string, and the click path. A client site
  left broken while tool routes are exhausted is strictly worse than a two-line handover, and on a
  site already 500ing every extra request risks the IP-level challenge that would have blocked the
  fix itself.
