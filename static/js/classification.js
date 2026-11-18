// CinemaPredict - Classification Module Controller

window.loadClassificationMetrics = async function() {
  try {
    const res = await fetch("/api/classification/metrics");
    const data = await res.json();
    if (!data) return;

    renderClassificationTable(data);
    renderConfusionMatrix(data);
    renderClassificationFeatureImportance(data.feature_importances);
    setupClassificationForm();
  } catch (err) {
    console.error("Failed to load classification metrics:", err);
  }
};

function renderClassificationTable(data) {
  const tbody = document.getElementById("classification-metrics-table");
  if (!tbody) return;

  const models = ["Random Forest", "Logistic Regression", "Decision Tree"];
  const bestModel = data.best_model || "Random Forest";

  document.getElementById("classification-best-badge").innerText = `Best: ${bestModel}`;
  document.getElementById("cls-cm-model-name").innerText = `${bestModel} Confusion Matrix`;

  tbody.innerHTML = models.map(m => {
    const metrics = data[m];
    if (!metrics) return "";
    const isBest = (m === bestModel);
    const star = isBest ? `<i class="fa-solid fa-crown" style="color: #fbbf24; margin-right: 6px;"></i>` : "";

    return `
      <tr style="${isBest ? 'background: rgba(0, 240, 255, 0.05); font-weight: 600;' : ''}">
        <td>${star}${m}</td>
        <td><span class="badge ${isBest ? 'badge-normal' : 'badge-blue'}">${metrics.accuracy}%</span></td>
        <td>${metrics.precision}%</td>
        <td>${metrics.recall}%</td>
        <td><strong style="color: ${isBest ? '#00f0ff' : '#cbd5e1'};">${metrics.f1_score}%</strong></td>
      </tr>
    `;
  }).join("");
}

function renderConfusionMatrix(data) {
  const bestModel = data.best_model || "Random Forest";
  const metrics = data[bestModel];
  if (!metrics || !metrics.confusion_matrix) return;

  const zValues = metrics.confusion_matrix;
  const labels = metrics.labels || ["NORMAL", "WARNING", "CRITICAL"];

  const plotData = [{
    z: zValues,
    x: labels,
    y: labels,
    type: 'heatmap',
    colorscale: [
      [0.0, '#0b1220'],
      [0.5, '#0284c7'],
      [1.0, '#00f0ff']
    ],
    showscale: true,
    hoverongaps: false
  }];

  const annotations = [];
  for (let i = 0; i < labels.length; i++) {
    for (let j = 0; j < labels.length; j++) {
      annotations.push({
        x: labels[j],
        y: labels[i],
        text: String(zValues[i][j]),
        font: { family: 'Inter', size: 14, color: '#ffffff', weight: 'bold' },
        showarrow: false
      });
    }
  }

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    title: false,
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Predicted Delivery Risk'
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Actual Delivery Risk',
      autorange: 'reversed'
    },
    annotations: annotations
  };

  Plotly.newPlot('chart-confusion-matrix', plotData, layout, PLOTLY_CONFIG);
}

function renderClassificationFeatureImportance(features) {
  if (!features) return;

  const feats = features.slice(0, 7).reverse();
  const trace = {
    x: feats.map(f => f.importance),
    y: feats.map(f => f.feature.replace(/_/g, ' ')),
    type: 'bar',
    orientation: 'h',
    marker: {
      color: '#00f0ff'
    }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    margin: { t: 10, r: 20, l: 140, b: 25 },
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Relative Importance (%)'
    }
  };

  Plotly.newPlot('chart-cls-feature-importance', [trace], layout, PLOTLY_CONFIG);
}

function setupClassificationForm() {
  const form = document.getElementById("form-classify-predict");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      cinema_screen: document.getElementById("cls-screen").value,
      payment_completed: parseInt(document.getElementById("cls-payment").value),
      kdm_available: parseInt(document.getElementById("cls-kdm-avail").value),
      kdm_decryptable: parseInt(document.getElementById("cls-kdm-dec").value),
      kdm_expired: parseInt(document.getElementById("cls-kdm-exp").value),
      dcp_corruption_pct: parseFloat(document.getElementById("cls-dcp-corr").value),
      network_delay_ms: parseFloat(document.getElementById("cls-network-delay").value),
      model_name: document.getElementById("cls-model-select").value
    };

    try {
      const res = await fetch("/api/classification/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.success) {
        showToast(data.error || "Inference failed", "error");
        return;
      }

      displayClassificationResult(data.prediction);
      showToast("Risk classification inference complete", "success");
    } catch (err) {
      console.error("Classification inference error:", err);
      showToast("Prediction error", "error");
    }
  });
}

function displayClassificationResult(result) {
  const container = document.getElementById("cls-prediction-output");
  const badge = document.getElementById("cls-result-badge");
  const barsContainer = document.getElementById("cls-prob-bars");
  const reasonsList = document.getElementById("cls-reasons-list");

  if (!container || !result) return;

  const risk = result.predicted_risk;
  badge.innerText = risk;
  badge.className = "badge";
  if (risk === "NORMAL") badge.classList.add("badge-normal");
  else if (risk === "WARNING") badge.classList.add("badge-warning");
  else if (risk === "CRITICAL") badge.classList.add("badge-critical");

  barsContainer.innerHTML = Object.entries(result.probabilities || {}).map(([cat, prob]) => {
    let barColor = "#10b981";
    if (cat === "WARNING") barColor = "#f59e0b";
    if (cat === "CRITICAL") barColor = "#ef4444";

    return `
      <div style="font-size: 0.76rem; display: flex; align-items: center; justify-content: space-between;">
        <span style="color: #cbd5e1; width: 80px;">${cat}</span>
        <div style="flex: 1; height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin: 0 10px;">
          <div style="width: ${prob}%; height: 100%; background: ${barColor}; border-radius: 4px; transition: width 0.4s ease;"></div>
        </div>
        <span style="font-weight: 600; color: #fff; width: 45px; text-align: right;">${prob}%</span>
      </div>
    `;
  }).join("");

  reasonsList.innerHTML = (result.explanations || []).map(r => `<li>${r}</li>`).join("");

  container.classList.add("show");
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
