const topics = {
  experience: ["Experiências", "Que funções você exerceu e quais eram suas responsabilidades?"],
  projects: ["Projetos", "De quais projetos você participou e qual foi sua contribuição?"],
  skills: ["Habilidades", "Que habilidades ou ferramentas você aplicou e em que situação?"],
  results: ["Resultados", "Quais resultados você ajudou a alcançar? Inclua números somente se souber."],
};

const byId = (id) => document.getElementById(id);
const controls = byId("interview-controls");
const questions = byId("interview-answers");
const review = byId("interview-review");
const detail = byId("interview-detail");
const list = byId("interview-list");
const ownerField = byId("interview-owner");
const answerFields = {};
const pageSize = 50;
let endpoint;
let offset = 0;
let draft;
let draftId;
let draftFields;
let savedRecord;
let correctionSource;
let reviewSeed;
let busy = false;

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function labeledTextArea(id, labelText, value = "") {
  const label = element("label", labelText);
  label.htmlFor = id;
  const field = element("textarea");
  field.id = id;
  field.maxLength = 3000;
  field.rows = 3;
  field.value = value;
  return { label, field };
}

for (const [topic, [, question]] of Object.entries(topics)) {
  const { label, field } = labeledTextArea("answer-" + topic, question);
  byId("interview-questions").append(label, field);
  answerFields[topic] = field;
}

function message(text) {
  byId("interview-status").textContent = text;
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Não foi possível concluir a ação (HTTP " + response.status + ").");
  return response.json();
}

async function run(action) {
  if (busy) return;
  busy = true;
  controls.disabled = true;
  try {
    await action();
  } catch (error) {
    message(error.message);
  } finally {
    controls.disabled = false;
    busy = false;
  }
}

function showQuestions() {
  questions.hidden = false;
  review.hidden = true;
  byId("interview-heading").textContent = correctionSource ? "1. Corrija suas respostas" : "1. Responda à entrevista";
}

function showSaved(record) {
  savedRecord = record;
  const sources = byId("interview-sources");
  sources.replaceChildren();
  for (const [topic, [title]] of Object.entries(topics)) {
    const section = element("section");
    section.className = "form-section";
    section.append(element("h4", title));
    if (record.facts[topic]) {
      section.append(element("p", record.facts[topic]), element("p", "Resposta original"), element("blockquote", record.answers[topic]));
    } else {
      section.append(element("p", "Nenhum fato confirmado."));
    }
    sources.append(section);
  }
  detail.hidden = false;
}

function resetCorrection() {
  correctionSource = null;
  reviewSeed = null;
  draft = null;
  questions.reset();
  byId("interview-correction-notice").hidden = true;
  byId("interview-cancel-correction").hidden = true;
  showQuestions();
}

byId("interview-correct").addEventListener("click", () => {
  if (!savedRecord) return;
  if (correctionSource || draft || Object.values(answerFields).some((field) => field.value.trim())) {
    message("Conclua a entrevista em andamento ou cancele a correção antes de corrigir outro perfil.");
    return;
  }
  correctionSource = savedRecord;
  reviewSeed = null;
  for (const [topic, field] of Object.entries(answerFields)) field.value = savedRecord.answers[topic] || "";
  byId("interview-correction-notice").hidden = false;
  byId("interview-cancel-correction").hidden = false;
  showQuestions();
  answerFields.experience.focus();
  message("Perfil carregado para correção. O registro anterior será preservado.");
});

byId("interview-cancel-correction").addEventListener("click", () => {
  resetCorrection();
  message("Correção cancelada. O perfil salvo permanece igual.");
});

function addToList(record, prepend = false) {
  const item = element("li");
  const timestamp = new Date(record.created_at).toLocaleString("pt-BR");
  const button = element("button", "Abrir perfil de " + timestamp);
  button.type = "button";
  button.className = "text-button";
  button.addEventListener("click", () => run(async () => {
    showSaved(await request(endpoint + "/" + record.id));
    message("Perfil profissional reaberto.");
  }));
  item.append(button);
  if (prepend) list.prepend(item);
  else list.append(item);
}

function showPage(records) {
  for (const record of records) addToList(record);
  offset += records.length;
  byId("interview-empty").hidden = offset > 0;
  byId("interview-more").hidden = records.length < pageSize;
}

byId("interview-connect").addEventListener("submit", (event) => {
  event.preventDefault();
  const owner = ownerField.value.trim();
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(owner)) {
    message("Informe um identificador de espaço válido.");
    return;
  }
  if (endpoint && (correctionSource || draft || Object.values(answerFields).some((field) => field.value.trim()))) {
    message("Salve a entrevista em andamento ou recarregue a página para trocar de espaço.");
    return;
  }
  run(async () => {
    const nextEndpoint = "/career/owners/" + owner + "/interviews";
    const records = await request(nextEndpoint + "?limit=" + pageSize);
    resetCorrection();
    endpoint = nextEndpoint;
    ownerField.value = owner;
    list.replaceChildren();
    offset = 0;
    detail.hidden = true;
    savedRecord = null;
    showPage(records);
    byId("interview-workspace").hidden = false;
    message("Espaço aberto.");
  });
});

byId("interview-more").addEventListener("click", () => run(async () => {
  showPage(await request(endpoint + "?limit=" + pageSize + "&offset=" + offset));
}));

questions.addEventListener("submit", (event) => {
  event.preventDefault();
  const answers = Object.fromEntries(
    Object.entries(answerFields).filter(([, field]) => field.value.trim()).map(([topic, field]) => [topic, field.value]),
  );
  if (!Object.keys(answers).length) {
    message("Responda pelo menos uma pergunta para revisar.");
    return;
  }
  draft = answers;
  draftId = crypto.randomUUID();
  draftFields = {};
  const container = byId("interview-draft");
  container.replaceChildren();
  for (const [topic, answer] of Object.entries(answers)) {
    const title = topics[topic][0];
    const section = element("section");
    section.className = "form-section";
    const include = element("input");
    include.type = "checkbox";
    const seed = reviewSeed || correctionSource;
    include.checked = !seed || !(topic in seed.answers) || topic in seed.facts;
    const includeLabel = element("label");
    includeLabel.className = "interview-include";
    includeLabel.append(include, " Incluir " + title.toLowerCase());
    const fact = seed && seed.answers[topic] === answer && topic in seed.facts ? seed.facts[topic] : answer;
    const { label, field } = labeledTextArea("fact-" + topic, "Fato sobre " + title.toLowerCase(), fact);
    field.disabled = !include.checked;
    include.addEventListener("change", () => { field.disabled = !include.checked; });
    section.append(element("h3", title), element("p", "Resposta original"), element("blockquote", answer), includeLabel, label, field);
    container.append(section);
    draftFields[topic] = { include, field };
  }
  questions.hidden = true;
  review.hidden = false;
  byId("interview-heading").textContent = "2. Revise e confirme os fatos";
  message("Rascunho preparado a partir das respostas. Confira antes de salvar.");
});

byId("interview-back").addEventListener("click", () => {
  reviewSeed = {
    answers: draft,
    facts: Object.fromEntries(Object.entries(draftFields).filter(([, entry]) => entry.include.checked).map(([topic, entry]) => [topic, entry.field.value])),
  };
  draft = null;
  showQuestions();
  message("Respostas disponíveis para edição.");
});

review.addEventListener("submit", (event) => {
  event.preventDefault();
  const facts = Object.fromEntries(
    Object.entries(draftFields).filter(([, entry]) => entry.include.checked).map(([topic, entry]) => [topic, entry.field.value.trim()]),
  );
  if (!Object.keys(facts).length || Object.values(facts).some((fact) => !fact)) {
    message("Mantenha pelo menos um fato e preencha todos os fatos marcados.");
    return;
  }
  run(async () => {
    const record = await request(endpoint + "/" + draftId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers: draft, facts }),
    });
    addToList(record, true);
    offset += 1;
    byId("interview-empty").hidden = true;
    showSaved(record);
    resetCorrection();
    message("Perfil profissional salvo. Os fatos confirmados e suas fontes estão disponíveis abaixo.");
  });
});

try {
  ownerField.value = localStorage.getItem("career-owner-id") || "";
} catch {
  // The space can still be opened manually.
}
