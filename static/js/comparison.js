// CinemaPredict - Comparative Performance Analysis Controller

window.loadComparisonData = async function() {
  try {
    const res = await fetch("/api/comparison/summary");
    const data = await res.json();
    if (!data) return;

    renderComparisonClassificationChart(data.classification);
    renderComparisonRegressionChart(data.regression);
    renderComprehensiveMatrix(data);
  } catch (err) {
    console.error("Failed to load comparison data:", err);
  }
};

function renderComparisonClassificationChart(cls) {
  if (!cls) return;

  const models = ["Logistic Regression", "Decision Tree", "Random Forest"];
  const accuracy = models.map(m => cls[m] ? cls[m].accuracy : 0);
  const f1 = models.map(m => cls[m] ? cls[m].f1_score : 0);

  const traceAcc = {
    x: models,
    y: accuracy,
    name: 'Accuracy (%)',
    type: 'bar',
    marker: { color: '#00f0ff' }
  };

  const traceF1 = {
    x: models,
    y: f1,
    name: 'F1-Score (%)',
    type: 'bar',
    marker: { color: '#fbbf24' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'group',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Score (%)',
      range: [0, 105]
    }
  };

  Plotly.newPlot('chart-comp-classification', [traceAcc, traceF1], layout, PLOTLY_CONFIG);
}

function renderComparisonRegressionChart(reg) {
  if (!reg) return;

  const models = ["Linear Regression", "Random Forest Regressor", "Gradient Boosting Regressor"];
  const mae = models.map(m => reg[m] ? reg[m].mae : 0);
  const rmse = models.map(m => reg[m] ? reg[m].rmse : 0);

  const traceMAE = {
    x: models,
    y: mae,
    name: 'MAE (Minutes)',
    type: 'bar',
    marker: { color: '#10b981' }
  };

  const traceRMSE = {
    x: models,
    y: rmse,
    name: 'RMSE (Minutes)',
    type: 'bar',
    marker: { color: '#ef4444' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'group',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Error (Lower is Better)'
    }
  };

  Plotly.newPlot('chart-comp-regression', [traceMAE, traceRMSE], layout, PLOTLY_CONFIG);
}

function renderComprehensiveMatrix(data) {
  const tbody = document.getElementById("comparison-matrix-body");
  if (!tbody) return;

  const rows = [];
  const cls = data.classification || {};
  const reg = data.regression || {};
  const clust = data.clustering || {};
  const hmmData = data.hmm || {};

  // Classification rows
  ["Random Forest", "Logistic Regression", "Decision Tree"].forEach(m => {
    if (cls[m]) {
      const isBest = (m === cls.best_model);
      rows.push(`
        <tr>
          <td><span class="badge badge-blue">Risk Classification</span></td>
          <td><strong>${m}</strong></td>
          <td>F1: <strong>${cls[m].f1_score}%</strong></td>
          <td>Accuracy: ${cls[m].accuracy}%</td>
          <td>Precision: ${cls[m].precision}% | Recall: ${cls[m].recall}%</td>
          <td><span class="badge ${isBest ? 'badge-normal' : 'badge-blue'}">${isBest ? 'Production Selected' : 'Benchmarked'}</span></td>
        </tr>
      `);
    }
  });

  // Regression rows
  ["Gradient Boosting Regressor", "Random Forest Regressor", "Linear Regression"].forEach(m => {
    if (reg[m]) {
      const isBest = (m === reg.best_model);
      rows.push(`
        <tr>
          <td><span class="badge badge-warning">Recovery Regression</span></td>
          <td><strong>${m}</strong></td>
          <td>R² Score: <strong>${reg[m].r2_score}</strong></td>
          <td>MAE: ${reg[m].mae} min</td>
          <td>RMSE: ${reg[m].rmse} min (${reg[m].accuracy_pct}% variance)</td>
          <td><span class="badge ${isBest ? 'badge-normal' : 'badge-blue'}">${isBest ? 'Production Selected' : 'Benchmarked'}</span></td>
        </tr>
      `);
    }
  });

  // Clustering row
  rows.push(`
    <tr>
      <td><span class="badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);">Unsupervised Clustering</span></td>
      <td><strong>K-Means Clustering</strong></td>
      <td>Optimal K: <strong>${clust.selected_k} Clusters</strong></td>
      <td>Silhouette: ${clust.best_silhouette}</td>
      <td>PCA 2D Spatial Projection &amp; Centroid Profiling</td>
      <td><span class="badge badge-normal">Active Pipeline</span></td>
    </tr>
  `);

  // HMM row
  rows.push(`
    <tr>
      <td><span class="badge" style="background: rgba(236, 72, 153, 0.15); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.3);">Sequential Dynamics</span></td>
      <td><strong>Gaussian HMM (hmmlearn)</strong></td>
      <td>Holdout Test LL: <strong>${hmmData.test_ll}</strong></td>
      <td>Train LL: ${hmmData.train_ll}</td>
      <td>${hmmData.test_ll_per_obs} /obs (Independent holdout sequences)</td>
      <td><span class="badge badge-normal">Active Pipeline</span></td>
    </tr>
  `);

  tbody.innerHTML = rows.join("");
}
