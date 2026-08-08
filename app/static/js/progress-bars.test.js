const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function runScript(context) {
  const code = fs.readFileSync(path.join(__dirname, 'progress-bars.js'), 'utf8');
  vm.createContext(context);
  vm.runInContext(code, context);
}

test('data-progress-width を持つ要素に style.width を反映する', () => {
  const elements = [
    { dataset: { progressWidth: '40' }, style: {} },
    { dataset: { progressWidth: '75' }, style: {} },
  ];
  const context = {
    document: {
      readyState: 'complete',
      addEventListener: () => {},
      querySelectorAll: (selector) => {
        assert.equal(selector, '[data-progress-width]');
        return elements;
      },
    },
  };

  runScript(context);

  assert.equal(elements[0].style.width, '40%');
  assert.equal(elements[1].style.width, '75%');
});

test('document がロード中の場合は DOMContentLoaded を待ってから適用する', () => {
  const listeners = {};
  const elements = [{ dataset: { progressWidth: '10' }, style: {} }];
  const context = {
    document: {
      readyState: 'loading',
      addEventListener: (event, cb) => { listeners[event] = cb; },
      querySelectorAll: () => elements,
    },
  };

  runScript(context);

  assert.equal(elements[0].style.width, undefined);
  listeners.DOMContentLoaded();
  assert.equal(elements[0].style.width, '10%');
});
