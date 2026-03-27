// チェックイン通知ポーリング
(function () {
  const POLL_INTERVAL = 30000; // 30秒

  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }

  function showBrowserNotification(sessionId) {
    if ('Notification' in window && Notification.permission === 'granted') {
      const n = new Notification('たんちゃーならんど', {
        body: 'チェックインの時間です！今すぐ感情チェックをしましょう。',
        icon: '/static/img/icon.png',
      });
      n.onclick = function () {
        window.focus();
        window.location.href = '/check-in?session_id=' + sessionId;
      };
    }
  }

  function showBanner(sessionId) {
    const banner = document.getElementById('check-in-banner');
    const link = document.getElementById('check-in-link');
    if (banner && link) {
      link.href = '/check-in?session_id=' + sessionId;
      banner.classList.remove('d-none');
    }
  }

  async function poll() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();
      if (data.check_in_ready) {
        showBanner(data.session_id);
        showBrowserNotification(data.session_id);
      }
    } catch (e) {
      // ネットワークエラーは無視
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    requestNotificationPermission();
    // 初回ポーリング（10秒後）
    setTimeout(poll, 10000);
    // 以降は30秒ごと
    setInterval(poll, POLL_INTERVAL);
  });
})();
