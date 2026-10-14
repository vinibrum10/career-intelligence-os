import {compareText} from '/jobs/assets/jobs-comparison.js';
const $ = id => document.getElementById(id);
let owner = "", selected = null, dirty = false, busy = false, jobs = [], captures = [], epoch = 0;
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
function discard() { return !dirty || window.confirm("Descartar as alterações ainda não salvas?"); }
function lock(value) { busy = value; for (const input of document.querySelectorAll("form input, form textarea, form button")) input.disabled = value; for (const id of ["save-job", "new-job", "more-jobs", "more-history", "reload-job"]) $(id).disabled = value || (id === "new-job" && !owner); }
function localTime(value) {
  if (!value) return "";
  const d = new Date(value); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0,16);
}
function show(job = null) {
  selected = job; dirty = false; epoch++;
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
  $("job-list").replaceChildren();
  if (!jobs.length) { const p = document.createElement("p"); p.className = "empty"; p.textContent = "Nenhuma vaga cadastrada neste espaço."; $("job-list").append(p); }
  for (const job of jobs) {
    const button = document.createElement("button"); button.type = "button"; button.className = "profile-item" + (selected?.id === job.id ? " selected" : "");
    button.textContent = job.latest.label; const small = document.createElement("small"); small.textContent = `Captura ${job.latest.version} · ${date(job.latest.imported_at)}`; button.append(small);
    button.addEventListener("click", async () => {
      if (busy || !discard()) return; lock(true);
      try { const result = await api(`${base()}/${job.id}`); show(result); await loadHistory(); status("Vaga aberta. Para registrar mudanças, salve uma nova captura."); }
      catch(e) { status(e.message,true); } finally { lock(false); }
    }); $("job-list").append(button);
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
      if (busy) return; lock(true);
      try { const original = await api(`${base()}/${source}/snapshots/${c.version}`);
        if (epoch !== token) return;
        $("capture-title").textContent = `Captura ${original.version} — somente leitura`;
        $("capture-text").value = original.original_text; $("capture-origin").replaceChildren();
        if (original.source_url) { const a = document.createElement("a"); a.href = original.source_url; a.target = "_blank"; a.rel = "noopener noreferrer"; a.textContent = "Abrir link informado"; $("capture-origin").append(a); }
        const p = document.createElement("span"); p.textContent = original.association_confirmed ? " · Associação declarada pelo usuário" : " · Associação não confirmada"; $("capture-origin").append(p);
        $("capture-preview").hidden = false;
        renderComparison(original, selected.latest);
      } catch(e) { status(e.message,true); } finally { lock(false); }
    }); item.append(button,info); $("history-list").append(item);
  }
}
$("connect-form").addEventListener("submit", async e => {
  e.preventDefault(); if (busy || !discard()) return;
  const id = $("owner-id").value.trim();
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) return status("Cole o identificador completo do proprietário.",true);
  lock(true); const previous = owner; owner = id;
  try { await loadJobs(); remember(owner); selected = null; dirty = false; epoch++; $("editor").hidden = true; $("history").hidden = true; $("welcome").hidden = false; status("Espaço aberto. Escolha uma vaga ou cadastre uma nova."); }
  catch(e) { owner = previous; status(e.message,true); } finally { lock(false); }
});
$("new-job").addEventListener("click", () => { if (!busy && discard()) { show(); $("job-label").focus(); } });
$("job-form").addEventListener("input", () => { dirty = true; });
$("job-form").addEventListener("submit", async e => {
  e.preventDefault(); if (busy || !owner) return;
  const data = {label:$("job-label").value, original_text:$("original-text").value, source_url:$("source-url").value.trim() || null, association_confirmed:$("confirmed").checked, captured_at:null};
  if (!data.original_text.trim() || !data.label.trim()) return status("Preencha um nome e a descrição original.",true);
  if (data.association_confirmed && !data.source_url) return status("Informe o link antes de confirmar a associação.",true);
  // Preserve the original timestamp when unchanged, including seconds and its offset.
  data.captured_at = $("captured-at").value === localTime(selected?.latest.captured_at) ? (selected?.latest.captured_at || null) : $("captured-at").value ? new Date($("captured-at").value).toISOString() : null;
  if (selected) data.expected_version = selected.latest.version;
  lock(true); let saved = false;
  try {
    const result = await api(selected ? `${base()}/${selected.id}/snapshots` : base(), "POST",data);
    saved = true; show(result); await loadJobs(); await loadHistory(); status("Captura salva. Texto e referência preservados no banco local.");
  } catch(e) { if(e.code === 409) $("reload-job").hidden = false; status(saved ? "Captura salva, mas a lista não pôde ser atualizada. Reabra o espaço para consultar." : e.message,true); }
  finally { lock(false); }
});
$("reload-job").addEventListener("click", async () => {
  if (busy || !selected || !discard()) return; lock(true);
  try { const result = await api(`${base()}/${selected.id}`); show(result); await loadHistory(); status("Última captura carregada."); } catch(e) {status(e.message,true);} finally {lock(false);}
});
$("more-jobs").addEventListener("click",async()=>{if(busy)return;lock(true);try{await loadJobs(true);}catch(e){status(e.message,true);}finally{lock(false);}});
$("more-history").addEventListener("click",async()=>{if(busy)return;lock(true);try{await loadHistory(true);}catch(e){status(e.message,true);}finally{lock(false);}});
window.addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue="";}});
try { $("owner-id").value = localStorage.getItem("career-owner-id") || ""; } catch {}
if ($("owner-id").value) $("connect-form").requestSubmit();
