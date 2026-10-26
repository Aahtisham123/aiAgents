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
.council{display:grid;gap:6px;margin-top:6px}.crow{background:var(--bg);border-radius:8px;padding:8px 10px}
.dots{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}.dots i{width:12px;height:12px;border-radius:50%;display:inline-block}
.plan.go{border-color:var(--long);border-width:2px}.plan.short{border-color:var(--short);border-width:2px}.plan.wait{border-color:var(--accent);border-width:2px}
.steps{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:6px}
.steps details{background:var(--bg);border-radius:8px;padding:8px 10px}
.steps summary{cursor:pointer;list-style:none;display:flex;gap:8px;align-items:baseline}
.steps summary::-webkit-details-marker{display:none}
.steps ul{margin:6px 0 0;padding-left:20px;font-size:13px;color:var(--muted)}
.st{flex:none;width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff}
.st.PASS{background:var(--long)}.st.FAIL{background:var(--short)}.st.WARN{background:#c98a00}.st.INFO{background:var(--none)}
.how{margin:8px 0 0;padding-left:22px}.how li{margin:3px 0}
.fan{width:100%;height:170px;display:block}
</style>
</head>
<body>
<main>
<h1>Crypto Trading Agents</h1>
<p class="sub">Five analyst agents, a risk manager and a chief strategist working on live Binance data, plus a pro trader's pre-trade checklist that tells you exactly where to enter, with optional Claude AI for screenshots and a senior-trader review.</p>

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
  <label>Plan side<select id="side"><option value="AUTO">Auto (agents decide)</option><option>LONG</option><option>SHORT</option></select></label>
  <label>Target<select id="target"><option value="1.5">1.5R</option><option value="2" selected>2R</option><option value="3">3R</option></select></label>
  <label class="check"><input id="demo" type="checkbox">Demo data</label>
  <label class="check"><input id="alert" type="checkbox">Alert me when it's time to enter</label>
  <button id="go" type="submit">Analyze</button>
  <button id="aibtn" type="button" class="secondary hidden">AI senior trader review</button>
</form></div>

<div id="plan"></div>

<div id="next"></div>

<div id="report"></div>

<div class="card" id="paper">
  <div class="agent-head"><h2>Demo trading · $100,000 paper account</h2>
    <button type="button" class="secondary" id="pt-reset" style="padding:4px 10px">Reset account</button></div>
  <div class="grid" id="pt-stats"></div>
  <h3>New order</h3>
  <div class="row">
    <label>Side<select id="pt-side"><option value="LONG">LONG (buy)</option><option value="SHORT">SHORT (sell)</option></select></label>
    <label>Order type<select id="pt-type"><option value="market">Market</option><option value="limit">Limit</option></select></label>
    <label id="pt-limit-l" class="hidden">Limit price<input id="pt-limit" type="number" step="any"></label>
    <label>Margin (USDT)<input id="pt-margin" type="number" value="1000" min="1" step="any"></label>
    <label>Leverage<select id="pt-lev"><option>1</option><option>2</option><option>3</option><option selected>5</option><option>10</option><option>20</option></select></label>
    <label>Stop-loss<input id="pt-sl" type="number" step="any" placeholder="optional"></label>
    <label>Take-profit<input id="pt-tp" type="number" step="any" placeholder="optional"></label>
    <label class="check"><input id="pt-candle" type="checkbox">Close at candle close</label>
  </div>
  <div class="row" style="margin-top:10px">
    <button type="button" id="pt-open">Open trade</button>
    <button type="button" class="secondary" id="pt-follow">Fill from Chief's call</button>
    <label class="check"><input id="pt-auto" type="checkbox">Auto-trade the Chief's LONG/SHORT calls</label>
  </div>
  <p class="muted" id="pt-msg">Fees 0.04% per side. Uses live Binance prices. Saved in this browser only, no real money.</p>
  <h3>Open positions</h3><div id="pt-pos" class="scroll"></div>
  <h3>Pending limit orders</h3><div id="pt-orders" class="scroll"></div>
  <h3>Closed trades</h3><div id="pt-hist" class="scroll"></div>
</div>
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
  for (const k of ["symbol","tf","account","risk","side","target"]) if (saved[k]) $(k).value = saved[k]; } catch(e) {}

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
    if (stream.includes("@aggTrade")) { trades.push({t:data.T, v:+data.p * +data.q, sell:data.m, p:+data.p}); ptPrice(sym, +data.p); }
    else if (stream.includes("@depth")) book = data;
    else if (stream.includes("@kline")) {
      const closedNow = data.k.x && kline && !kline.x; kline = data.k;
      if (closedNow) { gradeForecast(sym, tf, data.k); ptCandleClosed(sym, data.k); if ($("auto").value === "close") setTimeout(() => runAnalysis(true), 800); }
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

// ---------------------------------------------------------------- live data straight from Binance (in the browser)
const PROFILES = {"1m":["15m","5m","1m"],"5m":["1h","15m","5m"],"15m":["4h","1h","15m"],"1h":["1d","4h","1h"],"4h":["1w","1d","4h"],"1d":["1w","1d"]};
const REST_HOSTS = ["https://api.binance.com", "https://data-api.binance.vision"];
let restHost = 0;

async function binance(path){
  let last;
  for (let i = 0; i < REST_HOSTS.length; i++) {
    const host = REST_HOSTS[(restHost + i) % REST_HOSTS.length];
    try {
      const r = await fetch(host + path);
      if (r.status === 400) throw Object.assign(new Error("Unknown symbol on Binance"), {fatal:true});
      if (!r.ok) throw new Error(`${host} answered ${r.status}`);
      restHost = (restHost + i) % REST_HOSTS.length;
      return await r.json();
    } catch(e) { if (e.fatal) throw e; last = e; }
  }
  throw last;
}

async function fetchLive(sym, tf){
  const kl = await Promise.all(PROFILES[tf].map(t => binance(`/api/v3/klines?symbol=${sym}&interval=${t}&limit=1000`)));
  const [depth, trades] = await Promise.all([
    binance(`/api/v3/depth?symbol=${sym}&limit=500`).catch(() => null),
    binance(`/api/v3/aggTrades?symbol=${sym}&limit=1000`).catch(() => null)]);
  const klines = {}, rows = k => k.map(x => [x[0], +x[1], +x[2], +x[3], +x[4], +x[5], +x[9]]);
  PROFILES[tf].forEach((t, i) => klines[t] = rows(kl[i]));
  const [daily, btc_daily] = await Promise.all([dailyCandles(sym), sym === "BTCUSDT" ? null : dailyCandles("BTCUSDT")]);
  return {klines, depth, trades: trades && trades.map(t => ({p:t.p, q:t.q, m:t.m, T:t.T})), daily, btc_daily};
}

// Daily candles of the coin and of BTC, for the market-regime check (they change slowly: cached 10 minutes)
const dailyCache = {};
async function dailyCandles(sym){
  const hit = dailyCache[sym];
  if (hit && Date.now() - hit.at < 600000) return hit.rows;
  try {
    const k = await binance(`/api/v3/klines?symbol=${sym}&interval=1d&limit=400`);
    const rows = k.map(x => [x[0], +x[1], +x[2], +x[3], +x[4], +x[5], +x[9]]);
    dailyCache[sym] = {at: Date.now(), rows}; return rows;
  } catch(e) { return null; }
}

// ---------------------------------------------------------------- next-candle forecast + live track record
let lastForecast = null;
const sbKey = (sym, tf) => `cta-sb2-${sym}-${tf}`;
const loadSB = (sym, tf) => { try { return JSON.parse(localStorage.getItem(sbKey(sym, tf)) || "[]"); } catch(e) { return []; } };
const saveSB = (sym, tf, rows) => { try { localStorage.setItem(sbKey(sym, tf), JSON.stringify(rows.slice(-100))); } catch(e) {} };

function recordForecast(f){
  if ($("demo").checked) return;
  const rows = loadSB(f.symbol, f.timeframe), open = Math.round(f.target_candle_open * 1000);
  const row = {open, call:f.direction, chance:f.chance, strength:f.strength, final:f.final_call};
  const i = rows.findIndex(r => r.open === open);
  if (i >= 0) { if (rows[i].result == null) rows[i] = row; } else rows.push(row);  // keep the latest call before the candle closes
  saveSB(f.symbol, f.timeframe, rows);
}

function gradeForecast(sym, tf, k){
  const rows = loadSB(sym, tf), r = rows.find(x => x.open === k.t && x.result == null);
  if (!r) return;
  r.result = +k.c > +k.o ? "UP" : +k.c < +k.o ? "DOWN" : "FLAT";
  r.correct = (r.call === "LONG" && r.result === "UP") || (r.call === "SHORT" && r.result === "DOWN");
  saveSB(sym, tf, rows);
  if (lastForecast && lastForecast.symbol === sym && lastForecast.timeframe === tf && $("nx-sb")) $("nx-sb").innerHTML = scoreboard(sym, tf);
}

function scoreboard(sym, tf){
  const graded = loadSB(sym, tf).filter(r => r.result);
  if (!graded.length) return '<span class="muted">Every prediction is checked automatically when its candle closes, while this page is open. Results will appear here.</span>';
  const line = (rows, label) => { if (!rows.length) return ""; const ok = rows.filter(r => r.correct).length;
    return `<div><b>${label}: ${ok} of ${rows.length} right (${Math.round(ok / rows.length * 100)}%)</b></div>`; };
  const longs = graded.filter(r => r.call === "LONG").length;
  return line(graded.filter(r => r.final && r.final !== "NO TRADE"), "Chief's LONG/SHORT calls") + line(graded, "All leans (incl. NO TRADE)") +
    `<div class="muted">Calls made: ${longs} LONG / ${graded.length - longs} SHORT</div>` +
    `<div class="dots">${graded.slice(-40).map(r => `<i title="${new Date(r.open).toLocaleTimeString()} ${r.call} (${r.strength}) → ${r.result}" style="background:${r.correct ? "var(--long)" : "var(--short)"};opacity:${r.strength === "WEAK" ? .45 : 1}"></i>`).join("")}</div>
    <span class="muted">${esc(sym)} ${esc(tf)}, saved in this browser. Faded dots = WEAK calls.</span>`;
}

function renderForecastError(msg){
  $("next").innerHTML = `<div class="card next err" id="next-card"><h2>Couldn't make a prediction</h2><p>${esc(msg)}</p>
    <p class="muted">The page retries automatically at the next candle close. You can also press Analyze.</p></div>`;
}

function renderForecast(f, source){
  if (f.error) { lastForecast = null; renderForecastError(f.error); return; }
  lastForecast = f;
  recordForecast(f);
  const t = f.model_test, hhmm = s => new Date(s * 1000).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  const call = f.final_call, cls = call === "NO TRADE" ? "NO" : call;
  const sCls = f.strength === "STRONG" ? "UP" : f.strength === "MODERATE" ? "WAIT" : "DOWN";
  const acc = t.calls ? `${pct(t.call_accuracy)} right on ${t.calls} recent unseen candles` : "not enough test calls yet";
  const voteCell = v => v === "UP" ? '<b class="UP">▲ UP</b>' : v === "DOWN" ? '<b class="DOWN">▼ DOWN</b>' : `<span class="muted">${esc(v)}</span>`;
  const rec = c => c.track_record == null ? '<span class="muted">–</span>' :
    `<span class="${c.track_record >= 0.53 ? "UP" : c.track_record < 0.5 ? "DOWN" : ""}">${pct(c.track_record)}</span> <span class="muted">of ${c.track_votes}</span>`;
  $("next").innerHTML = `<div class="card next ${call === "NO TRADE" ? "" : call + "b"}" id="next-card">
    <div class="agent-head"><h2>Chief's call · next ${esc(f.timeframe)} candle · ${esc(f.symbol)} · ${hhmm(f.target_candle_open)}–${hhmm(f.target_candle_close)}</h2>
      <span class="pill NEUTRAL" id="nx-left">live</span></div>
    <div class="big ${cls}">${call === "LONG" ? "▲ " : call === "SHORT" ? "▼ " : ""}${esc(call)}
      <span style="font-size:.5em">${call === "NO TRADE" ? `leans ${esc(f.direction)} ${pct(f.chance)}` : `${pct(f.chance)} chance`}</span></div>
    <div style="margin:6px 0 2px"><span class="pill ${sCls}">${esc(f.strength)}</span> ${esc(f.advice)}</div>
    <div class="prob"><span class="UP">UP ${pct(f.probability_up)}</span><span class="DOWN">DOWN ${pct(f.probability_down)}</span></div>
    <div class="meter"><span style="width:${(f.probability_up * 100).toFixed(1)}%"></span></div>
    <p><b>Chief:</b> ${esc(f.chief_summary)}</p>
    <h3>Agent council: what each agent sees and its vote for the next candle</h3>
    <div class="council">${f.council.map(c => `<div class="crow">
      <div class="agent-head"><b>${esc(c.agent)}</b><span>${voteCell(c.vote)} · ${rec(c)}</span></div>
      <div class="muted">${esc(c.reading)}</div></div>`).join("")}</div>
    <p class="muted">Each agent's vote is what its reading has actually meant for the next candle on this coin and timeframe, learned from recent history. On 1m, for example, an overbought reading usually meant a pullback. Track record = how often that agent's vote was right on recent candles it never saw.</p>
    <h3>Why</h3><ul>${f.why.map(w => `<li>${esc(w)}</li>`).join("")}</ul>
    ${f.patterns.length ? `<div class="chips">${f.patterns.map(p => `<span class="chip"><span class="${p.bias}">${p.bias === "UP" ? "▲" : p.bias === "DOWN" ? "▼" : "•"}</span> ${esc(p.name)}</span>`).join("")}</div>` : ""}
    ${f.warnings.length ? `<div class="warn"><ul>${f.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}
    <div class="grid"><div class="kv"><b>Entry</b><span>${num(f.plan.entry)}</span></div>
      <div class="kv"><b>Stop-loss</b><span>${num(f.plan.stop_loss)}</span></div>
      <div class="kv"><b>Target</b><span>${num(f.plan.take_profit)}</span></div>
      <div class="kv"><b>Chief's recent accuracy</b><span>${acc}</span></div>
      <div class="kv"><b>Market drift (last 200 candles)</b><span>${pct(f.recent_up_rate)} closed up</span></div></div>
    <p class="muted">Exit: ${esc(f.plan.exit)}.</p>
    <h3>Live track record</h3><div id="nx-sb">${scoreboard(f.symbol, f.timeframe)}</div>
    <p class="muted">${esc(f.note)} The chance assumes the candle moves at all${f.flat_candle_rate > 0.05 ? ` (${pct(f.flat_candle_rate)} of recent candles closed flat)` : ""}. Data: ${esc(source)} · updated ${new Date().toLocaleTimeString()}.</p></div>`;
}

// ---------------------------------------------------------------- pro trade plan
let lastPlan = null, lastPlanAction = "";
const ICON = {PASS:"✓", FAIL:"✕", WARN:"!", INFO:"i"};

function fanChart(p){
  const mc = p.steps.find(s => s.key === "timemachine")?.data?.mc;
  if (!mc || !mc.fan) return "";
  const W = 600, H = 170, pad = 4, n = mc.fan.length;
  const vals = mc.fan.flat().concat([p.entry, p.stop, p.targets[1]]);
  const lo = Math.min(...vals), hi = Math.max(...vals), y = v => pad + (hi - v) / ((hi - lo) || 1) * (H - 2 * pad);
  const x = i => (i + 1) / n * W;
  const band = (a, b) => `M0,${y(p.entry)} ` + mc.fan.map((q, i) => `L${x(i)},${y(q[a])}`).join(" ") + " " +
    mc.fan.map((q, i) => `L${x(n - 1 - i)},${y(mc.fan[n - 1 - i][b])}`).join(" ") + ` L0,${y(p.entry)} Z`;
  const line = (v, color, label) => `<line x1="0" x2="${W}" y1="${y(v)}" y2="${y(v)}" stroke="${color}" stroke-dasharray="4 4"/>
    <text x="${W - 4}" y="${y(v) < 16 ? y(v) + 13 : y(v) - 4}" text-anchor="end" font-size="11" fill="${color}">${label} ${num(v)}</text>`;
  return `<svg class="fan" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Range of replayed prices">
    <path d="${band(0, 4)}" fill="var(--accent)" opacity=".12"/><path d="${band(1, 3)}" fill="var(--accent)" opacity=".22"/>
    <path d="M0,${y(p.entry)} ${mc.fan.map((q, i) => `L${x(i)},${y(q[2])}`).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="2"/>
    ${line(p.targets[1], "var(--long)", "target")}${line(p.entry, "var(--muted)", "entry")}${line(p.stop, "var(--short)", "stop")}</svg>
    <p class="muted">Where ${mc.replays.toLocaleString()} replays of the next ${mc.steps} candles ended up: the dark band holds half of them, the light band 90%, the line is the middle one.</p>`;
}

function renderPlan(p, source){
  if (!p) { $("plan").innerHTML = ""; return; }
  if (p.error) { lastPlan = null; $("plan").innerHTML = `<div class="card err">${esc(p.error)}</div>`; return; }
  lastPlan = p;
  const go = p.action.startsWith("ENTER"), no = p.action.startsWith("NO TRADE");
  const cls = no ? "" : go ? (p.side === "LONG" ? "go" : "short") : "wait";
  const color = no ? "NO" : p.side;
  const t = p.sizing, base = p.symbol.replace(/USDT$/, "");
  $("plan").innerHTML = `<div class="card plan ${cls}" id="plan-card">
    <div class="agent-head"><h2>Pro trade plan · ${esc(p.symbol)} · ${esc(p.timeframe)}</h2><span class="pill NEUTRAL">${esc(p.score)}</span></div>
    <div class="action ${color}">${esc(p.action)}</div>
    <p style="margin:4px 0 0"><b>${esc(p.headline)}</b></p>
    <div class="grid">
      <div class="kv"><b>Entry (${esc(p.entry_kind)})</b><span>${num(p.entry)}</span></div>
      <div class="kv"><b>Stop-loss</b><span class="DOWN">${num(p.stop)}</span></div>
      <div class="kv"><b>Take profit 1R / ${p.target_r}R / ${p.target_r + 1}R</b><span class="UP">${p.targets.map(num).join(" · ")}</span></div>
      <div class="kv"><b>Size</b><span>${Number(t.units).toPrecision(4)} ${esc(base)}</span> <span class="muted">≈ ${num(t.value)} USDT, ${t.leverage}x</span></div>
      <div class="kv"><b>Max loss at the stop</b><span>${num(t.max_loss)} USDT</span></div>
      <div class="kv"><b>Price now</b><span>${num(p.price)}</span></div></div>
    <h3>How to enter</h3><ol class="how">${p.how_to_enter.map(h => `<li>${esc(h)}</li>`).join("")}</ol>
    ${p.warnings.length ? `<div class="warn"><ul>${p.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}
    <div class="row" style="margin-top:12px"><button type="button" id="plan-load" ${no ? 'class="secondary"' : ""}>Load plan into demo trade</button>
      <span class="muted" id="plan-msg"></span></div>
    <h3>Time Machine</h3>${fanChart(p)}
    <h3>Pre-trade checklist</h3>
    <ul class="steps">${p.steps.map(s => `<li><details><summary><span class="st ${s.status}">${ICON[s.status]}</span>
      <span><b>${esc(s.title)}</b> <span class="chip">${esc(s.skill)}</span><br>${esc(s.summary)}</span></summary>
      ${s.details.length ? `<ul>${s.details.map(d => `<li>${esc(d)}</li>`).join("")}</ul>` : ""}</details></li>`).join("")}</ul>
    <p class="muted">${esc(p.disclaimer)} Data: ${esc(source)} · updated ${new Date(p.generated_at * 1000).toLocaleTimeString()}. Tap a step to see the details.</p></div>`;
  $("plan-load").onclick = loadPlan;
  if ($("alert").checked && go && lastPlanAction !== p.action + p.symbol) notify(`${p.action}: ${p.symbol}`, p.headline);
  lastPlanAction = p.action + p.symbol;
}

function notify(title, body){
  try { const a = new AudioContext(), o = a.createOscillator(); o.connect(a.destination); o.frequency.value = 880; o.start(); o.stop(a.currentTime + 0.25); } catch(e) {}
  try { if (Notification.permission === "granted") new Notification(title, {body}); } catch(e) {}
}
$("alert").onchange = () => { try { if ($("alert").checked && Notification.permission === "default") Notification.requestPermission(); } catch(e) {} };

function loadPlan(){
  const p = lastPlan; if (!p) return;
  const msg = t => $("plan-msg").textContent = t;
  $("pt-side").value = p.side; $("pt-sl").value = p.stop; $("pt-tp").value = p.targets[1];
  const levs = [...$("pt-lev").options].map(o => +o.value), lev = levs.find(l => l >= p.sizing.leverage) || levs[levs.length - 1];
  $("pt-lev").value = lev; $("pt-margin").value = (p.sizing.value / lev).toFixed(2); $("pt-candle").checked = false;
  const limit = p.entry_kind === "retest limit";
  $("pt-type").value = limit ? "limit" : "market"; $("pt-limit-l").classList.toggle("hidden", !limit);
  if (limit) $("pt-limit").value = p.entry;
  $("paper").scrollIntoView({behavior:"smooth", block:"start"});
  msg(p.action.startsWith("NO TRADE") ? "Filled in, but the checklist says NO TRADE."
    : p.action.startsWith("ENTER") ? "Filled in the demo order below. Check it, then press Open trade."
    : limit ? "Filled in a limit order at the retest level. Check it, then press Open trade."
    : "Filled in, but wait: only open it once a candle closes past the level (tick 'Alert me' to be told).");
}

// What the circuit breaker and the risk manager need from the demo account
function ptJournal(){
  return {start_equity: PT_START, open_symbols: PT.positions.map(p => p.symbol),
          trades: PT.history.map(t => ({closed: t.closed, pnl: t.pnl, symbol: t.symbol}))};
}

function renderReport(r){
  if (!r) { $("report").innerHTML = ""; return; }
  const t = s => new Date(s * 1000).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  $("report").innerHTML = `<div class="card"><h2>Market analysis</h2>
    ${r.sections.map(sec => `<h3>${esc(sec.title)}</h3><ul>${sec.items.map(i => `<li>${esc(i)}</li>`).join("")}</ul>
      ${sec.title === "Candle analysis" ? `<div class="scroll"><table><tr><th>Candle</th><th>Color</th><th>Change</th><th>Size (ATR)</th><th>Notes</th></tr>
        ${r.candles.map(c => `<tr><td>${t(c.time)}</td><td class="${c.color === "green" ? "UP" : c.color === "red" ? "DOWN" : ""}">${esc(c.color)}</td>
          <td>${c.change_pct >= 0 ? "+" : ""}${c.change_pct.toFixed(3)}%</td><td>${c.range_atr.toFixed(2)}</td>
          <td style="white-space:normal">${esc(c.note)}</td></tr>`).join("")}</table></div>` : ""}`).join("")}
  </div>`;
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

async function loadOdds(sym, tf, live){
  const key = sym + tf + $("demo").checked;
  if (key === lastOddsKey && Date.now() - lastOddsAt < 300000) return;
  lastOddsKey = key; lastOddsAt = Date.now();
  if ($("odds")) $("odds").innerHTML = '<div class="card muted" id="odds-card">Measuring historical win/loss odds for this setup…</div>';
  try { const o = await getJSON("/api/odds", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({symbol:sym, tf, account:$("account").value, risk:$("risk").value, demo:$("demo").checked ? "1" : "0", live})});
    if ($("odds")) $("odds").innerHTML = renderOdds(o);
  } catch(e) { lastOddsKey = ""; if ($("odds")) $("odds").innerHTML = `<div class="card err" id="odds-card">${esc(e.message)}</div>`; }
}

async function runAnalysis(silent){
  if (busy) return; busy = true;
  const sym = $("symbol").value.trim().toUpperCase().replace(/[^A-Z0-9]/g, ""), tf = $("tf").value, demo = $("demo").checked;
  try { localStorage.setItem("cta", JSON.stringify({symbol:sym, tf, account:$("account").value, risk:$("risk").value,
    side:$("side").value, target:$("target").value})); } catch(e) {}
  $("go").disabled = true;
  if (!lastForecast || lastForecast.symbol !== sym || lastForecast.timeframe !== tf) {
    $("plan").innerHTML = '<div class="card">Running the pro trader checklist: market regime, setups, entry timer, exit plan, 10,000 replays, sizing and risk limits…</div>';
    $("next").innerHTML = '<div class="card next">Fetching live candles and asking all agents for the next candle…</div>';
    $("out").innerHTML = "";
  }
  try {
    let live = null, source = demo ? "demo data" : "Binance via the server";
    if (!demo) {
      try { live = await fetchLive(sym, tf); source = "live Binance candles fetched by your browser"; }
      catch(e) { if (e.fatal) throw new Error(`${sym} is not a Binance spot pair. Try e.g. BTCUSDT, ETHUSDT or SOLUSDT.`); }
    }
    const body = {symbol:sym, tf, account:$("account").value, risk:$("risk").value, demo: demo ? "1" : "0", live,
      side:$("side").value, target_r:$("target").value, max_leverage:$("pt-lev").value, journal: ptJournal()};
    const j = await getJSON("/api/next", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    const d = j.decision;
    if (lastDecision && (lastDecision.symbol !== d.symbol || lastDecision.timeframe !== d.timeframe)) { lastOddsKey = ""; $("out").innerHTML = ""; }
    renderPlan(j.plan, source);
    renderForecast(j.forecast, source);
    renderReport(j.report);
    if (!marks[j.forecast.symbol] && j.forecast.price) marks[j.forecast.symbol] = j.forecast.price;
    ptAuto(j.forecast);
    renderDecision(d);
    loadOdds(d.symbol, tf, live);
  } catch(e) { renderForecastError(e.message); }
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
  try {
    let live = null;
    if (!$("demo").checked) { try { live = await fetchLive(sym, tf); } catch(e) { if (e.fatal) throw e; } }
    const j = await getJSON("/api/ai-review", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({symbol:sym, tf, account:$("account").value, risk:$("risk").value, demo:$("demo").checked ? "1" : "0", live})});
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
const STABLES = new Set(["USDC","FDUSD","TUSD","BUSD","DAI","USDP","USDE","EUR","AEUR","EURI","USD1","PAXG","XUSD","BFUSD","RLUSD","USDS","PYUSD"]);
const normSym = raw => { let x = String(raw || "").toUpperCase().split(":").pop().split(".")[0].replace(/[^A-Z0-9]/g, "");
  if (x.endsWith("PERP")) x = x.slice(0, -4); if (x.endsWith("USD")) x += "T";
  if (x && !/(USDT|USDC|BTC|ETH|BNB|FDUSD)$/.test(x)) x += "USDT"; return x; };
const STRENGTH_RANK = {STRONG: 0, MODERATE: 1, WEAK: 2};

async function scanUniverse(){
  const list = $("s-list").value.split(",").map(normSym).filter(Boolean);
  if (list.length) return list.slice(0, 40).map(symbol => ({symbol}));
  const rows = await binance("/api/v3/ticker/24hr");
  return rows.filter(r => r.symbol.endsWith("USDT") && !STABLES.has(r.symbol.slice(0, -4)) && !/(UP|DOWN|BULL|BEAR)USDT$/.test(r.symbol) && +r.lastPrice > 0)
    .sort((a, b) => +b.quoteVolume - +a.quoteVolume).slice(0, +$("s-top").value)
    .map(r => ({symbol: r.symbol, change_24h: +r.priceChangePercent}));
}

function renderScan(tf, rows, done, total){
  const sorted = [...rows].sort((a, b) => ("error" in a) - ("error" in b) ||
    (STRENGTH_RANK[a.f?.strength] ?? 3) - (STRENGTH_RANK[b.f?.strength] ?? 3) || (b.f?.chance ?? 0) - (a.f?.chance ?? 0));
  const body = sorted.map(r => r.error
    ? `<tr><td>${esc(r.symbol)}</td><td class="err" colspan="8">${esc(r.error)}</td></tr>`
    : `<tr><td><a href="#" data-s="${esc(r.symbol)}">${esc(r.symbol)}</a></td>
       <td class="${r.f.direction}"><b>${r.f.direction === "LONG" ? "▲" : "▼"} ${esc(r.f.direction)}</b></td>
       <td>${pct(r.f.chance)}</td><td><span class="pill ${r.f.strength === "STRONG" ? "UP" : r.f.strength === "MODERATE" ? "WAIT" : "DOWN"}">${esc(r.f.strength)}</span></td>
       <td class="${r.d.action === "NO TRADE" ? "NO" : r.d.action}">${esc(r.d.action)}</td>
       <td class="${(r.change_24h ?? 0) >= 0 ? "UP" : "DOWN"}">${r.change_24h == null ? "–" : r.change_24h.toFixed(1) + "%"}</td>
       <td>${num(r.f.price)}</td><td>${num(r.f.plan.stop_loss)}</td><td>${num(r.f.plan.take_profit)}</td></tr>`).join("");
  $("s-out").innerHTML = `<div class="card"><h2>Scan · next ${esc(tf)} candle ${done < total ? `(${done}/${total} analyzed…)` : ""}</h2>
    <div class="scroll"><table><tr><th>Symbol</th><th>Next candle</th><th>Chance</th><th>Strength</th><th>Agents (bigger picture)</th><th>24h</th><th>Price</th><th>Stop</th><th>Target</th></tr>
    ${body}</table></div><p class="muted">STRONG and MODERATE calls are listed first. Click a coin to watch it live with every agent's reasoning.</p></div>`;
  $("s-out").querySelectorAll("a[data-s]").forEach(a => a.onclick = e => { e.preventDefault();
    $("symbol").value = a.dataset.s; $("tf").value = tf;
    document.querySelector('[data-tab="live"]').click(); $("f").requestSubmit(); });
}

$("s-go").onclick = async () => {
  $("s-go").disabled = true;
  const tf = $("s-tf").value, demo = $("demo").checked;
  $("s-out").innerHTML = '<div class="card">Finding the most traded coins on Binance…</div>';
  try {
    const universe = demo ? ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"].map(symbol => ({symbol})) : await scanUniverse();
    const rows = []; let next = 0;
    const worker = async () => {
      while (next < universe.length) {
        const row = universe[next++];
        try {
          const live = demo ? null : await fetchLive(row.symbol, tf);
          const j = await getJSON("/api/next", {method:"POST", headers:{"Content-Type":"application/json"},
            body: JSON.stringify({symbol:row.symbol, tf, account:$("account").value, risk:$("risk").value, demo: demo ? "1" : "0", live})});
          if (j.forecast.error) throw new Error(j.forecast.error);
          rows.push({...row, f:j.forecast, d:j.decision});
        } catch(e) { rows.push({...row, error:e.message}); }
        renderScan(tf, rows, rows.length, universe.length);
      }
    };
    await Promise.all([worker(), worker(), worker()]);
  } catch(e) { $("s-out").innerHTML = `<div class="card err">Couldn't load the coin list from Binance: ${esc(e.message)}</div>`; }
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
        note:$("x-note").value, account:$("account").value, risk:$("risk").value, skip_live:true})});
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
    $("x-out").innerHTML = h + '<div id="x-live" class="card muted">Checking the chart against live Binance data…</div>';
    const sym = normSym($("x-symbol").value || c.symbol_guess);
    const ltf = $("x-tf").value || (TFS.includes(c.timeframe_guess) ? c.timeframe_guess : "1h");
    if (!sym) { $("x-live").textContent = "Couldn't read the coin from the screenshot. Type the symbol above to cross-check with live data."; }
    else {
      try {
        const live = $("demo").checked ? null : await fetchLive(sym, ltf);
        const k = await getJSON("/api/next", {method:"POST", headers:{"Content-Type":"application/json"},
          body: JSON.stringify({symbol:sym, tf:ltf, account:$("account").value, risk:$("risk").value, demo:$("demo").checked ? "1" : "0", live})});
        const f = k.forecast, d = k.decision;
        const liveCall = f.error || f.strength === "WEAK" ? "WAIT" : f.direction;
        const agreement = liveCall === c.suggested_action ? "AGREE" : (liveCall === "WAIT" || c.suggested_action === "WAIT") ? "PARTIAL" : "CONFLICT";
        $("x-live").className = "card";
        $("x-live").innerHTML = `<h2>Live cross-check · ${esc(sym)} ${esc(ltf)}: <span class="${agreement}">${esc(agreement)}</span></h2>
          ${f.error ? `<p class="err">${esc(f.error)}</p>` : `<p>Next ${esc(ltf)} candle on live data: <b class="${f.direction}">${f.direction === "LONG" ? "▲" : "▼"} ${esc(f.direction)} ${pct(f.chance)}</b> <span class="pill ${f.strength === "STRONG" ? "UP" : f.strength === "MODERATE" ? "WAIT" : "DOWN"}">${esc(f.strength)}</span></p>`}
          <p>Agents (bigger picture): <b class="${d.action === "NO TRADE" ? "NO" : d.action}">${esc(d.action)}</b> · ${esc(d.strategy)}</p>
          <p class="muted">${agreement === "AGREE" && liveCall === "WAIT" ? "Both the screenshot and live data say wait. There's no clear trade right now." :
            agreement === "AGREE" ? "The screenshot and live data agree, which makes for a stronger setup." :
            agreement === "CONFLICT" ? "The screenshot and live data point in opposite directions, so stay out." :
            "One side says wait, so it's better to wait for confirmation."}</p>`;
      } catch(e) { $("x-live").className = "card warn"; $("x-live").textContent = `Live cross-check for ${sym} failed: ${e.message}`; }
    }
  } catch(e) { $("x-out").innerHTML = `<div class="card err">${esc(e.message)}</div>`; }
  finally { $("x-go").disabled = false; }
};

// ---------------------------------------------------------------- demo (paper) trading
const PT_KEY = "cta-paper-v1", PT_START = 100000, FEE = 0.0004;
const ptFresh = () => ({balance: PT_START, positions: [], orders: [], history: [], nextId: 1});
let PT = (() => { try { return JSON.parse(localStorage.getItem(PT_KEY)) || ptFresh(); } catch(e) { return ptFresh(); } })();
const marks = {};
const ptSave = () => { try { localStorage.setItem(PT_KEY, JSON.stringify(PT)); } catch(e) {} };
const ptMsg = (t, bad) => { $("pt-msg").textContent = t; $("pt-msg").className = bad ? "err" : "muted"; };
const money = x => (x < 0 ? "-$" : "$") + Math.abs(x).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
const sgn = s => s === "LONG" ? 1 : -1;
const upnl = p => marks[p.symbol] ? (marks[p.symbol] - p.entry) * p.qty * sgn(p.side) : 0;

function ptOpen({symbol, side, margin, lev, sl, tp, price, closeAt, source}){
  if (!(price > 0)) return ptMsg("No live price yet for " + symbol + ". Wait a second and try again.", true);
  const notional = margin * lev, fee = notional * FEE;
  if (!(margin > 0)) return ptMsg("Enter a margin amount.", true);
  if (margin + fee > PT.balance) return ptMsg(`Not enough balance: you have ${money(PT.balance)}.`, true);
  if (sl && (side === "LONG" ? sl >= price : sl <= price)) return ptMsg(`Stop-loss must be ${side === "LONG" ? "below" : "above"} the entry price.`, true);
  if (tp && (side === "LONG" ? tp <= price : tp >= price)) return ptMsg(`Take-profit must be ${side === "LONG" ? "above" : "below"} the entry price.`, true);
  PT.balance -= margin + fee;
  PT.positions.push({id: PT.nextId++, symbol, side, qty: notional / price, entry: price, lev, margin, sl: sl || null, tp: tp || null,
    opened: Date.now(), closeAt: closeAt || null, feesPaid: fee, source: source || "manual"});
  ptSave(); ptMsg(`Opened ${side} ${symbol} at ${num(price)} with ${money(margin)} × ${lev}x.`); ptRender();
}

function ptClose(p, price, reason){
  const pnlGross = (price - p.entry) * p.qty * sgn(p.side);
  const fee = price * p.qty * FEE;
  const pnl = Math.max(pnlGross - fee, -p.margin);          // you can't lose more than the margin
  PT.balance += p.margin + pnl;
  PT.positions = PT.positions.filter(x => x.id !== p.id);
  const net = pnl - p.feesPaid;
  PT.history.unshift({...p, exit: price, closed: Date.now(), pnl: net, pct: net / p.margin * 100, reason,
                      result: net > 0 ? "WIN" : "LOSS"});
  PT.history = PT.history.slice(0, 200);
  ptSave(); ptMsg(`${net > 0 ? "WIN" : "LOSS"}: ${p.side} ${p.symbol} closed at ${num(price)} (${reason}) → ${money(net)}.`, net <= 0);
}

function ptPrice(symbol, price){
  marks[symbol] = price;
  for (const o of PT.orders.filter(o => o.symbol === symbol)) {
    if ((o.side === "LONG" && price <= o.limit) || (o.side === "SHORT" && price >= o.limit)) {
      PT.orders = PT.orders.filter(x => x.id !== o.id); PT.balance += o.margin;  // release the reserved margin
      ptOpen({...o, price: o.limit, source: "limit"});
    }
  }
  for (const p of PT.positions.filter(p => p.symbol === symbol)) {
    const loss = -(price - p.entry) * p.qty * sgn(p.side);
    if (loss >= p.margin * 0.9) ptClose(p, price, "Liquidated");
    else if (p.sl && (p.side === "LONG" ? price <= p.sl : price >= p.sl)) ptClose(p, p.sl, "Stop-loss hit");
    else if (p.tp && (p.side === "LONG" ? price >= p.tp : price <= p.tp)) ptClose(p, p.tp, "Take-profit hit");
  }
}

function ptCandleClosed(symbol, k){
  for (const p of PT.positions.filter(p => p.symbol === symbol && p.closeAt && p.closeAt <= k.T + 1)) ptClose(p, +k.c, "Candle closed");
}

// prices for positions in other coins (the live stream only covers the coin on screen)
setInterval(async () => {
  const syms = [...new Set([...PT.positions, ...PT.orders].map(p => p.symbol))];
  if (!syms.length || $("demo").checked) return;
  try {
    const rows = await binance(`/api/v3/ticker/price?symbols=${encodeURIComponent(JSON.stringify(syms))}`);
    for (const r of rows) {
      ptPrice(r.symbol, +r.price);
      for (const p of PT.positions.filter(p => p.symbol === r.symbol && p.closeAt && Date.now() > p.closeAt + 3000)) ptClose(p, +r.price, "Candle closed");
    }
  } catch(e) {}
}, 3000);

function ptRender(){
  const unreal = PT.positions.reduce((a, p) => a + upnl(p), 0);
  const locked = PT.positions.reduce((a, p) => a + p.margin, 0) + PT.orders.reduce((a, o) => a + o.margin, 0);
  const equity = PT.balance + locked + unreal;
  const h = PT.history, wins = h.filter(t => t.result === "WIN").length, realized = h.reduce((a, t) => a + t.pnl, 0);
  $("pt-stats").innerHTML = `
    <div class="kv"><b>Equity</b><span class="${equity >= PT_START ? "UP" : "DOWN"}">${money(equity)}</span></div>
    <div class="kv"><b>Total P&amp;L</b><span class="${equity >= PT_START ? "UP" : "DOWN"}">${money(equity - PT_START)} (${((equity / PT_START - 1) * 100).toFixed(2)}%)</span></div>
    <div class="kv"><b>Available balance</b><span>${money(PT.balance)}</span></div>
    <div class="kv"><b>Closed trades</b><span>${h.length ? `${wins} won / ${h.length - wins} lost (${Math.round(wins / h.length * 100)}%)` : "none yet"}</span></div>
    <div class="kv"><b>Realized P&amp;L</b><span class="${realized >= 0 ? "UP" : "DOWN"}">${money(realized)}</span></div>
    <div class="kv"><b>Open P&amp;L</b><span class="${unreal >= 0 ? "UP" : "DOWN"}">${money(unreal)}</span></div>`;
  $("pt-pos").innerHTML = PT.positions.length ? `<table><tr><th>Coin</th><th>Side</th><th>Size</th><th>Entry</th><th>Price</th><th>P&amp;L</th><th>SL / TP</th><th></th></tr>
    ${PT.positions.map(p => { const u = upnl(p); return `<tr><td>${esc(p.symbol)}</td><td class="${p.side}">${p.side} ${p.lev}x</td>
      <td>${money(p.margin * p.lev)}</td><td>${num(p.entry)}</td><td>${num(marks[p.symbol])}</td>
      <td class="${u >= 0 ? "UP" : "DOWN"}">${money(u)} (${(u / p.margin * 100).toFixed(1)}%)</td>
      <td>${p.sl ? num(p.sl) : "–"} / ${p.tp ? num(p.tp) : "–"}${p.closeAt ? `<br><span class="muted">closes ${new Date(p.closeAt).toLocaleTimeString()}</span>` : ""}</td>
      <td><button type="button" class="secondary" data-close="${p.id}" style="padding:2px 8px">Close</button></td></tr>`; }).join("")}</table>`
    : '<p class="muted">No open positions.</p>';
  $("pt-orders").innerHTML = PT.orders.length ? `<table><tr><th>Coin</th><th>Side</th><th>Limit</th><th>Size</th><th></th></tr>
    ${PT.orders.map(o => `<tr><td>${esc(o.symbol)}</td><td class="${o.side}">${o.side} ${o.lev}x</td><td>${num(o.limit)}</td><td>${money(o.margin * o.lev)}</td>
      <td><button type="button" class="secondary" data-cancel="${o.id}" style="padding:2px 8px">Cancel</button></td></tr>`).join("")}</table>`
    : '<p class="muted">No pending orders.</p>';
  $("pt-hist").innerHTML = h.length ? `<table><tr><th>Result</th><th>Coin</th><th>Side</th><th>Entry → exit</th><th>P&amp;L</th><th>Why closed</th><th>When</th></tr>
    ${h.slice(0, 50).map(t => `<tr><td class="${t.result === "WIN" ? "UP" : "DOWN"}"><b>${t.result}</b></td><td>${esc(t.symbol)}</td>
      <td class="${t.side}">${t.side} ${t.lev}x${t.source === "auto" ? " (auto)" : ""}</td><td>${num(t.entry)} → ${num(t.exit)}</td>
      <td class="${t.pnl >= 0 ? "UP" : "DOWN"}">${money(t.pnl)} (${t.pct.toFixed(1)}%)</td><td>${esc(t.reason)}</td>
      <td class="muted">${new Date(t.closed).toLocaleTimeString()}</td></tr>`).join("")}</table>`
    : '<p class="muted">No closed trades yet. Results (WIN / LOSS) appear here.</p>';
}
setInterval(ptRender, 1000);

$("paper").addEventListener("click", e => {
  const c = e.target.dataset.close, x = e.target.dataset.cancel;
  if (c) { const p = PT.positions.find(p => p.id === +c); if (p) { ptClose(p, marks[p.symbol] || p.entry, "Closed by you"); ptRender(); } }
  if (x) { const o = PT.orders.find(o => o.id === +x); if (o) { PT.balance += o.margin; PT.orders = PT.orders.filter(q => q.id !== o.id); ptSave(); ptRender(); } }
});
$("pt-type").onchange = () => $("pt-limit-l").classList.toggle("hidden", $("pt-type").value !== "limit");
$("pt-reset").onclick = () => { if (confirm("Reset the demo account to $100,000 and delete its history?")) { PT = ptFresh(); ptSave(); ptRender(); ptMsg("Account reset to $100,000."); } };

function currentSymbol(){ return $("symbol").value.trim().toUpperCase().replace(/[^A-Z0-9]/g, ""); }
$("pt-open").onclick = () => {
  const symbol = currentSymbol(), side = $("pt-side").value, margin = +$("pt-margin").value, lev = +$("pt-lev").value;
  const sl = +$("pt-sl").value || null, tp = +$("pt-tp").value || null;
  const closeAt = $("pt-candle").checked && lastForecast && lastForecast.symbol === symbol ? lastForecast.target_candle_close * 1000 : null;
  if ($("pt-type").value === "limit") {
    const limit = +$("pt-limit").value;
    if (!(limit > 0)) return ptMsg("Enter a limit price.", true);
    if (margin <= 0 || margin > PT.balance) return ptMsg(`Not enough balance: you have ${money(PT.balance)}.`, true);
    PT.balance -= margin;
    PT.orders.push({id: PT.nextId++, symbol, side, margin, lev, sl, tp, limit, closeAt});
    ptSave(); ptRender(); return ptMsg(`Limit ${side} ${symbol} at ${num(limit)} placed. It fills when the live price reaches it.`);
  }
  ptOpen({symbol, side, margin, lev, sl, tp, price: marks[symbol], closeAt});
};
$("pt-follow").onclick = () => {
  if (!lastForecast) return ptMsg("No prediction yet. Press Analyze first.", true);
  const f = lastForecast, call = f.final_call || f.direction;
  if (call === "NO TRADE") ptMsg("The Chief says NO TRADE for this candle. Filled the levels anyway, but you might want to skip it.", true);
  $("pt-side").value = call === "SHORT" || (call === "NO TRADE" && f.direction === "SHORT") ? "SHORT" : "LONG";
  const lv = planLevels(f, $("pt-side").value, marks[f.symbol] || f.price);
  $("pt-sl").value = lv.sl.toPrecision(6); $("pt-tp").value = lv.tp.toPrecision(6);
  $("pt-candle").checked = true; $("pt-type").value = "market"; $("pt-limit-l").classList.add("hidden");
};

// The Chief's stop/target as distances from the entry, applied to the price you actually get
function planLevels(f, side, price){
  const stopDist = Math.abs(f.plan.entry - f.plan.stop_loss), tpDist = Math.abs(f.plan.take_profit - f.plan.entry);
  return side === "LONG" ? {sl: price - stopDist, tp: price + tpDist} : {sl: price + stopDist, tp: price - tpDist};
}

// auto-trade: open one position per Chief LONG/SHORT call, closed at the candle's close
function ptAuto(f){
  if (!$("pt-auto").checked || $("demo").checked || !f || f.error) return;
  const call = f.final_call || (f.strength !== "WEAK" ? f.direction : "NO TRADE");
  if (call === "NO TRADE") return;
  const step = f.target_candle_close - f.target_candle_open;
  if (f.seconds_elapsed > 0.3 * step) return;                              // too late into the candle
  if (PT.positions.some(p => p.symbol === f.symbol && p.source === "auto")) return;
  if (PT.history.some(t => t.symbol === f.symbol && t.source === "auto" && t.closeAt === f.target_candle_close * 1000)) return;
  const price = marks[f.symbol] || f.price, lv = planLevels(f, call, price);
  ptOpen({symbol: f.symbol, side: call, margin: +$("pt-margin").value, lev: +$("pt-lev").value,
          sl: lv.sl, tp: lv.tp, price, closeAt: f.target_candle_close * 1000, source: "auto"});
}
ptRender();

startLive();
if (!$("demo").checked) runAnalysis(false);
</script>
</body>
</html>
"""
