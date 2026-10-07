# Career Intelligence OS — Local V1

[English](#english) | [Português](#português)

## English

Local infrastructure and configurable profiles: an Agno/AgentOS runtime with no registered agents, PostgreSQL 17 and pgvector running in Docker. No career role is predefined. This stage includes no agents, RAG, embeddings, AI provider or API key.

### Verified environment

- Docker CLI 29.6.2 and Compose 5.3.1 installed.
- Git 2.54.0, Python 3.14.5 and VS Code 1.140.0 installed.
- The Python container uses version 3.12 to isolate the application from Windows Python.
- `docker compose config --quiet` passed.
- Validation completed: the API and database were healthy, pgvector was available, and a database record survived a restart of both containers, as verified by `verify.ps1`.
- Result: `PASS: API, PostgreSQL, pgvector and persistence after restart.`
- Profile validation completed on October 7, 2026: all 10 PostgreSQL tests passed, including preference history, owner scoping, invalid input rejection and concurrent edits. A synthetic profile and its two preference versions survived a restart of the database and API containers. The disposable test database was removed.
- Result: `PASS: profile API, version history, owner isolation and restart persistence.`

### Start and verify

Prerequisites: Docker Desktop with Linux containers, Docker Compose and PowerShell. Git is needed to clone the repository. Python on Windows is not required: dependencies are installed inside the container.

After cloning, copy `.env.example` to `.env` only if `.env` does not already exist. Replace the example password with a random hexadecimal password. Preserve the `.env` file of an already configured installation.

Open Docker Desktop, wait for “Engine running”, and run the following in PowerShell from the project directory:

```powershell
.\verify.ps1
```

The test builds and starts the containers, checks the API and pgvector, writes a unique identifier to the database, restarts both containers, and confirms that the identifier was preserved. It generates `verification.json` only after success. The containers remain running.

To install or upgrade the profile API and run its PostgreSQL tests, also execute:

```powershell
.\verify-profiles.ps1
```

This applies migrations without removing the persistent volume, uses a disposable test database and restarts the containers belonging to this project. Owner IDs delimit operations but do not provide authentication. See [profile setup and examples](docs/profile-api.md).

Local API: http://127.0.0.1:8000/docs. Database readiness check: http://127.0.0.1:8000/health/ready.

In the validated local installation, `.env` contains a random password. `.env` and `verification.json` are excluded from Git. Each person cloning the repository must create their own `.env`. Do not publish passwords or personal data.

### Persistence and commands

The named volume `career-intelligence-os_postgres_data` stores data at `/var/lib/postgresql/data`. The database does not publish a port on Windows; the API only accepts connections on localhost.

```powershell
docker compose ps
docker compose logs --tail 100
docker compose stop
docker compose up -d --wait
```

`docker compose down` preserves the volume. **Do not use `docker compose down -v`** if you want to keep the data. Persistent storage is not a backup.

Agno is pinned to 3.1.1. Supporting dependencies use version ranges and the pg17 image receives updates; a complete dependency lock and image digests can be defined after the first successful build.

Official references consulted: https://docs.agno.com/agent-os/introduction, https://github.com/agno-agi/agentos-docker and https://github.com/pgvector/pgvector. This is a new, minimal foundation rather than a copy of the template's demonstration agents.

### Scope and next steps

This V1 includes local infrastructure and configurable profiles with preference history. Infrastructure and profile tests passed in the local installation. Run `verify-profiles.ps1` to apply profile migrations and validate each new or existing installation. See [Profile API setup and examples](docs/profile-api.md). It does not yet analyze job openings or recommend careers. No role is predefined in the core; future career options should be evaluated using market evidence.

Agents and RAG are reserved for a later phase. Suggestions and bug reports can be shared through GitHub Issues.

---

## Português

Infraestrutura local e perfis configuráveis: Agno/AgentOS sem agentes registrados, PostgreSQL 17 e pgvector no Docker. Nenhum cargo foi fixado. Não há agentes, RAG, embeddings, provedor de IA ou chave de API nesta etapa.

### Ambiente verificado

- Docker CLI 29.6.2 e Compose 5.3.1 instalados.
- Git 2.54.0, Python 3.14.5 e VS Code 1.140.0 instalados.
- O container Python usa 3.12 para isolar a aplicação do Python do Windows.
- `docker compose config --quiet` passou.
- Validação concluída: API e banco saudáveis, pgvector disponível e registro preservado após reiniciar os dois containers, conforme a execução de `verify.ps1`.
- Resultado: `PASS: API, PostgreSQL, pgvector and persistence after restart.`
- Perfis validados em 7 de outubro de 2026: os 10 testes no PostgreSQL passaram, incluindo histórico de preferências, delimitação por proprietário, rejeição de entradas inválidas e edições simultâneas. Um perfil fictício e suas duas versões de preferências sobreviveram ao restart do banco e da API. O banco descartável de testes foi removido.
- Resultado: `PASS: profile API, version history, owner isolation and restart persistence.`

### Iniciar e comprovar

Pré-requisitos: Docker Desktop com containers Linux, Docker Compose e PowerShell. Git é necessário para clonar. Python no Windows não é necessário: as dependências são instaladas dentro do container.

Após clonar, copie `.env.example` para `.env` somente se `.env` ainda não existir. Substitua a senha de exemplo por uma senha hexadecimal aleatória. Preserve o `.env` da instalação já configurada.

Abra o Docker Desktop, aguarde “Engine running” e execute no PowerShell na pasta do projeto:

```powershell
.\verify.ps1
```

O teste constrói e inicia os containers, consulta a API e pgvector, grava um identificador único no banco, reinicia os dois containers e confirma que o identificador foi preservado. Só gera `verification.json` após sucesso. Os containers ficam rodando.

Para instalar ou atualizar a API de perfis e executar seus testes no PostgreSQL, execute também:

```powershell
.\verify-profiles.ps1
```

O script aplica migrations sem remover o volume persistente, usa um banco descartável de testes e reinicia os containers deste projeto. Os IDs de proprietários delimitam operações, mas não oferecem autenticação. Veja [instalação e exemplos de perfis](docs/profile-api.md).

API local: http://127.0.0.1:8000/docs. Verificação do banco: http://127.0.0.1:8000/health/ready.

Na instalação local validada, `.env` contém uma senha aleatória. `.env` e `verification.json` estão excluídos do Git. Cada pessoa que clonar deve criar seu próprio `.env`. Não publique senhas nem dados pessoais.

### Persistência e comandos

O volume nomeado `career-intelligence-os_postgres_data` guarda os dados em `/var/lib/postgresql/data`. O banco não publica uma porta no Windows; a API só aceita conexões em localhost.

```powershell
docker compose ps
docker compose logs --tail 100
docker compose stop
docker compose up -d --wait
```

`docker compose down` preserva o volume. **Não use `docker compose down -v`** se quiser manter os dados. O volume é persistência, não backup.

Agno está fixado em 3.1.1. As dependências auxiliares têm intervalos e a imagem pg17 recebe atualizações; um lock completo e imagens por digest podem ser definidos após a primeira construção bem-sucedida.

Referências oficiais consultadas: https://docs.agno.com/agent-os/introduction, https://github.com/agno-agi/agentos-docker e https://github.com/pgvector/pgvector. Esta é uma base nova e mínima, não uma cópia dos agentes de demonstração do template.

### Escopo e próximos passos

Esta V1 inclui infraestrutura local e perfis configuráveis com histórico de preferências. Os testes de infraestrutura e perfis passaram na instalação local. Execute `verify-profiles.ps1` para aplicar as migrations de perfis e validar cada instalação nova ou existente. Veja [instalação e exemplos da API de perfis](docs/profile-api.md). Ainda não analisa vagas nem recomenda carreiras. Não há cargo predefinido no core; futuras opções deverão ser avaliadas com evidências de mercado.

Agentes e RAG ficam para uma fase posterior. Sugestões e relatos de problemas podem ser compartilhados pelas Issues no GitHub.
