PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Trading Agents</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--text:#16181d;--muted:#5d6472;--border:#e2e5ea;--accent:#2f5bea;
--long:#12805c;--short:#c4352b;--none:#6b7280;--warn-bg:#fff6e5;--warn:#8a5a00;--chip:#eef1f6}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#181b21;--text:#e8eaee;--muted:#9aa2b1;
--border:#2a2f38;--accent:#7b9bff;--long:#3ccf95;--short:#ff6b5e;--none:#9aa2b1;--warn-bg:#2a2210;--warn:#f2c26b;--chip:#222731}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:24px;margin:0 0 2px}h2{font-size:17px;margin:0 0 8px}h3{font-size:15px;margin:12px 0 4px}
.sub{color:var(--muted);margin:0 0 14px}
.tabs{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.tabs button{background:transparent;color:var(--text);border:1px solid var(--border)}
.tabs button.on{background:var(--accent);border-color:var(--accent);color:#fff}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:end}
label{display:flex;flex-direction:column;font-size:12px;color:var(--muted);gap:4px}
input,select,textarea{font:inherit;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text)}
input{width:130px}textarea{width:100%;min-height:60px}
button{font:inherit;padding:9px 16px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.secondary{background:transparent;color:var(--accent)}
button:disabled{opacity:.5;cursor:wait}
.check{flex-direction:row;align-items:center;gap:6px;padding-bottom:9px}.check input{width:auto}
.hidden{display:none!important}
#tv{height:460px;border-radius:12px;overflow:hidden;border:1px solid var(--border);margin-bottom:14px;background:var(--card)}
.live{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.kv{background:var(--bg);border-radius:8px;padding:8px 10px;min-width:0}
.kv b{display:block;font-size:12px;color:var(--muted);font-weight:500}
.kv span{font-variant-numeric:tabular-nums;font-size:16px;overflow-wrap:anywhere}
.ticks{display:flex;gap:2px;margin-top:10px;height:18px}.ticks i{flex:1;border-radius:2px;background:var(--border)}
.action{font-size:30px;font-weight:700;letter-spacing:.5px}
.LONG,.UP,.AGREE{color:var(--long)}.SHORT,.DOWN,.CONFLICT{color:var(--short)}.NO,.WAIT,.SIDEWAYS,.UNCLEAR,.PARTIAL{color:var(--none)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px}
ul{margin:6px 0 0;padding-left:18px}li{margin:2px 0}
.agent-head{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.pill{font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.BULLISH{color:var(--long)}.BEARISH{color:var(--short)}.NEUTRAL{color:var(--none)}
.bar{height:6px;background:var(--border);border-radius:3px;margin:8px 0;position:relative;overflow:hidden}
.bar span{position:absolute;top:0;bottom:0}
.meter{height:10px;border-radius:5px;background:var(--short);overflow:hidden;margin:6px 0}
.meter span{display:block;height:100%;background:var(--long)}
.warn{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:10px 12px;margin-top:12px}
.muted,.disclaimer{font-size:13px;color:var(--muted)}
.err{color:var(--short)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--border);white-space:nowrap}
th:nth-child(-n+3),td:nth-child(-n+3){text-align:left}
.scroll{overflow-x:auto}
.drop{border:2px dashed var(--border);border-radius:12px;padding:24px;text-align:center;color:var(--muted);cursor:pointer}
.drop.over{border-color:var(--accent)}
.drop img{max-width:100%;max-height:360px;border-radius:8px}
.md p{margin:6px 0}.md ul{margin:4px 0}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--none);margin-right:6px}
.dot.on{background:var(--long)}
.next{border-width:2px}.next.LONGb{border-color:var(--long)}.next.SHORTb{border-color:var(--short)}
.big{font-size:44px;font-weight:800;letter-spacing:.5px;line-height:1.1}
.prob{display:flex;justify-content:space-between;font-weight:700;font-size:18px;margin-top:8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.chip{background:var(--chip);border-radius:999px;padding:2px 10px;font-size:13px}
.dots{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}.dots i{width:12px;height:12px;border-radius:50%;display:inline-block}
</style>
</head>
<body>
<main>
<h1>Crypto Trading Agents</h1>
<p class="sub">Five analyst agents, a risk manager and a chief strategist working on live Binance data, with optional Claude AI for screenshots and a senior-trader review.</p>

<div class="tabs" role="tablist">
  <button class="on" data-tab="live">Live trading</button>
  <button data-tab="scan">Scanner</button>
  <button data-tab="shot">Screenshot AI</button>
</div>

<!-- ============================== LIVE ============================== -->
<section id="tab-live">
<div class="card"><form id="f" class="row">
  <label>Symbol<input id="symbol" value="BTCUSDT" autocomplete="off"></label>
  <label>Timeframe<select id="tf"></select></label>
  <label>Account (USDT)<input id="account" type="number" value="1000" min="1" step="any"></label>
  <label>Risk / trade %<input id="risk" type="number" value="1" min="0.05" max="10" step="any"></label>
  <label>Re-run agents<select id="auto">
    <option value="0">Manual</option><option value="close" selected>Every candle close</option>
    <option value="5">Every 5 s</option><option value="10">Every 10 s</option>
    <option value="30">Every 30 s</option><option value="60">Every 60 s</option></select></label>
  <label class="check"><input id="demo" type="checkbox">Demo data</label>
  <button id="go" type="submit">Analyze</button>
  <button id="aibtn" type="button" class="secondary hidden">AI senior trader review</button>
</form></div>

<div id="next"></div>
<div id="tv"></div>

<div class="card">
  <div class="agent-head"><h2><span id="wsdot" class="dot"></span>Live order flow, updated every second</h2>
  <span id="pressure" class="pill NEUTRAL">connecting…</span></div>
  <div class="live">
    <div class="kv"><b>Price</b><span id="lv-price">–</span></div>
    <div class="kv"><b>Current candle</b><span id="lv-candle">–</span></div>
    <div class="kv"><b>Candle closes in</b><span id="lv-close">–</span></div>
    <div class="kv"><b>Taker buys (10 s)</b><span id="lv-b10">–</span></div>
    <div class="kv"><b>Taker buys (60 s)</b><span id="lv-b60">–</span></div>
    <div class="kv"><b>Order-book imbalance</b><span id="lv-book">–</span></div>
  </div>
  <div class="ticks" id="ticks" title="Last 60 seconds of pressure: green = buyers, red = sellers"></div>
  <p class="muted">Second-by-second pressure is noisy and is not a trade signal by itself. The agents combine it with trend, momentum and structure.</p>
</div>

<div id="out"></div>
</section>

<!-- ============================== SCANNER ============================== -->
<section id="tab-scan" class="hidden">
<div class="card"><div class="row">
  <label>Timeframe<select id="s-tf"></select></label>
  <label>Coins<select id="s-top"><option>10</option><option selected>20</option><option>30</option><option>40</option></select></label>
  <label style="flex:1;min-width:200px">Or your own list (comma separated)<input id="s-list" style="width:100%" placeholder="BTCUSDT, ETHUSDT, PEPEUSDT"></label>
  <button id="s-go" type="button">Scan market</button>
</div><p class="muted">Ranks the most traded USDT pairs on Binance by 24h volume and shows the best setups first.</p></div>
<div id="s-out"></div>
</section>

<!-- ============================== SCREENSHOT ============================== -->
<section id="tab-shot" class="hidden">
<div id="noai" class="card warn hidden">Screenshot analysis uses Claude AI. Add an <code>ANTHROPIC_API_KEY</code> environment variable in Vercel (Project → Settings → Environment Variables) and redeploy.</div>
<div class="card">
  <div id="drop" class="drop" tabindex="0">Drop a chart screenshot here, click to choose a file, or paste with Ctrl/Cmd+V</div>
  <input id="file" type="file" accept="image/*" class="hidden">
  <div class="row" style="margin-top:12px">
    <label>Symbol (optional)<input id="x-symbol" placeholder="auto-detect"></label>
    <label>Chart timeframe<select id="x-tf"><option value="">auto-detect</option></select></label>
    <label>Predict for the next<input id="x-horizon" value="1 hour"></label>
  </div>
  <label style="margin-top:10px">Note for the AI (optional)<textarea id="x-note" placeholder="e.g. I'm thinking of a long here, what do you see?"></textarea></label>
  <div style="margin-top:10px"><button id="x-go" type="button" disabled>Analyze screenshot</button></div>
</div>
<div id="x-out"></div>
</section>

<p class="disclaimer">Not financial advice. No signal is 100% accurate, and every trade can lose. The win and loss odds shown are measured on recent history and can change at any time. Always use a stop-loss and only risk money you can afford to lose.</p>
</main>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = x => x == null ? "–" : (Math.abs(x) >= 1 ? x.toLocaleString(undefined,{maximumFractionDigits:2}) : Number(x).toPrecision(5));
const pct = x => x == null ? "–" : (x*100).toFixed(0) + "%";
const TFS = ["1m","5m","15m","1h","4h","1d"];
const TV_INTERVAL = {"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"};
const TF_SEC = {"1m":60,"5m":300,"15m":900,"1h":3600,"4h":14400,"1d":86400};
let CONFIG = {ai:false};

for (const sel of ["tf","s-tf","x-tf"]) for (const t of TFS) {
  const def = sel === "tf" ? "1m" : "5m";
  $(sel).add(sel === "x-tf" ? new Option(t,t) : new Option(t,t,t===def,t===def));
}
try { const saved = JSON.parse(localStorage.getItem("cta") || "{}");
  for (const k of ["symbol","tf","account","risk"]) if (saved[k]) $(k).value = saved[k]; } catch(e) {}

// ---------------------------------------------------------------- tabs
document.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {
  document.querySelectorAll(".tabs button").forEach(x => x.classList.toggle("on", x === b));
  for (const t of ["live","scan","shot"]) $("tab-"+t).classList.toggle("hidden", t !== b.dataset.tab);
});

async function getJSON(url, opts){
  const r = await fetch(url, opts); let j;
  try { j = await r.json(); } catch(e) { throw new Error(`Server error ${r.status}`); }
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
const params = extra => new URLSearchParams({account:$("account").value, risk:$("risk").value,
  demo:$("demo").checked ? "1" : "0", ...extra});

fetch("/api/config").then(r => r.json()).then(c => { CONFIG = c;
  $("aibtn").classList.toggle("hidden", !c.ai); $("noai").classList.toggle("hidden", c.ai); }).catch(() => {});

// ---------------------------------------------------------------- TradingView chart
function loadChart(sym, tf){
  const dark = matchMedia("(prefers-color-scheme: dark)").matches;
  $("tv").innerHTML = '<div class="tradingview-widget-container" style="height:100%"><div class="tradingview-widget-container__widget" style="height:100%"></div></div>';
  const s = document.createElement("script");
  s.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"; s.async = true;
  s.innerHTML = JSON.stringify({autosize:true, symbol:"BINANCE:"+sym, interval:TV_INTERVAL[tf], timezone:"Etc/UTC",
    theme: dark ? "dark" : "light", style:"1", locale:"en", allow_symbol_change:false,
    studies:["STD;RSI","STD;MACD"], support_host:"https://www.tradingview.com"});
  $("tv").firstChild.appendChild(s);
}

// ---------------------------------------------------------------- live websocket (every second)
const WS_HOSTS = ["wss://stream.binance.com:9443", "wss://data-stream.binance.vision"];
let ws = null, wsKey = "", hostIdx = 0, trades = [], book = null, kline = null, history = [], retry = 0;

function connect(sym, tf){
  const key = sym + tf; if (ws && wsKey === key) return;
  if (ws) { ws.onclose = null; ws.close(); }
  wsKey = key; trades = []; book = null; kline = null; history = [];
  const s = sym.toLowerCase();
  ws = new WebSocket(`${WS_HOSTS[hostIdx]}/stream?streams=${s}@kline_${tf}/${s}@aggTrade/${s}@depth20`);
  ws.onopen = () => { retry = 0; $("wsdot").classList.add("on"); };
  ws.onmessage = e => {
    const {stream, data} = JSON.parse(e.data);
    if (stream.includes("@aggTrade")) trades.push({t:data.T, v:+data.p * +data.q, sell:data.m, p:+data.p});
    else if (stream.includes("@depth")) book = data;
    else if (stream.includes("@kline")) {
      const closedNow = data.k.x && kline && !kline.x; kline = data.k;
      if (closedNow) { gradeForecast(sym, tf, data.k); if ($("auto").value === "close") setTimeout(() => runAnalysis(true), 800); }
    }
  };
  ws.onclose = () => { $("wsdot").classList.remove("on");
    hostIdx = (hostIdx + 1) % WS_HOSTS.length; wsKey = "";
    setTimeout(() => { if (!wsKey) connect(sym, tf); }, Math.min(1000 * 2 ** retry++, 15000)); };
}

setInterval(() => {
  const now = Date.now(); trades = trades.filter(t => now - t.t < 60000);
  const sum = (ms, sell) => trades.filter(t => now - t.t < ms && t.sell === sell).reduce((a, t) => a + t.v, 0);
  const b10 = sum(10000,false), s10 = sum(10000,true), b60 = sum(60000,false), s60 = sum(60000,true);
  let imb = 0;
  if (book) { const side = a => a.reduce((s, [p, q]) => s + p * q, 0); const b = side(book.bids), a = side(book.asks); imb = (b - a) / ((b + a) || 1); }
  const flow10 = (b10 + s10) ? (b10 - s10) / (b10 + s10) : 0;
  const score = 0.6 * flow10 + 0.4 * imb;
  if (trades.length) {
    $("lv-price").textContent = num(trades[trades.length - 1].p);
    $("lv-b10").textContent = (b10 + s10) ? pct(b10 / (b10 + s10)) : "–";
    $("lv-b60").textContent = (b60 + s60) ? pct(b60 / (b60 + s60)) : "–";
  }
  if (book) $("lv-book").textContent = (imb >= 0 ? "+" : "") + (imb * 100).toFixed(0) + "% " + (imb > 0 ? "bids" : "asks");
  if (kline) {
    const ch = (+kline.c - +kline.o) / +kline.o * 100;
    $("lv-candle").innerHTML = `<span class="${ch >= 0 ? "UP" : "DOWN"}">${ch >= 0 ? "+" : ""}${ch.toFixed(2)}%</span>`;
    const left = Math.max(0, Math.round((kline.T - now) / 1000));
    $("lv-close").textContent = left >= 3600 ? `${Math.floor(left/3600)}h ${Math.floor(left%3600/60)}m` : `${Math.floor(left/60)}:${String(left%60).padStart(2,"0")}`;
  }
  if (ws && ws.readyState === 1) {
    const label = score > 0.25 ? ["BUY PRESSURE","BULLISH"] : score < -0.25 ? ["SELL PRESSURE","BEARISH"] : ["BALANCED","NEUTRAL"];
    $("pressure").className = "pill " + label[1]; $("pressure").textContent = `${label[0]} ${score >= 0 ? "+" : ""}${score.toFixed(2)}`;
    history.push(score); history = history.slice(-60);
    $("ticks").innerHTML = history.map(v => `<i style="background:${v > 0.1 ? "var(--long)" : v < -0.1 ? "var(--short)" : "var(--border)"};opacity:${0.35 + Math.min(Math.abs(v), 1) * 0.65}"></i>`).join("");
  }
  if (lastForecast && $("nx-left") && $("demo").checked) $("nx-left").textContent = "demo data";
  else if (lastForecast && $("nx-left")) {
    const left = Math.round(lastForecast.target_candle_close - now / 1000);
    $("nx-left").textContent = left > 0 ? `closes in ${left >= 3600 ? Math.floor(left/3600) + "h " + Math.floor(left%3600/60) + "m" : Math.floor(left/60) + ":" + String(left%60).padStart(2,"0")}` : "candle closed, updating…";
  }
}, 1000);

// ---------------------------------------------------------------- next-candle forecast + live track record
let lastForecast = null;
const sbKey = (sym, tf) => `cta-sb-${sym}-${tf}`;
const loadSB = (sym, tf) => { try { return JSON.parse(localStorage.getItem(sbKey(sym, tf)) || "[]"); } catch(e) { return []; } };
const saveSB = (sym, tf, rows) => { try { localStorage.setItem(sbKey(sym, tf), JSON.stringify(rows.slice(-50))); } catch(e) {} };

function recordForecast(f){
  if (f.action === "NO TRADE" || $("demo").checked) return;
  const rows = loadSB(f.symbol, f.timeframe), open = Math.round(f.target_candle_open * 1000);
  if (rows.some(r => r.open === open)) return;
  rows.push({open, call:f.action, p:f.action === "LONG" ? f.probability_up : f.probability_down, late:f.seconds_elapsed > 0.3 * (f.target_candle_close - f.target_candle_open)});
  saveSB(f.symbol, f.timeframe, rows);
}

function gradeForecast(sym, tf, k){
  const rows = loadSB(sym, tf), r = rows.find(x => x.open === k.t && x.result == null);
  if (!r) return;
  r.result = +k.c > +k.o ? "UP" : +k.c < +k.o ? "DOWN" : "FLAT";
  r.correct = (r.call === "LONG" && r.result === "UP") || (r.call === "SHORT" && r.result === "DOWN");
  saveSB(sym, tf, rows);
  if (lastForecast && lastForecast.symbol === sym && lastForecast.timeframe === tf) $("nx-sb").innerHTML = scoreboard(sym, tf);
}

function scoreboard(sym, tf){
  const graded = loadSB(sym, tf).filter(r => r.result);
  if (!graded.length) return '<span class="muted">No graded calls yet. Each LONG/SHORT call is checked automatically when its candle closes, while this page is open.</span>';
  const ok = graded.filter(r => r.correct).length;
  return `<b>${ok} of ${graded.length} correct (${Math.round(ok / graded.length * 100)}%)</b> <span class="muted">· ${esc(sym)} ${esc(tf)}, this browser</span>
    <div class="dots">${graded.slice(-30).map(r => `<i title="${new Date(r.open).toLocaleTimeString()} ${r.call} → ${r.result}" style="background:${r.correct ? "var(--long)" : "var(--short)"}"></i>`).join("")}</div>`;
}

function renderForecast(f){
  lastForecast = f.error ? null : f;
  if (f.error) { $("next").innerHTML = `<div class="card warn">${esc(f.error)}</div>`; return; }
  recordForecast(f);
  const t = f.model_test, hhmm = s => new Date(s * 1000).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  const cls = f.action === "NO TRADE" ? "NO" : f.action;
  const acc = t.calls ? `${pct(t.call_accuracy)} right on ${t.calls} calls <span class="muted">(95% range ${pct(t.call_accuracy_95ci[0])}–${pct(t.call_accuracy_95ci[1])}; always guessing the usual direction scores ${pct(t.majority_baseline)})</span>` : "not enough calls to test";
  $("next").innerHTML = `<div class="card next ${cls}b" id="next-card">
    <div class="agent-head"><h2>Next ${esc(f.timeframe)} candle · ${esc(f.symbol)} · ${hhmm(f.target_candle_open)}–${hhmm(f.target_candle_close)}</h2>
      <span class="pill NEUTRAL" id="nx-left"></span></div>
    <div class="big ${cls}">${esc(f.action)}</div>
    <div class="prob"><span class="UP">UP ${pct(f.probability_up)}</span><span class="DOWN">DOWN ${pct(f.probability_down)}</span></div>
    <div class="meter"><span style="width:${(f.probability_up * 100).toFixed(1)}%"></span></div>
    <div class="grid">
      <div class="kv"><b>Model check on recent candles it never saw</b><span>${acc}</span></div>
      <div class="kv"><b>Proven edge right now?</b><span class="${f.has_edge ? "UP" : "DOWN"}">${f.has_edge ? "YES" : "NO"}</span></div>
      <div class="kv"><b>Typical ${esc(f.timeframe)} move vs fees</b><span>${f.typical_move_pct.toFixed(3)}% vs ${f.fees_round_trip_pct.toFixed(2)}%</span></div>
    </div>
    ${f.reasons.length ? `<ul>${f.reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
    ${f.vetoes.length ? `<div class="warn"><b>Why no trade</b><ul>${f.vetoes.map(v => `<li>${esc(v)}</li>`).join("")}</ul></div>` : ""}
    <h3>What is driving the forecast</h3>
    <div class="chips">${f.drivers.map(d => `<span class="chip"><span class="${d.push}">${d.push === "UP" ? "▲" : "▼"}</span> ${esc(d.feature)}</span>`).join("")}</div>
    ${f.plan ? `<div class="grid"><div class="kv"><b>Entry</b><span>${num(f.plan.entry)}</span></div>
      <div class="kv"><b>Stop-loss (1 ATR)</b><span>${num(f.plan.stop_loss)}</span></div>
      <div class="kv"><b>Target (1 ATR)</b><span>${num(f.plan.take_profit)}</span></div></div>
      <p class="muted">Exit: ${esc(f.plan.exit)}.</p>` : ""}
    <h3>Live track record</h3><div id="nx-sb">${scoreboard(f.symbol, f.timeframe)}</div>
    <p class="muted">${esc(f.note)} Trained on ${f.trained_on} candles. All agents' votes are below.</p></div>`;
}

// ---------------------------------------------------------------- analysis
let busy = false, autoTimer = null, lastOddsKey = "", lastOddsAt = 0, lastDecision = null;

function bar(score){
  const w = Math.abs(score) * 50, left = score >= 0 ? 50 : 50 - w;
  const color = score > 0.15 ? "var(--long)" : score < -0.15 ? "var(--short)" : "var(--none)";
  return `<div class="bar"><span style="left:${left}%;width:${w}%;background:${color}"></span></div>`;
}

function planHTML(p){
  const dist = Math.abs(p.entry - p.stop_loss) / p.entry * 100;
  return `<div class="grid">
    <div class="kv"><b>Entry</b><span>${num(p.entry)}</span></div>
    <div class="kv"><b>Stop-loss (${dist.toFixed(2)}%)</b><span>${num(p.stop_loss)}</span></div>
    ${p.take_profits.map((t,i) => `<div class="kv"><b>Take-profit ${i+1} (${[1.5,2.5,4][i]}R)</b><span>${num(t)}</span></div>`).join("")}
    <div class="kv"><b>Position size</b><span>${Number(p.position_size).toPrecision(5)}</span> <span class="muted">≈ ${num(p.position_value)} USDT</span></div>
    <div class="kv"><b>Max loss if stopped</b><span>${num(p.risk_amount)} USDT</span></div></div>
    <p class="muted">Take partial profit at TP1 and move the stop to break-even.</p>`;
}

function renderDecision(d){
  lastDecision = d;
  const cls = d.action === "NO TRADE" ? "NO" : d.action;
  const t = new Date(d.generated_at * 1000).toLocaleTimeString();
  let h = `<div class="card"><div class="agent-head"><h2>${esc(d.symbol)} · ${esc(d.timeframe)}: Chief Strategist</h2><span class="muted">updated ${t}</span></div>
    <div class="action ${cls}">${esc(d.action)}</div>
    <div class="grid"><div class="kv"><b>Price</b><span>${num(d.price)}</span></div>
    <div class="kv"><b>Combined score</b><span>${d.score >= 0 ? "+" : ""}${d.score.toFixed(2)}</span></div>
    <div class="kv"><b>Setup quality (not win %)</b><span>${d.setup_quality}/100</span></div>
    <div class="kv"><b>Signal valid for</b><span>${esc(d.horizon_text)}</span></div></div>
    <h3>Strategy: ${esc(d.strategy)}</h3><p class="muted">${esc(d.playbook)}</p>
    <ul>${d.reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul>
    ${d.plan ? planHTML(d.plan) : ""}
    ${d.warnings.length ? `<div class="warn"><b>Warnings</b><ul>${d.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}
  </div><div id="odds"></div><div id="ai"></div>`;
  for (const r of d.reports){
    const risk = r.agent === "Risk Manager";
    h += `<div class="card"><div class="agent-head"><h2>${esc(r.agent)}</h2>
      ${risk ? "" : `<span class="pill ${r.bias}">${r.bias} ${r.score >= 0 ? "+" : ""}${r.score.toFixed(2)}</span>`}</div>
      <div>${esc(r.summary)} <span class="muted">· confidence ${Math.round(r.confidence*100)}%</span></div>
      ${risk ? "" : bar(r.score)}
      <ul>${r.reasons.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
  }
  const keepOdds = $("odds-card"), keepAI = $("ai-card");
  $("out").innerHTML = h;
  if (keepOdds) $("odds").appendChild(keepOdds);
  if (keepAI) $("ai").appendChild(keepAI);
}

function renderOdds(o){
  if (o.error) return `<div class="card muted" id="odds-card">${esc(o.error)}</div>`;
  const s = o.same_direction || o.all_signals;
  const line = (x, label) => x && x.signals ? `<div class="kv"><b>${label}</b><span>${pct(x.win_rate)} won</span>
     <span class="muted"> (${x.wins} W / ${x.losses} L / ${x.timeouts} expired of ${x.signals}; 95% range ${pct(x.win_rate_95ci[0])}–${pct(x.win_rate_95ci[1])}; avg ${x.avg_r >= 0 ? "+" : ""}${x.avg_r.toFixed(2)}R)</span></div>`
     : `<div class="kv"><b>${label}</b><span>no signals</span></div>`;
  return `<div class="card" id="odds-card"><h2>Chances of winning and losing (measured, not guessed)</h2>
    <div class="grid"><div class="kv"><b>Chance price is higher in ${o.horizon_candles} × ${esc(o.timeframe)}</b>
      <span class="UP">${pct(o.chance_up)}</span> <span class="muted">up</span> / <span class="DOWN">${pct(o.chance_down)}</span> <span class="muted">down</span>
      <div class="meter"><span style="width:${(o.chance_up*100).toFixed(0)}%"></span></div>
      <span class="muted">from ${o.chance_samples} past moments with ${esc(o.chance_basis)}; normal up-rate ${pct(o.base_rate_up)}</span></div>
    ${o.same_direction ? line(o.same_direction, "Past signals in this direction") : ""}
    ${line(o.all_signals, "All past signals")}</div>
    <p class="muted">Win means ${esc(o.target)} within ${o.horizon_candles} candles. Tested on ${o.windows_tested} recent candles (${esc(o.period)}). ${esc(o.note)}</p></div>`;
}

async function loadOdds(sym, tf){
  const key = sym + tf + $("demo").checked;
  if (key === lastOddsKey && Date.now() - lastOddsAt < 300000) return;
  lastOddsKey = key; lastOddsAt = Date.now();
  if ($("odds")) $("odds").innerHTML = '<div class="card muted" id="odds-card">Measuring historical win/loss odds for this setup…</div>';
  try { const o = await getJSON("/api/odds?" + params({symbol:sym, tf}));
    if ($("odds")) $("odds").innerHTML = renderOdds(o);
  } catch(e) { lastOddsKey = ""; if ($("odds")) $("odds").innerHTML = `<div class="card err" id="odds-card">${esc(e.message)}</div>`; }
}

async function runAnalysis(silent){
  if (busy) return; busy = true;
  const sym = $("symbol").value.trim().toUpperCase(), tf = $("tf").value;
  try { localStorage.setItem("cta", JSON.stringify({symbol:sym, tf, account:$("account").value, risk:$("risk").value})); } catch(e) {}
  if (!silent) { $("go").disabled = true; if (!lastDecision || lastDecision.symbol !== sym || lastDecision.timeframe !== tf)
    { $("next").innerHTML = ""; $("out").innerHTML = '<div class="card">All agents are analyzing live market data and forecasting the next candle…</div>'; } }
  try {
    const j = await getJSON("/api/next?" + params({symbol:sym, tf})), d = j.decision;
    if (lastDecision && (lastDecision.symbol !== d.symbol || lastDecision.timeframe !== d.timeframe)) { lastOddsKey = ""; $("out").innerHTML = ""; }
    renderForecast(j.forecast);
    renderDecision(d);
    loadOdds(d.symbol, tf);
  } catch(e) { if (!silent) $("out").innerHTML = `<div class="card err">${esc(e.message)}</div>`; }
  finally { busy = false; $("go").disabled = false; }
}

function startLive(){
  const sym = $("symbol").value.trim().toUpperCase(), tf = $("tf").value;
  loadChart(sym, tf);
  if ($("demo").checked) { if (ws) { ws.onclose = null; ws.close(); ws = null; wsKey = ""; } $("pressure").textContent = "off in demo mode"; }
  else connect(sym, tf);
}

$("f").onsubmit = e => { e.preventDefault(); startLive(); runAnalysis(false); };
$("auto").onchange = () => {
  clearInterval(autoTimer); const v = $("auto").value;
  if (+v) autoTimer = setInterval(() => runAnalysis(true), +v * 1000);
};

$("aibtn").onclick = async () => {
  const sym = $("symbol").value.trim().toUpperCase(), tf = $("tf").value;
  $("aibtn").disabled = true;
  if (!$("ai")) $("out").insertAdjacentHTML("afterbegin", '<div id="ai"></div>');
  $("ai").innerHTML = '<div class="card" id="ai-card">The AI senior trader is reviewing the agents and checking the latest news (about 20–60 s)…</div>';
  try { const j = await getJSON("/api/ai-review?" + params({symbol:sym, tf}));
    $("ai").innerHTML = `<div class="card md" id="ai-card"><h2>AI Senior Trader review</h2>${md(j.review)}</div>`;
  } catch(e) { $("ai").innerHTML = `<div class="card err" id="ai-card">${esc(e.message)}</div>`; }
  finally { $("aibtn").disabled = false; }
};

// tiny, safe Markdown: escape first, then bold, links, bullets, paragraphs
function md(src){
  const lines = esc(src).split("\n"); let out = "", inList = false;
  const inline = s => s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  for (const l of lines) {
    const m = l.match(/^\s*[-*•]\s+(.*)/);
    if (m) { if (!inList) { out += "<ul>"; inList = true; } out += `<li>${inline(m[1])}</li>`; continue; }
    if (inList) { out += "</ul>"; inList = false; }
    if (l.trim()) out += `<p>${inline(l.replace(/^#+\s*/, ""))}</p>`;
  }
  return out + (inList ? "</ul>" : "");
}

// ---------------------------------------------------------------- scanner
$("s-go").onclick = async () => {
  $("s-go").disabled = true;
  $("s-out").innerHTML = '<div class="card">Scanning the market. Each coin is analyzed by all agents (about 10–30 s)…</div>';
  try {
    const j = await getJSON("/api/scan?" + params({tf:$("s-tf").value, top:$("s-top").value, symbols:$("s-list").value}));
    const rows = j.results.map(r => r.error
      ? `<tr><td>${esc(r.symbol)}</td><td class="err" colspan="8">${esc(r.error)}</td></tr>`
      : `<tr><td><a href="#" data-s="${esc(r.symbol)}">${esc(r.symbol)}</a></td>
         <td class="${r.action === "NO TRADE" ? "NO" : r.action}">${esc(r.action)}</td><td>${esc(r.strategy)}</td>
         <td>${r.setup_quality}</td><td>${r.score.toFixed(2)}</td>
         <td class="${(r.change_24h ?? 0) >= 0 ? "UP" : "DOWN"}">${r.change_24h == null ? "–" : r.change_24h.toFixed(1) + "%"}</td>
         <td>${num(r.entry ?? r.price)}</td><td>${num(r.stop_loss)}</td><td>${num(r.take_profit_1)}</td></tr>`).join("");
    $("s-out").innerHTML = `<div class="card"><h2>Scan results · ${esc(j.timeframe)}</h2><div class="scroll"><table>
      <tr><th>Symbol</th><th>Action</th><th>Strategy</th><th>Quality</th><th>Score</th><th>24h</th><th>Entry / price</th><th>Stop</th><th>TP1</th></tr>
      ${rows}</table></div><p class="muted">Best setups are listed first. Click a symbol to open it live with each agent's reasoning.</p></div>`;
    $("s-out").querySelectorAll("a[data-s]").forEach(a => a.onclick = e => { e.preventDefault();
      $("symbol").value = a.dataset.s; $("tf").value = $("s-tf").value;
      document.querySelector('[data-tab="live"]').click(); $("f").requestSubmit(); });
  } catch(e) { $("s-out").innerHTML = `<div class="card err">${esc(e.message)}</div>`; }
  finally { $("s-go").disabled = false; }
};

// ---------------------------------------------------------------- screenshot AI
let shotData = null;
function takeFile(file){
  if (!file || !file.type.startsWith("image/")) return;
  const img = new Image();
  img.onload = () => {
    const scale = Math.min(1, 1568 / Math.max(img.width, img.height));
    const c = document.createElement("canvas"); c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
    shotData = c.toDataURL("image/jpeg", 0.9);
    $("drop").innerHTML = `<img src="${shotData}" alt="Chart screenshot preview">`;
    $("x-go").disabled = !CONFIG.ai;
    URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(file);
}
$("drop").onclick = () => $("file").click();
$("drop").onkeydown = e => { if (e.key === "Enter" || e.key === " ") $("file").click(); };
$("file").onchange = e => takeFile(e.target.files[0]);
$("drop").ondragover = e => { e.preventDefault(); $("drop").classList.add("over"); };
$("drop").ondragleave = () => $("drop").classList.remove("over");
$("drop").ondrop = e => { e.preventDefault(); $("drop").classList.remove("over"); takeFile(e.dataTransfer.files[0]); };
document.addEventListener("paste", e => { if ($("tab-shot").classList.contains("hidden")) return;
  const item = [...e.clipboardData.items].find(i => i.type.startsWith("image/")); if (item) takeFile(item.getAsFile()); });

$("x-go").onclick = async () => {
  if (!shotData) return;
  $("x-go").disabled = true;
  $("x-out").innerHTML = '<div class="card">The AI is reading the chart and cross-checking it with live data (about 20–60 s)…</div>';
  try {
    const j = await getJSON("/api/screenshot", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({image:shotData, symbol:$("x-symbol").value, tf:$("x-tf").value, horizon:$("x-horizon").value,
        note:$("x-note").value, account:$("account").value, risk:$("risk").value})});
    const c = j.chart, list = a => a && a.length ? `<ul>${a.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : '<p class="muted">none</p>';
    let h = `<div class="card"><h2>AI chart reading ${c.symbol_guess ? "· " + esc(c.symbol_guess) : ""} ${c.timeframe_guess ? "· " + esc(c.timeframe_guess) : ""}</h2>
      <div class="action ${c.suggested_action}">${esc(c.suggested_action)}</div>
      <div class="grid"><div class="kv"><b>Trend on chart</b><span class="${c.trend}">${esc(c.trend)}</span></div>
      <div class="kv"><b>Bias for next ${esc($("x-horizon").value || "period")}</b><span class="${c.bias_next_period}">${esc(c.bias_next_period)}</span></div>
      <div class="kv"><b>AI estimate: chance up</b><span>${c.probability_up_pct}%</span><div class="meter"><span style="width:${c.probability_up_pct}%"></span></div></div>
      <div class="kv"><b>Entry / stop</b><span>${num(c.entry)} / ${num(c.stop_loss)}</span></div>
      <div class="kv"><b>Targets</b><span>${c.take_profits.map(num).join(", ") || "–"}</span></div></div>
      <h3>Structure</h3><p>${esc(c.market_structure)}</p>
      <h3>Patterns</h3>${list(c.patterns)}<h3>Indicators</h3>${list(c.indicators_seen)}
      <h3>Levels</h3><p>Support: ${c.supports.map(num).join(", ") || "–"} · Resistance: ${c.resistances.map(num).join(", ") || "–"}</p>
      <h3>Reasoning</h3><p>${esc(c.reasoning)}</p>
      <h3>Invalidation</h3><p>${esc(c.invalidation)}</p><h3>Risks</h3>${list(c.risks)}
      ${c.image_quality_issues ? `<div class="warn">${esc(c.image_quality_issues)}</div>` : ""}</div>`;
    if (j.live) { const d = j.live;
      h += `<div class="card"><h2>Live cross-check · ${esc(d.symbol)} ${esc(d.timeframe)}: <span class="${j.agreement}">${esc(j.agreement)}</span></h2>
        <p>Live agents say <b class="${d.action === "NO TRADE" ? "NO" : d.action}">${esc(d.action)}</b> (score ${d.score.toFixed(2)}, quality ${d.setup_quality}/100, strategy: ${esc(d.strategy)}).</p>
        <p class="muted">${j.agreement === "AGREE" ? "The screenshot reading and live data agree, which makes for a stronger setup." :
          j.agreement === "CONFLICT" ? "The screenshot and live data point in opposite directions, so stay out." :
          "One side says wait, so it's better to wait for confirmation."}</p>
        ${d.plan ? planHTML(d.plan) : ""}</div>`; }
    else if (j.live_error) h += `<div class="card warn">${esc(j.live_error)}</div>`;
    $("x-out").innerHTML = h;
  } catch(e) { $("x-out").innerHTML = `<div class="card err">${esc(e.message)}</div>`; }
  finally { $("x-go").disabled = false; }
};

startLive();
if (!$("demo").checked) runAnalysis(false);
</script>
</body>
</html>
"""
