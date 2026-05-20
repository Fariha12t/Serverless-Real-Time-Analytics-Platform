/* dashboard.js — Real-Time Analytics Dashboard */

const REFRESH_INTERVAL = 5000; // ms
let refreshTimer = null;
let feedCount = 0;
let demoMode = false;

// ── Chart instances ────────────────────────────────────────────────────────
const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 8 } },
    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 } }, beginAtZero: true },
  },
  animation: { duration: 400 },
};

const volumeChart = new Chart(document.getElementById('volumeChart'), {
  type: 'bar',
  data: { labels: [], datasets: [{ data: [], backgroundColor: 'rgba(0,229,160,0.5)', borderColor: '#00e5a0', borderWidth: 1, borderRadius: 3 }] },
  options: { ...CHART_OPTS },
});

const usersChart = new Chart(document.getElementById('usersChart'), {
  type: 'line',
  data: { labels: [], datasets: [{ data: [], fill: true, borderColor: '#0090ff', backgroundColor: 'rgba(0,144,255,0.1)', tension: 0.4, pointRadius: 2 }] },
  options: { ...CHART_OPTS },
});

const durationChart = new Chart(document.getElementById('durationChart'), {
  type: 'line',
  data: { labels: [], datasets: [{ data: [], fill: false, borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', tension: 0.4, pointRadius: 2 }] },
  options: { ...CHART_OPTS },
});

// ── Update charts from API response ───────────────────────────────────────
function updateCharts(data) {
  const labels = data.series.map(s => s.hour.slice(11)); // HH only
  const counts = data.series.map(s => s.count);
  const users = data.series.map(s => s.unique_users);
  const durations = data.series.map(s => s.avg_duration_ms);

  [volumeChart, usersChart, durationChart].forEach((c, i) => {
    c.data.labels = labels;
    c.data.datasets[0].data = [counts, users, durations][i];
    c.update('none');
  });

  // KPI cards
  setText('kpi-total', fmt(data.totals.count));
  setText('kpi-users', fmt(data.totals.unique_users));

  const avgDur = data.totals.count
    ? Math.round(data.totals.sum_duration / data.totals.count)
    : 0;
  setText('kpi-duration', avgDur ? avgDur + 'ms' : '—');

  const lastHour = data.series[data.series.length - 1];
  setText('kpi-rate', fmt(lastHour ? lastHour.count : 0));
  setText('last-refresh', 'Updated ' + new Date().toLocaleTimeString());
}

// ── Fetch from real API ────────────────────────────────────────────────────
async function fetchKPIs() {
  const base = document.getElementById('api-url').value.trim().replace(/\/$/, '');
  if (!base) return;
  const eventType = document.getElementById('event-type-select').value;
  const hours = document.getElementById('hours-select').value;

  try {
    const res = await fetch(`${base}/kpis?event_type=${eventType}&hours=${hours}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    updateCharts(data);
    document.getElementById('status-badge').textContent = '● LIVE';
    document.getElementById('status-badge').style.color = 'var(--accent)';
  } catch (err) {
    console.error('Fetch failed:', err);
    document.getElementById('status-badge').textContent = '● ERROR';
    document.getElementById('status-badge').style.color = 'var(--accent3)';
  }
}

// ── Demo mode — generates synthetic data locally ───────────────────────────
function generateDemoData(hours = 24) {
  const now = new Date();
  const series = [];
  for (let i = hours - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 3600000);
    const hour = d.toISOString().slice(0, 13);
    const isPeak = d.getHours() >= 9 && d.getHours() <= 18;
    const base = isPeak ? 3000 : 800;
    const count = Math.round(base + Math.random() * base * 0.4 - base * 0.2);
    const dur = Math.round(900 + Math.random() * 600);
    const users = Math.round(count * (0.3 + Math.random() * 0.2));
    series.push({ hour, count, avg_duration_ms: dur, unique_users: users });
  }
  const totals = series.reduce(
    (a, s) => ({
      count: a.count + s.count,
      sum_duration: a.sum_duration + s.avg_duration_ms * s.count,
      unique_users: a.unique_users + s.unique_users,
    }),
    { count: 0, sum_duration: 0, unique_users: 0 }
  );
  return { series, totals };
}

function runDemo() {
  demoMode = true;
  updateCharts(generateDemoData(parseInt(document.getElementById('hours-select').value)));
  document.getElementById('status-badge').textContent = '● DEMO';
  document.getElementById('status-badge').style.color = '#f0b429';

  // Simulate live feed
  const types = ['page_view', 'click', 'purchase', 'sign_up'];
  const colors = ['#00e5a0', '#0090ff', '#ff6b6b', '#f0b429'];
  setInterval(() => {
    const i = Math.floor(Math.random() * types.length);
    addFeedItem(types[i], 'u' + Math.floor(Math.random() * 9999).toString().padStart(4, '0'), colors[i]);
    // Refresh chart with fresh demo data every 5s
  }, 800 + Math.random() * 1200);

  setInterval(() => {
    if (demoMode) updateCharts(generateDemoData(parseInt(document.getElementById('hours-select').value)));
  }, REFRESH_INTERVAL);
}

// ── Live feed ──────────────────────────────────────────────────────────────
function addFeedItem(type, user, color = '#00e5a0') {
  feedCount++;
  const list = document.getElementById('feed-list');

  // Clear placeholder
  if (list.querySelector('div[style]')) list.innerHTML = '';

  const item = document.createElement('div');
  item.className = 'feed-item';
  const time = new Date().toLocaleTimeString('en', { hour12: false });
  item.innerHTML = `
    <span class="feed-dot" style="background:${color}"></span>
    <span class="feed-type">${type}</span>
    <span class="feed-user">${user}</span>
    <span class="feed-time">${time}</span>
  `;
  list.prepend(item);

  // Keep max 50 items
  while (list.children.length > 50) list.removeChild(list.lastChild);

  document.getElementById('feed-count').textContent = feedCount + ' events';
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function setText(id, val) {
  document.getElementById(id).textContent = val;
}

function fmt(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
  return n.toString();
}

// ── Wire up buttons ────────────────────────────────────────────────────────
document.getElementById('connect-btn').addEventListener('click', () => {
  demoMode = false;
  clearInterval(refreshTimer);
  fetchKPIs();
  refreshTimer = setInterval(fetchKPIs, REFRESH_INTERVAL);
});

document.getElementById('demo-btn').addEventListener('click', () => {
  clearInterval(refreshTimer);
  runDemo();
});

document.getElementById('event-type-select').addEventListener('change', () => {
  if (!demoMode) fetchKPIs();
});
document.getElementById('hours-select').addEventListener('change', () => {
  if (demoMode) updateCharts(generateDemoData(parseInt(document.getElementById('hours-select').value)));
  else fetchKPIs();
});

// ── Boot ───────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  document.getElementById('loading').style.display = 'none';
  // Auto-demo if no API URL
  if (!document.getElementById('api-url').value) {
    setTimeout(runDemo, 300);
  }
});
