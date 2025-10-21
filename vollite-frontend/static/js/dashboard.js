// Helpers
function setRisk(value) {
  value = Math.max(0, Math.min(100, value|0));
  const ring = document.getElementById("riskMeter");
  const valEl = document.getElementById("riskValue");
  valEl.textContent = value + "%";

  // color stops: 0-50 green, 50-80 yellow, 80-100 red
  const greenStop = Math.min(value, 50) / 100 * 100;
  const yellowStop = value <= 50 ? 0 : Math.min(value-50, 30) / 30 * 100;
  const redStop = value <= 80 ? 0 : (value-80) / 20 * 100;

  // Build conic gradient such that the filled angle matches value
  // Simple approach: base is gray, then overlay a single hue from 0 to value
  // But we want smooth green->yellow->red. We'll interpolate stops.
  let color;
  if (value < 50) color = "var(--ok)";
  else if (value < 80) color = "var(--warn)";
  else color = "var(--danger)";
  ring.style.background = `conic-gradient(${color} ${value*3.6}deg, #1a2032 0deg)`;
}

function makeTree(container, node) {
  container.innerHTML = "";
  const ul = document.createElement("ul");
  function rec(n, parent) {
    const li = document.createElement("li");
    const badge = document.createElement("span");
    badge.className = "badge " + (n.risk || "Low");
    badge.textContent = n.risk || "Low";

    const label = document.createElement("span");
    label.className = "node";
    label.innerHTML = `<span>${n.name}</span>`;
    label.prepend(badge);
    li.appendChild(label);

    if (n.children && n.children.length) {
      const childUl = document.createElement("ul");
      n.children.forEach(c => rec(c, childUl));
      li.appendChild(childUl);
    }
    parent.appendChild(li);
  }
  rec(node, ul);
  container.appendChild(ul);
}

async function analyze(formDataOrSimulate) {
  let res;
  if (formDataOrSimulate instanceof FormData) {
    res = await fetch("/api/analyze", { method: "POST", body: formDataOrSimulate });
  } else {
    res = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ simulate: true }) });
  }
  if (!res.ok) throw new Error("Analysis failed");
  const data = await res.json();

  // Summary
  document.getElementById("summaryText").textContent = data.summary || "—";
  const ul = document.getElementById("findingsList");
  ul.innerHTML = "";
  (data.key_findings || []).forEach(f => {
    const li = document.createElement("li");
    li.textContent = f;
    ul.appendChild(li);
  });

  // Risk
  setRisk(data.risk_score || 0);

  // Tree
  makeTree(document.getElementById("processTree"), data.process_tree || { name: "No data", children: [] });

  // Alerts
  const panel = document.getElementById("alertsPanel");
  panel.innerHTML = "";
  (data.alerts || []).forEach(a => {
    const div = document.createElement("div");
    div.className = "alert";
    div.innerHTML = `
      <div class="title"><span class="badge ${a.severity}">${a.severity}</span> ${a.title}</div>
      <div class="msg">${a.message}</div>
      <div class="rec"><em>Recommendation:</em> ${a.recommendation}</div>
      <div class="actions" style="margin-top:8px;">
        <button class="btn btn-secondary" data-act="copy-ioc">Copy IOC</button>
        <button class="btn" data-act="ack">Acknowledge</button>
      </div>
    `;
    div.querySelector('[data-act="copy-ioc"]').addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText((a.ioc || []).join("\\n"));
        alert("IOCs copied to clipboard.");
      } catch (e) {
        alert("Could not copy IOCs: " + e.message);
      }
    });
    div.querySelector('[data-act="ack"]').addEventListener("click", () => {
      div.style.opacity = 0.6;
    });
    panel.appendChild(div);
  });

  // Store latest for export
  window.__LATEST_RESULT__ = data;
}

async function exportReport() {
  const payload = window.__LATEST_RESULT__ || {
    summary: document.getElementById("summaryText").textContent,
    key_findings: Array.from(document.querySelectorAll("#findingsList li")).map(li => li.textContent),
    risk_score: Number((document.getElementById("riskValue").textContent || "0").replace("%","")) || 0,
    alerts: [],
    process_tree: {}
  };

  const res = await fetch("/export_report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = res.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "") || "report.html";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  const simulateBtn = document.getElementById("simulateBtn");
  const exportBtn = document.getElementById("exportBtn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    await analyze(fd);
  });

  simulateBtn.addEventListener("click", async () => {
    await analyze("simulate");
  });

  exportBtn.addEventListener("click", async () => {
    await exportReport();
  });
});
