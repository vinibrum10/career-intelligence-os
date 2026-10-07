# Career Intelligence OS — V1 local

Base de infraestrutura: Agno/AgentOS vazio, PostgreSQL 17 e pgvector no Docker local. Nenhum cargo foi fixado. Não há agentes, RAG, embeddings, provedor de IA ou chave de API nesta etapa.

## Ambiente verificado

- Docker CLI 29.6.2 e Compose 5.3.1 instalados.
- Git 2.54.0, Python 3.14.5 e VS Code 1.140.0 instalados.
- O container Python usa 3.12 para isolar a aplicação do Python do Windows.
- `docker compose config --quiet` passou.
- Validação concluída: API e banco saudáveis, pgvector disponível e registro preservado após reiniciar os dois containers, conforme a execução de `verify.ps1`.
- Resultado: `PASS: API, PostgreSQL, pgvector and persistence after restart.`

## Iniciar e comprovar

Pré-requisitos: Docker Desktop com containers Linux, Docker Compose e PowerShell. Git é necessário para clonar. Python no Windows não é necessário: as dependências são instaladas dentro do container.

Após clonar, copie `.env.example` para `.env` somente se `.env` ainda não existir. Substitua a senha de exemplo por uma senha hexadecimal aleatória. Preserve o `.env` da instalação já configurada.

Abra o Docker Desktop, aguarde “Engine running” e execute no PowerShell na pasta do projeto:

```powershell
.\verify.ps1
```

O teste constrói e inicia os containers, consulta a API e pgvector, grava um identificador único no banco, reinicia os dois containers e confirma que o identificador foi preservado. Só gera `verification.json` após sucesso. Os containers ficam rodando.

API local: http://127.0.0.1:8000/docs. Verificação do banco: http://127.0.0.1:8000/health/ready.

Na instalação local validada, `.env` contém uma senha aleatória. `.env` e `verification.json` estão excluídos do Git. Cada pessoa que clonar deve criar seu próprio `.env`. Não publique senhas nem dados pessoais.

## Persistência e comandos

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

## Escopo e próximos passos

Esta V1 comprova a infraestrutura local e a persistência após restart. Ainda não analisa vagas nem recomenda carreiras. Não há cargo predefinido no core; futuras opções deverão ser avaliadas com evidências de mercado.

Agentes e RAG ficam para uma fase posterior. Após a publicação no GitHub, Issues poderão receber sugestões e relatos de problemas.
