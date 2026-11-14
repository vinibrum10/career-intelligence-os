const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const nodes = new Map(), calls = [], downloads = [], blobs = [];
class Element {
  constructor(tag = 'div') { this.tagName = tag; this.children = []; this.listeners = {}; this.value = ''; this.hidden = false; }
  set id(value) { this._id = value; nodes.set(value, this); }
  get id() { return this._id; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
  focus() {}
  remove() {}
  click() { downloads.push(this.download); }
  async dispatch(event, target = this) {
    await this.listeners[event]({preventDefault() {}, target});
    await new Promise(resolve => setImmediate(resolve));
  }
}
const html = fs.readFileSync(path.join(__dirname, '../app/web/resume.html'), 'utf8');
for (const [, id] of html.matchAll(/id="([^"]+)"/g)) { const node = new Element(); node.id = id; }
const owner = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const interview = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const facts = {experience:'Atuação em 2 sistemas fictícios.', skills:'Python.'};
const record = {id:interview, created_at:'2026-01-01T12:00:00Z', facts, answers:{experience:'RAW ANSWER NOT SENT'}};
const draft = {interview_id:interview, facts, missing_topics:['projects','results'],
  summary:{text:'Profissional com atuação em sistemas fictícios.', sources:['experience']},
  sections:Object.entries(facts).map(([topic,text]) => ({topic,text,sources:[topic]}))};
let firstAttempt = true;
const script = fs.readFileSync(path.join(__dirname, '../app/web/resume.js'), 'utf8').replace(/^import[^\n]+\n/, '');
const get = id => nodes.get(id);

(async () => {
  const exportSource = fs.readFileSync(path.join(__dirname, '../app/web/resume-export.js'), 'utf8');
  const exports = await import('data:text/javascript;base64,' + Buffer.from(exportSource).toString('base64'));
  vm.runInNewContext(script, {
    document:{getElementById:get, createElement:tag => new Element(tag), body:new Element('body')},
    location:{search:`?owner=${owner}&interview=${interview}`}, URLSearchParams, Blob,
    URL:{createObjectURL:blob => { blobs.push(blob); return 'blob:resume-test'; }, revokeObjectURL() {}},
    setTimeout:callback => callback(), resumeText:exports.resumeText, resumeHtml:exports.resumeHtml,
    fetch:async (url,options) => {
      calls.push({url,options});
      if (!options) return {ok:true,json:async () => structuredClone(record)};
      assert.equal(options.method,'POST');
      assert.deepEqual(JSON.parse(options.body),{consent:true});
      if(firstAttempt) { firstAttempt = false; return {ok:false,json:async () => ({detail:'IA indisponível. Tente novamente.'})}; }
      return {ok:true,json:async () => structuredClone(draft)};
    },
  });
  await new Promise(resolve => setImmediate(resolve));
  await get('resume-generate').dispatch('click');
  assert.equal(calls.length,1,'No model request without consent');
  get('resume-consent').checked = true;
  await get('resume-consent').dispatch('change');
  await get('resume-generate').dispatch('click');
  assert.equal(get('resume-generate').disabled,false,'Provider failure must allow another attempt');
  assert.match(get('resume-status').textContent,/indisponível/);
  await get('resume-generate').dispatch('click');
  assert.equal(get('resume-review').hidden,false);
  assert.equal(get('resume-generate').hidden,true);
  assert.equal(get('resume-block-1').value,facts.experience);
  await get('resume-download-text').dispatch('click');
  assert.equal(downloads.length,0,'Cannot export before review');
  get('resume-name').value = 'Pessoa fictícia';
  get('resume-contact').value = 'local@example.invalid';
  await get('resume-form').dispatch('input',get('resume-name'));
  get('resume-approved').checked = true;
  await get('resume-approved').dispatch('change');
  assert.equal(get('resume-download-text').disabled,false);
  await get('resume-download-text').dispatch('click');
  const exported = await blobs[0].text();
  assert.ok(exported.includes('Pessoa fictícia'));
  assert.ok(exported.includes('local@example.invalid'));
  assert.ok(!exported.includes(owner) && !exported.includes(interview) && !exported.includes('RAW ANSWER'));
  get('resume-block-0').value = '<script>unsafe()</script>';
  await get('resume-form').dispatch('input',get('resume-block-0'));
  assert.equal(get('resume-approved').checked,false,'Editing must invalidate approval');
  assert.equal(get('resume-download-print').disabled,true);
  await get('resume-download-print').dispatch('click');
  assert.equal(downloads.length,1,'Direct export handler also enforces review');
  get('resume-approved').checked = true;
  await get('resume-approved').dispatch('change');
  await get('resume-download-print').dispatch('click');
  assert.deepEqual(downloads,['curriculo-portugues.txt','curriculo-portugues.html']);
  const printVersion = await blobs[1].text();
  assert.ok(printVersion.includes('&lt;script&gt;'));
  assert.ok(!printVersion.includes('<script>'));
  assert.equal(calls.filter(call=>call.options).length,2,'Only the two explicit generation attempts call the server');
  assert.ok(!JSON.stringify(calls).includes('local@example.invalid'));
  console.log('PASS: resume consent, controlled retry, source review, local contact fields and approval invalidation before export.');
})().catch(error=>{ console.error(error); process.exitCode = 1; });
