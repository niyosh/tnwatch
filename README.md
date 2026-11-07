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

Court verdicts and sentences (they come years after the crime), appeals, prosecutor appointments, relief payments,
politicians' statements and crimes in other states are not counted as new incidents. Crime-search stories about bribes
or corruption are counted under corruption.

## How the page is organized
Most important first, so phones show what matters before the reader has to scroll far:

1. **Headline numbers**: latest crime reports (24 h), road deaths, women's safety, inflation, then the 30-day crime and
   corruption counts, debt and borrowing. Each opens its section.
2. **Your District**: readers pick their district once (saved in their own browser only, nothing is sent anywhere). It then
   shows first: its crime reports and rank among the 38 districts, women's safety reports, road deaths and its latest
   stories. Its stories get a pin in every list, it is outlined on both maps, and its news moves up in Top Stories.
3. **Top Stories**: the six most important reports of the last two days, ranked by how many outlets covered the incident,
   how serious it is (murder and crimes against women and children above theft; deaths in a crash) and how recent it is,
   with at most three per section.
4. **Safety**: crime (types, district map, districts with most reports, latest stories, trend), then road accidents.
5. **Cost of living**: inflation in Tamil Nadu vs India and what is getting costlier.
6. **Corruption**: counts by type and the latest cases.
7. **Government money**: debt and this year's borrowing.
8. **More news & sources**: other news, where every number comes from, downloads.

The order lives in `index.html`; the ranking rules for Top Stories are in `js/app.js` (search "Top stories").

## How the hourly update works
`.github/workflows/update.yml` runs on GitHub Actions (free for public repositories):

- **Every hour** the update starts itself: each run ends by starting `.github/workflows/timer.yml`, which waits
  55 minutes on the `hourly` environment's wait timer (Settings → Environments; waiting uses no runner and isn't billed)
  and then starts the next update. GitHub's own schedule started only 4–5 of 24 hourly runs a day here, so it is now
  just a backup that restarts the chain if it ever stops. Starting the timer is retried, since one failed request to
  GitHub once stopped the chain for 9 hours. Runs started by the timer or the schedule update only when the published
  data is over 50 minutes old.
- **Each update** searches the last 24 hours, rebuilds the numbers, draws the share image and publishes the site.
  When the last **full sweep** is over 20 hours old it also runs the 7- and 30-day searches and refreshes the official data.
- **On every push to `main`** — publishes the new code with the latest data, without fetching.

The stored stories live on the **`data` branch** (a single commit, replaced every run), so the `main` branch only changes
when the code does. GitHub Pages is published by the workflow (Settings → Pages → Source: GitHub Actions).

If an update is ever missed, the site shows "Updated N min ago", turns the notice amber when the data is more than
3 hours old, and offers visitors a refresh when newer data is published.
To refresh by hand: **Actions → Update data and site → Run workflow**. To pause the hourly updates, disable
**Hourly timer** in the Actions tab (the backup schedule still updates a few times a day); to restart them, enable it
and run **Update data and site** once.

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
data.gov.in refuses connections from GitHub's servers (they are outside India), so its datasets are refreshed from a
computer in India instead. NCRB publishes once a year, so once a year is enough; the site keeps the figures in between.
From the project folder in PowerShell:
```
powershell -ExecutionPolicy Bypass -File scripts\update_official.ps1
```
It asks for your data.gov.in API key at a hidden prompt (not saved), fetches the official figures, publishes them and
rebuilds the site. The `DATA_GOV_IN_API_KEY` repository secret is still used if data.gov.in ever accepts GitHub's servers.

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
