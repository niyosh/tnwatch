"""Fetch every dashboard figure from public sources and write the files in data/.

Sources
  - Google News RSS search feeds, English and Tamil editions
      -> news lists, news-reported crime and corruption counts, district map, trends
  - data.gov.in API (scripts/sources.json)
      -> official NCRB crime totals, GSDP (needs a free DATA_GOV_IN_API_KEY)

Modes
  hourly  searches covering the last 24 hours (run every hour)
  full    also the 7- and 30-day searches and the official datasets (run once a day)

Usage:  python scripts/fetch_data.py [--mode hourly|full]
Fixes to the automatic classification go in scripts/corrections.json.
Uses only the Python standard library.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import official

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HISTORY = os.path.join(DATA, "history.json")
SOURCES = os.path.join(ROOT, "scripts", "sources.json")
CORRECTIONS = os.path.join(ROOT, "scripts", "corrections.json")

IST = timezone(timedelta(hours=5, minutes=30))
KEEP_DAYS = 70
UA = "Mozilla/5.0 (compatible; TamilNaduWatch/1.0; +https://github.com/niyosh/tnwatch)"

# ---------------------------------------------------------------------------
# Classification rules
#
# Every headline is matched against English and Tamil rules alike (the scripts
# never overlap). English words match from a word start, so "rape" does not
# fire on "grape". Tamil words are written as stems so suffixes still match
# (திருட -> திருட்டு, திருடிய, திருடன்).
# ---------------------------------------------------------------------------
CRIME_TYPES = {
    "Murder": ["murder", "hacked to death", "stabbed to death", "bludgeoned", "homicide", "honour killing",
               "கொலை"],
    "Theft": ["theft", "stolen", "burglary", "burgled", "chain snatch", "snatched", "house break",
              "திருட", "நகை பறிப்பு", "செயின் பறிப்பு", "சங்கிலி பறிப்பு"],
    "Robbery": ["robbery", "robbed", "dacoity", "looted",
                "கொள்ளை", "வழிப்பறி"],
    "Assault": ["assault", "attacked", "stabbed", "beaten up", "acid attack",
                "தாக்குதல்", "தாக்கிய", "தாக்கப்பட்ட", "அரிவாள் வெட்டு", "அரிவாளால் வெட்ட", "கத்திக்குத்து",
                "கத்தியால் குத்த"],
    "Cyber Crime": ["cyber", "online fraud", "digital arrest", "phishing", "online scam", "investment scam",
                    "சைபர்", "ஆன்லைன் மோசடி", "இணைய மோசடி", "இணையவழி மோசடி", "டிஜிட்டல் அரெஸ்ட்", "டிஜிட்டல் கைது"],
    "Women Safety": [r"rape\b", "raped", "rapist", "sexual assault", "molest", "sexual harassment", "pocso", "dowry",
                     "eve teas",
                     "பாலியல்", "போக்சோ", "போக்ஸோ", "வரதட்சணை", "பலாத்காரம்", "சில்மிஷம்"],
    "Narcotics": ["ganja", "narcotic", "ndps", "drug peddl", "methamphetamine", r"heroin\b", "drugs seized",
                  "கஞ்சா", "போதைப்பொருள்", "போதைப் பொருள்", "போதை மாத்திரை", "மெத்தம்பெட்டமைன்", "ஹெராயின்"],
}
CRIME_ICONS = {
    "Murder": "fa-skull-crossbones", "Theft": "fa-bag-shopping", "Robbery": "fa-sack-dollar",
    "Assault": "fa-hand-fist", "Cyber Crime": "fa-laptop-code", "Women Safety": "fa-person-dress",
    "Narcotics": "fa-pills",
}
# Not counted as crime: wildlife, accidents and political statements
CRIME_EXCLUDE = re.compile(
    r"\b(?:elephant|leopard|tiger|bear attack|dog attack|stray dog|accident|crash|slams|condemns|flays|lashes out|"
    r"questions|blames|hits out|takes a dig|law and order|law-and-order|"
    r"attacks (?:cm|govt|government|centre|dmk|aiadmk|bjp|tvk|congress|stalin|vijay|eps))"
    r"|யானை|சிறுத்தை|கரடி|காட்டெருமை|தெருநாய்|விபத்த|கண்டனம்|வாக்கு திருட்ட|தாக்கு(?=\s|$|[!.,:'\"’])"
    r"|கேள்வி|பாய்ச்சல்|சாடல்|விமர்சன|முதல்வரே|ஆட்சியில்|ஆட்சி தான்|அரசு மீது|அறிக்கை|பேட்டி|வலியுறுத்த"
    r"|கவனம் செலுத்த|சட்டம்.?ஒழுங்|மவுன|ஏன்(?=\s|\?|$)",
    re.I)
# "Attempt to murder" is an assault; suicide (தற்கொலை) and death threats are not murders
ATTEMPT_RE = re.compile(r"\battempt(?:ed)? to murder|\bmurder attempt|\battempted murder|கொலை ?முயற்சி", re.I)
NOT_MURDER_RE = re.compile(r"தற்கொலை|கொலை ?மிரட்டல்")

CORRUPTION_GATE = ["bribe", "corruption", "corrupt", "dvac", "vigilance", "disproportionate assets", "anti-corruption",
                   "லஞ்ச", "ஊழல்", "சொத்துக் குவிப்பு", "சொத்து குவிப்பு", "வருமானத்துக்கு அதிகமாக",
                   "வருமானத்திற்கு அதிகமாக", "முறைகேடு"]
CORRUPTION_TYPES = {
    "Bribery Cases": ["bribe", "caught accepting", "trap", "லஞ்சம்", "லஞ்சப்", "கையும் களவுமாக"],
    "Vigilance Raids & Searches": ["raid", "searches", "search operation", "சோதனை", "ரெய்டு"],
    "Disproportionate Assets": ["disproportionate assets", r"da case", "illegal assets", "சொத்துக் குவிப்பு",
                                "சொத்து குவிப்பு", "வருமானத்துக்கு அதிகமாக", "வருமானத்திற்கு அதிகமாக"],
    "Officials Suspended": ["suspended", "suspension", "பணியிடை நீக்க", "சஸ்பெண்ட்"],
    "Arrests & Chargesheets": ["arrested", "chargesheet", "charge sheet", "convicted", "sentenced",
                               "கைது", "குற்றப்பத்திரிகை", "தண்டனை", "சிறை"],
}
CORRUPTION_ICONS = {
    "Bribery Cases": "fa-hand-holding-dollar", "Vigilance Raids & Searches": "fa-magnifying-glass",
    "Disproportionate Assets": "fa-briefcase", "Officials Suspended": "fa-user-slash",
    "Arrests & Chargesheets": "fa-gavel",
}
DEV_TAGS = {
    "Infrastructure": ["metro", "highway", "bridge", "airport", "port ", "railway", "flyover",
                       "மெட்ரோ", "மேம்பால", "நெடுஞ்சாலை", "விமான நிலைய", "ரயில்"],
    "Development": ["investment", "industrial", "factory", "plant", "mou", "jobs", "project",
                    "முதலீடு", "தொழிற்சாலை", "தொழில் பூங்கா", "வேலைவாய்ப்பு", "திட்ட"],
    "Policy": ["scheme", "policy", "budget", "assembly", "bill ", "government order", "cabinet",
               "அரசாணை", "சட்டப்பேரவை", "மசோதா", "அமைச்சரவை", "கொள்கை"],
}

# Road accidents: an accident word plus a vehicle or road word, sorted by the vehicles involved
ROAD_GATE = ["road accident", "accident", "collision", "collided", "collides", "crash", "rammed", "rams ", "overturn",
             "hit-and-run", "hit and run", "run over", "runs over", "knocked down", "mowed down", "head-on", "skidded",
             "விபத்த", "மோதி", "மோதல்", "கவிழ்ந்", "கவிழ்த்", "நேருக்கு நேர்", "சக்கரத்தில் சிக்கி"]
ROAD_PLACE = ["road", "highway", r"nh\b", "bypass", "flyover", "vehicle", "சாலை", "நெடுஞ்சாலை", "வாகன"]
ROAD_TYPES = {
    "Two-wheeler": ["bike", "motorcycl", "two-wheeler", "two wheeler", "scooter", "moped", "pillion",
                    "பைக்", "இருசக்கர", "ஸ்கூட்டர்", "மொபெட்"],
    "Bus": [r"bus\b", "buses", "பேருந்த", "பஸ்"],
    "Lorry / Truck": ["lorr", "truck", "tanker", "tipper", "container", "trailer",
                      "லாரி", "டிப்பர்", "டேங்கர்", "கன்டெய்னர்", "கண்டெய்னர்"],
    "Car / Van": [r"car\b", r"cars\b", "suv", "jeep", r"van\b", r"cab\b", "taxi",
                  "கார்(?!த்)", "காரில்", "காரும்", "காரின்", "வேன்", "வேனில்", "ஜீப்"],
    "Pedestrian": ["pedestrian", "knocked down", "mowed down", "run over", "runs over", "walking", "crossing the road",
                   "பாதசாரி", "நடந்து சென்ற", "சாலையைக் கடக்க", "சாலையை கடக்க"],
    "Other": ["autorickshaw", r"auto\b", "tractor", "ஆட்டோ", "டிராக்டர"],
}
ROAD_ICONS = {
    "Two-wheeler": "fa-motorcycle", "Bus": "fa-bus", "Lorry / Truck": "fa-truck", "Car / Van": "fa-car-side",
    "Pedestrian": "fa-person-walking", "Other": "fa-car-burst",
}
# Not road accidents: fires, explosions, drowning, rail, air, landslides, VIP convoys
ROAD_EXCLUDE = re.compile(
    r"\b(?:fire accident|blaze|cracker|firecracker|fireworks|explosion|blast|boiler|electrocut|drown|landslide|"
    r"wall collapse|building collapse|train|rail|flight|plane|helicopter|boat|ship|convoy|workplace|quarry)"
    r"|தீ விபத்த|பட்டாசு|வெடி விபத்த|வெடித்து|மின்சாரம் தாக்கி|மின் விபத்த|நீரில் மூழ்கி|ரயில்|விமான|படகு"
    r"|நிலச்சரிவ|சுவர் இடிந்து|கான்வாய்", re.I)
# Roundups that add up several states ("40 killed across MP, Punjab, UP, Tamil Nadu…") are not Tamil Nadu figures
OTHER_STATES = re.compile(
    r"\b(?:across india|nationwide|across the country|madhya pradesh|mp|punjab|uttar pradesh|up|bengal|kerala|karnataka|"
    r"andhra|telangana|maharashtra|gujarat|rajasthan|bihar|odisha|haryana|assam|jharkhand)\b"
    r"|கேரள|கர்நாடக|ஆந்திர|தெலங்கானா|மகாராஷ்டிர|ராஜஸ்தான்|உத்தரப் ?பிரதேச|மத்தியப் ?பிரதேச|பீகார்|ஒடிசா", re.I)
# Casualties named in a headline ("2 killed", "Two killed", "இருவர் பலி", "14 பேர் படுகாயம்").
# Without a number, a death or injury word counts as one; "60-year-old" and "Class 12" are not counts.
NUM_EN = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
          "ten": 10, "eleven": 11, "twelve": 12, "a dozen": 12, "dozen": 12, "couple": 2}
NUM_TA = {"ஒருவர்": 1, "இருவர்": 2, "மூவர்": 3, "நால்வர்": 4, "ஐவர்": 5, "இரண்டு பேர்": 2, "மூன்று பேர்": 3,
          "நான்கு பேர்": 4, "ஐந்து பேர்": 5, "ஆறு பேர்": 6, "ஏழு பேர்": 7, "எட்டு பேர்": 8, "பத்து பேர்": 10}
COUNT_EN = r"(\d{1,3}|" + "|".join(sorted(NUM_EN, key=len, reverse=True)) + r")"
COUNT_TA = r"(?:(\d{1,3})\s*(?:பேர்|நபர்கள்|பேரும்)|(" + "|".join(sorted(NUM_TA, key=len, reverse=True)) + r"))"
PEOPLE_EN = (r"(?:\s+(?:more|other|people|persons|members|of|a|family|men|women|youths|students|children|kids|"
             r"pilgrims|devotees|workers|labourers|passengers|friends|siblings|cops|policemen))*")
NOT_GRADE = r"(?<!class )(?<!std )(?<!plus )(?<![-\w])"
DEATH_EN = r"\b(?:killed|dead|die|dies|died|charred to death|crushed to death|lose their lives|lost their lives|succumb\w*)\b"
DEATH_TA = r"(?:பலி|உயிரிழ|சாவு|இறந்|மரணம்)"
HURT_EN = r"\b(?:injured|hurt|wounded|hospitali[sz]ed)\b"
HURT_TA = r"(?:படுகாய|காயம|காயமடை)"
DEATH_COUNT_RE = [
    re.compile(r"\bdeath toll (?:rises|climbs|goes up|increases|reaches|touches) to " + COUNT_EN, re.I),
    re.compile(r"பலி எண்ணிக்கை\s*(\d{1,3})"),
    re.compile(NOT_GRADE + COUNT_EN + PEOPLE_EN + r"\s+(?:were\s+|are\s+)?" + DEATH_EN, re.I),
    re.compile(r"\b(?:kills|claims|claimed)\s+" + COUNT_EN, re.I),
    re.compile(COUNT_TA + r"\s*(?:\S+\s+){0,2}?" + DEATH_TA),
]
HURT_COUNT_RE = [
    re.compile(NOT_GRADE + COUNT_EN + PEOPLE_EN + r"\s+(?:were\s+|are\s+)?" + HURT_EN, re.I),
    re.compile(r"\binjures\s+" + COUNT_EN, re.I),
    re.compile(COUNT_TA + r"\s*(?:\S+\s+){0,2}?" + HURT_TA),
]
DEATH_RE = re.compile(DEATH_EN + "|" + DEATH_TA, re.I)
HURT_RE = re.compile(HURT_EN + "|" + HURT_TA, re.I)

# What Google News is asked for (it matches whole words, so inflected forms are listed)
SEARCH_TERMS = {
    "en": {
        "Murder": ["murder", "murdered", "hacked to death", "stabbed to death", "homicide"],
        "Theft": ["theft", "stolen", "burglary", "chain snatching", "snatched"],
        "Robbery": ["robbery", "robbed", "dacoity", "looted"],
        "Assault": ["assault", "attacked", "stabbed", "beaten up", "acid attack"],
        "Cyber Crime": ["cyber crime", "online fraud", "digital arrest", "phishing", "online scam"],
        "Women Safety": ["rape", "sexual assault", "molested", "sexual harassment", "POCSO"],
        "Narcotics": ["ganja", "narcotics", "NDPS", "drug peddler", "methamphetamine"],
    },
    "ta": {
        "Murder": ["கொலை", "வெட்டிக் கொலை", "கொலையாளி"],
        "Theft": ["திருட்டு", "திருடிய", "நகை பறிப்பு", "செயின் பறிப்பு"],
        "Robbery": ["கொள்ளை", "கொள்ளையர்கள்", "வழிப்பறி"],
        "Assault": ["தாக்குதல்", "அரிவாள் வெட்டு", "கத்திக்குத்து"],
        "Cyber Crime": ["சைபர் கிரைம்", "ஆன்லைன் மோசடி", "டிஜிட்டல் அரெஸ்ட்"],
        "Women Safety": ["பாலியல் தொல்லை", "பாலியல் வன்கொடுமை", "போக்சோ", "வரதட்சணை"],
        "Narcotics": ["கஞ்சா", "போதைப்பொருள்", "போதை மாத்திரை"],
    },
}
ROAD_SEARCH = {
    "en": ["road accident", "accident", "collided", "rammed", "overturned", "hit-and-run"],
    "ta": ["சாலை விபத்து", "விபத்தில்", "மோதி பலி", "கவிழ்ந்து", "நேருக்கு நேர் மோதல்"],
}
# Salem and Erode are left out: in English they mostly find stories from abroad (Tamil searches cover them)
BIG_CITIES = "(Chennai OR Coimbatore OR Madurai OR Tiruchi OR Tirunelveli OR Vellore)"

# District names, spellings and big towns -> district
DISTRICTS = {
    "Chennai": ["chennai", "velachery", "mylapore", "adyar", "egmore", "royapettah", "triplicane", "perambur",
                "kodambakkam", "vadapalani", "guindy", "saidapet", "tondiarpet", "ambattur", "porur", "koyambedu",
                "madhavaram", "sholinganallur", "thoraipakkam", "kilpauk", "nungambakkam", "washermanpet", "ennore",
                "tiruvottiyur", "pulianthope", "vyasarpadi", "virugambakkam", "valasaravakkam", "alandur", "mogappair",
                "villivakkam"],
    "Tiruvallur": ["tiruvallur", "thiruvallur", "avadi", "ponneri", "tiruttani", "gummidipoondi", "poonamallee"],
    "Chengalpattu": ["chengalpattu", "tambaram", "mamallapuram", "vandalur", "guduvanchery", "pallavaram", "chromepet",
                     "kelambakkam", "maraimalai nagar", "perungalathur"], "Kanchipuram": ["kanchipuram", "kancheepuram", "sriperumbudur"],
    "Ranipet": ["ranipet", "arakkonam"], "Vellore": ["vellore", "gudiyatham"], "Tirupathur": ["tirupathur", "tirupattur", "ambur", "vaniyambadi"],
    "Krishnagiri": ["krishnagiri", "hosur"], "Dharmapuri": ["dharmapuri"], "Salem": ["salem", "attur", "mettur"],
    "Tiruvannamalai": ["tiruvannamalai", "thiruvannamalai"], "Villupuram": ["villupuram", "viluppuram", "tindivanam"],
    "Cuddalore": ["cuddalore", "neyveli"], "Kallakurichi": ["kallakurichi"], "Nilgiris": ["nilgiris", "ooty", "udhagamandalam", "coonoor"],
    "Erode": ["erode", "gobichettipalayam"], "Namakkal": ["namakkal", "tiruchengode", "rasipuram"], "Perambalur": ["perambalur"],
    "Ariyalur": ["ariyalur"], "Mayiladuthurai": ["mayiladuthurai"], "Coimbatore": ["coimbatore", "pollachi", "mettupalayam"],
    "Tiruppur": ["tiruppur", "tirupur"], "Karur": ["karur"], "Tiruchirappalli": ["tiruchirappalli", "tiruchi", "trichy"],
    "Thanjavur": ["thanjavur", "tanjore", "kumbakonam"], "Tiruvarur": ["tiruvarur", "thiruvarur"], "Nagapattinam": ["nagapattinam", "velankanni"],
    "Theni": ["theni", "bodinayakanur"], "Dindigul": ["dindigul", "palani", "kodaikanal"], "Madurai": ["madurai"],
    "Pudukkottai": ["pudukkottai"], "Virudhunagar": ["virudhunagar", "sivakasi", "rajapalayam"], "Sivaganga": ["sivaganga", "karaikudi"],
    "Ramanathapuram": ["ramanathapuram", "rameswaram"], "Tenkasi": ["tenkasi"], "Tirunelveli": ["tirunelveli", "nellai"],
    "Thoothukudi": ["thoothukudi", "tuticorin", "kovilpatti"], "Kanyakumari": ["kanyakumari", "kanniyakumari", "nagercoil"],
}
# Also ordinary English words or foreign places: only the capitalised spelling counts
CASE_SENSITIVE = {"erode": "Erode", "salem": "Salem"}
DISTRICTS_TA = {
    "Chennai": ["சென்னை", "வேளச்சேரி", "மயிலாப்பூர்", "அடையாறு", "எழும்பூர்", "ராயப்பேட்டை", "திருவல்லிக்கேணி",
                "பெரம்பூர்", "கோடம்பாக்கம்", "வடபழனி", "கிண்டி", "சைதாப்பேட்டை", "தண்டையார்பேட்டை", "அம்பத்தூர்",
                "போரூர்", "கோயம்பேடு", "மாதவரம்", "சோழிங்கநல்லூர்", "கீழ்ப்பாக்கம்", "நுங்கம்பாக்கம்",
                "வண்ணாரப்பேட்டை", "எண்ணூர்", "திருவொற்றியூர்", "புளியந்தோப்பு", "வியாசர்பாடி", "விருகம்பாக்கம்",
                "ஆலந்தூர்", "முகப்பேர்", "வில்லிவாக்கம்"],
    "Tiruvallur": ["திருவள்ளூர்", "ஆவடி", "பொன்னேரி", "திருத்தணி", "கும்மிடிப்பூண்டி", "பூந்தமல்லி"],
    "Chengalpattu": ["செங்கல்பட்டு", "தாம்பரம்", "மாமல்லபுரம்", "வண்டலூர்", "கூடுவாஞ்சேரி", "பல்லாவரம்",
                     "குரோம்பேட்டை", "கேளம்பாக்கம்", "மறைமலைநகர்", "பெருங்களத்தூர்"], "Kanchipuram": ["காஞ்சிபுரம்", "ஸ்ரீபெரும்புதூர்"],
    "Ranipet": ["ராணிப்பேட்டை", "அரக்கோணம்"], "Vellore": ["வேலூர்", "குடியாத்தம்"],
    "Tirupathur": ["திருப்பத்தூர்", "ஆம்பூர்", "வாணியம்பாடி"], "Krishnagiri": ["கிருஷ்ணகிரி", "ஓசூர்", "ஒசூர்"],
    "Dharmapuri": ["தருமபுரி", "தர்மபுரி"], "Salem": ["சேலம்", "மேட்டூர்"], "Tiruvannamalai": ["திருவண்ணாமலை"],
    "Villupuram": ["விழுப்புரம்", "திண்டிவனம்"], "Cuddalore": ["கடலூர்", "நெய்வேலி"], "Kallakurichi": ["கள்ளக்குறிச்சி"],
    "Nilgiris": ["நீலகிரி", "உதகை", "குன்னூர்"], "Erode": ["ஈரோடு", "கோபிசெட்டிபாளையம்"],
    "Namakkal": ["நாமக்கல்", "திருச்செங்கோடு", "ராசிபுரம்"], "Perambalur": ["பெரம்பலூர்"], "Ariyalur": ["அரியலூர்"],
    "Mayiladuthurai": ["மயிலாடுதுறை"], "Coimbatore": ["கோயம்புத்தூர்", "கோவை", "பொள்ளாச்சி", "மேட்டுப்பாளையம்"],
    "Tiruppur": ["திருப்பூர்"], "Karur": ["கரூர்"], "Tiruchirappalli": ["திருச்சிராப்பள்ளி", "திருச்சி"],
    "Thanjavur": ["தஞ்சாவூர்", "தஞ்சை", "கும்பகோணம்"], "Tiruvarur": ["திருவாரூர்"],
    "Nagapattinam": ["நாகப்பட்டினம்", "நாகை", "வேளாங்கண்ணி"], "Theni": ["தேனி", "போடிநாயக்கனூர்"],
    "Dindigul": ["திண்டுக்கல்", "(?<![\u0b80-\u0bff])பழனி(?!ச)", "கொடைக்கானல்"], "Madurai": ["மதுரை"],
    "Pudukkottai": ["புதுக்கோட்டை"], "Virudhunagar": ["விருதுநகர்", "சிவகாசி", "ராஜபாளையம்"],
    "Sivaganga": ["சிவகங்கை", "காரைக்குடி"], "Ramanathapuram": ["ராமநாதபுரம்", "இராமநாதபுரம்", "ராமேஸ்வரம்"],
    "Tenkasi": ["தென்காசி"], "Tirunelveli": ["திருநெல்வேலி", "நெல்லை"], "Thoothukudi": ["தூத்துக்குடி", "கோவில்பட்டி"],
    "Kanyakumari": ["கன்னியாகுமரி", "நாகர்கோவில்", "குமரி"],
}
# Court names say where the court sits, not where the crime happened
COURT_RE = re.compile(r"madras high court|madras hc|சென்னை உயர் ?நீதிமன்ற", re.I)
TN_RE = re.compile(r"\b(?:tamil ?nadu|tn|dmk|aiadmk|tvk|pmk|vck|mdmk)\b|தமிழ்நாட|தமிழக|திமுக|அதிமுக|தவெக|பாமக|விசிக|மதிமுக", re.I)
# Salem, Erode etc. also exist abroad; these words only appear in foreign stories
NOT_TN_RE = re.compile(r"winston|massachusetts|oregon|virginia|illinois|ohio|indiana|dekalb|new hampshire|\bcounty\b|"
                       r"\bsheriff|salem,? (?:ma|or|nh|va)\b|\bga\.|georgia|atlanta|troopers|rockdale|"
                       r"\bhigh (?:school )?football|st\.? ann\b|jamaica|missouri|\binterstate \d", re.I)
# US local TV and papers that report on their own Salems
FOREIGN_SOURCE = re.compile(r"\b(?:fox|cbs|nbc|abc) \d+|\b(?:wsb|wsoc|ktvu|khou|wral|wtvd|wbtv|wfaa|kcra|11alive)\b|"
                            r"journal-constitution|statesman journal|patch\b|gleaner", re.I)


def foreign_source(source):
    return bool(source) and bool(NOT_TN_RE.search(source) or FOREIGN_SOURCE.search(source))
# A question naming a party is political talk, not a crime report
PARTY_RE = re.compile(r"\b(?:dmk|aiadmk|tvk|bjp|pmk|congress)\b|திமுக|அதிமுக|தவெக|பாஜக|பாமக|காங்கிரஸ்", re.I)

STOPWORDS = set("""the a an in of for to on at by with and or from as is are was were be been after over into near
    his her their its this that who what how why case cases police tamil nadu district city said says new two three
    four five one man men woman women youth held arrested booked
    அருகே பேர் போலீஸ் போலீசார் காவல் காவல்துறை இளைஞர் பெண் வழக்கு வழக்கில் மற்றும் பரபரப்பு அதிர்ச்சி
    சம்பவம் வீட்டில் லட்சம் கோடி பவுன் மாவட்டம் நகரில் இருவர் மூவர் உள்ளிட்ட மீது தொடர்பாக நபர் கும்பல்
    கும்பலால் கொண்ட பிரபல புகார் விசாரணை""".split())
SPLIT_RE = re.compile(r"[\s\-–—:;,.!?'\"‘’“”()\[\]|/₹…]+")


def _rx(words):
    """One regex for a keyword list; English keywords must start at a word start."""
    return re.compile("|".join((r"\b" + w) if w.isascii() else w for w in words), re.I)


def _ta_stem(alias):
    """Tamil place names change their ending before suffixes: சேலம் -> சேலத்தில், வேலூர் -> வேலூரில்."""
    if "(" in alias:
        return alias
    if alias.endswith("ம்"):
        return re.escape(alias[:-2]) + "(?:ம்|த்)"
    if alias.endswith(("்", "ு")):
        return re.escape(alias[:-1])
    return re.escape(alias)


def _district_rx(english, tamil):
    parts = []
    ci = [re.escape(a) for a in english if a not in CASE_SENSITIVE]
    cs = [re.escape(CASE_SENSITIVE[a]) for a in english if a in CASE_SENSITIVE]
    if ci:
        parts.append(r"(?<![-\w])(?i:" + "|".join(ci) + r")\b")
    if cs:
        parts.append(r"(?<![-\w])(?:" + "|".join(cs) + r")\b")
    parts += [_ta_stem(a) for a in tamil]
    return re.compile("|".join(parts))


CRIME_RX = {t: _rx(w) for t, w in CRIME_TYPES.items()}
CORRUPTION_GATE_RX = _rx(CORRUPTION_GATE)
CORRUPTION_RX = {t: _rx(w) for t, w in CORRUPTION_TYPES.items()}
DEV_RX = {t: _rx(w) for t, w in DEV_TAGS.items()}
ROAD_GATE_RX = _rx(ROAD_GATE)
ROAD_PLACE_RX = _rx(ROAD_PLACE)
ROAD_RX = {t: _rx(w) for t, w in ROAD_TYPES.items()}
DISTRICT_RX = [(d, _district_rx(DISTRICTS[d], DISTRICTS_TA[d])) for d in DISTRICTS]
PLACE_WORDS = {w for names in DISTRICTS.values() for n in names for w in n.split()}
PLACE_TA_RX = re.compile("|".join(_ta_stem(a) for names in DISTRICTS_TA.values() for a in names))
TYPE_WORDS = {re.sub(r"\\b|\(.*\)", "", w).lower()
              for words in [*CRIME_TYPES.values(), *CORRUPTION_TYPES.values(), *ROAD_TYPES.values(), ROAD_GATE]
              for w in words if " " not in w.strip()}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def norm_text(s):
    """Unicode-normalise and undo old Tamil typing conventions some sites still use:
    ர் typed as ா் (DinaMani: ஒசூா், போ்) and ூ typed as ுா (Dinamalar: கடலுார்)."""
    s = unicodedata.normalize("NFC", s or "")
    return s.replace("ோ்", "ேர்").replace("ொ்", "ெர்").replace("ா்", "ர்").replace("ுா", "ூ")


def clean_title(raw):
    # Google News titles end in " - Source Name"
    return re.sub(r"\s+-\s+[^-]+$", "", norm_text(raw)).strip()


def norm_key(title):
    return re.sub(r"[^0-9a-z஀-௿ ]", "", norm_text(title).lower())[:80]


def script_lang(title):
    return "ta" if re.search("[஀-௿]", title) else "en"


def tokens(title):
    return {w for w in SPLIT_RE.split(norm_text(title).lower()) if len(w) > 2 and w not in STOPWORDS}


def distinct(tk):
    """Words that identify an incident: not places, crime words or filler."""
    return {w for w in tk if w not in PLACE_WORDS and not PLACE_TA_RX.match(w) and not any(k in w for k in TYPE_WORDS)}


def find_district(text):
    """The district named earliest in the text."""
    text = COURT_RE.sub(" ", norm_text(text))
    best = None
    for district, rx in DISTRICT_RX:
        m = rx.search(text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), district)
    return best[1] if best else None


def strip_special(text):
    extra = set()
    if ATTEMPT_RE.search(text):
        extra.add("Assault")
        text = ATTEMPT_RE.sub(" ", text)
    return NOT_MURDER_RE.sub(" ", text), extra


def classify(bucket, title):
    """Return ((category, types), district) for a relevant Tamil Nadu headline, else None."""
    text = norm_text(title)
    if NOT_TN_RE.search(text):
        return None
    district = find_district(text)
    if not (district or TN_RE.search(text)):
        return None
    if bucket == "crime":
        if CRIME_EXCLUDE.search(text) or ("?" in text and PARTY_RE.search(text)):
            return None
        text, extra = strip_special(text)
        types = sorted(extra | {t for t, rx in CRIME_RX.items() if rx.search(text)})
        return (("crime", types), district) if types else None
    if bucket == "corruption":
        if not CORRUPTION_GATE_RX.search(text):
            return None
        types = [t for t, rx in CORRUPTION_RX.items() if rx.search(text)]
        return ("corruption", types or ["Other Corruption News"]), district
    if bucket == "road":
        if ROAD_EXCLUDE.search(text) or not ROAD_GATE_RX.search(text):
            return None
        if not district and OTHER_STATES.search(text):
            return None  # a national or other-state story that mentions Tamil Nadu in passing
        types = [t for t, rx in ROAD_RX.items() if rx.search(text)]
        if not types and not ROAD_PLACE_RX.search(text):
            return None  # an "accident" with no vehicle or road in sight
        return ("road", types or ["Other"]), district
    tag = next((t for t, rx in DEV_RX.items() if rx.search(text)), "Development")
    return ("development", [tag]), district


def casualties(title):
    """(deaths, injured) named in a road accident headline."""
    text = norm_text(title)

    def find(patterns, word_rx):
        for rx in patterns:
            m = rx.search(text)
            if m:
                g = next(x for x in m.groups() if x)
                return int(g) if g.isdigit() else NUM_EN.get(g.lower(), NUM_TA.get(g, 1))
        return 1 if word_rx.search(text) else 0

    return find(DEATH_COUNT_RE, DEATH_RE), find(HURT_COUNT_RE, HURT_RE)


def _day(a):
    return date.fromisoformat(a["date"]).toordinal()


def same_story(a, b, tka=None, tkb=None):
    """True when two stored stories most likely describe the same incident."""
    if a["cat"] != b["cat"]:
        return False
    tka = tokens(a["title"]) if tka is None else tka
    tkb = tokens(b["title"]) if tkb is None else tkb
    days = abs(_day(a) - _day(b))
    if days <= 2 and len(tka) >= 3 and len(tkb) >= 3 and len(tka & tkb) / len(tka | tkb) >= 0.5:
        return True
    # "Other" (no vehicle named) can be the same crash as any typed report of it
    same_type = set(a["types"]) & set(b["types"]) or (a["cat"] == "road" and "Other" in a["types"] + b["types"])
    if days > 1 or not a["district"] or a["district"] != b["district"] or not same_type:
        return False
    if a.get("lang", "en") != b.get("lang", "en"):
        return True  # English and Tamil words can't be compared: same type, district and day is the best signal
    return bool(distinct(tka) & distinct(tkb))


# ---------------------------------------------------------------------------
# News feeds
# ---------------------------------------------------------------------------
def gnews_url(query, edition):
    q = urllib.parse.quote(query)
    if edition == "ta":
        return f"https://news.google.com/rss/search?q={q}&hl=ta&gl=IN&ceid=IN:ta"
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def or_terms(words):
    return "(" + " OR ".join(f'"{w}"' if " " in w else w for w in words) + ")"


def build_queries(mode):
    """(bucket, edition, query) for every search feed read in this mode."""
    windows = ("1d",) if mode == "hourly" else ("1d", "7d", "30d")
    corr_en = or_terms(["bribe", "DVAC", "disproportionate assets", "vigilance and anti-corruption", "corruption case"])
    corr_ta = or_terms(["லஞ்சம்", "லஞ்ச ஒழிப்பு", "சொத்துக் குவிப்பு", "ஊழல் வழக்கு"])
    qs = []
    for when in windows:
        for words in SEARCH_TERMS["en"].values():
            qs.append(("crime", "en", f'{or_terms(words)} "Tamil Nadu" when:{when}'))
            qs.append(("crime", "en", f"{or_terms(words)} {BIG_CITIES} when:{when}"))
        for words in SEARCH_TERMS["ta"].values():
            qs.append(("crime", "ta", f"{or_terms(words)} when:{when}"))
        qs.append(("corruption", "en", f'{corr_en} "Tamil Nadu" when:{when}'))
        qs.append(("corruption", "en", f"{corr_en} {BIG_CITIES} when:{when}"))
        qs.append(("corruption", "ta", f"{corr_ta} when:{when}"))
        qs.append(("road", "en", f'{or_terms(ROAD_SEARCH["en"])} "Tamil Nadu" when:{when}'))
        qs.append(("road", "en", f"{or_terms(ROAD_SEARCH['en'])} {BIG_CITIES} when:{when}"))
        qs.append(("road", "ta", f"{or_terms(ROAD_SEARCH['ta'])} when:{when}"))
    dev_when = "1d" if mode == "hourly" else "3d"
    qs.append(("development", "en",
               f'{or_terms(["metro", "investment", "scheme", "industrial", "project", "policy"])} "Tamil Nadu" government when:{dev_when}'))
    qs.append(("development", "ta",
               f'{or_terms(["முதலீடு", "மெட்ரோ", "தொழிற்சாலை", "புதிய திட்டம்"])} தமிழக அரசு when:{dev_when}'))
    return qs


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt:
                raise
            time.sleep(3)


def load_corrections():
    if not os.path.exists(CORRECTIONS):
        return {}
    with open(CORRECTIONS, encoding="utf-8") as f:
        return json.load(f)


def _hit(a, pattern):
    p = (pattern or "").lower()
    return bool(p) and (p in a["title"].lower() or p in (a.get("url") or "").lower())


def fetch_news(history, status, mode, corr):
    """Read the search feeds and store new relevant stories. Returns True if any feed worked."""
    articles = history.setdefault("articles", {})
    merged = history.get("merged", {})
    counts = {"en": [0, 0, 0], "ta": [0, 0, 0]}  # feeds read, feeds failed, new stories
    for bucket, edition, query in build_queries(mode):
        c = counts[edition]
        try:
            root = ET.fromstring(http_get(gnews_url(query, edition)))
            c[0] += 1
        except Exception as e:  # one feed failing is fine
            c[1] += 1
            print(f"  ! feed failed: {query[:60]}… ({e})", file=sys.stderr)
            continue
        for item in root.iter("item"):
            title = clean_title(item.findtext("title"))
            link = item.findtext("link") or ""
            try:
                published = parsedate_to_datetime(item.findtext("pubDate")).astimezone(IST)
            except Exception:
                continue
            key = norm_key(title)
            if not key or key in merged or foreign_source(item.findtext("source")):
                continue
            if any(_hit({"title": title, "url": link}, p) for p in corr.get("exclude", [])):
                continue
            result = classify(bucket, title)
            if not result:
                continue
            (cat, types), district = result
            prev = articles.get(key)
            if prev:
                # same headline seen through another feed
                if prev["cat"] == cat:
                    prev["types"] = sorted(set(prev["types"]) | set(types))
                elif prev["cat"] == "development":
                    prev["cat"], prev["bucket"], prev["types"] = cat, cat, types
                continue
            articles[key] = {
                "title": title, "url": link, "source": item.findtext("source") or "", "cat": cat, "bucket": cat,
                "types": types,
                "district": district, "lang": script_lang(title), "date": published.strftime("%Y-%m-%d"),
                "ts": published.isoformat(),
            }
            if cat == "road":
                articles[key]["deaths"], articles[key]["injured"] = casualties(title)
            c[2] += 1
        time.sleep(1.0)  # be polite to the feed server
    for edition, name in (("en", "Google News RSS — English"), ("ta", "Google News RSS — Tamil")):
        ok, fail, added = counts[edition]
        status.append({
            "name": name, "url": "https://news.google.com/",
            "status": "ok" if ok and not fail else ("partial" if ok else "error"),
            "detail": f"{ok} feeds read, {fail} failed, {added} new stories",
        })
    return any(c[0] for c in counts.values())


# ---------------------------------------------------------------------------
# Keeping the stored stories consistent
# ---------------------------------------------------------------------------
def prune(history, today):
    cutoff = (today - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    for store in ("articles", "merged"):
        items = history.get(store, {})
        for k in [k for k, v in items.items() if (v["date"] if isinstance(v, dict) else v) < cutoff]:
            del items[k]
    history.setdefault("since", today.strftime("%Y-%m-%d"))


def reclassify(history):
    """Re-apply the current rules to stored stories, so rule fixes also correct past data."""
    arts = history.get("articles", {})
    for key in list(arts):
        a = arts[key]
        # "bucket" is the search a story came from; corrections may later change its "cat"
        result = classify(a.setdefault("bucket", a["cat"]), a["title"])
        if not result or foreign_source(a.get("source")):
            del arts[key]
            continue
        (a["cat"], a["types"]), a["district"] = result
        a["lang"] = script_lang(a["title"])
        if a["cat"] == "road":
            # the highest numbers any merged outlet reported win over this headline's own
            deaths, injured = casualties(a["title"])
            a["deaths"] = max(deaths, a.get("merged_deaths", 0))
            a["injured"] = max(injured, a.get("merged_injured", 0))
        a["title"] = norm_text(a["title"])
        new_key = norm_key(a["title"])
        if new_key != key:
            del arts[key]
            if new_key in arts:
                arts[new_key]["also"] = arts[new_key].get("also", 1) + a.get("also", 1)
            else:
                arts[new_key] = a


def apply_corrections(history, corr):
    """Hand-made fixes from scripts/corrections.json win over the automatic rules."""
    arts = history.get("articles", {})
    for key in [k for k, a in arts.items() if any(_hit(a, p) for p in corr.get("exclude", []))]:
        del arts[key]
    for rule in corr.get("override", []):
        for a in arts.values():
            if _hit(a, rule.get("match")):
                for field in ("cat", "types", "district"):
                    if field in rule:
                        a[field] = rule[field]


def dedupe(history):
    """Merge stories about the same incident (the earliest is kept, the rest counted as extra outlets)."""
    arts = history.get("articles", {})
    merged = history.setdefault("merged", {})
    kept = []  # (article, tokens, day), oldest first
    removed = 0
    for key, a in sorted(arts.items(), key=lambda kv: kv[1]["ts"]):
        tk, day = tokens(a["title"]), _day(a)
        dup = None
        for a2, tk2, day2 in reversed(kept):
            if day - day2 > 2:
                break
            if same_story(a, a2, tk, tk2):
                dup = a2
                break
        if dup:
            dup["types"] = sorted(set(dup["types"]) | set(a["types"]))
            dup["district"] = dup["district"] or a["district"]
            dup["also"] = dup.get("also", 1) + a.get("also", 1)
            for field in ("deaths", "injured"):
                if field in a:
                    dup["merged_" + field] = max(dup.get("merged_" + field, 0), a[field])
                    dup[field] = max(dup.get(field, 0), a[field])
            merged[key] = a["date"]
            del arts[key]
            removed += 1
        else:
            kept.append((a, tk, day))
    return removed


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------
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
    # script has been running for a while. Changes are only shown once both windows were collected live.
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


def hourly_series(arts, now):
    """Crime, corruption and road accident stories per hour (by publication time) over the last 24 hours."""
    end = now.replace(minute=0, second=0, microsecond=0)
    slots = [end - timedelta(hours=i) for i in range(23, -1, -1)]
    rows = [{"hour": s.strftime("%Y-%m-%dT%H:00"), "crime": 0, "corruption": 0, "road": 0} for s in slots]
    index = {s.strftime("%Y-%m-%dT%H"): i for i, s in enumerate(slots)}
    for a in arts:
        i = index.get(a["ts"][:13])
        if i is not None and a["cat"] in ("crime", "corruption", "road"):
            rows[i][a["cat"]] += 1
    return rows


def road_summary(arts, today, since):
    """Road accident reports and the deaths and injuries they name, by vehicle, district and day."""
    road = [a for a in arts if a["cat"] == "road"]

    def window(days):
        start = (today - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        return [a for a in road if a["date"] >= start]

    periods, totals = {}, {}
    for name, days in (("today", 1), ("week", 7), ("month", 30)):
        sel = window(days)
        periods[name] = [{"type": t, "icon": ROAD_ICONS[t], "count": sum(1 for a in sel if t in a["types"]),
                          "deaths": sum(a.get("deaths", 0) for a in sel if t in a["types"])} for t in ROAD_TYPES]
        totals[name] = {"reports": len(sel), "deaths": sum(a.get("deaths", 0) for a in sel),
                        "injured": sum(a.get("injured", 0) for a in sel)}
    month = window(30)
    districts = {d: {"reports": 0, "deaths": 0} for d in DISTRICTS}
    for a in month:
        if a["district"]:
            districts[a["district"]]["reports"] += 1
            districts[a["district"]]["deaths"] += a.get("deaths", 0)
    days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    daily = [{"date": d, "reports": sum(1 for a in road if a["date"] == d),
              "deaths": sum(a.get("deaths", 0) for a in road if a["date"] == d), "partial": d < since} for d in days]
    return {"periods": periods, "totals": totals, "districts": districts, "daily": daily,
            "recent": [story(a) for a in month][:300]}


# ---------------------------------------------------------------------------
# Official data (data.gov.in)
# ---------------------------------------------------------------------------
def fetch_datagov(history, status):
    cfg = json.load(open(SOURCES, encoding="utf-8"))
    key = os.environ.get("DATA_GOV_IN_API_KEY", "").strip()
    cache = history.setdefault("official", {})
    entries = []
    for src in cfg.get("datagov", []):
        entry = {"name": src["name"], "url": src.get("page") or "https://www.data.gov.in/"}
        entries.append(entry)
        if not src.get("resource"):
            entry.update(status="not configured", detail="Add a data.gov.in resource id in scripts/sources.json")
            continue
        if not key:
            entry.update(status="needs key" if src["id"] not in cache else "cached",
                         detail="Set DATA_GOV_IN_API_KEY (free at data.gov.in) to refresh")
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
    history["official_status"] = entries
    status.extend(entries)


# ---------------------------------------------------------------------------
def story(a):
    s = {"title": a["title"], "url": a["url"], "source": a["source"], "date": a["date"],
         "district": a["district"], "tag": a["types"][0], "types": a["types"],
         "lang": a.get("lang", "en"), "outlets": a.get("also", 1)}
    if a["cat"] == "road":
        s["deaths"], s["injured"] = a.get("deaths", 0), a.get("injured", 0)
    return s


def fetch_stats(history, status, mode, now):
    """Inflation (MoSPI), debt and borrowing (RBI). Each keeps its last good result if a source is down."""
    stats = history.setdefault("stats", {})
    if mode == "offline":
        status.extend(history.get("stats_status", []))
        return stats
    entries = []
    for key, name, url, fetch in (
        ("inflation", "MoSPI — Consumer Price Index (inflation)", official.MOSPI_PAGE,
         lambda: official.fetch_inflation(stats, now, force=mode == "full")),
        ("debt", "RBI — Outstanding liabilities of states", official.RBI_HANDBOOK,
         lambda: official.fetch_debt(stats, now, force=mode == "full")),
        ("borrowing", "RBI — State Government Securities auctions", official.RBI_LIST,
         lambda: official.fetch_borrowing(stats, now, full=mode == "full")),
    ):
        try:
            result = fetch()
        except Exception as e:  # keep the cached figures and say why they weren't refreshed
            print(f"  ! {name}: {e}", file=sys.stderr)
            result = {"status": "cached" if key in stats else "error", "detail": str(e)[:160]}
        entries.append({"name": name, "url": url, **result})
    history["stats_status"] = entries
    status.extend(entries)
    return stats


def main():
    ap = argparse.ArgumentParser(description="Fetch dashboard data from public sources.")
    ap.add_argument("--mode", choices=("hourly", "full", "offline"), default="full",
                    help="offline re-processes stored stories without fetching (to test rule changes)")
    mode = ap.parse_args().mode

    now = datetime.now(IST)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    os.makedirs(DATA, exist_ok=True)
    history = json.load(open(HISTORY, encoding="utf-8")) if os.path.exists(HISTORY) else {}
    corr = load_corrections()
    status = []

    if mode == "offline":
        status.extend(history.get("news_status", []))
    else:
        print(f"Fetching news feeds ({mode})…")
        if fetch_news(history, status, mode, corr):
            history["last_success"] = now.isoformat(timespec="minutes")
        history["news_status"] = list(status)
    if mode == "full":
        print("Fetching data.gov.in datasets…")
        fetch_datagov(history, status)
    else:
        status.extend(history.get("official_status", []))
    print("Fetching MoSPI and RBI statistics…")
    stats = fetch_stats(history, status, mode, now)
    history.setdefault("road_since", today.strftime("%Y-%m-%d"))
    prune(history, today)
    reclassify(history)
    apply_corrections(history, corr)
    print(f"Merged {dedupe(history)} duplicate stories")

    arts = sorted(history["articles"].values(), key=lambda a: a["ts"], reverse=True)
    month_start = (today - timedelta(days=29)).strftime("%Y-%m-%d")
    since = history["since"]

    districts = {d: 0 for d in DISTRICTS}
    for a in arts:
        if a["cat"] == "crime" and a["date"] >= month_start and a["district"]:
            districts[a["district"]] += 1

    def daily(cat):
        days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
        counts = {d: 0 for d in days}
        for a in arts:
            if a["cat"] == cat and a["date"] in counts:
                counts[a["date"]] += 1
        # days before the script started running are under-sampled by the feeds
        return [{"date": d, "count": counts[d], "partial": d < since} for d in days]

    news = [story(a) | {"tag": {"crime": "Crime", "corruption": "Corruption", "road": "Road Safety"}
                        .get(a["cat"], a["types"][0])}
            for a in arts[:40]]
    official = history.get("official", {})
    out = {
        "generatedAt": now.isoformat(timespec="minutes"),
        "lastSuccess": history.get("last_success"),
        "mode": mode,  # hourly | full | offline
        "crime": {
            "periods": build_periods(history, "crime", list(CRIME_TYPES), CRIME_ICONS, today),
            "districts": districts,
            "recent": [story(a) for a in arts if a["cat"] == "crime" and a["date"] >= month_start][:600],
            "daily": daily("crime"),
            "official": next((v for v in official.values() if v["use"] == "crime_official"), None),
        },
        "corruption": {
            "periods": build_periods(history, "corruption", list(CORRUPTION_TYPES) + ["Other Corruption News"],
                                     CORRUPTION_ICONS, today),
            "latest": [story(a) for a in arts if a["cat"] == "corruption"][:12],
            "daily": daily("corruption"),
        },
        "road": road_summary(arts, today, max(since, history["road_since"])),
        "inflation": stats.get("inflation"),
        "debt": stats.get("debt"),
        "borrowing": stats.get("borrowing"),
        "hourly": hourly_series(arts, now),
        "news": news,
        "economy": next((v for v in official.values() if v["use"] == "economy"), None),
        "sources": status,
    }

    def write(name, text):
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
            f.write(text)

    write("history.json", json.dumps(history, ensure_ascii=False, separators=(",", ":")))
    write("auto.js", "/* AUTO-GENERATED by scripts/fetch_data.py — do not edit by hand. */\nwindow.AUTO_DATA = "
          + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    write("auto.json", json.dumps(out, ensure_ascii=False, indent=1))
    write("version.json", json.dumps({"generatedAt": out["generatedAt"], "lastSuccess": out["lastSuccess"]}))
    with open(os.path.join(DATA, "stories.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "category", "types", "district", "language", "title", "source", "url", "outlets",
                    "deaths", "injured"])
        for a in arts:
            w.writerow([a["date"], a["cat"], "; ".join(a["types"]), a["district"] or "", a.get("lang", "en"),
                        a["title"], a["source"], a["url"], a.get("also", 1), a.get("deaths", ""), a.get("injured", "")])

    month = out["crime"]["periods"]["month"]
    by_lang = {lang: sum(1 for a in arts if a.get("lang", "en") == lang) for lang in ("en", "ta")}
    print(f"Done. {len(arts)} stored stories ({by_lang['en']} English, {by_lang['ta']} Tamil); "
          f"crime reports (30d): {sum(r['count'] for r in month)}")
    for s in status:
        print(f"  [{s['status']}] {s['name']}: {s['detail']}")


if __name__ == "__main__":
    main()
