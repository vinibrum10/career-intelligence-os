# Job facts, eligibility comparison and AI draft / Fatos da vaga, comparação de elegibilidade e rascunho por IA

## English

Everything here works on a saved capture (`/career/owners/{owner_id}/jobs/{source_id}/snapshots/{version}`) and uses the prefix `…/extractions`. Nothing is saved automatically: a person reviews and saves. Owner IDs delimit records but are not authentication; keep the service on localhost.

| Method | Path (after the prefix) | Purpose |
| --- | --- | --- |
| POST | `/draft` | AI draft of claims from the capture text. Saves nothing |
| POST | prefix | Save a reviewed set of claims as a new extraction run |
| GET | prefix, `/{extraction_id}` | List or read saved runs |
| GET | `/{extraction_id}/comparison?profile_id=&profile_version=` | Read-only comparison of the run against one saved profile version |

### Claims

A claim is one fact about the vacancy: `field_key` (`work_arrangement`, `work_countries`, `sponsorship`, `authorization_restriction`, `contract`, `working_time`, `compensation`, `skill_group`), `knowledge` and a normalised `value`.

- `explicit`: needs at least one evidence excerpt that equals `original_text[start_char:end_char]` (zero-based Unicode characters, end exclusive).
- `inferred`: needs a `basis`. The comparison never treats it as proof.
- `not_provided`: records that the field was inspected and the text says nothing. No value, evidence, requirement or basis.

Runs are append-only: a correction is a new run, never an edit. The database repeats these rules in CHECK constraints.

### Eligibility comparison (`rules-v1`)

Only `required` profile criteria decide. `preferred` ones are reported but never eliminate. Pathways are alternatives: any compatible pathway makes the result compatible; all incompatible makes it incompatible; anything else needs confirmation. Only explicit, non-conflicting claims prove a fact; inferred, missing or conflicting facts ask for confirmation. A remote job without a `work_countries` claim is never assumed worldwide. Compensation is compared only when currency, period, amount basis and currency basis match (no conversions). Technical fit is always `not_assessed`.

### AI draft

`POST …/extractions/draft` sends **only the vacancy text** (never a profile) to a local Ollama model and returns `extractor`, `claims` and `discarded`. The model proposes only `explicit` and `not_provided` claims and quotes an excerpt; the code finds the offsets in the saved text and discards a candidate whose excerpt is absent or appears more than once, whose value does not fit the vocabulary, whose field is unknown or whose knowledge is `inferred`. Each discard is listed with its reason. Texts above 12,000 characters are refused. A model failure returns 502 and stores nothing.

Review the draft, edit or remove claims, then send `extractor` and `claims` to the extractions POST. The default extractor label is `ollama-qwen3:8b+reviewed`.

Settings (environment variables of the `api` service, optional): `OLLAMA_URL` (default `http://host.docker.internal:11434`) and `OLLAMA_MODEL` (default `qwen3:8b`). Ollama runs on Windows; the container reaches it through `host.docker.internal`.

```powershell
# List saved jobs (take owner_id and the job id)
Invoke-RestMethod "http://127.0.0.1:8000/career/owners/<owner_id>/jobs" | ConvertTo-Json -Depth 5
# Ask for a draft of capture 1 (the first call may take a minute while the model loads)
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/career/owners/<owner_id>/jobs/<source_id>/snapshots/1/extractions/draft" | ConvertTo-Json -Depth 10
```

The model is adopted only after a check on real vacancies that you label by hand; measure how many proposed claims are wrong or invented, and change the model if that rate is not low. `verify-jobs.ps1` tests the draft with simulated model answers; it does not call Ollama.

## Português

Tudo aqui trabalha sobre uma captura salva e usa o prefixo `…/extractions`. Nada é salvo automaticamente: uma pessoa revisa e salva. Os IDs de proprietário delimitam registros, mas não são autenticação; mantenha o serviço em localhost.

- **Claims:** cada fato da vaga tem `field_key`, `knowledge` (`explicit`, `inferred`, `not_provided`) e valor normalizado. Um claim `explicit` exige trecho idêntico ao texto salvo, com posições em caracteres Unicode. Claims são acrescentados em novas execuções, nunca editados.
- **Comparação (`rules-v1`):** só critérios `required` do perfil decidem; `preferred` são apenas informados. Caminhos do perfil são alternativas. Só fatos explícitos e sem conflito provam algo; o resto pede confirmação. Compensação só é comparada com mesma moeda, período e base, sem conversão. Aderência técnica fica sempre `not_assessed`.
- **Rascunho por IA:** `POST …/extractions/draft` envia **somente o texto da vaga** (nunca o perfil) ao Ollama local e devolve claims candidatos. O código localiza o trecho no texto salvo e descarta candidatos com trecho inexistente ou repetido, valor fora do vocabulário, campo desconhecido ou conhecimento `inferred`, listando o motivo. O rascunho não grava nada; revise e envie `extractor` e `claims` ao POST de extrações. Variáveis opcionais do serviço `api`: `OLLAMA_URL` e `OLLAMA_MODEL`. O modelo só é adotado depois de avaliar vagas reais rotuladas por você; o `verify-jobs.ps1` testa o rascunho com respostas simuladas e não chama o Ollama.
