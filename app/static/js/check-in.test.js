const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function makeTextElement() {
  return {
    textContent: '',
    classList: { added: [], add(name) { this.added.push(name); } },
    disabled: false,
    style: {},
  };
}

function buildDom(totalQuestions) {
  const radios = [];
  for (let i = 1; i <= totalQuestions; i++) {
    radios.push({ name: 'q_' + i, addEventListener() {} });
  }

  const elementsById = {
    'check-in-form': { dataset: { total: String(totalQuestions) } },
    'progress-bar': makeTextElement(),
    'progress-text': makeTextElement(),
    remaining: makeTextElement(),
    'submit-btn': makeTextElement(),
    'submit-hint': makeTextElement(),
  };

  const documentStub = {
    getElementById(id) {
      return elementsById[id] || null;
    },
    querySelectorAll(selector) {
      assert.equal(selector, '.answer-radio');
      return radios;
    },
  };

  return { documentStub, elementsById, radios };
}

function loadCheckInScript(context) {
  const code = fs.readFileSync(path.join(__dirname, 'check-in.js'), 'utf8');
  vm.createContext(context);
  vm.runInContext(code, context);
}

test('フォームが無いページでは何もしない', () => {
  const documentStub = {
    getElementById: () => null,
    querySelectorAll: () => {
      throw new Error('form が無い場合は querySelectorAll を呼んではいけない');
    },
  };
  assert.doesNotThrow(() => loadCheckInScript({ document: documentStub }));
});

test('全問回答すると進捗表示が更新され送信ボタンが有効化される', () => {
  const total = 2;
  const { documentStub, elementsById, radios } = buildDom(total);
  const capturedHandlers = [];
  radios.forEach((r) => {
    r.addEventListener = function (event, cb) {
      if (event === 'change') capturedHandlers.push(cb.bind(r));
    };
  });

  loadCheckInScript({ document: documentStub });

  assert.equal(capturedHandlers.length, total);
  elementsById['submit-btn'].disabled = true;

  capturedHandlers[0]();
  assert.equal(elementsById['progress-text'].textContent, '1 / 2');
  assert.equal(elementsById['progress-bar'].style.width, '50%');
  assert.equal(elementsById['remaining'].textContent, 1);
  assert.equal(elementsById['submit-btn'].disabled, true);

  capturedHandlers[1]();
  assert.equal(elementsById['progress-text'].textContent, '2 / 2');
  assert.equal(elementsById['progress-bar'].style.width, '100%');
  assert.equal(elementsById['submit-btn'].disabled, false);
  assert.ok(elementsById['submit-hint'].classList.added.includes('d-none'));
});

test('同じ設問への再回答は回答数を二重カウントしない', () => {
  const total = 2;
  const { documentStub, elementsById, radios } = buildDom(total);
  const capturedHandlers = [];
  radios.forEach((r) => {
    r.addEventListener = function (event, cb) {
      if (event === 'change') capturedHandlers.push(cb.bind(r));
    };
  });

  loadCheckInScript({ document: documentStub });

  capturedHandlers[0]();
  capturedHandlers[0]();
  assert.equal(elementsById['progress-text'].textContent, '1 / 2');
});
