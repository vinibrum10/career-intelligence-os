# Job facts, eligibility comparison and AI draft / Fatos da vaga, comparação de elegibilidade e rascunho por IA

## English

### Compare from the job screen

Open your workspace at `/jobs` and choose a saved job from the central list or sidebar. Opening a job automatically loads its facts and profiles; choose a profile and **Comparar elegibilidade**. Use **Atualizar fatos e perfis** to refresh. Criterion details explain the job and profile values in Portuguese, with the original evidence.

At `/jobs`, save or open a job, then choose **Continuar: revisar fatos da vaga**. The latest saved capture is available immediately; use the history for an earlier capture. Step 1 lets you add facts manually or request a draft from the Ollama Cloud service. Each explicit fact needs a value and an exact excerpt appearing once in the saved text. Missing information can be marked **Não informado na descrição**. Review, correct or remove suggestions, check the confirmation and choose **Salvar fatos revisados**. This creates a new extraction run without changing earlier runs. Editing a fact clears the review confirmation; leaving an unfinished review asks before discarding it. If the model is unavailable, the review is preserved and manual entry remains available.

After saving facts, step 2 loads profiles and selects the newly saved run. Choose a profile and **Comparar elegibilidade**. **Atualizar fatos e perfis** also loads existing runs and refreshes profile versions. Both lists support pagination. The comparison uses the indicated capture, run and profile version; unsaved description edits are excluded. It shows alternative pathways, mandatory and preferred criteria, reasons and evidence. Comparisons themselves are not stored. Technical fit remains unassessed. Draft validation checks excerpts and vocabulary, not semantic correctness: human review is still required.

Everything here works on a saved capture (`/career/owners/{owner_id}/jobs/{source_id}/snapshots/{version}`) and uses the prefix `…/extractions`. Nothing is saved automatically: a person reviews and saves. Owner IDs delimit records but are not authentication; keep the service on localhost.

| Method | Path (after the prefix) | Purpose |
| --- | --- | --- |
| POST | `/draft` | AI draft of claims from the capture text. Saves nothing |
| POST | prefix | Save a reviewed set of claims as a new extraction run |
| GET | prefix, `/{extraction_id}` | List or read saved runs |
| GET | `/{extraction_id}/comparison?profile_id=&profile_version=` | Read-only comparison of the run against one saved profile version |

### Claims

A claim is one fact about the vacancy: `field_key` (`work_arrangement`, `work_countries`, `employer_countries`, `sponsorship`, `authorization_restriction`, `contract`, `working_time`, `compensation`, `skill_group`), `knowledge` and a normalised `value`.

- `explicit`: needs at least one evidence excerpt that equals `original_text[start_char:end_char]` (zero-based Unicode characters, end exclusive).
- `inferred`: needs a `basis`. The comparison never treats it as proof.
- `not_provided`: records that the field was inspected and the text says nothing. No value, evidence, requirement or basis.

Runs are append-only: a correction is a new run, never an edit. The API validates typed values and exact evidence slices; the database additionally enforces ownership, knowledge/value consistency, inference basis and evidence ranges.

`employer_countries` uses `{"countries": ["BR"]}` and means the explicitly stated country of the employer, not the work location. `contract` still accepts a single code such as `employee`. A single fact explicitly offering options, such as “CLT ou PJ”, uses `{"alternatives": ["employee", "contractor"]}` with evidence of the complete choice. Separate conflicting claims remain separate and unresolved. Existing saved facts are not rewritten; record a new reviewed extraction to group an old pair of claims as alternatives. These additions use the existing JSON storage and require no new migration beyond `0003_extractions`.

### Eligibility comparison (`rules-v2`)

Only `required` profile criteria decide. `preferred` ones are reported but never eliminate. Pathways are alternatives: any compatible pathway makes the result compatible; all incompatible makes it incompatible; anything else needs confirmation. Only explicit, non-conflicting claims prove a fact; inferred, missing or conflicting facts ask for confirmation. A remote job without a `work_countries` claim is never assumed worldwide. Compensation is compared only when currency, period, amount basis and currency basis match (no conversions). Technical fit is always `not_assessed`.

The global employer-country criterion is evaluated in every pathway. A required employer country without evidence needs confirmation; an explicit mismatch is incompatible. Preferred employer countries never eliminate. An explicit contract-options fact matches when at least one offered option is accepted; separate contradictory facts still need confirmation.

If a pathway contains authorization declarations, the rules evaluate them against explicit work countries. Required pathway countries narrow the alternatives; preferred countries do not. Each eligible country is evaluated separately: a self-declared authorization supports that route, a declaration requiring sponsorship depends on explicit sponsorship evidence, and unknown/missing declarations need confirmation. Any supported country suffices; all incompatible countries make this authorization check incompatible. Missing/conflicting work countries remain unresolved. An explicit lack of sponsorship conflicts with a relevant declaration requiring it. A profile that declares sponsorship required for that country but also configures only `not_needed` cannot become compatible just because sponsorship is offered: it needs profile review. These checks use self-declarations and are not legal verification.

This remains a partial comparison: city/region, relocation conditions, travel, career interests and skill evidence are not evaluated. No authorization declaration means this additional check is absent, not that permission to work has been verified. Free-text authorization restrictions in a vacancy still require review. Comparisons are read-only calculations against the requested saved versions and are not stored as historical results.

### AI draft

`POST …/extractions/draft` sends **only the vacancy text** (never a profile) to Ollama Cloud (`gemma4:31b`) and returns `extractor`, `claims` and `discarded`. The model proposes only `explicit` and `not_provided` claims and quotes an excerpt; the code finds the offsets in the saved text and discards a candidate whose excerpt is absent or appears more than once, whose value does not fit the vocabulary, whose field is unknown or whose knowledge is `inferred`. Each discard is listed with its reason. Texts above 12,000 characters are refused. Provider failures store nothing; authentication, credit and limit errors keep their specific status codes.

Review the draft, edit or remove claims, then send `extractor` and `claims` to the extractions POST. The default extractor label is `ollama-cloud-gemma4:31b+reviewed`.

The server calls `https://ollama.com` using `gemma4:31b` and a nonempty `OLLAMA_API_KEY`. No local Ollama installation is needed. See [configuration and real connection test](ollama-cloud.md).

```powershell
# List saved jobs (take owner_id and the job id)
Invoke-RestMethod "http://127.0.0.1:8000/career/owners/<owner_id>/jobs" | ConvertTo-Json -Depth 5
# Ask for a draft of capture 1 (the first call may take a minute while the model loads)
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/career/owners/<owner_id>/jobs/<source_id>/snapshots/1/extractions/draft" | ConvertTo-Json -Depth 10
```

The model is adopted only after a check on real vacancies that you label by hand; measure how many proposed claims are wrong or invented, and change the model if that rate is not low. `verify-jobs.ps1` tests the draft with simulated model answers; it does not call Ollama.

## Português

### Comparar pela tela de vagas

Abra seu espaço em `/jobs` e escolha uma vaga na lista central ou na lateral. Ao abrir a vaga, os fatos e os perfis são carregados automaticamente; escolha um perfil e clique em **Comparar elegibilidade**. Use **Atualizar fatos e perfis** para atualizar as listas. Cada critério mostra a justificativa em português, com os valores da vaga e do perfil e os trechos originais de evidência.

Em `/jobs`, salve ou abra uma vaga e clique em **Continuar: revisar fatos da vaga**. A captura mais recente já fica disponível; use o histórico para uma anterior. Na etapa 1, adicione fatos manualmente ou gere um rascunho pelo serviço Ollama Cloud. Cada fato explícito precisa de valor e trecho exato que apareça uma vez no texto salvo. Ausências podem ser marcadas como **Não informado na descrição**. Confira, corrija ou remova sugestões, marque a confirmação e clique em **Salvar fatos revisados**. Isso cria um novo conjunto sem alterar os anteriores. Editar um fato desmarca a confirmação; sair de uma revisão não salva pede confirmação de descarte. Se o modelo estiver indisponível, a revisão é preservada e o preenchimento manual continua disponível.

Depois de salvar os fatos, a etapa 2 carrega os perfis e seleciona o conjunto recém-salvo. Escolha o perfil e clique em **Comparar elegibilidade**. **Atualizar fatos e perfis** também consulta conjuntos existentes e atualiza versões de perfis. As duas listas permitem carregar mais resultados. A consulta usa a captura, os fatos e a versão do perfil indicados; alterações não salvas na descrição ficam de fora. Exibe caminhos alternativos, critérios obrigatórios e preferenciais, justificativas e evidências. A comparação em si não é armazenada. Aderência técnica permanece não avaliada. A validação do rascunho verifica trechos e vocabulário, mas não garante a interpretação correta: a revisão humana continua necessária.

Tudo aqui trabalha sobre uma captura salva e usa o prefixo `…/extractions`. Nada é salvo automaticamente: uma pessoa revisa e salva. Os IDs de proprietário delimitam registros, mas não são autenticação; mantenha o serviço em localhost.

- **Claims:** cada fato da vaga tem `field_key`, `knowledge` (`explicit`, `inferred`, `not_provided`) e valor normalizado. Um claim `explicit` exige trecho idêntico ao texto salvo, com posições em caracteres Unicode. Claims são acrescentados em novas execuções, nunca editados.
- **Comparação (`rules-v2`):** só critérios `required` do perfil decidem; `preferred` são apenas informados. Caminhos do perfil são alternativas. Só fatos explícitos e sem conflito provam algo; o resto pede confirmação. Compensação só é comparada com mesma moeda, período e base, sem conversão. Aderência técnica fica sempre `not_assessed`.
- **País da empresa:** `employer_countries` usa `{"countries": ["BR"]}` e é independente do local de trabalho. O critério global vale em todos os caminhos. Se obrigatório, ausência de evidência pede confirmação e conflito explícito é incompatível; se preferencial, não elimina.
- **Alternativas de contrato:** um fato com `{"alternatives": ["employee", "contractor"]}` e evidência de “CLT ou PJ” permite qualquer opção aceita pelo perfil. Fatos separados com valores divergentes continuam como conflito. Registros antigos não são reescritos; corrija a interpretação com uma nova extração revisada. Não há nova migration: os dados usam o JSON existente desde `0003_extractions`.
- **Declarações de autorização:** quando presentes no caminho, são cruzadas com os países de trabalho explícitos. Países obrigatórios do caminho restringem as alternativas; preferenciais não. Autorização declarada pode sustentar um caminho; necessidade declarada de patrocínio exige evidência de oferta. Ausência explícita de patrocínio contradiz essa necessidade. País ou declaração ausente, desconhecido ou conflitante pede confirmação. Um país compatível basta; todos incompatíveis tornam essa verificação incompatível. Declarar necessidade e configurar apenas `not_needed` exige revisão do perfil, mesmo se a vaga oferecer patrocínio. Não é verificação jurídica; sem declarações cadastradas, esse teste adicional não é feito.
- **Limites:** cidade/região, condições de mudança, viagens, interesses e evidências técnicas ainda não são avaliados. Restrições de autorização em texto livre continuam exigindo revisão. O resultado é calculado com as versões solicitadas, sem salvar um histórico de comparações.
- **Rascunho por IA:** `POST …/extractions/draft` envia **somente o texto da vaga** (nunca o perfil) ao Ollama Cloud (`gemma4:31b`) e devolve claims candidatos. O código localiza o trecho no texto salvo e descarta candidatos com trecho inexistente ou repetido, valor fora do vocabulário, campo desconhecido ou conhecimento `inferred`, listando o motivo. O rascunho não grava nada; revise e envie `extractor` e `claims` ao POST de extrações. O serviço `api` precisa de `OLLAMA_API_KEY`, somente no servidor. Veja [configuração e teste real](ollama-cloud.md). O modelo só é adotado depois de avaliar vagas reais rotuladas por você; o `verify-jobs.ps1` testa o rascunho com respostas simuladas e não chama o Ollama.
