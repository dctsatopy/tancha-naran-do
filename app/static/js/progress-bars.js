// data-progress-width 属性を持つ要素に style.width を反映する共通スクリプト
// CSP の style-src から 'unsafe-inline' を除去するため、動的な幅指定は
// インライン style 属性ではなく JS 経由で行う。
(function () {
  function applyProgressBarWidths() {
    document.querySelectorAll('[data-progress-width]').forEach(function (el) {
      el.style.width = el.dataset.progressWidth + '%';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyProgressBarWidths);
  } else {
    applyProgressBarWidths();
  }
})();
