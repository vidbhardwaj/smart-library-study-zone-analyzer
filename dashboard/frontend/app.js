/**
 * Smart Library Study Zone Analyzer - Frontend Controller
 * Connects to FastAPI backend, renders real-time sensor metrics,
 * animated gauges, responsive canvas charts, and hardware simulator.
 */

// Determine API Base URL automatically
const API_BASE = (window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file"))
  ? window.location.origin
  : "http://127.0.0.1:8000";

let currentZoneId = 1;
let activeChartType = "climate"; // "climate" or "sensory"
let readingsHistory = [];
let isAutoSimulating = false;
let autoSimInterval = null;
let packetCount = 0;

// DOM Elements
const dom = {
  zonePills: document.querySelectorAll(".zone-pill"),
  statusBadge: document.getElementById("systemStatusBadge"),
  statusDot: document.querySelector(".status-dot"),
  statusText: document.getElementById("systemStatusText"),
  refreshBtn: document.getElementById("refreshBtn"),
  refreshIcon: document.getElementById("refreshIcon"),

  // Hero Score
  overallScoreVal: document.getElementById("overallScoreVal"),
  scoreGaugeProgress: document.getElementById("scoreGaugeProgress"),
  zoneLocationTag: document.getElementById("zoneLocationTag"),
  zoneTitle: document.getElementById("zoneTitle"),
  ratingBadge: document.getElementById("ratingBadge"),
  ratingText: document.getElementById("ratingText"),
  lastSyncTime: document.getElementById("lastSyncTime"),
  scoreDesc: document.getElementById("scoreDescription"),

  // Sub-scores
  acousticVal: document.getElementById("acousticScoreVal"),
  acousticBar: document.getElementById("acousticBar"),
  thermalVal: document.getElementById("thermalScoreVal"),
  thermalBar: document.getElementById("thermalBar"),
  visualVal: document.getElementById("visualScoreVal"),
  visualBar: document.getElementById("visualBar"),
  occupancyVal: document.getElementById("occupancyScoreVal"),
  occupancyBar: document.getElementById("occupancyBar"),

  // Sensors
  tempValue: document.getElementById("tempValue"),
  tempBarFill: document.getElementById("tempBarFill"),
  tempChip: document.getElementById("tempStatusChip"),
  humValue: document.getElementById("humValue"),
  humBarFill: document.getElementById("humBarFill"),
  humChip: document.getElementById("humStatusChip"),
  lightValue: document.getElementById("lightValue"),
  lightBarFill: document.getElementById("lightBarFill"),
  lightChip: document.getElementById("lightStatusChip"),
  noiseValue: document.getElementById("noiseValue"),
  noiseBarFill: document.getElementById("noiseBarFill"),
  noiseChip: document.getElementById("noiseStatusChip"),
  occupancyValue: document.getElementById("occupancyValue"),
  capacityMax: document.getElementById("capacityMax"),
  occupancyChip: document.getElementById("occupancyStatusChip"),
  capacityPercentText: document.getElementById("capacityPercentText"),
  rfidSlotsContainer: document.getElementById("rfidSlotsContainer"),

  // Analytics & Lists
  recommendationsList: document.getElementById("recommendationsList"),
  allZonesList: document.getElementById("allZonesList"),
  chartCanvas: document.getElementById("telemetryChart"),
  chartTabs: document.querySelectorAll(".chart-tab"),

  // Terminal Log
  terminalLog: document.getElementById("terminalLog"),
  packetCountBadge: document.getElementById("packetCountBadge"),
  clearLogBtn: document.getElementById("clearLogBtn"),

  // Simulator
  openSimBtn: document.getElementById("openSimBtn"),
  closeSimBtn: document.getElementById("closeSimBtn"),
  simModal: document.getElementById("simModal"),
  simTemp: document.getElementById("simTemp"),
  simTempVal: document.getElementById("simTempVal"),
  simHum: document.getElementById("simHum"),
  simHumVal: document.getElementById("simHumVal"),
  simLight: document.getElementById("simLight"),
  simLightVal: document.getElementById("simLightVal"),
  simNoise: document.getElementById("simNoise"),
  simNoiseVal: document.getElementById("simNoiseVal"),
  simOcc: document.getElementById("simOcc"),
  simOccVal: document.getElementById("simOccVal"),
  sendSimPacketBtn: document.getElementById("sendSimPacketBtn"),
  autoSimToggle: document.getElementById("autoSimToggle"),
  presetIdeal: document.getElementById("presetIdeal"),
  presetNoisy: document.getElementById("presetNoisy"),
  presetDark: document.getElementById("presetDark"),
};

// ==============================================================================
// Initialization & Polling
// ==============================================================================

async function init() {
  setupEventListeners();
  setupCanvas();
  await checkSystemStatus();
  await fetchAllZones();
  await refreshActiveZoneData();

  // Polling every 3 seconds
  setInterval(async () => {
    await refreshActiveZoneData();
  }, 3000);
}

function setupEventListeners() {
  // Zone Pills
  dom.zonePills.forEach(pill => {
    pill.addEventListener("click", () => {
      dom.zonePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      currentZoneId = parseInt(pill.dataset.zone, 10);
      logTerminal(`[NAV] Switched view to Zone ${currentZoneId}`, "info");
      refreshActiveZoneData();
    });
  });

  // Refresh Button
  dom.refreshBtn.addEventListener("click", async () => {
    dom.refreshIcon.style.transform = "rotate(360deg)";
    dom.refreshIcon.style.transition = "transform 0.6s ease";
    setTimeout(() => { dom.refreshIcon.style.transform = ""; }, 600);
    await checkSystemStatus();
    await fetchAllZones();
    await refreshActiveZoneData();
  });

  // Chart Tabs
  dom.chartTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      dom.chartTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      activeChartType = tab.dataset.chart;
      drawChart();
    });
  });

  // Clear Terminal
  dom.clearLogBtn.addEventListener("click", () => {
    dom.terminalLog.innerHTML = `<div class="terminal-line info">[LOG] Console cleared.</div>`;
  });

  // Simulator Modal
  dom.openSimBtn.addEventListener("click", () => dom.simModal.classList.add("open"));
  dom.closeSimBtn.addEventListener("click", () => dom.simModal.classList.remove("open"));
  dom.simModal.addEventListener("click", (e) => {
    if (e.target === dom.simModal) dom.simModal.classList.remove("open");
  });

  // Simulator Sliders
  dom.simTemp.addEventListener("input", (e) => dom.simTempVal.textContent = `${e.target.value} °C`);
  dom.simHum.addEventListener("input", (e) => dom.simHumVal.textContent = `${e.target.value} %`);
  dom.simLight.addEventListener("input", (e) => dom.simLightVal.textContent = `${e.target.value} lx`);
  dom.simNoise.addEventListener("input", (e) => dom.simNoiseVal.textContent = `${e.target.value} dB`);
  dom.simOcc.addEventListener("input", (e) => dom.simOccVal.textContent = `${e.target.value} / 2`);

  // Simulator Presets
  dom.presetIdeal.addEventListener("click", () => {
    setSliderValues(22.5, 48, 450, 36, 1);
  });
  dom.presetNoisy.addEventListener("click", () => {
    setSliderValues(26.0, 62, 520, 78, 2);
  });
  dom.presetDark.addEventListener("click", () => {
    setSliderValues(29.0, 75, 120, 48, 2);
  });

  // Transmit Simulated Packet
  dom.sendSimPacketBtn.addEventListener("click", async () => {
    await sendSimulatedTelemetry();
  });

  // Toggle Auto Simulator
  dom.autoSimToggle.addEventListener("click", () => {
    if (isAutoSimulating) {
      clearInterval(autoSimInterval);
      isAutoSimulating = false;
      dom.autoSimToggle.textContent = "Start Auto Stream";
      dom.autoSimToggle.classList.remove("btn-primary");
      logTerminal("[SIMULATOR] Auto-streaming paused.", "warn");
    } else {
      isAutoSimulating = true;
      dom.autoSimToggle.textContent = "Stop Auto Stream";
      dom.autoSimToggle.classList.add("btn-primary");
      logTerminal("[SIMULATOR] Auto-streaming active (packet every 3s).", "info");
      autoSimInterval = setInterval(sendRandomDriftTelemetry, 3000);
    }
  });

  window.addEventListener("resize", () => drawChart());
}

function setSliderValues(temp, hum, light, noise, occ) {
  dom.simTemp.value = temp; dom.simTempVal.textContent = `${temp} °C`;
  dom.simHum.value = hum; dom.simHumVal.textContent = `${hum} %`;
  dom.simLight.value = light; dom.simLightVal.textContent = `${light} lx`;
  dom.simNoise.value = noise; dom.simNoiseVal.textContent = `${noise} dB`;
  dom.simOcc.value = occ; dom.simOccVal.textContent = `${occ} / 2`;
}

// ==============================================================================
// Backend API Requests
// ==============================================================================

async function checkSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (res.ok) {
      const data = await res.json();
      dom.statusText.textContent = `${data.database_driver.split(' ')[0]} Connected`;
      dom.statusBadge.style.background = "rgba(16, 185, 129, 0.15)";
      dom.statusBadge.style.color = "#10b981";
      dom.statusDot.classList.add("online");
    }
  } catch (err) {
    dom.statusText.textContent = "API Reconnecting...";
    dom.statusBadge.style.background = "rgba(239, 68, 68, 0.15)";
    dom.statusBadge.style.color = "#ef4444";
    dom.statusDot.classList.remove("online");
  }
}

async function fetchAllZones() {
  try {
    const res = await fetch(`${API_BASE}/zones`);
    if (res.ok) {
      const zones = await res.json();
      renderAllZones(zones);
    }
  } catch (err) {
    console.error("Failed to fetch zones:", err);
  }
}

async function refreshActiveZoneData() {
  try {
    // 1. Fetch latest reading for active zone
    const resLatest = await fetch(`${API_BASE}/zones/${currentZoneId}/latest`);
    if (resLatest.ok) {
      const latest = await resLatest.json();
      renderZoneDetails(latest);
    } else {
      // Zone might not have readings yet
      handleEmptyZone();
    }

    // 2. Fetch recent readings history for the chart
    const resHistory = await fetch(`${API_BASE}/readings?zone_id=${currentZoneId}&limit=15`);
    if (resHistory.ok) {
      const history = await resHistory.json();
      readingsHistory = history.reverse(); // chronological order
      drawChart();
    }

  } catch (err) {
    console.error("Error refreshing zone data:", err);
  }
}

async function sendSimulatedTelemetry() {
  const payload = {
    zone_id: currentZoneId,
    temperature_c: parseFloat(dom.simTemp.value),
    humidity_percent: parseFloat(dom.simHum.value),
    light_lux: parseFloat(dom.simLight.value),
    noise_db: parseFloat(dom.simNoise.value),
    occupancy: parseInt(dom.simOcc.value, 10),
    capacity: 2
  };

  try {
    const res = await fetch(`${API_BASE}/readings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const result = await res.json();
      packetCount++;
      dom.packetCountBadge.textContent = `${packetCount} packets`;
      logTerminal(
        `[INGEST] Zone ${payload.zone_id} | T: ${payload.temperature_c}°C, H: ${payload.humidity_percent}%, Occ: ${payload.occupancy}/2 -> Score: ${result.reading.study_score} (${result.reading.study_rating})`,
        "success"
      );
      await refreshActiveZoneData();
      await fetchAllZones();
    } else {
      logTerminal(`[POST ERROR] HTTP ${res.status}: Failed to submit reading`, "error");
    }
  } catch (err) {
    logTerminal(`[NETWORK ERROR] Could not reach backend: ${err.message}`, "error");
  }
}

function sendRandomDriftTelemetry() {
  // Drift current slider values realistically
  let t = parseFloat(dom.simTemp.value) + (Math.random() * 0.6 - 0.3);
  let h = parseFloat(dom.simHum.value) + (Math.random() * 2 - 1);
  let l = parseFloat(dom.simLight.value) + (Math.random() * 20 - 10);
  let n = parseFloat(dom.simNoise.value) + (Math.random() * 4 - 2);
  let occ = parseInt(dom.simOcc.value, 10);

  // Occasional random RFID tap toggle
  if (Math.random() < 0.2) {
    occ = occ === 0 ? 1 : (occ === 1 ? (Math.random() > 0.5 ? 2 : 0) : 1);
  }

  t = Math.max(18, Math.min(35, Math.round(t * 10) / 10));
  h = Math.max(30, Math.min(80, Math.round(h)));
  l = Math.max(100, Math.min(800, Math.round(l)));
  n = Math.max(30, Math.min(85, Math.round(n)));

  setSliderValues(t, h, l, n, occ);
  sendSimulatedTelemetry();
}

// ==============================================================================
// UI Rendering Functions
// ==============================================================================

function renderZoneDetails(data) {
  const score = data.study_score || 0;
  const rating = data.study_rating || "Unknown";
  const details = data.score_details || {};
  const sub = details.sub_scores || { acoustic: 80, thermal: 80, visual: 80, occupancy: 80 };

  // Zone Name & Location
  dom.zoneTitle.textContent = data.zone_name;
  dom.zoneLocationTag.textContent = `Zone ${data.zone_id} • Assigned Node`;
  dom.lastSyncTime.textContent = `Updated: ${data.recorded_at.split(' ')[1] || data.recorded_at}`;

  // Gauge & Overall Score
  dom.overallScoreVal.textContent = score;
  const circumference = 427; // 2 * PI * 68
  const offset = circumference - (score / 100) * circumference;
  dom.scoreGaugeProgress.style.strokeDashoffset = offset;

  // Rating color & badge
  const color = details.color || (score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444");
  dom.scoreGaugeProgress.style.stroke = color;
  dom.ratingBadge.style.color = color;
  dom.ratingBadge.style.borderColor = `${color}44`;
  dom.ratingBadge.style.background = `${color}18`;
  dom.ratingText.textContent = rating;

  // Sub-scores
  dom.acousticVal.textContent = `${Math.round(sub.acoustic)}%`;
  dom.acousticBar.style.width = `${sub.acoustic}%`;
  dom.thermalVal.textContent = `${Math.round(sub.thermal)}%`;
  dom.thermalBar.style.width = `${sub.thermal}%`;
  dom.visualVal.textContent = `${Math.round(sub.visual)}%`;
  dom.visualBar.style.width = `${sub.visual}%`;
  dom.occupancyVal.textContent = `${Math.round(sub.occupancy)}%`;
  dom.occupancyBar.style.width = `${sub.occupancy}%`;

  // Sensor Cards
  // Temperature
  dom.tempValue.textContent = data.temperature_c.toFixed(1);
  const tempPct = Math.min(100, Math.max(0, ((data.temperature_c - 15) / 20) * 100));
  dom.tempBarFill.style.width = `${tempPct}%`;
  if (data.temperature_c >= 20 && data.temperature_c <= 24.5) {
    setChip(dom.tempChip, "Ideal", "chip-good");
  } else if (data.temperature_c < 19 || data.temperature_c > 27) {
    setChip(dom.tempChip, "Uncomfortable", "chip-alert");
  } else {
    setChip(dom.tempChip, "Acceptable", "chip-warn");
  }

  // Humidity
  dom.humValue.textContent = Math.round(data.humidity_percent);
  dom.humBarFill.style.width = `${data.humidity_percent}%`;
  if (data.humidity_percent >= 40 && data.humidity_percent <= 60) {
    setChip(dom.humChip, "Optimal", "chip-good");
  } else {
    setChip(dom.humChip, "Suboptimal", "chip-warn");
  }

  // Light
  dom.lightValue.textContent = Math.round(data.light_lux);
  const lightPct = Math.min(100, (data.light_lux / 800) * 100);
  dom.lightBarFill.style.width = `${lightPct}%`;
  if (data.light_lux >= 300 && data.light_lux <= 600) {
    setChip(dom.lightChip, "Good Reading", "chip-good");
  } else if (data.light_lux < 250) {
    setChip(dom.lightChip, "Dim Light", "chip-warn");
  } else {
    setChip(dom.lightChip, "Bright", "chip-good");
  }

  // Noise
  dom.noiseValue.textContent = Math.round(data.noise_db);
  const noisePct = Math.min(100, Math.max(0, ((data.noise_db - 30) / 60) * 100));
  dom.noiseBarFill.style.width = `${noisePct}%`;
  if (data.noise_db <= 42) {
    setChip(dom.noiseChip, "Ultra Quiet", "chip-good");
  } else if (data.noise_db <= 55) {
    setChip(dom.noiseChip, "Moderate", "chip-warn");
  } else {
    setChip(dom.noiseChip, "Distracting", "chip-alert");
  }

  // Occupancy & Capacity
  const occ = data.occupancy || 0;
  const cap = data.capacity || 2;
  dom.occupancyValue.textContent = occ;
  dom.capacityMax.textContent = `/ ${cap} Seats`;
  const occPercent = Math.round((occ / cap) * 100);
  dom.capacityPercentText.textContent = `${occPercent}% Full`;

  if (occ >= cap) {
    setChip(dom.occupancyChip, "FULL", "chip-alert");
  } else if (occ > 0) {
    setChip(dom.occupancyChip, "In Use", "chip-warn");
  } else {
    setChip(dom.occupancyChip, "Available", "chip-good");
  }

  // Render Seat slots
  dom.rfidSlotsContainer.innerHTML = "";
  for (let i = 1; i <= cap; i++) {
    const isOccupied = i <= occ;
    const seatEl = document.createElement("div");
    seatEl.className = `seat-badge ${isOccupied ? "occupied" : ""}`;
    seatEl.textContent = isOccupied ? `Seat ${i}: Occupied` : `Seat ${i}: Empty`;
    dom.rfidSlotsContainer.appendChild(seatEl);
  }

  // Smart Recommendations
  dom.recommendationsList.innerHTML = "";
  const recs = details.recommendations || ["Study environment parameters are within acceptable thresholds."];
  recs.forEach(rec => {
    const item = document.createElement("div");
    item.className = "rec-item";
    item.innerHTML = `<span class="rec-bullet">✓</span><span>${rec}</span>`;
    dom.recommendationsList.appendChild(item);
  });
}

function handleEmptyZone() {
  dom.overallScoreVal.textContent = "--";
  dom.scoreGaugeProgress.style.strokeDashoffset = 427;
  dom.ratingText.textContent = "No Telemetry Yet";
  dom.ratingBadge.style.color = "#94a3b8";
  dom.ratingBadge.style.borderColor = "rgba(255, 255, 255, 0.1)";
  dom.ratingBadge.style.background = "rgba(255, 255, 255, 0.05)";
  dom.tempValue.textContent = "--";
  dom.humValue.textContent = "--";
  dom.lightValue.textContent = "--";
  dom.noiseValue.textContent = "--";
  dom.occupancyValue.textContent = "0";
  dom.recommendationsList.innerHTML = `
    <div class="rec-item">
      <span class="rec-bullet">•</span>
      <span>Awaiting sensor telemetry from ESP32 edge node or Simulator.</span>
    </div>
  `;
}

function setChip(el, text, className) {
  el.textContent = text;
  el.className = `sensor-chip ${className}`;
}

function renderAllZones(zones) {
  dom.allZonesList.innerHTML = "";
  zones.forEach(z => {
    const row = document.createElement("div");
    row.className = "comp-row";

    const score = z.latest_reading ? z.latest_reading.study_score : "--";
    let scoreColor = "#64748b";
    if (score !== "--") {
      scoreColor = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";
    }

    row.innerHTML = `
      <span class="comp-zone-name">${z.zone_name}</span>
      <span class="comp-score-tag" style="background: ${scoreColor}22; color: ${scoreColor}; border: 1px solid ${scoreColor}44">
        ${score} pts
      </span>
    `;
    dom.allZonesList.appendChild(row);
  });
}

function logTerminal(message, type = "info") {
  const line = document.createElement("div");
  line.className = `terminal-line ${type}`;
  const now = new Date().toLocaleTimeString();
  line.textContent = `[${now}] ${message}`;
  dom.terminalLog.appendChild(line);
  dom.terminalLog.scrollTop = dom.terminalLog.scrollHeight;
}

// ==============================================================================
// HTML5 Canvas Time Series Chart
// ==============================================================================

let ctx = null;

function setupCanvas() {
  const canvas = dom.chartCanvas;
  ctx = canvas.getContext("2d");
}

function drawChart() {
  if (!ctx || readingsHistory.length === 0) return;

  const canvas = dom.chartCanvas;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  ctx.clearRect(0, 0, width, height);

  // Background Grid Lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  const gridLines = 4;
  for (let i = 0; i <= gridLines; i++) {
    const y = padding.top + (graphHeight / gridLines) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  // Determine series to draw
  let series1 = [];
  let series2 = [];
  let s1Name = "", s2Name = "";
  let s1Color = "#3b82f6", s2Color = "#06b6d4";
  let minVal = 0, maxVal = 100;

  if (activeChartType === "climate") {
    series1 = readingsHistory.map(r => r.temperature_c);
    series2 = readingsHistory.map(r => r.humidity_percent);
    s1Name = "Temp (°C)";
    s2Name = "Humidity (%)";
    s1Color = "#f43f5e";
    s2Color = "#06b6d4";
    minVal = 10;
    maxVal = 80;
  } else {
    series1 = readingsHistory.map(r => r.noise_db);
    series2 = readingsHistory.map(r => r.light_lux / 10); // scale for visual parity
    s1Name = "Noise (dB)";
    s2Name = "Light (Lux/10)";
    s1Color = "#6366f1";
    s2Color = "#f59e0b";
    minVal = 10;
    maxVal = 90;
  }

  const n = readingsHistory.length;
  if (n < 2) return;

  const getX = (idx) => padding.left + (idx / (n - 1)) * graphWidth;
  const getY = (val) => padding.top + graphHeight - ((val - minVal) / (maxVal - minVal)) * graphHeight;

  // Draw Series 2 Line & Fill
  drawLineSeries(series2, s2Color, getX, getY, true);
  // Draw Series 1 Line & Fill
  drawLineSeries(series1, s1Color, getX, getY, true);

  // Time Labels on X axis
  ctx.fillStyle = "#64748b";
  ctx.font = "10px 'JetBrains Mono', monospace";
  ctx.textAlign = "center";
  readingsHistory.forEach((r, idx) => {
    if (idx % 3 === 0 || idx === n - 1) {
      const timeStr = r.recorded_at ? (r.recorded_at.split(" ")[1] || "").slice(0, 5) : "";
      ctx.fillText(timeStr, getX(idx), height - 8);
    }
  });

  // Chart Legend in corner
  ctx.textAlign = "right";
  ctx.fillStyle = s1Color;
  ctx.fillText(`● ${s1Name}`, width - padding.right, padding.top + 10);
  ctx.fillStyle = s2Color;
  ctx.fillText(`● ${s2Name}`, width - padding.right - 90, padding.top + 10);
}

function drawLineSeries(data, color, getX, getY, fill = false) {
  if (data.length < 2) return;

  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;

  ctx.beginPath();
  data.forEach((val, i) => {
    const x = getX(i);
    const y = getY(val);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Highlight points
  data.forEach((val, i) => {
    const x = getX(i);
    const y = getY(val);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#070a12";
    ctx.beginPath();
    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
    ctx.fill();
  });
}

// Start application
window.addEventListener("DOMContentLoaded", init);
