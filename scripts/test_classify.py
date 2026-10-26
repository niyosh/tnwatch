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

    total = len(CASES) + len(DISTRICT_CASES) + len(SAME_STORY_CASES)
    if failures:
        print(f"{len(failures)} of {total} checks failed:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"All {total} classifier checks passed.")


if __name__ == "__main__":
    main()
