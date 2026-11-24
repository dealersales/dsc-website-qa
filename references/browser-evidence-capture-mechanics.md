# Browser evidence-capture mechanics (screenshots, mobile, PDF delivery)

Tool-level quirks that eat time on every QA/audit pass and are invisible until you
lose work to them. Applies to `browser_exec`, the preview pane and report delivery.

## Screenshots: never trust the default path inside a loop

`capture_screenshot()` in `browser_exec` reuses **one** output path per session, so
a loop over N sites leaves you with exactly one image — the last one. Every other
capture is silently overwritten. Always copy to a unique filename immediately:

```python
import os, shutil
ws = os.environ.get("BH_AGENT_WORKSPACE", "/tmp")
shutil.copy(capture_screenshot(), os.path.join(ws, "site_%s.png" % name))
```

Then **look at the images** with `vision_analyze` — cosmetics (hero balance,
palette, crowdedness, what the eye lands on) cannot be inferred from HTML.

## Mobile viewport: use CDP device metrics, not window resizing

`resize_window` does not reliably change the CSS viewport. Force it:

```python
cdp("Emulation.setDeviceMetricsOverride", width=390, height=844,
    deviceScaleFactor=2, mobile=True)
# ... screenshot ...
cdp("Emulation.clearDeviceMetricsOverride")
```

390×844 is the working default for a UK dealer site. Dismiss cookie/consent
banners before capturing, or the shot is a wall of legalese. For React/JS
hamburger menus, dispatch the full mouse sequence
(`pointerdown/mousedown/pointerup/mouseup/click`) via `dispatchEvent` — a bare
`.click()` is often ignored (see `dsc-website-qa` SKILL.md §3).

## Rendered DOM vs static HTML: they disagree, and it matters

Two traps found live in Sep 2026:

- **Alt coverage.** One dealer site showed 96% of images with alt text in the
  raw HTML but **49%** in the rendered DOM — lazy-loaded and JS-injected images
  only exist after render. Report the rendered figure, and say which you measured.
- **Meta descriptions.** Another site's server-rendered source ships the
  placeholder `As Autotrader…` and only fills it in at runtime. Compare raw
  source against the rendered DOM before writing up a metadata finding.

Corollary: confirm any **encoding** finding on raw HTML fetched with `curl` and a
browser User-Agent, at byte level — extraction tools mis-decode UTF-8 and produce
false positives (`weâ€™ve`). A genuine double-encoded apostrophe in a live meta
description *is* a legitimate finding; tool mojibake is not.

Strip the harness status/emoji prefix from `document.title` before quoting a page
title as an SEO finding.

## HTML → PDF: the command writes the file, then hangs

Headless Chrome's `--print-to-pdf` produces the PDF and then never exits, so the
command hits its timeout (exit 124) and looks like a failure. It isn't:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --user-data-dir="$(mktemp -d)" \
  --print-to-pdf="/abs/out.pdf" "file:///abs/report.html"
```

- Always pass `--user-data-dir` (a fresh temp dir) so it can't collide with the
  user's running Chrome profile.
- Run it **in the background** (`background=true`) rather than blocking a
  foreground call on a command that will not return.
- Then verify the artifact instead of trusting the exit code: check
  `%PDF-` header and `/Type /Page` count in Python, and render page 1
  (`qlmanage -t -s 900 -o /tmp/dir report.pdf`, or `pdftoppm -png -r 90 -f 1 -l 1`)
  and view it to confirm the layout isn't broken before delivering.

Write the report as **standalone HTML with its own background/padding** when it is
destined for PDF; an inline chat widget styled with theme tokens has no page chrome
and prints badly.

## A captured page shown as a widget must have its CSS scoped

Showing a reviewer the real screens of a multi-step form (rather than describing them) is
worth doing — serve the saved screens with `python3 -m http.server` and embed each one in
a `::preview{file=…}` widget. But a capture is a **whole document**, and its `<style>`
block redefines `:root` custom properties whose names collide with the host app's own
theme variables — `--accent` among them. An un-scoped embed therefore recolours the
surrounding chat UI as well as the pane, which looks like a styling bug in the app.

- Extract the capture's `<style>` **once** and prefix every selector with a wrapper class
  before embedding: `:root` → `.pane`, `*` → `.pane *`, everything else → `.pane …`.
  Splitting on `}` and re-joining each comma-separated selector list is enough for
  hand-written CSS; skip any `@` rule.
- Keep the captured page's own `background` on the pane — it is part of the artifact being
  shown — but never set one on `body`, and never re-declare the app's theme tokens.
- Neutralise the interactive parts: `pointer-events: none` on inputs, selects and buttons,
  plus a `submit` listener calling `preventDefault()`. A preview that POSTs to a dev server
  is a broken tab, and one that silently navigates loses the other screens.
- Verify the scoping rather than assuming it: grep the built file for a bare `^:root{`.
  One match means the leak is live.

Same rule for a captured screen used as evidence in a report figure — the page keeps its
own palette, and nothing of it escapes into the document around it.

## When the harness reports Chromium missing

`agent-browser install` answering *"✓ Chrome … is already installed"* is **not** evidence
that the harness will start. Hermes' readiness gate
(`tools/browser_tool_install.py::_chromium_installed`) checks, in order:
`AGENT_BROWSER_EXECUTABLE_PATH` → a `google-chrome` / `chromium` / `chrome` binary on `PATH`
→ **Playwright's cache** (`$PLAYWRIGHT_BROWSERS_PATH`, `~/.cache/ms-playwright`,
`~/Library/Caches/ms-playwright`) for a `chromium-*` directory. It never looks in
`~/.agent-browser/browsers/`, which is exactly where `agent-browser install` *and*
`hermes tools post-setup agent_browser` put their Chrome-for-Testing builds. Both install
paths therefore report success while the tool keeps refusing to start, and the error's own
suggested remedy (`npx agent-browser install --with-deps`) cannot satisfy the check.

Fix — point the first check at a real binary:

```bash
ls ~/.agent-browser/browsers/                     # find the installed version
hermes config set AGENT_BROWSER_EXECUTABLE_PATH \
  "$HOME/.agent-browser/browsers/<chrome-version>/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
```

`hermes config set` routes this env-read key into the profile `.env`. Verify in a **fresh
process**, because the running one caches the answer:

```bash
cd ~/.hermes/hermes-agent && ./venv/bin/python -c "import sys;sys.path.insert(0,'.');\
from tools.browser_tool_install import _chromium_installed as c; print(c())"
```

Then **restart the backend**: `_cached_chromium_installed` is a module-level global and the
registry's `check_fn` results are TTL-cached process-wide, so a brand-new session in the same
process keeps reporting missing. Restarting the backend ends the current session — say so, do
the config fix and the fresh-process verification, and let the user choose when.

Until that restart lands, the CDP fallback in
`dsc-seo-audit` → `references/mobile-experience-audit.md` §3 needs no browser install at all.
Do not spend a session reinstalling — diagnose the gate first, and keep collecting evidence
through the fallback driver.

## Before reporting a Hermes failure upstream — search first

A Hermes tooling failure that looks like a fresh bug is often already reported, with a fix
in flight. **Search the repo's issues *and* pull requests for the exact error string before
drafting anything**, and read the comments — the thread usually already contains part of
your diagnosis, and a duplicate costs the maintainers a triage and signals you didn't look.

The browser readiness gate is the worked example: the symptom reads like a local install
problem, but the tracker already held an open report, a closed-unmerged fix and an open
replacement. When that happens:

- **Contribute a comment, not a new issue** — and add only what the thread lacks (the
  resolution route you hit, the hook that reports success without satisfying the check, the
  second condition the fix needs, a platform data point). Keep it to those additions.
- **Say which parts the open fix PR does and does not cover**, and offer a reproduction on
  your platform — that is what makes a comment useful rather than sympathetic.
- **Match the repo's own issue template** if you do file, and leave the debug bundle
  (`hermes debug share`) for the user to run: it uploads config and logs, so it is their
  call, not yours.
- The profile digest carries the live issue and PR numbers; the rule here is the search,
  not the identifiers.

## Sites you cannot load

Some hosts refuse the connection outright (TLS handshake refused / timeout, seen
on carplanet.co.uk Sep 2026). Record them as **not reviewed** and say why — never
describe a page you could not inspect, and never let a gap be filled from another
site's figures. The same rule applies to performance claims: measure every site in
the same browser session and label the numbers indicative, not lab-grade; a cached
transfer size is not page weight.
