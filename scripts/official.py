"""Official statistics for Tamil Nadu, read from government sources by fetch_data.py.

  inflation  MoSPI API (api.mospi.gov.in): Consumer Price Index, base 2024=100, monthly (released on the 12th)
  debt       RBI Handbook of Statistics on Indian States: "State-wise Composition of Outstanding Liabilities", yearly
  borrowing  RBI press releases: weekly auctions of State Government Securities (SDLs), Tamil Nadu's share

Every fetcher keeps its last good result in the history "cache", so a failed run never blanks the page.
Uses only the Python standard library.
"""

import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; TamilNaduWatch/1.0; +https://github.com/niyosh/tnwatch)"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]

# MoSPI's server only completes TLS with legacy renegotiation enabled (MoSPI's own API client does the same);
# certificates are still verified.
MOSPI_TLS = ssl.create_default_context()
MOSPI_TLS.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
MOSPI_CPI = "https://api.mospi.gov.in/api/cpi/getCPIData"
MOSPI_PAGE = "https://esankhyiki.mospi.gov.in/"
TN, INDIA = 31, 1
# States with more than 50 lakh people (Census 2011): MoSPI ranks state inflation among these
MAJOR_STATES = {
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "NCT of Delhi", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jammu And Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha", "Punjab",
    "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh", "Uttarakhand", "West Bengal",
}

RBI_HANDBOOK = "https://www.rbi.org.in/scripts/AnnualPublications.aspx?head=Handbook+of+Statistics+on+Indian+States"
RBI_RSS = "https://www.rbi.org.in/pressreleases_rss.xml"
RBI_LIST = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
RBI_PR = "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid={}"


def get(url, data=None, ctx=None, timeout=60):
    headers = {"User-Agent": UA}
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if attempt:
                raise
            time.sleep(3)


def _num(s):
    s = str(s or "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _age_hours(cached, now):
    try:
        return (now - datetime.fromisoformat(cached["fetched"])).total_seconds() / 3600
    except (KeyError, TypeError, ValueError):
        return 1e9


class Rows(HTMLParser):
    """Text of every table row in a page, as lists of cell strings."""

    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def table_rows(page):
    p = Rows()
    p.feed(page)
    return p.rows


# ---------------------------------------------------------------------------
# Inflation (MoSPI CPI)
# ---------------------------------------------------------------------------
def mospi(**params):
    """Rows of a getCPIData query (10 rows per page without a token, so ask for up to 100)."""
    query = {"base_year": "2024", "series": "Current", "Format": "JSON", "limit": 100, **params}
    data = json.loads(get(MOSPI_CPI + "?" + urllib.parse.urlencode(query), ctx=MOSPI_TLS))
    time.sleep(0.3)
    return data.get("data") or []


def _month_key(row):
    return f"{row['year']}-{MONTHS.index(row['month']) + 1:02d}"


def fetch_inflation(cache, now, force=False):
    """Tamil Nadu and All-India consumer price inflation. Refreshed every 6 hours, hourly around release day
    and on every full run."""
    old = cache.get("inflation")
    if old and not force and _age_hours(old, now) < 6 and not 12 <= now.day <= 14:
        return {"status": "ok", "detail": f"latest {old['latest']['month']}, checked {old['fetched'][:16]}"}
    years = f"{now.year - 1},{now.year}"
    series = {}
    for code, who in ((TN, "tn"), (INDIA, "india")):
        for r in mospi(state_code=code, division_code=0, sector_code="1,2,3", year=years):
            if r.get("inflation") is None:
                continue
            series.setdefault(_month_key(r), {})[f"{who}_{r['sector'].lower()}"] = _num(r["inflation"])
    months = sorted(m for m, v in series.items() if "tn_combined" in v and "india_combined" in v)
    if not months:
        raise ValueError("MoSPI returned no inflation figures")
    latest = months[-1]
    y, m = (int(x) for x in latest.split("-"))

    states = [{"state": r["state"], "value": _num(r["inflation"])}
              for r in mospi(division_code=0, sector_code=3, year=y, month_code=m)
              if r["state"] in MAJOR_STATES and r.get("inflation") is not None]
    states.sort(key=lambda s: -s["value"])
    rank = next((i + 1 for i, s in enumerate(states) if s["state"] == "Tamil Nadu"), None)

    def top_level(rows):
        return [r for r in rows if not r.get("group") and not r.get("class") and r.get("inflation") is not None]

    divisions = {}
    for code, who in ((TN, "tn"), (INDIA, "india")):
        rows = mospi(state_code=code, sector_code=3, year=y, month_code=m,
                     division_code=",".join(str(c) for c in range(1, 14)), limit=20)
        for r in top_level(rows):
            divisions.setdefault(r["division"], {})[who] = _num(r["inflation"])

    def food(code):
        rows = mospi(state_code=code, group_code=1, sector_code=3, year=y, month_code=m, limit=10)
        row = next((r for r in rows if r.get("group") == "Food" and not r.get("class")), None)
        return _num(row["inflation"]) if row else None

    cur = series[latest]
    next_release = date(y + (m == 12), m % 12 + 1, 12)
    next_release = date(next_release.year + (next_release.month == 12), next_release.month % 12 + 1, 12)
    result = {
        "fetched": now.isoformat(timespec="minutes"),
        "source": {"name": "MoSPI — Consumer Price Index (base 2024=100)", "url": MOSPI_PAGE},
        "latest": {"month": latest, "provisional": True, "nextRelease": next_release.isoformat()},
        "tn": {"combined": cur["tn_combined"], "rural": cur.get("tn_rural"), "urban": cur.get("tn_urban"), "food": food(TN)},
        "india": {"combined": cur["india_combined"], "rural": cur.get("india_rural"), "urban": cur.get("india_urban"),
                  "food": food(INDIA)},
        "rank": {"position": rank, "of": len(states), "top": states[:5]},
        "series": [{"month": mo, "tn": series[mo]["tn_combined"], "india": series[mo]["india_combined"]}
                   for mo in months[-24:]],
        "divisions": sorted(({"name": k, **v} for k, v in divisions.items() if "tn" in v),
                            key=lambda d: -d["tn"]),
    }
    cache["inflation"] = result
    return {"status": "ok", "detail": f"latest {latest}: Tamil Nadu {cur['tn_combined']}%, India {cur['india_combined']}%"}


# ---------------------------------------------------------------------------
# Debt (RBI Handbook of Statistics on Indian States)
# ---------------------------------------------------------------------------
LIAB_TITLE = "State-wise Composition of Outstanding Liabilities"


def parse_liabilities(page):
    """{year: {state: {column: value}}} from the RBI table page (each year is printed in two parts)."""
    years = {}
    parts = re.split(r"(OUTSTANDING LIABILITIES\s*-\s*\d{4})", page, flags=re.I)
    for title, chunk in zip(parts[1::2], parts[2::2]):
        year, header = int(re.search(r"\d{4}", title).group()), None
        for row in table_rows(chunk):
            if row[0].startswith("State") and len(row) >= 3:
                header = row
            elif header and len(row) == len(header) and re.search(r"[A-Za-z]", row[0]):
                values = years.setdefault(year, {}).setdefault(row[0], {})
                for name, cell in zip(header[1:], row[1:]):
                    values[name] = _num(cell) if cell not in ("-", "") else 0.0
    return years


def fetch_debt(cache, now, force=False):
    """Tamil Nadu's outstanding liabilities (end-March), all years in the latest Handbook.
    Refreshed weekly and on every full run."""
    old = cache.get("debt")
    if old and not force and _age_hours(old, now) < 24 * 7:
        return {"status": "ok", "detail": f"end-March {old['latest']['year']}, checked {old['fetched'][:10]}"}
    listing = get(RBI_HANDBOOK)
    m = re.search(r"PublicationsView\.aspx\?id=(\d+)'?\"?>\s*Table\s*\d+:\s*" + LIAB_TITLE, listing, re.I)
    if not m:
        raise ValueError("liabilities table not found in the Handbook listing")
    table_url = f"https://www.rbi.org.in/Scripts/PublicationsView.aspx?id={m.group(1)}"
    years = parse_liabilities(get(table_url))
    total_col = "Outstanding Liabilities"
    series = []
    for y in sorted(years):
        tn = years[y].get("Tamil Nadu", {})
        if tn.get(total_col):
            series.append({"year": y, "total": tn[total_col]})
    if not series:
        raise ValueError("no Tamil Nadu rows in the liabilities table")
    latest_year = series[-1]["year"]
    tn = years[latest_year]["Tamil Nadu"]
    states = sorted(((s, v[total_col]) for s, v in years[latest_year].items()
                     if v.get(total_col) and not s.startswith("All")), key=lambda sv: -sv[1])
    all_states = next((v[total_col] for s, v in years[latest_year].items() if s.startswith("All")), None)
    internal = tn.get("Total Internal Debt", 0)
    sdl = tn.get("SDLs", 0)
    centre = tn.get("Loans and Advances from Centre", 0)
    pf = tn.get("Provident Fund etc.,", tn.get("Provident Fund etc.", 0))
    other = tn[total_col] - internal - centre - pf
    cache["debt"] = {
        "fetched": now.isoformat(timespec="minutes"),
        "source": {"name": "RBI — Handbook of Statistics on Indian States, " + LIAB_TITLE, "url": table_url},
        "latest": {"year": latest_year, "total": tn[total_col]},
        "rank": {"position": next(i + 1 for i, (s, _) in enumerate(states) if s == "Tamil Nadu"), "of": len(states)},
        "shareOfStates": round(tn[total_col] / all_states * 100, 1) if all_states else None,
        "composition": [
            {"part": "Market loans (SDLs)", "value": sdl},
            {"part": "Other loans", "value": internal - sdl},
            {"part": "Loans from the Centre", "value": centre},
            {"part": "Provident funds", "value": pf},
            {"part": "Deposits, reserves and other", "value": other},
        ],
        "series": series,
    }
    return {"status": "ok", "detail": f"end-March {latest_year}: ₹{tn[total_col]:,.0f} crore"}


# ---------------------------------------------------------------------------
# Borrowing (RBI weekly auctions of State Government Securities)
# ---------------------------------------------------------------------------
def _release_date(text):
    m = re.search(r"Date\s*:\s*([A-Z][a-z]{2})[a-z]*\.? (\d{1,2}), (\d{4})", text)
    if not m:
        return None
    return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y").date()


def _tenor(cell, year):
    """Years to maturity: "20", or a re-issue such as "Re-issue of 7.80% Tamil Nadu SGS 2041 ..."."""
    if re.fullmatch(r"\d{1,2}", cell.strip()):
        return int(cell)
    m = re.search(r"SGS (\d{4})", cell)
    return max(int(m.group(1)) - year, 1) if m else None


def tn_tranches(rows, kind):
    """Tamil Nadu's securities in a results ("result") or announcement ("notice") table."""
    out, inside = [], False
    width = 4 if kind == "result" else 3
    for row in rows:
        # cells naming a state (not amounts, re-issue descriptions or the auction type)
        names = [c for c in row if re.search(r"[A-Za-z]{3}", c) and not c.startswith("Re-issue")
                 and c not in ("Price", "Yield")]
        if any(c.rstrip("*#") == "Tamil Nadu" for c in row):
            inside = True
        elif inside and (names or row[0].startswith("Total")):
            break
        if inside and len(row) >= width:
            out.append(row[-width:])
    return out


def parse_result(page, prid):
    """Tamil Nadu's accepted amounts and cut-off yields from a "Result of ... Auction" release."""
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page)).split())
    day = _release_date(text)
    if not day:
        return None
    tranches = []
    for notified, accepted, cutoff, tenor in tn_tranches(table_rows(page), "result"):
        amount = _num(accepted)
        yld = _num(cutoff.split("/")[-1]) if cutoff not in ("-", "") else None
        tranches.append({"notified": _num(notified), "accepted": amount or 0.0, "yield": yld,
                         "tenor": _tenor(tenor, day.year), "reissue": tenor.startswith("Re-issue")})
    return {"prid": prid, "date": day.isoformat(), "tranches": tranches}


def parse_notice(page, prid):
    """Tamil Nadu's planned amounts and the auction date from an "Auction of State Government Securities" release."""
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page)).split())
    m = re.search(r"conducted.{0,200}? on ([A-Z][a-z]+ \d{1,2}, \d{4}) \(\w+day\)", text)
    released = _release_date(text)
    when = datetime.strptime(m.group(1), "%B %d, %Y").date() if m else (released and released + timedelta(days=4))
    tranches = [{"amount": _num(a), "tenor": _tenor(t, when.year if when else date.today().year)}
                for a, t, _type in tn_tranches(table_rows(page), "notice")]
    return {"prid": prid, "auctionDate": when.isoformat() if when else None, "tranches": tranches}


def _month_listing(year, month):
    """(prid, title) of every press release in a month, from the RBI archive (an ASP.NET form post)."""
    first = get(RBI_LIST)
    form = {n: html.unescape(v) for n, v in re.findall(r'name="(__[A-Z]+)"[^>]*value="([^"]*)"', first)}
    page = get(RBI_LIST, data=dict(form, hdnYear=str(year), hdnMonth=str(month)))
    return [(int(p), " ".join(html.unescape(t).split())) for p, t in re.findall(r"prid=(\d+)[^>]*>([^<]+)</a>", page)]


def _fy_start(day):
    return date(day.year if day.month >= 4 else day.year - 1, 4, 1)


def fetch_borrowing(cache, now, full):
    """Weekly SDL auctions. Every run reads the RBI feed; full runs also fill gaps from the monthly archive
    (this financial year and the last one)."""
    store = cache.setdefault("auctions", {"results": {}, "notices": {}, "months": []})
    results, notices = store["results"], store["notices"]
    checked = 0

    def kind(title):
        if re.search(r"result of .*auction of state government securities", title, re.I):
            return "result"
        if re.fullmatch(r"auction of state government securities", title.strip(), re.I):
            return "notice"
        return None

    def take(prid, title, page):
        if kind(title) == "result":
            r = parse_result(page, prid)
            if r:
                results[str(prid)] = r
        elif kind(title) == "notice":
            notices[str(prid)] = parse_notice(page, prid)

    for item in ET.fromstring(get(RBI_RSS).encode("utf-8")).iter("item"):
        title = item.findtext("title") or ""
        prid = re.search(r"prid=(\d+)", item.findtext("link") or "")
        if prid and kind(title) and prid.group(1) not in results:
            body = f"<p>Date : {_rss_date(item.findtext('pubDate'))}</p>" + (item.findtext("description") or "")
            take(int(prid.group(1)), title, body)

    if full:
        today = now.date()
        start = _fy_start(today).replace(year=_fy_start(today).year - 1)
        y, m = start.year, start.month
        while (y, m) <= (today.year, today.month):
            key = f"{y}-{m:02d}"
            if key not in store["months"]:
                current = (y, m) == (today.year, today.month)
                for prid, title in _month_listing(y, m):
                    # results of every month; announcements only matter for the coming auction
                    wanted = kind(title) == "result" or (kind(title) == "notice" and current)
                    if wanted and str(prid) not in results and str(prid) not in notices:
                        take(prid, title, get(RBI_PR.format(prid)))
                        checked += 1
                        time.sleep(0.5)
                if (y, m) < (today.year, today.month):
                    store["months"].append(key)  # past months are complete
                time.sleep(0.5)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    # summary for the page
    today = now.date()
    fy, prev_fy = _fy_start(today), _fy_start(today).replace(year=_fy_start(today).year - 1)
    same_day_last_year = today - timedelta(days=365)
    auctions = sorted((r for r in results.values() if r["tranches"]), key=lambda r: r["date"], reverse=True)

    def total(since, until):
        return sum(t["accepted"] for r in auctions if since.isoformat() <= r["date"] <= until.isoformat()
                   for t in r["tranches"])

    this_year = [r for r in auctions if r["date"] >= fy.isoformat()]
    raised = sum(t["accepted"] for r in this_year for t in r["tranches"])
    weighted = sum(t["accepted"] * t["yield"] for r in this_year for t in r["tranches"] if t["yield"])
    upcoming = min((n for n in notices.values() if n.get("auctionDate") and n["auctionDate"] >= today.isoformat()
                    and n["tranches"]), key=lambda n: n["auctionDate"], default=None)
    cache["borrowing"] = {
        "fetched": now.isoformat(timespec="minutes"),
        "source": {"name": "RBI — Results of auctions of State Government Securities", "url": RBI_LIST},
        "fyStart": fy.isoformat(),
        "raised": raised,
        "auctions": len(this_year),
        "avgYield": round(weighted / raised, 2) if raised else None,
        "lastYearSamePeriod": total(prev_fy, same_day_last_year),
        "lastYearTotal": total(prev_fy, fy - timedelta(days=1)),
        "upcoming": upcoming and {"date": upcoming["auctionDate"],
                                  "amount": sum(t["amount"] or 0 for t in upcoming["tranches"])},
        "recent": [{"date": r["date"], "prid": r["prid"], "tranches": r["tranches"]} for r in auctions[:12]],
        "monthly": _monthly(auctions, fy, today),
    }
    return {"status": "ok", "detail": f"₹{raised:,.0f} crore raised in {len(this_year)} auctions since {fy:%d %b %Y}"
            + (f"; {checked} releases read" if checked else "")}


def _rss_date(pub):
    try:
        d = datetime.strptime(pub.strip()[:16], "%a, %d %b %Y")
        return d.strftime("%b %d, %Y")
    except (AttributeError, ValueError):
        return ""


def _monthly(auctions, fy, today):
    """Amount raised per month of this financial year (₹ crore)."""
    out = []
    y, m = fy.year, fy.month
    while (y, m) <= (today.year, today.month):
        key = f"{y}-{m:02d}"
        out.append({"month": key, "amount": sum(t["accepted"] for r in auctions if r["date"].startswith(key)
                                                for t in r["tranches"])})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out
