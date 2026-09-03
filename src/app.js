(() => {
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ord = n => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th","st","nd","rd"][n % 10] || "th");
const sgn = (v, d = 1) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
const VIT = "#2563eb", WARM = "#c2410c", OTHER = "#b8b3a8", INK3 = "#5d5949", RULE = "#eeedeb";

/* ---------- tooltip ---------- */
const tip = $("#tip");
function showTip(html, ev) { tip.innerHTML = html; tip.style.opacity = 1; moveTip(ev); }
function moveTip(ev) {
  const x = ev.clientX + 14, y = ev.clientY + 14, w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = (x + w > innerWidth - 12 ? ev.clientX - w - 14 : x) + "px";
  tip.style.top = (y + h > innerHeight - 12 ? ev.clientY - h - 14 : y) + "px";
}
function hideTip() { tip.style.opacity = 0; }
function bindTips(root) {
  root.querySelectorAll("[data-tip]").forEach(el => {
    el.addEventListener("mouseenter", e => showTip(el.dataset.tip, e));
    el.addEventListener("mousemove", moveTip);
    el.addEventListener("mouseleave", hideTip);
  });
}

/* ---------- rank chart (animated re-sort) ---------- */
function rankChart(el, data, cfg) {
  const H = 24, rows = data.map((d, i) => ({ d, i }));
  el.style.height = data.length * H + "px";
  el.innerHTML = rows.map(({ d, i }) => `
    <div class="rk-row${d.vit ? " vit" : ""}" data-i="${i}">
      <span class="rank"></span>
      <span class="name">${esc(d.name)}${d.reserve ? "<small>reserve</small>" : ""}</span>
      <span class="track"><span class="bar"></span></span>
      <span class="val"></span>
    </div>`).join("") + `<div class="zero" hidden></div><div class="cut" hidden><i></i></div>`;
  const zero = $(".zero", el), cut = $(".cut", el);
  function update(key) {
    const m = cfg.metrics[key];
    const vals = data.map(d => d[key]);
    const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
    const centered = lo < 0;
    const order = data.map((d, i) => i).sort((a, b) => vals[b] - vals[a] || (data[a].tie || 0) - (data[b].tie || 0));
    const pos = []; order.forEach((i, r) => pos[i] = r);
    const trackW = $(".track", el).getBoundingClientRect().width || 400;
    const z = centered ? (-lo / (hi - lo)) * trackW : 0;
    const scale = centered ? trackW / (hi - lo) : trackW / hi;
    rows.forEach(({ d, i }) => {
      const row = el.children[i], v = vals[i];
      row.style.transform = `translateY(${pos[i] * H}px)`;
      $(".rank", row).textContent = ord(pos[i] + 1);
      $(".val", row).textContent = m.fmt(v);
      const bar = $(".bar", row);
      const w = Math.abs(v) * scale;
      bar.className = "bar" + (v < 0 ? " neg" : "");
      bar.style.left = (v < 0 ? z - w : z) + "px"; bar.style.width = Math.max(w, 1) + "px";
    });
    zero.hidden = !centered; zero.style.left = `calc(${(28 + 130 + 20)}px + ${z}px)`;
    if (m.cut) { cut.hidden = false; cut.style.top = m.cut * H - 0.5 + "px"; $("i", cut).textContent = m.cutLabel; } else cut.hidden = true;
    if (cfg.caption) cfg.caption(key);
  }
  return update;
}

/* Level chart */
const levelMetrics = {
  published: { fmt: v => v, cut: 8, cutLabel: "play-off line" },
  pts: { fmt: v => v, cut: 8, cutLabel: "play-off line" },
  xpts: { fmt: v => v.toFixed(1), cut: 8, cutLabel: "play-off line" },
  xgd: { fmt: v => sgn(v, 1) },
};
const levelCaps = {
  published: "The official table: Vitesse 15th on 44 points after the 12-point deduction confirmed by the KNVB on 9 July 2025. Only Vitesse were deducted in 2025/26.",
  pts: "Points earned on the pitch. At 56, Vitesse finish 7th on goal difference (+9 against Jong PSV’s +2) and take the last play-off place from Roda JC.",
  xpts: "Expected points from the independent xG model: 53.7, ranked 10th. The licensed model gives 52.1, ranked 11th. Vitesse earned two to four points more than their chances deserved — about one result.",
  xgd: "xG difference over the season, independent model: +2.8, ranked 10th of 20. The licensed model gives −0.8 — also 10th, a rank derived from its xG-for and xG-against pages. The two models disagree on level and agree on rank.",
};
const dl = D.clubs.map(c => ({ ...c, tie: c.vit ? 0 : 1 }));
const updLevel = rankChart($("#c-level"), dl, { metrics: levelMetrics, caption: k => $("#cap-level").textContent = levelCaps[k] });
updLevel("published");
$("#seg-level").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return;
  $("#seg-level .on").classList.remove("on"); b.classList.add("on"); updLevel(b.dataset.k); });

/* methods table */
$("#t-methods").innerHTML = `<thead><tr><th>Method</th><th class="r">xG difference</th><th class="r">Rank</th><th class="r">Expected points</th><th class="r">Points − expected</th><th class="r">Rank</th></tr></thead><tbody>` +
  D.methods.map(m => `<tr><td>${m.name}<span class="sub">${m.note}</span></td><td class="r">${m.xgd}</td><td class="r">${m.xgdRank}</td><td class="r">${m.xpts}</td><td class="r sig">${m.resid}</td><td class="r">${m.residRank}</td></tr>`).join("") + "</tbody>";

/* ---------- SVG helpers ---------- */
const svg = (w, h, inner, cls = "") => `<svg viewBox="0 0 ${w} ${h}" class="${cls}" role="img">${inner}</svg>`;

/* six seasons */
(function () {
  const W = 500, H = 250, L = 44, R = 12, T = 30, B = 46, pw = W - L - R, ph = H - T - B;
  const s = D.seasons, lo = -1, hi = 0.3, y = v => T + (hi - v) / (hi - lo) * ph, bw = pw / s.length;
  let g = `<g class="grid">${[0.2, 0, -0.2, -0.4, -0.6, -0.8].map(v => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>`).join("")}</g>`;
  g += `<g class="ax">${[0.2, 0, -0.2, -0.4, -0.6, -0.8].map(v => `<text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${sgn(v, 1)}</text>`).join("")}</g>`;
  g += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="${INK3}" stroke-width="1"/>`;
  // division band
  const kkd0 = L + 4 * bw;
  g += `<rect x="${kkd0}" y="${T - 18}" width="${2 * bw}" height="${ph + 18}" fill="#eeedeb" opacity=".55"/>`;
  g += `<text x="${L + 2 * bw}" y="${T - 6}" text-anchor="middle" font-size="10.5" fill="${INK3}" letter-spacing=".08em">EREDIVISIE</text><text x="${kkd0 + bw}" y="${T - 6}" text-anchor="middle" font-size="10.5" fill="${INK3}" letter-spacing=".08em">EERSTE DIVISIE</text>`;
  s.forEach((d, i) => {
    const x = L + i * bw + bw * 0.22, w = bw * 0.56, y0 = y(0), y1 = y(d.xgd);
    const top = Math.min(y0, y1), h = Math.abs(y0 - y1);
    g += `<rect x="${x}" y="${top}" width="${w}" height="${Math.max(h, 1.5)}" fill="${d.xgd >= 0 ? VIT : WARM}" rx="2" data-tip="<b>${d.s} · ${d.div}</b><span class='t'>xGD ${sgn(d.xgd, 3)} per match · ranked ${ord(d.rank)} of ${d.of}</span><span class='t'>Official ${ord(d.official)}${d.deduct ? " after a " + d.deduct + "-point deduction" : ""}</span>"/>`;
    g += `<text x="${x + w / 2}" y="${d.xgd >= 0 ? y1 - 6 : y1 + 13}" text-anchor="middle" font-size="11.5" font-weight="600" fill="${d.xgd >= 0 ? VIT : WARM}">${ord(d.rank)}</text>`;
    g += `<text x="${x + w / 2}" y="${H - B + 16}" text-anchor="middle" font-size="11" fill="${INK3}">${d.s}</text>`;
    g += `<text x="${x + w / 2}" y="${H - B + 30}" text-anchor="middle" font-size="10.5" fill="${INK3}">${d.deduct ? "−" + d.deduct + " pts" : ""}</text>`;
  });
  $("#c-seasons").innerHTML = svg(W, H, g);
})();

/* residuals: two small multiples */
(function () {
  const W = 500, H = 250, L = 44, R = 12, T = 30, B = 40, pw = (W - L - R - 24) / 2, ph = H - T - B;
  const lo = -0.5, hi = 0.2, y = v => T + (hi - v) / (hi - lo) * ph;
  const panel = (x0, key, title) => {
    const bw = pw / 4; let g = `<text x="${x0}" y="${T - 10}" font-size="12" font-weight="500" fill="#313131">${title}</text>`;
    g += `<g class="grid">${[0.1, 0, -0.1, -0.2, -0.3, -0.4].map(v => `<line x1="${x0}" x2="${x0 + pw}" y1="${y(v)}" y2="${y(v)}"/>`).join("")}</g>`;
    g += `<line x1="${x0}" x2="${x0 + pw}" y1="${y(0)}" y2="${y(0)}" stroke="${INK3}"/>`;
    D.residuals.forEach((d, i) => {
      const v = d[key], x = x0 + i * bw + bw * 0.2, w = bw * 0.6, y0 = y(0), y1 = y(v);
      g += `<rect x="${x}" y="${Math.min(y0, y1)}" width="${w}" height="${Math.max(Math.abs(y0 - y1), 1.5)}" fill="${v >= 0 ? VIT : WARM}" rx="2" data-tip="<b>${d.s}</b><span class='t'>${title}: ${sgn(v, 3)} per match</span>"/>`;
      g += `<text x="${x + w / 2}" y="${v >= 0 ? y1 - 5 : y1 + 12}" text-anchor="middle" font-size="10.5" fill="${v >= 0 ? VIT : WARM}">${sgn(v, 2)}</text>`;
      g += `<text x="${x + w / 2}" y="${H - B + 16}" text-anchor="middle" font-size="10.5" fill="${INK3}">${d.s}</text>`;
    });
    return g;
  };
  let g = `<g class="ax">${[0.1, 0, -0.1, -0.2, -0.3, -0.4].map(v => `<text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${sgn(v, 1)}</text>`).join("")}</g>`;
  g += panel(L, "fin", "Finishing (goals − xG)") + panel(L + pw + 24, "prev", "Prevention (xGA − conceded)");
  $("#c-resid").innerHTML = svg(W, H, g);
})();

/* phases */
$("#c-phases").innerHTML = D.phases.map(p => {
  const pct = (p.rank - 1) / 19 * 100, good = p.rank <= 8;
  return `<div class="phase"><div class="pn">${p.name}</div>
    <div class="ptrack${good ? " good" : ""}"><i class="pfill" style="width:${pct}%"></i><i class="pdot" style="left:${pct}%"></i></div>
    <div class="pr"><b>${ord(p.rank)}</b> of 20</div><div class="why">${p.why}</div></div>`;
}).join("");

/* style tables */
function styleTable(id, rows, withP) {
  $(id).innerHTML = `<thead><tr><th></th><th class="r">Vitesse</th><th class="r">Opponents</th>${withP ? '<th class="r">p</th>' : ""}</tr></thead><tbody>` +
    rows.map(r => `<tr><td>${r[0]}${r[1] ? `<span class="sub">${r[1]}</span>` : ""}</td><td class="r vit">${r[2]}</td><td class="r">${r[3]}</td>${withP ? `<td class="r ${parseFloat(r[4]) < 0.05 ? "sig" : "muted"}">${r[4]}</td>` : ""}</tr>`).join("") + "</tbody>";
}
styleTable("#t-styleA", D.styleA, true); styleTable("#t-styleB", D.styleB, false);

/* set pieces */
const spMetrics = { corner: { fmt: v => sgn(v, 2) }, sp: { fmt: v => sgn(v, 2) }, ifk: { fmt: v => v.toFixed(2) } };
const spCaps = {
  corner: "Corner xG difference, 2025/26. Vitesse 12th of 20 at −0.98, the hole. Willem II sit at +6.86 on corners alone; the +3.6 plan is half the all-set-piece gap to their +9.63.",
  sp: "All set pieces: corners, direct and indirect free kicks. Vitesse 6th of 20 at +2.52. The definition matters — throw-ins and penalties are excluded and would change the numbers.",
  ifk: "Expected goals for from indirect free kicks. Vitesse first in the division at 6.24 — the club can already coach a dead ball. The volume line is free kicks, not corners: more than twice the league share at indirect free kicks, 185 to 178 at corners.",
};
const updSP = rankChart($("#c-sp"), D.setpieces, { metrics: spMetrics, caption: k => $("#cap-sp").textContent = spCaps[k] });
updSP("corner");
$("#seg-sp").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return;
  $("#seg-sp .on").classList.remove("on"); b.classList.add("on"); updSP(b.dataset.k); });

$("#t-spseasons").innerHTML = `<thead><tr><th>Season</th><th>Div</th><th class="r">Set-piece xGD</th><th class="r">Rank</th><th class="r">Corner xGD</th><th class="r">Rank</th><th class="r">Indirect FK xG for</th><th class="r">Rank</th></tr></thead><tbody>` +
  D.spSeasons.map(s => `<tr${s.season === "2025-26" ? ' class="hl"' : ""}><td>${s.season}</td><td class="muted">${s.div}</td><td class="r">${sgn(s.sp, 2)}</td><td class="r ${s.sp_rank <= 6 ? "sig" : ""}">${s.sp_rank}</td><td class="r">${sgn(s.corner, 2)}</td><td class="r ${s.corner_rank > 10 ? "dn" : "sig"}">${s.corner_rank}</td><td class="r">${s.ifk.toFixed(2)}</td><td class="r ${s.ifk_rank <= 3 ? "sig" : ""}">${s.ifk_rank}</td></tr>`).join("") + "</tbody>";

$("#t-persist").innerHTML = `<thead><tr><th>Persistence of…</th><th class="r">Eerste Divisie<span class="sub">n = 85</span></th><th class="r">Eredivisie<span class="sub">n = 75</span></th><th class="r">Pooled<span class="sub">n = 160</span></th></tr></thead><tbody>` +
  D.persistence.map((r, i) => `<tr><td${i >= 3 ? ' class="muted"' : ""}>${r[0]}</td><td class="r ${i === 0 ? "sig" : ""}">${r[1]}</td><td class="r">${r[2]}</td><td class="r ${i === 0 || i === 4 ? "sig" : ""}">${r[3]}</td></tr>`).join("") + "</tbody>";

$("#c-bands").innerHTML = D.bands.map(b => {
  const r = b.top8 / b.n * 100;
  return `<div class="band${b.here ? " here" : ""}${b.target ? " target" : ""}"><div class="bl">${b.band}${b.here ? " · Vitesse" : ""}${b.target ? " · target" : ""}</div><div class="bt"><div class="bb" style="width:${r}%"></div></div><div class="bv">${b.top8} of ${b.n} · ${Math.round(r)}%</div></div>`;
}).join("");

/* scatter */
(function () {
  const W = 860, H = 540, L = 52, R = 20, T = 18, B = 46, pw = W - L - R, ph = H - T - B;
  const xmax = 0.75, ymax = 0.6, x = v => L + Math.min(v, xmax) / xmax * pw, y = v => T + ph - Math.min(v, ymax) / ymax * ph;
  let g = `<g class="grid">${[0.1, 0.2, 0.3, 0.4, 0.5, 0.6].map(v => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>`).join("")}${[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7].map(v => `<line y1="${T}" y2="${T + ph}" x1="${x(v)}" x2="${x(v)}"/>`).join("")}</g>`;
  g += `<g class="ax">${[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6].map(v => `<text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${v.toFixed(1)}</text>`).join("")}${[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7].map(v => `<text x="${x(v)}" y="${T + ph + 18}" text-anchor="middle">${v.toFixed(1)}</text>`).join("")}</g>`;
  g += `<text x="${L + pw / 2}" y="${H - 8}" text-anchor="middle" font-size="12" fill="${INK3}">non-penalty xG per 90</text>`;
  g += `<text transform="translate(14 ${T + ph / 2}) rotate(-90)" text-anchor="middle" font-size="12" fill="${INK3}">expected assists per 90</text>`;
  const mx = x(D.npxgMedian);
  g += `<line x1="${mx}" x2="${mx}" y1="${T}" y2="${T + ph}" stroke="${INK3}" stroke-dasharray="3 3" opacity=".6"/><text x="${mx + 5}" y="${T + 12}" font-size="10.5" fill="${INK3}">league median</text>`;
  const others = D.players.filter(p => !p.v), vit = D.players.filter(p => p.v);
  const dot = (p, r, fill, ring) => `<circle cx="${x(p.x)}" cy="${y(p.y)}" r="${r}" fill="${fill}" ${ring ? 'stroke="#fff" stroke-width="1.5"' : ""} opacity="${p.v ? 1 : .6}"/><circle cx="${x(p.x)}" cy="${y(p.y)}" r="9" fill="transparent" data-tip="<b>${esc(p.n)}</b><span class='t'>${esc(p.t)} · ${p.m.toLocaleString()} min</span><span class='t'>NPxG/90 ${p.x.toFixed(2)} · xA/90 ${p.y.toFixed(2)}</span><span class='t'>Expected goal involvement ${p.gi.toFixed(2)}, ${ord(p.rk)} of 355</span>"/>`;
  g += others.map(p => dot(p, 3.4, OTHER, false)).join("");
  // label the notable non-Vitesse points
  others.filter(p => p.x > 0.5 || p.y > 0.4).forEach(p => { g += `<text x="${x(p.x) + 7}" y="${y(p.y) + 4}" font-size="10.5" fill="${INK3}">${esc(p.n)} (${esc(p.t)})</text>`; });
  g += vit.map(p => dot(p, 5.5, VIT, true)).join("");
  vit.filter(p => p.gi >= 0.28).forEach(p => { g += `<text class="lbl" x="${x(p.x) + 9}" y="${y(p.y) + 4}">${esc(p.n)}</text>`; });
  $("#c-scatter").innerHTML = svg(W, H, g);
})();

/* Vitesse table */
const LEFT = { "A. Tahaui": "left", "D. Hoogewerf": "left", "E. Huth": "left" };
$("#t-vit").innerHTML = `<thead><tr><th>Player</th><th class="r">xGI per 90</th><th class="r">Rank of 355</th><th class="r">NPxG per 90</th><th class="r">xA per 90</th><th class="r">Minutes</th></tr></thead><tbody>` +
  D.players.filter(p => p.v && p.rk <= 200).map(p => `<tr><td>${esc(p.n)}${LEFT[p.n] ? ' <span class="muted">(left)</span>' : ""}</td><td class="r ${p.rk <= 50 ? "sig" : ""}">${p.gi.toFixed(3)}</td><td class="r">${ord(p.rk)}</td><td class="r">${p.x.toFixed(3)}</td><td class="r">${p.y.toFixed(3)}</td><td class="r">${p.m.toLocaleString()}</td></tr>`).join("") + "</tbody>";

const butt = D.players.find(p => p.n === "A. Büttner");
$("#buttner-big").innerHTML = `${ord(butt ? butt.rxt : 32)}<i>of 355 on ball progression</i>`;

/* fixtures */
$("#fixtures").innerHTML = D.fixtures.map(f => `<div><div class="d">${f.date} · ${f.ha === "H" ? "home" : "away"} · ${f.shape}</div><div class="o">${f.ha === "H" ? "Vitesse – " + f.opp : f.opp + " – Vitesse"}</div><div class="s">${f.ha === "H" ? f.gf + "–" + f.ga : f.ga + "–" + f.gf}</div><div class="x">xG ${f.ha === "H" ? `<b>${f.xg.toFixed(2)}</b> – ${f.xga.toFixed(2)}` : `${f.xga.toFixed(2)} – <b>${f.xg.toFixed(2)}</b>`}</div><div class="n">${f.note}</div></div>`).join("");

/* shift table */
$("#t-shift").innerHTML = `<thead><tr><th>per match</th><th class="r">2025/26</th><th class="r">2026/27</th><th></th></tr></thead><tbody>` +
  D.shift.map(r => `<tr><td>${r[0]}</td><td class="r">${r[1]}</td><td class="r vit">${r[2]}</td><td class="${r[3] > 0 ? "up" : "dn"}">${r[3] > 0 ? "as recommended" : "the other way"}</td></tr>`).join("") + "</tbody>";

/* pitch */
(function () {
  const xi = D.xi4, W = 300, H = 400;
  const spots = [[150, 372], [258, 300], [186, 300], [114, 300], [42, 300], [150, 232], [82, 178], [218, 178], [250, 92], [50, 92], [150, 62]];
  let g = `<rect x="6" y="6" width="288" height="388" rx="6" fill="#f5f5f5" stroke="#e2e1df"/><line x1="6" x2="294" y1="200" y2="200" stroke="#e2e1df"/><circle cx="150" cy="200" r="36" fill="none" stroke="#e2e1df"/><rect x="72" y="6" width="156" height="58" fill="none" stroke="#e2e1df"/><rect x="72" y="336" width="156" height="58" fill="none" stroke="#e2e1df"/>`;
  xi.forEach((n, i) => { const [cx, cy] = spots[i]; g += `<circle cx="${cx}" cy="${cy}" r="9" fill="${VIT}"/><text x="${cx}" y="${cy + 24}" text-anchor="middle">${esc(n)}</text>`; });
  $("#c-pitch").innerHTML = svg(W, H, g);
})();

/* signings */
$("#signings-grid").innerHTML = D.signings.map(s => `<div class="card"><div class="top"><h4>${esc(s.name)}</h4><span class="pos">${s.age} · ${s.pos}</span></div>
  <dl><dt>From</dt><dd>${esc(s.from)} · ${s.when}</dd><dt>Prior sample</dt><dd>${s.sample}<span class="sub" style="display:block;color:#5d5949;font-size:12px">${s.league}</span></dd><dt>So far</dt><dd>${s.sofar}</dd><dt>Contract</dt><dd>${s.contract} · Transfermarkt value ${s.value}</dd></dl>
  <p class="read">${s.read}</p><p class="verdict">${s.verdict}</p></div>`).join("");
$("#departures").innerHTML = D.departures.map(d => `<div class="dep"><b>${esc(d.name)} <span class="muted" style="font-weight:400;color:#5d5949">${d.pos}</span></b><span class="l">${d.lost}</span><span class="n">${d.note}</span></div>`).join("");

/* scouting: radar + facet tables, one block per player */
function radarSVG(facets, pool, keyIdx) {
  const W = 600, H = 350, cx = 300, cy = 172, R = 112, n = facets.length;
  const ang = i => -Math.PI / 2 + i * 2 * Math.PI / n, pt = (i, r) => [cx + Math.cos(ang(i)) * r, cy + Math.sin(ang(i)) * r];
  const pc = f => Math.round((pool - f.rank) / pool * 100);
  let g = "";
  [25, 50, 75, 100].forEach(v => { g += `<polygon points="${facets.map((_, i) => pt(i, R * v / 100).join(",")).join(" ")}" fill="none" stroke="${RULE}"/>`; });
  facets.forEach((_, i) => { const [x, y] = pt(i, R); g += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="${RULE}"/>`; });
  g += `<text x="${cx + 4}" y="${cy - R * 0.5 + 4}" font-size="9.5" fill="${INK3}">50th</text>`;
  g += `<polygon points="${facets.map((f, i) => pt(i, R * pc(f) / 100).join(",")).join(" ")}" fill="${VIT}" fill-opacity=".12" stroke="#090909" stroke-width="1.5"/>`;
  facets.forEach((f, i) => {
    const [x, y] = pt(i, R * pc(f) / 100), [lx, ly] = pt(i, R + 20), key = keyIdx.includes(i);
    g += `<circle cx="${x}" cy="${y}" r="${key ? 5 : 3.5}" fill="${key ? VIT : "#090909"}" stroke="#fff" stroke-width="1.5" data-tip="<b>${f.name}</b><span class='t'>${ord(f.rank)} of ${pool} · ≈${pc(f)}th percentile</span>"/>`;
    const anchor = Math.abs(lx - cx) < 8 ? "middle" : lx > cx ? "start" : "end";
    g += `<text x="${lx}" y="${ly + 4}" text-anchor="${anchor}" font-size="11" ${key ? `font-weight="600" fill="${VIT}"` : `fill="#313131"`}>${f.name} <tspan fill="${INK3}" font-weight="400">${f.rank}</tspan></text>`;
  });
  return svg(600, 350, g);
}
const SC_KEY = { wouters: ["Defensive Heading", "Aerial Threat"], dahbo: ["Involvement", "Pressing"], decarvalho: ["Effectiveness", "Pressing"] };
$("#sc-blocks").innerHTML = D.scouting.map(p => {
  const keyIdx = p.facets.map((f, i) => SC_KEY[p.key].includes(f.name) ? i : -1).filter(i => i >= 0);
  const rows = p.facets.map(f => `<tr><td><b>${f.name}</b><span class="sub">${f.zone ? "Zone read: " + esc(f.zone) : "No zone map"}</span></td><td class="r ${f.rank <= Math.ceil(p.pool / 4) ? "sig" : f.rank > p.pool * 0.75 ? "dn" : ""}">${ord(f.rank)} of ${p.pool}</td><td>${f.metrics.map(m => `<span class="mt"><span>${esc(m[0])}</span><b>${esc(m[1])}</b><i>${ord(m[2])}</i></span>`).join("")}</td></tr>`).join("");
  return `<div class="sc">
    <div class="sc-head"><div><h4>${esc(p.name)}</h4><div class="sub">${esc(p.role)}</div></div><div class="sc-meta"><span>${esc(p.sample)}</span><span>Compared with ${esc(p.poolLabel)}</span></div></div>
    <div class="split" style="margin-top:14px">
      <div class="fig chart" style="margin:0"><div class="fig-head"><div><h4>Nine facets, as ranked</h4><div class="sub">Twelve Earpiece · implied percentile from rank of ${p.pool} · the two that matter to Vitesse in blue</div></div></div>${radarSVG(p.facets, p.pool, keyIdx)}</div>
      <div class="sc-notes"><h5>What the data supports</h5><p>${p.shows}</p><h5>What it cannot</h5><p>${p.cannot}</p><h5>Where the vendor’s text fails its own table</h5><p>${p.prose}</p><h5>Fit to how Vitesse are playing now</h5><p>${p.fit}</p></div>
    </div>
    <div class="fig" style="margin-top:20px"><div class="fig-head"><div><h4>Every metric behind the facets</h4><div class="sub">Value · rank of ${p.pool}. Definitions are the vendor’s; values are per-match, possession-adjusted where the glossary says so.</div></div></div>
      <div class="tab-wrap"><table class="tab sc-tab"><thead><tr><th>Facet</th><th class="r">Rank</th><th>Metrics</th></tr></thead><tbody>${rows}</tbody></table></div></div>
  </div>`;
}).join("");

/* profile: style fit */
$("#c-stylefit").innerHTML = D.profile.style.map(s => `<div class="sf"><div class="sf-h">${s[0]}</div>
  <div class="sf-row"><span class="sf-l">${s[1]}</span><div class="sf-track"><i class="sf-mid"></i><i class="sf-v" style="left:${s[3]}%" data-tip="<b>Vitesse</b><span class='t'>${s[0]}: ${s[3]} from ${s[1].toLowerCase()} toward ${s[2].toLowerCase()}</span>"></i><i class="sf-r" style="left:${s[4]}%" data-tip="<b>RKC Waalwijk</b><span class='t'>${s[0]}: ${s[4]} from ${s[1].toLowerCase()} toward ${s[2].toLowerCase()}</span>"></i></div><span class="sf-l r">${s[2]}</span></div></div>`).join("") +
  `<div class="legend"><span><i style="background:var(--vit);border-radius:50%"></i>Vitesse</span><span><i style="background:var(--ink)"></i>RKC Waalwijk</span></div>`;


bindTips(document);
addEventListener("resize", () => { updLevel($("#seg-level .on").dataset.k); updSP($("#seg-sp .on").dataset.k); });

/* nav */
const links = [...document.querySelectorAll(".rail a")];
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id)); } }), { rootMargin: "-20% 0px -70% 0px" });
document.querySelectorAll("main section").forEach(s => io.observe(s));
})();
