# Career Intelligence OS — Regras de trabalho

Versão: 1.0 · Data: 29/10/2026 · Responsável: Vinicius

Este arquivo deve ficar na raiz do repositório e ser versionado. É a referência canônica das regras operacionais do projeto para o Codex no VS Code, no terminal e em outras interfaces. Ele define o fluxo exigido; sua existência não significa que ambientes, automações ou proteções já estejam configurados.

## 1. Objetivo e referências

- Apoiar decisões de carreira com comparações rastreáveis entre vagas, fatos e preferências profissionais.
- Consultar `FOCO_DO_PROJETO.md`, `docs/product-requirements.md` e a documentação pertinente antes de implementar uma tarefa. Respeitar o status de proposta ou aprovação de cada documento.
- Usar este arquivo para regras de trabalho; o documento de foco para direção do produto; os requisitos para comportamento esperado; e `README.md` e `CONTRIBUTING.md` para instalação e contribuição.
- Não tratar funcionalidades planejadas como entregues. Confirmar o estado no código e nas verificações.
- Não fixar cargo, país ou preferência pessoal como objetivo universal. Preservar evidências e revisão humana dos fatos sugeridos por IA.
- Concluir uma tarefa delimitada por vez. Não ampliar escopo, trocar a arquitetura ou adicionar serviços sem necessidade demonstrada para a entrega.
- Quando documentos divergirem, informar o conflito e resolvê-lo conforme as decisões de Vinicius. Não alterar estas regras silenciosamente para acomodar uma implementação.

## 2. Responsabilidades

- O Codex inspeciona o projeto, prepara a worktree, implementa a tarefa, executa as verificações pertinentes e entrega um resumo revisável.
- Vinicius abre o pull request, revisa os resultados e faz o merge. O Codex não abre pull requests, não os aprova, não faz merge e não ativa merge automático.
- O Codex pode preparar uma sugestão de título e descrição do pull request.
- Commit e push dependem de instrução de Vinicius; não estão implícitos em um pedido de implementação. Quando autorizados, incluir apenas os arquivos da tarefa e nunca enviar diretamente à `main`.
- Publicação em produção depende de validação e autorização de Vinicius para a versão correspondente.
- Comunicar-se em português, com explicações claras sobre resultado, validação e limitações. Pedir esclarecimento apenas quando faltar uma decisão necessária; avançar nas partes independentes.

## 3. Worktrees e branches

- Toda implementação ou alteração versionada deve ocorrer em uma worktree dedicada à tarefa, em branch `codex/descricao-curta`. Reutilizar uma worktree adequada se ela já existir.
- Manter `main` como branch de integração. Não desenvolver, commitar nem enviar alterações diretamente nela. Não criar uma branch permanente `develop` sem nova decisão.
- Antes de editar, conferir diretório, branch, worktrees existentes e alterações locais. Apresentar o objetivo e os critérios de aceitação da tarefa.
- Abrir no VS Code a pasta da worktree em que o trabalho será feito e verificar a presença deste `AGENTS.md` nessa cópia.
- Não sobrescrever, descartar, mover ou incluir em commits alterações anteriores de Vinicius sem instrução. Uma worktree nova não contém automaticamente alterações não commitadas da pasta original.
- Não usar limpeza destrutiva, reset forçado, push forçado ou remoção forçada de worktree como rotina.
- Remover uma worktree somente quando sua entrega estiver preservada e não houver alterações ou arquivos locais necessários. Não remover bancos ou volumes junto com ela.

## 4. Homologação e produção

- Manter dois ambientes persistentes: homologação (`staging`) e produção (`production`). O desenvolvimento por worktree e a infraestrutura descartável da CI ficam separados desses ambientes.
- Começar com execução local, conforme a direção atual do projeto. Hospedagem externa exige decisão própria; não expor a aplicação atual na internet sem tratar autenticação e acesso.
- Homologação usa dados fictícios ou preparados para teste. Produção guarda os dados reais de uso.
- Separar configurações, credenciais, bancos, volumes, redes e portas. Não compartilhar volume ou conexão de banco entre ambientes ou entre execuções de teste.
- Cada worktree que executar containers deve usar um projeto Docker Compose exclusivo e portas disponíveis. Diretórios diferentes, sozinhos, não garantem isolamento.
- Antes de qualquer comando que altere banco ou reinicie containers, confirmar o projeto Docker, ambiente e banco de destino sem exibir segredos. Se o isolamento não estiver comprovado, não executar a operação.
- Nunca executar testes automatizados contra o banco de produção. A CI usa infraestrutura descartável e não recebe credenciais de produção para testar pull requests.
- Não copiar dados pessoais de produção para homologação ou CI. Usar dados sintéticos.
- Arquivos `.env`, senhas, tokens, cópias de banco e documentos pessoais não entram no Git, nos relatórios públicos ou nos logs. Modelos de configuração contêm apenas exemplos sem credenciais reais.
- Não substituir o `.env` existente. Criar configuração própria para cada destino e verificar que está ignorada pelo Git.

## 5. Testes e GitHub Actions

- Implementar os workflows em `.github/workflows/` e manter os comandos reproduzíveis na documentação.
- Executar a CI em abertura, reabertura e atualização de pull requests destinados à `main`, e em `push` na `main` após o merge. Disponibilizar execução manual quando útil.
- `git pull` não é o gatilho deste fluxo: ele atualiza uma cópia local. O envio ao GitHub e os eventos do pull request acionam as verificações remotas.
- Exigir os checks pertinentes antes do merge, por proteção da branch ou ruleset. Não declarar essa proteção ativa sem conferir sua configuração e disponibilidade no repositório.
- Cobrir testes Python existentes, testes JavaScript pertinentes, migrations em PostgreSQL/pgvector descartável, construção da aplicação e verificações básicas de saúde e persistência conforme o escopo.
- Usar a versão Python do container e dependências de teste declaradas. Não trocar o framework de testes existente apenas para configurar a CI.
- Verificar que os testes esperados realmente rodaram. Uma suíte com casos de integração ignorados por falta de banco não comprova a integração com PostgreSQL.
- Simular respostas de IA nos testes comuns. Não depender de Ollama local, serviços pagos ou credenciais pessoais para aprovar um pull request. Avaliações reais de modelos são separadas e identificadas.
- Usar permissões mínimas nos workflows; não executar código de pull request com credenciais de produção. Nunca enfraquecer checks para obter um resultado verde.
- Executar localmente os testes pertinentes à mudança. Mudanças apenas de texto exigem revisão de conteúdo, links e coerência; mudanças de comportamento exigem testes adequados e regressão quando aplicável.
- Inspecionar `verify.ps1`, `verify-profiles.ps1` e `verify-jobs.ps1` antes de usá-los: podem aplicar migrations e reiniciar serviços. Adaptar e comprovar o isolamento antes de executá-los em paralelo ou na CI.
- Registrar testes aprovados, falhas e verificações não executadas com seus motivos. Não reutilizar relatórios antigos como evidência de uma nova execução.

## 6. Integração, homologação e liberação

Fluxo obrigatório:

`worktree e branch → validação local → envio autorizado → pull request por Vinicius → CI aprovada → revisão e merge por Vinicius → homologação → validação de uso por Vinicius → produção`

- O merge na `main` torna a mudança candidata à homologação; não autoriza publicação automática em produção.
- Identificar a versão homologada pelo commit exato e, quando disponível, pelo artefato ou imagem imutável. Promover esse mesmo conteúdo para produção, alterando somente a configuração do ambiente.
- Registrar versão, commit, resultado da homologação e procedimento de atualização. Tags de versão, como `v0.1.0`, são criadas apenas conforme instrução de Vinicius.
- Não publicar uma versão diferente da homologada. Alterações posteriores exigem nova validação.
- Quando o deployment for automatizado pelo GitHub Actions, separar os destinos `staging` e `production`, restringir acesso às credenciais e impedir publicações concorrentes no mesmo ambiente.
- A configuração de GitHub Environments não cria a infraestrutura por si só. Conferir também onde a aplicação e os bancos estão executando.
- Antes de migrations em produção, ter backup e procedimento de restauração apropriados. Volumes persistentes não substituem backup.
- Planejar compatibilidade e recuperação das migrations. Voltar a imagem da aplicação não desfaz automaticamente alterações do banco.
- Nunca remover volumes com dados de uso. `docker compose down -v` não deve ser usado em homologação ou produção como limpeza de rotina.

## 7. Critério de entrega

Uma implementação está pronta para revisão quando:

- Atende ao objetivo e aos critérios de aceitação combinados, sem mudanças sem relação com a tarefa.
- As verificações pertinentes passaram ou as limitações foram explicitamente informadas, sem declarar como comprovado o que não foi testado.
- O comportamento alterado está documentado e o diff foi revisado quanto a segredos, dados pessoais e arquivos gerados.
- A entrega informa branch e worktree, o que mudou, como foi validado e o que Vinicius deve conferir.
- Há uma sugestão de título e descrição para Vinicius abrir o pull request quando a tarefa envolver integração.

Pronto para revisão não significa integrado, homologado ou publicado. Registrar esses estados separadamente, com evidências.

## 8. Primeira retomada e manutenção destas regras

- Antes de iniciar funcionalidades, inventariar o estado atual, preservar as alterações locais existentes e estabelecer a worktree de trabalho. Não fazer commit automático das alterações anteriores.
- Como este arquivo pode ser inserido manualmente por Vinicius antes do primeiro pull request, garantir sua presença na worktree inicial sem incluir outros arquivos não revisados. A inserção manual inicial é o bootstrap destas regras; as próximas edições seguem o fluxo normal.
- Implementar primeiro o isolamento de execução, os workflows de testes e as proteções possíveis no GitHub, ajustando README e CONTRIBUTING para refletir o fluxo aprovado.
- Enquanto uma regra depender de configuração ainda ausente, registrar a pendência. Não presumir que CI, ambientes ou proteções já existem.
- Manter decisões de produto pendentes como pendentes, inclusive a validação do documento de foco. Essas pendências não impedem preparar a infraestrutura já autorizada.
- Alterar estas regras somente a pedido ou com aprovação explícita de Vinicius. Registrar aqui a data, a decisão e o motivo, mantendo a versão atual como referência única.

### Registro de decisões

| Data | Decisão | Motivo |
| --- | --- | --- |
| 29/10/2026 | Adotar worktrees por tarefa, homologação e produção isoladas, e testes no GitHub Actions. | Retomar o desenvolvimento com validação reproduzível e proteção dos dados. |
| 29/10/2026 | Reservar a abertura de pull request e o merge a Vinicius. | Decisão explícita do responsável pelo projeto. |
