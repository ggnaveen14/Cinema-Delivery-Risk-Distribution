// CinemaPredict - Main UI Navigation & Global Helpers

// Global Plotly Dark Theme Configuration
const PLOTLY_DARK_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(16, 26, 46, 0.4)',
  font: {
    family: 'Inter, sans-serif',
    color: '#94a3b8',
    size: 11
  },
  margin: { t: 30, r: 25, l: 45, b: 35 },
  xaxis: {
    gridcolor: 'rgba(255, 255, 255, 0.05)',
    zerolinecolor: 'rgba(255, 255, 255, 0.1)',
    color: '#94a3b8'
  },
  yaxis: {
    gridcolor: 'rgba(255, 255, 255, 0.05)',
    zerolinecolor: 'rgba(255, 255, 255, 0.1)',
    color: '#94a3b8'
  },
  legend: {
    font: { color: '#cbd5e1' },
    bgcolor: 'rgba(11, 18, 32, 0.7)'
  }
};

const PLOTLY_CONFIG = {
  responsive: true,
  displayModeBar: false
};

const TAB_TITLES = {
  dashboard: {
    title: "Overview Dashboard",
    subtitle: "Real-time digital cinema content delivery monitoring & key performance indicators"
  },
  classification: {
    title: "Cinema Delivery Risk Classification",
    subtitle: "Supervised risk classification comparing Logistic Regression, Decision Tree, Random Forest, & SVM"
  },
  ensemble: {
    title: "Ensemble Learning Module",
    subtitle: "Benchmarking Random Forest, Bagging Classifier, Voting Classifier, & Gradient Boosting"
  },
  regression: {
    title: "Cinema Delivery Recovery Time Prediction",
    subtitle: "Regression modeling predicting incident resolution duration in minutes (Linear, RF, SVR, GB)"
  },
  clustering: {
    title: "Cinema Delivery Failure Pattern Analysis",
    subtitle: "Unsupervised K-Means clustering, elbow curve, silhouette score, & 2D PCA failure signatures"
  },
  hmm: {
    title: "Sequential Cinema Delivery State Prediction (HMM)",
    subtitle: "Hidden Markov Model sequence dynamics, transition matrix, & emission distributions (hmmlearn)"
  },
  comparison: {
    title: "Research Results & Comparative Analysis",
    subtitle: "Full cross-algorithmic benchmark comparison matrix for PBL academic presentation"
  },
  optimizer: {
    title: "Intelligent Cinema Delivery Optimization",
    subtitle: "Proactive operational advisory & automated risk mitigation recommendations"
  },
  dataset: {
    title: "Excel Dataset Management & Ingest",
    subtitle: "Upload, validate, preprocess, deduplicate, and retrain ML pipelines"
  },
  reports: {
    title: "Report Generation & Export",
    subtitle: "Export comprehensive operational diagnostics in multi-sheet Excel & PDF formats"
  }
};

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupQuickReportButton();
  
  if (window.loadDashboardData) {
    window.loadDashboardData();
  }
});

function setupNavigation() {
  const navLinks = document.querySelectorAll(".nav-link");
  const tabPanes = document.querySelectorAll(".tab-pane");

  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const tabId = link.getAttribute("data-tab");
      if (!tabId) return;

      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      tabPanes.forEach(pane => pane.classList.remove("active"));
      const targetPane = document.getElementById(`tab-${tabId}`);
      if (targetPane) {
        targetPane.classList.add("active");
      }

      const meta = TAB_TITLES[tabId] || { title: "CinemaPredict", subtitle: "" };
      document.getElementById("page-title").innerText = meta.title;
      document.getElementById("page-subtitle").innerText = meta.subtitle;

      triggerTabLoad(tabId);
    });
  });
}

function triggerTabLoad(tabId) {
  switch (tabId) {
    case "dashboard":
      if (window.loadDashboardData) window.loadDashboardData();
      break;
    case "classification":
      if (window.loadClassificationMetrics) window.loadClassificationMetrics();
      break;
    case "ensemble":
      if (window.loadEnsembleMetrics) window.loadEnsembleMetrics();
      break;
    case "regression":
      if (window.loadRegressionMetrics) window.loadRegressionMetrics();
      break;
    case "clustering":
      if (window.loadClusteringResults) window.loadClusteringResults();
      break;
    case "hmm":
      if (window.loadHMMResults) window.loadHMMResults();
      break;
    case "comparison":
      if (window.loadComparisonData) window.loadComparisonData();
      break;
    case "optimizer":
      if (window.loadOptimizationRecommendations) window.loadOptimizationRecommendations();
      break;
    case "dataset":
      if (window.loadDatasetPreview) window.loadDatasetPreview();
      break;
  }
}

function setupQuickReportButton() {
  const btn = document.getElementById("btn-quick-report");
  if (btn) {
    btn.addEventListener("click", () => {
      window.location.href = "/api/reports/download/pdf";
      showToast("Generating executive PDF report...", "info");
    });
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.style.padding = "12px 18px";
  toast.style.borderRadius = "8px";
  toast.style.fontSize = "0.84rem";
  toast.style.fontWeight = "500";
  toast.style.color = "#ffffff";
  toast.style.boxShadow = "0 6px 16px rgba(0,0,0,0.5)";
  toast.style.display = "flex";
  toast.style.alignItems = "center";
  toast.style.gap = "10px";
  toast.style.minWidth = "260px";
  toast.style.maxWidth = "380px";
  toast.style.animation = "fadeIn 0.25s ease";

  let icon = "fa-circle-info";
  if (type === "success") {
    toast.style.background = "linear-gradient(135deg, #059669 0%, #047857 100%)";
    icon = "fa-circle-check";
  } else if (type === "warning") {
    toast.style.background = "linear-gradient(135deg, #d97706 0%, #b45309 100%)";
    icon = "fa-triangle-exclamation";
  } else if (type === "error") {
    toast.style.background = "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)";
    icon = "fa-circle-xmark";
  } else {
    toast.style.background = "linear-gradient(135deg, #7e22ce 0%, #2563eb 100%)";
  }

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
