// CinemaPredict - Ensemble Learning Module Controller

window.loadEnsembleMetrics = async function() {
  try {
    const res = await fetch("/api/ensemble/metrics");
    const data = await res.json();
    if (!data) return;

    renderEnsembleTable(data);
    renderEnsembleAccuracyChart(data);
    renderEnsemblePrecRecChart(data);
    renderEnsembleConfusionMatrix(data);
  } catch (err) {
    console.error("Failed to load ensemble metrics:", err);
  }
};

function renderEnsembleTable(data) {
  const tbody = document.getElementById("ensemble-metrics-table");
  if (!tbody) return;

  const models = ["Random Forest", "Bagging Classifier", "Voting Classifier", "Gradient Boosting"];
  const bestModel = data.best_model || "Gradient Boosting";

  document.getElementById("ensemble-best-badge").innerText = `Best Ensemble: ${bestModel}`;
  document.getElementById("ens-cm-model-name").innerText = `${bestModel} Confusion Matrix`;

  tbody.innerHTML = models.map(m => {
    const metrics = data[m];
    if (!metrics) return "";
    const isBest = (m === bestModel);
    const star = isBest ? `<i class="fa-solid fa-crown" style="color: #c084fc; margin-right: 6px;"></i>` : "";

    return `
      <tr style="${isBest ? 'background: rgba(168, 85, 247, 0.08); font-weight: 600;' : ''}">
        <td>${star}${m}</td>
        <td><span class="badge ${isBest ? 'badge-normal' : 'badge-blue'}">${metrics.accuracy}%</span></td>
        <td>${metrics.precision}%</td>
        <td>${metrics.recall}%</td>
        <td><strong style="color: ${isBest ? '#c084fc' : '#cbd5e1'};">${metrics.f1_score}%</strong></td>
      </tr>
    `;
  }).join("");
}

function renderEnsembleAccuracyChart(data) {
  const models = ["Random Forest", "Bagging Classifier", "Voting Classifier", "Gradient Boosting"];
  const accuracy = models.map(m => data[m] ? data[m].accuracy : 0);
  const f1 = models.map(m => data[m] ? data[m].f1_score : 0);

  const traceAcc = {
    x: models,
    y: accuracy,
    name: 'Accuracy (%)',
    type: 'bar',
    marker: { color: '#a855f7' }
  };

  const traceF1 = {
    x: models,
    y: f1,
    name: 'F1-Score (%)',
    type: 'bar',
    marker: { color: '#00f0ff' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'group',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Performance Score (%)',
      range: [0, 105]
    }
  };

  Plotly.newPlot('chart-ensemble-accuracy', [traceAcc, traceF1], layout, PLOTLY_CONFIG);
}

function renderEnsemblePrecRecChart(data) {
  const models = ["Random Forest", "Bagging Classifier", "Voting Classifier", "Gradient Boosting"];
  const precision = models.map(m => data[m] ? data[m].precision : 0);
  const recall = models.map(m => data[m] ? data[m].recall : 0);

  const tracePrec = {
    x: models,
    y: precision,
    name: 'Precision (%)',
    type: 'bar',
    marker: { color: '#38bdf8' }
  };

  const traceRec = {
    x: models,
    y: recall,
    name: 'Recall (%)',
    type: 'bar',
    marker: { color: '#fbbf24' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'group',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Precision / Recall (%)',
      range: [0, 105]
    }
  };

  Plotly.newPlot('chart-ensemble-prec-rec', [tracePrec, traceRec], layout, PLOTLY_CONFIG);
}

function renderEnsembleConfusionMatrix(data) {
  const bestModel = data.best_model || "Gradient Boosting";
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
      [0.5, '#7e22ce'],
      [1.0, '#c084fc']
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
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Predicted Risk Category'
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Actual Ground Truth Risk',
      autorange: 'reversed'
    },
    annotations: annotations
  };

  Plotly.newPlot('chart-ensemble-confusion-matrix', plotData, layout, PLOTLY_CONFIG);
}
