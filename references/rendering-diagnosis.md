# Diagnosing a reported rendering fault

For the moment a client says *"the images look zoomed in"*, *"this page is broken"* or *"the photos are
stretched"* — before any finding is written, and before the stylesheet is opened.

## 1. The screenshot is the evidence; the stylesheet is only a hypothesis

CSS says what a rule *declares*, not what the browser did with it.

- `object-fit` applies to **replaced elements** only. On a `<div>` it is inert, so a rule reading
  `object-fit:contain` on a container tells you nothing about the image inside it.
- Gallery and slider libraries (RoyalSlider, Swiper, Slick) size slides and images **in JS after load**, so the
  container ratio in the cascade predicts neither a crop nor a letterbox.
- A fixed default (`width:600px;height:350px`) in a vendor block can be overridden at runtime by the plugin's
  own inline styles.

The order that works:

1. Open the capture the user already sent — they usually have one, and it is faster and truer than any
   inference. Crop the affected region at full resolution (`sips -c <h> <w> --cropOffset <y> <x>`) and look at
   what is actually cut off: the top, the side, or the whole car.
2. Describe the failure in words before naming a cause ("only the front grille is visible; the frame is tall
   and narrow" is a description; "the CSS crops it 25%" is a guess).
3. Only then read the CSS/JS for a mechanism, and label whatever you find as a hypothesis until a second
   observation supports it.

A reasoned-from-CSS diagnosis has previously named a "16:9 `cover` container cropping 25% off every photo" on a
site whose gallery was `contain` in a div — and the source photograph was a clean full-car shot all along.

## 2. Get a control before scoping a fault across a page type

"Every vehicle page crops the photo" and "some do" are different findings, with different fixes and different
severities. The user frequently knows which:

> Ask for one page that looks right alongside one that looks wrong. Two URLs is all it takes.

Then diff the two cases:

- **Markup**: the gallery container, the `<img>` attributes, the lazy-loader, the data attributes.
- **Source assets**: fetch each hero at full size and compare real pixel dimensions and ratios; open the file
  and look at it (a "cropped" car may be a photo the supplier framed that way).
- **Asset health**: status-check every gallery image — one 404 can break a slider's initialisation.

If the markup is **identical** and the rendering differs, the cause is runtime state, a per-asset property or
the viewport — not the template. Say that in the finding instead of blaming the whole estate, and name the
control pair in the evidence so the developer can reproduce it.

## 3. Confirm the viewport before calling it a capture artefact

Zoom, window size and DPR all change a screenshot:

- A viewport readout (`whatismyviewport.com`) gives **width × height × DPR**. 2988 px wide at DPR 2 is a
  1494 px window at 100% zoom — a normal desktop, not a zoom artefact.
- A **short** window height matters: a gallery capped with `max-height:75vw` is taller than a 624 px viewport,
  which is exactly where a slider's height calculation goes wrong.
- Re-check at a second window height. A fault that only appears at one viewport is a real bug with a narrower
  scope; a fault that disappears at 100% zoom was a capture artefact. Either way, ask for the numbers rather
  than arguing from the image.

## 4. What goes into the finding

- The control (working URL) beside the failing one.
- What was ruled out and how — markup identical, all N images 200, asset dimensions measured, viewport confirmed.
- The one asymmetry that remains, offered to the developer as a lead rather than a conclusion ("this car's set
  contains a single 640×480 file among 1024 px ones").

Do not generalise from a single page to "every car", and do not let a mechanism you have not observed become
the headline of the finding.

## 5. Closing a finding — evidence it on a render, not on the markup

A finding is not resolved because the mechanism you named has gone; it is resolved when a browser shows the
page correct. The two are not the same, and a report that marks something FIXED on markup alone gets reopened
by the client.

- **The stylesheet losing the rule is a hypothesis that the fix landed, not proof of the result.** A gallery
  rebuilt from a fixed-ratio slider to a single image plus a thumbnail strip has removed the crop rule — but
  whether the car now renders whole is a question for a pixel. Render the page, look at it, then write the
  finding.
- **Re-test on current stock when the originally reported URL has gone.** Sold vehicles 301 to their category
  page (or 404), so the exact failing page is often untestable a week later. Test two or three cars that are
  live now, say plainly that the original page can no longer be reproduced, and scope the finding to what you
  actually saw — "verified on two current vehicles" is honest and still closes it; "fixed" over an unrepeatable
  page is not.
- **A blank in a third-party screenshot is not evidence of anything.** Services that do not execute the page's
  JavaScript (thum.io, WordPress mShots and friends) return a **blank gallery box** on any lazy-loaded slider.
  That blank is neither a fault nor a pass, and reporting it as either wastes a round. Use a renderer that runs
  the page and waits (microlink with `waitForTimeout`, or a real browser over CDP), and state in the evidence
  which one you used.
- **Regenerate the report after you edit the builder.** The `.docx`/`.pdf` on disk is the deliverable; a patched
  `build_*.py` is not. Re-run the builder, then read the new file back and assert the new wording is present
  (`'FIXED and verified' in text`, a resolution line, the evidence URLs) before telling anyone it is updated —
  the file in the delivery folder is several revisions behind its own script by default.
- **Say which viewport you verified.** A desktop render closing a finding does not cover mobile, and galleries
  are exactly the component that differs between them. If you have only checked one, write the finding as
  "desktop verified" — Woody click-tests live pages and will find the phone case himself.
