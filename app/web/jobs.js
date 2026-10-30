import {compareText} from '/jobs/assets/jobs-comparison.js';
const $ = id => document.getElementById(id);
let owner = "", selected = null, dirty = false, busy = false, jobs = [], captures = [], epoch = 0;
let comparisonCapture = null, extractions = [], comparisonProfiles = [];
let reviewDirty = false, reviewExtractor = "manual-reviewed", factSequence = 0;
const pageSize = 20;
function status(message, error = false) { $("status").hidden = false; $("status").textContent = message; $("status").className = error ? "error" : ""; }
async function api(path, method = "GET", data) {
  const response = await fetch(path, {method, headers: data ? {"Content-Type":"application/json"} : {}, body: data ? JSON.stringify(data) : undefined});
  const result = await response.json();
  if (!response.ok) {
    const message = response.status === 409 ? "Há uma captura mais recente. Seu texto não foi descartado. Recarregue antes de salvar." : response.status === 404 ? "Espaço ou vaga não encontrado. Confira o identificador." : response.status === 422 ? "Confira os campos: texto não vazio, link HTTP/HTTPS e confirmação apenas com link." : "Não foi possível concluir a operação.";
    const error = new Error(message); error.code = response.status; throw error;
  }
  return result;
}
const base = () => `/career/owners/${encodeURIComponent(owner)}/jobs`;
const date = value => value ? new Date(value).toLocaleString("pt-BR") : "Não informado";
function remember(id) { try { localStorage.setItem("career-owner-id", id); } catch {} }
function discard() { return !(dirty || reviewDirty) || window.confirm("Descartar as alterações ainda não salvas?"); }
function discardReview() { return !reviewDirty || window.confirm("Descartar os fatos ainda não salvos desta revisão?"); }
function lock(value) { busy = value; for (const input of document.querySelectorAll("form input, form textarea, form button, #eligibility-panel button, #eligibility-panel select, #continue-review")) input.disabled = value; for (const id of ["save-job", "new-job", "more-jobs", "more-history", "reload-job"]) $(id).disabled = value || (id === "new-job" && !owner); $("compare-profile").disabled = value || !extractions.length || !comparisonProfiles.length; }
function localTime(value) {
  if (!value) return "";
  const d = new Date(value); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0,16);
}
function show(job = null) {
  selected = job; dirty = false; epoch++;
  resetEligibility(job?.latest || null);
  $("next-step").hidden = !job;
  $("welcome").hidden = true; $("editor").hidden = false; $("history").hidden = !job;
  $("capture-preview").hidden = true; $("reload-job").hidden = true;
  const c = job?.latest;
  $("editor-title").textContent = job ? "Nova captura da mesma vaga" : "Nova vaga";
  $("version").textContent = job ? `Última captura: ${c.version}` : "Primeira captura";
  $("job-label").value = c?.label || ""; $("source-url").value = c?.source_url || "";
  $("confirmed").checked = c?.association_confirmed || false;
  $("original-text").value = c?.original_text || ""; $("captured-at").value = localTime(c?.captured_at);
  $("save-job").textContent = job ? "Salvar nova captura" : "Salvar vaga";
  $("save-hint").textContent = job ? "As capturas anteriores permanecem no histórico." : "O texto fica no banco local.";
  renderJobs();
}
function renderJobs() {
  for (const containerId of ["job-list", "welcome-jobs"]) {
    const container = $(containerId); container.replaceChildren();
    if (!jobs.length) {
      const p = document.createElement("p"); p.className = "empty";
      p.textContent = owner ? "Nenhuma vaga cadastrada neste espaço. Use + Nova vaga para começar." : "Abra seu espaço para ver as vagas salvas.";
      container.append(p);
    }
    for (const job of jobs) {
      const button = document.createElement("button"); button.type = "button";
      button.className = "profile-item" + (selected?.id === job.id ? " selected" : "");
      button.textContent = job.latest.label;
      const small = document.createElement("small"); small.textContent = `Abrir e comparar · Captura ${job.latest.version} · ${date(job.latest.imported_at)}`;
      button.append(small);
      button.addEventListener("click", async () => {
        if (busy || !discard()) return; lock(true);
        try {
          const result = await api(`${base()}/${job.id}`); show(result); await loadHistory();
          const loaded = await loadEligibility();
          status("Vaga aberta. Confira os fatos e escolha um perfil para comparar.");
          if (loaded) {
            const target = $(extractions.length && comparisonProfiles.length ? "comparison-heading" : "eligibility-heading");
            target.focus(); target.scrollIntoView({block:"start"});
          }
        } catch(e) { status(e.message,true); } finally { lock(false); }
      });
      container.append(button);
    }
  }
}
async function loadJobs(append=false) {
  const result = await api(`${base()}?limit=${pageSize}&offset=${append ? jobs.length : 0}`);
  jobs = append ? jobs.concat(result) : result; $("more-jobs").hidden = result.length < pageSize; renderJobs();
}
function renderComparison(original, latest) {
  const panel = $("capture-comparison");
  panel.replaceChildren();
  const title = document.createElement("h3"); title.textContent = "O que mudou"; panel.append(title);
  if (original.version === latest.version) {
    const note = document.createElement("p"); note.textContent = "Escolha uma captura anterior no histórico para comparar com a mais recente.";
    panel.append(note); return;
  }
  const info = document.createElement("p"); info.textContent = `Captura ${original.version} → Captura ${latest.version} (mais recente carregada). Comparação dos textos salvos; alterações no formulário não entram aqui.`;
  panel.append(info);
  const origin = document.createElement("p");
  origin.textContent = original.source_url === latest.source_url ? "Link de origem: sem alteração." : `Link anterior: ${original.source_url || "Não informado"}\nLink mais recente: ${latest.source_url || "Não informado"}`;
  origin.className = "comparison-origin"; panel.append(origin);
  const diff = compareText(original.original_text, latest.original_text);
  const note = document.createElement("p"); note.className = "hint";
  note.textContent = diff.changed ? "Destaque do primeiro ao último caractere diferente. O trecho pode incluir partes que permaneceram iguais." : "Descrição: sem alteração.";
  panel.append(note);
  if (!diff.changed) return;
  const columns = document.createElement("div"); columns.className = "grid";
  for (const [label, text, tag] of [[`Antes · Captura ${original.version}`, diff.removed, "del"], [`Depois · Captura ${latest.version}`, diff.added, "ins"]]) {
    const column = document.createElement("div"), heading = document.createElement("h4"), pre = document.createElement("pre");
    heading.textContent = label; pre.className = "comparison-text";
    const highlight = document.createElement(tag); highlight.textContent = text;
    pre.append(document.createTextNode(diff.prefix), highlight, document.createTextNode(diff.suffix));
    column.append(heading, pre); columns.append(column);
  }
  panel.append(columns);
}
async function loadHistory(append=false) {
  const source = selected.id, token = epoch;
  const result = await api(`${base()}/${source}/snapshots?limit=${pageSize}&offset=${append ? captures.length : 0}`);
  if (epoch !== token) return;
  captures = append ? captures.concat(result) : result; $("more-history").hidden = result.length < pageSize;
  $("history-list").replaceChildren();
  for (const c of captures) {
    const item = document.createElement("div"); item.className = "history-entry";
    const button = document.createElement("button"); button.type = "button"; button.className = "secondary"; button.textContent = `Captura ${c.version} · ${c.label}`;
    const info = document.createElement("p"); info.className = "hint"; info.textContent = `Cadastrada: ${date(c.imported_at)} · Fonte consultada: ${date(c.captured_at)}`;
    button.addEventListener("click", async () => {
      if (busy || !discardReview()) return; lock(true);
      try { const original = await api(`${base()}/${source}/snapshots/${c.version}`);
        if (epoch !== token) return;
        $("capture-title").textContent = `Captura ${original.version} — somente leitura`;
        $("capture-text").value = original.original_text; $("capture-origin").replaceChildren();
        if (original.source_url) { const a = document.createElement("a"); a.href = original.source_url; a.target = "_blank"; a.rel = "noopener noreferrer"; a.textContent = "Abrir link informado"; $("capture-origin").append(a); }
        const p = document.createElement("span"); p.textContent = original.association_confirmed ? " · Associação declarada pelo usuário" : " · Associação não confirmada"; $("capture-origin").append(p);
        $("capture-preview").hidden = false;
        renderComparison(original, selected.latest);
        resetEligibility(original);
      } catch(e) { status(e.message,true); } finally { lock(false); }
    }); item.append(button,info); $("history-list").append(item);
  }
}
$("connect-form").addEventListener("submit", async e => {
  e.preventDefault(); if (busy || !discard()) return;
  const id = $("owner-id").value.trim();
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) return status("Cole o identificador completo do proprietário.",true);
  lock(true); const previous = owner; owner = id;
  try { await loadJobs(); remember(owner); selected = null; dirty = false; epoch++; resetEligibility(); $("editor").hidden = true; $("history").hidden = true; $("welcome").hidden = false; status("Espaço aberto. Escolha uma vaga ou cadastre uma nova."); }
  catch(e) { owner = previous; status(e.message,true); } finally { lock(false); }
});
$("new-job").addEventListener("click", () => { if (!busy && discard()) { show(); $("job-label").focus(); } });
$("job-form").addEventListener("input", () => { dirty = true; });
$("job-form").addEventListener("submit", async e => {
  e.preventDefault(); if (busy || !owner) return;
  if (!discardReview()) return;
  const data = {label:$("job-label").value, original_text:$("original-text").value, source_url:$("source-url").value.trim() || null, association_confirmed:$("confirmed").checked, captured_at:null};
  if (!data.original_text.trim() || !data.label.trim()) return status("Preencha um nome e a descrição original.",true);
  if (data.association_confirmed && !data.source_url) return status("Informe o link antes de confirmar a associação.",true);
  // Preserve the original timestamp when unchanged, including seconds and its offset.
  data.captured_at = $("captured-at").value === localTime(selected?.latest.captured_at) ? (selected?.latest.captured_at || null) : $("captured-at").value ? new Date($("captured-at").value).toISOString() : null;
  if (selected) data.expected_version = selected.latest.version;
  lock(true); let saved = false;
  try {
    const result = await api(selected ? `${base()}/${selected.id}/snapshots` : base(), "POST",data);
    saved = true; show(result); await loadJobs(); await loadHistory(); status("Vaga salva. Próximo passo: revisar os fatos da descrição e comparar com seu perfil.");
  } catch(e) { if(e.code === 409) $("reload-job").hidden = false; status(saved ? "Captura salva, mas a lista não pôde ser atualizada. Reabra o espaço para consultar." : e.message,true); }
  finally { lock(false); if(saved){$("continue-review").focus();$("continue-review").scrollIntoView({block:"center"});} }
});
$("reload-job").addEventListener("click", async () => {
  if (busy || !selected || !discard()) return; lock(true);
  try { const result = await api(`${base()}/${selected.id}`); show(result); await loadHistory(); status("Última captura carregada."); } catch(e) {status(e.message,true);} finally {lock(false);}
});
$("more-jobs").addEventListener("click",async()=>{if(busy)return;lock(true);try{await loadJobs(true);}catch(e){status(e.message,true);}finally{lock(false);}});
$("more-history").addEventListener("click",async()=>{if(busy)return;lock(true);try{await loadHistory(true);}catch(e){status(e.message,true);}finally{lock(false);}});
window.addEventListener("beforeunload",e=>{if(dirty || reviewDirty){e.preventDefault();e.returnValue="";}});

const resultLabels = {compatible:"Compatível com as restrições avaliadas", incompatible:"Incompatível", needs_confirmation:"Precisa confirmar", incomplete_profile:"Perfil incompleto: configure um caminho no perfil"};
const fieldLabels = {work_arrangement:"Modalidade", work_countries:"Países de trabalho", employer_countries:"País da empresa", sponsorship:"Patrocínio", contract:"Contratação", compensation:"Remuneração", authorization:"Autorização declarada", authorization_restriction:"Restrição de autorização", working_time:"Jornada", skill_group:"Habilidades"};
const knowledgeLabels = {explicit:"Explícito", inferred:"Inferido", not_provided:"Não informado"};
const valueLabels = {remote:"Remoto", hybrid:"Híbrido", on_site:"Presencial", employee:"Vínculo empregatício", contractor:"Contractor/PJ", self_employed:"Autônomo", other:"Outro", offered:"Oferecido", not_offered:"Não oferecido", full_time:"Tempo integral", part_time:"Tempo parcial", advertised:"Anunciada", actual_payment:"Pagamento efetivo", gross:"Bruto", net:"Líquido", unknown:"Não informado", hour:"Hora", month:"Mês", year:"Ano", countries:"Países", alternatives:"Alternativas", minimum:"Mínimo", maximum:"Máximo", currency:"Moeda", currency_basis:"Base da moeda", period:"Período", amount_basis:"Base do valor"};
function factValue(value) {
  if (value === null) return "Não informado";
  if (Array.isArray(value)) return value.map(factValue).join(", ");
  if (typeof value === "object") return Object.entries(value).map(([key, item]) => `${valueLabels[key] || key}: ${factValue(item)}`).join(" · ");
  return valueLabels[value] || String(value);
}
function paragraph(parent, text, className = "") {
  const p = document.createElement("p"); p.textContent = text; p.className = className; parent.append(p); return p;
}
function resetEligibility(capture = null) {
  clearReview();
  comparisonCapture = capture; extractions = []; comparisonProfiles = [];
  $("eligibility-panel").hidden = !capture; $("eligibility-options").hidden = true;
  $("eligibility-status").textContent = "";
  for (const id of ["eligibility-result", "extraction-facts", "extraction-select", "comparison-profile"]) $(id).replaceChildren();
  for (const id of ["more-extractions", "more-comparison-profiles"]) $(id).hidden = true;
  $("eligibility-context").textContent = capture ? `Captura ${capture.version} · ${capture.label}` : "";
  $("review-source").value = capture?.original_text || "";
}
const extractionBase = () => `${base()}/${selected.id}/snapshots/${comparisonCapture.version}/extractions`;
function selectedExtraction() { return extractions.find(run => run.id === $("extraction-select").value); }
function renderClaim(parent, claim) {
  const entry = document.createElement("div"); entry.className = "history-path";
  paragraph(entry, `${fieldLabels[claim.field_key] || claim.field_key} · ${knowledgeLabels[claim.knowledge] || claim.knowledge}`);
  if (claim.value !== null) paragraph(entry, factValue(claim.value), "comparison-origin");
  if (claim.basis) paragraph(entry, `Base da inferência: ${claim.basis}`, "hint");
  for (const evidence of claim.evidence) {
    const quote = document.createElement("blockquote"); quote.className = "comparison-origin"; quote.textContent = evidence.excerpt; entry.append(quote);
  }
  parent.append(entry);
}
function renderFacts() {
  $("extraction-facts").replaceChildren(); $("eligibility-result").replaceChildren();
  const run = selectedExtraction();
  if (run) for (const claim of run.claims) renderClaim($("extraction-facts"), claim);
}
function fillComparisonOptions() {
  const previousRun = $("extraction-select").value, previousProfile = $("comparison-profile").value;
  $("extraction-select").replaceChildren(); $("comparison-profile").replaceChildren();
  for (const [index, run] of extractions.entries()) {
    const option = document.createElement("option"); option.value = run.id;
    option.textContent = `${date(run.created_at)} · ${run.extractor} · ${run.id.slice(0,8)}${index === 0 ? " (mais recente carregado)" : ""}`;
    $("extraction-select").append(option);
  }
  for (const profile of comparisonProfiles) {
    const option = document.createElement("option"); option.value = profile.id;
    option.textContent = `${profile.label} · versão ${profile.latest.version}`; $("comparison-profile").append(option);
  }
  if (extractions.some(run => run.id === previousRun)) $("extraction-select").value = previousRun;
  if (comparisonProfiles.some(profile => profile.id === previousProfile)) $("comparison-profile").value = previousProfile;
  $("eligibility-options").hidden = !extractions.length;
  const notes = [];
  if (!extractions.length) notes.push("Ainda não há fatos salvos nesta captura. Use a etapa 1 acima para adicionar fatos e salvar sua revisão.");
  if (!comparisonProfiles.length) notes.push("Nenhum perfil disponível neste espaço. Cadastre um em Meus perfis e carregue novamente.");
  $("eligibility-status").textContent = notes.join(" ") || "Fatos e perfis carregados. Confira as evidências antes de comparar.";
  renderFacts();
}
async function loadComparisonOptions(kind, append = false) {
  const runs = kind === "extractions", items = runs ? extractions : comparisonProfiles;
  const path = runs ? extractionBase() : `/career/owners/${encodeURIComponent(owner)}/profiles`;
  const result = await api(`${path}?limit=${pageSize}&offset=${append ? items.length : 0}`);
  if (runs) extractions = append ? items.concat(result) : result;
  else comparisonProfiles = append ? items.concat(result) : result;
  $(runs ? "more-extractions" : "more-comparison-profiles").hidden = result.length < pageSize;
}
async function loadEligibility() {
  $("eligibility-result").replaceChildren();
  $("eligibility-status").textContent = "Carregando fatos e perfis…";
  try {
    const loaded = await Promise.allSettled([loadComparisonOptions("extractions"), loadComparisonOptions("profiles")]);
    if (loaded.some(item => item.status === "rejected")) throw new Error("Load failed");
    fillComparisonOptions(); return true;
  } catch {
    extractions = []; comparisonProfiles = []; $("eligibility-options").hidden = true;
    $("eligibility-status").textContent = "Não foi possível carregar fatos e perfis. Tente novamente. Sua revisão foi preservada.";
    return false;
  }
}
$("load-eligibility").addEventListener("click", async () => {
  if (busy || !comparisonCapture) return;
  lock(true);
  try { await loadEligibility(); } finally { lock(false); }
});
for (const [id, kind] of [["more-extractions", "extractions"], ["more-comparison-profiles", "profiles"]]) {
  $(id).addEventListener("click", async () => {
    if (busy) return; lock(true); $("eligibility-result").replaceChildren();
    try { await loadComparisonOptions(kind, true); fillComparisonOptions(); }
    catch { $("eligibility-status").textContent = "Não foi possível carregar mais opções. Tente novamente."; }
    finally { lock(false); }
  });
}
$("extraction-select").addEventListener("change", renderFacts);
$("comparison-profile").addEventListener("change", () => $("eligibility-result").replaceChildren());
$("compare-profile").addEventListener("click", async () => {
  const run = selectedExtraction(), profile = comparisonProfiles.find(item => item.id === $("comparison-profile").value);
  if (busy || !run || !profile) return; lock(true); $("eligibility-result").replaceChildren();
  $("eligibility-status").textContent = "Comparando as versões selecionadas…";
  try {
    const result = await api(`${extractionBase()}/${encodeURIComponent(run.id)}/comparison?profile_id=${encodeURIComponent(profile.id)}&profile_version=${profile.latest.version}`);
    const panel = $("eligibility-result");
    const heading = document.createElement("h3"); heading.textContent = resultLabels[result.eligibility]; panel.append(heading);
    paragraph(panel, `Captura ${comparisonCapture.version} · Fatos ${run.id} · ${profile.label}, versão ${profile.latest.version} · Regras ${result.rules_version}`, "hint");
    for (const path of result.pathways) {
      const section = document.createElement("section"); section.className = "pathway";
      const title = document.createElement("h4"); title.textContent = `${path.label}: ${resultLabels[path.eligibility]}`; section.append(title);
      if (!path.required_criteria) paragraph(section, "Este caminho não tem restrições obrigatórias configuradas. O resultado não comprova elegibilidade para trabalhar.", "hint");
      for (const criterion of path.criteria) {
        const detail = document.createElement("details"); detail.className = "form-section";
        const summary = document.createElement("summary");
        summary.textContent = `${fieldLabels[criterion.key] || criterion.key} · ${criterion.strength === "required" ? "Obrigatório" : "Preferência (não elimina)"} · ${resultLabels[criterion.result]}`;
        detail.append(summary);
        paragraph(detail, criterion.explanation);
        for (const id of criterion.claim_ids) { const claim = run.claims.find(item => item.id === id); if (claim) renderClaim(detail, claim); }
        if (!criterion.claim_ids.length) paragraph(detail, "Sem fato da vaga associado a este critério.", "hint");
        section.append(detail);
      }
      panel.append(section);
    }
    $("eligibility-status").textContent = "Comparação concluída. O resultado não foi salvo.";
  } catch { $("eligibility-status").textContent = "Não foi possível comparar. Recarregue fatos e perfis e tente novamente."; }
  finally { lock(false); }
});
function clearReview() {
  reviewDirty = false; reviewExtractor = "manual-reviewed";
  $("review-form").hidden = true; $("review-claims").replaceChildren();
  $("review-confirmed").checked = false; $("review-status").textContent = "";
}
function reviewChanged() { reviewDirty = true; $("review-confirmed").checked = false; $("eligibility-result").replaceChildren(); }
function control(parent, label, options = null, value = "") {
  const id = `fact-${++factSequence}`, wrap = document.createElement("div"), text = document.createElement("label");
  text.htmlFor = id; text.textContent = label;
  const input = document.createElement(options ? "select" : "input"); input.id = id;
  if (options) for (const [code, name] of options) { const option = document.createElement("option"); option.value = code; option.textContent = name; input.append(option); }
  input.value = value ?? ""; wrap.append(text,input); parent.append(wrap); return input;
}
const factEnums = {
  work_arrangement:["remote","hybrid","on_site"], sponsorship:["offered","not_offered"],
  working_time:["full_time","part_time","other"]
};
function enumOptions(values) { return [["","Selecione"], ...values.map(code => [code,valueLabels[code] || code])]; }
function addReviewClaim(claim = {field_key:"work_arrangement", knowledge:"explicit", value:null, evidence:[]}) {
  const row = document.createElement("section"); row.className = "pathway review-fact";
  const heading = document.createElement("h4"); heading.textContent = "Fato da vaga"; row.append(heading);
  const field = control(row,"Informação da vaga",Object.entries(fieldLabels).filter(([key]) => !["authorization"].includes(key)),claim.field_key);
  const knowledge = control(row,"O que a descrição informa?",[["explicit","Informação explícita no texto"],["not_provided","Não informado na descrição"]],claim.knowledge);
  const body = document.createElement("div"); row.append(body);
  let readValue, excerpt, requirement;
  function buildValue(value = null, quote = "", strength = "informational") {
    body.replaceChildren(); body.hidden = knowledge.value === "not_provided";
    if (body.hidden) return;
    const key = field.value;
    if (factEnums[key]) {
      const input = control(body,"Valor",enumOptions(factEnums[key]),value); input.required = true; readValue = () => input.value;
    } else if (key === "contract") {
      const codes = ["employee","contractor","self_employed","other"];
      paragraph(body,"Marque uma opção, ou várias somente se a vaga oferecer explicitamente essa escolha.","hint");
      const choices = document.createElement("fieldset"); choices.className = "choices"; const legend = document.createElement("legend"); legend.textContent = "Tipos de contratação oferecidos"; choices.append(legend);
      const selectedValues = typeof value === "string" ? [value] : value?.alternatives || [];
      const inputs = codes.map(code => { const label = document.createElement("label"), input = document.createElement("input"); input.type="checkbox"; input.value=code; input.checked=selectedValues.includes(code); label.append(input,document.createTextNode(valueLabels[code])); choices.append(label); return input; }); body.append(choices);
      readValue = () => { const values = inputs.filter(i => i.checked).map(i => i.value); if (!values.length) throw new Error("Selecione ao menos um tipo de contratação."); return values.length === 1 ? values[0] : {alternatives:values}; };
    } else if (key === "compensation") {
      const group = document.createElement("div"); group.className="grid"; body.append(group);
      const min = control(group,"Valor mínimo (opcional)",null,value?.minimum), max = control(group,"Valor máximo (opcional)",null,value?.maximum);
      for (const input of [min,max]) { input.type="number"; input.min="0"; input.step="any"; }
      const currency = control(group,"Moeda (três letras, ex.: BRL)",null,value?.currency); currency.required=true; currency.pattern="[A-Za-z]{3}";
      const basis = control(group,"Moeda anunciada ou pagamento efetivo?",enumOptions(["advertised","actual_payment"]),value?.currency_basis); basis.required=true;
      const period = control(group,"Período",enumOptions(["hour","month","year"]),value?.period); period.required=true;
      const amount = control(group,"Valor bruto ou líquido?",enumOptions(["gross","net","unknown"]),value?.amount_basis || "unknown"); amount.required=true;
      readValue = () => { if (!min.value && !max.value) throw new Error("Informe ao menos um valor de remuneração."); return {minimum:min.value || null,maximum:max.value || null,currency:currency.value.toUpperCase(),currency_basis:basis.value,period:period.value,amount_basis:amount.value}; };
    } else {
      const countries = key === "work_countries" || key === "employer_countries", skills = key === "skill_group";
      const input = control(body,countries ? "Países (duas letras, separados por vírgula, ex.: BR, PT)" : skills ? "Habilidade ou alternativas aceitas (separadas por vírgula)" : "Restrição declarada no texto",null,countries ? value?.countries?.join(", ") : skills ? value?.alternatives?.join(", ") : value);
      input.required=true;
      readValue = () => { const values=input.value.split(",").map(item=>item.trim()).filter(Boolean); return countries ? {countries:values.map(item=>item.toUpperCase())} : skills ? {alternatives:values} : input.value; };
    }
    requirement = control(body,"Importância declarada pela vaga",[["informational","Informação sobre a vaga"],["required","Requisito obrigatório"],["preferred","Requisito desejável"]],strength || "informational");
    const label = document.createElement("label"); excerpt=document.createElement("textarea"); excerpt.id=`fact-${++factSequence}`; label.htmlFor=excerpt.id; label.textContent="Trecho exato que comprova este fato"; excerpt.rows=3; excerpt.required=true; excerpt.maxLength=5000; excerpt.value=quote; body.append(label,excerpt);
    paragraph(body,"Copie um trecho da descrição salva acima. Se aparecer repetido, copie um trecho maior que apareça só uma vez. O trecho deve sustentar o valor escolhido.","hint");
  }
  buildValue(claim.value,claim.evidence?.[0]?.excerpt || "",claim.requirement);
  field.addEventListener("change",()=>{buildValue(); reviewChanged();});
  knowledge.addEventListener("change",()=>{buildValue(); reviewChanged();});
  row.addEventListener("input",reviewChanged);
  const remove = document.createElement("button"); remove.type="button"; remove.className="text-button remove"; remove.textContent="Remover este fato";
  remove.addEventListener("click",()=>{if(busy)return;row.remove();reviewChanged();if(!$("review-claims").children.length) $("review-form").hidden=true;}); row.append(remove);
  row.readClaim = () => {
    if (knowledge.value === "not_provided") return {field_key:field.value,knowledge:"not_provided"};
    const quote = excerpt.value, text = comparisonCapture.original_text, index=text.indexOf(quote);
    if (!quote || index < 0 || text.indexOf(quote,index+1) !== -1) throw new Error("Confira o trecho de evidência: ele deve existir exatamente uma vez na descrição salva.");
    const start=Array.from(text.slice(0,index)).length;
    return {field_key:field.value,knowledge:"explicit",value:readValue(),requirement:requirement.value,evidence:[{start_char:start,end_char:start+Array.from(quote).length,excerpt:quote}]};
  };
  $("review-claims").append(row); $("review-form").hidden=false;
  return field;
}
$("continue-review").addEventListener("click",()=>{if(busy)return;$("eligibility-heading").focus();$("eligibility-heading").scrollIntoView({block:"start"});});
$("add-fact").addEventListener("click",()=>{if(busy)return;if($("review-claims").children.length>=200)return;addReviewClaim().focus();reviewChanged();});
$("discard-review").addEventListener("click",()=>{if(!busy && discardReview())clearReview();});
$("draft-facts").addEventListener("click",async()=>{
  if(busy || !comparisonCapture || !discardReview())return;
  lock(true);$("eligibility-result").replaceChildren();$("review-status").textContent="A IA está preparando o rascunho. Aguarde; nada será salvo automaticamente…";
  try {
    const draft=await api(`${extractionBase()}/draft`,"POST"); clearReview(); reviewExtractor=draft.extractor;
    for(const claim of draft.claims)addReviewClaim(claim);
    reviewDirty=!!draft.claims.length;
    $("review-status").textContent=draft.claims.length ? `Rascunho pronto com ${draft.claims.length} fatos. Confira cada valor e trecho antes de salvar. ${draft.discarded.length} sugestões foram descartadas na validação.` : "A IA não retornou fatos utilizáveis. Você pode adicioná-los manualmente.";
    for(const discarded of draft.discarded)paragraph($("review-status"),`Sugestão descartada: ${discarded.reason}`,"hint");
  }catch(e){
    const reasons = {
      401:"A chave do Ollama Cloud precisa ser corrigida no servidor.",
      402:"É necessário adicionar créditos de uso à conta Ollama.",
      404:"Não foi possível localizar a captura ou o modelo no Ollama Cloud.",
      429:"O limite de uso do Ollama Cloud foi atingido. Aguarde antes de tentar novamente.",
      503:"O acesso à IA ainda não foi configurado.",
      422:"O rascunho automático aceita até 12.000 caracteres.",
    };
    $("review-status").textContent=(reasons[e.code] || "Não foi possível gerar o rascunho no Ollama Cloud.") + " Sua revisão foi preservada. Você pode continuar manualmente.";
  }
  finally{lock(false);}
});
$("review-form").addEventListener("submit",async e=>{
  e.preventDefault();if(busy || !comparisonCapture || !$("review-confirmed").checked)return;
  let claims;try{claims=Array.from($("review-claims").children,row=>row.readClaim());if(!claims.length)throw new Error("Adicione ao menos um fato.");}
  catch(error){$("review-status").textContent=error.message;return;}
  lock(true);let saved=false;
  try{
    const run=await api(extractionBase(),"POST",{extractor:reviewExtractor,claims});saved=true;clearReview();
    extractions.unshift(run);fillComparisonOptions();$("extraction-select").value=run.id;renderFacts();
    await loadComparisonOptions("profiles");fillComparisonOptions();$("extraction-select").value=run.id;renderFacts();
    $("review-status").textContent="Fatos revisados salvos. Agora escolha o perfil na etapa 2 e compare.";
  }catch(error){$("review-status").textContent=saved ? "Fatos salvos. Não foi possível atualizar os perfis; use Atualizar fatos e perfis na etapa 2." : "Não foi possível salvar. Sua revisão foi preservada. Confira valores, países, remuneração e trechos de evidência e tente novamente.";}
  finally{lock(false);if(saved){$("comparison-profile").focus();$("comparison-profile").scrollIntoView({block:"center"});}}
});
try { $("owner-id").value = localStorage.getItem("career-owner-id") || ""; } catch {}
if ($("owner-id").value) $("connect-form").requestSubmit();
