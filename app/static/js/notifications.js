// チェックイン通知ポーリング
(function () {
  const POLL_INTERVAL = 30000; // 30秒

  // Web Audio API: ブラウザの自動再生ポリシーに対応するため
  // ユーザー操作後に AudioContext を初期化する
  let audioCtx = null;
  const notifiedSessions = new Set(); // 通知済みセッションID（チャイム重複防止）

  function unlockAudio() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  // 任意のユーザー操作で AudioContext を解放する
  document.addEventListener('click', unlockAudio, { once: false });
  document.addEventListener('keydown', unlockAudio, { once: false });

  // 3音のチャイム（ソ→ド→ミ の上昇和音）
  function playChime() {
    if (!audioCtx || audioCtx.state === 'suspended') return;

    const notes = [784, 1047, 1319]; // G5, C6, E6 (Hz)
    const startTime = audioCtx.currentTime;

    notes.forEach(function (freq, i) {
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(freq, startTime);

      // 各音を 0.3秒ずつ時間差で鳴らし、フェードアウトさせる
      const noteStart = startTime + i * 0.35;
      const noteEnd = noteStart + 0.8;
      gainNode.gain.setValueAtTime(0, noteStart);
      gainNode.gain.linearRampToValueAtTime(0.4, noteStart + 0.02);
      gainNode.gain.exponentialRampToValueAtTime(0.001, noteEnd);

      oscillator.start(noteStart);
      oscillator.stop(noteEnd);
    });
  }

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
        // 同じセッションで繰り返しチャイムが鳴らないよう制御
        if (!notifiedSessions.has(data.session_id)) {
          notifiedSessions.add(data.session_id);
          playChime();
        }
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
