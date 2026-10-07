# Contributing to Career Intelligence OS

[English](#english) | [Português](#português)

## English

Contributions in English or Portuguese are welcome: documentation improvements, bug reports, setup testing and focused code changes.

### Current scope

V1 is a local Docker foundation with an empty Agno/AgentOS runtime, PostgreSQL and pgvector. Container health and persistence after restart have been verified. Job analysis, agents and RAG are planned for later phases.

Keep career options open. Do not hardcode a particular role as the default goal. Future career recommendations should explain their market evidence, sources and limitations.

### Issues

Search existing Issues before opening a new one. For bugs, include expected and actual behavior, reproduction steps, relevant operating system and Docker versions, and sanitized error logs. For suggestions, explain the problem, who it helps and a concrete example. Discuss substantial changes in an Issue before implementing them.

Do not share passwords, tokens, `.env`, personal documents or private database contents in Issues, commits or logs.

### Local development and validation

1. Fork this repository and clone your fork.
2. Create a focused branch, such as `docs/improve-setup`.
3. Follow [README.md](README.md) and create your own `.env` from `.env.example`.
4. Make your change and validate it.

For runtime or infrastructure changes, run in PowerShell from the project directory:

```powershell
.\verify.ps1
```

The test builds and starts this project's containers, inserts a test record, restarts both containers and checks persistence. It leaves the containers running and writes `verification.json` after success. Run it when restarting this installation is acceptable. Documentation changes only require checking the text, links and instructions.

Keep `.env` and `verification.json` out of commits. `docker compose down -v` removes the project's volumes; do not use it on data you want to preserve.

### Pull requests

Push your branch to your fork and open a pull request targeting `main` here. Describe the problem, the resulting behavior, any related Issue, validation performed and remaining limitations. Keep unrelated changes separate. Contributions are reviewed before merging.

---

## Português

Contribuições em português ou inglês são bem-vindas: melhorias na documentação, relatos de erros, testes de instalação e mudanças focadas no código.

### Escopo atual

A V1 é uma base local em Docker com Agno/AgentOS vazio, PostgreSQL e pgvector. A saúde dos containers e a persistência após restart foram verificadas. Análise de vagas, agentes e RAG ficam para fases posteriores.

Mantenha as opções de carreira abertas. Não fixe um cargo como objetivo padrão. Recomendações futuras devem explicar suas evidências de mercado, fontes e limitações.

### Issues

Pesquise as Issues existentes antes de abrir uma nova. Para erros, inclua o comportamento esperado e observado, os passos para reproduzir, as versões relevantes do sistema operacional e Docker e os logs sem informações privadas. Para sugestões, explique o problema, quem se beneficia e um exemplo concreto. Discuta mudanças grandes em uma Issue antes de implementá-las.

Não compartilhe senhas, tokens, `.env`, documentos pessoais ou conteúdo privado do banco em Issues, commits ou logs.

### Desenvolvimento local e validação

1. Faça um fork deste repositório e clone seu fork.
2. Crie uma branch focada, como `docs/improve-setup`.
3. Siga o [README.md](README.md) e crie seu próprio `.env` a partir de `.env.example`.
4. Faça a mudança e valide o resultado.

Para mudanças na aplicação ou infraestrutura, execute no PowerShell na pasta do projeto:

```powershell
.\verify.ps1
```

O teste constrói e inicia os containers deste projeto, insere um registro, reinicia os dois containers e verifica a persistência. Deixa os containers rodando e grava `verification.json` após sucesso. Execute quando for aceitável reiniciar esta instalação. Mudanças na documentação exigem apenas conferir texto, links e instruções.

Mantenha `.env` e `verification.json` fora dos commits. `docker compose down -v` remove os volumes do projeto; não use esse comando em dados que deseja preservar.

### Pull requests

Envie sua branch para seu fork e abra um pull request direcionado à `main` deste repositório. Descreva o problema, o comportamento resultante, a Issue relacionada se houver, a validação realizada e as limitações restantes. Separe mudanças sem relação. As contribuições serão revisadas antes do merge.
