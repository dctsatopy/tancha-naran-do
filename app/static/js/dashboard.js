let overallChart, categoryChart, radarChart;

const CHART_COLORS = {
  overall: 'rgb(58, 123, 213)',
  anger: 'rgb(231, 76, 60)',
  regulation: 'rgb(52, 152, 219)',
  mindfulness: 'rgb(39, 174, 96)',
  stress: 'rgb(243, 156, 18)',
};

async function loadChart(days) {
  // ボタンのアクティブ切り替え
  document.querySelectorAll('.btn-group .btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('btn-' + days);
  if (activeBtn) activeBtn.classList.add('active');

  const res = await fetch('/api/history?days=' + days);
  const data = await res.json();

  const labels = data.map(d => d.date);
  const overall = data.map(d => d.overall);
  const anger = data.map(d => d.anger);
  const regulation = data.map(d => d.regulation);
  const mindfulness = data.map(d => d.mindfulness);
  const stress = data.map(d => d.stress);

  // ─── 総合スコアグラフ ─── //
  const overallCtx = document.getElementById('overallChart').getContext('2d');
  if (overallChart) overallChart.destroy();
  overallChart = new Chart(overallCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '総合スコア',
        data: overall,
        borderColor: CHART_COLORS.overall,
        backgroundColor: 'rgba(58,123,213,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7,
      }],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: 'スコア' } },
      },
      plugins: { legend: { display: false } },
    },
  });

  // ─── カテゴリ別グラフ ─── //
  const catCtx = document.getElementById('categoryChart').getContext('2d');
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(catCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: '怒り', data: anger, borderColor: CHART_COLORS.anger, tension: 0.4, pointRadius: 4 },
        { label: '感情調節', data: regulation, borderColor: CHART_COLORS.regulation, tension: 0.4, pointRadius: 4 },
        { label: 'マインドフルネス', data: mindfulness, borderColor: CHART_COLORS.mindfulness, tension: 0.4, pointRadius: 4 },
        { label: 'ストレス', data: stress, borderColor: CHART_COLORS.stress, tension: 0.4, pointRadius: 4 },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: 'スコア' } },
      },
    },
  });

  // ─── レーダーチャート（全期間平均）─── //
  const avg = arr => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;
  const radarCtx = document.getElementById('radarChart').getContext('2d');
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(radarCtx, {
    type: 'radar',
    data: {
      labels: ['怒り制御\n(低い=良)', '感情調節', 'マインドフルネス', 'ストレス\n(低い=良)', '総合'],
      datasets: [{
        label: '平均スコア',
        data: [100 - avg(anger), avg(regulation), avg(mindfulness), 100 - avg(stress), avg(overall)],
        backgroundColor: 'rgba(58,123,213,0.2)',
        borderColor: CHART_COLORS.overall,
        pointBackgroundColor: CHART_COLORS.overall,
      }],
    },
    options: {
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 25 } } },
      plugins: { legend: { display: false } },
    },
  });

  // ─── 履歴テーブル ─── //
  await loadHistoryTable();
}

async function loadHistoryTable() {
  const res = await fetch('/api/sessions?limit=20');
  const sessions = await res.json();
  const tbody = document.getElementById('history-table');
  if (!sessions.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">データがありません</td></tr>';
    return;
  }
  const statusMap = {
    pending: '<span class="badge bg-light text-dark">予定</span>',
    in_progress: '<span class="badge bg-warning">実施中</span>',
    completed: '<span class="badge bg-success">完了</span>',
    skipped: '<span class="badge bg-secondary">スキップ</span>',
  };
  tbody.innerHTML = sessions.map(s => {
    const dt = new Date(s.scheduled_at);
    const dtStr = dt.toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    const statusHtml = Object.prototype.hasOwnProperty.call(statusMap, s.status)
      ? statusMap[s.status]
      : '<span class="badge bg-secondary">不明</span>';
    const scoreStr = s.overall_score != null ? `<strong>${Math.round(s.overall_score)}</strong> 点` : '—';
    return `<tr><td>${dtStr}</td><td>${statusHtml}</td><td>${scoreStr}</td></tr>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', () => loadChart(7));
