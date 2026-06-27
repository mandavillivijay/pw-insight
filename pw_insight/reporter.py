from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>pw-insight — Playwright Failure Report</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f172a;--card:#1e293b;--border:#334155;
  --text:#f1f5f9;--muted:#94a3b8;
  --blue:#3b82f6;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;
}
body{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh;padding:24px 32px}
h1{font-size:1.5rem;font-weight:700;margin-bottom:4px}
.subtitle{color:var(--muted);font-size:.875rem;margin-bottom:24px}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}
.stat-label{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.stat-value{font-size:2rem;font-weight:700}
.green{color:var(--green)} .red{color:var(--red)} .amber{color:var(--amber)}

.filter-bar{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:24px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
select,input[type=text]{background:#0f172a;border:1px solid var(--border);color:var(--text);border-radius:6px;padding:7px 12px;font-size:.875rem;outline:none;font-family:inherit}
select:focus,input:focus{border-color:var(--blue)}
input[type=text]{flex:1;min-width:200px}
.count-label{color:var(--muted);font-size:.875rem;white-space:nowrap;margin-left:auto}
.btn{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:7px 14px;font-size:.875rem;cursor:pointer;font-family:inherit}
.btn:hover{border-color:var(--text);color:var(--text)}

.table-wrap{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:24px}
table{width:100%;border-collapse:collapse;font-size:.85rem}
thead{background:#0f172a}
th{padding:11px 14px;text-align:left;color:var(--muted);font-weight:600;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;cursor:pointer;user-select:none;white-space:nowrap}
th:hover{color:var(--text)}
th .arr{margin-left:4px;opacity:.35}
th.active .arr{opacity:1}
td{padding:11px 14px;border-top:1px solid var(--border);vertical-align:top;line-height:1.45}
tr:hover td{background:#1a2540}
.cell-file{max-width:200px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-family:monospace;font-size:.78rem;vertical-align:bottom}
.cell-reason{color:var(--muted)}
.no-results{padding:48px;text-align:center;color:var(--muted)}

.badge{display:inline-block;border-radius:4px;padding:2px 9px;font-size:.72rem;font-weight:600;white-space:nowrap}
.b-Timeout{color:#f59e0b;background:#451a03}
.b-ElementNotFound{color:#ef4444;background:#450a0a}
.b-AssertionFailed{color:#3b82f6;background:#0c1a3a}
.b-NetworkError{color:#a855f7;background:#2e1065}
.b-AuthError{color:#f97316;background:#431407}
.b-ServerError{color:#ec4899;background:#500724}
.b-JSError{color:#14b8a6;background:#042f2e}
.b-VisualDiff{color:#84cc16;background:#1a2e05}
.b-Other{color:#94a3b8;background:#1e293b}

.insights{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:32px}
.panel{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px}
.panel h2{font-size:.9rem;font-weight:700;margin-bottom:16px}
.bar-row{margin-bottom:10px}
.bar-row:last-child{margin-bottom:0}
.bar-meta{display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:4px}
.bar-meta .bname{color:var(--text)}
.bar-meta .bcnt{color:var(--muted)}
.bar-track{height:6px;background:#334155;border-radius:3px}
.bar-fill{height:100%;background:var(--blue);border-radius:3px}
.ranked{list-style:none}
.ranked li{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:7px 0;border-top:1px solid var(--border);font-size:.8rem}
.ranked li:first-child{border-top:none;padding-top:0}
.ranked .rtxt{color:var(--muted);flex:1}
.ranked .rnum{color:var(--text);font-weight:700;white-space:nowrap}
footer{text-align:center;color:var(--muted);font-size:.75rem;padding-top:4px}
</style>
</head>
<body>
<h1>pw-insight</h1>
<p class="subtitle">Playwright failure analysis — offline, no API keys</p>

<div class="stats" id="stats"></div>

<div class="filter-bar">
  <select id="selOwner"><option value="">All owners</option></select>
  <select id="selCat"><option value="">All categories</option></select>
  <input type="text" id="txtSearch" placeholder="Search test name…"/>
  <select id="selSort">
    <option value="file">Sort: File</option>
    <option value="title">Sort: Test name</option>
    <option value="owner">Sort: Owner</option>
    <option value="category">Sort: Category</option>
  </select>
  <button class="btn" id="btnClear">Clear filters</button>
  <span class="count-label" id="countLabel"></span>
</div>

<div class="table-wrap">
  <table>
    <thead><tr>
      <th data-col="title">Test name<span class="arr">↕</span></th>
      <th data-col="file">File<span class="arr">↕</span></th>
      <th data-col="owner">Owner<span class="arr">↕</span></th>
      <th data-col="date">Last commit<span class="arr">↕</span></th>
      <th data-col="category">Category<span class="arr">↕</span></th>
      <th data-col="reason">Reason<span class="arr">↕</span></th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="no-results" id="noRes" style="display:none">No failures match the current filters.</div>
</div>

<div class="insights">
  <div class="panel"><h2>Failures by owner</h2><div id="ownerBars"></div></div>
  <div class="panel"><h2>Failures by category</h2><div id="catBars"></div></div>
  <div class="panel"><h2>Top 10 failure reasons</h2><ul class="ranked" id="reasonList"></ul></div>
</div>

<footer>Generated by pw-insight &mdash; fully local, no external dependencies</footer>

<script>
const D = %%PW_DATA%%;

const BC = {
  "Timeout":"b-Timeout","Element Not Found":"b-ElementNotFound",
  "Assertion Failed":"b-AssertionFailed","Network Error":"b-NetworkError",
  "Auth Error":"b-AuthError","Server Error":"b-ServerError",
  "JS Error":"b-JSError","Visual Diff":"b-VisualDiff","Other":"b-Other"
};
const esc = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

// stat cards
const statsEl = document.getElementById("stats");
const total = D.total, passed = D.passed, failed = D.failures.length;
const rate = total > 0 ? ((failed/total)*100).toFixed(1) : "0.0";
statsEl.innerHTML = `
  <div class="stat-card"><div class="stat-label">Total tests</div><div class="stat-value">${total.toLocaleString()}</div></div>
  <div class="stat-card"><div class="stat-label">Passed</div><div class="stat-value green">${passed.toLocaleString()}</div></div>
  <div class="stat-card"><div class="stat-label">Failed</div><div class="stat-value red">${failed.toLocaleString()}</div></div>
  <div class="stat-card"><div class="stat-label">Failure rate</div><div class="stat-value amber">${rate}%</div></div>`;

// populate selects
const selOwner = document.getElementById("selOwner");
const selCat = document.getElementById("selCat");
[...new Set(D.failures.map(f=>f.owner))].sort().forEach(o=>{
  const opt = document.createElement("option"); opt.value=opt.textContent=o; selOwner.appendChild(opt);
});
[...new Set(D.failures.map(f=>f.category))].sort().forEach(c=>{
  const opt = document.createElement("option"); opt.value=opt.textContent=c; selCat.appendChild(opt);
});

// sort state
let sortCol = "file", sortDir = 1;

function getFiltered(){
  const owner = selOwner.value, cat = selCat.value;
  const q = document.getElementById("txtSearch").value.toLowerCase();
  return D.failures.filter(f =>
    (!owner || f.owner===owner) &&
    (!cat || f.category===cat) &&
    (!q || f.title.toLowerCase().includes(q) || f.full_title.toLowerCase().includes(q))
  );
}

function sorted(arr){
  return [...arr].sort((a,b) => (a[sortCol]||"").localeCompare(b[sortCol]||"") * sortDir);
}

function updateHeaders(){
  document.querySelectorAll("th[data-col]").forEach(th=>{
    const arr = th.querySelector(".arr");
    if(th.dataset.col===sortCol){ th.classList.add("active"); arr.textContent = sortDir===1?"↑":"↓"; }
    else { th.classList.remove("active"); arr.textContent="↕"; }
  });
}

function render(){
  const data = sorted(getFiltered());
  updateHeaders();
  const tbody = document.getElementById("tbody");
  const noRes = document.getElementById("noRes");
  if(!data.length){ tbody.innerHTML=""; noRes.style.display=""; }
  else {
    noRes.style.display="none";
    tbody.innerHTML = data.map(f=>`<tr>
      <td>${esc(f.title)}</td>
      <td><span class="cell-file" title="${esc(f.file)}">${esc(f.file)}</span></td>
      <td>${esc(f.owner)}</td>
      <td style="white-space:nowrap;color:var(--muted);font-size:.8rem">${esc(f.date)}</td>
      <td><span class="badge ${BC[f.category]||"b-Other"}">${esc(f.category)}</span></td>
      <td class="cell-reason">${esc(f.reason)}</td>
    </tr>`).join("");
  }
  document.getElementById("countLabel").textContent = `Showing ${data.length} of ${D.failures.length} failures`;
}

document.querySelectorAll("th[data-col]").forEach(th=>th.addEventListener("click",()=>{
  sortCol===th.dataset.col ? sortDir*=-1 : (sortCol=th.dataset.col, sortDir=1);
  render();
}));
document.getElementById("selSort").addEventListener("change", e=>{ sortCol=e.target.value; sortDir=1; render(); });
selOwner.addEventListener("change", render);
selCat.addEventListener("change", render);
document.getElementById("txtSearch").addEventListener("input", render);
document.getElementById("btnClear").addEventListener("click",()=>{
  selOwner.value=selCat.value="";
  document.getElementById("txtSearch").value="";
  sortCol="file"; sortDir=1;
  document.getElementById("selSort").value="file";
  render();
});

// insights
function buildBars(id, entries){
  const el = document.getElementById(id);
  const max = Math.max(...entries.map(e=>e[1]),1);
  el.innerHTML = entries.map(([name,cnt])=>`
    <div class="bar-row">
      <div class="bar-meta"><span class="bname">${esc(name)}</span><span class="bcnt">${cnt}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${(cnt/max*100).toFixed(1)}%"></div></div>
    </div>`).join("");
}

const ownerCounts={}, catCounts={}, reasonCounts={};
D.failures.forEach(f=>{
  ownerCounts[f.owner]=(ownerCounts[f.owner]||0)+1;
  catCounts[f.category]=(catCounts[f.category]||0)+1;
  reasonCounts[f.reason]=(reasonCounts[f.reason]||0)+1;
});

buildBars("ownerBars", Object.entries(ownerCounts).sort((a,b)=>b[1]-a[1]));
buildBars("catBars", Object.entries(catCounts).sort((a,b)=>b[1]-a[1]));

const top10 = Object.entries(reasonCounts).sort((a,b)=>b[1]-a[1]).slice(0,10);
document.getElementById("reasonList").innerHTML = top10.map(([r,n])=>`
  <li><span class="rtxt">${esc(r)}</span><span class="rnum">${n}</span></li>`).join("");

render();
</script>
</body>
</html>"""


def generate_report(failures: list[dict[str, Any]], passed: int, total: int, output_path: str) -> None:
    payload: dict[str, Any] = {
        "total": total,
        "passed": passed,
        "failures": [
            {
                "file": f["file"],
                "title": f["title"],
                "full_title": f["full_title"],
                "owner": f["owner"],
                "email": f["email"],
                "date": f["date"],
                "category": f["category"],
                "reason": f["reason"],
                "error_message": f["error_message"],
            }
            for f in failures
        ],
    }
    html = _HTML.replace("%%PW_DATA%%", json.dumps(payload, ensure_ascii=False))
    Path(output_path).write_text(html, encoding="utf-8")
