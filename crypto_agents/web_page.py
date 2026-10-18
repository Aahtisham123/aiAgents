PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crypto Trading Agents</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--text:#16181d;--muted:#5d6472;--border:#e2e5ea;--accent:#2f5bea;
--long:#12805c;--short:#c4352b;--none:#6b7280;--warn-bg:#fff6e5;--warn:#8a5a00}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#181b21;--text:#e8eaee;--muted:#9aa2b1;
--border:#2a2f38;--accent:#7b9bff;--long:#3ccf95;--short:#ff6b5e;--none:#9aa2b1;--warn-bg:#2a2210;--warn:#f2c26b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:0 0 8px}
.sub{color:var(--muted);margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px}
form{display:flex;flex-wrap:wrap;gap:10px;align-items:end}
label{display:flex;flex-direction:column;font-size:12px;color:var(--muted);gap:4px}
input{font:inherit;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);width:140px}
button{font:inherit;padding:9px 16px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.secondary{background:transparent;color:var(--accent)}
button:disabled{opacity:.5;cursor:wait}
.check{flex-direction:row;align-items:center;gap:6px;padding-bottom:9px}.check input{width:auto}
.action{font-size:30px;font-weight:700;letter-spacing:.5px}
.LONG{color:var(--long)}.SHORT{color:var(--short)}.NO{color:var(--none)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px}
.kv{background:var(--bg);border-radius:8px;padding:8px 10px}.kv b{display:block;font-size:12px;color:var(--muted);font-weight:500}
ul{margin:6px 0 0;padding-left:18px}li{margin:2px 0}
.agent-head{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.pill{font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.BULLISH{color:var(--long)}.BEARISH{color:var(--short)}.NEUTRAL{color:var(--none)}
.bar{height:6px;background:var(--border);border-radius:3px;margin:8px 0;position:relative;overflow:hidden}
.bar span{position:absolute;top:0;bottom:0}
.warn{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:10px 12px;margin-top:12px}
.disclaimer{font-size:13px;color:var(--muted)}
.err{color:var(--short)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--border)}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
.scroll{overflow-x:auto}
</style>
</head>
<body>
<main>
<h1>Crypto Trading Agents</h1>
<p class="sub">Five analysts (trend, momentum, price action and volume, sentiment, risk) vote, and a chief strategist makes the call.</p>

<div class="card">
<form id="f">
<label>Symbol<input id="symbol" value="BTCUSDT" autocomplete="off"></label>
<label>Account (USDT)<input id="account" type="number" value="1000" min="1" step="any"></label>
<label>Risk per trade %<input id="risk" type="number" value="1" step="any" min="0.05" max="10"></label>
<label class="check"><input id="demo" type="checkbox">Demo data</label>
<button id="go" type="submit">Analyze</button>
<button id="scan" type="button" class="secondary">Scan top coins</button>
</form>
</div>

<div id="out"></div>
<p class="disclaimer">Not financial advice. No signal is 100% accurate, and every trade can lose. Always use the stop-loss and only risk money you can afford to lose.</p>
</main>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = x => x == null ? "–" : (Math.abs(x) >= 1 ? x.toLocaleString(undefined,{maximumFractionDigits:2}) : x.toPrecision(5));
const params = extra => new URLSearchParams({account:$("account").value, risk:$("risk").value,
  demo:$("demo").checked ? "1" : "0", ...extra});

async function call(url, btn){
  document.querySelectorAll("button").forEach(b => b.disabled = true);
  $("out").innerHTML = '<div class="card">The agents are analyzing the market…</div>';
  try {
    const r = await fetch(url); const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.statusText);
    return j;
  } catch(e){ $("out").innerHTML = `<div class="card err">${esc(e.message)}</div>`; }
  finally { document.querySelectorAll("button").forEach(b => b.disabled = false); }
}

function bar(score){
  const w = Math.abs(score) * 50, left = score >= 0 ? 50 : 50 - w;
  const color = score > 0.15 ? "var(--long)" : score < -0.15 ? "var(--short)" : "var(--none)";
  return `<div class="bar"><span style="left:${left}%;width:${w}%;background:${color}"></span></div>`;
}

function renderDecision(d){
  const cls = d.action === "NO TRADE" ? "NO" : d.action;
  let h = `<div class="card"><h2>${esc(d.symbol)}: Chief Strategist</h2>
    <div class="action ${cls}">${esc(d.action)}</div>
    <div class="grid"><div class="kv"><b>Combined score</b>${d.score.toFixed(2)}</div>
    <div class="kv"><b>Setup quality (not win %)</b>${d.setup_quality}/100</div></div>
    <ul>${d.reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul>`;
  if (d.plan){
    const p = d.plan, pct = Math.abs(p.entry - p.stop_loss) / p.entry * 100;
    h += `<div class="grid">
      <div class="kv"><b>Entry</b>${num(p.entry)}</div>
      <div class="kv"><b>Stop-loss (${pct.toFixed(2)}%)</b>${num(p.stop_loss)}</div>
      ${p.take_profits.map((t,i) => `<div class="kv"><b>Take-profit ${i+1} (${[1.5,2.5,4][i]}R)</b>${num(t)}</div>`).join("")}
      <div class="kv"><b>Position size</b>${p.position_size.toPrecision(5)} (${num(p.position_value)} USDT)</div>
      <div class="kv"><b>Max loss</b>${num(p.risk_amount)} USDT</div></div>
      <p class="disclaimer">Take partial profit at TP1 and move the stop to break-even.</p>`;
  }
  if (d.warnings.length) h += `<div class="warn"><b>Warnings</b><ul>${d.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul></div>`;
  h += `</div>`;
  for (const r of d.reports){
    const risk = r.agent === "Risk Manager";
    h += `<div class="card"><div class="agent-head"><h2>${esc(r.agent)}</h2>
      ${risk ? "" : `<span class="pill ${r.bias}">${r.bias} ${r.score >= 0 ? "+" : ""}${r.score.toFixed(2)}</span>`}</div>
      <div>${esc(r.summary)} <span class="disclaimer">· confidence ${Math.round(r.confidence*100)}%</span></div>
      ${risk ? "" : bar(r.score)}
      <ul>${r.reasons.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
  }
  $("out").innerHTML = h;
}

function renderScan(j){
  const rows = j.results.map(r => r.error
    ? `<tr><td>${esc(r.symbol)}</td><td class="err" colspan="6">${esc(r.error)}</td></tr>`
    : `<tr><td><a href="#" data-s="${esc(r.symbol)}">${esc(r.symbol)}</a></td>
       <td class="${r.action === "NO TRADE" ? "NO" : r.action}">${esc(r.action)}</td>
       <td>${r.score.toFixed(2)}</td><td>${r.setup_quality}</td><td>${num(r.entry)}</td>
       <td>${num(r.stop_loss)}</td><td>${num(r.take_profit_1)}</td></tr>`).join("");
  $("out").innerHTML = `<div class="card"><h2>Scan results</h2><div class="scroll"><table>
    <tr><th>Symbol</th><th>Action</th><th>Score</th><th>Quality</th><th>Entry</th><th>Stop</th><th>TP1</th></tr>
    ${rows}</table></div><p class="disclaimer">Click a symbol to see each agent's reasoning.</p></div>`;
  $("out").querySelectorAll("a[data-s]").forEach(a => a.onclick = e => {
    e.preventDefault(); $("symbol").value = a.dataset.s; $("f").requestSubmit(); });
}

$("f").onsubmit = async e => {
  e.preventDefault();
  const d = await call("/api/analyze?" + params({symbol: $("symbol").value.trim()}));
  if (d) renderDecision(d);
};
$("scan").onclick = async () => { const j = await call("/api/scan?" + params({})); if (j) renderScan(j); };
</script>
</body>
</html>
"""
