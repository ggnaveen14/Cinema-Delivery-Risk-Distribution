// CinemaPredict - Hidden Markov Model Controller

let hmmDataCache = null;

window.loadHMMResults = async function() {
  try {
    const res = await fetch("/api/hmm/results");
    const data = await res.json();
    if (!data) return;

    hmmDataCache = data;
    updateHMMPerformance(data.performance);
    renderInitialStateProbabilities(data.initial_state_probabilities);
    renderTransitionHeatmap(data.transition_matrix);
    renderEmissionHeatmap(data.emission_matrix);
    renderEmissionDistributions(data.emission_profiles);
    setupHMMTimeline(data.screen_timelines, data.available_timeline_screens);
  } catch (err) {
    console.error("Failed to load HMM results:", err);
  }
};

function updateHMMPerformance(perf) {
  if (!perf) return;

  document.getElementById("hmm-train-ll").innerText = perf.train_log_likelihood;
  document.getElementById("hmm-test-ll").innerText = perf.test_log_likelihood;
  document.getElementById("hmm-train-norm").innerText = `${perf.train_ll_per_obs} /obs`;
  document.getElementById("hmm-test-norm").innerText = `${perf.test_ll_per_obs} /obs`;

  document.getElementById("hmm-train-obs").innerText = `${perf.train_screens_count} screens (${perf.train_sequences_length} obs)`;
  document.getElementById("hmm-test-obs").innerText = `${perf.test_screens_count} screens (${perf.test_sequences_length} obs)`;
}

function renderInitialStateProbabilities(initProbs) {
  if (!initProbs) return;

  const trace = {
    x: initProbs.map(p => p.state),
    y: initProbs.map(p => p.probability),
    type: 'bar',
    marker: {
      color: initProbs.map(p => p.color)
    },
    text: initProbs.map(p => `${(p.probability * 100).toFixed(1)}%`),
    textposition: 'auto',
    textfont: { family: 'Inter', color: '#fff', size: 11 }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Initial Probability &pi;',
      range: [0, 1.05]
    }
  };

  Plotly.newPlot('chart-hmm-initial-probs', [trace], layout, PLOTLY_CONFIG);
}

function renderTransitionHeatmap(transMatrix) {
  if (!transMatrix || !transMatrix.matrix) return;

  const states = transMatrix.states;
  const zValues = transMatrix.matrix;

  const plotData = [{
    z: zValues,
    x: states,
    y: states,
    type: 'heatmap',
    colorscale: [
      [0.0, '#0b1220'],
      [0.5, '#7e22ce'],
      [1.0, '#fbbf24']
    ],
    showscale: true,
    hoverongaps: false
  }];

  const annotations = [];
  for (let i = 0; i < states.length; i++) {
    for (let j = 0; j < states.length; j++) {
      annotations.push({
        x: states[j],
        y: states[i],
        text: `${(zValues[i][j] * 100).toFixed(1)}%`,
        font: { family: 'Inter', size: 12, color: '#ffffff', weight: 'bold' },
        showarrow: false
      });
    }
  }

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Transitioned State (Time t+1)'
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Current State (Time t)',
      autorange: 'reversed'
    },
    annotations: annotations
  };

  Plotly.newPlot('chart-hmm-transition-heatmap', plotData, layout, PLOTLY_CONFIG);
}

function renderEmissionHeatmap(emMatrix) {
  if (!emMatrix || !emMatrix.matrix) return;

  const states = emMatrix.states;
  const observations = emMatrix.observations;
  const zValues = emMatrix.matrix;

  const plotData = [{
    z: zValues,
    x: observations,
    y: states,
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
  for (let i = 0; i < states.length; i++) {
    for (let j = 0; j < observations.length; j++) {
      annotations.push({
        x: observations[j],
        y: states[i],
        text: `${(zValues[i][j] * 100).toFixed(0)}%`,
        font: { family: 'Inter', size: 10, color: '#ffffff', weight: 'bold' },
        showarrow: false
      });
    }
  }

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    margin: { t: 30, r: 25, l: 110, b: 70 },
    xaxis: {
      ...PLOTLY_DARK_LAYOUT.xaxis,
      title: 'Observable Operational Condition',
      tickangle: -25
    },
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Hidden Operational State',
      autorange: 'reversed'
    },
    annotations: annotations
  };

  Plotly.newPlot('chart-hmm-emission-heatmap', plotData, layout, PLOTLY_CONFIG);
}

function renderEmissionDistributions(emissions) {
  if (!emissions) return;

  const states = emissions.map(e => e.state_name);
  const corruption = emissions.map(e => e.means.dcp_corruption_pct);
  const latency = emissions.map(e => e.means.network_delay_ms);
  const kdmAvail = emissions.map(e => e.means.kdm_available_pct);
  const soundSync = emissions.map(e => e.means.sound_sync_error_ms);

  const traceCorr = {
    x: states,
    y: corruption,
    name: 'Avg DCP Corruption (%)',
    type: 'bar',
    marker: { color: '#ef4444' }
  };

  const traceKDM = {
    x: states,
    y: kdmAvail,
    name: 'KDM Availability (%)',
    type: 'bar',
    marker: { color: '#10b981' }
  };

  const traceLatency = {
    x: states,
    y: latency,
    name: 'Network Latency (ms)',
    type: 'bar',
    marker: { color: '#38bdf8' }
  };

  const traceSound = {
    x: states,
    y: soundSync,
    name: 'Sound Offset (ms)',
    type: 'bar',
    marker: { color: '#fbbf24' }
  };

  const layout = {
    ...PLOTLY_DARK_LAYOUT,
    barmode: 'group',
    yaxis: {
      ...PLOTLY_DARK_LAYOUT.yaxis,
      title: 'Learned Feature Value'
    }
  };

  Plotly.newPlot('chart-hmm-emissions', [traceKDM, traceCorr, traceLatency, traceSound], layout, PLOTLY_CONFIG);
}

function setupHMMTimeline(screenTimelines, availableScreens) {
  const select = document.getElementById("hmm-timeline-screen-select");
  if (!select || !availableScreens || availableScreens.length === 0) return;

  select.innerHTML = availableScreens.map(scr => `<option value="${scr}">${scr}</option>`).join("");

  const updateChart = (screenId) => {
    const timeline = (screenTimelines && screenTimelines[screenId]) ? screenTimelines[screenId] : [];
    if (timeline.length === 0) return;

    const weeks = timeline.map(t => `W${t.week}`);
    const stateIds = timeline.map(t => t.state_id);
    const stateNames = timeline.map(t => t.state_name);
    const colors = timeline.map(t => t.color);

    const trace = {
      x: weeks,
      y: stateIds,
      text: stateNames,
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#c084fc', width: 2.5, shape: 'hv' },
      marker: {
        size: 11,
        color: colors,
        line: { color: '#ffffff', width: 1.5 }
      }
    };

    const layout = {
      ...PLOTLY_DARK_LAYOUT,
      yaxis: {
        ...PLOTLY_DARK_LAYOUT.yaxis,
        title: 'Inferred Operational State',
        tickvals: [0, 1, 2],
        ticktext: ['0: STABLE', '1: DEGRADED', '2: CRITICAL']
      },
      xaxis: {
        ...PLOTLY_DARK_LAYOUT.xaxis,
        title: 'Weekly Timeline Sequence'
      }
    };

    Plotly.newPlot('chart-hmm-timeline', [trace], layout, PLOTLY_CONFIG);
  };

  updateChart(availableScreens[0]);

  select.addEventListener("change", (e) => {
    updateChart(e.target.value);
  });
}
