# Statutory and finance details — the checks that carry real exposure

A dealer site can pass every SEO, layout and link check and still publish a false statutory
detail. These are the ones that have been found live, with the check that catches each.

## Company number

- UK company numbers are **eight digits and the leading zero is part of it**. A footer printing
  `8974082` for company `08974082` is wrong, and it is the kind of wrong a copy edit makes.
- Verify against Companies House by name (`find-and-update.company-information.service.gov.uk`),
  not from memory or from the client's own footer — the footer is what you are checking.
- Grab the **registered office** at the same time; you need it for the next check.

## What the website must display

A UK company's site must carry: registered name, company number, **place of registration**
(England and Wales) and **registered office address**. A footer showing only a VAT number, a
company number and an FCA number is incomplete even when all three are correct — raise it as its
own finding rather than folding it into a copy note.

## ICO registration

- The privacy policy usually states an ICO registration number. **That number must belong to this
  entity.** Templates cloned from another dealer carry the donor's, in the footer *and* inside the
  privacy policy where it reads as an assertion about data protection.
- A registration number that resolves to a different company is a **Critical** leak, not a typo:
  the policy is telling customers who regulates their data, and it is naming someone else.
- If the dealer's own number is unknown, omit the claim. Never borrow, guess or keep the donor's.

## FCA firm reference number

- The FRN identifies the entity, so verify it resolves to the company you think it does — a
  correct-looking six-digit number can belong to a different firm, and a revoked predecessor of
  the same company often ranks above the live one.
- The register's JSON API needs credentials; a name/number web search against a register mirror is
  the fallback when you have none, and it is enough to confirm the firm name and status.
- Confirming the FRN does **not** clear the finance copy. It proves the disclosure names the right
  entity; the representative example is a separate finding.

## Representative examples and monthly payments

- Read the example's own fields. `annual mileage is 0` and `excess mileage fee per mile is £0.00`
  is a defective disclosure — an example that cannot describe a real agreement.
- One fixed example shown against cars from £10,995 to £22,850 is worth questioning: cash price,
  deposit and term should relate to something.
- **A monthly payment is a rate claim.** A card or vehicle page showing `£x/mo` without the APR it
  was calculated from is publishing a regulated figure with no basis. Either the dealer's approved
  example travels with it, or the monthly figure comes off the site.
- Finance copy on vehicle pages and in FAQ answers is generated from the same constants; fixing the
  headline number does not fix the sentence in the FAQ or the print card.

## Cookies and consent

- A banner offering only "I understand" or "Accept" is a PECR finding when analytics, ads or
  remarketing tags are present — consent needs a refusal as easy as the acceptance.
- Check whether tags fire **before** a choice: find the GA4/GTM/Ads IDs in the served HTML and see
  whether they load unconditionally. A dead Universal Analytics property still in the source is
  separate housekeeping, but evidence the tag set is unmanaged.
- Consent-mode defaults set from `localStorage` tell you the plugin exists, not that the banner
  offers a choice — read the rendered banner.

## Presentation

Report these as compliance findings with their own severity, never as copy edits. In the narrative,
name the exposure in one clause (what a customer or regulator would see) and keep the fix concrete.
