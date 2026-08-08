// チェックイン画面: 回答の進捗表示と送信ボタンの活性化制御
// CSP の script-src から 'unsafe-inline' を除去するため外部ファイル化。
// 動的な設問数は #check-in-form の data-total 属性から取得する。
(function () {
  const form = document.getElementById('check-in-form');
  if (!form) return;

  const totalQuestions = parseInt(form.dataset.total, 10);
  const answered = new Set();

  document.querySelectorAll('.answer-radio').forEach(function (radio) {
    radio.addEventListener('change', function () {
      answered.add(this.name);
      const count = answered.size;
      const pct = (count / totalQuestions * 100).toFixed(0);

      document.getElementById('progress-bar').style.width = pct + '%';
      document.getElementById('progress-text').textContent = count + ' / ' + totalQuestions;
      document.getElementById('remaining').textContent = totalQuestions - count;

      if (count >= totalQuestions) {
        document.getElementById('submit-btn').disabled = false;
        document.getElementById('submit-hint').classList.add('d-none');
      }
    });
  });
})();
