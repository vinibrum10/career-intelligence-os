# Ollama Cloud — conexão do aplicativo

Por solicitação de Vinicius em 29/10/2026, esta integração substitui o transporte local de rascunhos por acesso direto ao Ollama Cloud. A aplicação e o banco continuam locais; somente o texto da vaga é enviado ao provedor quando o usuário pede um rascunho. Perfis não são enviados. Revisão humana e salvamento explícito continuam obrigatórios.

## Código e configuração

`app/ollama_cloud.py` usa o SDK oficial `ollama==0.6.3`, host fixo `https://ollama.com`, modelo `gemma4:31b` e `Authorization: Bearer` com o valor não vazio de `OLLAMA_API_KEY`. Não usa `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ou autenticação do Ollama local. Sem a chave específica, a chamada é bloqueada antes de criar o cliente. Redirecionamentos não são seguidos e os erros do provedor não são expostos integralmente.

O endpoint existente `POST /career/owners/{owner_id}/jobs/{source_id}/snapshots/{version}/extractions/draft`, em `app/jobs/propose.py`, passa a usar esse cliente. Não há nova rota de chat pública. A chave nunca vai para HTML, JavaScript, resposta da API ou logs do aplicativo. A indisponibilidade da IA preserva o fluxo manual.

O Docker Compose recebe a chave do arquivo privado selecionado por `--env-file`, como já faz com a senha do banco. Os modelos `.env.example`, `.env.staging.example` e `.env.production.example` incluem somente `OLLAMA_API_KEY=` vazio. Esses arquivos privados já estão ignorados pelo Git e pelo contexto Docker.

Nesta instalação, use o arquivo privado existente:

`C:/Users/Vinicius/Documents/1.0-Desenvolvimentos_Projetos/8-Career Intelligence OS/.docker-local/environments/.env.staging`

Preencha a linha `OLLAMA_API_KEY=` nesse arquivo com a chave criada em [Ollama API keys](https://ollama.com/settings/keys). Preserve todas as outras linhas e não envie a chave pelo chat. O teste carrega esse arquivo explicitamente, sem precisar carregar o perfil do terminal.

## Teste real com o código do aplicativo

Na raiz da worktree Cloud, com o ambiente virtual preparado:

```powershell
.venv/Scripts/python.exe scripts/test-ollama-cloud.py --env-file "C:/Users/Vinicius/Documents/1.0-Desenvolvimentos_Projetos/8-Career Intelligence OS/.docker-local/environments/.env.staging"
```

O script faz uma única solicitação através de `app.ollama_cloud.chat` e imprime somente a resposta recebida. Não usa curl, não lê perfis e não grava no banco. `python-dotenv` carrega o arquivo informado sem interpolar outras variáveis ou imprimir valores. Uma variável `OLLAMA_API_KEY` já exportada tem precedência sobre o arquivo; remova-a do terminal se estiver vazia ou desatualizada.

- Chave ausente: `Not tested yet`, sem chamada ao provedor.
- HTTP 401: corrigir a chave.
- HTTP 402: adicionar créditos de uso; não repetir automaticamente.
- HTTP 404: conferir o nome do modelo no catálogo do Ollama.
- HTTP 429: limite atingido; parar e aguardar.
- Erro de conexão: conferir a liberação de rede do terminal.

Os testes automáticos usam `httpx.MockTransport` e não fazem chamadas Cloud nem precisam de chave real. Validam host, modelo, header, chave vazia, ausência de fallback, erros sem vazamento e bloqueio de redirecionamentos para outro host.

Esta entrega não publica em produção nem substitui a imagem de homologação automaticamente. A avaliação anterior do modelo local está preservada em outra worktree e não comprova a qualidade do Gemma na nuvem. Ainda é necessário avaliar a extração em vagas reais antes de considerar seus fatos confiáveis.

## Referências lidas antes da implementação

- [Introdução](https://docs.ollama.com/api/introduction.md)
- [Autenticação](https://docs.ollama.com/api/authentication.md)
- [Índice](https://docs.ollama.com/llms.txt)
- [Catálogo oficial de modelos](https://ollama.com/api/tags)

## Verificação realizada

Em 29/10/2026, uma chamada real pelo comando acima e por `app.ollama_cloud.chat` retornou do modelo `gemma4:31b`:

> Mensagem de teste recebida com sucesso.

O teste real terminou com código 0. A chave foi carregada do arquivo privado e não foi exibida. Antes disso, 63 testes passaram em PostgreSQL descartável, incluindo persistência após reinício. Os testes de autenticação e erros usam transporte simulado; somente o teste manual faz a solicitação real.

## Arquivos desta entrega

- `app/ollama_cloud.py`: cliente Cloud somente no servidor.
- `app/jobs/propose.py`: endpoint existente de rascunhos usando o cliente Cloud.
- `scripts/test-ollama-cloud.py`: solicitação real reproduzível, carregando o arquivo privado.
- `requirements.txt`: SDK oficial e carregamento explícito do arquivo de ambiente no teste.
- `compose.yaml`: chave fornecida somente ao serviço do servidor.
- `.env.example`, `.env.staging.example`, `.env.production.example`: nome da chave sem valor.
- `app/web/jobs.html`, `app/web/jobs.js`: aviso do envio à nuvem e tratamento dos erros, sem acesso à chave.
- `tests/test_ollama_cloud.py`, `tests/test_propose.py`, `tests/test_environment_config.cjs`: verificações simuladas e isolamento das configurações.
- `README.md`, `CONTRIBUTING.md`, `docs/job-extractions.md`, `docs/ollama-cloud.md`: instruções atualizadas.

No arquivo privado existente `.env.staging`, foi acrescentada somente a linha vazia da chave; seu preenchimento foi feito pelo usuário. Nenhuma outra linha desse arquivo foi alterada nesta entrega. O envio e a implantação seguem o fluxo de revisão do projeto.
