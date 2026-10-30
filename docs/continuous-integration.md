# Testes antes do pull request

O workflow `CI`, em `.github/workflows/ci.yml`, roda ao enviar commits para `codex/**` ou `main`, e ao abrir, reabrir ou atualizar um pull request destinado à `main`. Não é necessário abrir um PR para testar uma branch `codex/`. Cada envio testa o commit enviado; não comprova alterações que ficaram apenas no computador.

## Como acompanhar

1. Trabalhe em uma worktree e branch `codex/descricao-da-tarefa`.
2. Faça as verificações locais e envie o commit da branch quando autorizado.
3. Abra [Actions do projeto](https://github.com/vinibrum10/career-intelligence-os/actions), escolha a execução `CI` e confira branch e commit.
4. Aguarde os dois jobs: `Python, JavaScript and scripts` e `PostgreSQL, migrations and restart persistence`.
5. Se falhar, abra a etapa vermelha, corrija na mesma branch e envie outro commit. A nova execução deve passar antes de Vinicius abrir o PR.
6. Vinicius abre o pull request para `main`; a CI roda novamente no contexto do PR. Vinicius revisa e faz o merge.

O botão **Run workflow** permite escolher uma branch para executar manualmente depois que o workflow estiver integrado à `main`. Enviar o próprio workflow em uma branch `codex/` já permite sua primeira execução por `push`, antes do PR.

## O que é verificado

- Python 3.12, como no container, com as dependências de `requirements-test.txt`.
- Testes Python descobertos em `tests/test_*.py`. O job rápido usa SQLite e pode ignorar testes exclusivos de PostgreSQL; o job de integração exige testes executados e nenhum teste ignorado.
- Sintaxe dos arquivos JavaScript e casos de regressão `tests/test_*.cjs` presentes no commit.
- Scripts de regressão `tests/test_*.ps1` presentes no commit, sem executar os scripts de manutenção da instalação local.
- Construção da aplicação, migrations em banco vazio, PostgreSQL 17/pgvector, API saudável e persistência dos registros sintéticos após reiniciar banco e aplicação.
- As suítes e provas de persistência são descobertas automaticamente, incluindo as de vagas e extrações quando esses arquivos estiverem integrados à branch.

A CI não faz revisão semântica completa do código, avaliação real do Ollama, teste visual do fluxo inteiro nem publicação. Os testes comuns de IA usam respostas simuladas quando presentes. Aprovação dos testes não substitui revisão e homologação.

## Isolamento e reprodução

`compose.ci.yaml` é uma configuração independente: não combina com `compose.yaml`, não publica portas no computador, não lê o `.env` local e não utiliza bancos ou volumes de uso. O nome do banco é `career_profile_test_ci`; as credenciais declaradas são públicas e descartáveis, exclusivas desta infraestrutura de teste.

A execução usa um projeto Docker `career-ci-<id>-<tentativa>`, com rede e volume próprios. O script recusa nomes que já tenham containers ou volumes. Ao terminar, remove somente os recursos desse projeto CI, inclusive quando um teste falha. Não execute este procedimento com configurações de homologação ou produção.

Para reproduzir em uma worktree, com Docker Desktop em execução e PowerShell:

```powershell
./scripts/verify-ci.ps1 -ProjectName ("career-ci-local-" + [guid]::NewGuid().ToString('N'))
```

Para os testes Python rápidos, dentro de um ambiente virtual:

```powershell
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -t . -v
```

O estágio `test` do Dockerfile inclui dependências de teste; o estágio final `runtime` continua sendo o padrão da aplicação. Os scripts `verify.ps1`, `verify-profiles.ps1` e `verify-jobs.ps1` não são chamados pela CI, pois podem alterar e reiniciar a instalação de uso.

## Proteção do merge

Depois da primeira execução, o administrador deve configurar um ruleset ou proteção da `main` exigindo os dois checks acima. A presença do workflow não ativa essa proteção automaticamente. Enquanto a proteção não for conferida, tratar o bloqueio de merge como pendente.

Este workflow tem apenas permissão de leitura do repositório e não usa segredos de produção. As actions estão fixadas por commit; as dependências Python auxiliares e a imagem pgvector ainda usam intervalos/tags, portanto não há garantia de reprodução binária entre datas diferentes.
