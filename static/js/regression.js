// CinemaPredict - Regression Module Controller

window.loadRegressionMetrics = async function() {
  try {
    const res = await fetch("/api/regression/metrics");
    const data = await res.json();
    if (!data) return;

    renderRegressionTable(data);
    renderActualVsPredicted(data.comparison_sample);
    renderRegressionFeatureImportance(data.feature_importances);
    setupRegressionForm();
  } catch (err) {
    console.error("Failed to load regression metrics:", err);
  }
};

function renderRegressionTable(data) {
  const tbody = document.getElementById("regression-metrics-table");
  if (!tbody) return;

  const models = ["Gradient Boosting Regressor", "Random Forest Regressor", "Linear Regression"];
  const bestModel = data.best_model || "Gradient Boosting Regressor";

  document.getElementById("regression-best-badge").innerText = `Best: ${bestModel}`;
  document.getElementById("reg-actual-pred-model").innerText = `Test Set (${bestModel})`;

  const bestMetrics = data[bestModel] || {};
  document.getElementById("reg-gb-r2").innerText = bestMetrics.r2_score || "--";
  document.getElementById("reg-best-mae").innerText = `${bestMetrics.mae || '--'} min`;
  document.getElementById("reg-best-rmse").innerText = `${bestMetrics.rmse || '--'} min`;
  document.getElementById("reg-best-var").innerText = `${bestMetrics.accuracy_pct || '--'}%`;

  tbody.innerHTML = models.map(m => {
    const metrics = data[m];
    if (!metrics) return "";
    const isBest = (m === bestModel);
    const star = isBest ? `<i class="fa-solid fa-crown" style="color: #fbbf24; margin-right: 6px;"></i>` : "";

    return `
      <tr style="${isBest ? 'background: rgba(251, 191, 36, 0.05); font-weight: 600;' : ''}">
        <td>${star}${m}</td>
        <td><strong style="color: ${isBest ? '#fbbf24' : '#cbd5e1'};">${metrics.mae} min</strong></td>
        <td>${metrics.rmse} min</td>
        <td><span class="badge ${isBest ? 'badge-normal' : 'badge-blue'}">${metrics.r2_score}</span></td>
      </tr>
    `;
  }).join("");
}

function renderActualVsPredicted(sample) {
  if (!sample || !sample.actual || !sample.predicted) return;

  const indices = sample.indices.map(i => `#${i + 1}`);

  const traceActual = {
    x: indices,
    y: sample.actual,
    name: 'Actual Recovery Time (min)',
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#00f0ff', width: 2.5 },
    marker: { size: 6, color: '#00f0ff' }
  };

  const tracePredicted = {
    x: indices,
    y: sample.predicted,
    name: `Predicted (${sample.model_name})`,
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#fbbf24', width: 2.5, dash: 'dash' },
    marker: { size: 6, color: '#fbbf24', symbol: 'diamond' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    title: false,
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Resolution Time (Minutes)'
    },
    hovermode: 'x unified'
  };

  Plotly.newPlot('chart-actual-vs-predicted', [traceActual, tracePredicted], layout, PLOTLY_CONFIG);
}

function renderRegressionFeatureImportance(features) {
  if (!features) return;

  const feats = features.slice(0, 7).reverse();
  const trace = {
    x: feats.map(f => f.importance),
    y: feats.map(f => f.feature.replace(/_/g, ' ')),
    type: 'bar',
    orientation: 'h',
    marker: {
      color: '#fbbf24'
    }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    margin: { t: 10, r: 20, l: 155, b: 25 },
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Relative Feature Impact (%)'
    }
  };

  Plotly.newPlot('chart-reg-feature-importance', [trace], layout, PLOTLY_CONFIG);
}

function setupRegressionForm() {
  const form = document.getElementById("form-reg-predict");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      dcp_corruption_pct: parseFloat(document.getElementById("reg-dcp-corr").value),
      broken_kdm: parseInt(document.getElementById("reg-broken-kdm").value),
      kdm_decryption_failure: parseInt(document.getElementById("reg-kdm-dec-fail").value),
      firmware_update_required: parseInt(document.getElementById("reg-firmware").value),
      sound_sync_error_ms: parseFloat(document.getElementById("reg-sound-sync").value),
      network_delay_ms: parseFloat(document.getElementById("reg-net-delay").value),
      dcp_file_size_gb: parseFloat(document.getElementById("reg-file-size").value),
      model_name: document.getElementById("reg-model-select").value
    };

    try {
      const res = await fetch("/api/regression/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || "Regression calculation failed", "error");
        return;
      }

      displayRegressionResult(data.prediction);
      showToast("Recovery time prediction computed", "success");
    } catch (err) {
      console.error("Regression error:", err);
      showToast("Prediction error", "error");
    }
  });
}

function displayRegressionResult(result) {
  const container = document.getElementById("reg-prediction-output");
  const minElement = document.getElementById("reg-result-minutes");
  const warningsContainer = document.getElementById("reg-warnings-container");
  const breakdownBody = document.getElementById("reg-breakdown-body");

  if (!container || !result) return;

  minElement.innerText = `${result.predicted_recovery_time_min} Minutes`;

  if (result.warnings && result.warnings.length > 0) {
    warningsContainer.innerHTML = result.warnings.map(w => `
      <div style="background: rgba(239, 68, 68, 0.12); border-left: 3px solid #ef4444; padding: 10px 14px; border-radius: 6px; font-size: 0.8rem; color: #fca5a5; margin-bottom: 6px;">
        <i class="fa-solid fa-triangle-exclamation" style="margin-right: 6px;"></i> ${w}
      </div>
    `).join("");
  } else {
    warningsContainer.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 8px 12px; border-radius: 6px; font-size: 0.8rem; color: #6ee7b7;">
        <i class="fa-solid fa-circle-check" style="margin-right: 6px;"></i> Minimal operational anomalies detected. Standard pre-show verification speed.
      </div>
    `;
  }

  breakdownBody.innerHTML = (result.breakdowns || []).map(b => {
    let sevBadge = `<span class="badge badge-normal">LOW</span>`;
    if (b.severity === "MEDIUM") sevBadge = `<span class="badge badge-warning">MEDIUM</span>`;
    if (b.severity === "HIGH") sevBadge = `<span class="badge badge-critical">HIGH</span>`;

    return `
      <tr>
        <td><strong>${b.problem}</strong></td>
        <td>${b.estimated_impact}</td>
        <td>${sevBadge}</td>
      </tr>
    `;
  }).join("");

  container.classList.add("show");
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
