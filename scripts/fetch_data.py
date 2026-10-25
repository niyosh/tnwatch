"""Fetch every dashboard figure from public sources and write data/auto.js.

Sources
  - Google News RSS search feeds  -> news list, news-reported crime and corruption counts, district map
  - data.gov.in API (sources.json) -> official NCRB crime totals, GSDP (needs DATA_GOV_IN_API_KEY)

Run once a day:  python scripts/fetch_data.py
Uses only the Python standard library.
"""

import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JS = os.path.join(ROOT, "data", "auto.js")
HISTORY = os.path.join(ROOT, "data", "history.json")
SOURCES = os.path.join(ROOT, "scripts", "sources.json")

IST = timezone(timedelta(hours=5, minutes=30))
KEEP_DAYS = 70
UA = "Mozilla/5.0 (compatible; TamilNaduWatch/1.0; +daily public-data dashboard)"

# ---------------------------------------------------------------------------
# Classification rules (matched against headlines, case-insensitive)
# ---------------------------------------------------------------------------
CRIME_TYPES = {
    "Murder": ["murder", "murdered", "hacked to death", "stabbed to death", "bludgeoned", "homicide"],
    "Theft": ["theft", "stolen", "burglary", "chain snatch", "snatched", "house break"],
    "Robbery": ["robbery", "robbed", "dacoity", "looted"],
    "Assault": ["assault", "attacked", "stabbed", "beaten up", "acid attack"],
    "Cyber Crime": ["cyber", "online fraud", "digital arrest", "phishing", "online scam", "investment scam"],
    "Women Safety": ["rape", "sexual assault", "molest", "sexual harassment", "pocso", "dowry", "eve teas"],
    "Narcotics": ["ganja", "narcotic", "ndps", "drug peddl", "methamphetamine", "heroin", "drugs seized"],
}
CRIME_ICONS = {
    "Murder": "fa-skull-crossbones", "Theft": "fa-bag-shopping", "Robbery": "fa-sack-dollar",
    "Assault": "fa-hand-fist", "Cyber Crime": "fa-laptop-code", "Women Safety": "fa-person-dress",
    "Narcotics": "fa-pills",
}
# Headlines containing these are not counted as crime (wildlife, accidents, politics)
CRIME_EXCLUDE = ["elephant", "leopard", "tiger", "bear attack", "dog attack", "accident", "crash",
                 "attacks cm", "attacks govt", "attacks dmk", "attacks aiadmk", "attacks bjp", "attacks tvk"]

CORRUPTION_TYPES = {
    "Bribery Cases": ["bribe", "bribery", "caught accepting", "trap"],
    "Vigilance Raids & Searches": ["raid", "searches", "search operation"],
    "Disproportionate Assets": ["disproportionate assets", "da case", "illegal assets"],
    "Officials Suspended": ["suspended", "suspension"],
    "Arrests & Chargesheets": ["arrested", "chargesheet", "charge sheet", "convicted", "sentenced"],
}
CORRUPTION_ICONS = {
    "Bribery Cases": "fa-hand-holding-dollar", "Vigilance Raids & Searches": "fa-magnifying-glass",
    "Disproportionate Assets": "fa-briefcase", "Officials Suspended": "fa-user-slash",
    "Arrests & Chargesheets": "fa-gavel",
}
CORRUPTION_GATE = ["bribe", "corruption", "dvac", "vigilance", "disproportionate assets", "anti-corruption"]

DEV_TAGS = {
    "Infrastructure": ["metro", "highway", "bridge", "airport", "port ", "railway", "flyover"],
    "Development": ["investment", "industrial", "factory", "plant", "mou", "jobs", "project"],
    "Policy": ["scheme", "policy", "budget", "assembly", "bill ", "government order", "cabinet"],
}

# District names and common spellings / major towns -> district
DISTRICTS = {
    "Chennai": ["chennai", "madras"], "Tiruvallur": ["tiruvallur", "thiruvallur", "avadi", "ponneri"],
    "Chengalpattu": ["chengalpattu", "tambaram", "mamallapuram"], "Kanchipuram": ["kanchipuram", "kancheepuram", "sriperumbudur"],
    "Ranipet": ["ranipet", "arakkonam"], "Vellore": ["vellore", "gudiyatham"], "Tirupathur": ["tirupathur", "tirupattur", "ambur", "vaniyambadi"],
    "Krishnagiri": ["krishnagiri", "hosur"], "Dharmapuri": ["dharmapuri"], "Salem": ["salem", "attur", "mettur"],
    "Tiruvannamalai": ["tiruvannamalai", "thiruvannamalai"], "Villupuram": ["villupuram", "viluppuram", "tindivanam"],
    "Cuddalore": ["cuddalore", "chidambaram", "neyveli"], "Kallakurichi": ["kallakurichi"], "Nilgiris": ["nilgiris", "ooty", "udhagamandalam", "coonoor"],
    "Erode": ["erode", "gobichettipalayam"], "Namakkal": ["namakkal", "tiruchengode", "rasipuram"], "Perambalur": ["perambalur"],
    "Ariyalur": ["ariyalur"], "Mayiladuthurai": ["mayiladuthurai"], "Coimbatore": ["coimbatore", "pollachi", "mettupalayam"],
    "Tiruppur": ["tiruppur", "tirupur"], "Karur": ["karur"], "Tiruchirappalli": ["tiruchirappalli", "tiruchi", "trichy"],
    "Thanjavur": ["thanjavur", "tanjore", "kumbakonam"], "Tiruvarur": ["tiruvarur", "thiruvarur"], "Nagapattinam": ["nagapattinam", "velankanni"],
    "Theni": ["theni", "bodinayakanur"], "Dindigul": ["dindigul", "palani", "kodaikanal"], "Madurai": ["madurai"],
    "Pudukkottai": ["pudukkottai"], "Virudhunagar": ["virudhunagar", "sivakasi", "rajapalayam"], "Sivaganga": ["sivaganga", "karaikudi"],
    "Ramanathapuram": ["ramanathapuram", "rameswaram"], "Tenkasi": ["tenkasi"], "Tirunelveli": ["tirunelveli", "nellai"],
    "Thoothukudi": ["thoothukudi", "tuticorin", "kovilpatti"], "Kanyakumari": ["kanyakumari", "kanniyakumari", "nagercoil"],
}
DISTRICT_RE = [(d, re.compile(r"(?<![-\w])(" + "|".join(map(re.escape, names)) + r")\b", re.I)) for d, names in DISTRICTS.items()]
NOT_TN_RE = re.compile(r"winston|massachusetts|oregon|salem,? (ma|or|nh|va)\b", re.I)
TN_RE = re.compile(r"\b(tamil nadu|tamilnadu|tn)\b", re.I)

BIG_CITIES = "(Chennai OR Coimbatore OR Madurai OR Tiruchi OR Salem OR Tirunelveli OR Vellore OR Erode)"


def gnews_url(query):
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def or_terms(words):
    return "(" + " OR ".join(f'"{w}"' if " " in w else w for w in words) + ")"


def build_queries():
    """(bucket, hint, query) for every feed we read."""
    qs = []
    for ctype, words in CRIME_TYPES.items():
        terms = or_terms(words[:5])
        for when in ("1d", "7d", "30d"):
            qs.append(("crime", ctype, f'{terms} "Tamil Nadu" when:{when}'))
            qs.append(("crime", ctype, f"{terms} {BIG_CITIES} when:{when}"))
    corr = or_terms(["bribe", "DVAC", "disproportionate assets", "vigilance and anti-corruption", "corruption case"])
    for when in ("1d", "7d", "30d"):
        qs.append(("corruption", None, f'{corr} "Tamil Nadu" when:{when}'))
        qs.append(("corruption", None, f"{corr} {BIG_CITIES} when:{when}"))
    dev = or_terms(["metro", "investment", "scheme", "industrial", "project", "policy"])
    qs.append(("development", None, f'{dev} "Tamil Nadu" government when:3d'))
    return qs


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean_title(raw):
    # Google News titles end in " - Source Name"
    return re.sub(r"\s+-\s+[^-]+$", "", raw or "").strip()


def norm_key(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower())[:80]


STOPWORDS = set("""the a an in of for to on at by with and or from as is are was were be been after over into near
    his her their its this that who what how why case cases police tamil nadu district city said says new two three
    four five one man men woman women youth held arrested booked""".split())


def tokens(title):
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 2 and w not in STOPWORDS}


def dedupe(history):
    """Merge stories that are the same incident reported by different outlets.

    Two headlines in the same category, within 2 days, sharing at least half of their
    meaningful words are treated as one story (the earliest one is kept)."""
    arts = history.get("articles", {})
    kept = []  # (key, article, tokens, day)
    removed = 0
    for key, a in sorted(arts.items(), key=lambda kv: kv[1]["ts"]):
        tk = tokens(a["title"])
        day = datetime.fromisoformat(a["date"]).toordinal()
        dup = None
        if len(tk) >= 3:
            for k2, a2, tk2, day2 in reversed(kept):
                if day - day2 > 2:
                    break
                if a2["cat"] == a["cat"] and len(tk2) >= 3 and len(tk & tk2) / len(tk | tk2) >= 0.5:
                    dup = a2
                    break
        if dup:
            dup["types"] = sorted(set(dup["types"]) | set(a["types"]))
            dup["district"] = dup["district"] or a["district"]
            dup["also"] = dup.get("also", 1) + 1
            history.setdefault("merged", {})[key] = a["date"]
            del arts[key]
            removed += 1
        else:
            kept.append((key, a, tk, day))
    return removed


def match_any(text, words):
    t = text.lower()
    return any(w in t for w in words)


def find_district(text):
    for d, rx in DISTRICT_RE:
        if rx.search(text):
            return d
    return None


def classify(bucket, hint, title):
    """Return (category, types) or None when the headline is not relevant."""
    if NOT_TN_RE.search(title):
        return None
    district = find_district(title)
    if not (district or TN_RE.search(title)):
        return None
    if bucket == "crime":
        types = [t for t, w in CRIME_TYPES.items() if match_any(title, w)]
        if not types or match_any(title, CRIME_EXCLUDE):
            return None
        return ("crime", types), district
    if bucket == "corruption":
        if not match_any(title, CORRUPTION_GATE):
            return None
        types = [t for t, w in CORRUPTION_TYPES.items() if match_any(title, w)]
        return ("corruption", types or ["Other Corruption News"]), district
    tag = next((t for t, w in DEV_TAGS.items() if match_any(title, w)), "Development")
    return ("development", [tag]), district


def fetch_news(history, status):
    articles = history.setdefault("articles", {})
    ok = fail = added = 0
    for bucket, hint, query in build_queries():
        try:
            root = ET.fromstring(http_get(gnews_url(query)))
            ok += 1
        except Exception as e:  # keep going; one feed failing is fine
            fail += 1
            print(f"  ! feed failed: {query[:60]}… ({e})", file=sys.stderr)
            continue
        for item in root.iter("item"):
            title = clean_title(item.findtext("title"))
            link = item.findtext("link") or ""
            src = item.findtext("source") or ""
            try:
                published = parsedate_to_datetime(item.findtext("pubDate")).astimezone(IST)
            except Exception:
                continue
            key = norm_key(title)
            if not key or key in history.get("merged", {}):
                continue
            result = classify(bucket, hint, title)
            if not result:
                continue
            (cat, types), district = result
            prev = articles.get(key)
            if prev:
                # same story seen through another feed
                if prev["cat"] == cat:
                    prev["types"] = sorted(set(prev["types"]) | set(types))
                elif prev["cat"] == "development":
                    prev["cat"], prev["types"] = cat, types
                continue
            articles[key] = {
                "title": title, "url": link, "source": src, "cat": cat, "types": types,
                "district": district, "date": published.strftime("%Y-%m-%d"),
                "ts": published.isoformat(),
            }
            added += 1
        time.sleep(1.0)  # be polite to the feed server
    status.append({
        "name": "Google News RSS (news reports)",
        "url": "https://news.google.com/",
        "status": "ok" if ok and not fail else ("partial" if ok else "error"),
        "detail": f"{ok} feeds read, {fail} failed, {added} new articles",
    })


def prune(history, today):
    cutoff = (today - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    arts = history.get("articles", {})
    for k in [k for k, a in arts.items() if a["date"] < cutoff]:
        del arts[k]
    merged = history.get("merged", {})
    for k in [k for k, d in merged.items() if d < cutoff]:
        del merged[k]
    history.setdefault("since", today.strftime("%Y-%m-%d"))


def window_counts(arts, cat, types, today, start_back, length, since):
    """Counts per type for days [today-start_back-length+1 .. today-start_back]; None if before history began."""
    end = today - timedelta(days=start_back)
    begin = end - timedelta(days=length - 1)
    if begin.strftime("%Y-%m-%d") < since:
        return None
    b, e = begin.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    counts = {t: 0 for t in types}
    for a in arts:
        if a["cat"] == cat and b <= a["date"] <= e:
            for t in a["types"]:
                if t in counts:
                    counts[t] += 1
    return counts


def build_periods(history, cat, types, icons, today):
    arts = list(history.get("articles", {}).values())
    # Feeds return at most ~100 stories per search, so older days are under-sampled until the
    # script has been running daily. Changes are only shown once both windows were collected live.
    since = history.get("since", today.strftime("%Y-%m-%d"))
    out = {}
    for name, length in (("today", 1), ("week", 7), ("month", 30)):
        cur = window_counts(arts, cat, types, today, 0, length, "0000")
        prev = window_counts(arts, cat, types, today, length, length, since)
        rows = []
        for t in types:
            change = None
            if prev is not None and prev[t]:
                change = round((cur[t] - prev[t]) / prev[t] * 100)
            rows.append({"type": t, "icon": icons.get(t, "fa-circle"), "count": cur[t], "change": change})
        out[name] = rows
    return out


def fetch_datagov(history, status):
    cfg = json.load(open(SOURCES, encoding="utf-8"))
    key = os.environ.get("DATA_GOV_IN_API_KEY", "").strip()
    cache = history.setdefault("official", {})
    for src in cfg.get("datagov", []):
        entry = {"name": src["name"], "url": src.get("page") or "https://www.data.gov.in/"}
        if not src.get("resource"):
            entry.update(status="not configured", detail="Add a data.gov.in resource id in scripts/sources.json")
            status.append(entry)
            continue
        if not key:
            entry.update(status="needs key" if src["id"] not in cache else "cached",
                         detail="Set DATA_GOV_IN_API_KEY (free at data.gov.in) to refresh")
            status.append(entry)
            continue
        url = (f"https://api.data.gov.in/resource/{src['resource']}?"
               + urllib.parse.urlencode({"api-key": key, "format": "json", "limit": 100}))
        try:
            data = json.loads(http_get(url))
            row = next(r for r in data.get("records", [])
                       if any("tamil nadu" in str(v).lower() for v in r.values()))
            series = []
            for k, v in row.items():
                m = re.search(r"(19|20)\d\d(?:[-_]\d\d)?", k)
                if not m:
                    continue
                try:
                    val = float(str(v).replace(",", ""))
                except ValueError:
                    continue
                series.append({"year": m.group(0).replace("_", "-"), "value": round(val / float(src.get("divide", 1)), 2)})
            series.sort(key=lambda s: s["year"])
            if not series:
                raise ValueError("no year columns found")
            cache[src["id"]] = {"use": src["use"], "name": src["name"], "url": entry["url"],
                                "unit": src.get("unit", ""), "series": series,
                                "fetched": datetime.now(IST).strftime("%Y-%m-%d")}
            entry.update(status="ok", detail=f"{len(series)} years, latest {series[-1]['year']}")
        except StopIteration:
            entry.update(status="error", detail="No Tamil Nadu row in this dataset")
        except Exception as e:
            entry.update(status="error" if src["id"] not in cache else "cached", detail=str(e)[:120])
        status.append(entry)


def main():
    now = datetime.now(IST)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    history = json.load(open(HISTORY, encoding="utf-8")) if os.path.exists(HISTORY) else {}
    status = []

    print("Fetching news feeds…")
    fetch_news(history, status)
    print("Fetching data.gov.in datasets…")
    fetch_datagov(history, status)
    prune(history, today)
    print(f"Merged {dedupe(history)} duplicate stories")

    arts = sorted(history["articles"].values(), key=lambda a: a["ts"], reverse=True)
    month_start = (today - timedelta(days=29)).strftime("%Y-%m-%d")

    districts = {d: 0 for d in DISTRICTS}
    for a in arts:
        if a["cat"] == "crime" and a["date"] >= month_start and a["district"]:
            districts[a["district"]] += 1

    def latest(cat, n):
        return [{k: a[k] for k in ("title", "url", "source", "date", "district")} | {"tag": a["types"][0]}
                for a in arts if a["cat"] == cat][:n]

    news = []
    for a in arts[:60]:
        tag = {"crime": "Crime", "corruption": "Corruption"}.get(a["cat"], a["types"][0])
        news.append({"title": a["title"], "url": a["url"], "source": a["source"], "date": a["date"], "tag": tag})

    since = history.get("since", today.strftime("%Y-%m-%d"))

    def daily(cat):
        days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
        counts = {d: 0 for d in days}
        for a in arts:
            if a["cat"] == cat and a["date"] in counts:
                counts[a["date"]] += 1
        # days before the script started running daily are under-sampled by the feeds
        return [{"date": d, "count": counts[d], "partial": d < since} for d in days]

    recent_crime = [{k: a.get(k) for k in ("title", "url", "source", "date", "district")} | {"tag": a["types"][0], "types": a["types"], "outlets": a.get("also", 1)}
                    for a in arts if a["cat"] == "crime" and a["date"] >= month_start]

    official = history.get("official", {})
    out = {
        "generatedAt": now.isoformat(timespec="minutes"),
        "crime": {
            "periods": build_periods(history, "crime", list(CRIME_TYPES), CRIME_ICONS, today),
            "districts": districts,
            "latest": latest("crime", 6),
            "recent": recent_crime[:500],
            "daily": daily("crime"),
            "official": next((v for v in official.values() if v["use"] == "crime_official"), None),
        },
        "corruption": {
            "periods": build_periods(history, "corruption", list(CORRUPTION_TYPES) + ["Other Corruption News"],
                                     CORRUPTION_ICONS, today),
            "latest": latest("corruption", 6),
            "daily": daily("corruption"),
        },
        "news": news[:8],
        "economy": next((v for v in official.values() if v["use"] == "economy"), None),
        "sources": status,
    }

    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, separators=(",", ":"))
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("/* AUTO-GENERATED by scripts/fetch_data.py — do not edit by hand. */\n")
        f.write("window.AUTO_DATA = ")
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    # Open data downloads
    with open(os.path.join(ROOT, "data", "auto.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data", "stories.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "category", "types", "district", "title", "source", "url", "outlets"])
        for a in arts:
            w.writerow([a["date"], a["cat"], "; ".join(a["types"]), a["district"] or "", a["title"], a["source"], a["url"], a.get("also", 1)])

    month = out["crime"]["periods"]["month"]
    print(f"Done. {len(arts)} stored articles; crime reports (30d): {sum(r['count'] for r in month)}; "
          f"wrote {os.path.relpath(OUT_JS, ROOT)}")
    for s in status:
        print(f"  [{s['status']}] {s['name']}: {s['detail']}")


if __name__ == "__main__":
    main()
