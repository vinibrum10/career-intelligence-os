# Local profile API

[English](#english) | [Português](#português)

## English

This stage stores typed, configurable profiles and append-only preference versions in PostgreSQL. It does not compare jobs, use an LLM or provide authentication. Owner IDs scope every profile operation; they are not credentials. Keep the service on localhost; do not expose it to a network or multiple untrusted users.

### Upgrade and verify

From the project directory in PowerShell, with Docker Desktop running:

```powershell
.\verify-profiles.ps1
```

This builds the image, applies Alembic migrations to the existing database, starts the API and tests profiles in a new disposable `career_profile_test_*` database. It restarts only this project's containers to verify persistence, then removes the disposable database. Existing career and AgentOS records and the volume are preserved. No Python packages are installed in Windows by this command.

For an upgrade without profile tests:

```powershell
docker compose build api
docker compose up -d --wait db
docker compose run --rm --no-deps api alembic upgrade head
docker compose up -d --wait api
```

Migration downgrade is not part of normal setup: it removes profile tables and data. Do not delete the volume or expect initialization SQL to upgrade it. The original `verify.ps1` still tests base infrastructure; it does not apply profile migrations. Database test verification is separate from local SQLite checks; row locking and PostgreSQL migration behavior require the Docker test.

### Use in the API documentation

Open http://127.0.0.1:8000/docs and find **Local profiles (no authentication)**.

1. POST `/career/owners` with an optional display label. Save the returned owner ID locally.
2. POST `/career/owners/{owner_id}/profiles` with a label and preferences, using that owner ID.
3. GET the profile or the owner's profile list.
4. PUT the profile with a complete label/preferences object and `expected_version` equal to the current version. An outdated update returns HTTP 409; reload before trying again.
5. GET `/career/owners/{owner_id}/profiles/{profile_id}/versions` to see preference history, newest first. Lists accept `limit` (1–100) and `offset`.

Synthetic profile example:

```json
{
  "label": "Example career scenario",
  "preferences": {
    "current_location": {"country": "CA", "region": "Ontario", "city": "Ottawa"},
    "pathways": [
      {
        "id": "remote",
        "label": "Remote from current country",
        "search_scope": "national",
        "work_countries": {"mode": "required", "values": ["CA"]},
        "work_arrangements": {"mode": "required", "values": ["remote"]},
        "contracts": {"mode": "preferred", "values": ["employee"]}
      },
      {
        "id": "relocate",
        "label": "Sponsored relocation",
        "search_scope": "international",
        "work_countries": {"mode": "required", "values": ["DE"]},
        "relocation_allowed": true,
        "sponsorship": {"mode": "required", "values": ["offered"]}
      }
    ]
  }
}
```

Modes: `required`, `preferred`, `unrestricted`, `unspecified`. Required/preferred choices need values; unrestricted/unspecified choices have no values. A missing boolean remains null, not false. Incomplete profiles may be saved but do not establish eligibility. At this stage pathways are stored; their AND/OR comparison logic is not implemented.

Country and currency inputs require uppercase two/three-letter code format; membership in ISO reference lists is not yet checked. Skills can include self-declared experience and a provenance description, which is not independent verification. Compensation requires explicit advertised/actual-payment currency basis; minimum amounts require one currency, a period and gross/net basis. A missing gross/net basis may be explicitly `unknown`. There is no conversion, salary estimate or hiring-probability calculation.

Creating/updating a profile creates an immutable preferences version. The current display label is not versioned. Deletion and shared-user authentication are not implemented yet. Do not put real profiles in public examples or commit private data.

## Português

Esta etapa guarda perfis tipados e configuráveis e versões de preferências no PostgreSQL. Não compara vagas, usa LLM nem oferece autenticação. O ID do proprietário delimita cada operação de perfil; não é uma credencial. Mantenha o serviço em localhost, sem exposição à rede ou a usuários não confiáveis.

### Atualizar e verificar

No PowerShell na pasta do projeto, com Docker Desktop rodando:

```powershell
.\verify-profiles.ps1
```

O script constrói a imagem, aplica migrations Alembic ao banco existente, inicia a API e testa perfis em um banco novo e descartável `career_profile_test_*`. Reinicia apenas os containers deste projeto para verificar persistência e remove o banco de teste. Preserva registros reais, tabelas AgentOS e volume. Esse comando não instala bibliotecas Python no Windows.

Os comandos de atualização sem testes estão na seção em inglês. Downgrade não faz parte da instalação normal: remove tabelas e dados de perfis. Não apague o volume nem espere atualização pelo SQL de inicialização. `verify.ps1` continua testando a infraestrutura base, mas não aplica migrations de perfis. Os testes SQLite locais não comprovam locks nem migrations PostgreSQL; isso exige o teste no Docker.

### Usar pela documentação da API

Abra http://127.0.0.1:8000/docs e procure **Local profiles (no authentication)**.

1. POST `/career/owners` com rótulo opcional. Guarde localmente o ID retornado.
2. POST `/career/owners/{owner_id}/profiles` com nome e preferências, usando esse ID.
3. Consulte o perfil ou a lista de perfis do proprietário com GET.
4. Atualize com PUT, enviando nome/preferências completos e `expected_version` igual à versão atual. Uma edição desatualizada retorna HTTP 409; consulte novamente antes de repetir.
5. Consulte `/career/owners/{owner_id}/profiles/{profile_id}/versions` para o histórico, do mais recente ao mais antigo. Listas aceitam `limit` (1–100) e `offset`.

O JSON na seção em inglês é um exemplo fictício de duas alternativas: remoto do país atual ou mudança com sponsor. Modos: obrigatório (`required`), preferencial (`preferred`), sem restrição (`unrestricted`) e não especificado (`unspecified`). Escolhas obrigatórias/preferenciais exigem valores; sem restrição/não especificado não recebem valores. Booleano ausente permanece null, não false. Perfis incompletos podem ser salvos sem estabelecer elegibilidade. Caminhos são armazenados; a comparação E/OU ainda não foi implementada.

País e moeda exigem formato de código em maiúsculas com duas/três letras; não há validação de pertencimento às listas ISO ainda. Habilidades podem incluir experiência declarada e descrição da origem, sem verificação independente. Remuneração diferencia moeda anunciada e pagamento efetivo; valores mínimos exigem uma moeda, período e base bruta/líquida. Base desconhecida pode ser declarada como `unknown`. Não há conversão, estimativa salarial nem probabilidade de contratação.

Cadastro/atualização cria versão imutável das preferências. O rótulo atual não é versionado. Exclusão e autenticação compartilhada ainda não foram implementadas. Não publique perfis reais nem dados privados no Git.
