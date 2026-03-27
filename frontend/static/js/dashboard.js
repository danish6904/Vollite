// Helpers
function computeRiskContributions(finalScore, activityScore, llmScore) {
  const value = Math.max(0, Math.min(100, Number(finalScore || 0)));
  const rawActivity = Math.max(0, Number(activityScore || 0) * 0.80);
  const rawLlm = Math.max(0, Number(llmScore || 0) * 0.20);
  const rawTotal = rawActivity + rawLlm;

  let activityContrib = 0;
  let llmContrib = 0;
  if (rawTotal > 0) {
    const scale = value / rawTotal;
    activityContrib = Math.round((rawActivity * scale) * 10) / 10;
    llmContrib = Math.round((value - activityContrib) * 10) / 10;
  }

  return {
    activityContrib,
    llmContrib,
  };
}

function setRisk(value, activityScore = null, llmScore = null, quantData = null) {
  value = Math.max(0, Math.min(100, value | 0));
  const ring = document.getElementById("riskMeter");
  const valEl = document.getElementById("riskValue");
  let legendEl = document.getElementById("riskLegend");
  if (!legendEl && ring) {
    const visual = ring.closest(".risk-visual") || ring.parentElement;
    if (visual) {
      legendEl = document.createElement("div");
      legendEl.id = "riskLegend";
      legendEl.className = "risk-legend";
      visual.appendChild(legendEl);
    }
  }
  if (legendEl) legendEl.innerHTML = "";

  // If contributions are provided, show segmented breakdown
  if (activityScore !== null && llmScore !== null) {
    const contribution = computeRiskContributions(value, activityScore, llmScore);
    const activityContrib = contribution.activityContrib;
    const llmContrib = contribution.llmContrib;

    // Calculate total contribution and angles
    const totalContrib = activityContrib + llmContrib;
    const totalFillDeg = value * 3.6; // Total degrees to fill

    // Enhanced color palettes with more differential colors
    let activityColors, llmColors;
    if (value < 50) {
      // Green palette with distinct hues for Activity components
      activityColors = {
        process: "#06D6A0",      // Bright teal
        network: "#00A878",      // Medium teal  
        system: "#2F9B7C"        // Darker teal
      };
      // Blue-green gradient for LLM issues
      llmColors = ["#5CC8E2", "#3BA39C", "#00B4A6", "#008B7C"];
    } else if (value < 80) {
      // Amber palette with distinct hues for Activity components
      activityColors = {
        process: "#FFD166",      // Bright amber
        network: "#F4A261",      // Medium amber
        system: "#E8860F"        // Darker gold
      };
      // Orange-amber gradient for LLM issues
      llmColors = ["#FF9F1C", "#F77F00", "#E89D00", "#D87F00"];
    } else {
      // Red palette with distinct hues for Activity components
      activityColors = {
        process: "#FF6B6B",      // Bright red
        network: "#E63946",      // Medium red
        system: "#C1121F"        // Dark crimson
      };
      // Red-orange gradient for LLM issues
      llmColors = ["#FF7F50", "#FF6347", "#E53935", "#C62828"];
    }

    const segments = [];

    // Build activity subsegments (process/network/system) as parts of total risk.
    const activityPerc = quantData?.activity?.quantification?.percent_of_activity_score;
    if (activityContrib > 0 && activityPerc) {
      const processVal = (activityContrib * Number(activityPerc.process || 0)) / 100;
      const networkVal = (activityContrib * Number(activityPerc.network || 0)) / 100;
      const systemVal = (activityContrib * Number(activityPerc.system || 0)) / 100;

      segments.push({
        value: processVal,
        color: activityColors.process,
        name: "Process",
        contribution: processVal,
        category: "Activity"
      });
      segments.push({
        value: networkVal,
        color: activityColors.network,
        name: "Network",
        contribution: networkVal,
        category: "Activity"
      });
      segments.push({
        value: systemVal,
        color: activityColors.system,
        name: "System",
        contribution: systemVal,
        category: "Activity"
      });
    } else if (activityContrib > 0) {
      segments.push({
        value: activityContrib,
        color: activityColors.process,
        name: "Activity",
        contribution: activityContrib,
        category: "Activity"
      });
    }

    // Build LLM subsegments from issue points as parts of total risk.
    const issues = Array.isArray(quantData?.llm?.issues) ? quantData.llm.issues : [];
    const totalIssuePoints = issues.reduce((sum, issue) => sum + Number(issue.points || 0), 0);
    if (llmContrib > 0 && issues.length > 0 && totalIssuePoints > 0) {
      issues.forEach((issue, idx) => {
        const share = Number(issue.points || 0) / totalIssuePoints;
        const issueContrib = llmContrib * share;
        segments.push({
          value: issueContrib,
          color: llmColors[idx % llmColors.length],
          name: (issue.name || issue.title || `Issue ${idx + 1}`).substring(0, 20),
          contribution: issueContrib,
          category: "LLM"
        });
      });
    } else if (llmContrib > 0) {
      segments.push({
        value: llmContrib,
        color: llmColors[0],
        name: "LLM",
        contribution: llmContrib,
        category: "LLM"
      });
    }

    // Create multi-segment conic gradient from subcategory segments.
    let cursorDeg = 0;
    const stops = [];
    segments.forEach((seg) => {
      if (seg.value <= 0) return;
      const segDeg = totalContrib > 0 ? (seg.value / totalContrib) * totalFillDeg : 0;
      const endDeg = cursorDeg + segDeg;
      stops.push(`${seg.color} ${cursorDeg}deg`, `${seg.color} ${endDeg}deg`);
      cursorDeg = endDeg;
    });
    ring.style.background = `conic-gradient(${stops.join(", ")}, #1a2032 ${cursorDeg}deg, #1a2032 360deg)`;

    // Render side legend with matching segment colors and contribution percentages.
    if (legendEl) {
      segments
        .filter(seg => seg.value > 0)
        .forEach((seg) => {
          const contribPercent = totalContrib > 0
            ? ((seg.value / totalContrib) * 100).toFixed(1)
            : "0.0";

          const item = document.createElement("div");
          item.className = "risk-legend-item";

          const left = document.createElement("span");
          left.className = "risk-legend-left";

          const dot = document.createElement("span");
          dot.className = "risk-legend-dot";
          dot.style.background = seg.color;

          const name = document.createElement("span");
          name.className = "risk-legend-name";
          name.title = seg.name;
          name.textContent = seg.name;

          const pct = document.createElement("span");
          pct.className = "risk-legend-value";
          pct.textContent = `${contribPercent}%`;

          left.appendChild(dot);
          left.appendChild(name);
          item.appendChild(left);
          item.appendChild(pct);
          legendEl.appendChild(item);
        });
    }

    // Center keeps only the final score for clarity.
    valEl.textContent = value + "%";
  } else {
    // Default single-color gradient
    let color;
    if (value < 50) color = "var(--ok)";
    else if (value < 80) color = "var(--warn)";
    else color = "var(--danger)";
    ring.style.background = `conic-gradient(${color} ${value * 3.6}deg, #1a2032 0deg)`;

    if (legendEl) {
      const item = document.createElement("div");
      item.className = "risk-legend-item";

      const left = document.createElement("span");
      left.className = "risk-legend-left";

      const dot = document.createElement("span");
      dot.className = "risk-legend-dot";
      dot.style.background = color;

      const name = document.createElement("span");
      name.className = "risk-legend-name";
      name.textContent = "Overall Risk";

      const pct = document.createElement("span");
      pct.className = "risk-legend-value";
      pct.textContent = `${value}%`;

      left.appendChild(dot);
      left.appendChild(name);
      item.appendChild(left);
      item.appendChild(pct);
      legendEl.appendChild(item);
    }

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

  const finalScore = Number(quantData.final?.score || data?.risk_score || 0);
  const activityScoreForRisk = Number(quantData.activity?.score || 0);
  const llmScoreForRisk = Number(quantData.llm?.score || 0);
  const contribution = computeRiskContributions(finalScore, activityScoreForRisk, llmScoreForRisk);

  // Activity contribution
  if (quantData.activity) {
    processActivityBlock.style.display = "";
    const actScore = quantData.activity.score || 0;
    const actPercent = contribution.activityContrib;
    document.getElementById("processActivityScore").textContent =
      actScore + "% activity score -> " + actPercent.toFixed(1) + "% of total risk";

    // Activity subcategories as percentage of total risk
    if (quantData.activity.quantification && quantData.activity.quantification.percent_of_activity_score) {
      const percents = quantData.activity.quantification.percent_of_activity_score;
      const processRiskPct = (actPercent * Number(percents.process || 0)) / 100;
      const networkRiskPct = (actPercent * Number(percents.network || 0)) / 100;
      const systemRiskPct = (actPercent * Number(percents.system || 0)) / 100;
      document.getElementById("processActivityProcess").textContent =
        processRiskPct.toFixed(1) + "%";
      document.getElementById("processActivityNetwork").textContent =
        networkRiskPct.toFixed(1) + "%";
      document.getElementById("processActivitySystem").textContent =
        systemRiskPct.toFixed(1) + "%";
    } else {
      document.getElementById("processActivityProcess").textContent = "0.0%";
      document.getElementById("processActivityNetwork").textContent = "0.0%";
      document.getElementById("processActivitySystem").textContent = "0.0%";
    }
  } else {
    processActivityBlock.style.display = "none";
  }

  // LLM contribution in AI Insights box
  if (quantData.llm) {
    aiLlmBlock.style.display = "";
    const llmScore = quantData.llm.score || 0;
    const llmPercent = contribution.llmContrib;
    document.getElementById("aiLlmContributionScore").textContent =
      llmScore + "% LLM score -> " + llmPercent.toFixed(1) + "% of total risk";

    const aiFindingsList = document.getElementById("aiLlmFindingsList");
    aiFindingsList.innerHTML = "";
    const summaryIssuesList = document.getElementById("summaryTopIssuesList");
    summaryIssuesList.innerHTML = "";

    if (quantData.llm.issues && quantData.llm.issues.length > 0) {
      summaryIssuesBlock.style.display = "";
      const totalIssuePoints = quantData.llm.issues.reduce((sum, issue) => sum + Number(issue.points || 0), 0);
      quantData.llm.issues.forEach((issue) => {
        const issueRiskPct = totalIssuePoints > 0
          ? (llmPercent * Number(issue.points || 0)) / totalIssuePoints
          : 0;
        const aiIssueDiv = document.createElement("div");
        aiIssueDiv.style.cssText =
          "background: #0a0d17; padding: 10px 12px; border-radius: 8px; " +
          "border-left: 3px solid #6ea8fe; font-size: 0.9rem;";
        aiIssueDiv.innerHTML = `
          <div><strong>${issue.issue}</strong></div>
          <div style="color: var(--muted); font-size: 0.85rem; margin-top: 4px;">
            ${issueRiskPct.toFixed(1)}% of total risk
          </div>
        `;
        aiFindingsList.appendChild(aiIssueDiv);

        const summaryIssueDiv = document.createElement("div");
        summaryIssueDiv.style.cssText =
          "background:#0a0d17; padding:8px 10px; border-radius:8px; border-left:3px solid #8ef0a5; font-size:0.9rem;";
        summaryIssueDiv.innerHTML = `<strong>${issue.issue}</strong> <span style="color:var(--muted);">(${issueRiskPct.toFixed(1)}%)</span>`;
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
  const quantData = data?.ai_insights?.risk_quantification || data?.risk_quantification || null;
  let actScore = null, llmScore = null;
  if (quantData?.activity?.score !== undefined) {
    actScore = quantData.activity.score;
  }
  if (quantData?.llm?.score !== undefined) {
    llmScore = quantData.llm.score;
  }
  setRisk(data.risk_score || 0, actScore, llmScore, quantData);

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
