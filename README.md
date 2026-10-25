# Tamil Nadu Watch — Home Dashboard

Every figure on the site is fetched automatically from public sources. Nothing is typed in by hand.

## Where the data comes from

| Section | Source | Notes |
|---|---|---|
| Crime: Today / This Week / This Month, district map | Google News RSS search feeds | Counts of **news reports**, not official police figures. Headlines are classified by keywords in `scripts/fetch_data.py`. |
| Crime: Official | NCRB *Crime in India* via the data.gov.in API | Yearly, about a year behind. Needs a free API key. |
| Corruption | Google News RSS (bribery, DVAC, vigilance, disproportionate assets) | News reports. |
| Latest news | Google News RSS | Every story links to its original publisher. |
| Economy (GSDP) | data.gov.in API | Switched off until you add a dataset id in `scripts/sources.json`. The card stays hidden until then. |

Changes (↑ / ↓ %) only appear once the script has run daily long enough to compare two full periods
(1 day for "Today", 1 week for "This Week", 30 days for "This Month").

## Updating the data
```
python scripts/fetch_data.py
```
This writes `data/auto.js` (what the page shows) and `data/history.json` (stored stories used for weekly and monthly counts).
Don't edit either file by hand.

## Running it every day automatically (free)
1. Put this folder in a GitHub repository.
2. In the repository settings, turn on **Pages** (deploy from the main branch, root folder).
3. Get a free API key at https://data.gov.in (sign up, then "My Account" → API key) and add it under
   **Settings → Secrets and variables → Actions** as `DATA_GOV_IN_API_KEY`.
4. The workflow in `.github/workflows/fetch-data.yml` runs every day at 06:00 IST, commits the new data,
   and GitHub Pages republishes the site. You can also start it with **Actions → Fetch public data → Run workflow**.

## Running it locally
```
python -m http.server 8080
```
Then open http://localhost:8080

## Adding another official dataset
Open the dataset on data.gov.in, go to its **API** tab and copy the id after `/resource/`.
Add it to `scripts/sources.json` with `"use": "economy"` (GSDP) or `"use": "crime_official"`.
The dataset must have one row per state and one column per year.

## Hero image
Save a wide photo as `assets/hero.jpg` (e.g. 1920×800). Without it a drawn skyline is shown.
