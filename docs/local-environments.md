# Homologação e produção locais

Um único `compose.yaml` atende os dois ambientes. As configurações abaixo separam a execução; não criam serviços até você executar os comandos de inicialização.

| Ambiente | Arquivo privado | Projeto Docker | Endereço | Volume de banco |
| --- | --- | --- | --- | --- |
| Homologação | `.env.staging` | `career-staging` | http://127.0.0.1:8001 | `career-staging_postgres_data` |
| Produção | `.env.production` | `career-production` | http://127.0.0.1:8002 | `career-production_postgres_data` |

A instalação antiga continua usando `.env`, porta 8000 e o volume `career-intelligence-os_postgres_data`. Nenhum comando deste guia transfere, apaga ou reaproveita seus dados. Os ambientes novos começam vazios. O banco não publica porta; a aplicação continua acessível somente no próprio computador, sem autenticação.

## 1. Preparar os arquivos uma única vez

Copie `.env.staging.example` para `.env.staging` e `.env.production.example` para `.env.production`, somente se os destinos não existirem. Substitua a senha de cada arquivo por uma senha hexadecimal diferente. Você pode gerar cada uma no PowerShell com `[guid]::NewGuid().ToString('N')`.

Esses arquivos privados são ignorados pelo Git e pelo contexto de construção Docker. Preserve-os e mantenha uma cópia segura: volumes persistentes não são backup. Os arquivos `.example` ficam versionados e não contêm credenciais reais.

Abra um terminal novo, sem variáveis `POSTGRES_PASSWORD`, `CAREER_APP_IMAGE`, `API_PORT` ou `COMPOSE_PROJECT_NAME` exportadas. Variáveis do terminal têm precedência sobre o arquivo selecionado; não use essa precedência para misturar ambientes.

## 2. Construir uma versão e homologar

Na worktree com o commit que será validado, confira que não há alterações locais pendentes. Construa a imagem uma vez:

```powershell
if (git status --porcelain) { throw 'Use um commit limpo antes de construir a versão.' }
$release = git rev-parse HEAD
docker build --target runtime -t "career-intelligence-os:$release" .
```

No `.env.staging`, preencha `CAREER_APP_IMAGE` com `career-intelligence-os:` seguido desse SHA completo. Mantenha o projeto e a porta indicados no modelo.

Os argumentos abaixo fixam arquivo de configuração e projeto. Recrie a variável ao abrir outro terminal:

```powershell
$stage = @('--file','compose.yaml','--env-file','.env.staging','--project-name','career-staging')
docker compose @stage config --quiet
docker compose @stage up -d --no-build --pull never --wait db
docker compose @stage run --rm --no-deps --pull never api alembic upgrade head
docker compose @stage up -d --no-build --pull never --wait api
```

Se qualquer comando falhar, pare e corrija antes de continuar. Abra http://127.0.0.1:8001/profiles e valide o fluxo com dados fictícios. Não use dados reais de produção ou o mesmo volume da instalação antiga.

`--no-build` e `--pull never` evitam construir ou baixar uma aplicação diferente durante a inicialização. O comando de migration usa a imagem local selecionada. Para uma atualização posterior, faça backup antes das migrations também em homologação, se precisar preservar seus dados.

## 3. Promover a mesma versão para produção

Esta etapa depende da validação de uso e da autorização de Vinicius. Não execute testes automatizados em produção.

Preencha `CAREER_APP_IMAGE` no `.env.production` com a mesma imagem validada em homologação. Não reconstrua a imagem. Antes de atualizar um banco de produção existente, tenha backup verificável e procedimento de restauração. Voltar a imagem não desfaz migrations automaticamente.

```powershell
$prod = @('--file','compose.yaml','--env-file','.env.production','--project-name','career-production')
docker compose @prod config --quiet
docker compose @prod up -d --no-build --pull never --wait db
docker compose @prod run --rm --no-deps --pull never api alembic upgrade head
docker compose @prod up -d --no-build --pull never --wait api
```

Abra http://127.0.0.1:8002/profiles. Registre o SHA, a imagem e o resultado da validação. Preserve a imagem local aprovada e evite sobrescrever sua tag; antes da promoção, `docker image inspect career-intelligence-os:<SHA> --format '{{.Id}}'` deve corresponder à imagem usada pelo container de homologação, consultável com `docker inspect (docker compose @stage ps -q api) --format '{{.Image}}'`.

## Operação e worktrees

- Consultar: `docker compose @stage ps` ou `docker compose @prod ps`.
- Logs: `docker compose @stage logs --tail 100 api` (troque para `@prod` quando necessário). Não publique logs com dados pessoais.
- Parar preservando os dados: `docker compose @stage stop` ou `docker compose @prod stop`.
- Nunca usar `down -v`, nem comandos de limpeza global de volumes.
- Os scripts `verify.ps1`, `verify-profiles.ps1` e `verify-jobs.ps1` são da instalação antiga. Não os use para testar estes ambientes; a CI tem infraestrutura descartável própria.
- Os projetos `career-staging` e `career-production` são destinos persistentes. Opere cada um a partir de uma única pasta por vez; não os inicialize por worktrees concorrentes. Ao trocar de pasta, use os mesmos arquivos privados preservados, preferencialmente por caminho absoluto em `--env-file`.
- Para executar uma worktree de desenvolvimento, use projeto exclusivo (`--project-name career-dev-descricao`), outra porta via `API_PORT` e credenciais próprias em um arquivo privado. Nunca aponte testes para os projetos persistentes.

## Verificação e limites

`node tests/test_environment_config.cjs` resolve os três modelos Compose com credenciais sintéticas, sem iniciar containers, e verifica compatibilidade da instalação antiga, portas, redes, volumes e imagem de release. Esse teste roda automaticamente na CI junto dos demais casos JavaScript.

Esta entrega prepara as configurações. A CI valida a aplicação em infraestrutura descartável; ela não inicializa os ambientes persistentes, não migra os dados antigos e não autoriza publicação em produção. A validação real do fluxo em homologação é a próxima etapa de uso.
