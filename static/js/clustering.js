// CinemaPredict - K-Means Clustering Controller

window.loadClusteringResults = async function() {
  try {
    const res = await fetch("/api/clustering/results");
    const data = await res.json();
    if (!data) return;

    renderElbowMethod(data.elbow_data);
    renderSilhouetteAnalysis(data.silhouette_data);
    renderPCAClusterScatter(data.pca_visualization);
    renderClusterProfiles(data.cluster_profiles);
    renderClusterRadar(data.cluster_profiles);
  } catch (err) {
    console.error("Failed to load clustering results:", err);
  }
};

function renderElbowMethod(elbowData) {
  if (!elbowData) return;

  const selectedK = elbowData.selected_k;
  document.getElementById("kmeans-k-badge").innerText = `Optimal K = ${selectedK} Selected`;

  const traceInertia = {
    x: elbowData.k_values,
    y: elbowData.inertias,
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Inertia (SSE)',
    line: { color: '#00f0ff', width: 3 },
    marker: { size: 7, color: '#00f0ff' }
  };

  // Highlight selected K point
  const selIdx = elbowData.k_values.indexOf(selectedK);
  const selInertia = selIdx !== -1 ? elbowData.inertias[selIdx] : elbowData.inertias[0];

  const traceSelected = {
    x: [selectedK],
    y: [selInertia],
    type: 'scatter',
    mode: 'markers',
    name: `Selected K = ${selectedK}`,
    marker: { size: 14, color: '#fbbf24', symbol: 'star' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Number of Clusters (K)',
      tickmode: 'linear',
      dtick: 1
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Inertia (Within-Cluster Sum of Squares)'
    }
  };

  Plotly.newPlot('chart-elbow-curve', [traceInertia, traceSelected], layout, PLOTLY_CONFIG);
}

function renderSilhouetteAnalysis(silData) {
  if (!silData) return;

  document.getElementById("kmeans-sil-badge").innerText = `Peak Score: ${silData.best_silhouette}`;

  const trace = {
    x: silData.k_values,
    y: silData.silhouettes,
    type: 'bar',
    marker: {
      color: silData.silhouettes.map(s => s === silData.best_silhouette ? '#fbbf24' : '#0284c7')
    }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Number of Clusters (K)',
      tickmode: 'linear',
      dtick: 1
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Silhouette Coefficient',
      range: [0, Math.max(...silData.silhouettes) * 1.35]
    }
  };

  Plotly.newPlot('chart-silhouette-scores', [trace], layout, PLOTLY_CONFIG);
}

function renderPCAClusterScatter(pcaData) {
  if (!pcaData || !pcaData.points) return;

  const points = pcaData.points;
  const clusterColors = ['#00f0ff', '#fbbf24', '#ef4444', '#10b981', '#a855f7', '#ec4899'];
  const clusters = [...new Set(points.map(p => p.cluster))].sort();

  const traces = clusters.map((c, i) => {
    const cPoints = points.filter(p => p.cluster === c);
    return {
      x: cPoints.map(p => p.pc1),
      y: cPoints.map(p => p.pc2),
      text: cPoints.map(p => `${p.cinema_screen} (Week ${p.time_step})`),
      mode: 'markers',
      type: 'scatter',
      name: `Cluster ${c}`,
      marker: {
        size: 7,
        color: clusterColors[i % clusterColors.length],
        opacity: 0.85
      }
    };
  });

  const varInfo = pcaData.explained_variance_ratio || [0, 0];
  document.getElementById("pca-var-badge").innerText = `PC1: ${varInfo[0]}% | PC2: ${varInfo[1]}% Variance`;

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    title: false,
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: `Principal Component 1 (${varInfo[0]}% variance)`
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: `Principal Component 2 (${varInfo[1]}% variance)`
    },
    hovermode: 'closest'
  };

  Plotly.newPlot('chart-pca-clusters', traces, layout, PLOTLY_CONFIG);
}

function renderClusterProfiles(profiles) {
  const container = document.getElementById("cluster-profiles-container");
  if (!container || !profiles) return;

  const clusterColors = ['#00f0ff', '#fbbf24', '#ef4444', '#10b981', '#a855f7'];

  container.innerHTML = profiles.map((p, i) => {
    const color = clusterColors[i % clusterColors.length];
    const m = p.means;

    return `
      <div style="background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-top: 3px solid ${color}; border-radius: 10px; padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <h4 style="font-size: 0.92rem; color: #fff; font-weight: 700;">${p.label}</h4>
          <span class="badge" style="background: rgba(255,255,255,0.06); color: ${color};">${p.percentage}%</span>
        </div>
        <p style="font-size: 0.76rem; color: #94a3b8; margin-bottom: 12px; line-height: 1.4;">${p.description}</p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.72rem; color: #cbd5e1; border-top: 1px solid var(--border-subtle); padding-top: 10px;">
          <div>Avg DCP Corruption: <strong>${m.dcp_corruption_pct}%</strong></div>
          <div>KDM Failure Rate: <strong>${m.kdm_failure_rate_pct}%</strong></div>
          <div>Avg Latency: <strong>${m.network_delay_ms} ms</strong></div>
          <div>Firmware Upgrades: <strong>${m.firmware_update_pct}%</strong></div>
          <div>Sound Offset: <strong>${m.sound_sync_error_ms} ms</strong></div>
          <div>Cluster Ingests: <strong>${p.size} runs</strong></div>
        </div>
      </div>
    `;
  }).join("");
}

function renderClusterRadar(profiles) {
  if (!profiles) return;

  const categories = ['DCP Corruption', 'KDM Failure', 'Network Delay', 'Firmware Req', 'Sound Sync Offset'];
  const clusterColors = ['#00f0ff', '#fbbf24', '#ef4444', '#10b981'];

  const traces = profiles.map((p, idx) => {
    const m = p.means;
    // Normalize values to 0-100 scale for clean radar comparison
    const values = [
      Math.min(100, m.dcp_corruption_pct * 3),
      m.kdm_failure_rate_pct,
      Math.min(100, (m.network_delay_ms / 300) * 100),
      m.firmware_update_pct,
      Math.min(100, (m.sound_sync_error_ms / 80) * 100)
    ];
    values.push(values[0]); // close the radar polygon

    return {
      type: 'scatterpolar',
      r: values,
      theta: [...categories, categories[0]],
      fill: 'toself',
      name: `Cluster ${p.cluster_id}: ${p.label.split(':')[1] || p.label}`,
      line: { color: clusterColors[idx % clusterColors.length] },
      fillcolor: `${clusterColors[idx % clusterColors.length]}18`
    };
  });

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 100],
        color: '#64748b',
        gridcolor: 'rgba(255, 255, 255, 0.06)'
      },
      angularaxis: {
        color: '#cbd5e1',
        gridcolor: 'rgba(255, 255, 255, 0.06)'
      },
      bgcolor: 'rgba(11, 18, 32, 0.5)'
    },
    showlegend: true
  };

  Plotly.newPlot('chart-cluster-radar', traces, layout, PLOTLY_CONFIG);
}
