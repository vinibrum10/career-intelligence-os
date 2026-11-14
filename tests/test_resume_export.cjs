const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../app/web/resume-export.js'), 'utf8');
  const {resumeText, resumeHtml} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  const document = {name:'Nome fictício <img src=x onerror=alert(1)>', contact:'contato@example.invalid',
    blocks:[{title:'Resumo profissional', text:'Atuação fictícia.\nSem dados inventados.'},
      {title:'Experiências <script>', text:'<script>alert("test")</script> & conteúdo original.'},
      {title:'Seção vazia', text:' '}], additions:'Formação: informação fictícia revisada.'};
  const text = resumeText(document);
  assert.ok(text.includes('Atuação fictícia.\nSem dados inventados.'));
  assert.ok(text.includes(document.contact));
  assert.ok(!text.includes('Seção vazia'));
  const html = resumeHtml(document);
  assert.ok(html.includes('lang="pt-BR"'));
  assert.ok(html.includes('Content-Security-Policy'));
  assert.ok(html.includes("default-src 'none'"));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.ok(!html.includes('<script'));
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('Seção vazia'));
  assert.ok(!html.includes('https://'));
  assert.ok(html.includes('@page{size:A4'));
  console.log('PASS: Portuguese resume exports preserve reviewed content, omit empty sections and escape active markup.');
})().catch(error => { console.error(error); process.exitCode = 1; });
