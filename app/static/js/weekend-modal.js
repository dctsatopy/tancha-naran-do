// ホーム画面: 週末振り返りモーダルの表示・作成ボタン処理
// CSP の script-src から 'unsafe-inline' を除去するため外部ファイル化。
(function () {
  const modalEl = document.getElementById('weekendModal');
  if (!modalEl) return;

  const modal = new bootstrap.Modal(modalEl);
  modal.show();

  document.getElementById('weekendOkBtn').addEventListener('click', function () {
    const btn = this;
    btn.disabled = true;
    fetch('/api/sessions/weekend', { method: 'POST' })
      .then(function (r) {
        if (r.ok) {
          location.reload();
        } else {
          r.json().then(function (d) {
            alert('エラー: ' + d.detail);
            btn.disabled = false;
          });
        }
      })
      .catch(function () {
        alert('通信エラーが発生しました');
        btn.disabled = false;
      });
  });
})();
