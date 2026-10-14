# Manual job captures / Capturas manuais de vagas

## English

This stage stores manual evidence only: a user-supplied label, exact text received by the API, optional HTTP/HTTPS source URL, user-declared URL association and optional timezone-aware source consultation time. Import time is recorded separately. No scraper, AI extraction, scoring, market analysis or default career role is included. A saved URL does not prove that a job is active or that its content matches the text.

### Install and verify

From the project directory, with Docker Desktop running:

```powershell
.\verify-jobs.ps1
```

The script builds the API, applies Alembic migrations (including `0002_job_captures`) to the existing database and starts the services. It runs profile and job API tests in a generated disposable `career_profile_test_*` PostgreSQL database. It saves synthetic profiles and job captures, restarts this project's database and API, checks both histories and removes only the disposable database. Existing application data and the named volume are retained. Restart briefly interrupts the local service. Do not run verification scripts concurrently.

On October 9, 2026, the script completed on the local PostgreSQL installation: all 18 profile and job tests passed, including concurrent edits and owner scoping. Synthetic profile preferences and job text, provenance and history survived a database/API container restart. Both services were healthy afterward, and `DROP DATABASE` confirmed removal of the disposable test database. These results describe the tested local installation; run the script to validate another installation.

### Screen

Open `http://127.0.0.1:8000/jobs`. The last remembered profile workspace opens automatically. If none is remembered, enter its ID and choose **Abrir minhas vagas**. Choose **+ Nova vaga**, enter a label, paste the description and optionally supply a source URL. Check the association box only if you confirm that the pasted text belongs to that URL. Leave consultation time empty if unknown. Save, then select a saved job and save another capture to preserve its earlier version. A history entry opens its original text in a read-only field. More results can be loaded in pages of 20.

### Compare saved captures

Open an earlier entry in the capture history. **O que mudou** compares that entry against the most recent capture loaded for the selected job. It shows the previous and current source URLs when different, or states that the URL is unchanged. Changed descriptions appear as **Antes / Depois**, highlighting the range from the first to the last differing character. That range can contain unchanged text between separate edits; this is not a word-by-word or semantic analysis. Identical descriptions are reported as unchanged.

Only saved text is compared. Unsaved form edits are excluded, and viewing a comparison creates no new capture. Reopen the job to load updates saved in another browser. The comparison does not verify the source URL or interpret job requirements.

Browser verification on October 9, 2026 confirmed that a fictional job's two saved descriptions remained readable and that the changed requirement was highlighted correctly. The unchanged-URL state was checked; a changed URL has not yet been tested in the browser.

### Isolated regression checks

From the project directory:

```powershell
# Requires Node.js; compares text without accessing Docker or the database.
node tests/test_job_comparison.cjs
# Requires PowerShell 7 (pwsh); mocks Docker and HTTP in a temporary directory.
pwsh -NoProfile -File tests/test_verify_report.ps1
```

All 10 text-comparison cases passed, covering insertion, deletion, identical text, whitespace, line endings, Unicode and long input. All six verification-report scenarios passed, including a previous successful report followed by missing `.env`, Compose/HTTP failures, probe mismatch, final `compose ps` failure and success. The mocked report tests leave the installation's `.env`, database and report untouched. These checks supplement the PostgreSQL verification; they do not replace it. Node.js is needed only for the isolated comparison check, not to run the application.

Browser textareas may normalize line endings during paste or editing. The API preserves received text exactly, including whitespace, accents and CRLF/LF, and calculates SHA-256 over its UTF-8 bytes. The hash identifies content, not its truth. Duplicate text is allowed; it is never silently merged. Re-saving unchanged input explicitly creates a new capture. Raw text is limited to 100,000 characters and NUL is rejected for PostgreSQL compatibility. The label is for organization, not an extracted job title. URL confirmation is a user declaration. There is no automatic source association or fetch.

Owner IDs delimit records but are not authentication. Keep the service on localhost. Raw vacancy text and user records belong in the local database, never in Git. History is append-only through this API; database administrators can still alter records. A concurrent edit returns 409, preserves the unsaved form and requires reloading before another save.

### API and storage

Prefix: `/career/owners/{owner_id}/jobs`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | prefix | Create a source with capture 1 |
| GET | prefix | Paginated summaries, without original text |
| GET | prefix + `/{source_id}` | Latest full capture |
| POST | prefix + `/{source_id}/snapshots` | Append capture; requires `expected_version` |
| GET | prefix + `/{source_id}/snapshots` | Paginated capture summaries |
| GET | prefix + `/{source_id}/snapshots/{version}` | Read original text of a specific capture |

`career.job_sources` stores stable owner-qualified identities; `career.job_snapshots` stores sequential captures, labels, URLs, association flags, original text, hash and timestamps. URLs are versioned in snapshots so changing a reference cannot overwrite old provenance. Composite foreign keys prevent references to another owner's source. A short source-row lock and expected-version check protect concurrent appends. Existing profile tables remain intact. External posting IDs, language detection and extracted claims are deferred.

## Português

Esta etapa guarda evidências informadas manualmente: nome para organizar, texto recebido pela API, link HTTP/HTTPS opcional, associação declarada pelo usuário e horário opcional da consulta à fonte, com fuso. A data do cadastro é registrada separadamente. Não há coleta automática, extração com IA, pontuação, análise de mercado ou cargo fixo. O link salvo não comprova que a vaga está aberta ou que corresponde ao texto.

### Instalar e verificar

Na pasta do projeto, com o Docker Desktop aberto:

```powershell
.\verify-jobs.ps1
```

O script constrói a API, aplica as migrations (incluindo `0002_job_captures`) ao banco existente e inicia os serviços. Executa testes de perfis e vagas em um banco PostgreSQL descartável `career_profile_test_*`, grava dados fictícios, reinicia o banco e a API deste projeto, confere os dois históricos e remove somente o banco de testes. Preserva os dados existentes e o volume. O restart interrompe brevemente o serviço local. Não execute scripts de verificação simultaneamente.

Em 9 de outubro de 2026, o script concluiu na instalação PostgreSQL local: os 18 testes de perfis e vagas passaram, incluindo edições simultâneas e delimitação por proprietário. As preferências dos perfis e o texto, a origem e o histórico das vagas fictícias sobreviveram ao restart do banco e da API. Os dois serviços ficaram saudáveis e `DROP DATABASE` confirmou a remoção do banco descartável. Esses resultados descrevem a instalação testada; execute o script para validar outra instalação.

### Usar

Abra `http://127.0.0.1:8000/jobs`. O último espaço lembrado da tela de perfis abre automaticamente. Se nenhum estiver lembrado, informe seu identificador e clique em **Abrir minhas vagas**. Clique em **+ Nova vaga**, preencha um nome, cole a descrição e, opcionalmente, informe a URL. Marque a confirmação apenas quando souber que o texto corresponde ao link. Deixe o horário da consulta vazio se desconhecido. Salve. Para registrar mudanças na mesma vaga, selecione-a e use **Salvar nova captura**. Clique em uma entrada do histórico para ler o texto daquela captura. Listas são paginadas em grupos de 20.

### Comparar capturas salvas

Abra uma entrada anterior no histórico. **O que mudou** compara essa entrada com a captura mais recente carregada da vaga selecionada. Links diferentes são mostrados como anterior e mais recente; links iguais aparecem como sem alteração. Descrições diferentes aparecem em **Antes / Depois**, com destaque do primeiro ao último caractere diferente. O trecho pode incluir partes iguais entre mudanças separadas; não é uma análise palavra por palavra nem uma interpretação dos requisitos. Descrições idênticas aparecem como sem alteração.

A comparação usa somente textos salvos. Alterações ainda não salvas no formulário ficam fora dela e a consulta não cria outra captura. Reabra a vaga para carregar atualizações feitas em outro navegador. A comparação não verifica a página de origem.

Na conferência pelo navegador em 9 de outubro de 2026, os dois textos da vaga fictícia permaneceram legíveis e a mudança de requisito apareceu destacada. O estado de link sem alteração foi conferido; uma mudança de link ainda não foi testada no navegador.

### Testes isolados de regressão

Na pasta do projeto:

```powershell
# Exige Node.js; compara textos sem acessar Docker ou banco.
node tests/test_job_comparison.cjs
# Exige PowerShell 7 (pwsh); simula Docker e HTTP em pasta temporária.
pwsh -NoProfile -File tests/test_verify_report.ps1
```

Os 10 casos de comparação passaram, cobrindo inserção, exclusão, texto idêntico, espaços, quebras de linha, Unicode e entradas longas. Os seis cenários de relatório passaram, incluindo sucesso anterior seguido de `.env` ausente, falhas de Compose/HTTP, registro de persistência divergente, falha no `compose ps` final e sucesso. Os testes simulados preservam o `.env`, o banco e o relatório da instalação. Complementam a verificação PostgreSQL, sem substituí-la. Node.js é necessário apenas para o teste isolado de comparação, não para executar a aplicação.

O navegador pode padronizar quebras de linha ao colar ou editar. A API preserva exatamente o texto recebido e calcula SHA-256 sobre os bytes UTF-8; esse hash identifica conteúdo, não comprova sua veracidade. O limite é 100.000 caracteres e o caractere NUL é rejeitado. Textos repetidos são permitidos, sem mesclagem automática. Salvar novamente cria uma nova captura, mesmo sem alteração. O nome não é um título extraído. A confirmação do link é uma declaração sua; nenhuma página é consultada.

Os IDs delimitam registros e não autenticam pessoas. Use em localhost. Dados e textos de vagas ficam no banco local, nunca no Git. O histórico não pode ser sobrescrito por esta API, embora administradores do banco possam alterar registros. Em edição simultânea, o erro 409 mantém o formulário e exige recarregar antes de salvar.

As rotas estão na tabela em inglês e em `/docs`, na seção **Local job captures (no authentication)**. `job_sources` guarda a identidade da fonte; `job_snapshots` guarda texto, URL e metadados de cada captura. A URL também é versionada para preservar a origem antiga. As chaves incluem o proprietário e impedem referências entre espaços. Os perfis existentes permanecem intactos. Identificador externo da vaga, detecção de idioma e extração ficam para depois.
