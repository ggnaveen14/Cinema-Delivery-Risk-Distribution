// CinemaPredict - Dataset Management & Ingest Controller

window.loadDatasetPreview = async function() {
  try {
    const res = await fetch("/api/dataset/preview?limit=80");
    const data = await res.json();
    if (!data) return;

    renderDatasetMetadata(data.dataset_info, data.total_records, data.statistics);
    renderPreviewTable(data.columns, data.records);
    setupUploadHandlers();
  } catch (err) {
    console.error("Failed to load dataset preview:", err);
  }
};

function renderDatasetMetadata(info, totalRecords, stats) {
  if (info) {
    document.getElementById("meta-filename").innerText = info.filename || "sample_cinema_delivery.xlsx";
    document.getElementById("meta-records").innerText = `${totalRecords || info.row_count} Ingest Records`;
    
    const synBadge = document.getElementById("meta-synthetic");
    if (synBadge) {
      synBadge.innerText = info.is_synthetic ? "Synthetic Demonstration" : "Operational Telemetry";
      synBadge.className = info.is_synthetic ? "badge badge-warning" : "badge badge-normal";
    }
  }

  if (stats) {
    const screensCount = stats.unique_screens || 20;
    document.getElementById("meta-screens").innerText = `${screensCount} Monitored Auditoriums`;
  }
}

function renderPreviewTable(columns, records) {
  const thead = document.getElementById("preview-thead");
  const tbody = document.getElementById("preview-tbody");

  if (!thead || !tbody) return;

  if (!columns || columns.length === 0 || !records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center;">No records available.</td></tr>`;
    return;
  }

  thead.innerHTML = `<tr>${columns.map(c => `<th>${c.replace(/_/g, ' ').toUpperCase()}</th>`).join("")}</tr>`;

  tbody.innerHTML = records.map(r => {
    return `<tr>${columns.map(c => {
      let val = r[c];
      if (typeof val === 'number') {
        val = Number.isInteger(val) ? val : val.toFixed(1);
      }
      if (c === 'delivery_risk') {
        if (val === 'CRITICAL') return `<td><span class="badge badge-critical">${val}</span></td>`;
        if (val === 'WARNING') return `<td><span class="badge badge-warning">${val}</span></td>`;
        return `<td><span class="badge badge-normal">${val}</span></td>`;
      }
      return `<td>${val !== null && val !== undefined ? val : ''}</td>`;
    }).join("")}</tr>`;
  }).join("");
}

function setupUploadHandlers() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("dataset-file-input");
  const statusEl = document.getElementById("upload-status");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--accent-cyan)";
    dropZone.style.background = "rgba(0, 240, 255, 0.08)";
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "var(--border-accent)";
    dropZone.style.background = "rgba(0, 240, 255, 0.02)";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--border-accent)";
    dropZone.style.background = "rgba(0, 240, 255, 0.02)";
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const statusEl = document.getElementById("upload-status");
  statusEl.style.display = "block";
  statusEl.innerHTML = `
    <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid var(--accent-cyan); padding: 12px; border-radius: 8px; font-size: 0.82rem; color: #fff;">
      <i class="fa-solid fa-spinner fa-spin" style="margin-right: 8px; color: var(--accent-cyan);"></i>
      Uploading, validating schema, imputing missing values, and retraining ML models...
    </div>
  `;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/dataset/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (!data.success) {
      statusEl.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; padding: 12px; border-radius: 8px; font-size: 0.82rem; color: #fca5a5;">
          <i class="fa-solid fa-circle-xmark" style="margin-right: 8px;"></i>
          ${data.error}
        </div>
      `;
      showToast(data.error, "error");
      return;
    }

    const cs = data.cleaning_stats || {};
    statusEl.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; padding: 12px; border-radius: 8px; font-size: 0.82rem; color: #6ee7b7;">
        <i class="fa-solid fa-circle-check" style="margin-right: 8px;"></i>
        ${data.message} &bull; Duplicates dropped: ${cs.duplicates_removed || 0} &bull; Missing imputed: ${cs.missing_values_detected || 0}
      </div>
    `;

    document.getElementById("meta-duplicates").innerText = cs.duplicates_removed || 0;
    document.getElementById("meta-missing").innerText = cs.missing_values_detected || 0;

    showToast("Dataset loaded! ML pipelines retrained successfully.", "success");

    // Refresh active views
    window.loadDatasetPreview();
    if (window.loadDashboardData) window.loadDashboardData();
  } catch (err) {
    console.error("Upload error:", err);
    statusEl.innerHTML = `
      <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; padding: 12px; border-radius: 8px; font-size: 0.82rem; color: #fca5a5;">
        <i class="fa-solid fa-circle-xmark" style="margin-right: 8px;"></i> Upload failed.
      </div>
    `;
    showToast("Server error during upload", "error");
  }
}
