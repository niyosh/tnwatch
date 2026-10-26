"""Checks for the headline classifier. Run: python scripts/test_classify.py

The hourly job runs these before publishing, so a broken rule never reaches the site.
When a real headline is misclassified, add it here together with the fix.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_data as fd  # noqa: E402

# (bucket, headline, expected) — expected is None (not counted) or (category, required types, district)
CASES = [
    # English
    ("crime", "Man stabbed to death in Thoothukudi", ("crime", {"Murder"}, "Thoothukudi")),
    ("crime", "Man murdered in Winston-Salem on Goldfloss Street", None),
    ("crime", "Two killed in elephant attacks in Coimbatore, the Nilgiris", None),
    ("crime", "Attempt to murder case: two held in Madurai", ("crime", {"Assault"}, "Madurai")),
    ("crime", "Madras High Court quashes chargesheet in Sivaganga murder case", ("crime", {"Murder"}, "Sivaganga")),
    ("crime", "Stalin slams TVK government over rising murders in Tamil Nadu", None),
    ("crime", "Grape farmers in Theni seek better prices", None),
    ("crime", "Tamil Nadu heroine opens up about her new film in Chennai", None),
    ("crime", "Youth held with ganja escapes from custody in Chennai", ("crime", {"Narcotics"}, "Chennai")),
    ("corruption", "Panchayat secretary arrested for accepting ₹20,000 bribe in the Nilgiris",
     ("corruption", {"Bribery Cases", "Arrests & Chargesheets"}, "Nilgiris")),
    ("corruption", "Vigilance raids at Hosur and Karur offices", ("corruption", {"Vigilance Raids & Searches"}, "Krishnagiri")),
    # Tamil
    ("crime", "சேலத்தில் பிரபல ரவுடி 5 பேர் கொண்ட கும்பலால் கொலை", ("crime", {"Murder"}, "Salem")),
    ("crime", "கடன் தொல்லையால் விவசாயி தற்கொலை - தஞ்சாவூர்", None),
    ("crime", "மனைவி கொலை: கணவர் தற்கொலை - மதுரையில் சோகம்", ("crime", {"Murder"}, "Madurai")),
    ("crime", "கோவையில் கஞ்சா விற்ற 3 பேர் கைது", ("crime", {"Narcotics"}, "Coimbatore")),
    ("crime", "ஒசூா் அருகே வீட்டின் கதவை உடைத்து 10 பவுன் நகை, ரூ. 50 ஆயிரம் திருட்டு", ("crime", {"Theft"}, "Krishnagiri")),
    ("crime", "தினமும் கொலைகளை எண்ணும் கொடிய நிலையில் தமிழ்நாடு இருக்கிறது: மு.க. ஸ்டாலின் தாக்கு", None),
    ("crime", "வாக்கு திருட்டுக்கு எதிராக நவ.1ல் பேரணி - தமிழக காங்கிரஸ்", None),
    ("crime", "ஹட்டன் நகரில் பாரிய திருட்டு!", None),
    ("crime", "செங்கல்பட்டில் இளைஞர் கொலை முயற்சி: 2 பேர் கைது", ("crime", {"Assault"}, "Chengalpattu")),
    ("crime", "சென்னை உயர்நீதிமன்ற மதுரைக் கிளை உத்தரவு: கொலை வழக்கில் ஜாமீன்", ("crime", {"Murder"}, "Madurai")),
    ("crime", "நெல்லையில் மூதாட்டியிடம் 5 பவுன் நகை பறிப்பு", ("crime", {"Theft"}, "Tirunelveli")),
    ("crime", "கடலுாரில் பைக் திருடிய சென்னை வாலிபர் கைது", ("crime", {"Theft"}, "Cuddalore")),
    ("crime", "தவெக அரசின் துணையோடுதான் போதைப்பொருள் கடத்தல் நடக்கிறதா? - இபிஎஸ் கேள்வி", None),
    ("crime", "அரிவாள் வெட்டு, சிறுமிகள் கடத்தல்... தூத்துக்குடியில் நாளுக்கு நாள் சட்டம்-ஒழுங்கு சீர்கேடு", None),
    ("crime", "Velachery techie loses ₹12 lakh in digital arrest scam", ("crime", {"Cyber Crime"}, "Chennai")),
    ("crime", "Male Suspect from DeKalb Charged with Attempted Murder After Stabbing Man at Salem", None),
    ("crime", "நாகை போதைப்பொருள் வழக்கில் மவுனம் ஏன்? - EPS", None),
    ("crime", "சர்வதேச போதைப்பொருள் மாபியாவின் கூடாரமா தவெக? - நயினார் நாகேந்திரன்", None),
    ("crime", "போதைப்பொருள் விற்பனையில் கூட்டணி: திமுக, தவெக நிர்வாகிகள் கைது", ("crime", {"Narcotics"}, None)),
    ("corruption", "லஞ்சம் வாங்கிய வருவாய் ஆய்வாளர் கைது - திருச்சி",
     ("corruption", {"Bribery Cases", "Arrests & Chargesheets"}, "Tiruchirappalli")),
]

CASES += [
    # Road accidents
    ("road", "Two Killed in Road Accident in Erode District", ("road", set(), "Erode")),
    ("road", "Omni bus cleaner killed, over 40 passengers injured in accident on highway in Tiruchi district",
     ("road", {"Bus"}, "Tiruchirappalli")),
    ("road", "தூத்துக்குடி: பைக் மீது லாரி மோதிய விபத்தில் வாலிபர் பலி",
     ("road", {"Two-wheeler", "Lorry / Truck"}, "Thoothukudi")),
    ("road", "சுற்றுலா வேன் கவிழ்ந்து 14 பேர் படுகாயம் - கொடைக்கானல்", ("road", {"Car / Van"}, "Dindigul")),
    ("road", "Salem High football bus crash leaves 25 injured; one remains hospitalized", None),
    ("road", "ராஜஸ்தான்: சாலை விபத்தில் 6 போ் உயிரிழப்பு", None),
    ("road", "சிவகாசி பட்டாசு ஆலை வெடி விபத்தில் 3 பேர் பலி", None),
    ("road", "Driver dies as TNSTC bus buried under landslide on Mettupalayam-Coonoor Ghat Road", None),
    ("road", "Road Accidents Mar Festivities Across India; 40 Killed Across MP, Punjab, UP, Tamil Nadu And Bengal", None),
    ("road", "Three dead in crash along Salem Main Road in St. Ann last night", None),
    ("road", "Kerala man dies as car rams lorry near Coimbatore", ("road", {"Car / Van"}, "Coimbatore")),
]

# (headline, deaths, injured) named in road accident headlines
CASUALTY_CASES = [
    ("2 Killed As Bike Bursts Into Flames After Head-On Crash With Another 2-Wheeler In Tamil Nadu", 2, 0),
    ("Omni bus cleaner killed, over 40 passengers injured in accident on highway in Tiruchi district", 1, 40),
    ("Chennai bus-motorcycle collision injures three teens, driver assaulted", 0, 3),
    ("Class 12 student killed and four injured in accident on Tambaram-Maduravoyal bypass", 1, 4),
    ("60-year-old man dies in road accident in Madurai city", 1, 0),
    ("Diesel tanker overturns on Salem highway, driver injured", 0, 1),
    ("கிருஷ்ணகிரியில் சாலை விபத்தில் 2 பேர் உடல் கருகி பலி", 2, 0),
    ("மாத்தூர் அருகே இருசக்கர வாகனங்கள் நேருக்கு நேர் மோதல்: தீயில் கருகி இருவர் பலி", 2, 0),
    ("ஆந்திரம்: சாலை விபத்தில் ஐவா் உயிரிழப்பு", 5, 0),
    ("சுற்றுலா வேன் கவிழ்ந்து 14 பேர் படுகாயம்", 0, 14),
]

# RBI tables, trimmed copies of the real layout
RESULT_HTML = """<p>Date : Oct 13, 2026</p><table>
<tr><td>Sr. No</td><td>State</td><td>Amount to be raised</td><td>Amount Accepted</td><td>Cut off Price/Yield</td><td>Tenor</td></tr>
<tr><td>9.</td><td>Odisha</td><td>500</td><td>500</td><td>96.79/7.8520</td><td>Re-issue of 7.16% Odisha SGS 2032</td></tr>
<tr><td>10.</td><td>Tamil Nadu</td><td>2000</td><td>2000</td><td>8.14</td><td>20</td></tr>
<tr><td>2000</td><td>-</td><td>-</td><td>25</td></tr>
<tr><td>3000</td><td>3000</td><td>97.10/8.18</td><td>Re-issue of 7.90% Tamil Nadu SGS 2056, issued on October 14, 2026</td></tr>
<tr><td>11.</td><td>Uttar Pradesh</td><td>1500</td><td>1500</td><td>8.11</td><td>12</td></tr>
<tr><td>Total</td><td>31200</td><td>30005</td></tr></table>"""
NOTICE_HTML = """<p>Date : Oct 23, 2026</p><table>
<tr><td>11.</td><td>Tamil Nadu</td><td>2500</td><td>Re-issue of 7.80% Tamil Nadu SGS 2041, issued on June 03, 2026</td><td>Price</td></tr>
<tr><td>2000</td><td>30</td><td>Yield</td></tr>
<tr><td>12.</td><td>Uttar Pradesh</td><td>500</td><td>Re-issue of 7.14% Uttar Pradesh SGS 2032</td><td>Price</td></tr>
</table><p>The auction will be conducted on the Reserve Bank of India Core Banking Solution (E-Kuber) system
on October 27, 2026 (Tuesday).</p>"""
LIAB_HTML = """<p>TABLE 176: STATE-WISE COMPOSITION OF OUTSTANDING LIABILITIES - 2024 (Concld.)</p><table>
<tr><td>State/Union Territory</td><td>Total Internal Debt</td><td>Outstanding Liabilities</td></tr>
<tr><td>1</td><td>13</td><td>20 = (14 to 19)</td></tr>
<tr><td>Kerala</td><td>3,00,000.0</td><td>4,00,000.0</td></tr>
<tr><td>Tamil Nadu</td><td>6,50,000.5</td><td>8,50,000.5</td></tr></table>
<p>TABLE 176: STATE-WISE COMPOSITION OF OUTSTANDING LIABILITIES - 2025 (Concld.)</p><table>
<tr><td>State/Union Territory</td><td>Total Internal Debt</td><td>Outstanding Liabilities</td></tr>
<tr><td>Tamil Nadu</td><td>7,29,411.5</td><td>9,55,690.5</td></tr></table>"""

DISTRICT_CASES = [
    ("Rising input costs erode margins of Tamil Nadu textile units", None),
    ("P Chidambaram questions the Centre on GST", None),
    ("எடப்பாடி பழனிசாமி தமிழக அரசு மீது குற்றச்சாட்டு", None),
    ("பழனியில் பக்தர்கள் கூட்டம்", "Dindigul"),
    ("காவல்துறை செயல்படும் லட்சணம் இதுதானா? எடப்பாடி பழனிச்ச", None),
    ("வடபழனியில் செல்போன் திருட்டு", "Chennai"),
    ("பெரம்பலூர் மாவட்டத்தில் 17 போ் கைது", "Perambalur"),
    ("வேலூரில் வீட்டில் திருட்டு", "Vellore"),
    ("ஈரோட்டில் இளைஞர் கைது", "Erode"),
    ("Murder in Erode: two held", "Erode"),
]


def story(title, cat, types, district, day="2026-10-26"):
    return {"title": title, "cat": cat, "types": types, "district": district, "date": day,
            "lang": fd.script_lang(title)}


SAME_STORY_CASES = [
    # same incident, two Tamil outlets
    (story("சேலத்தில் பிரபல ரவுடி 5 பேர் கொண்ட கும்பலால் கொலை", "crime", ["Murder"], "Salem"),
     story("பட்டப்பகலில் ரவுடி வெட்டிக் கொலை... சேலத்தில் பரபரப்பு", "crime", ["Murder"], "Salem"), True),
    # same incident in English and Tamil
    (story("Rowdy hacked to death in Salem", "crime", ["Murder"], "Salem"),
     story("சேலத்தில் பிரபல ரவுடி 5 பேர் கொண்ட கும்பலால் கொலை", "crime", ["Murder"], "Salem"), True),
    # two different thefts in Chennai on the same day
    (story("Chain snatched from woman in Chennai's Anna Nagar", "crime", ["Theft"], "Chennai"),
     story("House burgled in Chennai's Velachery, 20 sovereigns stolen", "crime", ["Theft"], "Chennai"), False),
    # one crash, one report names the vehicle and the other doesn't
    (story("Class 12 student killed as car driven by minor crashes on Tambaram-Maduravoyal bypass road", "road",
           ["Car / Van"], "Chengalpattu"),
     story("Class 12 student killed and four injured in accident on Tambaram-Maduravoyal bypass", "road",
           ["Other"], "Chengalpattu"), True),
    # same type and district but days apart
    (story("Rowdy hacked to death in Salem", "crime", ["Murder"], "Salem", "2026-10-20"),
     story("சேலத்தில் ரவுடி கொலை", "crime", ["Murder"], "Salem", "2026-10-26"), False),
]


def main():
    failures = []
    for bucket, title, expected in CASES:
        got = fd.classify(bucket, title)
        if expected is None:
            if got is not None:
                failures.append(f"should be ignored: {title!r} -> {got}")
            continue
        cat, need, district = expected
        if got is None:
            failures.append(f"should count: {title!r} -> ignored")
            continue
        (gcat, gtypes), gdistrict = got
        if gcat != cat or not need <= set(gtypes) or gdistrict != district:
            failures.append(f"{title!r}: expected {cat}/{sorted(need)}/{district}, got {gcat}/{gtypes}/{gdistrict}")
        if "Murder" in gtypes and ("முயற்சி" in title or "attempt" in title.lower()):
            failures.append(f"attempt counted as murder: {title!r}")
    for title, district in DISTRICT_CASES:
        got = fd.find_district(title)
        if got != district:
            failures.append(f"district of {title!r}: expected {district}, got {got}")
    for a, b, expected in SAME_STORY_CASES:
        if fd.same_story(a, b) != expected:
            failures.append(f"same_story({a['title']!r}, {b['title']!r}) should be {expected}")
    for title, deaths, injured in CASUALTY_CASES:
        got = fd.casualties(title)
        if got != (deaths, injured):
            failures.append(f"casualties of {title!r}: expected {(deaths, injured)}, got {got}")

    official = []
    result = fd.official.parse_result(RESULT_HTML, 1)
    got = [(t["accepted"], t["yield"], t["tenor"]) for t in result["tranches"]]
    if result["date"] != "2026-10-13" or got != [(2000.0, 8.14, 20), (0.0, None, 25), (3000.0, 8.18, 30)]:
        official.append(f"auction result parsed as {result}")
    notice = fd.official.parse_notice(NOTICE_HTML, 2)
    if notice["auctionDate"] != "2026-10-27" or [(t["amount"], t["tenor"]) for t in notice["tranches"]] != [(2500.0, 15), (2000.0, 30)]:
        official.append(f"auction notice parsed as {notice}")
    years = fd.official.parse_liabilities(LIAB_HTML)
    if years.get(2025, {}).get("Tamil Nadu", {}).get("Outstanding Liabilities") != 955690.5 \
            or years.get(2024, {}).get("Kerala", {}).get("Outstanding Liabilities") != 400000.0:
        official.append(f"liabilities parsed as {years}")
    failures += official

    total = len(CASES) + len(DISTRICT_CASES) + len(SAME_STORY_CASES) + len(CASUALTY_CASES) + 3
    if failures:
        print(f"{len(failures)} of {total} checks failed:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"All {total} classifier checks passed.")


if __name__ == "__main__":
    main()
