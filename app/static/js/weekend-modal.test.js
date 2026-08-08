const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function loadScript(context) {
  const code = fs.readFileSync(path.join(__dirname, 'weekend-modal.js'), 'utf8');
  vm.createContext(context);
  vm.runInContext(code, context);
}

function makeButton() {
  return { disabled: false, addEventListener() {} };
}

function buildContext({ modalEl }) {
  const shownModals = [];
  const alerts = [];
  const okBtn = makeButton();
  let clickHandler = null;
  okBtn.addEventListener = function (event, cb) {
    if (event === 'click') clickHandler = cb.bind(okBtn);
  };

  const elementsById = { weekendModal: modalEl, weekendOkBtn: okBtn };
  const documentStub = {
    getElementById: (id) => elementsById[id] || null,
  };

  const bootstrapStub = {
    Modal: function (el) {
      this.el = el;
      this.show = () => shownModals.push(el);
    },
  };

  const context = {
    document: documentStub,
    bootstrap: bootstrapStub,
    alert: (msg) => alerts.push(msg),
    fetch: null, // 各テストで差し替える
    location: { reload: () => { context.reloaded = true; } },
    reloaded: false,
  };

  return { context, okBtn, clickHandler: () => clickHandler, shownModals, alerts };
}

test('モーダル要素が無いページでは何もしない', () => {
  const { context } = buildContext({ modalEl: null });
  assert.doesNotThrow(() => loadScript(context));
});

test('モーダルが存在する場合は表示される', () => {
  const { context, shownModals } = buildContext({ modalEl: {} });
  loadScript(context);
  assert.equal(shownModals.length, 1);
});

test('作成ボタン押下で成功時はページをリロードする', async () => {
  const { context, okBtn, clickHandler } = buildContext({ modalEl: {} });
  context.fetch = async () => ({ ok: true });
  loadScript(context);

  await clickHandler()();
  assert.equal(okBtn.disabled, true);
  assert.equal(context.reloaded, true);
});

test('作成ボタン押下で失敗時はエラーを表示しボタンを再度有効化する', async () => {
  const { context, okBtn, clickHandler, alerts } = buildContext({ modalEl: {} });
  context.fetch = async () => ({
    ok: false,
    json: async () => ({ detail: 'weekend session already exists' }),
  });
  loadScript(context);

  await clickHandler()();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /weekend session already exists/);
  assert.equal(okBtn.disabled, false);
});
