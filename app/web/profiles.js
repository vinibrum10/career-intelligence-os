"use strict";
const $ = (id) => document.getElementById(id);
const clone = (value) => structuredClone(value);
const modes = {unspecified: "Não informado", unrestricted: "Sem restrição", required: "Obrigatório", preferred: "Preferencial"};
const arrangements = {remote: "Remoto", hybrid: "Híbrido", on_site: "Presencial"};
const sponsors = {offered: "Com sponsor oferecido", not_needed: "Sem necessidade de sponsor"};
const contracts = {employee: "Empregado", contractor: "Prestador de serviço", self_employed: "Autônomo", other: "Outro"};
const scopes = {unspecified: "Não informado", local: "Local", national: "Nacional", international: "Internacional", selected_regions: "Regiões selecionadas"};
const boolOptions = {"": "Não informado", true: "Sim", false: "Não"};
const fieldNames = {preferences:"Preferências",current_location:"Localização atual",country:"País",region:"Região",city:"Cidade",commute_radius_km:"Raio de deslocamento",pathways:"Caminhos",label:"Nome",work_countries:"Países onde trabalhar",work_arrangements:"Modalidade",sponsorship:"Sponsor",contracts:"Vínculo",relocation_allowed:"Mudança",relocation_conditions:"Condições de mudança",compensation:"Remuneração",minimum:"Valor mínimo",career_roles:"Cargos",domains:"Áreas",employer_countries:"País do empregador",accepted_currencies:"Moedas",values:"Valores",mode:"Importância"};
function validationError(error) {
  const path = error.loc.slice(1).map(part => typeof part === "number" ? String(part + 1) : fieldNames[part] || part).join(" → ");
  const explanations = {"A required/preferred criterion needs at least one value":"Escolha pelo menos um valor para o critério obrigatório ou preferencial.","Country is required when supplying local location details":"Informe o país quando preencher cidade, região ou deslocamento.","Commute radius requires a city":"Informe a cidade para definir o raio de deslocamento.","Relocation conditions require relocation_allowed=true":"Selecione Sim em Aceita mudança para informar suas condições.","Compensation criterion requires currencies or minimum":"Informe moedas ou valor mínimo para a preferência de remuneração.","Specify advertised versus actual payment currency":"Escolha se a moeda se refere ao valor anunciado ou ao pagamento efetivo.","Minimum requires exactly one currency, period and gross/net basis":"O valor mínimo exige uma moeda, período e base bruta, líquida ou desconhecida."};
  const detail = explanations[error.msg.replace(/^Value error, /, "")] || (error.type === "string_pattern_mismatch" ? "Confira o formato: país com duas letras e moeda com três letras." : "Confira o valor informado e os limites deste campo.");
  return path + ": " + detail;
}
const state = {owner: null, profile: null, dirty: false, busy: false, profiles: [], pathways: [], history: []};
let locationControl, interestControls;
function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function message(text, kind = "success") {
  $("status").textContent = text; $("status").className = kind; $("status").hidden = false;
  $("status").scrollIntoView({block: "nearest"});
}
async function api(path, method = "GET", data) {
  let response;
  try { response = await fetch(path, {method, headers: data ? {"Content-Type": "application/json"} : {}, body: data ? JSON.stringify(data) : undefined}); }
  catch { throw new Error("Não foi possível conectar. Confira se os containers estão rodando e tente novamente."); }
  if (!response.ok) {
    let body; try { body = await response.json(); } catch { body = {}; }
    const error = new Error(response.status === 409 ? "O perfil mudou em outra aba. Seus campos foram mantidos aqui. Recarregue a versão salva antes de editar novamente." : response.status === 404 ? "Este espaço ou perfil não foi encontrado. Confira o identificador informado." : response.status === 422 ? "Revise os campos:\n" + (Array.isArray(body.detail) ? body.detail.map(validationError).join("\n") : "Dados inválidos.") : "Não foi possível concluir a operação (" + response.status + ").");
    error.status = response.status; throw error;
  }
  return response.json();
}
async function run(action) {
  if (state.busy) return;
  state.busy = true; document.querySelector("main").inert = true;
  try { await action(); } catch (error) { message(error.message, "error"); }
  finally { state.busy = false; document.querySelector("main").inert = false; }
}
function discard() { return !state.dirty || window.confirm("Há alterações não salvas. Deseja descartá-las?"); }
function markDirty() { state.dirty = true; $("save-note").textContent = "Alterações ainda não salvas"; }
function field(parent, label, value = "", options = {}) {
  const wrapper = node("div", undefined, "field");
  const id = "field-" + crypto.randomUUID();
  const caption = node("label", label); caption.htmlFor = id;
  const input = node(options.select ? "select" : options.multiline ? "textarea" : "input");
  input.id = id;
  if (options.select) Object.entries(options.select).forEach(([key, title]) => { const option = node("option", title); option.value = key; input.append(option); });
  else { if (!options.multiline) input.type = options.type || "text"; input.maxLength = options.maxLength || 200; }
  if (options.min !== undefined) input.min = options.min;
  if (options.max !== undefined) input.max = options.max;
  if (options.pattern) input.pattern = options.pattern;
  if (options.placeholder) input.placeholder = options.placeholder;
  if (options.multiline) input.rows = 3;
  input.value = value ?? "";
  input.addEventListener("input", markDirty);
  wrapper.append(caption, input); parent.append(wrapper); return input;
}
function location(parent, value = {}) {
  const country = field(parent, "País (duas letras)", value.country, {pattern: "[A-Za-z]{2}", maxLength: 2});
  const region = field(parent, "Estado ou região", value.region);
  const city = field(parent, "Cidade", value.city);
  const radius = field(parent, "Raio de deslocamento (km)", value.commute_radius_km, {type: "number", min: 0, max: 1000});
  return () => ({country: country.value.trim().toUpperCase() || null, region: region.value.trim() || null, city: city.value.trim() || null, commute_radius_km: radius.value === "" ? null : Number(radius.value)});
}
function criterion(parent, title, value = {}, options = null, codes = false) {
  const box = node("div", undefined, "criterion"); const row = node("div", undefined, "criterion-fields"); box.append(row); parent.append(box);
  const mode = field(row, title + " · importância", value.mode || "unspecified", {select: modes});
  let input, checks = [];
  if (options) {
    const group = node("fieldset", undefined, "choices"); group.append(node("legend", title));
    Object.entries(options).forEach(([key, text]) => {const label = node("label"); const check = node("input"); check.type = "checkbox"; check.value = key; check.checked = (value.values || []).includes(key); check.addEventListener("change", markDirty); label.append(check, document.createTextNode(text)); group.append(label); checks.push(check);});
    row.append(group);
  } else input = field(row, codes ? title + " · códigos separados por vírgula" : title + " · um por linha", (value.values || []).join(codes ? ", " : "\n"), {multiline: !codes, maxLength: 20100});
  function sync() { const inactive = ["unspecified", "unrestricted"].includes(mode.value); if (input) input.disabled = inactive; checks.forEach(c => c.disabled = inactive); }
  mode.addEventListener("change", sync); sync();
  return () => {
    const active = ["required", "preferred"].includes(mode.value);
    const values = !active ? [] : input ? input.value.split(codes ? /[,;\n]/ : /\n/).map(s => codes ? s.trim().toUpperCase() : s.trim()).filter(Boolean) : checks.filter(c => c.checked).map(c => c.value);
    return {mode: mode.value, values: [...new Set(values)]};
  };
}
function compensation(parent, value = {}) {
  const grid = node("div", undefined, "grid"); parent.append(grid);
  const mode = field(grid, "Remuneração · importância", value.mode || "unspecified", {select: modes});
  const currencies = field(grid, "Moedas aceitas (três letras, por vírgula)", (value.accepted_currencies || []).join(", "));
  const basis = field(grid, "A moeda se refere a", value.currency_basis, {select: {"": "Não informado", advertised: "Valor anunciado", actual_payment: "Pagamento efetivo"}});
  // Monetary values stay strings; do not convert through floating point.
  const minimum = field(grid, "Valor mínimo (opcional, use ponto decimal)", value.minimum, {pattern: "[0-9]+([.][0-9]+)?", maxLength: 100});
  const period = field(grid, "Período do valor", value.period, {select: {"": "Não informado", hour: "Hora", month: "Mês", year: "Ano"}});
  const amount = field(grid, "Base do valor", value.amount_basis, {select: {"": "Não informado", gross: "Bruto", net: "Líquido", unknown: "Desconhecida"}});
  const inputs = [currencies, basis, minimum, period, amount];
  function sync() { inputs.forEach(input => input.disabled = ["unspecified", "unrestricted"].includes(mode.value)); }
  mode.addEventListener("change", sync); sync();
  parent.append(node("p", "Valor mínimo exige uma moeda, período e base. Não há conversão de moedas.", "hint"));
  return () => ["unspecified", "unrestricted"].includes(mode.value) ? {mode: mode.value, accepted_currencies: [], currency_basis: null, minimum: null, period: null, amount_basis: null} : {mode: mode.value, accepted_currencies: [...new Set(currencies.value.split(/[,;\n]/).map(s => s.trim().toUpperCase()).filter(Boolean))], currency_basis: basis.value || null, minimum: minimum.value.trim() || null, period: period.value || null, amount_basis: amount.value || null};
}
function renderPathway(raw) {
  const card = node("div", undefined, "pathway"); const header = node("div", undefined, "pathway-header"); header.append(node("strong", "Alternativa de busca"));
  const remove = node("button", "Remover caminho", "text-button remove"); remove.type = "button"; header.append(remove); card.append(header);
  const grid = node("div", undefined, "grid"); card.append(grid);
  const label = field(grid, "Nome do caminho", raw.label); label.required = true;
  const scope = field(grid, "Abrangência da busca", raw.search_scope || "unspecified", {select: scopes});
  const countries = criterion(card, "Países onde trabalhar", raw.work_countries, null, true);
  const work = criterion(card, "Modalidade de trabalho", raw.work_arrangements, arrangements);
  const mobility = node("div", undefined, "grid"); card.append(mobility);
  const relocation = field(mobility, "Aceita mudança?", raw.relocation_allowed === null || raw.relocation_allowed === undefined ? "" : String(raw.relocation_allowed), {select: boolOptions});
  const travel = field(mobility, "Aceita viagens?", raw.travel_allowed === null || raw.travel_allowed === undefined ? "" : String(raw.travel_allowed), {select: boolOptions});
  const conditions = field(card, "Condições para mudança (opcional)", raw.relocation_conditions);
  const sponsor = criterion(card, "Sponsor", raw.sponsorship, sponsors);
  const contract = criterion(card, "Tipo de vínculo", raw.contracts, contracts);
  const destination = node("details"); destination.append(node("summary", "Localidade específica do caminho")); const destinationGrid = node("div", undefined, "grid"); destination.append(destinationGrid); card.append(destination);
  const destinationLocation = location(destinationGrid, raw.location);
  const salary = node("details"); salary.append(node("summary", "Preferências de remuneração")); card.append(salary);
  const pay = compensation(salary, raw.compensation);
  if ((raw.authorizations || []).length) card.append(node("p", "Declarações de autorização de trabalho já salvas serão preservadas. A edição dessas declarações ainda é feita pela API.", "hint"));
  const control = {card, read: () => ({...clone(raw), label: label.value.trim(), search_scope: scope.value, location: destinationLocation(), work_countries: countries(), work_arrangements: work(), relocation_allowed: relocation.value === "" ? null : relocation.value === "true", relocation_conditions: conditions.value.trim() || null, travel_allowed: travel.value === "" ? null : travel.value === "true", sponsorship: sponsor(), contracts: contract(), compensation: pay()})};
  remove.addEventListener("click", () => { if (!window.confirm("Remover este caminho do formulário? A versão anterior continuará no histórico após salvar.")) return; state.pathways = state.pathways.filter(c => c !== control); card.remove(); markDirty(); });
  state.pathways.push(control); $("pathways").append(card);
}
function editor(profile = null) {
  state.profile = profile ? clone(profile) : null; state.pathways = []; state.dirty = false;
  $("welcome").hidden = true; $("profile-form").hidden = false; $("history-panel").hidden = !profile; $("reload-profile").hidden = !profile;
  $("editor-title").textContent = profile ? "Editar perfil" : "Novo perfil";
  $("version").textContent = profile ? "Versão " + profile.latest.version : "Ainda não salvo";
  $("profile-label").value = profile?.label || ""; $("save-note").textContent = profile ? "Versão salva carregada" : "Preencha e salve seu perfil";
  const prefs = profile?.latest.preferences || {};
  $("current-location").replaceChildren(); locationControl = location($("current-location"), prefs.current_location);
  $("interests").replaceChildren(); interestControls = {employer_countries: criterion($("interests"), "País do empregador", prefs.employer_countries, null, true), career_roles: criterion($("interests"), "Cargos de interesse", prefs.career_roles), domains: criterion($("interests"), "Áreas de interesse", prefs.domains)};
  $("pathways").replaceChildren(); (prefs.pathways || []).forEach(renderPathway);
  if ((prefs.skill_evidence || []).length) $("interests").append(node("p", "Habilidades e suas fontes já cadastradas serão preservadas; sua edição ainda é feita pela API.", "hint"));
  renderProfiles();
}
function payload() {
  const prefs = clone(state.profile?.latest.preferences || {});
  prefs.current_location = locationControl(); Object.entries(interestControls).forEach(([key, read]) => prefs[key] = read()); prefs.pathways = state.pathways.map(c => c.read());
  return {label: $("profile-label").value.trim(), preferences: prefs, ...(state.profile ? {expected_version: state.profile.latest.version} : {})};
}
function renderProfiles() {
  $("profile-list").replaceChildren();
  if (!state.profiles.length) $("profile-list").append(node("p", "Nenhum perfil salvo neste espaço. Clique em + Novo.", "empty"));
  state.profiles.forEach(profile => { const button = node("button", profile.label, "profile-item" + (profile.id === state.profile?.id ? " selected" : "")); button.type = "button"; button.append(node("small", "Versão " + profile.latest.version)); button.addEventListener("click", () => run(async () => { if (!discard()) return; const saved = await api(profileUrl(profile.id)); editor(saved); await history(); })); $("profile-list").append(button); });
}
function profileUrl(id = state.profile?.id) { return "/career/owners/" + state.owner + "/profiles" + (id ? "/" + id : ""); }
function rememberOwner(id) { try { localStorage.setItem("career-owner-id", id); } catch { message("Espaço aberto. O navegador não permite lembrar o identificador; guarde-o manualmente.", "warning"); } }
async function connect(id) {
  if (!/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(id)) throw new Error("Cole um identificador completo no formato retornado ao criar o proprietário.");
  const profiles = await api("/career/owners/" + id + "/profiles?limit=100&offset=0");
  state.owner = id; state.profiles = profiles; rememberOwner(id); $("owner-id").value = id; $("new-profile").disabled = false; $("more-profiles").hidden = profiles.length < 100;
  editor(profiles[0] || null); message("Espaço aberto. Guarde o identificador para acessar em outro navegador.");
  if (state.profile) await history();
}
function friendlyChoice(choice, labels = {}) { if (!choice || ["unspecified", "unrestricted"].includes(choice.mode)) return modes[choice?.mode || "unspecified"]; return modes[choice.mode] + ": " + choice.values.map(v => labels[v] || v).join(", "); }
function locationText(value) { return [value?.city, value?.region, value?.country].filter(Boolean).join(" · ") || "Não informada"; }
function renderHistory() {
  $("history-list").replaceChildren();
  state.history.forEach(version => {
    const details = node("details", undefined, "history-entry"); const summary = node("summary", "Versão " + version.version + " · " + locationText(version.preferences.current_location)); summary.append(node("span", new Date(version.created_at).toLocaleString("pt-BR"))); details.append(summary);
    const prefs = version.preferences; const dl = node("dl");
    const pair = (name, value) => dl.append(node("dt", name), node("dd", value));
    pair("Localização atual", locationText(prefs.current_location)); pair("País do empregador", friendlyChoice(prefs.employer_countries)); pair("Cargos", friendlyChoice(prefs.career_roles)); pair("Áreas", friendlyChoice(prefs.domains));
    details.append(dl);
    if (!prefs.pathways.length) details.append(node("p", "Nenhum caminho informado.", "hint"));
    prefs.pathways.forEach(path => {
      const box = node("div", undefined, "history-path");
      box.append(node("strong", path.label), node("p", "Busca: " + scopes[path.search_scope] + ". Países: " + friendlyChoice(path.work_countries) + ". Modalidade: " + friendlyChoice(path.work_arrangements, arrangements) + "."), node("p", "Mudança: " + boolOptions[path.relocation_allowed === null ? "" : String(path.relocation_allowed)] + ". Sponsor: " + friendlyChoice(path.sponsorship, sponsors) + ". Vínculo: " + friendlyChoice(path.contracts, contracts) + "."));
      box.append(node("p", "Localidade do caminho: " + locationText(path.location) + ". Viagens: " + boolOptions[path.travel_allowed === null ? "" : String(path.travel_allowed)] + "."));
      if (path.relocation_conditions) box.append(node("p", "Condições de mudança: " + path.relocation_conditions));
      const pay = path.compensation;
      const payText = [modes[pay.mode], pay.accepted_currencies.join(", "), pay.currency_basis === "actual_payment" ? "pagamento efetivo" : pay.currency_basis === "advertised" ? "valor anunciado" : "", pay.minimum === null ? "" : "mínimo " + pay.minimum, {hour:"por hora",month:"por mês",year:"por ano"}[pay.period], {gross:"bruto",net:"líquido",unknown:"base desconhecida"}[pay.amount_basis]].filter(Boolean).join(" · ");
      box.append(node("p", "Remuneração: " + payText));
      (path.authorizations || []).forEach(auth => box.append(node("p", "Autorização declarada: " + auth.country + " · " + {authorized:"autorizado",requires_sponsorship:"necessita sponsor",unknown:"desconhecida"}[auth.status])));
      details.append(box);
    });
    prefs.skill_evidence.forEach(skill => details.append(node("p", "Habilidade declarada: " + skill.skill + (skill.experience_years === null ? "" : " · " + skill.experience_years + " anos") + " · Fonte: " + skill.provenance, "hint")));
    $("history-list").append(details);
  });
}
async function history(more = false) {
  if (!state.profile) return;
  const rows = await api(profileUrl() + "/versions?limit=100&offset=" + (more ? state.history.length : 0));
  state.history = more ? [...state.history, ...rows] : rows; renderHistory(); $("more-history").hidden = rows.length < 100;
}
$("connect-form").addEventListener("submit", event => { event.preventDefault(); run(async () => { if (discard()) await connect($("owner-id").value.trim()); }); });
$("owner-form").addEventListener("submit", event => { event.preventDefault(); run(async () => { if (!discard()) return; const owner = await api("/career/owners", "POST", {label: $("owner-label").value.trim() || null}); $("owner-id").value = owner.id; rememberOwner(owner.id); await connect(owner.id); $("owner-create").open = false; message("Espaço criado. Seu identificador está na coluna ao lado. Agora cadastre seu primeiro perfil."); }); });
$("new-profile").addEventListener("click", () => { if (discard()) { editor(); $("profile-label").focus(); } });
$("add-pathway").addEventListener("click", () => { if (state.pathways.length >= 20) return message("Cada perfil aceita até 20 caminhos.", "warning"); renderPathway({id: crypto.randomUUID(), label: ""}); markDirty(); });
$("profile-label").addEventListener("input", markDirty);
$("profile-form").addEventListener("submit", event => {
  event.preventDefault();
  if (!$("profile-form").checkValidity()) {
    const invalid = $("profile-form").querySelector(":invalid");
    let parent = invalid?.parentElement;
    while (parent && parent !== $("profile-form")) { if (parent.tagName === "DETAILS") parent.open = true; parent = parent.parentElement; }
    $("profile-form").reportValidity(); return;
  }
  run(async () => {
  if (!state.owner) throw new Error("Abra um espaço antes de salvar.");
  const data = payload(); const editing = Boolean(state.profile);
  const saved = await api(profileUrl(), editing ? "PUT" : "POST", data);
  const index = state.profiles.findIndex(p => p.id === saved.id); if (index < 0) state.profiles.push(saved); else state.profiles[index] = saved;
  editor(saved); message("Perfil salvo. Versão " + saved.latest.version + " registrada no banco local.");
  try { await history(); } catch { message("Perfil salvo, mas o histórico não carregou. Clique em Atualizar histórico para tentar novamente.", "warning"); }
}); });
$("reload-profile").addEventListener("click", () => run(async () => { if (discard()) { editor(await api(profileUrl())); await history(); message("Versão salva recarregada."); } }));
$("refresh-history").addEventListener("click", () => run(() => history()));
$("more-history").addEventListener("click", () => run(() => history(true)));
$("more-profiles").addEventListener("click", () => run(async () => { const rows = await api(profileUrl(null) + "?limit=100&offset=" + state.profiles.length); state.profiles.push(...rows); renderProfiles(); $("more-profiles").hidden = rows.length < 100; }));
window.addEventListener("beforeunload", event => { if (state.dirty) { event.preventDefault(); event.returnValue = ""; } });
let remembered; try { remembered = localStorage.getItem("career-owner-id"); } catch { /* Manual identifier entry remains available. */ }
if (remembered) { $("owner-id").value = remembered; run(() => connect(remembered)); }
