# Diagnosing a rendering fault without guessing

Rules for separating a markup or data fault from a rendering one, and for measuring a site you cannot
load yourself.

## CSS is not evidence

- **Read a rendered screenshot before asserting a mechanism.** A stylesheet rule can be completely inert:
  `object-fit` on a `<div>` does nothing (it only applies to replaced elements), and an `aspect-ratio`
  declared in one rule is overridden by a slider library sizing the same element inline. Quoting CSS as
  the cause produced two confident, wrong diagnoses in a row on the same defect.
- **A class name describes intent, not behaviour.** Find which element actually carries the class before
  reasoning from it, and check the property applies to that element type at all.
- **When a client has already sent a screenshot, read it first.** It is the evidence; the stylesheet is a
  hypothesis. The screenshot on disk settled in one look what two rounds of CSS reading got wrong.

## Establish a control pair before generalising

- Get **one URL that renders correctly and one that does not**, from the same template. Comparing them
  eliminates causes in order: identical markup rules out the template; comparable image dimensions rule
  out the data; what is left is runtime — script initialisation, viewport, or load order.
- **Never widen a single sample to "every car" or "every page".** A dealer with 60 vehicles will spot the
  overstatement immediately. If you cannot find a working example yourself, ask for one — the client knows
  which page looks right.
- A defect fixed in appearance but not in mechanism is still open. State what was ruled out, so the next
  person does not repeat the elimination.

## When the site refuses your crawler

- A Cloudflare rule against datacentre addresses answers the shell, the managed browser and a
  local-profile browser with the same "Sorry, you have been blocked" page. The customer sees nothing, so
  this is a measurement problem, not a finding about the site — say so rather than reporting the site down.
- **Working fallback: `https://r.jina.ai/<full-url>` with the header `X-Return-Format: html`** returns the
  served HTML, including head tags, inline CSS and inline scripts. The same endpoint without that header
  returns markdown, which loses exactly the attributes an audit needs.
- Keep the proxy in the method note of the report: the page set was fetched through a third party, and the
  block is not something a normal visitor experiences.
- Confirm encoding findings against those served bytes, never against an extraction tool's output.

## Measure what you can still reach

- **Image CDNs are usually a separate host and are not behind the same rule.** Fetch the files directly to
  get true pixel dimensions, file weights and aspect ratios — that is what turns "looks zoomed" into a
  measurement.
- When a lab score is unavailable (quota exhausted, throttled), say so in the report and quote the measured
  weights and markup counts instead. Never present a score you did not actually obtain.
