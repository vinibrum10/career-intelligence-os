# Career Intelligence OS — Product Requirements

[English](#english) | [Português](#português)

## English

### 1. Purpose and current status

Help people compare career opportunities using traceable evidence and their own preferences. The product must support different profiles, countries, employment arrangements and career interests. No role, location, currency or personal preference may be hardcoded as a universal default.

The infrastructure V1 has been verified locally: an empty Agno/AgentOS runtime, PostgreSQL with pgvector, a persistent Docker volume, healthy services and a database record preserved after container restart. Agents, RAG, profile management and job analysis are not implemented yet. This document defines the next phase; it does not establish that these features already exist or authorize their implementation.

### 2. Configurable profiles

Each user must be able to configure and update:

| Group | Fields |
|---|---|
| Current location | Country, state/region and city; optional commute area |
| Search geography | Local, national and international opportunities; selected countries or regions; optional employer country preferences |
| Work arrangement | On-site, hybrid and remote; allow multiple selections |
| Mobility | Willingness to relocate, destinations, conditions and travel availability |
| Work eligibility | User-declared work authorization by country; need for sponsorship; willingness to relocate when sponsorship is offered |
| Employment | Accepted employee, contractor, self-employed or other arrangements |
| Compensation | Desired currencies, minimum compensation if supplied, period and gross/net basis, and requirement for actual payment in a currency |
| Career interests | Multiple roles, domains and skills; no mandatory fixed profession |
| Preference strength | Required constraint, preference or unspecified |

An unspecified field is unknown, not a negative answer. The user may explicitly indicate no restriction. A saved profile must be editable rather than embedded in application code. Work authorization is self-declared information, not legal verification.

Location, contract type, employer country and salary currency are independent dimensions. The application's core should support multiple profiles; the first interface may operate with one selected profile at a time. Shared access and authentication need separate design before any multi-user deployment.

### 3. First workflow

1. The user selects a profile and supplies job descriptions with source links where available.
2. The system retains the original text, source, collection time and extraction version.
3. It extracts structured facts with supporting excerpts.
4. It compares the job with the selected profile.
5. It displays eligibility, preferences, technical requirements and uncertainties separately.
6. It compares recurring skills across the supplied sample without treating the sample as a measure of overall market demand.

The initial input is user-supplied text. Automated collection from LinkedIn or other job sites is outside this phase. A supplied posting is a snapshot, not proof that the vacancy remains open. Source URLs must not be assigned to descriptions without a confirmed match.

### 4. Job records and evidence

Preserve the advertised title and any different role title in the description. Record employer when identified, location, allowed working countries, modality, employment arrangement, experience, education, required and preferred skills, salary, currency, sponsorship and authorization restrictions.

Each extracted fact must include a supporting excerpt or be marked as inferred or not provided. Preserve conflicting claims rather than silently selecting one. For example, different salary ranges in the header and description must remain visible with their respective evidence.

Keep salary period, currency and gross/net basis explicit. An advertised USD amount does not confirm payment in USD. “Full-time” does not establish employee status. “Remote” does not mean worldwide eligibility. Relative dates such as “five days ago” cannot establish an exact posting date without an anchored capture date.

Examples of extracted restrictions:

- “Remote (U.S.)” describes a geographic restriction, not permission to work from any country.
- “No present or future sponsorship” is evidence against a profile requiring sponsorship for that country.
- A lack of sponsorship information must remain unknown.
- Company not named: preserve as not identified; do not infer it from the recruiter.

No missing qualification, salary or eligibility fact may be invented.

### 5. Comparison rules and output

For each required profile constraint, show one of:

- **Compatible:** available evidence supports the criterion.
- **Incompatible:** available evidence explicitly conflicts with it.
- **Needs confirmation:** missing, ambiguous or conflicting evidence prevents a conclusion.

Overall eligibility is incompatible when a required constraint has an explicit conflict; otherwise it needs confirmation when a required constraint is unresolved; otherwise it is compatible with the configured constraints. Optional preferences are reported separately and do not automatically disqualify a vacancy.

Different acceptable pathways must be evaluated separately. A person may accept remote work from their current country OR relocation with sponsorship. A job may satisfy either pathway; a conflict in one must not erase a supported alternative. If every pathway is incompatible, the overall result is incompatible; if at least one is compatible, it is compatible; otherwise it needs confirmation.

Always show reasons and evidence. Keep technical fit separate from geographic and contractual eligibility. Do not equate match scores with probability of hiring. Without documented skills and experience, personal technical fit remains unassessed. Do not choose a career automatically or conclude market-wide demand from a few vacancies.

### 6. Privacy and local persistence

Profiles, imported private documents and job-analysis records belong in local storage, separate from public source code. Do not commit real profiles, personal documents, credentials or private database contents. Public examples must use synthetic data. Do not transmit profile data to a model provider without a clearly configured and authorized data flow.

Profile preferences must survive application restart and remain isolated by profile. A persistent volume is not a backup. Docker-local storage does not mean model inference is automatically local; model provider selection and costs remain undecided.

### 7. Acceptance criteria for the next phase

- Two synthetic profiles with different geography and contract preferences produce different, evidence-backed results for the same job.
- Editing a profile changes the comparison without source-code edits; stored preferences survive restart.
- Remote work restricted to one country does not qualify as worldwide remote.
- Explicit lack of sponsorship conflicts with a sponsorship-dependent relocation pathway; missing sponsorship information yields needs confirmation.
- Alternative pathways and optional preferences follow the rules above.
- Missing salary stays not provided; conflicting salary ranges remain visible.
- Advertised currency and actual payment currency remain distinct; full-time and employee status remain distinct.
- Every extracted fact has evidence or an explicit inference/unknown marker; facts can be reviewed against the source text.
- Profile records do not cross between users, and public fixtures contain no personal information.
- No career role, country, currency or founder-specific preference is fixed in the core.

### 8. Boundaries and open decisions

This phase does not include automated applications, contacting recruiters, sending community messages, legal eligibility decisions, agents or RAG. Any implementation or external publication requires a separate user authorization in this collaboration.

Before implementation, decide the profile entry interface, model/provider if needed, schema and evidence format, deduplication strategy, private data location and access model. Do not silently assume a cloud service, a paid provider or a public multi-user deployment.

---

## Português

### 1. Objetivo e estado atual

Ajudar pessoas a comparar oportunidades de carreira usando evidências rastreáveis e suas próprias preferências. O produto deve atender a diferentes perfis, países, formas de contratação e interesses profissionais. Nenhum cargo, local, moeda ou preferência pessoal pode ser fixado como padrão universal no código.

A infraestrutura V1 foi verificada localmente: Agno/AgentOS vazio, PostgreSQL com pgvector, volume Docker persistente, serviços saudáveis e registro preservado após reiniciar os containers. Agentes, RAG, gestão de perfis e análise de vagas ainda não foram implementados. Este documento define a próxima fase; não declara essas funcionalidades existentes nem autoriza sua implementação.

### 2. Perfis configuráveis

Cada usuário deve poder configurar e atualizar:

| Grupo | Campos |
|---|---|
| Localização atual | País, estado/região e cidade; área de deslocamento opcional |
| Geografia da busca | Oportunidades locais, nacionais e internacionais; países ou regiões selecionados; preferência opcional pelo país da empresa |
| Modalidade | Presencial, híbrido e remoto; permitir múltiplas escolhas |
| Mobilidade | Disponibilidade para mudança, destinos, condições e viagens |
| Elegibilidade de trabalho | Autorização declarada por país; necessidade de sponsor; aceitação de mudança quando houver patrocínio |
| Contratação | Vínculo empregatício, contractor, autônomo/PJ ou outras formas aceitas |
| Remuneração | Moedas desejadas, mínimo se informado, período e base bruta/líquida, exigência de pagamento efetivo em determinada moeda |
| Interesses profissionais | Múltiplos cargos, setores e habilidades; sem profissão fixa obrigatória |
| Força da preferência | Restrição obrigatória, preferência ou não especificada |

Campo não especificado significa desconhecido, não uma resposta negativa. O usuário pode indicar explicitamente que não tem restrição. O perfil salvo deve ser editável, sem ficar embutido no código. Autorização de trabalho é informação declarada pelo usuário, não verificação jurídica.

Localização, contrato, país da empresa e moeda salarial são dimensões independentes. O core deve suportar múltiplos perfis; a primeira interface pode operar com um perfil selecionado por vez. Acesso compartilhado e autenticação precisam de desenho separado antes de qualquer implantação multiusuário.

### 3. Primeiro fluxo

1. O usuário seleciona um perfil e fornece descrições de vagas com links quando disponíveis.
2. O sistema preserva texto original, fonte, momento da coleta e versão da extração.
3. Extrai fatos estruturados com trechos de evidência.
4. Compara a vaga com o perfil selecionado.
5. Apresenta elegibilidade, preferências, requisitos técnicos e incertezas separadamente.
6. Compara habilidades recorrentes na amostra recebida sem tratá-la como medida de demanda de todo o mercado.

A entrada inicial é texto fornecido pelo usuário. Coleta automática no LinkedIn ou em outros sites fica fora desta fase. Um anúncio fornecido é um retrato, não prova de que a vaga continua aberta. Não associe URLs às descrições sem correspondência confirmada.

### 4. Registros de vagas e evidências

Preserve o título anunciado e eventual título diferente na descrição. Registre empresa quando identificada, localização, países permitidos para trabalhar, modalidade, contrato, experiência, formação, habilidades obrigatórias e desejáveis, salário, moeda, sponsor e restrições de autorização.

Cada fato extraído deve incluir um trecho de evidência ou ser marcado como inferido ou não informado. Preserve afirmações conflitantes, sem escolher silenciosamente uma delas. Por exemplo, faixas salariais diferentes no cabeçalho e na descrição devem permanecer visíveis com suas respectivas evidências.

Mantenha explícitos período salarial, moeda e base bruta/líquida. Valor anunciado em USD não confirma pagamento em USD. “Full-time” não comprova vínculo empregatício. “Remoto” não significa elegibilidade mundial. Datas relativas como “há cinco dias” não determinam a publicação exata sem data de captura conhecida.

Exemplos de restrições extraídas:

- “Remote (U.S.)” indica uma restrição geográfica, não permissão para trabalhar de qualquer país.
- “No present or future sponsorship” é evidência contrária a um perfil que precise de patrocínio naquele país.
- Ausência de informação sobre sponsor deve permanecer desconhecida.
- Empresa sem nome: preserve como não identificada; não deduza a empresa a partir do recrutador.

Nenhuma qualificação, remuneração ou condição de elegibilidade ausente pode ser inventada.

### 5. Regras de comparação e resultado

Para cada restrição obrigatória do perfil, apresente:

- **Compatível:** a evidência disponível sustenta o critério.
- **Incompatível:** a evidência disponível contradiz explicitamente o critério.
- **Precisa confirmar:** informação ausente, ambígua ou conflitante impede a conclusão.

A elegibilidade geral é incompatível quando uma restrição obrigatória tem conflito explícito; caso contrário, precisa confirmar quando uma restrição obrigatória permanece sem resolução; caso contrário, é compatível com as restrições configuradas. Preferências opcionais são apresentadas separadamente e não eliminam automaticamente uma vaga.

Caminhos alternativos aceitos devem ser avaliados separadamente. Uma pessoa pode aceitar trabalho remoto do país atual OU mudança com sponsor. A vaga pode atender a qualquer caminho; um conflito em um deles não pode apagar uma alternativa sustentada. Se todos os caminhos forem incompatíveis, o resultado geral será incompatível; se pelo menos um for compatível, será compatível; caso contrário, precisa confirmar.

Sempre mostre justificativas e evidências. Separe aderência técnica de elegibilidade geográfica e contratual. Não transforme pontuação de aderência em probabilidade de contratação. Sem habilidades e experiência documentadas, a aderência técnica pessoal permanece não avaliada. Não escolha automaticamente uma carreira nem conclua demanda de todo o mercado com poucas vagas.

### 6. Privacidade e persistência local

Perfis, documentos privados importados e análises devem ficar no armazenamento local, separados do código público. Não inclua perfis reais, documentos pessoais, credenciais ou conteúdo privado do banco em commits. Exemplos públicos devem usar dados fictícios. Não transmita dados do perfil a um provedor de modelos sem fluxo claramente configurado e autorizado.

As preferências devem sobreviver ao restart da aplicação e permanecer isoladas por perfil. Volume persistente não é backup. Armazenamento local em Docker não significa inferência automaticamente local; escolha de provedor e custos continuam indefinidos.

### 7. Critérios de aceitação da próxima fase

- Dois perfis fictícios com preferências geográficas e contratuais diferentes produzem resultados diferentes, sustentados por evidências, para a mesma vaga.
- Editar o perfil altera a comparação sem mudar o código; preferências salvas sobrevivem ao restart.
- Trabalho remoto restrito a um país não é classificado como remoto mundial.
- Ausência explícita de sponsor contradiz um caminho de mudança dependente de patrocínio; sponsor não informado gera precisa confirmar.
- Caminhos alternativos e preferências opcionais seguem as regras anteriores.
- Salário ausente permanece não informado; faixas conflitantes ficam visíveis.
- Moeda anunciada e moeda efetiva de pagamento permanecem distintas; full-time e vínculo empregatício permanecem distintos.
- Cada fato tem evidência ou indicação explícita de inferência/desconhecimento; é possível revisar os fatos contra o texto original.
- Registros de perfis não se misturam entre usuários e exemplos públicos não contêm informações pessoais.
- Nenhum cargo, país, moeda ou preferência particular do criador fica fixado no core.

### 8. Limites e decisões em aberto

Esta fase não inclui candidaturas automáticas, contato com recrutadores, mensagens a comunidades, decisões jurídicas de elegibilidade, agentes ou RAG. Qualquer implementação ou publicação externa exige autorização separada do usuário nesta colaboração.

Antes da implementação, definir interface de cadastro do perfil, modelo/provedor se necessário, schema e formato de evidências, deduplicação, local dos dados privados e modelo de acesso. Não presumir silenciosamente serviço cloud, provedor pago ou implantação pública multiusuário.
