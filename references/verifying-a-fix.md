# Verifying a fix, and closing the finding on evidence

A fix claim has three parts: the mechanism changed, the symptom is gone on **current** data, and the report says
which of those is proven. Skipping the third makes a closed finding indistinguishable from an unclosed one.

## 1. Re-test on current stock — the car in the original finding may no longer exist

Dealer inventory churns faster than the audit cycle. A vehicle URL that was the reproduction case last week
usually **302s to a make/category listing** once the car sells, which returns 200 and renders a perfectly good
page — so a naive "the URL still loads" check reads as a pass on a page that is no longer a VDP.

- Fetch the URL and read the **canonical** and the `<h1>`. A title like "Used Audi cars in Bury" on a
  `/used-audi-a3-…` URL means the car sold and you are looking at a category page.
- Say so explicitly in the finding. "The original failing car has sold, so that exact page cannot be retested"
  is a defensible closing note; "fixed" based on a different page is not.
- Sample **at least two current listings from different price/make bands**. One page proves a page; two across
  the template prove the template, which is what the finding actually claimed.

## 2. Render it — do not infer the symptom from the markup

The fault usually cannot be re-read out of the HTML.

- Use a renderer that executes JS and waits for lazy loaders/plugins; the working route and its parameters are
  in the `blocked-page-recovery` skill.
- **A blank region is not a pass.** Screenshot services that do not run the page's own JS return every
  lazy-loaded gallery as an empty white box, which reads identically to "no image" and to "fine now". If the
  gallery is blank in one capture and populated in another, believe only the capture that waited.
- Record the **mechanism** change as well as the picture: the offending CSS rule absent from the stylesheet, the
  container replaced by a different one. "The `aspect-ratio` rule that caused the crop is gone and the layout is
  now a single image with a thumbnail strip" is what makes the render trustworthy — it explains why the symptom
  cannot recur.

## 3. Write the closure into the finding itself

Do not delete a fixed finding, and do not silently lower its severity — the severity history is what shows the
client the audit was worth paying for.

- Retitle it in place: `«original title» — FIXED and verified «DD Month YYYY»`.
- Add a **Resolved:** sentence to the evidence block: what changed on their side, which pages were tested, and
  any caveat (sold stock, one viewport only).
- Keep the original expected / actual / recommendation text intact beneath it.
- Re-run the report build and **grep the rendered .docx/.pdf** for the resolution string — a title edited in the
  builder source is not a title that reached the document.
- State the limits plainly in the covering message. "On desktop it is right" is the safe form until a narrow
  viewport has been checked, especially where the original fault was viewport-dependent.

## What does not count as verification

- A 200 on the URL (a category page redirects and returns 200).
- A screenshot whose gallery area is empty.
- The client's own word that it is fixed, when the fault was reproducible from outside.
- Markup that *looks* different, with no render — templates get restructured without the symptom changing.
