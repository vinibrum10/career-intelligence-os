const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../app/web/jobs-comparison.js'), 'utf8');
  const {compareText} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  const cases = [
    ['igual', 'igual', false],
    ['Python básico', 'Python intermediário e SQL básico', true],
    ['abc', 'abXYZc', true],
    ['abXYZc', 'abc', true],
    ['', 'novo', true],
    ['antigo', '', true],
    ['a\r\nb ', 'a\nb', true],
    ['Vaga 😀 remota', 'Vaga 😃 remota', true],
    ['<script>alert(1)</script>', '<b>texto</b>', true],
    ['a'.repeat(100000), 'a'.repeat(99999) + 'b', true],
  ];
  for (const [before, after, changed] of cases) {
    const diff = compareText(before, after);
    assert.equal(diff.changed, changed);
    assert.equal(diff.prefix + diff.removed + diff.suffix, before);
    assert.equal(diff.prefix + diff.added + diff.suffix, after);
  }
  const emoji = compareText('😀', '😃');
  assert.equal(emoji.removed, '😀'); assert.equal(emoji.added, '😃');
  const inserted = compareText('abc', 'abXYZc');
  assert.equal(inserted.removed, ''); assert.equal(inserted.added, 'XYZ');
  console.log(`PASS: ${cases.length} comparison cases; exact reconstruction, Unicode and insertion boundaries.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
