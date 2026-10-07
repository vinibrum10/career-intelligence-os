# Local profile screen / Tela local de perfis

## English

The profile screen is served by the existing application at `http://127.0.0.1:8000/profiles`. It uses the profile API and stores records in PostgreSQL. No separate frontend server, cloud deployment, Python installation on Windows or new dependency is required.

With the profile migration already applied, rebuild the API from the project directory:

```powershell
docker compose up -d --build --wait api
```

For a new installation, first follow the environment and migration steps in [Profile API setup](profile-api.md).

Open the screen. Paste an existing owner identifier and choose **Abrir meus perfis**, or expand **Primeira vez? Criar um espaço** to create a new owner. Keep its identifier: the browser only remembers the last owner ID; clearing browser storage loses that shortcut, not database records. Owner IDs are not authentication. Continue using localhost only.

Choose a saved profile or **+ Novo**. Enter its name, current location and optional interests. Add independent search pathways with geography, work arrangements, relocation, sponsorship, contracts and optional compensation. Fields start unspecified; there is no predefined country or role. Required/preferred criteria require values. Country codes use two letters and currencies three; lowercase is normalized and codes are format-checked by the API, not validated against ISO lists.

**Salvar perfil** creates a new preference version. The history shows older versions without editing them. Unsaved changes prompt before switching profiles or reloading. A stale edit displays a conflict message and keeps the form; **Recarregar versão salva** discards the form only after confirmation when dirty. The display name is not versioned. Existing skill evidence and authorization declarations are preserved; their editing remains available through the API. History displays these declarations as self-reported information.

Validation: browser creation, editing, reload, history, compensation decimals, unspecified/negative preferences, preserved advanced fields and stale-edit rejection were checked against an isolated SQLite test server. The previous PostgreSQL API and restart checks passed; the new screen must also be opened against the rebuilt Docker service. This screen does not analyze vacancies or provide authentication.

## Português

A tela fica em `http://127.0.0.1:8000/profiles`, na aplicação existente. Usa a API de perfis e grava no PostgreSQL. Não exige outro servidor de interface, nuvem ou novas bibliotecas.

Com a migration de perfis já aplicada, execute na pasta do projeto:

```powershell
docker compose up -d --build --wait api
```

Em uma instalação nova, siga antes as etapas de ambiente e migration da [API de perfis](profile-api.md).

Na tela, cole o identificador de proprietário existente e clique em **Abrir meus perfis**, ou use **Primeira vez? Criar um espaço**. Guarde o identificador. O navegador lembra apenas o último ID; limpar seus dados remove esse atalho, sem apagar registros do banco. IDs não oferecem autenticação. Mantenha a aplicação em localhost.

Selecione um perfil ou clique em **+ Novo**. Informe nome, localização atual e interesses opcionais. Adicione caminhos independentes de busca com países, modalidade, mudança, sponsor, vínculo e remuneração opcional. Nenhum país ou cargo é predefinido. Campos começam não informados. Critérios obrigatórios/preferenciais exigem valores. Países usam duas letras e moedas três; minúsculas são normalizadas. A API verifica formato, não pertencimento às listas ISO.

**Salvar perfil** cria uma nova versão das preferências. O histórico mostra as anteriores sem alterá-las. Trocar de perfil ou recarregar pede confirmação quando há alterações não salvas. Uma edição desatualizada exibe conflito e mantém o formulário. **Recarregar versão salva** permite consultar o estado atual, descartando mudanças pendentes com confirmação. O nome de exibição não é versionado. Habilidades e autorizações já cadastradas são preservadas; sua edição permanece pela API. O histórico mostra essas informações como declarações do usuário.

Validação: cadastro, edição, recarregamento, histórico, decimais de remuneração, preferências não informadas/negativas, preservação de campos adicionais e bloqueio de edição desatualizada foram verificados pelo navegador em servidor isolado com SQLite. Os testes anteriores da API no PostgreSQL e de restart passaram; falta abrir a nova tela no serviço Docker reconstruído. A tela ainda não analisa vagas nem oferece autenticação.
