const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {randomUUID} = require('node:crypto');

// Exercise the screen's event handlers and network payloads without an external DOM package.
const nodes = new Map();
class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.listeners = {};
    this.value = '';
    this.hidden = false;
  }
  set id(value) { this._id = value; nodes.set(value, this); }
  get id() { return this._id; }
  append(...children) { this.children.push(...children); }
  prepend(child) { this.children.unshift(child); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
  focus() {}
  reset() {
    for (const [id, node] of nodes) if (id.startsWith('answer-')) node.value = '';
  }
  async dispatch(event) {
    await this.listeners[event]({preventDefault() {}});
    await new Promise(resolve => setImmediate(resolve));
  }
}
const html = fs.readFileSync(path.join(__dirname, '../app/web/interview.html'), 'utf8');
for (const [, id] of html.matchAll(/id="([^"]+)"/g)) {
  const node = new Element();
  node.id = id;
}
const owner = randomUUID();
const originalId = randomUUID();
const original = {
  id: originalId, created_at: '2026-01-01T12:00:00Z',
  answers: {experience: 'Maintained a fictitious sytem.', projects: 'An excluded fictitious project.'},
  facts: {experience: 'Maintained one fictitious system.'},
};
const originalSnapshot = structuredClone(original);
const records = new Map([[originalId, original]]);
const writes = [];
let failNextSave = false;
const source = fs.readFileSync(path.join(__dirname, '../app/web/interview.js'), 'utf8');
vm.runInNewContext(source, {
  document: {getElementById: id => nodes.get(id), createElement: tag => new Element(tag)},
  crypto: {randomUUID}, localStorage: {getItem: () => owner},
  fetch: async (url, options) => {
    assert.ok(url.startsWith(`/career/owners/${owner}/interviews`));
    if (options?.method === 'PUT') {
      const id = url.split('/').at(-1);
      const payload = JSON.parse(options.body);
      writes.push({id, ...payload});
      if (failNextSave) { failNextSave = false; return {ok: false, status: 503}; }
      assert.notEqual(id, originalId, 'Correction must never overwrite the original record');
      records.set(id, {id, created_at: '2026-01-02T12:00:00Z', ...payload});
      return {ok: true, json: async () => structuredClone(records.get(id))};
    }
    const result = url.includes('?') ? [...records.values()] : records.get(url.split('/').at(-1));
    return {ok: true, json: async () => structuredClone(result)};
  },
});
const get = id => nodes.get(id);
const click = id => get(id).dispatch('click');
const submit = id => get(id).dispatch('submit');
const reviewSections = () => get('interview-draft').children;
const inclusion = index => reviewSections()[index].children[3].children[0];

(async () => {
  await submit('interview-connect');
  await get('interview-list').children[0].children[0].dispatch('click');
  await click('interview-correct');
  assert.equal(get('answer-experience').value, original.answers.experience);
  assert.equal(get('answer-projects').value, original.answers.projects);
  assert.equal(get('answer-skills').value, '');
  await submit('interview-answers');
  assert.equal(get('fact-experience').value, original.facts.experience);
  assert.equal(inclusion(1).checked, false, 'An excluded fact must remain excluded');
  assert.equal(get('fact-projects').disabled, true);

  get('fact-experience').value = 'Revised fact kept when going back.';
  await click('interview-back');
  await submit('interview-answers');
  assert.equal(get('fact-experience').value, 'Revised fact kept when going back.');
  assert.equal(inclusion(1).checked, false);
  await click('interview-back');
  get('answer-experience').value = 'Maintained a fictitious system.';
  await submit('interview-answers');
  assert.equal(get('fact-experience').value, 'Maintained a fictitious system.');
  failNextSave = true;
  await submit('interview-review');
  assert.equal(records.size, 1);
  assert.match(get('interview-status').textContent, /503/);
  await submit('interview-review');
  assert.equal(writes[0].id, writes[1].id, 'Retry must reuse the same save identifier');
  assert.equal(records.size, 2);
  assert.deepEqual(records.get(originalId), originalSnapshot);
  assert.deepEqual(writes[1].facts, {experience: 'Maintained a fictitious system.'});
  assert.equal(writes[1].answers.projects, original.answers.projects);
  assert.equal('skills' in writes[1].answers, false);

  await click('interview-correct');
  get('answer-experience').value = 'Unsaved change';
  const listLength = get('interview-list').children.length;
  await submit('interview-connect');
  assert.equal(get('interview-list').children.length, listLength, 'Space selection must not discard an edit');
  await click('interview-cancel-correction');
  assert.equal(get('answer-experience').value, '');
  assert.equal(get('interview-correction-notice').hidden, true);
  assert.equal(records.size, 2, 'Cancel must not write another record');
  get('answer-skills').value = 'An unfinished interview';
  await click('interview-correct');
  assert.equal(get('answer-skills').value, 'An unfinished interview', 'Opening a correction must not discard another interview');
  get('interview-answers').reset();
  get('answer-experience').value = 'A fresh, independent interview.';
  await submit('interview-answers');
  assert.equal(get('fact-experience').value, 'A fresh, independent interview.');
  await submit('interview-review');
  assert.equal(records.size, 3, 'Starting a fresh interview must still work after a correction');
  console.log('PASS: saved-profile correction, original preservation, excluded facts, back navigation, retry and cancellation.');
})().catch(error => { console.error(error); process.exitCode = 1; });
