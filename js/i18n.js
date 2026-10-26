/* English / Tamil interface text.
   The page is written in English; elements with data-i18n="key" get the Tamil text below.
   Language: ?lang=ta|en in the URL, else the saved choice, else the browser language. */
(function () {
  "use strict";

  /* ---------- Static page text (index.html, data-i18n keys) ---------- */
  const PAGE_TA = {
    tagline: "உண்மைகள் · வெளிப்படைத்தன்மை · சிறந்த நாளை",
    navHome: "முகப்பு", navCrime: "குற்றம்", navCorruption: "ஊழல்", navNews: "செய்திகள்", navEconomy: "பொருளாதாரம்",
    navTrends: "போக்குகள்", navSources: "ஆதாரங்கள்", navOpenData: "திறந்த தரவு",
    heroTitle: 'வெளிப்படையான<br><span>தமிழ்நாடு</span>',
    heroLead: "உண்மையான தரவு. உண்மையான தகவல்கள். விழிப்புள்ள மக்கள்.",
    topicCrime: "குற்றம்", topicCorruption: "ஊழல்", topicNews: "செய்திகள்", topicSources: "பொது ஆதாரங்கள்",
    heroCite: "— பாதுகாப்பான, நியாயமான,<br>வலிமையான தமிழ்நாட்டிற்காக",
    searchBtn: "தேடு",
    notice: 'இங்குள்ள ஒவ்வொரு எண்ணும் பொது ஆதாரங்களிலிருந்து தானாகச் சேகரிக்கப்பட்டு ஒவ்வொரு மணி நேரமும் புதுப்பிக்கப்படுகிறது. தினசரி, வாராந்திர, மாதாந்திர எண்ணிக்கைகள் ஆங்கில மற்றும் தமிழ் பொதுச் செய்தி ஓடைகளில் வந்த <strong>செய்தி அறிக்கைகள்</strong> — அதிகாரப்பூர்வ காவல்துறை புள்ளிவிவரங்கள் அல்ல. பணவீக்கம் MoSPI-யிலிருந்தும், மாநிலக் கடன் RBI-யிலிருந்தும் வருகின்றன. <a href="#sources">ஆதாரங்களைப் பார்க்க</a>.',
    shareBtn: "பகிர்", shareViewBtn: "பகிர்",
    toastText: "புதிய தரவு வந்துள்ளது.", toastBtn: "புதுப்பி",
    crimeTitle: "தமிழ்நாட்டில் குற்றங்கள்",
    tabToday: "இன்று", tabWeek: "வாரம்", tabMonth: "மாதம்", tabOfficial: "அதிகாரப்பூர்வம்",
    lvNone: "இல்லை", lvLow: "குறைவு", lvModerate: "மிதமானது", lvHigh: "அதிகம்", lvVeryHigh: "மிக அதிகம்",
    mapNote: "மாவட்ட வாரியான குற்றச் செய்திகள், கடந்த 30 நாட்கள். கதைகளைப் பார்க்க <b>ஒரு மாவட்டத்தைக் கிளிக் செய்யவும்</b>.",
    corrTitle: "ஊழல் & முறைகேடு",
    corrSub: "லஞ்சம், சோதனைகள், அதிகாரிகள் மீதான நடவடிக்கைகள் பற்றிய செய்திகள்",
    corrDisclaimer: "இவை குற்றச்சாட்டுகள் மற்றும் அதிகாரப்பூர்வ நடவடிக்கைகள் பற்றிய செய்திகள். நீதிமன்றத்தில் நிரூபிக்கப்படும் வரை குற்றம் சாட்டப்பட்டவர் நிரபராதியே.",
    newsTitle: "சமீபத்திய செய்திகள்", newsSub: "குற்றம், ஊழல் மற்றும் வளர்ச்சி",
    trendTitle: "போக்கு", trendSub: "நாள்தோறும் வெளியான செய்திகள்", trend30: "30 நாட்கள்", trend24: "24 மணி நேரம்",
    crimeNewsTitle: "சமீபத்திய குற்றச் செய்திகள்",
    allDistricts: "அனைத்து மாவட்டங்களும்", allTypes: "அனைத்து வகைகளும்", showMore: "மேலும் காட்டு",
    allLanguages: "அனைத்து மொழிகளும்", langEnOpt: "ஆங்கிலம்",
    corrNewsTitle: "சமீபத்திய ஊழல் செய்திகள்", corrNewsSub: "லஞ்ச ஒழிப்பு மற்றும் லஞ்சம் தொடர்பான சமீபத்திய செய்திகள்",
    sourcesTitle: "ஆதாரங்கள் & புதுப்பிப்பு நிலை", sourcesSub: "ஒவ்வொரு எண்ணும் எங்கிருந்து வருகிறது",
    sourcesNote: "ஒரே சம்பவம் பல ஊடகங்களில் வந்தால் ஒருமுறை மட்டுமே கணக்கிடப்படுகிறது. ஆனால் பல குற்றங்கள் செய்திகளில் வருவதே இல்லை. இந்த எண்ணிக்கைகளை அதிகாரப்பூர்வ மொத்தமாக அல்ல, ஒரு குறிகாட்டியாகக் கொள்ளவும்.",
    openTitle: "திறந்த தரவு", openSub: "இலவசமாகப் பதிவிறக்கலாம், சரிபார்க்கலாம், மீண்டும் பயன்படுத்தலாம்",
    dlCsvTitle: "அனைத்துச் செய்திகளும் (CSV)",
    dlCsvSub: "கடந்த 70 நாட்களில் கணக்கிடப்பட்ட ஒவ்வொரு செய்தியும் — வகை, மாவட்டம், இணைப்புடன். Excel-இல் திறக்கும்.",
    dlJsonTitle: "டாஷ்போர்டு தரவு (JSON)", dlJsonSub: "இந்தப் பக்கத்தில் உள்ள அனைத்து எண்களும்.",
    dlCodeTitle: "மூலக் குறியீடு & முறை", dlCodeSub: "செய்திகள் எவ்வாறு கண்டறியப்பட்டு, வகைப்படுத்தப்பட்டு, கணக்கிடப்படுகின்றன.",
    methodTitle: "எண்ணிக்கை எப்படிக் கணக்கிடப்படுகிறது",
    method1: "ஒவ்வொரு மணி நேரமும் ஆங்கில மற்றும் தமிழ் பொதுச் செய்தி ஓடைகளிலிருந்து செய்திகள் சேகரிக்கப்படுகின்றன.",
    method2: "தலைப்புச் சொற்களைக் கொண்டு குற்ற வகையும் மாவட்டமும் கண்டறியப்படுகின்றன.",
    method3: "பல ஊடகங்கள் வெளியிட்ட ஒரே சம்பவம் ஒருமுறை மட்டுமே கணக்கிடப்படுகிறது. ஆங்கில, தமிழ் செய்திகள் ஒரே வகை, மாவட்டம், நாள் அடிப்படையில் பொருத்தப்படுகின்றன.",
    method5: "ஒவ்வொரு செய்தியிலும் உள்ள கொடிக் குறியீட்டின் மூலம் தவறுகளைத் தெரிவிக்கலாம்; அவை கைமுறையாகத் திருத்தப்படும்.",
    method4: "அதிகாரப்பூர்வ ஆண்டு குற்ற மொத்தங்கள் data.gov.in வழியாக NCRB-யிலிருந்து பெறப்படுகின்றன.",
    method6: "பணவீக்கம் MoSPI-யின் அதிகாரப்பூர்வ API-யிலிருந்தும், மாநிலக் கடன் மற்றும் வாராந்திரக் கடன் வாங்குதல் RBI வெளியீடுகளிலிருந்தும் பெறப்படுகின்றன.",
    econTitle: "தமிழ்நாடு GDP & பொருளாதாரம்",
    navRoad: "சாலைப் பாதுகாப்பு", navPrices: "விலைவாசி", navDebt: "கடன்",
    topicRoad: "சாலைப் பாதுகாப்பு", topicPrices: "விலைவாசி", topicDebt: "அரசுக் கடன்",
    roadTitle: "சாலைப் பாதுகாப்பு",
    roadNote: "உயிரிழப்பு, காயம் எண்ணிக்கைகள் செய்தித் தலைப்புகளில் குறிப்பிடப்பட்டவை; எண் இல்லாத தலைப்பு ஒன்றாகக் கணக்கிடப்படுகிறது. இவை அதிகாரப்பூர்வ காவல்துறை எண்ணிக்கைகள் அல்ல.",
    roadMapTitle: "மாவட்ட வாரியான சாலை விபத்து உயிரிழப்புகள்", roadMapSub: "செய்திகளில் குறிப்பிடப்பட்ட உயிரிழப்புகள், கடந்த 30 நாட்கள்",
    roadNewsTitle: "சமீபத்திய சாலை விபத்துச் செய்திகள்", roadNewsSub: "மாவட்டத்துடன் சமீபத்திய விபத்துச் செய்திகள்",
    pricesTitle: "விலைவாசி & பணவீக்கம்",
    pricesTrendTitle: "பணவீக்கப் போக்கு", pricesTrendSub: "தமிழ்நாடு vs இந்தியா, ஆண்டு அடிப்படையில் (%)",
    pricesWhyTitle: "எது விலை உயர்கிறது", pricesWhySub: "வகை வாரியான பணவீக்கம், தமிழ்நாடு vs இந்தியா (%)",
    debtTitle: "தமிழ்நாடு அரசின் கடன்",
    debtTrendTitle: "ஆண்டுவாரியான கடன் வளர்ச்சி", debtTrendSub: "மார்ச் இறுதியில் நிலுவைக் கடன் (₹ லட்சம் கோடி)",
    borrowTitle: "இந்த ஆண்டு வாங்கிய கடன்", borrowSub: "RBI நடத்தும் வாராந்திர மாநில அரசுப் பத்திர ஏலங்கள்",
    footer: "<strong>Tamil Nadu Watch</strong> — பொது ஆதாரங்களை மட்டுமே கொண்டு உருவாக்கப்பட்ட சுயாதீன குடிமக்கள் டாஷ்போர்டு. ஒவ்வொரு செய்தியும் அதன் அசல் வெளியீட்டாளருக்கு இணைக்கப்பட்டுள்ளது."
  };
  const ATTR_TA = {
    searchPh: "குற்றங்கள், மாவட்டங்கள், அதிகாரிகள், செய்திகளைத் தேடுங்கள்…",
    searchLabel: "தேடல்", menuLabel: "மெனுவைத் திற",
    districtLabel: "மாவட்ட வாரியாக வடிகட்டு", typeLabel: "குற்ற வகை வாரியாக வடிகட்டு", langLabel: "செய்தி மொழி",
    trendLabel: "கால அளவு"
  };

  /* ---------- Text built by app.js ---------- */
  const UI = {
    en: {
      updated: "Updated {date}, {time}",
      updatedAgo: "Updated {ago}", justNow: "just now", minAgo: "{n} min ago", hoursAgo: "{n} h ago", daysAgo: "{n} days ago",
      stale: "Last update was {ago} — the hourly update may be delayed.",
      statCrime: "Crime News Reports", statWomen: "Women Safety Reports", statCorruption: "Corruption News Reports",
      statRecent: "Latest Crime Reports", statOfficial: "IPC Crimes (Official)",
      last30: "Last 30 days", last24: "Last 24 hours",
      totalReports: "Total reports", needsHistory: "Needs more days of history",
      officialEmpty: "Official NCRB figures are fetched from data.gov.in. Add a free API key (<code>DATA_GOV_IN_API_KEY</code>) to the daily job to show them here.",
      ipcYear: "IPC crimes, {year}", source: "Source",
      subToday: "News reports today", subWeek: "News reports, last 7 days", subMonth: "News reports, last 30 days", subOfficial: "Official NCRB annual figures",
      tileLabel: "{d}: {n} reports. Show stories", tileTip: "{n} news reports",
      noStories: "No stories fetched yet.", noMatch: "No crime stories match this filter in the last 30 days.",
      storiesCount: "{n} stories in the last 30 days", crimeNewsSub: "Most recent crime stories with district",
      moreOutlets: "+{n} more", report: "Report a mistake in this story",
      noResults: "No results for “{q}”", kindCrime: "Crime", kindCorruption: "Corruption", kindDistrict: "District", kindType: "Crime type",
      searchDistrict: "{d} — {n} crime reports (30 days)", searchType: "{t} — {n} reports (30 days)",
      trendNote: "Lighter bars: days before collection began. News feeds only return recent stories, so those days are under-counted.",
      trendSubDay: "News reports per day", trendSubHour: "News reports per hour, last 24 hours",
      trendNote24: "Hours are when stories were published (IST).",
      shareText: "Tamil Nadu Watch: {n} crime news reports in the last 30 days, updated every hour from public sources.",
      shareDistrict: "{d}: {n} crime news reports in the last 30 days — Tamil Nadu Watch",
      crimeReports: "Crime reports", corruptionReports: "Corruption reports",
      growth: "Growth (%)", nominalGrowth: "Nominal growth",
      stOk: "ok", stPartial: "partial", stCached: "cached", stNeedsKey: "needs key", stNotConfigured: "not configured", stError: "error",
      switchTo: "தமிழ்", switchLabel: "தமிழில் படிக்க",
      showStories: "Show stories", kindRoad: "Road accident",
      crimeRate: "Crimes per lakh people, {y}", chargesheetRate: "Cases chargesheeted, {y}",
      covidNote: "2020 is inflated by COVID-19 lockdown-violation cases (IPC section 188).",
      crore: "crore", lakhCrore: "lakh crore",
      statRoad: "Road Deaths Reported", statInflation: "Tamil Nadu Inflation", statDebt: "Tamil Nadu Govt Debt",
      statBorrowed: "Borrowed This Year", endMarch: "End-March {y}", sinceApril: "Since 1 April {y}",
      deaths: "Deaths", injured: "Injured", reports: "Reports", reportsCount: "{n} reports", thDeaths: "Deaths",
      roadSubToday: "Road accident reports today", roadSubWeek: "Road accident reports, last 7 days",
      roadSubMonth: "Road accident reports, last 30 days",
      roadTip: "{d} deaths in {r} reports", clearFilter: "Show all districts",
      cpiSub: "Consumer Price Index · {month}", tnRetail: "Retail inflation in Tamil Nadu, {month}",
      rankFirst: "Highest of {n} major states", rankNth: "{p} of {n} major states (1 = highest)",
      india: "India", food: "Food", rural: "Rural", urban: "Urban",
      provisionalNote: "The latest month is provisional.", nextRelease: "Next update: {date}.",
      topStates: "Highest inflation among major states", officialPending: "Waiting for the first official figures.",
      debtTotal: "Total outstanding debt", debtRankFirst: "Highest of {n} states", debtRankNth: "{p} of {n} states (1 = highest)",
      debtShare: "{s}% of all states' debt", debtMix: "What the debt is made of",
      debtNote: "Includes market loans, loans from the Centre, small savings, provident funds and deposits, at end-March.",
      debtGrowth: "{from} in {y1} → {to} in {y2}: {x}× in ten years.",
      yearsShort: "{n} yr", notAccepted: "not accepted",
      raisedLabel: "Raised in {n} auctions since {date}", avgRate: "Average interest rate",
      lastYearSame: "Same period last year", thisYearVs: "This year {p}%", lastYearTotal: "Whole of last year",
      nextAuction: "Next auction", recentAuctions: "Recent auctions",
      borrowNote: "Market loans only (State Development Loans); amounts accepted at each weekly auction."
    },
    ta: {
      updated: "புதுப்பிக்கப்பட்டது: {date}, {time}",
      updatedAgo: "{ago} புதுப்பிக்கப்பட்டது", justNow: "சற்று முன்", minAgo: "{n} நிமிடங்களுக்கு முன்",
      hoursAgo: "{n} மணி நேரத்துக்கு முன்", daysAgo: "{n} நாட்களுக்கு முன்",
      stale: "கடைசிப் புதுப்பிப்பு {ago} — மணிநேரப் புதுப்பிப்பு தாமதமாகியிருக்கலாம்.",
      statCrime: "குற்றச் செய்திகள்", statWomen: "பெண்கள் பாதுகாப்புச் செய்திகள்", statCorruption: "ஊழல் செய்திகள்",
      statRecent: "சமீபத்திய குற்றச் செய்திகள்", statOfficial: "IPC குற்றங்கள் (அதிகாரப்பூர்வம்)",
      last30: "கடந்த 30 நாட்கள்", last24: "கடந்த 24 மணி நேரம்",
      totalReports: "மொத்தச் செய்திகள்", needsHistory: "ஒப்பிட இன்னும் சில நாட்களின் தரவு தேவை",
      officialEmpty: "அதிகாரப்பூர்வ NCRB எண்ணிக்கைகள் data.gov.in-இலிருந்து பெறப்படுகின்றன. அவற்றை இங்கே காட்ட, தினசரிப் பணியில் இலவச API key-ஐ (<code>DATA_GOV_IN_API_KEY</code>) சேர்க்கவும்.",
      ipcYear: "IPC குற்றங்கள், {year}", source: "ஆதாரம்",
      subToday: "இன்றைய செய்திகள்", subWeek: "செய்திகள், கடந்த 7 நாட்கள்", subMonth: "செய்திகள், கடந்த 30 நாட்கள்", subOfficial: "அதிகாரப்பூர்வ NCRB ஆண்டு எண்ணிக்கைகள்",
      tileLabel: "{d}: {n} செய்திகள். கதைகளைக் காட்டு", tileTip: "{n} செய்திகள்",
      noStories: "இன்னும் செய்திகள் எதுவும் பெறப்படவில்லை.", noMatch: "கடந்த 30 நாட்களில் இந்த வடிகட்டிக்குப் பொருந்தும் குற்றச் செய்திகள் இல்லை.",
      storiesCount: "கடந்த 30 நாட்களில் {n} செய்திகள்", crimeNewsSub: "மாவட்டத்துடன் சமீபத்திய குற்றச் செய்திகள்",
      moreOutlets: "+{n} ஊடகங்கள்", report: "இந்தச் செய்தியில் உள்ள தவறைத் தெரிவிக்க",
      noResults: "“{q}” என்பதற்கு முடிவுகள் இல்லை", kindCrime: "குற்றம்", kindCorruption: "ஊழல்", kindDistrict: "மாவட்டம்", kindType: "குற்ற வகை",
      searchDistrict: "{d} — {n} குற்றச் செய்திகள் (30 நாட்கள்)", searchType: "{t} — {n} செய்திகள் (30 நாட்கள்)",
      trendNote: "வெளிர் நிறப் பட்டைகள்: சேகரிப்பு தொடங்குவதற்கு முந்தைய நாட்கள். செய்தி ஓடைகள் சமீபத்திய செய்திகளை மட்டுமே தருவதால் அந்த நாட்களின் எண்ணிக்கை குறைவாக இருக்கும்.",
      trendSubDay: "நாள்தோறும் வெளியான செய்திகள்", trendSubHour: "கடந்த 24 மணி நேரத்தில், மணிநேர வாரியான செய்திகள்",
      trendNote24: "நேரம் என்பது செய்தி வெளியான நேரம் (IST).",
      shareText: "தமிழ்நாடு வாட்ச்: கடந்த 30 நாட்களில் {n} குற்றச் செய்திகள் — பொது ஆதாரங்களிலிருந்து ஒவ்வொரு மணி நேரமும் புதுப்பிக்கப்படுகிறது.",
      shareDistrict: "{d}: கடந்த 30 நாட்களில் {n} குற்றச் செய்திகள் — தமிழ்நாடு வாட்ச்",
      crimeReports: "குற்றச் செய்திகள்", corruptionReports: "ஊழல் செய்திகள்",
      growth: "வளர்ச்சி (%)", nominalGrowth: "பெயரளவு வளர்ச்சி",
      stOk: "சரி", stPartial: "பகுதியளவு", stCached: "முந்தைய தரவு", stNeedsKey: "key தேவை", stNotConfigured: "இணைக்கப்படவில்லை", stError: "பிழை",
      switchTo: "English", switchLabel: "Read in English",
      showStories: "செய்திகளைக் காட்டு", kindRoad: "சாலை விபத்து",
      crimeRate: "ஒரு லட்சம் பேருக்குக் குற்றங்கள், {y}", chargesheetRate: "குற்றப்பத்திரிகை தாக்கல் விகிதம், {y}",
      covidNote: "2020 எண்ணிக்கை கொரோனா ஊரடங்கு மீறல் வழக்குகளால் (IPC பிரிவு 188) உயர்ந்துள்ளது.",
      crore: "கோடி", lakhCrore: "லட்சம் கோடி",
      statRoad: "சாலை விபத்து உயிரிழப்புகள்", statInflation: "தமிழ்நாடு பணவீக்கம்", statDebt: "தமிழ்நாடு அரசுக் கடன்",
      statBorrowed: "இந்த ஆண்டு வாங்கிய கடன்", endMarch: "மார்ச் {y} இறுதியில்", sinceApril: "1 ஏப்ரல் {y} முதல்",
      deaths: "உயிரிழப்புகள்", injured: "காயமடைந்தோர்", reports: "செய்திகள்", reportsCount: "{n} செய்திகள்", thDeaths: "இறப்பு",
      roadSubToday: "இன்றைய சாலை விபத்துச் செய்திகள்", roadSubWeek: "சாலை விபத்துச் செய்திகள், கடந்த 7 நாட்கள்",
      roadSubMonth: "சாலை விபத்துச் செய்திகள், கடந்த 30 நாட்கள்",
      roadTip: "{r} செய்திகளில் {d} உயிரிழப்புகள்", clearFilter: "அனைத்து மாவட்டங்களையும் காட்டு",
      cpiSub: "நுகர்வோர் விலைக் குறியீடு · {month}", tnRetail: "{month} — தமிழ்நாட்டின் சில்லறைப் பணவீக்கம்",
      rankFirst: "{n} பெரிய மாநிலங்களில் அதிகம்", rankNth: "{n} பெரிய மாநிலங்களில் {p}-வது இடம் (1 = அதிகம்)",
      india: "இந்தியா", food: "உணவு", rural: "கிராமப்புறம்", urban: "நகர்ப்புறம்",
      provisionalNote: "சமீபத்திய மாதம் தற்காலிகமானது.", nextRelease: "அடுத்த வெளியீடு: {date}.",
      topStates: "பெரிய மாநிலங்களில் அதிக பணவீக்கம்", officialPending: "முதல் அதிகாரப்பூர்வ எண்ணிக்கைகளுக்காகக் காத்திருக்கிறது.",
      debtTotal: "மொத்த நிலுவைக் கடன்", debtRankFirst: "{n} மாநிலங்களில் அதிகம்", debtRankNth: "{n} மாநிலங்களில் {p}-வது இடம் (1 = அதிகம்)",
      debtShare: "அனைத்து மாநிலங்களின் கடனில் {s}%", debtMix: "கடன் எவற்றால் ஆனது",
      debtNote: "சந்தைக் கடன்கள், ஒன்றிய அரசுக் கடன்கள், சிறுசேமிப்பு, வருங்கால வைப்பு நிதி, வைப்புகள் உட்பட — மார்ச் இறுதி நிலவரம்.",
      debtGrowth: "{y1}-இல் {from} → {y2}-இல் {to}: பத்து ஆண்டுகளில் {x} மடங்கு.",
      yearsShort: "{n} ஆண்டு", notAccepted: "ஏற்கப்படவில்லை",
      raisedLabel: "{date} முதல் {n} ஏலங்களில் திரட்டப்பட்டது", avgRate: "சராசரி வட்டி விகிதம்",
      lastYearSame: "கடந்த ஆண்டு இதே காலம்", thisYearVs: "இந்த ஆண்டு {p}%", lastYearTotal: "கடந்த முழு ஆண்டு",
      nextAuction: "அடுத்த ஏலம்", recentAuctions: "சமீபத்திய ஏலங்கள்",
      borrowNote: "சந்தைக் கடன்கள் மட்டும் (மாநில வளர்ச்சிக் கடன்கள்); ஒவ்வொரு வார ஏலத்திலும் ஏற்கப்பட்ட தொகை."
    }
  };

  /* ---------- Data terms (crime types, categories, districts, months) ---------- */
  const TERMS_TA = {
    "Murder": "கொலை", "Theft": "திருட்டு", "Robbery": "கொள்ளை", "Assault": "தாக்குதல்", "Cyber Crime": "சைபர் குற்றம்",
    "Women Safety": "பெண்கள் பாதுகாப்பு", "Narcotics": "போதைப்பொருள்",
    "Bribery Cases": "லஞ்ச வழக்குகள்", "Vigilance Raids & Searches": "லஞ்ச ஒழிப்புச் சோதனைகள்",
    "Disproportionate Assets": "வருமானத்துக்கு மீறிய சொத்து", "Officials Suspended": "பணியிடை நீக்கம் செய்யப்பட்ட அதிகாரிகள்",
    "Arrests & Chargesheets": "கைதுகள் & குற்றப்பத்திரிகைகள்", "Other Corruption News": "பிற ஊழல் செய்திகள்",
    "Crime": "குற்றம்", "Corruption": "ஊழல்", "Development": "வளர்ச்சி", "Policy": "கொள்கை", "Infrastructure": "உள்கட்டமைப்பு",
    "None": "இல்லை", "Low": "குறைவு", "Moderate": "மிதமானது", "High": "அதிகம்", "Very High": "மிக அதிகம்",
    "Chennai": "சென்னை", "Tiruvallur": "திருவள்ளூர்", "Chengalpattu": "செங்கல்பட்டு", "Kanchipuram": "காஞ்சிபுரம்",
    "Ranipet": "ராணிப்பேட்டை", "Vellore": "வேலூர்", "Tirupathur": "திருப்பத்தூர்", "Krishnagiri": "கிருஷ்ணகிரி",
    "Dharmapuri": "தருமபுரி", "Salem": "சேலம்", "Tiruvannamalai": "திருவண்ணாமலை", "Villupuram": "விழுப்புரம்",
    "Cuddalore": "கடலூர்", "Kallakurichi": "கள்ளக்குறிச்சி", "Nilgiris": "நீலகிரி", "Erode": "ஈரோடு",
    "Namakkal": "நாமக்கல்", "Perambalur": "பெரம்பலூர்", "Ariyalur": "அரியலூர்", "Mayiladuthurai": "மயிலாடுதுறை",
    "Coimbatore": "கோயம்புத்தூர்", "Tiruppur": "திருப்பூர்", "Karur": "கரூர்", "Tiruchirappalli": "திருச்சிராப்பள்ளி",
    "Thanjavur": "தஞ்சாவூர்", "Tiruvarur": "திருவாரூர்", "Nagapattinam": "நாகப்பட்டினம்", "Theni": "தேனி",
    "Dindigul": "திண்டுக்கல்", "Madurai": "மதுரை", "Pudukkottai": "புதுக்கோட்டை", "Virudhunagar": "விருதுநகர்",
    "Sivaganga": "சிவகங்கை", "Ramanathapuram": "இராமநாதபுரம்", "Tenkasi": "தென்காசி", "Tirunelveli": "திருநெல்வேலி",
    "Thoothukudi": "தூத்துக்குடி", "Kanyakumari": "கன்னியாகுமரி",
    "Road Safety": "சாலைப் பாதுகாப்பு", "Two-wheeler": "இருசக்கர வாகனம்", "Bus": "பேருந்து", "Lorry / Truck": "லாரி / டிரக்",
    "Car / Van": "கார் / வேன்", "Pedestrian": "பாதசாரிகள்", "Other": "பிற",
    "Food & drinks": "உணவு & பானங்கள்", "Paan & tobacco": "பான் & புகையிலை", "Clothes & shoes": "ஆடை & காலணி",
    "Housing & fuel": "வீடு & எரிபொருள்", "Household goods": "வீட்டுப் பொருட்கள்", "Health": "சுகாதாரம்",
    "Transport": "போக்குவரத்து", "Phone & internet": "தொலைபேசி & இணையம்", "Recreation": "பொழுதுபோக்கு",
    "Education": "கல்வி", "Eating out & stays": "உணவகங்கள் & தங்குமிடம்", "Personal care & jewellery": "தனிநபர் பராமரிப்பு & நகை",
    "Market loans (SDLs)": "சந்தைக் கடன்கள் (SDL)", "Other loans": "பிற கடன்கள்", "Loans from the Centre": "ஒன்றிய அரசுக் கடன்கள்",
    "Provident funds": "வருங்கால வைப்பு நிதி", "Deposits, reserves and other": "வைப்புகள், இருப்பு நிதி & பிற",
    "Tamil Nadu": "தமிழ்நாடு", "Andhra Pradesh": "ஆந்திரப் பிரதேசம்", "Assam": "அசாம்", "Bihar": "பீகார்",
    "Chhattisgarh": "சத்தீஸ்கர்", "NCT of Delhi": "டெல்லி", "Gujarat": "குஜராத்", "Haryana": "ஹரியானா",
    "Himachal Pradesh": "இமாச்சலப் பிரதேசம்", "Jammu And Kashmir": "ஜம்மு காஷ்மீர்", "Jharkhand": "ஜார்க்கண்ட்",
    "Karnataka": "கர்நாடகா", "Kerala": "கேரளா", "Madhya Pradesh": "மத்தியப் பிரதேசம்", "Maharashtra": "மகாராஷ்டிரா",
    "Odisha": "ஒடிசா", "Punjab": "பஞ்சாப்", "Rajasthan": "ராஜஸ்தான்", "Telangana": "தெலங்கானா",
    "Uttar Pradesh": "உத்தரப் பிரதேசம்", "Uttarakhand": "உத்தராகண்ட்", "West Bengal": "மேற்கு வங்கம்"
  };
  const MONTHS = {
    en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    ta: ["ஜன", "பிப்", "மார்", "ஏப்", "மே", "ஜூன்", "ஜூலை", "ஆக", "செப்", "அக்", "நவ", "டிச"]
  };

  /* ---------- Pick the language ---------- */
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };
  const fromUrl = new URLSearchParams(location.search).get("lang");
  let lang = fromUrl || store.get("tnw-lang") || ((navigator.language || "").toLowerCase().startsWith("ta") ? "ta" : "en");
  if (lang !== "ta") lang = "en";
  if (fromUrl) store.set("tnw-lang", lang);

  const fill = (s, vars) => String(s).replace(/\{(\w+)\}/g, (_, k) => (vars && k in vars ? vars[k] : `{${k}}`));
  const t = (key, vars) => fill((UI[lang] && UI[lang][key]) ?? UI.en[key] ?? key, vars);
  const term = (s) => (lang === "ta" && TERMS_TA[s]) || s;

  /* ---------- Apply to the static page ---------- */
  document.documentElement.lang = lang;
  if (lang === "ta") {
    document.title = "தமிழ்நாடு வாட்ச் — Tamil Nadu Watch";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const v = PAGE_TA[el.dataset.i18n];
      if (v) el.innerHTML = v;
    });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = ATTR_TA[el.dataset.i18nPh] || el.placeholder; });
    document.querySelectorAll("[data-i18n-label]").forEach((el) => {
      el.setAttribute("aria-label", ATTR_TA[el.dataset.i18nLabel] || el.getAttribute("aria-label"));
    });
  }

  /* ---------- Toggle button: reload in the other language, keeping the scroll position ---------- */
  const btn = document.getElementById("langToggle");
  if (btn) {
    btn.textContent = t("switchTo");
    btn.setAttribute("aria-label", t("switchLabel"));
    btn.lang = lang === "ta" ? "en" : "ta";
    btn.addEventListener("click", () => {
      const next = lang === "ta" ? "en" : "ta";
      store.set("tnw-lang", next);
      reload(next);
    });
  }

  /* Reload (optionally in another language), coming back to the same scroll position */
  function reload(nextLang) {
    try { sessionStorage.setItem("tnw-scroll", String(scrollY)); } catch (e) { /* ignore */ }
    const url = new URL(location.href);
    if (nextLang) url.searchParams.set("lang", nextLang);
    location.href = url.toString();
  }
  let restore = null;
  try { restore = sessionStorage.getItem("tnw-scroll"); sessionStorage.removeItem("tnw-scroll"); } catch (e) { /* ignore */ }

  window.I18N = {
    lang, t, term, months: MONTHS[lang], TERMS_TA, reload,
    /* Returns true when a saved position is being restored */
    restoreScroll() {
      if (restore === null) return false;
      // wait for fonts and charts so the page has its full height
      const go = () => scrollTo({ top: Number(restore), behavior: "instant" });
      document.readyState === "complete" ? go() : addEventListener("load", go, { once: true });
      return true;
    }
  };
})();
