/* Renders the home dashboard from window.AUTO_DATA (data/auto.js),
   which scripts/fetch_data.py rebuilds from public sources every hour. */
(function () {
  "use strict";

  const D = window.AUTO_DATA;
  if (!D) {
    document.body.insertAdjacentHTML("afterbegin",
      '<p style="padding:16px;background:#fde7ea;color:#8e0f22;margin:0">No data yet — run <code>python scripts/fetch_data.py</code>.</p>');
    return;
  }

  const { t, term, lang, months: MONTHS, TERMS_TA } = window.I18N;
  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? esc(u) : "#");
  const fmt = (n) => Number(n).toLocaleString("en-IN");
  const fmtDate = (iso) => {
    const [y, m, d] = String(iso).slice(0, 10).split("-").map(Number);
    return y && m && d ? `${d} ${MONTHS[m - 1]} ${y}` : esc(iso);
  };
  const sumCounts = (rows) => (rows || []).reduce((a, r) => a + r.count, 0);
  const REPO = "https://github.com/niyosh/tnwatch";
  const params = new URLSearchParams(location.search);

  /* Arrow + % with colour. upIsGood decides whether a rise is green or red. null = not enough history yet. */
  function change(pct, upIsGood) {
    if (pct === null || pct === undefined) return `<span class="flat" title="${t("needsHistory")}">—</span>`;
    const n = Number(pct);
    if (n === 0) return '<span class="flat">0%</span>';
    const up = n > 0;
    const good = up === !!upIsGood;
    return `<span class="${good ? "down" : "up"}"><i class="fa-solid fa-arrow-${up ? "up" : "down"}"></i> ${Math.abs(n)}%</span>`;
  }
  const pctChange = (cur, prev) => (prev ? Math.round(((cur - prev) / prev) * 100) : null);

  /* ---------- Hero photo (optional assets/hero.jpg) ---------- */
  const heroImg = new Image();
  heroImg.onload = () => $("#hero").classList.add("has-photo");
  heroImg.src = "assets/hero.jpg";

  const crime = D.crime || {};
  const corruption = D.corruption || {};
  const official = crime.official;
  const economy = D.economy;
  const hourly = D.hourly || [];
  const month = crime.periods?.month || [];
  const districts = crime.districts || {};

  /* ---------- Freshness: "updated 12 min ago", stale warning, check for newer data ---------- */
  const lastIso = D.lastSuccess || D.generatedAt;
  const lastUpdate = new Date(lastIso);
  function ago(ms) {
    const m = Math.round(ms / 60000);
    if (m < 1) return t("justNow");
    if (m < 60) return t("minAgo", { n: m });
    const h = Math.round(m / 60);
    return h < 48 ? t("hoursAgo", { n: h }) : t("daysAgo", { n: Math.round(h / 24) });
  }
  function renderFreshness() {
    if (isNaN(lastUpdate)) return;
    const age = Date.now() - lastUpdate;
    const time = lastUpdate.toLocaleTimeString(lang === "ta" ? "ta-IN" : "en-IN", { hour: "2-digit", minute: "2-digit" });
    const el = $("#lastUpdated");
    el.innerHTML = `<i class="fa-regular fa-clock"></i> ${t("updatedAgo", { ago: ago(age) })}`;
    el.title = t("updated", { date: fmtDate(lastIso), time });
    const stale = age > 3 * 3600e3;
    $("#notice").classList.toggle("stale", stale);
    $("#staleMsg").hidden = !stale;
    $("#staleMsg").textContent = stale ? t("stale", { ago: ago(age) }) : "";
  }
  renderFreshness();
  setInterval(renderFreshness, 60e3);

  async function checkForUpdate() {
    try {
      const r = await fetch(`data/version.json?ts=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) return;
      const v = await r.json();
      if (new Date(v.generatedAt) > new Date(D.generatedAt)) $("#updateToast").hidden = false;
    } catch (e) { /* offline, or opened from disk */ }
  }
  setInterval(checkForUpdate, 10 * 60e3);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) checkForUpdate(); });
  $("#updateToast button").addEventListener("click", () => window.I18N.reload());

  /* ---------- Stat cards (only what the sources provide) ---------- */
  const stats = [];
  stats.push({ icon: "fa-user-ninja", color: "red", value: fmt(sumCounts(month)), label: t("statCrime"), period: t("last30") });
  const women = month.find((r) => r.type === "Women Safety");
  if (women) stats.push({ icon: "fa-person-dress", color: "purple", value: fmt(women.count), label: t("statWomen"), period: t("last30"), change: women.change });
  stats.push({ icon: "fa-people-group", color: "amber", value: fmt(sumCounts(corruption.periods?.month)), label: t("statCorruption"), period: t("last30") });
  stats.push({ icon: "fa-bolt", color: "teal", value: fmt(hourly.reduce((a, h) => a + h.crime, 0)), label: t("statRecent"), period: t("last24") });
  if (official?.series?.length) {
    const s = official.series, last = s[s.length - 1], prev = s[s.length - 2];
    stats.push({ icon: "fa-scale-balanced", color: "blue", value: fmt(last.value), label: t("statOfficial"), period: `NCRB ${last.year}`,
      change: prev ? pctChange(last.value, prev.value) : null });
  }
  if (economy?.series?.length) {
    const s = economy.series, last = s[s.length - 1], prev = s[s.length - 2];
    stats.push({ icon: "fa-indian-rupee-sign", color: "green", value: `₹${last.value}`, label: `GSDP (${economy.unit})`, period: last.year,
      change: prev ? pctChange(last.value, prev.value) : null, upIsGood: true });
  }
  $("#stats").innerHTML = stats.map((s) => `
    <div class="stat">
      <span class="ico ${s.color}"><i class="fa-solid ${s.icon}"></i></span>
      <div>
        <div class="val">${esc(s.value)}</div>
        <div class="lbl">${esc(s.label)}</div>
        <div class="per">${esc(s.period)}${s.change == null ? "" : `<b>${change(s.change, s.upIsGood)}</b>`}</div>
      </div>
    </div>`).join("");

  /* ---------- Crime / corruption tables ---------- */
  function renderTable(el, rows, withTotal) {
    let html = rows.map((r) => `
      <tr>
        <td class="ti"><span><i class="fa-solid ${esc(r.icon)}"></i></span></td>
        <td>${esc(term(r.type))}</td>
        <td class="num">${fmt(r.count)}</td>
        <td class="chg">${change(r.change, false)}</td>
      </tr>`).join("");
    if (withTotal) {
      html += `<tr class="total"><td class="ti"><i class="fa-regular fa-square-check"></i></td>
        <td>${t("totalReports")}</td><td class="num">${fmt(sumCounts(rows))}</td><td class="chg"></td></tr>`;
    }
    el.innerHTML = `<tbody>${html}</tbody>`;
  }

  function renderOfficial() {
    const el = $("#crimeTable");
    if (!official?.series?.length) {
      el.innerHTML = `<tbody><tr><td class="empty">${t("officialEmpty")}</td></tr></tbody>`;
      return;
    }
    const s = official.series;
    el.innerHTML = `<tbody>${s.slice().reverse().map((p, i, arr) => `
      <tr><td class="ti"><span><i class="fa-solid fa-scale-balanced"></i></span></td>
        <td>${t("ipcYear", { year: esc(p.year) })}</td><td class="num">${fmt(p.value)}</td>
        <td class="chg">${arr[i + 1] ? change(pctChange(p.value, arr[i + 1].value), false) : ""}</td></tr>`).join("")}
      <tr><td colspan="4" class="fine">${t("source")}: <a href="${safeUrl(official.url)}" target="_blank" rel="noopener">${esc(official.name)}</a></td></tr>
    </tbody>`;
  }

  /* ---------- 30-day / 24-hour trend ---------- */
  if (window.Chart) {
    Chart.defaults.font.family = "Inter, 'Noto Sans Tamil', system-ui, sans-serif";
    Chart.defaults.color = "#6b7489";
  }
  let trendChart = null;
  function drawTrend(range) {
    const is24 = range === "24h";
    const crimeDaily = crime.daily || [];
    const corrDaily = corruption.daily || [];
    $("#trendSub").textContent = is24 ? t("trendSubHour") : t("trendSubDay");
    $("#trendNote").textContent = is24 ? t("trendNote24") : (crimeDaily.some((d) => d.partial) ? t("trendNote") : "");
    if (!window.Chart) return;
    const dayLabel = (iso) => { const [, m, d] = iso.split("-").map(Number); return `${d} ${MONTHS[m - 1]}`; };
    const labels = is24 ? hourly.map((h) => h.hour.slice(11, 16)) : crimeDaily.map((d) => dayLabel(d.date));
    const crimeData = is24 ? hourly.map((h) => h.crime) : crimeDaily.map((d) => d.count);
    const corrData = is24 ? hourly.map((h) => h.corruption) : corrDaily.map((d) => d.count);
    const bars = is24 ? crimeData.map(() => "rgba(224,51,74,.8)")
      : crimeDaily.map((d) => (d.partial ? "rgba(224,51,74,.25)" : "rgba(224,51,74,.8)"));
    if (trendChart) trendChart.destroy();
    trendChart = new Chart($("#trendChart"), {
      data: {
        labels,
        datasets: [
          { type: "bar", label: t("crimeReports"), data: crimeData, backgroundColor: bars, borderRadius: 3, order: 1 },
          { type: "line", label: t("corruptionReports"), data: corrData, borderColor: "#f5b301", backgroundColor: "#f5b301",
            pointRadius: 2.5, borderWidth: 2, tension: .3, order: 0 }
        ]
      },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { position: "top", align: "end", labels: { boxWidth: 12, boxHeight: 8, font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 0, autoSkipPadding: 12 } },
          y: { beginAtZero: true, grid: { color: "#eef0f4" }, ticks: { precision: 0, font: { size: 10 } } }
        }
      }
    });
  }

  /* ---------- Tabs (crime, corruption, trend) ---------- */
  const SUBS = { today: t("subToday"), week: t("subWeek"), month: t("subMonth"), official: t("subOfficial") };
  const tabTargets = {
    crime: (p) => {
      $("#crimeSub").textContent = SUBS[p];
      p === "official" ? renderOfficial() : renderTable($("#crimeTable"), crime.periods?.[p] || [], true);
    },
    corruption: (p) => renderTable($("#corruptionTable"), corruption.periods?.[p] || [], false),
    trend: drawTrend
  };
  document.querySelectorAll(".tabs").forEach((tabs) => {
    const render = tabTargets[tabs.dataset.target];
    const buttons = tabs.querySelectorAll("button");
    buttons.forEach((b) => {
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", b.classList.contains("on"));
    });
    tabs.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      buttons.forEach((b) => {
        b.classList.toggle("on", b === btn);
        b.setAttribute("aria-selected", b === btn);
      });
      render(btn.dataset.period);
    });
    render(tabs.querySelector("button.on").dataset.period);
  });

  /* ---------- Story helpers ---------- */
  const storyLang = (a) => a.lang || "en";
  const langBadge = (a) => (storyLang(a) === lang ? "" : `<span class="lang-badge">${storyLang(a) === "ta" ? "தமிழ்" : "EN"}</span>`);
  // Show stories in the reader's language when there are enough of them
  const preferLang = (items, min) => {
    const mine = items.filter((a) => storyLang(a) === lang);
    return mine.length >= min ? mine : items;
  };
  function reportLink(a, cat) {
    const q = new URLSearchParams({
      title: `Correction: ${a.title}`.slice(0, 120),
      labels: "correction",
      body: [`Story: ${a.title}`, `Link: ${a.url}`,
        `Shown as: ${cat} · ${(a.types || [a.tag]).join(", ")} · ${a.district || "no district"}`,
        "", "What is wrong?", "", "", "---", "Maintainer: add the fix to scripts/corrections.json"].join("\n")
    });
    return `<a class="report" href="${REPO}/issues/new?${esc(q.toString())}" target="_blank" rel="noopener"
      title="${esc(t("report"))}" aria-label="${esc(t("report"))}"><i class="fa-regular fa-flag"></i></a>`;
  }
  const storyMeta = (a, cat) => `<span class="meta">${a.district ? `<b>${esc(term(a.district))}</b> · ` : ""}`
    + `${esc((a.types || [a.tag]).map(term).join(", "))} · ${esc(a.source)}`
    + `${a.outlets > 1 ? ` ${t("moreOutlets", { n: a.outlets - 1 })}` : ""} · ${fmtDate(a.date)}${langBadge(a)}${reportLink(a, cat)}</span>`;

  /* ---------- District tile map (approximate geographic layout) ---------- */
  const LAYOUT = [
    ["Tiruvallur", 5, 0], ["Chennai", 6, 0],
    ["Krishnagiri", 1, 1], ["Tirupathur", 2, 1], ["Vellore", 3, 1], ["Ranipet", 4, 1], ["Kanchipuram", 5, 1], ["Chengalpattu", 6, 1],
    ["Dharmapuri", 1, 2], ["Salem", 2, 2], ["Tiruvannamalai", 3, 2], ["Villupuram", 4, 2], ["Cuddalore", 5, 2],
    ["Nilgiris", 0, 3], ["Erode", 1, 3], ["Namakkal", 2, 3], ["Kallakurichi", 3, 3], ["Perambalur", 4, 3], ["Ariyalur", 5, 3], ["Mayiladuthurai", 6, 3],
    ["Coimbatore", 0, 4], ["Tiruppur", 1, 4], ["Karur", 2, 4], ["Tiruchirappalli", 3, 4], ["Thanjavur", 4, 4], ["Tiruvarur", 5, 4], ["Nagapattinam", 6, 4],
    ["Theni", 1, 5], ["Dindigul", 2, 5], ["Madurai", 3, 5], ["Pudukkottai", 4, 5],
    ["Virudhunagar", 2, 6], ["Sivaganga", 3, 6], ["Ramanathapuram", 4, 6],
    ["Tenkasi", 1, 7], ["Tirunelveli", 2, 7], ["Thoothukudi", 3, 7],
    ["Kanyakumari", 2, 8]
  ];
  const maxD = Math.max(1, ...Object.values(districts));
  // Levels relative to the busiest district, since news counts are small numbers
  const level = (n) => (n === 0 ? "x" : n / maxD >= 0.6 ? 3 : n / maxD >= 0.3 ? 2 : n / maxD >= 0.12 ? 1 : 0);
  const LEVEL_NAMES = { x: term("None"), 0: term("Low"), 1: term("Moderate"), 2: term("High"), 3: term("Very High") };
  const map = $("#tileMap");
  map.innerHTML = LAYOUT.map(([name, c, r]) => {
    const n = districts[name] ?? 0;
    return `<div class="tile lv${level(n)}" style="grid-column:${c + 1};grid-row:${r + 1}"
      data-name="${esc(name)}" data-n="${n}" role="button" tabindex="0" aria-label="${esc(t("tileLabel", { d: term(name), n: fmt(n) }))}"></div>`;
  }).join("");

  const tip = document.createElement("div");
  tip.className = "tip";
  tip.hidden = true;
  document.body.appendChild(tip);
  map.addEventListener("mousemove", (e) => {
    const tile = e.target.closest(".tile");
    if (!tile) { tip.hidden = true; return; }
    const n = Number(tile.dataset.n);
    tip.innerHTML = `<b>${esc(term(tile.dataset.name))}</b> · ${t("tileTip", { n: fmt(n) })} · ${LEVEL_NAMES[level(n)]}`;
    tip.style.left = e.clientX + 12 + "px";
    tip.style.top = e.clientY + 12 + "px";
    tip.hidden = false;
  });
  map.addEventListener("mouseleave", () => { tip.hidden = true; });
  const pickDistrict = (tile) => {
    districtFilter.value = tile.dataset.name;
    renderCrimeStories(true);
    $("#crimeNews").scrollIntoView({ behavior: "smooth", block: "start" });
  };
  map.addEventListener("click", (e) => { const tile = e.target.closest(".tile"); if (tile) pickDistrict(tile); });
  map.addEventListener("keydown", (e) => {
    const tile = e.target.closest(".tile");
    if (tile && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pickDistrict(tile); }
  });

  /* ---------- News + corruption lists ---------- */
  const tagIcon = { crime: "fa-handcuffs", corruption: "fa-sack-dollar", development: "fa-industry", policy: "fa-scale-balanced", infrastructure: "fa-train-subway" };
  const tagBg = { crime: "#e0334a", corruption: "#d99a00", development: "#4f8df7", policy: "#8b4cf0", infrastructure: "#22b35e" };
  $("#newsList").innerHTML = preferLang(D.news || [], 4).slice(0, 8).map((n) => {
    const tag = String(n.tag || "").toLowerCase();
    return `<li>
      <span class="thumb" style="background:${tagBg[tag] || "#6b7489"}"><i class="fa-solid ${tagIcon[tag] || "fa-newspaper"}"></i></span>
      <span><a class="news-title" href="${safeUrl(n.url)}" target="_blank" rel="noopener">${esc(n.title)}</a>
        <small class="src">${esc(n.source)}${langBadge(n)}</small></span>
      <span class="news-meta"><time>${fmtDate(n.date)}</time><span class="pill ${esc(tag)}">${esc(term(n.tag))}</span></span>
    </li>`;
  }).join("") || `<li class="empty">${t("noStories")}</li>`;

  $("#corruptionHeadlines").innerHTML = preferLang(corruption.latest || [], 3).slice(0, 6).map((a) => `
    <li><a href="${safeUrl(a.url)}" target="_blank" rel="noopener">${esc(a.title)}</a>${storyMeta(a, "corruption")}</li>`).join("")
    || `<li class="empty">${t("noStories")}</li>`;

  /* ---------- Crime stories: filter by district / type / language, paged, shareable ---------- */
  const stories = crime.recent || [];
  const districtFilter = $("#districtFilter");
  const typeFilter = $("#typeFilter");
  const langFilter = $("#langFilter");
  const PAGE = 8;
  let shown = PAGE;
  let autoLang = true; // until the reader picks a language themselves
  Object.keys(districts).sort((a, b) => term(a).localeCompare(term(b), lang)).forEach((d) => {
    districtFilter.insertAdjacentHTML("beforeend", `<option value="${esc(d)}">${esc(term(d))} (${districts[d]})</option>`);
  });
  month.forEach((r) => typeFilter.insertAdjacentHTML("beforeend", `<option value="${esc(r.type)}">${esc(term(r.type))}</option>`));
  if (districts[params.get("d")] !== undefined) districtFilter.value = params.get("d");
  if (month.some((r) => r.type === params.get("ty"))) typeFilter.value = params.get("ty");
  langFilter.value = stories.filter((a) => storyLang(a) === lang).length >= 3 ? lang : "";

  const filtered = () => {
    const d = districtFilter.value, ty = typeFilter.value, l = langFilter.value;
    return stories.filter((a) => (!d || a.district === d) && (!ty || (a.types || [a.tag]).includes(ty)) && (!l || storyLang(a) === l));
  };
  function renderCrimeStories(reset) {
    if (reset) shown = PAGE;
    let list = filtered();
    if (!list.length && autoLang && langFilter.value) {
      langFilter.value = ""; // nothing in the reader's language for this filter: show every language
      list = filtered();
    }
    $("#crimeHeadlines").innerHTML = list.slice(0, shown).map((a) => `
      <li><a href="${safeUrl(a.url)}" target="_blank" rel="noopener">${esc(a.title)}</a>${storyMeta(a, "crime")}</li>`).join("")
      || `<li class="empty">${t("noMatch")}</li>`;
    $("#crimeNewsSub").textContent = districtFilter.value || typeFilter.value
      ? t("storiesCount", { n: list.length }) : t("crimeNewsSub");
    $("#crimeMore").hidden = list.length <= shown;
    // keep the address shareable: ?d=Madurai&ty=Murder
    const u = new URL(location.href);
    [["d", districtFilter.value], ["ty", typeFilter.value]].forEach(([k, v]) => (v ? u.searchParams.set(k, v) : u.searchParams.delete(k)));
    history.replaceState(null, "", u);
  }
  districtFilter.addEventListener("change", () => renderCrimeStories(true));
  typeFilter.addEventListener("change", () => renderCrimeStories(true));
  langFilter.addEventListener("change", () => { autoLang = false; renderCrimeStories(true); });
  $("#crimeMore").addEventListener("click", () => { shown += PAGE; renderCrimeStories(false); });
  renderCrimeStories(true);

  /* ---------- Sharing (native share sheet, else WhatsApp) ---------- */
  function shareUrl(base) {
    const u = new URL(base);
    u.hash = "";
    if (lang === "ta") u.searchParams.set("lang", "ta");
    // a new value every hour makes WhatsApp and others fetch a fresh preview image
    u.searchParams.set("s", String(D.generatedAt || "").slice(0, 13).replace(/\D/g, ""));
    return u.toString();
  }
  async function share(text, url) {
    if (navigator.share) {
      try { await navigator.share({ title: document.title, text, url }); } catch (e) { /* cancelled */ }
      return;
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`, "_blank", "noopener");
  }
  $("#shareSite").addEventListener("click", () =>
    share(t("shareText", { n: fmt(sumCounts(month)) }), shareUrl(location.origin + location.pathname)));
  $("#shareView").addEventListener("click", () => {
    const d = districtFilter.value;
    share(d ? t("shareDistrict", { d: term(d), n: fmt(districts[d] || 0) }) : t("shareText", { n: fmt(sumCounts(month)) }),
      shareUrl(location.href));
  });

  /* ---------- Sources ---------- */
  const STATUS = { ok: ["ok", "fa-circle-check"], partial: ["warn", "fa-triangle-exclamation"], cached: ["warn", "fa-clock-rotate-left"],
    "needs key": ["warn", "fa-key"], "not configured": ["off", "fa-plug-circle-xmark"], error: ["bad", "fa-circle-xmark"] };
  const STATUS_KEY = { ok: "stOk", partial: "stPartial", cached: "stCached", "needs key": "stNeedsKey", "not configured": "stNotConfigured", error: "stError" };
  $("#sourceList").innerHTML = (D.sources || []).map((s) => {
    const [cls, icon] = STATUS[s.status] || ["off", "fa-circle"];
    return `<li><i class="fa-solid ${icon} st-${cls}"></i>
      <span><a href="${safeUrl(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a><small>${esc(s.detail)}</small></span>
      <span class="pill st-${cls}">${esc(t(STATUS_KEY[s.status] || "stError"))}</span></li>`;
  }).join("");

  /* ---------- Search ---------- */
  // District and type names are indexed in both scripts so either can be typed
  const both = (s) => (TERMS_TA[s] ? `${term(s)} (${lang === "ta" ? s : TERMS_TA[s]})` : s);
  const index = [];
  (D.news || []).forEach((n) => index.push({ kind: term(n.tag || "News"), text: n.title, href: n.url }));
  stories.forEach((a) => index.push({ kind: t("kindCrime"), text: `${a.title}${a.district ? " — " + both(a.district) : ""}`, href: a.url }));
  (corruption.latest || []).forEach((a) => index.push({ kind: t("kindCorruption"), text: a.title, href: a.url }));
  Object.keys(districts).forEach((d) => index.push({ kind: t("kindDistrict"), text: t("searchDistrict", { d: both(d), n: fmt(districts[d]) }),
    href: `?d=${encodeURIComponent(d)}${lang === "ta" ? "&lang=ta" : ""}` }));
  month.forEach((r) => index.push({ kind: t("kindType"), text: t("searchType", { t: both(r.type), n: fmt(r.count) }),
    href: `?ty=${encodeURIComponent(r.type)}${lang === "ta" ? "&lang=ta" : ""}` }));

  const input = $("#searchInput");
  const results = $("#searchResults");
  function search() {
    const q = input.value.trim().toLowerCase();
    if (!q) { results.hidden = true; return; }
    const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig");
    const seen = new Set();
    const hits = index.filter((x) => x.text.toLowerCase().includes(q) && !seen.has(x.text) && seen.add(x.text)).slice(0, 12);
    results.innerHTML = hits.length
      ? hits.map((h) => {
          const ext = /^https?:/.test(h.href);
          return `<a href="${ext ? safeUrl(h.href) : esc(h.href)}"${ext ? ' target="_blank" rel="noopener"' : ""}><span class="kind">${esc(h.kind)}</span><span>${esc(h.text).replace(re, (m) => `<mark>${m}</mark>`)}</span></a>`;
        }).join("")
      : `<div class="none">${t("noResults", { q: esc(input.value) })}</div>`;
    results.hidden = false;
  }
  input.addEventListener("input", search);
  $("#searchForm").addEventListener("submit", (e) => { e.preventDefault(); search(); });
  results.addEventListener("click", () => { results.hidden = true; });
  document.addEventListener("click", (e) => { if (!e.target.closest("#searchForm")) results.hidden = true; });
  $(".search-jump").addEventListener("click", () => {
    $("#hero").scrollIntoView({ behavior: "smooth" });
    setTimeout(() => input.focus(), 300);
  });

  /* ---------- Mobile nav ---------- */
  const toggle = $(".nav-toggle");
  toggle.addEventListener("click", () => {
    const open = $("#mainnav").classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });
  $("#mainnav").addEventListener("click", (e) => {
    if (e.target.closest("a")) { $("#mainnav").classList.remove("open"); toggle.setAttribute("aria-expanded", false); }
  });

  /* ---------- Where to start: saved scroll after a language switch, else a shared district/type link ---------- */
  if (!window.I18N.restoreScroll() && (params.get("d") || params.get("ty"))) {
    const go = () => $("#crimeNews").scrollIntoView({ block: "start" });
    document.readyState === "complete" ? go() : addEventListener("load", go, { once: true });
  }

  /* ---------- Economy (only when an official source is connected) ---------- */
  if (!economy?.series?.length) return;
  $("#economy").hidden = false;
  $("#navEconomy").hidden = false;
  const years = economy.series.map((p) => p.year);
  const values = economy.series.map((p) => p.value);
  const growth = values.map((v, i) => (i ? +(((v - values[i - 1]) / values[i - 1]) * 100).toFixed(1) : null));
  $("#economySub").innerHTML = `${t("source")}: <a href="${safeUrl(economy.url)}" target="_blank" rel="noopener">${esc(economy.name)}</a>`;
  const last = values.length - 1;
  $("#highlights").innerHTML = `
    <div class="hl green"><b>₹${values[last]}</b><span>${esc(economy.unit)}</span><span>GSDP ${esc(years[last])}</span></div>
    <div class="hl purple"><b>${growth[last] ?? "—"}%</b><span>${t("nominalGrowth")}</span><span>${esc(years[last])}</span></div>`;

  if (!window.Chart) return;
  new Chart($("#gdpChart"), {
    data: {
      labels: years,
      datasets: [
        { type: "line", label: t("growth"), data: growth, yAxisID: "y1", borderColor: "#8b4cf0", backgroundColor: "#8b4cf0",
          pointRadius: 4, borderWidth: 2, tension: .25, order: 0, spanGaps: true },
        { type: "bar", label: `GSDP (${economy.unit})`, data: values, yAxisID: "y", backgroundColor: "rgba(79,141,247,.35)",
          borderColor: "#4f8df7", borderWidth: { top: 2 }, borderRadius: 3, barPercentage: .6, order: 1 }
      ]
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { boxWidth: 12, boxHeight: 8, font: { size: 11 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: { beginAtZero: true, grid: { color: "#eef0f4" }, ticks: { font: { size: 10 } } },
        y1: { position: "right", beginAtZero: true, grid: { display: false }, ticks: { font: { size: 10 }, callback: (v) => v + "%" } }
      }
    }
  });
})();
