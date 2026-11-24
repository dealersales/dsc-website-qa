# QA-ing a site that blocks our crawler

Some dealer sites sit behind a WAF (Cloudflare "Attention Required / you have been blocked") that refuses
datacentre addresses. The block is on the address, not on the agent: `requests`, the managed browser and the
local-profile browser all return the same short block page, and changing user-agent, retrying or waiting does
not clear it. Do not read that as "the site is down" or "the browser tool is broken" — a customer sees the
site perfectly well.

## Getting the HTML

`https://r.jina.ai/<url>` with the header `X-Return-Format: html` returns the **real served document** — head
tags, JSON-LD, forms, inline CSS — which is what findings rest on. Pace requests a few seconds apart; the
service throttles under bursts.

The markdown extractors are fine for reading copy but lose exactly the attributes a QA pass needs (canonical,
`meta robots`, form actions, image `srcset`, inline `style`). When a finding depends on markup, use the HTML
route; when it depends on what a visitor sees, use rendered text — and keep the two evidence types separate
in the report.

## Say how it was fetched

Put one line in the report's method note: the page set was fetched through a reader proxy because the site
refuses datacentre IPs. It is not a secret, and anyone auditing the evidence needs to know the transport was
third-party.

## A short extraction is not an empty page

A tool that returns less than you expected has usually truncated or mis-cropped — it has not proved absence.

- Long screenshots get downscaled or band-cropped by OCR; if the expected section heading is missing, re-read
  at higher scale with overlap before concluding the panel is empty.
- A markdown extraction that ends early is a character budget, not the end of the document.
- Before writing "no X on the page", grep the saved bytes for the label you expected (`FCA`, `Privacy`,
  `Doors`, the section heading). Absence claims are the ones that cost credibility when they are wrong.

## Order of work when the site is blocked

1. Fetch the sitemap through the proxy — it gives the URL inventory and `lastmod` without crawling.
2. Fetch the templates that carry findings (home, listing, one VDP, contact, finance, about, privacy, terms,
   cookie policy, plus any page the enquiry CTA targets).
3. Only then fetch a sample of VDPs, and measure their assets directly from the image CDN — that host is
   usually not behind the same WAF, so image dimensions, file weights and 200s can be measured directly even
   when the HTML cannot.
