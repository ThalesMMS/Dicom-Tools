const state = {
  filename: null,
  hasPixelData: false,
};

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const statusBar = document.getElementById('status');
const viewer = document.getElementById('viewer');
const detailsBody = document.getElementById('detailsBody');

const metaBtn = document.getElementById('metaBtn');
const statsBtn = document.getElementById('statsBtn');
const anonymizeBtn = document.getElementById('anonymizeBtn');
const validateBtn = document.getElementById('validateBtn');

const buttons = [metaBtn, statsBtn, anonymizeBtn, validateBtn];

function setStatus(message, tone = 'info') {
  // Map status updates to CSS classes for subtle color changes
  statusBar.textContent = message;
  statusBar.className = `status-bar ${tone === 'error' ? 'error' : tone === 'success' ? 'success' : ''}`;
}

function enableActions(enabled) {
  buttons.forEach((btn) => {
    btn.disabled = !enabled;
  });
}

function renderMetadata(data) {
  // Flatten nested metadata sections into cards grouped by category
  const groups = [
    ['Patient', data.patient],
    ['Study', data.study],
    ['Series', data.series],
    ['Image', data.image],
  ];

  const html = groups
    .map(([title, entries]) => {
      const body = Object.entries(entries)
        .map(([label, value]) => `<div class="meta-card"><div class="meta-label">${label}</div><div class="meta-value">${value}</div></div>`)
        .join('');
      return `<div><p class="eyebrow">${title}</p><div class="meta-grid">${body}</div></div>`;
    })
    .join('');

  detailsBody.innerHTML = html;
}

function renderStats(data) {
  // Present key statistics in a lightweight grid instead of a big table
  const entries = [
    ['Min', data.min],
    ['Max', data.max],
    ['Mean', data.mean.toFixed ? data.mean.toFixed(2) : data.mean],
    ['Median', data.median.toFixed ? data.median.toFixed(2) : data.median],
    ['Std', data.std.toFixed ? data.std.toFixed(2) : data.std],
    ['Range', data.range],
    ['Total Pixels', data.total_pixels],
    ['Unique', data.unique_values],
  ];

  const html = entries
    .map(([label, value]) => `<div class="stat-card"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`)
    .join('');

  detailsBody.innerHTML = `<div class="stats-grid">${html}</div>`;
}

function renderValidation(result) {
  const statusClass = result.valid ? 'success' : 'error';
  let html = `<div class="alert ${statusClass}">${result.valid ? 'File is valid.' : 'Validation failed.'}</div>`;

  if (result.errors?.length) {
    html += '<p class="eyebrow">Errors</p>' + result.errors.map((err) => `<div class="alert error">${err}</div>`).join('');
  }
  if (result.warnings?.length) {
    html += '<p class="eyebrow">Warnings</p>' + result.warnings.map((warn) => `<div class="alert">${warn}</div>`).join('');
  }

  detailsBody.innerHTML = html;
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  setStatus('Uploading…');
  enableActions(false);
  viewer.classList.add('muted');
  viewer.innerHTML = 'Processing…';

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Upload failed');
    }

    state.filename = data.filename;
    state.hasPixelData = Boolean(data.has_pixel_data);

    setStatus(`Loaded ${data.filename}`, 'success');
    enableActions(true);

    if (state.hasPixelData) {
      viewer.classList.remove('muted');
      viewer.innerHTML = `<img src="/api/image/${state.filename}" alt="DICOM preview">`;
    } else {
      viewer.classList.add('muted');
      viewer.textContent = 'File has no pixel data.';
    }

    renderMetadata(data.info);
  } catch (err) {
    setStatus(err.message, 'error');
    viewer.classList.add('muted');
    viewer.textContent = 'Upload failed.';
  }
}

async function loadMetadata() {
  if (!state.filename) return;
  setStatus('Loading metadata…');
  const res = await fetch(`/api/metadata/${state.filename}`);
  const data = await res.json();
  renderMetadata(data);
  setStatus('Metadata ready', 'success');
}

async function loadStats() {
  if (!state.filename || !state.hasPixelData) return;
  setStatus('Crunching numbers…');
  const res = await fetch(`/api/stats/${state.filename}`);
  const data = await res.json();
  renderStats(data);
  setStatus('Pixel stats ready', 'success');
}

async function anonymize() {
  if (!state.filename) return;
  setStatus('Anonymizing…');
  const res = await fetch(`/api/anonymize/${state.filename}`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok || !data.success) {
    setStatus(data.error || 'Anonymization failed', 'error');
    return;
  }
  setStatus('Anonymized file ready for download', 'success');
  window.location.href = `/api/download/${data.filename}`;
}

async function validate() {
  if (!state.filename) return;
  setStatus('Validating…');
  const res = await fetch(`/api/validate/${state.filename}`);
  const data = await res.json();
  renderValidation(data);
  setStatus(data.valid ? 'Valid DICOM' : 'Validation issues found', data.valid ? 'success' : 'error');
}

// Event wiring
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('dragover');
});
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) uploadFile(file);
});

metaBtn.addEventListener('click', loadMetadata);
statsBtn.addEventListener('click', loadStats);
anonymizeBtn.addEventListener('click', anonymize);
validateBtn.addEventListener('click', validate);

enableActions(false);
setStatus('Waiting for a DICOM file.');
