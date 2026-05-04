let overallChart, categoryChart, radarChart;

const CHART_COLORS = {
  overall: 'rgb(58, 123, 213)',
  anger_state: 'rgb(231, 76, 60)',
  cognitive_pattern: 'rgb(155, 89, 182)',
  physiological: 'rgb(52, 152, 219)',
  behavioral: 'rgb(243, 156, 18)',
  emotion_regulation: 'rgb(39, 174, 96)',
  psychological_state: 'rgb(149, 165, 166)',
};

async function loadChart(days) {
  document.querySelectorAll('.btn-group .btn').forEach(b => b.classList.remove('active'));
  const activeBtn = document.getElementById('btn-' + days);
  if (activeBtn) activeBtn.classList.add('active');

  const res = await fetch('/api/history?days=' + days);
  const data = await res.json();

  const labels = data.map(d => d.date);
  const overall = data.map(d => d.overall);
  const angerState = data.map(d => d.anger_state);
  const cognitivePattern = data.map(d => d.cognitive_pattern);
  const physiological = data.map(d => d.physiological);
  const behavioral = data.map(d => d.behavioral);
  const emotionRegulation = data.map(d => d.emotion_regulation);
  const psychologicalState = data.map(d => d.psychological_state);

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

  const catCtx = document.getElementById('categoryChart').getContext('2d');
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(catCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: '怒りの状態', data: angerState, borderColor: CHART_COLORS.anger_state, tension: 0.4, pointRadius: 4 },
        { label: '認知パターン', data: cognitivePattern, borderColor: CHART_COLORS.cognitive_pattern, tension: 0.4, pointRadius: 4 },
        { label: '身体反応', data: physiological, borderColor: CHART_COLORS.physiological, tension: 0.4, pointRadius: 4 },
        { label: '行動傾向', data: behavioral, borderColor: CHART_COLORS.behavioral, tension: 0.4, pointRadius: 4 },
        { label: '感情調節', data: emotionRegulation, borderColor: CHART_COLORS.emotion_regulation, tension: 0.4, pointRadius: 4 },
        { label: '心理的状態', data: psychologicalState, borderColor: CHART_COLORS.psychological_state, tension: 0.4, pointRadius: 4 },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: 'スコア（低い=良好）' } },
      },
    },
  });

  const avg = arr => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;
  const radarCtx = document.getElementById('radarChart').getContext('2d');
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(radarCtx, {
    type: 'radar',
    data: {
      labels: ['怒りの状態\n(低い=良)', '認知パターン\n(低い=良)', '身体反応\n(低い=良)', '行動傾向\n(低い=良)', '感情調節\n(低い=良)', '心理的状態\n(低い=良)'],
      datasets: [{
        label: '平均スコア（反転: 高い=良好）',
        data: [100 - avg(angerState), 100 - avg(cognitivePattern), 100 - avg(physiological), 100 - avg(behavioral), 100 - avg(emotionRegulation), 100 - avg(psychologicalState)],
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
