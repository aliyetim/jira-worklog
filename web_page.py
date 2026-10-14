"""Tek sayfalık arayüz (HTML/CSS/JS). Yer tutucular: __NONCE__, __APP_KEY__, __BOOT__."""

PAGE = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Worklog raporu</title>
<link rel="icon" href="data:,">
<style nonce="__NONCE__">
:root {
  --ground: #e9edec; --sheet: #f8faf9; --field: #ffffff;
  --ink: #17232b; --on-ink: #f8faf9; --muted: #566770;
  --line: #d3dad8; --line-strong: #b4bfbc;
  --amber: #c77d0a; --tick: #8e9ca0; --tick-weekend: #c6cecf; --tick-on: #17232b;
  --err: #9b3324; --err-bg: #f7e7e3; --focus: #2b6cb0;
  --serif: ui-serif, "New York", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ground: #10161a; --sheet: #182026; --field: #11181d;
    --ink: #e7ece9; --on-ink: #10161a; --muted: #9aa8ae;
    --line: #27323a; --line-strong: #3a4852;
    --amber: #e8a63a; --tick: #62727a; --tick-weekend: #2f3b42; --tick-on: #e7ece9;
    --err: #ffa08f; --err-bg: #3a1f1b; --focus: #6aa8ee;
  }
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { background: var(--ground); }
body {
  margin: 0; color: var(--ink); background: var(--ground);
  font: 15.5px/1.5 var(--sans); -webkit-font-smoothing: antialiased;
}
main { max-width: 660px; margin: 0 auto; padding: 44px 20px 40px; }

h1 {
  margin: 0 0 10px; font: 600 clamp(32px, 7vw, 42px)/1.08 var(--serif); letter-spacing: -0.015em;
}
.lede { margin: 0 0 28px; color: var(--muted); max-width: 52ch; }

.sheet {
  background: var(--sheet); border: 1px solid var(--line); border-radius: 10px;
  box-shadow: 0 1px 0 var(--line);
}
fieldset { margin: 0; padding: 0; border: 0; min-width: 0; }
.row {
  display: grid; grid-template-columns: 148px minmax(0, 1fr); gap: 6px 20px;
  padding: 18px 22px; border-top: 1px solid var(--line);
}
fieldset > .row:first-child { border-top: 0; }
.row > label, .row > .lbl { font-weight: 600; font-size: 14.5px; padding-top: 10px; }
.field { min-width: 0; }
.hint { margin: 6px 0 0; font-size: 13px; color: var(--muted); }

input[type="text"], input[type="password"], input[type="date"] {
  width: 100%; height: 42px; padding: 0 12px; color: var(--ink); background: var(--field);
  border: 1px solid var(--line-strong); border-radius: 6px; font: inherit;
}
input::placeholder { color: var(--muted); opacity: .75; }
input:focus-visible, button:focus-visible, summary:focus-visible, a:focus-visible,
.seg input:focus-visible + span { outline: 2px solid var(--focus); outline-offset: 2px; }
input:disabled { opacity: .6; }

.seg { display: inline-flex; border: 1px solid var(--line-strong); border-radius: 8px; overflow: hidden; background: var(--field); }
.seg label { position: relative; cursor: pointer; }
.seg input { position: absolute; opacity: 0; inset: 0; margin: 0; cursor: pointer; }
.seg span { display: block; padding: 9px 16px; font-size: 14px; white-space: nowrap; }
.seg label + label span { border-left: 1px solid var(--line-strong); }
.seg input:checked + span { background: var(--ink); color: var(--on-ink); font-weight: 600; }
fieldset:disabled .seg label, fieldset:disabled .seg input { cursor: default; }

.dates { display: flex; align-items: center; gap: 10px; margin-top: 12px; }
.dates input { flex: 0 1 156px; width: auto; min-width: 0; }
.dates span { color: var(--muted); }

/* Dönem şeridi: her gün bir çizgi; hazırlanırken dolar, bitince günlük saatleri gösterir */
.ruler {
  display: flex; align-items: flex-end; gap: 2px; height: 64px; margin-top: 16px;
  padding-bottom: 1px; border-bottom: 1px solid var(--line-strong);
}
.ruler i {
  flex: 1 1 0; min-width: 2px; height: calc(var(--h, .3) * 100%); background: var(--tick);
  border-radius: 1px 1px 0 0; transition: height .5s cubic-bezier(.2,.7,.2,1), background-color .25s;
}
.ruler i.weekend { background: var(--tick-weekend); }
.ruler i.on { background: var(--tick-on); }
.ruler i.hours { background: var(--amber); }
.ruler i.zero { background: var(--tick-weekend); }
.ruler-labels { display: flex; justify-content: space-between; margin-top: 6px; font-size: 12.5px; color: var(--muted); }
.ruler-labels span:empty { visibility: hidden; }

.field details { margin-top: 2px; }
summary { cursor: pointer; padding-top: 10px; color: var(--muted); font-size: 14px; list-style: none; }
summary::-webkit-details-marker { display: none; }
summary u { text-underline-offset: 3px; }
details input { margin-top: 10px; }

.link {
  appearance: none; background: none; border: 0; padding: 0; color: var(--focus);
  font: inherit; font-size: 13.5px; text-decoration: underline; text-underline-offset: 3px; cursor: pointer;
}
.token-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.token-head .link { white-space: nowrap; flex: none; }

.actions { display: flex; gap: 12px; padding: 18px 22px 22px; border-top: 1px solid var(--line); }
button.primary, a.primary {
  display: inline-flex; align-items: center; justify-content: center; flex: 1; height: 48px; padding: 0 22px;
  font: 600 16px var(--sans); color: var(--on-ink); background: var(--ink); border: 0; border-radius: 8px;
  cursor: pointer; text-decoration: none;
}
button.primary:hover, a.primary:hover { filter: brightness(1.18); }
button.ghost {
  flex: 1; height: 48px; padding: 0 22px; font: 600 15px var(--sans); color: var(--ink);
  background: transparent; border: 1px solid var(--line-strong); border-radius: 8px; cursor: pointer;
}

.note { margin: 18px 2px 0; }
.note p { margin: 0; }
.msg-err {
  padding: 12px 14px; color: var(--err); background: var(--err-bg);
  border-left: 3px solid var(--err); border-radius: 4px;
}
.msg-info { color: var(--muted); }
.progress-line { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); }
.result { margin: 22px 2px 0; }
.result p { margin: 0 0 14px; font: 500 21px/1.35 var(--serif); }
.result .num { font-variant-numeric: tabular-nums; }
.result .small { display: block; margin-top: 10px; font: 13px var(--sans); color: var(--muted); }
.result .primary { flex: none; display: inline-flex; }

footer { margin: 34px 2px 0; padding-top: 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
footer p { margin: 0 0 8px; max-width: 60ch; }

dialog {
  width: min(460px, calc(100vw - 32px)); padding: 24px 26px; color: var(--ink); background: var(--sheet);
  border: 1px solid var(--line-strong); border-radius: 10px;
}
dialog::backdrop { background: rgba(10, 16, 20, .55); }
dialog h2 { margin: 0 0 8px; font: 600 22px/1.2 var(--serif); }
dialog ol { margin: 12px 0 14px; padding-left: 22px; }
dialog li { margin-bottom: 8px; }
dialog .actions { padding: 6px 0 0; border: 0; }
dialog .primary { height: 44px; font-size: 15px; }

@media (max-width: 560px) {
  main { padding-top: 28px; }
  .row { grid-template-columns: 1fr; padding: 16px 16px; }
  .row > label, .row > .lbl { padding-top: 0; }
  .actions { padding: 16px; flex-direction: column; }
  .actions > .primary, .actions > .ghost { flex: none; width: 100%; }
  .dates input { flex: 1 1 0; }
  .seg { display: flex; }
  .seg label { flex: 1; text-align: center; }
  .seg span { padding: 9px 8px; }
}
@media (prefers-reduced-motion: reduce) { .ruler i { transition: none; } }
</style>
</head>
<body>
<main>
  <header>
    <h1>Worklog raporu</h1>
    <p class="lede">Jira'da seçtiğin projenin worklog kayıtlarını Excel'e aktarır: kim, hangi gün ve saatte, hangi task'a ne kadar süre girmiş.</p>
  </header>

  <form id="f" class="sheet" autocomplete="off" novalidate>
    <fieldset id="fs">
      <div class="row">
        <label for="project">Proje anahtarı</label>
        <div class="field">
          <input id="project" type="text" placeholder="PROJ" autocapitalize="characters" spellcheck="false" autocomplete="off">
          <p class="hint">PROJ-123 numaralı bir task için anahtar PROJ'dur. Birden fazla proje için virgül kullan.</p>
        </div>
      </div>

      <div class="row">
        <span class="lbl" id="period-l">Dönem</span>
        <div class="field">
          <div class="seg" role="radiogroup" aria-labelledby="period-l">
            <label><input type="radio" name="preset" value="prev"><span>Geçen ay</span></label>
            <label><input type="radio" name="preset" value="cur"><span>Bu ay</span></label>
            <label><input type="radio" name="preset" value="custom"><span>Özel aralık</span></label>
          </div>
          <div class="dates">
            <input id="start" type="date" aria-label="Başlangıç tarihi">
            <span>ile</span>
            <input id="end" type="date" aria-label="Bitiş tarihi">
          </div>
          <div id="ruler" class="ruler" aria-hidden="true"></div>
          <div class="ruler-labels" aria-hidden="true"><span id="rl-a"></span><span id="rl-b"></span></div>
          <p id="ruler-note" class="hint"></p>
        </div>
      </div>

      <div class="row">
        <label for="token">Jira token</label>
        <div class="field">
          <input id="token" type="password" placeholder="Token'ı buraya yapıştır" autocomplete="new-password" spellcheck="false">
          <p class="hint token-head"><span>Token kaydedilmez, yalnızca bu raporu almak için kullanılır.</span>
            <button type="button" id="help-open" class="link">Nasıl üretilir?</button></p>
        </div>
      </div>

      <div class="row">
        <span class="lbl" id="fmt-l">Dosya biçimi</span>
        <div class="field">
          <div class="seg" role="radiogroup" aria-labelledby="fmt-l">
            <label><input type="radio" name="fmt" value="xlsx"><span>Excel</span></label>
            <label><input type="radio" name="fmt" value="csv"><span>CSV</span></label>
          </div>
        </div>
      </div>

      <div class="row">
        <span class="lbl">Jira adresi</span>
        <div class="field">
          <details id="url-box">
            <summary><span id="url-view"></span> <u>değiştir</u></summary>
            <input id="url" type="text" spellcheck="false" autocomplete="off" placeholder="https://jira.sirketiniz.com" aria-label="Jira adresi">
          </details>
        </div>
      </div>
    </fieldset>

    <div class="actions">
      <button type="submit" id="go" class="primary">Raporu oluştur</button>
      <button type="button" id="cancel" class="ghost" hidden>İptal et</button>
    </div>
  </form>

  <div id="note" class="note" aria-live="polite"></div>

  <section id="result" class="result" hidden>
    <p id="result-text"></p>
    <a id="dl" class="primary" href="#" download>Excel'i indir</a>
    <span class="small">Dosya tarayıcının indirilenler klasörüne kaydedilir. Saatler Türkiye saatine (UTC+3) göre yazılır.</span>
  </section>

  <footer>
    <p>Bu uygulama Jira'dan yalnızca okuma yapar; hiçbir kaydı değiştirmez veya silmez. Bilgiler yalnızca bu bilgisayarda işlenir.</p>
    <button type="button" id="quit" class="link">Uygulamayı kapat</button>
  </footer>
</main>

<dialog id="help">
  <h2>Token nasıl üretilir?</h2>
  <p>Token, Jira'ya senin adına giriş yapan geçici bir şifredir. Kendi token'ını üret ve kimseyle paylaşma.</p>
  <ol>
    <li>Aşağıdaki düğmeyle Jira profil sayfanı aç (gerekirse giriş yap).</li>
    <li>Soldaki menüden <b>Personal Access Tokens</b> bölümünü aç.</li>
    <li><b>Create token</b> de, ad olarak «worklog rapor» yaz ve oluştur.</li>
    <li>Çıkan uzun metni kopyala (bir daha gösterilmez) ve bu sayfadaki token kutusuna yapıştır.</li>
  </ol>
  <p class="hint">Menü adları Jira sürümüne göre biraz değişebilir. İşin bitince token'ı Jira'dan silebilirsin.</p>
  <div class="actions">
    <a id="profile-link" class="primary" href="#" target="_blank" rel="noopener noreferrer">Jira profil sayfasını aç</a>
    <button type="button" id="help-close" class="ghost">Kapat</button>
  </div>
</dialog>

<script nonce="__NONCE__">
(() => {
  "use strict";
  const KEY = "__APP_KEY__";
  const BOOT = __BOOT__;
  const $ = (id) => document.getElementById(id);
  const nf = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1 });
  const dayFmt = new Intl.DateTimeFormat("tr-TR", { day: "numeric", month: "short" });
  const dayFull = new Intl.DateTimeFormat("tr-TR", { day: "numeric", month: "long", weekday: "short" });
  const pad = (n) => String(n).padStart(2, "0");
  const iso = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  const parseISO = (s) => { const d = /^\d{4}-\d{2}-\d{2}$/.test(s || "") ? new Date(s + "T00:00:00") : null; return d && !isNaN(d) ? d : null; };
  const radio = (name) => document.querySelector('input[name="' + name + '"]:checked').value;
  const setRadio = (name, v) => { const el = document.querySelector('input[name="' + name + '"][value="' + v + '"]'); if (el) el.checked = true; };

  const el = { project: $("project"), start: $("start"), end: $("end"), token: $("token"), url: $("url"),
               ruler: $("ruler"), note: $("note"), result: $("result") };
  let cells = [];           // şeritteki çizgiler: {node, keys}
  let lastRev = -1, failures = 0, timer = null;

  // ---------- API ----------
  async function api(path, opts) {
    const r = await fetch(path, Object.assign({ cache: "no-store" }, opts, {
      headers: { "X-App-Key": KEY, "Content-Type": "application/json" } }));
    let data = null; try { data = await r.json(); } catch (_) {}
    return { ok: r.ok, status: r.status, data };
  }

  // ---------- Jira adresi ----------
  function hostLabel() {
    try { return new URL(/^https?:/i.test(el.url.value) ? el.url.value : "https://" + el.url.value).host; }
    catch (_) { return el.url.value; }
  }
  function baseUrl() {
    try { const u = new URL(/^https?:/i.test(el.url.value) ? el.url.value : "https://" + el.url.value); return u.origin; }
    catch (_) { return BOOT.url; }
  }

  // ---------- Dönem şeridi ----------
  function buckets(s, e) {
    if (!s || !e || e < s) return null;
    const days = [];
    for (let d = new Date(s); d <= e && days.length <= 400; d.setDate(d.getDate() + 1)) days.push(new Date(d));
    if (days.length > 400) return null;
    const weekly = days.length > 92, items = [];
    if (!weekly) days.forEach((d) => items.push({ from: d, to: d, keys: [iso(d)], weekend: d.getDay() === 0 || d.getDay() === 6 }));
    else for (let i = 0; i < days.length; i += 7) {
      const c = days.slice(i, i + 7);
      items.push({ from: c[0], to: c[c.length - 1], keys: c.map(iso), weekend: false });
    }
    return { items, count: days.length, weekdays: days.filter((d) => d.getDay() % 6 !== 0).length, weekly };
  }

  function drawRuler(startISO, endISO) {
    const b = buckets(parseISO(startISO), parseISO(endISO));
    el.ruler.textContent = "";
    cells = [];
    if (!b) { $("rl-a").textContent = ""; $("rl-b").textContent = ""; $("ruler-note").textContent = "Başlangıç ve bitiş tarihlerini kontrol et."; return null; }
    b.items.forEach((it) => {
      const n = document.createElement("i");
      if (it.weekend) n.className = "weekend";
      n.style.setProperty("--h", it.weekend ? ".16" : ".34");
      el.ruler.appendChild(n);
      cells.push({ node: n, keys: it.keys, from: it.from, to: it.to, weekend: it.weekend });
    });
    $("rl-a").textContent = dayFmt.format(b.items[0].from);
    $("rl-b").textContent = dayFmt.format(b.items[b.items.length - 1].to);
    $("ruler-note").textContent = b.count + " gün, " + b.weekdays + " iş günü" + (b.weekly ? " (haftalık gösterim)" : "");
    return b;
  }
  const drawFromForm = () => drawRuler(el.start.value, el.end.value);

  function fillRuler(frac) {
    const upto = Math.round(frac * cells.length);
    cells.forEach((c, i) => c.node.classList.toggle("on", i < upto));
  }

  function showHours(daily) {
    let max = 0;
    const sums = cells.map((c) => c.keys.reduce((a, k) => a + (daily[k] || 0), 0));
    sums.forEach((v) => { if (v > max) max = v; });
    cells.forEach((c, i) => {
      const v = sums[i];
      c.node.classList.remove("on", "weekend");
      c.node.classList.toggle("hours", v > 0);
      c.node.classList.toggle("zero", v === 0);
      c.node.style.setProperty("--h", v > 0 && max > 0 ? Math.max(0.1, v / max).toFixed(3) : ".05");
      const when = c.from.getTime() === c.to.getTime() ? dayFull.format(c.from) : dayFmt.format(c.from) + " – " + dayFmt.format(c.to);
      c.node.title = when + ": " + (v > 0 ? nf.format(v) + " saat" : "kayıt yok");
    });
  }

  // ---------- Form ----------
  function applyPreset() {
    const p = radio("preset"), custom = p === "custom";
    if (!custom) { el.start.value = BOOT.ranges[p][0]; el.end.value = BOOT.ranges[p][1]; }
    el.start.disabled = el.end.disabled = !custom;
    drawFromForm();
  }
  function setNote(text, cls) {
    el.note.textContent = "";
    if (!text) return;
    const p = document.createElement("p");
    p.className = cls; p.textContent = text;
    if (cls === "msg-err") p.setAttribute("role", "alert");
    el.note.appendChild(p);
  }

  // ---------- Durum ----------
  function render(st) {
    const running = st.state === "running";
    $("fs").disabled = running;
    $("go").hidden = running;
    $("cancel").hidden = !running;
    if (st.rev === lastRev) return;
    lastRev = st.rev;

    if (running) {
      el.result.hidden = true;
      if (!cells.length || el.start.value !== st.start || el.end.value !== st.end) drawRuler(st.start, st.end);
      if (st.stage === "search" || !st.total) {
        setNote("Bu dönemde worklog girilmiş task'lar aranıyor…", "msg-info");
        fillRuler(0);
      } else {
        setNote(nf.format(st.done) + " / " + nf.format(st.total) + " task işlendi…", "msg-info");
        fillRuler(st.done / st.total);
      }
    } else if (st.state === "done") {
      drawRuler(st.start, st.end);
      showHours(st.daily || {});
      setNote("", "");
      $("result-text").textContent = "";
      const t = $("result-text");
      t.append("Rapor hazır: " + nf.format(st.people) + " kişi, " + nf.format(st.count) + " kayıt, toplam ");
      const num = document.createElement("span"); num.className = "num"; num.textContent = nf.format(st.hours) + " saat";
      t.append(num, ".");
      const a = $("dl");
      a.href = "/download?k=" + encodeURIComponent(KEY);
      a.textContent = (st.filename || "").endsWith(".csv") ? "CSV'yi indir" : "Excel'i indir";
      el.result.hidden = false;
    } else if (st.state === "error") {
      el.result.hidden = true; drawFromForm();
      setNote(st.message, "msg-err");
    } else if (st.state === "empty") {
      el.result.hidden = true; drawFromForm();
      setNote("Bu dönemde seçilen proje için worklog bulunamadı. Proje anahtarını ve tarihleri kontrol et.", "msg-err");
    } else if (st.state === "cancelled") {
      el.result.hidden = true; drawFromForm();
      setNote("İptal edildi.", "msg-info");
    }
  }

  function lost() {
    clearInterval(timer);
    $("fs").disabled = true; $("go").hidden = true; $("cancel").hidden = true;
    setNote("Uygulamayla bağlantı koptu. Jira Worklog uygulamasını yeniden aç; bu sekmeyi kapatabilirsin.", "msg-err");
  }

  async function poll() {
    try {
      const r = await api("/api/status");
      if (!r.ok) throw new Error("status " + r.status);
      failures = 0;
      render(r.data);
    } catch (_) {
      if (++failures >= 3) lost();
    }
  }

  // ---------- Olaylar ----------
  document.querySelectorAll('input[name="preset"]').forEach((r) => r.addEventListener("change", applyPreset));
  [el.start, el.end].forEach((i) => i.addEventListener("input", drawFromForm));
  el.url.addEventListener("input", () => { $("url-view").textContent = hostLabel() || "Jira adresini gir"; });

  $("f").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    setNote("", "");
    const body = { url: el.url.value, project: el.project.value, preset: radio("preset"),
                   start: el.start.value, end: el.end.value, token: el.token.value, format: radio("fmt") };
    let r;
    try { r = await api("/api/start", { method: "POST", body: JSON.stringify(body) }); }
    catch (_) { return lost(); }
    if (!r.ok) { setNote((r.data && r.data.error) || "İstek başarısız oldu.", "msg-err"); return; }
    lastRev = -1;
    el.result.hidden = true;
    poll();
  });

  $("cancel").addEventListener("click", async () => {
    $("cancel").disabled = true;
    try { await api("/api/cancel", { method: "POST", body: "{}" }); } catch (_) {}
    setTimeout(() => { $("cancel").disabled = false; }, 1500);
  });

  $("help-open").addEventListener("click", () => {
    const base = baseUrl();
    $("profile-link").href = base ? base + "/secure/ViewProfile.jspa" : "#";
    $("help").showModal();
  });
  $("help-close").addEventListener("click", () => $("help").close());

  $("quit").addEventListener("click", async () => {
    clearInterval(timer);
    try { await api("/api/quit", { method: "POST", body: "{}" }); } catch (_) {}
    document.querySelector("main").innerHTML = "";
    const m = document.createElement("main");
    const h = document.createElement("h1"); h.textContent = "Uygulama kapatıldı";
    const p = document.createElement("p"); p.className = "lede"; p.textContent = "Bu sekmeyi kapatabilirsin.";
    document.body.replaceChildren(m); m.append(h, p);
  });

  window.addEventListener("pagehide", () => { navigator.sendBeacon("/api/bye?k=" + encodeURIComponent(KEY)); });

  // ---------- Başlangıç ----------
  el.project.value = BOOT.project;
  el.url.value = BOOT.url;
  $("url-view").textContent = hostLabel() || "Jira adresini gir";
  if (!el.url.value) $("url-box").open = true;
  setRadio("preset", BOOT.preset);
  setRadio("fmt", BOOT.format);
  if (BOOT.preset === "custom") { el.start.value = BOOT.start; el.end.value = BOOT.end; }
  applyPreset();
  poll();
  timer = setInterval(poll, 1000);
})();
</script>
</body>
</html>
"""
