// Helpers
function setRisk(value, activityScore = null, llmScore = null) {
  value = Math.max(0, Math.min(100, value | 0));
  const ring = document.getElementById("riskMeter");
  const valEl = document.getElementById("riskValue");
  ring.querySelectorAll(".ring-label").forEach(el => el.remove());

  // If contributions are provided, show segmented breakdown
  if (activityScore !== null && llmScore !== null) {
    const rawActivity = Math.max(0, Number(activityScore || 0) * 0.80);
    const rawLlm = Math.max(0, Number(llmScore || 0) * 0.20);
    const rawTotal = rawActivity + rawLlm;

    // Normalize so components add up to the displayed total risk percentage.
    let activityContrib = 0;
    let llmContrib = 0;
    if (rawTotal > 0) {
      const scale = value / rawTotal;
      activityContrib = Math.round((rawActivity * scale) * 10) / 10;
      llmContrib = Math.round((value - activityContrib) * 10) / 10;
    }

    // Calculate total contribution and angles
    const totalContrib = activityContrib + llmContrib;
    const totalFillDeg = value * 3.6; // Total degrees to fill

    // Proportional angles for each contribution
    const activityDegreesRelative = totalContrib > 0 ? (activityContrib / totalContrib) * totalFillDeg : 0;
    const llmDegreesRelative = totalContrib > 0 ? (llmContrib / totalContrib) * totalFillDeg : 0;

    // Determine colors based on risk level
    let activityColor, llmColor;
    if (value < 50) {
      activityColor = "var(--ok)";      // Green
      llmColor = "var(--ok-dim)";       // Lighter green
    } else if (value < 80) {
      activityColor = "var(--warn)";    // Yellow
      llmColor = "var(--warn-dim)";     // Lighter yellow
    } else {
      activityColor = "var(--danger)";  // Red
      llmColor = "var(--danger-dim)";   // Lighter red
    }

    // Create segmented conic gradient
    const point1 = activityDegreesRelative;
    const point2 = activityDegreesRelative + llmDegreesRelative;
    ring.style.background = `conic-gradient(
      ${activityColor} 0deg,
      ${activityColor} ${point1}deg,
      ${llmColor} ${point1}deg,
      ${llmColor} ${point2}deg,
      #1a2032 ${point2}deg,
      #1a2032 360deg
    )`;

    const placeLabel = (text, color, angleDeg) => {
      const label = document.createElement("div");
      label.className = "ring-label";
      label.innerHTML = `<span class="ring-label-swatch" style="background:${color}"></span>${text}`;

      const radius = 102;
      const radians = (angleDeg - 90) * (Math.PI / 180);
      const x = 80 + (Math.cos(radians) * radius);
      const y = 80 + (Math.sin(radians) * radius);
      const rightSide = Math.cos(radians) >= 0;

      label.style.left = `${x}px`;
      label.style.top = `${y}px`;
      label.style.transform = rightSide ? "translate(8px, -50%)" : "translate(calc(-100% - 8px), -50%)";
      ring.appendChild(label);
    };

    const activityMid = point1 / 2;
    const llmMid = point1 + (llmDegreesRelative / 2);
    placeLabel(`Activity ${activityContrib}%`, activityColor, activityMid);
    placeLabel(`LLM ${llmContrib}%`, llmColor, llmMid);

    // Center keeps only the final score for clarity.
    valEl.textContent = value + "%";
  } else {
    // Default single-color gradient
    let color;
    if (value < 50) color = "var(--ok)";
    else if (value < 80) color = "var(--warn)";
    else color = "var(--danger)";
    ring.style.background = `conic-gradient(${color} ${value * 3.6}deg, #1a2032 0deg)`;
    valEl.textContent = value + "%";
  }
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

function renderAiInsights(aiInsights) {
  const section = document.getElementById("aiInsightsSection");
  if (!section) return;

  if (!aiInsights || Object.keys(aiInsights).length === 0) {
    section.style.display = "none";
    return;
  }

  section.style.display = "";

  const errorEl = document.getElementById("aiInsightsError");
  const summaryBlock = document.getElementById("aiInsightsSummaryBlock");
  const summaryEl = document.getElementById("aiSummaryText");
  const metaEl = document.getElementById("aiInsightsMeta");
  const similarBlock = document.getElementById("aiInsightsSimilarBlock");
  const similarList = document.getElementById("aiSimilarList");
  const recsBlock = document.getElementById("aiInsightsRecsBlock");
  const recsList = document.getElementById("aiRecsList");

  // Error
  if (aiInsights.error) {
    errorEl.style.display = "";
    errorEl.textContent = `AI analysis unavailable: ${aiInsights.error}`;
  } else {
    errorEl.style.display = "none";
    errorEl.textContent = "";
  }

  // Summary / Threat Assessment
  const summaryText = aiInsights.threat_assessment || aiInsights.summary || "";
  if (summaryText) {
    summaryBlock.style.display = "";
    // Convert line breaks to HTML and render
    const formattedText = summaryText
      .split('\n')
      .filter(line => line.trim())
      .map(line => `<p style="margin: 8px 0;">${line.trim()}</p>`)
      .join('');
    summaryEl.innerHTML = formattedText;
  } else {
    summaryBlock.style.display = "none";
    summaryEl.innerHTML = "";
  }

  // Meta
  const metaParts = [];
  if (typeof aiInsights.similar_cases_found === "number") {
    metaParts.push(`Similar cases found: ${aiInsights.similar_cases_found}`);
  }
  if (aiInsights.context_used !== undefined) {
    metaParts.push(`Context used: ${aiInsights.context_used ? "Yes" : "No"}`);
  }
  if (aiInsights.confidence) {
    metaParts.push(`Confidence: ${aiInsights.confidence}`);
  }
  metaEl.textContent = metaParts.join(" • ");

  // Similar cases
  const similarCases = Array.isArray(aiInsights.similar_cases) ? aiInsights.similar_cases : [];
  if (similarCases.length) {
    similarBlock.style.display = "";
    similarList.innerHTML = "";
    similarCases.forEach((c) => {
      const li = document.createElement("li");
      const desc = c.description || c.content || (c.metadata && c.metadata.title) || "Similar case";
      const score = c.similarity || c.similarity_score;
      li.textContent = score ? `${desc} (${score})` : desc;
      similarList.appendChild(li);
    });
  } else {
    similarBlock.style.display = "none";
    similarList.innerHTML = "";
  }

  // Recommendations
  let recommendations = [];
  if (Array.isArray(aiInsights.recommendations)) {
    recommendations = aiInsights.recommendations;
  } else if (typeof aiInsights.recommendations === "string") {
    recommendations = aiInsights.recommendations.split("\n").map(s => s.trim()).filter(Boolean);
  }

  if (recommendations.length) {
    recsBlock.style.display = "";
    recsList.innerHTML = "";
    recommendations.forEach((rec) => {
      const li = document.createElement("li");
      li.textContent = rec;
      recsList.appendChild(li);
    });
  } else {
    recsBlock.style.display = "none";
    recsList.innerHTML = "";
  }
}

// Poll a background job until it finishes or fails
async function pollJob(jobId) {
  const POLL_INTERVAL = 2000; // 2 seconds
  const MAX_POLLS = 150;      // 5 minutes max

  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL));
    const res = await fetch(`/api/jobs/status/${jobId}`);
    if (!res.ok) throw new Error("Failed to check job status");
    const info = await res.json();

    if (info.status === "finished") return info.result;
    if (info.status === "failed") throw new Error(info.error || "Analysis job failed");

    // Update UI with progress indicator
    document.getElementById("summaryText").textContent =
      `Analysis in progress\u2026 (${info.status})`;
  }
  throw new Error("Analysis timed out");
}

function renderQuantificationInSections(data) {
  const aiLlmBlock = document.getElementById("aiLlmFindingsBlock");
  const processActivityBlock = document.getElementById("processActivityBlock");
  const summaryIssuesBlock = document.getElementById("summaryIssuesBlock");
  if (!aiLlmBlock || !processActivityBlock || !summaryIssuesBlock) return;

  // Support all payload shapes seen across sync/async paths.
  let quantData =
    data?.ai_insights?.risk_quantification ||
    data?.risk_quantification ||
    null;

  // Fallback: build a minimal quantification model from exposed score fields.
  if (!quantData && (typeof data?.activity_risk_score === "number" || typeof data?.llm_risk_score === "number")) {
    const activityScore = Number(data?.activity_risk_score || 0);
    const llmScore = Number(data?.llm_risk_score || 0);
    const finalScore = Number(data?.risk_score || Math.round((activityScore * 0.8) + (llmScore * 0.2)));
    quantData = {
      final: {
        score: finalScore,
        equation: "final = (activity_score * 0.80) + (llm_score * 0.20)",
      },
      activity: {
        score: activityScore,
        quantification: {
          percent_of_activity_score: { process: 0, network: 0, system: 0 },
        },
      },
      llm: {
        score: llmScore,
        issues: [],
      },
    };
  }

  // Check if risk_quantification data exists
  if (!quantData || !quantData.final) {
    aiLlmBlock.style.display = "none";
    processActivityBlock.style.display = "none";
    summaryIssuesBlock.style.display = "none";
    return;
  }

  // Activity contribution
  if (quantData.activity) {
    processActivityBlock.style.display = "";
    const actScore = quantData.activity.score || 0;
    const actPercent = Math.round((actScore * 0.80) * 100) / 100;
    document.getElementById("processActivityScore").textContent =
      actScore + "% (contributes " + actPercent + " pts)";

    // Activity breakdown by component
    if (quantData.activity.quantification && quantData.activity.quantification.percent_of_activity_score) {
      const percents = quantData.activity.quantification.percent_of_activity_score;
      document.getElementById("processActivityProcess").textContent =
        (percents.process || 0).toFixed(1) + "%";
      document.getElementById("processActivityNetwork").textContent =
        (percents.network || 0).toFixed(1) + "%";
      document.getElementById("processActivitySystem").textContent =
        (percents.system || 0).toFixed(1) + "%";
    }
  } else {
    processActivityBlock.style.display = "none";
  }

  // LLM contribution in AI Insights box
  if (quantData.llm) {
    aiLlmBlock.style.display = "";
    const llmScore = quantData.llm.score || 0;
    const llmPercent = Math.round((llmScore * 0.20) * 100) / 100;
    document.getElementById("aiLlmContributionScore").textContent =
      llmScore + "% (contributes " + llmPercent + " pts)";

    const aiFindingsList = document.getElementById("aiLlmFindingsList");
    aiFindingsList.innerHTML = "";
    const summaryIssuesList = document.getElementById("summaryTopIssuesList");
    summaryIssuesList.innerHTML = "";

    if (quantData.llm.issues && quantData.llm.issues.length > 0) {
      summaryIssuesBlock.style.display = "";
      quantData.llm.issues.forEach((issue) => {
        const aiIssueDiv = document.createElement("div");
        aiIssueDiv.style.cssText =
          "background: #0a0d17; padding: 10px 12px; border-radius: 8px; " +
          "border-left: 3px solid #6ea8fe; font-size: 0.9rem;";
        aiIssueDiv.innerHTML = `
          <div><strong>${issue.issue}</strong></div>
          <div style="color: var(--muted); font-size: 0.85rem; margin-top: 4px;">
            +${issue.points} points
          </div>
        `;
        aiFindingsList.appendChild(aiIssueDiv);

        const summaryIssueDiv = document.createElement("div");
        summaryIssueDiv.style.cssText =
          "background:#0a0d17; padding:8px 10px; border-radius:8px; border-left:3px solid #8ef0a5; font-size:0.9rem;";
        summaryIssueDiv.innerHTML = `<strong>${issue.issue}</strong> <span style="color:var(--muted);">(+${issue.points})</span>`;
        summaryIssuesList.appendChild(summaryIssueDiv);
      });
    } else {
      summaryIssuesBlock.style.display = "none";
      const noFindingsDiv = document.createElement("div");
      noFindingsDiv.style.color = "var(--muted)";
      noFindingsDiv.textContent = "No issues detected by LLM analysis";
      aiFindingsList.appendChild(noFindingsDiv);
    }
  } else {
    aiLlmBlock.style.display = "none";
    summaryIssuesBlock.style.display = "none";
  }
}

async function analyze(formDataOrSimulate) {
  // Show immediate feedback
  document.getElementById("summaryText").textContent = "Starting analysis\u2026";

  let res;
  if (formDataOrSimulate instanceof FormData) {
    res = await fetch("/api/analyze", { method: "POST", body: formDataOrSimulate });
  } else {
    res = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ simulate: true }) });
  }

  if (!res.ok && res.status !== 202) throw new Error("Analysis failed");

  let data = await res.json();

  // If the server queued the job (202), poll until done
  if (res.status === 202 && data.job_id) {
    document.getElementById("summaryText").textContent = "Analysis queued\u2026 waiting for results";
    data = await pollJob(data.job_id);
  }

  // Summary
  document.getElementById("summaryText").textContent = data.summary || "—";
  const ul = document.getElementById("findingsList");
  ul.innerHTML = "";
  (data.key_findings || []).forEach(f => {
    const li = document.createElement("li");
    li.textContent = f;
    ul.appendChild(li);
  });

  // Risk - pass activity and LLM scores if available for breakdown display
  let actScore = null, llmScore = null;
  if (data?.ai_insights?.risk_quantification?.activity?.score !== undefined) {
    actScore = data.ai_insights.risk_quantification.activity.score;
  }
  if (data?.ai_insights?.risk_quantification?.llm?.score !== undefined) {
    llmScore = data.ai_insights.risk_quantification.llm.score;
  }
  setRisk(data.risk_score || 0, actScore, llmScore);

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

  // AI Insights (RAG)
  renderAiInsights(data.ai_insights || {});

  // Quantification details merged into existing sections
  renderQuantificationInSections(data || {});

  // Store latest for export
  window.__LATEST_RESULT__ = data;
}

async function exportReport() {
  const payload = window.__LATEST_RESULT__ || {
    summary: document.getElementById("summaryText").textContent,
    key_findings: Array.from(document.querySelectorAll("#findingsList li")).map(li => li.textContent),
    risk_score: Number((document.getElementById("riskValue").textContent || "0").replace("%", "")) || 0,
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
