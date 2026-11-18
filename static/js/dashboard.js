// CinemaPredict - Overview Dashboard Controller

let dashboardDataCache = null;

window.loadDashboardData = async function() {
  try {
    const res = await fetch("/api/dashboard");
    const data = await res.json();
    if (data.error) {
      showToast(data.error, "error");
      return;
    }

    dashboardDataCache = data;
    updateKPIs(data.kpis, data.dataset_info);
    renderKDMPaymentTrend(data.charts.weekly_timeline);
    renderRiskDonut(data.charts.risk_distribution);
    renderDCPCorruptionTrend(data.charts.weekly_timeline);
    renderMonthlyPerformance(data.charts.monthly_performance);
    renderKDMTable(data.recent_kdm_records);
    setupKDMTableSearch();
  } catch (err) {
    console.error("Failed to load dashboard data:", err);
    showToast("Error connecting to cinema telemetry backend", "error");
  }
};

function updateKPIs(kpis, datasetInfo) {
  if (!kpis) return;
  document.getElementById("kpi-total-screens").innerText = kpis.total_screens;
  document.getElementById("kpi-total-deliveries").innerText = kpis.total_deliveries;
  document.getElementById("kpi-kdm-avail").innerText = `${kpis.kdm_availability_rate}%`;
  document.getElementById("kpi-dcp-corrupt").innerText = kpis.dcp_corruption_incidents;
  document.getElementById("kpi-firmware-alerts").innerText = kpis.firmware_alerts;
  document.getElementById("kpi-sound-sync").innerText = kpis.sound_sync_errors;
  document.getElementById("kpi-critical-incidents").innerText = kpis.critical_incidents;
  document.getElementById("kpi-avg-recovery").innerText = `${kpis.avg_recovery_time_min} min`;

  // Sidebar info
  if (datasetInfo) {
    const nature = datasetInfo.is_synthetic ? "Synthetic Sample" : "Uploaded Data";
    document.getElementById("sidebar-dataset-name").innerText = `${nature}: ${datasetInfo.filename || ''}`;
    document.getElementById("sidebar-dataset-screens").innerText = `${kpis.total_screens} Screens • ${kpis.total_deliveries} Ingests`;
  }
}

function renderKDMPaymentTrend(timeline) {
  if (!timeline) return;

  const traceKDM = {
    x: timeline.weeks,
    y: timeline.kdm_availability,
    name: 'KDM Availability (%)',
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#00f0ff', width: 3 },
    marker: { size: 6, color: '#00f0ff' }
  };

  const tracePayment = {
    x: timeline.weeks,
    y: timeline.payment_compliance,
    name: 'Payment Compliance (%)',
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#fbbf24', width: 2.5, dash: 'dot' },
    marker: { size: 5, color: '#fbbf24' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    title: false,
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Compliance Rate (%)',
      range: [0, 105]
    },
    hovermode: 'x unified'
  };

  Plotly.newPlot('chart-kdm-payment-trend', [traceKDM, tracePayment], layout, PLOTLY_CONFIG);
}

function renderRiskDonut(riskDist) {
  if (!riskDist) return;

  const data = [{
    values: [riskDist.NORMAL, riskDist.WARNING, riskDist.CRITICAL],
    labels: ['NORMAL', 'WARNING', 'CRITICAL'],
    type: 'pie',
    hole: 0.6,
    marker: {
      colors: ['#10b981', '#f59e0b', '#ef4444']
    },
    textinfo: 'label+percent',
    textfont: { family: 'Inter', size: 10, color: '#ffffff' },
    hoverinfo: 'label+value+percent'
  }];

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    showlegend: true,
    margin: { t: 20, r: 20, l: 20, b: 20 },
    legend: { orientation: 'h', x: 0.1, y: -0.15 }
  };

  Plotly.newPlot('chart-risk-donut', data, layout, PLOTLY_CONFIG);
}

function renderDCPCorruptionTrend(timeline) {
  if (!timeline) return;

  const traceCorruption = {
    x: timeline.weeks,
    y: timeline.dcp_corruption,
    name: 'Avg DCP Corruption (%)',
    type: 'bar',
    marker: { color: 'rgba(239, 68, 68, 0.65)' }
  };

  const traceRecovery = {
    x: timeline.weeks,
    y: timeline.avg_recovery_time,
    name: 'Recovery Time (min)',
    type: 'scatter',
    mode: 'lines+markers',
    yaxis: 'y2',
    line: { color: '#fbbf24', width: 2.5 }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Corruption (%)'
    },
    yaxis2: {
      title: 'Recovery (min)',
      overlaying: 'y',
      side: 'right',
      gridcolor: 'transparent',
      color: '#fbbf24'
    },
    hovermode: 'x unified'
  };

  Plotly.newPlot('chart-dcp-corruption-trend', [traceCorruption, traceRecovery], layout, PLOTLY_CONFIG);
}

function renderMonthlyPerformance(monthly) {
  if (!monthly) return;

  const traceNormal = {
    x: monthly.months,
    y: monthly.normal,
    name: 'Normal',
    type: 'bar',
    marker: { color: '#10b981' }
  };

  const traceWarning = {
    x: monthly.months,
    y: monthly.warning,
    name: 'Warning',
    type: 'bar',
    marker: { color: '#f59e0b' }
  };

  const traceCritical = {
    x: monthly.months,
    y: monthly.critical,
    name: 'Critical',
    type: 'bar',
    marker: { color: '#ef4444' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'stack',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Total Deliveries'
    }
  };

  Plotly.newPlot('chart-monthly-perf', [traceNormal, traceWarning, traceCritical], layout, PLOTLY_CONFIG);
}

function renderKDMTable(records) {
  const tbody = document.getElementById("kdm-table-body");
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #64748b;">No delivery telemetry records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
    let riskBadge = `<span class="badge badge-normal"><i class="fa-solid fa-check"></i> NORMAL</span>`;
    if (r.delivery_risk === "WARNING") {
      riskBadge = `<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> WARNING</span>`;
    } else if (r.delivery_risk === "CRITICAL") {
      riskBadge = `<span class="badge badge-critical"><i class="fa-solid fa-skull-crossbones"></i> CRITICAL</span>`;
    }

    const payClass = r.payment_status === "Completed" ? "color: #10b981;" : "color: #f59e0b; font-weight: 600;";
    const kdmClass = r.kdm_issued === "Issued" ? "color: #10b981;" : "color: #ef4444; font-weight: 600;";
    const expClass = r.kdm_expiry === "Valid Active" ? "color: #cbd5e1;" : "color: #f59e0b; font-weight: 600;";
    const decClass = r.decryption_status === "Decrypted OK" ? "color: #10b981;" : "color: #ef4444; font-weight: 600;";

    return `
      <tr>
        <td><strong>Week ${r.week}</strong></td>
        <td><span class="badge badge-blue">${r.cinema_screen}</span></td>
        <td style="${payClass}">${r.payment_status}</td>
        <td style="${kdmClass}">${r.kdm_issued}</td>
        <td style="${expClass}">${r.kdm_expiry}</td>
        <td style="${decClass}">${r.decryption_status}</td>
        <td>${riskBadge}</td>
        <td><strong>${r.recovery_time_min}m</strong></td>
      </tr>
    `;
  }).join("");
}

function setupKDMTableSearch() {
  const searchInput = document.getElementById("kdm-table-search");
  if (!searchInput) return;

  searchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase().trim();
    if (!dashboardDataCache || !dashboardDataCache.recent_kdm_records) return;

    const filtered = dashboardDataCache.recent_kdm_records.filter(r => 
      r.cinema_screen.toLowerCase().includes(term) ||
      r.delivery_risk.toLowerCase().includes(term) ||
      `week ${r.week}`.includes(term)
    );
    renderKDMTable(filtered);
  });
}
