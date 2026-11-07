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
    # found in the first week of automatic collection
    ("road", "சவுதி அரேபியாவில் சாலை விபத்து - குமரி மாவட்டத்தை சேர்ந்த 2 பேர் உயிரிழப்பு", None),
    ("road", "Road accident fatalities have declined in Chennai, says Commissioner", None),
    ("crime", "தூத்துக்குடியில் 4 நாட்களில் 7 கொலைகள்; தவெக அரசை கண்டிக்கும் ஸ்டாலின்", None),
    ("crime", "போக்சோ, போதைப்பொருள் வழக்குகளை விரைந்து விசாரிக்க புதிதாக 30 சிறப்பு நீதிமன்றங்கள் - தமிழக அரசு", None),
    ("crime", "சென்னை: மணல் கொள்ளையால் அரசுக்கு வருவாய் இழப்பு - லாரி உரிமையாளர்கள் சங்கத்தினர் குற்றச்சாட்டு", None),
    ("crime", "Tamil Nadu man stabbed to death in Dubai", None),
    ("crime", "தூத்துக்குடியில் விசிக முன்னாள் நிர்வாகி பாலன் வெட்டிக் கொலை", ("crime", {"Murder"}, "Thoothukudi")),
    ("corruption", "இலவச பேருந்து பயணம்.. தங்கம் கொடுப்பதும் லஞ்சம்தான்! சிவகங்கையில் சீமான் ஆவேசம்", None),
    ("corruption", "DMK Ex-Minister Arrested In Rs 100-Crore Bribery Case. MK Stalin Hits Out",
     ("corruption", {"Arrests & Chargesheets"}, None)),
    ("corruption", "திமுக மாஜிக்கள் மீதான ஊழல் வழக்குகள்: ஸ்டாலின் மீது தமிழக வெற்றிக் கழகத்தின் ஐடி விங் விமர்சனம்!", None),
    ("corruption", "நாகை: பெண்ணிடம் ரூ.7,500 லஞ்சம் வாங்கிய கிராம நிர்வாக அதிகாரி கைது",
     ("corruption", {"Bribery Cases", "Arrests & Chargesheets"}, "Nagapattinam")),
    # found in the second week: verdicts, follow-ups, quotes and other states' crimes
    ("crime", "TN govt appoints three special prosecutors to handle child rape cases against Veeramani", None),
    ("crime", "ஜெம் வீரமணி போக்சோ வழக்கு: 3 அரசு சிறப்பு வழக்கறிஞர்களை நியமித்த தமிழக அரசு", None),
    ("crime", "கவின் கொலை வழக்கில் திடீர் திருப்பம்..! தமிழக அரசின் மேல்முறையீடு தள்ளுபடி..! சுப்ரீம் கோர்ட் உத்தரவு.!!", None),
    ("crime", "கடலூரில் இளைஞர் கொலை வழக்கு: புதுச்சேரியை சேர்ந்தவருக்கு ஆயுள் தண்டனை", None),
    ("crime", "பெரம்பலூர்: மகளுக்கு பாலியல் தொல்லை; தந்தைக்கு 20 ஆண்டுகள் சிறை", None),
    ("crime", "DMK looted public money in Periyar's name: CM Vijay", None),
    ("crime", "தமிழக வரலாறே கண்டிராத ஒரு மாபெரும் அறிவுத் திருட்டு: அமைச்சர் அருண் ராஜ் காட்டம்..!", None),
    ("crime", "ஆவடி நூலகத்தில் போக்ஸோ குற்றவாளி ஜெம் வீரமணி புத்தகம் இடம்பெற்ற விவகாரம்: நூலக நூல் கொள்முதல் ஊழலில் "
              "மேலும் ஒரு புதிய அதிர்ச்சி!", ("corruption", set(), "Tiruvallur")),
    ("crime", "Chennai: SI, constable suspended for taking Rs 10,000 bribe to release stolen bike",
     ("corruption", {"Bribery Cases", "Officials Suspended"}, "Chennai")),
    ("crime", "மும்பையில் இருந்து வாங்கி வந்து வேலூரில் சப்ளை: போதை மாத்திரைகள் விற்பனைக்கு வைத்திருந்த 3 பேர் கைது",
     ("crime", {"Narcotics"}, "Vellore")),
    ("road", "சவூதி சாலை விபத்து: தமிழக செவிலியர்கள் இருவர் உள்பட ஐவர் உயிரிழப்பு", None),
    ("crime", "Sivakasi Firecracker Sales Surge Ahead of Diwali, Despite Online Fraud Concerns", None),
    ("crime", "Karnataka Ethanol Blend Row, Bengaluru Mass Murder, And Tamil Nadu Politics", None),
    ("crime", "Bengaluru mass murder: Accused identifies wife and mother-in-law's bodies in a forest in Tamil Nadu's Salem",
     None),
    ("crime", "Bengaluru family murders: Wife, mother-in-law's bodies recovered in TN; victims' gold ornaments missing", None),
    ("crime", "Chennai-based animal activist attacked in Karnataka, FIR registered", None),
    ("crime", "School van driver arrested for sexually assaulting five-year-old girl in Chennai",
     ("crime", {"Women Safety"}, "Chennai")),
    ("crime", "Woman murdered in Madurai: Minister orders probe", ("crime", {"Murder"}, "Madurai")),
    ("crime", "நாகை வேதாரண்யம் மீனவர்கள் மீது இலங்கை கடற்கொள்ளையர்கள் தாக்குதல்.. வலைகளை கொள்ளையடித்து அட்டகாசம்!",
     ("crime", {"Assault"}, "Nagapattinam")),
    ("crime", "ஆந்திராவில் இருந்து புதுக்கோட்டைக்கு கஞ்சா கடத்திய 2 பெண்கள் கைது", ("crime", {"Narcotics"}, "Pudukkottai")),
    ("crime", "Youth beaten up by gang in Tamil Nadu", ("crime", {"Assault"}, None)),
    ("road", "When Mammootty's Car Hit a 10-Year-Old Boy : V.K. Sreeraman Remembers Ooty Accident", None),
    ("road", "நாகை: வாகன விபத்தில் உயிரிழந்த காவலருக்கு முதலமைச்சர் நிதியுதவி அறிவிப்பு", None),
    ("road", "Chennai: Two women killed, 18 injured after van rams into bus", ("road", {"Bus", "Car / Van"}, "Chennai")),
]
# Types a headline must not get
NOT_TYPES = {
    "School van driver arrested for sexually assaulting five-year-old girl in Chennai": {"Assault"},
}

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
    ("Tamil Nadu Bus Accidents Kill One, Injure 58", 1, 58),
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


def story(title, cat, types, district, day="2026-10-26", deaths=0):
    return {"title": title, "cat": cat, "types": types, "district": district, "date": day,
            "lang": fd.script_lang(title), "deaths": deaths}


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
    # one crash, datelined Chennai by one outlet and Mamallapuram (Chengalpattu) by another
    (story("Two women killed, nine injured as van collides with government bus near Mamallapuram", "road",
           ["Bus", "Car / Van"], "Chengalpattu", "2026-11-06", deaths=2),
     story("Chennai: Two women killed, 18 injured after van rams into bus", "road", ["Bus", "Car / Van"], "Chennai",
           "2026-11-06", deaths=2), True),
    # different death tolls in one district on one day: two crashes
    (story("Two killed as car hits lorry in Chennai", "road", ["Car / Van", "Lorry / Truck"], "Chennai", deaths=2),
     story("சென்னையில் கார் விபத்தில் 4 பேர் பலி", "road", ["Car / Van"], "Chennai", deaths=4), False),
    # ... unless one report is a toll update
    (story("Bus overturns near Salem, two killed", "road", ["Bus"], "Salem", deaths=2),
     story("சேலம் பேருந்து விபத்து: பலி எண்ணிக்கை 4 ஆக உயர்வு", "road", ["Bus"], "Salem", deaths=4), True),
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
        if NOT_TYPES.get(title, set()) & set(gtypes):
            failures.append(f"{title!r} should not be {sorted(NOT_TYPES[title] & set(gtypes))}")
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
    # data.gov.in NCRB row: three year columns plus 2022-only population, crime rate and chargesheet rate
    row = {"sl__no_": "26", "state_ut": "Tamil Nadu", "_2020": "891700", "_2021": "322852", "_2022": "193913",
           "mid_year_projected_population__in_lakhs___2022_": "767.1",
           "rate_of_total_cognizable_ipc_crimes__2022_": "252.8", "chargesheeting_rate__2022_": "70.7"}
    fields = [{"id": "_2020", "name": "2020"}, {"id": "_2021", "name": "2021"}, {"id": "_2022", "name": "2022"},
              {"id": "rate_of_total_cognizable_ipc_crimes__2022_", "name": "Rate of Total Cognizable IPC Crimes (2022)"}]
    series, extras = fd.parse_datagov_row(row, fields)
    if [(p["year"], p["value"]) for p in series] != [("2020", 891700.0), ("2021", 322852.0), ("2022", 193913.0)] \
            or extras.get("Rate of Total Cognizable IPC Crimes (2022)") != 252.8 \
            or extras.get("chargesheeting_rate__2022_") != 70.7:
        official.append(f"data.gov.in row parsed as {series}, {extras}")
    if [p["value"] for p in fd.first_per_year([{"year": "2022", "value": 1}, {"year": "2022", "value": 2}])] != [1]:
        official.append("repeated years are not dropped")
    failures += official

    total = len(CASES) + len(DISTRICT_CASES) + len(SAME_STORY_CASES) + len(CASUALTY_CASES) + 5
    if failures:
        print(f"{len(failures)} of {total} checks failed:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"All {total} classifier checks passed.")


if __name__ == "__main__":
    main()
