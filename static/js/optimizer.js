// CinemaPredict - Predictive Optimization Controller

let recommendationsCache = [];

window.loadOptimizationRecommendations = async function() {
  try {
    const res = await fetch("/api/optimizer/recommendations");
    const data = await res.json();
    if (!data || !data.recommendations) return;

    recommendationsCache = data.recommendations;
    updateCounts();
    renderAdvisories(recommendationsCache);
    setupFilters();
  } catch (err) {
    console.error("Failed to load optimization recommendations:", err);
  }
};

function updateCounts() {
  const critCount = recommendationsCache.filter(r => r.severity === "CRITICAL").length;
  const warnCount = recommendationsCache.filter(r => r.severity === "WARNING").length;

  document.getElementById("count-all-recs").innerText = recommendationsCache.length;
  document.getElementById("count-crit-recs").innerText = critCount;
  document.getElementById("count-warn-recs").innerText = warnCount;
}

function renderAdvisories(recs) {
  const container = document.getElementById("recommendations-container");
  if (!container) return;

  if (!recs || recs.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 40px; color: #10b981;">
        <i class="fa-solid fa-circle-check" style="font-size: 2.5rem; margin-bottom: 12px;"></i>
        <h4 style="font-size: 1.1rem; color: #fff;">All Ingest Telemetry Healthy</h4>
        <p style="font-size: 0.82rem; color: #94a3b8; max-width: 500px; margin: 8px auto 0;">
          No active high-risk anomalies or payment bottlenecks detected across monitored screens.
        </p>
      </div>
    `;
    return;
  }

  container.innerHTML = recs.map(r => {
    const isCrit = (r.severity === "CRITICAL");
    const borderAccent = isCrit ? "var(--status-critical)" : "var(--accent-gold)";
    const badgeClass = isCrit ? "badge-critical" : "badge-warning";
    const icon = isCrit ? "fa-triangle-exclamation" : "fa-circle-exclamation";

    return `
      <div class="card" style="border-left: 4px solid ${borderAccent}; transition: transform 0.2s ease;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span class="badge badge-blue"><i class="fa-solid fa-display"></i> ${r.screen}</span>
              <span class="badge ${badgeClass}"><i class="fa-solid ${icon}"></i> ${r.severity}</span>
              <span style="font-size: 0.75rem; color: var(--text-dim);">Week ${r.week} &bull; ${r.category}</span>
            </div>
            <h4 style="font-size: 1rem; font-weight: 700; color: #fff;">${r.issue}</h4>
          </div>

          <div style="text-align: right;">
            <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Predicted Recovery</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: ${borderAccent};">${Math.round(r.expected_recovery_time_min)} min</div>
          </div>
        </div>

        <div style="background: rgba(0, 0, 0, 0.2); border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; font-size: 0.8rem; color: #cbd5e1; line-height: 1.5;">
          <strong style="color: #94a3b8;">Operational Risk Impact:</strong> ${r.impact}
        </div>

        <div style="background: rgba(0, 240, 255, 0.04); border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 8px; padding: 12px 14px; font-size: 0.82rem; color: #e2e8f0; line-height: 1.5;">
          <strong style="color: var(--accent-cyan); display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
            <i class="fa-solid fa-screwdriver-wrench"></i> Recommended Corrective Action (Authorized Operator Workflow):
          </strong>
          ${r.action}
        </div>
      </div>
    `;
  }).join("");
}

function setupFilters() {
  const buttons = document.querySelectorAll(".btn-filter-opt");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => {
        b.classList.remove("active");
        b.classList.remove("btn-cyan");
        b.classList.add("btn-outline");
      });
      btn.classList.add("active");
      btn.classList.remove("btn-outline");
      btn.classList.add("btn-cyan");

      const filter = btn.getAttribute("data-filter");
      if (filter === "ALL") {
        renderAdvisories(recommendationsCache);
      } else {
        const filtered = recommendationsCache.filter(r => r.severity === filter);
        renderAdvisories(filtered);
      }
    });
  });

  const refreshBtn = document.getElementById("btn-refresh-recs");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      window.loadOptimizationRecommendations();
      showToast("Refreshed predictive advisories", "info");
    });
  }
}
