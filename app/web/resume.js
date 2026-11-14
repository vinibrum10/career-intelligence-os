import {resumeText, resumeHtml} from './resume-export.js';

const byId = id => document.getElementById(id);
const topics = {experience:'Experiências', projects:'Projetos', skills:'Habilidades', results:'Resultados'};
const params = new URLSearchParams(location.search);
const owner = params.get('owner') || '';
const interview = params.get('interview') || '';
const uuid = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const consent = byId('resume-consent');
const generate = byId('resume-generate');
const approved = byId('resume-approved');
const nameField = byId('resume-name');
const textButton = byId('resume-download-text');
const printButton = byId('resume-download-print');
let loaded = false;
let busy = false;
let blocks = [];

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}
function message(text) { byId('resume-status').textContent = text; }
async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Não foi possível concluir a solicitação. Confira o perfil selecionado e tente novamente.');
  }
  return response.json();
}
function updateDownloads() {
  const ready = blocks.length > 0 && nameField.value.trim() && approved.checked;
  textButton.disabled = !ready;
  printButton.disabled = !ready;
}
byId('resume-form').addEventListener('submit', event => event.preventDefault());
byId('resume-form').addEventListener('input', event => {
  if (event.target !== approved) approved.checked = false;
  updateDownloads();
});
approved.addEventListener('change', updateDownloads);
consent.addEventListener('change', () => { generate.disabled = !loaded || !consent.checked || busy; });

function addBlock(title, paragraph, facts) {
  const section = element('section');
  section.append(element('h3', title));
  const field = element('textarea');
  field.id = 'resume-block-' + blocks.length;
  field.value = paragraph.text;
  field.rows = 5;
  field.maxLength = 3000;
  const label = element('label', 'Texto de ' + title.toLowerCase());
  label.htmlFor = field.id;
  section.append(label, field);
  const sources = element('details');
  sources.append(element('summary', 'Conferir fontes de ' + title.toLowerCase()));
  for (const key of paragraph.sources) {
    sources.append(element('p', topics[key]), element('blockquote', facts[key]));
  }
  section.append(sources);
  byId('resume-blocks').append(section);
  blocks.push({title, field});
}

generate.addEventListener('click', async () => {
  if (!loaded || !consent.checked || busy || blocks.length) return;
  busy = true;
  byId('resume-generation').disabled = true;
  message('Gerando o rascunho com os fatos confirmados. Isso pode levar alguns minutos…');
  try {
    const draft = await request(`/career/owners/${owner}/interviews/${interview}/resume-draft`, {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({consent:true}),
    });
    if (draft.interview_id !== interview) throw new Error('A resposta não corresponde ao perfil selecionado.');
    blocks = [];
    byId('resume-blocks').replaceChildren();
    addBlock('Resumo profissional', draft.summary, draft.facts);
    for (const key of Object.keys(topics)) {
      const section = draft.sections.find(item => item.topic === key);
      if (section) addBlock(topics[key], section, draft.facts);
    }
    const missing = byId('resume-missing');
    missing.replaceChildren();
    if (draft.missing_topics.length) missing.append(element('p', 'Temas sem fatos confirmados: ' + draft.missing_topics.map(key => topics[key]).join(', ') + '. Complete apenas se tiver informações para isso.'));
    approved.checked = false;
    byId('resume-review').hidden = false;
    generate.hidden = true;
    updateDownloads();
    nameField.focus();
    message('Rascunho pronto para revisão. Confira o texto e suas fontes antes de baixar.');
  } catch (error) {
    message(error instanceof TypeError ? 'Não foi possível conectar ao servidor. Seu perfil continua preservado.' : error.message);
  } finally {
    busy = false;
    byId('resume-generation').disabled = false;
    generate.disabled = !loaded || !consent.checked;
  }
});

function download(format) {
  if (!blocks.length || !approved.checked || !nameField.value.trim()) {
    message('Preencha seu nome e confirme a revisão antes de baixar.');
    return;
  }
  const documentData = {
    name:nameField.value, contact:byId('resume-contact').value,
    blocks:blocks.map(block => ({title:block.title, text:block.field.value})),
    additions:byId('resume-additions').value,
  };
  if (!documentData.blocks.some(block => block.text.trim())) {
    message('Mantenha pelo menos um trecho do currículo antes de baixar.');
    return;
  }
  const html = format === 'html';
  const blob = new Blob([html ? resumeHtml(documentData) : resumeText(documentData)], {type:html ? 'text/html;charset=utf-8' : 'text/plain;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const anchor = element('a');
  anchor.href = url;
  anchor.download = 'curriculo-portugues.' + format;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  message('Currículo revisado baixado. O perfil original continua preservado.');
}
textButton.addEventListener('click', () => download('txt'));
printButton.addEventListener('click', () => download('html'));

async function loadSource() {
  if (!uuid.test(owner) || !uuid.test(interview)) {
    message('Abra uma entrevista salva e clique em “Criar currículo com IA” para selecionar o perfil.');
    return;
  }
  try {
    const record = await request(`/career/owners/${owner}/interviews/${interview}`);
    const container = byId('resume-facts');
    for (const [key, title] of Object.entries(topics)) if (record.facts[key]) {
      container.append(element('h3', title), element('blockquote', record.facts[key]));
    }
    byId('resume-source-date').textContent = 'Perfil salvo em ' + new Date(record.created_at).toLocaleString('pt-BR') + '.';
    byId('resume-source').hidden = false;
    loaded = Object.keys(record.facts).length > 0;
    generate.disabled = !loaded || !consent.checked;
    message(loaded ? 'Confira os fatos e autorize o envio para gerar o rascunho.' : 'Este perfil não contém fatos confirmados. Volte à entrevista para revisar.');
  } catch {
    message('Perfil não encontrado. Volte à entrevista e abra o perfil no espaço correto.');
  }
}
loadSource();
