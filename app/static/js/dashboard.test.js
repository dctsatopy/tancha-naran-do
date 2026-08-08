const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function loadScript(context) {
  const code = fs.readFileSync(path.join(__dirname, 'dashboard.js'), 'utf8');
  vm.createContext(context);
  vm.runInContext(code, context);
}

function makeDaysButton(days) {
  const el = {
    dataset: { days: String(days) },
    classList: {
      list: new Set(),
      add(name) { this.list.add(name); },
      remove(name) { this.list.delete(name); },
      contains(name) { return this.list.has(name); },
    },
  };
  el.addEventListener = function (event, cb) {
    if (event === 'click') el._clickHandler = cb.bind(el);
  };
  return el;
}

function buildContext() {
  const btn7 = makeDaysButton(7);
  const btn30 = makeDaysButton(30);
  const canvasStub = { getContext: () => ({}) };
  const historyTableStub = { innerHTML: '' };
  const domReadyHandlers = [];
  const fetchCalls = [];

  const documentStub = {
    addEventListener(event, cb) {
      if (event === 'DOMContentLoaded') domReadyHandlers.push(cb);
    },
    querySelectorAll(selector) {
      if (selector === '[data-days]') return [btn7, btn30];
      if (selector === '.btn-group .btn') return [btn7, btn30];
      return [];
    },
    getElementById(id) {
      if (id === 'history-table') return historyTableStub;
      if (id === 'btn-7') return btn7;
      if (id === 'btn-30') return btn30;
      return canvasStub;
    },
  };

  const context = {
    document: documentStub,
    fetch: async (url) => {
      fetchCalls.push(url);
      return { json: async () => [] };
    },
    Chart: function () {
      this.destroy = () => {};
    },
  };

  return { context, btn7, btn30, domReadyHandlers, fetchCalls };
}

test('data-days ボタンに click リスナーが登録される（onclick 属性は使わない）', async () => {
  const { context, btn7, btn30, domReadyHandlers } = buildContext();
  loadScript(context);

  await domReadyHandlers[0]();

  assert.equal(typeof btn7._clickHandler, 'function');
  assert.equal(typeof btn30._clickHandler, 'function');
});

test('data-days ボタンのクリックで対応する日数の loadChart が実行される', async () => {
  const { context, btn30, domReadyHandlers, fetchCalls } = buildContext();
  loadScript(context);
  await domReadyHandlers[0]();

  fetchCalls.length = 0;
  await btn30._clickHandler();

  assert.ok(fetchCalls.some((url) => url === '/api/history?days=30'));
});
