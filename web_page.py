"""Tek sayfalık arayüz (HTML/CSS/JS). Yer tutucular: __NONCE__, __APP_KEY__, __BOOT__."""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Worklog report</title>
<link rel="icon" href="data:,">
<style nonce="__NONCE__">
:root {
  --ground: #e9edec; --sheet: #f8faf9; --field: #ffffff;
  --ink: #17232b; --on-ink: #f8faf9; --muted: #566770;
  --line: #d3dad8; --line-strong: #b4bfbc;
  --amber: #c77d0a; --tick: #8e9ca0; --tick-weekend: #c6cecf; --tick-on: #17232b;
  --err: #9b3324; --err-bg: #f7e7e3; --focus: #2b6cb0; --hover: #eef2f1;
  --serif: ui-serif, "New York", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ground: #10161a; --sheet: #182026; --field: #11181d;
    --ink: #e7ece9; --on-ink: #10161a; --muted: #9aa8ae;
    --line: #27323a; --line-strong: #3a4852;
    --amber: #e8a63a; --tick: #62727a; --tick-weekend: #2f3b42; --tick-on: #e7ece9;
    --err: #ffa08f; --err-bg: #3a1f1b; --focus: #6aa8ee; --hover: #1e2930;
  }
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { background: var(--ground); }
body {
  margin: 0; color: var(--ink); background: var(--ground);
  font: 15.5px/1.5 var(--sans); -webkit-font-smoothing: antialiased;
}
main { max-width: 660px; margin: 0 auto; padding: 44px 20px 0; }
.foot { max-width: 660px; margin: 0 auto; padding: 0 20px 40px; }

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

/* Önizleme tablosu */
.preview { max-width: 1680px; margin: 40px auto 0; padding: 0 24px; }
.pv-head { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 14px; margin: 0 2px 12px; }
.pv-head h2 { margin: 0 auto 0 0; font: 600 26px/1.15 var(--serif); }
.pv-head input[type="search"] { width: 290px; height: 38px; }
input[type="search"] {
  padding: 0 12px; color: var(--ink); background: var(--field);
  border: 1px solid var(--line-strong); border-radius: 6px; font: inherit; font-size: 14px;
}
.chips:empty { display: none; }
.chips { display: flex; gap: 8px; margin: 0 2px 12px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px; height: 30px; padding: 0 4px 0 12px;
  color: var(--on-ink); background: var(--ink); border-radius: 15px; font-size: 13.5px;
}
.chip button {
  appearance: none; width: 24px; height: 24px; padding: 0; color: inherit; background: none;
  border: 0; border-radius: 12px; font: 16px/1 var(--sans); cursor: pointer;
}
.chip button:hover { background: rgba(127, 127, 127, .3); }
.pv-scroll {
  max-height: 72vh; overflow: auto; background: var(--sheet);
  border: 1px solid var(--line); border-radius: 10px;
}
table.pv { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13.5px; line-height: 1.4; }
.pv th {
  position: sticky; top: 0; z-index: 1; padding: 0; text-align: left; font-weight: 600; white-space: nowrap;
  background: var(--sheet); border-bottom: 1px solid var(--line-strong);
}
.pv th > span, .pv th > button { display: block; padding: 10px 9px; }
.pv th > button {
  appearance: none; width: 100%; color: inherit; background: none; border: 0;
  font: inherit; text-align: inherit; cursor: pointer;
}
.pv th > button:hover { background: var(--hover); }
.pv th > button::after { content: "↕"; margin-left: 6px; color: var(--muted); opacity: .45; font-weight: 400; }
.pv th[aria-sort="ascending"] > button::after { content: "↑"; opacity: 1; color: var(--ink); }
.pv th[aria-sort="descending"] > button::after { content: "↓"; opacity: 1; color: var(--ink); }
.pv td { padding: 8px 9px; vertical-align: top; border-bottom: 1px solid var(--line); }
.pv tbody tr:hover td { background: var(--hover); }
.pv .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.pv th.num > button { text-align: right; }
.pv .nw { white-space: nowrap; }
.pv .who { min-width: 96px; }
.pv .dim { color: var(--muted); }
.pv .sum { min-width: 150px; max-width: 360px; }
.pv .cmt { min-width: 130px; max-width: 420px; color: var(--muted); }
.pv .clip { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.pv a { color: var(--focus); text-underline-offset: 2px; }
.pv td .link { font-size: inherit; color: var(--ink); text-decoration-color: var(--line-strong); text-align: left; }
.pv td .link:hover { color: var(--focus); }
.pv .bar { width: 28%; min-width: 120px; }
.pv .bar i {
  display: block; height: 8px; margin-top: 6px; width: calc(var(--w, 0) * 100%); min-width: 2px;
  background: var(--amber); border-radius: 2px;
}
.pv tfoot td {
  position: sticky; bottom: 0; font-weight: 600; background: var(--sheet);
  border-top: 1px solid var(--line-strong); border-bottom: 0;
}
.pv tbody tr:last-child td { border-bottom: 0; }
.pv-foot {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px 16px;
  margin: 10px 2px 0; font-size: 13px; color: var(--muted);
}
.pv-foot .ghost { flex: none; height: 36px; padding: 0 16px; font-size: 14px; }
.pv-empty td { padding: 28px 12px; text-align: center; color: var(--muted); }

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
  .preview { padding: 0 16px; }
  .pv-head h2 { flex: 1 0 100%; }
  .pv-head .seg { flex: 1 1 100%; }
  .pv-head input[type="search"] { flex: 1 1 100%; width: auto; }
}
@media (prefers-reduced-motion: reduce) { .ruler i { transition: none; } }
</style>
</head>
<body>
<main>
  <header>
    <h1>Worklog report</h1>
    <p class="lede">Exports the worklogs of your Jira project to Excel: who logged how much time, on which issue, on which day and at what time.</p>
  </header>

  <form id="f" class="sheet" autocomplete="off" novalidate>
    <fieldset id="fs">
      <div class="row">
        <label for="project">Project key</label>
        <div class="field">
          <input id="project" type="text" placeholder="PROJ" autocapitalize="characters" spellcheck="false" autocomplete="off">
          <p class="hint">For an issue numbered PROJ-123 the key is PROJ. Separate several projects with commas.</p>
        </div>
      </div>

      <div class="row">
        <span class="lbl" id="period-l">Period</span>
        <div class="field">
          <div class="seg" role="radiogroup" aria-labelledby="period-l">
            <label><input type="radio" name="preset" value="prev"><span>Last month</span></label>
            <label><input type="radio" name="preset" value="cur"><span>This month</span></label>
            <label><input type="radio" name="preset" value="custom"><span>Custom range</span></label>
          </div>
          <div class="dates">
            <input id="start" type="date" aria-label="Start date">
            <span>to</span>
            <input id="end" type="date" aria-label="End date">
          </div>
          <div id="ruler" class="ruler" aria-hidden="true"></div>
          <div class="ruler-labels" aria-hidden="true"><span id="rl-a"></span><span id="rl-b"></span></div>
          <p id="ruler-note" class="hint"></p>
        </div>
      </div>

      <div class="row">
        <label for="token">Jira token</label>
        <div class="field">
          <input id="token" type="password" placeholder="Paste your token here" autocomplete="new-password" spellcheck="false">
          <p class="hint token-head"><span>The token is not saved; it is only used to fetch this report.</span>
            <button type="button" id="help-open" class="link">How do I create one?</button></p>
        </div>
      </div>

      <div class="row">
        <span class="lbl" id="fmt-l">File format</span>
        <div class="field">
          <div class="seg" role="radiogroup" aria-labelledby="fmt-l">
            <label><input type="radio" name="fmt" value="xlsx"><span>Excel</span></label>
            <label><input type="radio" name="fmt" value="csv"><span>CSV</span></label>
          </div>
        </div>
      </div>

      <div class="row">
        <span class="lbl">Jira address</span>
        <div class="field">
          <details id="url-box">
            <summary><span id="url-view"></span> <u>change</u></summary>
            <input id="url" type="text" spellcheck="false" autocomplete="off" placeholder="https://jira.yourcompany.com" aria-label="Jira address">
          </details>
        </div>
      </div>
    </fieldset>

    <div class="actions">
      <button type="submit" id="go" class="primary">Create report</button>
      <button type="button" id="cancel" class="ghost" hidden>Cancel</button>
    </div>
  </form>

  <div id="note" class="note" aria-live="polite"></div>

  <section id="result" class="result" hidden>
    <p id="result-text"></p>
    <a id="dl" class="primary" href="#" download>Download Excel</a>
    <span class="small">The file is saved to your browser's downloads folder. Times are in Turkey time (UTC+3).</span>
  </section>
</main>

<section id="preview" class="preview" aria-labelledby="pv-h" hidden>
  <div class="pv-head">
    <h2 id="pv-h">Preview</h2>
    <div class="seg" role="radiogroup" aria-label="View">
      <label><input type="radio" name="view" value="rows" checked><span>Worklogs</span></label>
      <label><input type="radio" name="view" value="people"><span>By person</span></label>
    </div>
    <input id="pv-q" type="search" placeholder="Search name, issue, text or 03.09" aria-label="Search the table" spellcheck="false" autocomplete="off">
  </div>
  <div id="pv-chips" class="chips"></div>
  <div class="pv-scroll"><table id="pv-t" class="pv"></table></div>
  <div class="pv-foot">
    <span id="pv-count" aria-live="polite"></span>
    <button type="button" id="pv-more" class="ghost" hidden></button>
  </div>
</section>

<div class="foot">
  <footer>
    <p>This app only reads from Jira; it never changes or deletes anything. Data is processed only on this computer.
      Closing this tab also closes the app.</p>
  </footer>
</div>

<dialog id="help">
  <h2>How to create a token</h2>
  <p>A token is a temporary password that signs in to Jira on your behalf. Create your own and never share it.</p>
  <ol>
    <li>Open your Jira profile page with the button below (sign in if needed).</li>
    <li>Open <b>Personal Access Tokens</b> in the left-hand menu.</li>
    <li>Click <b>Create token</b>, name it «worklog report» and create it.</li>
    <li>Copy the long text that appears (it is shown only once) and paste it into the token box on this page.</li>
  </ol>
  <p class="hint">Menu names may differ slightly between Jira versions. You can delete the token in Jira when you are done.</p>
  <div class="actions">
    <a id="profile-link" class="primary" href="#" target="_blank" rel="noopener noreferrer">Open Jira profile page</a>
    <button type="button" id="help-close" class="ghost">Close</button>
  </div>
</dialog>

<script nonce="__NONCE__">
(() => {
  "use strict";
  const KEY = "__APP_KEY__";
  const BOOT = __BOOT__;
  const $ = (id) => document.getElementById(id);
  const nf = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });
  const dayFmt = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" });
  const dayFull = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", weekday: "short" });
  const plural = (n, one, many) => nf.format(n) + " " + (n === 1 ? one : many || one + "s");
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
    if (!b) { $("rl-a").textContent = ""; $("rl-b").textContent = ""; $("ruler-note").textContent = "Check the start and end dates."; return null; }
    b.items.forEach((it) => {
      const n = document.createElement("i");
      if (it.weekend) n.className = "weekend";
      n.style.setProperty("--h", it.weekend ? ".16" : ".34");
      el.ruler.appendChild(n);
      cells.push({ node: n, keys: it.keys, from: it.from, to: it.to, weekend: it.weekend });
    });
    $("rl-a").textContent = dayFmt.format(b.items[0].from);
    $("rl-b").textContent = dayFmt.format(b.items[b.items.length - 1].to);
    $("ruler-note").textContent = plural(b.count, "day") + ", " + plural(b.weekdays, "working day") + (b.weekly ? " (weekly view)" : "");
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
      c.node.title = when + ": " + (v > 0 ? plural(v, "hour") : "no worklogs");
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

  // ---------- Önizleme tablosu ----------
  const PAGE_ROWS = 200;
  const hf = new Intl.NumberFormat("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const weekday = new Intl.DateTimeFormat("en-GB", { weekday: "short" });
  // İsimler Türkçe: sıralama ve aramada Türkçe kurallar (İ/ı, Ç, Ş) kullanılır
  const collator = new Intl.Collator("tr", { sensitivity: "base", numeric: true });
  const fold = (t) => String(t || "").toLocaleLowerCase("tr");
  const trDate = (s) => s ? s.slice(8, 10) + "." + s.slice(5, 7) + "." + s.slice(0, 4) : "";
  const pv = { rows: [], view: "rows", q: "", person: null, limit: PAGE_ROWS, multiProject: false,
               sort: { rows: ["user", 1], people: ["hours", -1] } };

  const COLS = {
    rows: [
      { k: "user", t: "User", c: "who" },
      { k: "date", t: "Date", c: "nw", by: (r) => r.date + " " + r.time },
      { k: "time", t: "Start", c: "nw" },
      { k: "key", t: "Issue", c: "nw" },
      { k: "summary", t: "Summary", c: "sum" },
      { k: "project", t: "Project", c: "nw", multi: true },
      { k: "type", t: "Type", c: "nw" },
      { k: "hours", t: "Hours", c: "num", num: true },
      { k: "comment", t: "Comment", c: "cmt" },
      { k: "created", t: "Logged at" },
    ],
    people: [
      { k: "user", t: "User", c: "nw" },
      { k: "count", t: "Worklogs", c: "num", num: true },
      { k: "days", t: "Days", c: "num", num: true },
      { k: "tasks", t: "Issues", c: "num", num: true },
      { k: "hours", t: "Total hours", c: "num", num: true },
      { k: "share", t: "Share", c: "bar", fixed: true },
    ],
  };

  const node = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };

  function visibleRows() {
    const q = fold(pv.q.trim());
    return pv.rows.filter((r) => (!pv.person || r.user === pv.person) && (!q || r._hay.includes(q)));
  }

  function peopleOf(rows) {
    const m = new Map();
    rows.forEach((r) => {
      let p = m.get(r.user);
      if (!p) m.set(r.user, p = { user: r.user, count: 0, hours: 0, d: new Set(), t: new Set() });
      p.count++; p.hours += r.hours; p.d.add(r.date); p.t.add(r.key);
    });
    return [...m.values()].map((p) => ({ user: p.user, count: p.count, hours: Math.round(p.hours * 100) / 100,
                                         days: p.d.size, tasks: p.t.size }));
  }

  function setPerson(user) {
    pv.person = user; pv.limit = PAGE_ROWS;
    const chips = $("pv-chips");
    chips.textContent = "";
    if (user) {
      const chip = node("span", "chip", "Person: " + user);
      const x = node("button", "", "×");
      x.type = "button"; x.setAttribute("aria-label", "Remove person filter");
      x.addEventListener("click", () => { setPerson(null); drawTable(); });
      chip.appendChild(x); chips.appendChild(chip);
    }
  }

  function headRow(cols, sortKey, dir) {
    const tr = node("tr");
    cols.forEach((col) => {
      const th = node("th", col.num ? "num" : "");
      th.scope = "col";
      if (col.fixed) { th.appendChild(node("span", "", col.t)); tr.appendChild(th); return; }
      th.setAttribute("aria-sort", col.k === sortKey ? (dir > 0 ? "ascending" : "descending") : "none");
      const b = node("button", "", col.t);
      b.type = "button";
      b.addEventListener("click", () => {
        const [k, d] = pv.sort[pv.view];
        pv.sort[pv.view] = [col.k, k === col.k ? -d : (col.num ? -1 : 1)];
        pv.limit = PAGE_ROWS;
        drawTable();
      });
      th.appendChild(b); tr.appendChild(th);
    });
    return tr;
  }

  function recordRow(r, cols) {
    const tr = node("tr");
    cols.forEach((col) => {
      const td = node("td", col.c);
      if (col.k === "date") {
        td.append(trDate(r.date) + " ", node("span", "dim", weekday.format(new Date(r.date + "T00:00:00"))));
      } else if (col.k === "key") {
        const a = node("a", "", r.key);
        a.href = r.url; a.target = "_blank"; a.rel = "noopener noreferrer";
        td.appendChild(a);
      } else if (col.k === "hours") {
        td.textContent = hf.format(r.hours);
      } else if (col.k === "summary" || col.k === "comment") {
        const d = node("div", "clip", r[col.k]);
        if (r[col.k]) d.title = r[col.k];
        td.appendChild(d);
      } else if (col.k === "created") {
        td.textContent = r.created ? trDate(r.created) + " " + r.created.slice(11) : "";
      } else {
        td.textContent = r[col.k];
      }
      tr.appendChild(td);
    });
    return tr;
  }

  function personRow(p, cols, maxHours, totalHours) {
    const tr = node("tr");
    cols.forEach((col) => {
      const td = node("td", col.c);
      if (col.k === "user") {
        const b = node("button", "link", p.user);
        b.type = "button"; b.title = "Show worklogs of " + p.user;
        b.addEventListener("click", () => { setPerson(p.user); pv.view = "rows"; setRadio("view", "rows"); drawTable(); });
        td.appendChild(b);
      } else if (col.k === "hours") {
        td.textContent = hf.format(p.hours);
      } else if (col.k === "share") {
        const i = node("i");
        i.style.setProperty("--w", maxHours > 0 ? (p.hours / maxHours).toFixed(4) : "0");
        td.title = totalHours > 0 ? "%" + nf.format(p.hours / totalHours * 100) : "";
        td.appendChild(i);
      } else {
        td.textContent = nf.format(p[col.k]);
      }
      tr.appendChild(td);
    });
    return tr;
  }

  function drawTable() {
    const cols = COLS[pv.view].filter((c) => !c.multi || pv.multiProject);
    const base = visibleRows();
    const data = pv.view === "rows" ? base.slice() : peopleOf(base);
    const [sortKey, dir] = pv.sort[pv.view];
    const col = cols.find((c) => c.k === sortKey) || cols[0];
    const val = col.by || ((r) => r[col.k]);
    data.sort((a, b) => {
      const x = val(a), y = val(b);
      return (typeof x === "number" ? x - y : collator.compare(x, y)) * dir;
    });

    const totalHours = base.reduce((a, r) => a + r.hours, 0);
    const table = $("pv-t");
    const thead = node("thead"), tbody = node("tbody"), tfoot = node("tfoot");
    thead.appendChild(headRow(cols, col.k, dir));

    const shown = pv.view === "rows" ? data.slice(0, pv.limit) : data;
    if (!shown.length) {
      const tr = node("tr", "pv-empty"), td = node("td", "", "No worklogs match your search.");
      td.colSpan = cols.length; tr.appendChild(td); tbody.appendChild(tr);
    } else if (pv.view === "rows") {
      shown.forEach((r) => tbody.appendChild(recordRow(r, cols)));
    } else {
      const maxHours = data.reduce((a, p) => Math.max(a, p.hours), 0);
      shown.forEach((p) => tbody.appendChild(personRow(p, cols, maxHours, totalHours)));
    }

    const ft = node("tr");
    cols.forEach((c, i) => {
      let text = "";
      if (i === 0) text = "Total: " + (pv.view === "rows" ? plural(base.length, "worklog") : plural(data.length, "person", "people"));
      else if (c.k === "hours") text = hf.format(totalHours);
      else if (c.k === "count") text = nf.format(base.length);
      else if (c.k === "days") text = nf.format(new Set(base.map((r) => r.date)).size);
      else if (c.k === "tasks") text = nf.format(new Set(base.map((r) => r.key)).size);
      ft.appendChild(node("td", c.c, text));
    });
    tfoot.appendChild(ft);
    table.replaceChildren(thead, tbody, tfoot);

    const more = $("pv-more");
    const rest = pv.view === "rows" ? data.length - shown.length : 0;
    more.hidden = rest <= 0;
    more.textContent = "Show " + plural(Math.min(rest, PAGE_ROWS), "more row");
    $("pv-count").textContent = pv.view === "rows"
      ? (rest > 0 ? "Showing " + nf.format(shown.length) + " of " + plural(data.length, "worklog") : plural(data.length, "worklog"))
        + (data.length !== pv.rows.length ? " (filtered from " + nf.format(pv.rows.length) + ")" : "")
      : "Click a person to see their worklogs.";
  }

  async function loadPreview() {
    let r;
    try { r = await api("/api/rows"); } catch (_) { return; }
    if (!r.ok || !r.data || !Array.isArray(r.data.rows)) return;
    pv.rows = r.data.rows.map((x) => Object.assign(x, {
      _hay: fold([x.user, x.key, x.summary, x.comment, x.type, x.project, trDate(x.date)].join(" ")) }));
    pv.multiProject = new Set(pv.rows.map((x) => x.project)).size > 1;
    pv.q = ""; $("pv-q").value = "";
    setPerson(null);
    $("preview").hidden = false;
    drawTable();
  }

  function hidePreview() {
    $("preview").hidden = true;
    pv.rows = [];
    $("pv-t").textContent = "";
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
      if (!$("preview").hidden) hidePreview();
      if (!cells.length || el.start.value !== st.start || el.end.value !== st.end) drawRuler(st.start, st.end);
      if (st.stage === "search" || !st.total) {
        setNote("Searching for issues with worklogs in this period…", "msg-info");
        fillRuler(0);
      } else {
        setNote(nf.format(st.done) + " / " + plural(st.total, "issue") + " processed…", "msg-info");
        fillRuler(st.done / st.total);
      }
    } else if (st.state === "done") {
      drawRuler(st.start, st.end);
      showHours(st.daily || {});
      setNote("", "");
      $("result-text").textContent = "";
      const t = $("result-text");
      t.append("Report ready: " + plural(st.people, "person", "people") + ", " + plural(st.count, "worklog") + ", ");
      const num = document.createElement("span"); num.className = "num"; num.textContent = plural(st.hours, "hour");
      t.append(num, " in total.");
      const a = $("dl");
      a.href = "/download?k=" + encodeURIComponent(KEY);
      a.textContent = (st.filename || "").endsWith(".csv") ? "Download CSV" : "Download Excel";
      el.result.hidden = false;
      loadPreview();
    } else if (st.state === "error") {
      el.result.hidden = true; drawFromForm();
      setNote(st.message, "msg-err");
    } else if (st.state === "empty") {
      el.result.hidden = true; drawFromForm();
      setNote("No worklogs found for the selected project in this period. Check the project key and the dates.", "msg-err");
    } else if (st.state === "cancelled") {
      el.result.hidden = true; drawFromForm();
      setNote("Cancelled.", "msg-info");
    }
  }

  function lost() {
    clearInterval(timer);
    $("fs").disabled = true; $("go").hidden = true; $("cancel").hidden = true;
    setNote("Lost connection to the app. Reopen Jira Worklog; you can close this tab.", "msg-err");
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
  el.url.addEventListener("input", () => { $("url-view").textContent = hostLabel() || "Enter the Jira address"; });

  document.querySelectorAll('input[name="view"]').forEach((r) => r.addEventListener("change", () => {
    pv.view = radio("view"); pv.limit = PAGE_ROWS; drawTable();
  }));
  let searchTimer = null;
  $("pv-q").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { pv.q = $("pv-q").value; pv.limit = PAGE_ROWS; drawTable(); }, 120);
  });
  $("pv-more").addEventListener("click", () => { pv.limit += PAGE_ROWS; drawTable(); });

  $("f").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    setNote("", "");
    const body = { url: el.url.value, project: el.project.value, preset: radio("preset"),
                   start: el.start.value, end: el.end.value, token: el.token.value, format: radio("fmt") };
    let r;
    try { r = await api("/api/start", { method: "POST", body: JSON.stringify(body) }); }
    catch (_) { return lost(); }
    if (!r.ok) { setNote((r.data && r.data.error) || "The request failed.", "msg-err"); return; }
    lastRev = -1;
    el.result.hidden = true;
    hidePreview();
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

  window.addEventListener("pagehide", () => { navigator.sendBeacon("/api/bye?k=" + encodeURIComponent(KEY)); });

  // ---------- Başlangıç ----------
  el.project.value = BOOT.project;
  el.url.value = BOOT.url;
  $("url-view").textContent = hostLabel() || "Enter the Jira address";
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
