# DSC Website QA

A structured website QA methodology for UK used-car dealership sites — severity-rated findings, expected-vs-actual, and a priority-ordered fix list, with the false positives that waste a pass already ruled out.

Written and maintained by [Digital Sales Consultants](https://sales-consultants.com) (Paul "Woody" Wood, Grimsby) and used on live dealer sites every week. Published because most of what is in here was learned the hard way and is not specific to us.

It is packaged as a **[Hermes Agent](https://hermes-agent.nousresearch.com/docs) skill**: a `SKILL.md` that the agent loads when a site review comes up, plus reference files it opens on demand.

## What it covers

- **The first pass** — every page template, the checks per page, the standing rule that vehicle and category pages must be transactional (`{Make} {Model} for Sale in {Town}`) rather than merely informative.
- **Recording findings** — the finding schema (severity, expected, actual, evidence, recommendation, status) and how to keep it honest: verify by value not presence, assert the absence of the wrong value, classify re-checks as fixed / still open / new.
- **Mobile** — synthetic clicks that don't fire React hamburgers, double-bound toggles, measuring layout defects instead of eyeballing them.
- **Delivering** — the house renderer, the developer message, the client report, the peer note, the status board on reissue, and the error that puts a report in a folder the user cannot attach from.
- **Pitfalls** — 78 of them, split by theme: front-end behaviour and tooling, hosts and launches, and content, claims and compliance.

## Install

Copy the directory into your Hermes profile's skills tree and it will be picked up by name:

```bash
git clone https://github.com/dealersales/dsc-website-qa.git \
  ~/.hermes/profiles/<profile>/skills/dsc/dsc-website-qa
```

The agent then loads it when the task matches (`"run the QA for <client>"`, a site review, a pre-launch check), or on request:

```text
skill_view(name="dsc-website-qa")
```

Nothing here is Hermes-only: `SKILL.md` and `references/` read as plain methodology, and `scripts/` are standalone Python. If you are using another agent framework, point it at `SKILL.md` as the entry point.

## Structure

```
SKILL.md                          the entry point: when to use, procedure, pitfalls index, verification checklist
references/                       topic depth, opened on demand
  pitfalls-frontend-and-tooling.md
  pitfalls-hosts-urls-and-launch.md
  pitfalls-content-claims-and-findings.md
  deliver-report-build-and-handover.md
  deliver-audience-variants.md
  deliver-reissue-and-status.md
  ...                             plus per-topic references (redirect maps, site-down triage,
                                  estate inventory, Elementor, bot walls, defect provenance, ...)
scripts/                          estate_survey.py, check-prelaunch-sitemap.py, measure-layout.py,
                                  findings-to-table.py, tunnel_proxy.py, check_media_delivery_path.py
templates/                        build_report.py (markdown → branded PDF/DOCX), check-live-site.py
```

## What has been redacted

This is a working copy with the client-specific material stripped, not a sanitised rewrite:

- dealer trading names, domains and locations → generic descriptions
- the dealer platform, its hostnames and the DSO code paths → `the platform` / `<platform-host>`
- colleagues, client contacts and their email addresses → roles (`the platform owner`, `the client coordinator`)
- credentials, keychain item names, server IPs, phone numbers and local paths → placeholders

The lessons, the measurements and the code are unchanged. Two reference files that `SKILL.md` points at (`mobile-experience-audit.md`, `sage-bedrock-ssh-editing.md`) are not in this copy — they were never written up.

## Companion skills

Some cross-references point at other skills in our set (`dsc-seo-audit`, `dsc-gbp-audit`, `dsc-fca-compliance`, `uk-car-dealer-copy`, `platform-estate-deploy`). Those are not published here; the cross-link simply won't resolve, and the methodology stands on its own.

## Contributing

Issues and pull requests welcome, particularly:

- a false positive you had to retract, with what would have caught it earlier
- a check that only works on one platform shape
- UK-specific compliance wording (FCA, distance selling, ICO) that we have got wrong

Please keep entries imperative and general — a rule plus the reason it exists, not an incident report.

## Licence

MIT — see [LICENSE](LICENSE).
