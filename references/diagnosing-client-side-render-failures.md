# When a widget renders nothing but the HTML looks fine

For "the form/booking widget/popup is there in the source but nothing appears on the page".
From Zagros Tyre & Auto Centre (Sep 2026): the MetForm contact form had **never received a
single entry** and had never rendered at all.

## The exception-isolation trap (this is usually it)

**jQuery does NOT isolate event-handler exceptions.** If one handler bound to an event throws,
jQuery aborts the dispatch and every handler bound *after* it silently never runs.

That is how you get a total, invisible failure: a plugin binds to Elementor's
`elementor/frontend/init` during parsing, throws `Cannot read properties of undefined
(reading 'hooks')` because `elementorFrontend` does not exist yet, and takes out Elementor's own
initialisation *and* every later handler — including MetForm's form mount.

Symptoms that should make you suspect this:

- Nothing renders, but `.elementor-initialized` count is **0** across the whole page.
- An unrelated plugin's frontend script logs an `errorText`/`ReferenceError` early.
- Re-firing the event yourself throws the same error from the same file.

**Diagnose by elimination, not by reading code.** In a real browser, block suspect scripts one at
a time and re-measure. With CDP:

```python
cmd('Network.setBlockedURLs', urls=['*jet-sticky-frontend.js*'])   # then reload and re-count
```

A single blocked cosmetic plugin took the form from `forms=0` to `forms=1, inputs=8`. Then check
whether the plugin is actually used at all before choosing a fix: grep the Elementor data for its
enable key (`"jet_sticky_section_sticky":"yes"`). Here it held only *styling for the sticky
state* — no element had sticky enabled — so it was dead weight and deactivating it cost nothing.

## MetForm specifics

- The form is **100% client-rendered**. The server emits an empty mount div plus a
  `<script type="text/mf" class="mf-template">` holding an htm template literal.
- The mount is registered on `jQuery(window).on('elementor/frontend/init', ...)`, which then calls
  `elementorFrontend.hooks.addAction('frontend/element_ready/metform.default', jt)`.
- `mf.postType` is `page` on a normal page, so the `'metform-form'` branch is not taken.
- The app does **not** need a REST call to draw the form. `POST /wp-json/metform/v1/forms/views/{id}`
  is only a view counter, and `post_views()` returns `null` (empty 200) unless counting is on —
  an empty body there is normal and is NOT the bug.
- A `mf-recaptcha` field with no keys configured renders `data-sitekey="dummy"` and Google shows
  "ERROR for site owner: Invalid site key". Remove the field (or supply real keys) or submission
  cannot pass validation. This is a second, independent defect — fix both.

## Don't trust a single renderer

Firecrawl's markdown render showed no form and I concluded it was broken — but it also cannot show
client-rendered form fields reliably. Confirm a *negative* with a real browser before acting on it.
