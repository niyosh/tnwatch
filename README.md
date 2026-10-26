# Tamil Nadu Watch — Home Dashboard

Live site: https://niyosh.github.io/tnwatch/ (English) · https://niyosh.github.io/tnwatch/?lang=ta (தமிழ்)

Every figure on the site is fetched automatically from public sources and refreshed every hour. Nothing is typed in by hand.

## Where the data comes from

| Section | Source | How often |
|---|---|---|
| Crime: Today / Week / Month, district map, trends | Google News RSS searches, English and Tamil editions | Every hour |
| Corruption | Google News RSS (bribery, DVAC / லஞ்ச ஒழிப்பு, disproportionate assets) | Every hour |
| Road safety: accidents, deaths and injuries by vehicle and district | Google News RSS (deaths/injuries are the numbers named in headlines) | Every hour |
| Prices & inflation | MoSPI API (`api.mospi.gov.in`, CPI base 2024=100): Tamil Nadu vs India, rural/urban/food, categories, state ranking | Checked every 6 h, hourly on 12–14th; MoSPI releases monthly on the 12th |
| Government debt | RBI *Handbook of Statistics on Indian States*, "State-wise Composition of Outstanding Liabilities" | Checked weekly; RBI publishes yearly |
| Borrowing this year | RBI press releases: weekly auctions of State Government Securities (RSS every hour, monthly archive daily) | Every hour; auctions are weekly |
| Latest news | Google News RSS | Every hour |
| Crime: Official | NCRB *Crime in India* via the data.gov.in API (needs a free API key) | Checked daily; NCRB publishes yearly |
| Economy (GSDP) | data.gov.in API — switched off until a dataset id is added to `scripts/sources.json` | Checked daily |

The MoSPI, RBI-debt and RBI-auction readers live in `scripts/official.py`. Each keeps its last good result, so a source
being down never blanks the page (the Sources card then shows "cached"). MoSPI's server needs legacy TLS renegotiation,
which the script enables for that host only (MoSPI's own API client does the same).

Daily, weekly and monthly counts are **news reports**, not official police figures. Headlines are sorted into crime types
and districts by keyword rules in `scripts/fetch_data.py`, which read English and Tamil (Tamil place names are matched as
stems, so சேலம் also finds சேலத்தில்). The same incident reported by several outlets is counted once: stories in the same
language that share their key words, or English and Tamil stories with the same type, district and day, are merged
(the CSV's `outlets` column shows how many were merged).

Changes (↑ / ↓ %) appear once the script has collected two full periods (2 days for "Today", 2 weeks for "This Week",
2 months for "This Month").

## How the hourly update works
`.github/workflows/update.yml` runs on GitHub Actions (free for public repositories):

- **Every hour (at :17)** — searches the last 24 hours, rebuilds the numbers, draws the share image and publishes the site.
- **Once a day (05:47 IST)** — also the 7- and 30-day searches and the official data.gov.in datasets.
- **On every push to `main`** — publishes the new code with the latest data, without fetching.

The stored stories live on the **`data` branch** (a single commit, replaced every run), so the `main` branch only changes
when the code does. GitHub Pages is published by the workflow (Settings → Pages → Source: GitHub Actions).

GitHub sometimes starts scheduled runs late or skips them at busy times. The site shows "Updated N min ago", turns the
notice amber when the data is more than 3 hours old, and offers visitors a refresh when newer data is published.
To refresh by hand: **Actions → Update data and site → Run workflow**.

## Fixing a wrong classification
Each story has a small flag that opens a pre-filled GitHub issue. To fix it, add a rule to `scripts/corrections.json`
(the file explains the format) — it applies on the next hourly run, also to stories already stored. If a rule in
`fetch_data.py` is wrong, fix it and add the headline to `scripts/test_classify.py`; the workflow runs those checks before
every publish, so a broken rule never reaches the site.

```
python scripts/test_classify.py
```

## Running it locally
```
python scripts/fetch_data.py               # full fetch (about 2 minutes); --mode hourly for a quick one
python scripts/fetch_data.py --mode offline  # re-apply the rules to stored stories without fetching
python scripts/make_card.py                # share image (needs: pip install pillow)
python -m http.server 8080
```
Then open http://localhost:8080. To start from the live data instead of an empty history:
```
git fetch origin data && git archive FETCH_HEAD | tar -x -C data
```

## Official data (NCRB, GSDP)
Get a free API key at https://data.gov.in (sign up, then "My Account" → API key) and add it under
**Settings → Secrets and variables → Actions** as `DATA_GOV_IN_API_KEY`.

To add another dataset: open it on data.gov.in, go to its **API** tab and copy the id after `/resource/`.
Add it to `scripts/sources.json` with `"use": "economy"` (GSDP) or `"use": "crime_official"`.
The dataset must have one row per state and one column per year.

## Sharing
Share buttons use the phone's share sheet (WhatsApp, Telegram…) or fall back to WhatsApp. Links keep the reader's view:
`?d=Madurai` opens Madurai's crime stories, `?ty=Murder` a crime type, `?lang=ta` Tamil. The preview image
(`data/card.png`) is redrawn every hour with the latest numbers.

## Languages (English / தமிழ்)
The button in the header switches the interface between English and Tamil. All interface text lives in `js/i18n.js`
(page text is marked with `data-i18n` in `index.html`). News headlines stay in the language they were published in;
story lists show the reader's language first.

## When changing CSS or JS
Bump the `?v=` number on the `css/style.css`, `js/i18n.js` and `js/app.js` links in `index.html`, so browsers don't mix
cached old files with new ones.

## Hero image
Save a wide photo as `assets/hero.jpg` (e.g. 1920×800). Without it a drawn skyline is shown.
