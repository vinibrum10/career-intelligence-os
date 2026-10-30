# Career Intelligence OS — Documento de foco e direção

**Versão:** 0.1
**Data:** 28 de outubro de 2026
**Status:** proposta para validação de Vinicius

## 1. Para que este documento existe

Manter uma direção clara para o projeto: qual problema estamos resolvendo, o que precisamos entregar agora e o que deve esperar. Este documento será a referência de foco nas próximas retomadas, após sua validação.

Ele resume a direção do produto. Os requisitos detalhados e as regras implementadas continuam nos documentos técnicos indicados ao final. Uma funcionalidade descrita como futura não deve ser tratada como disponível.

## 2. Problema que queremos resolver

Descrições de vagas e preferências profissionais ficam dispersas, dificultando comparar oportunidades de forma consistente. Informações como local de trabalho, contrato, remuneração, patrocínio e requisitos podem estar ausentes, ambíguas ou contraditórias.

O Career Intelligence OS deve ajudar a organizar essas informações e apoiar decisões de carreira com evidências verificáveis, deixando claro o que sabemos e o que ainda precisa ser confirmado.

## 3. Objetivo do produto

**Transformar descrições de vagas e preferências pessoais em comparações claras, rastreáveis e úteis para decidir quais oportunidades merecem investigação.**

A direção de evolução é permitir também a análise de requisitos recorrentes nas vagas fornecidas e, quando houver evidências suficientes sobre a pessoa, apoiar a identificação de lacunas de desenvolvimento.

O produto deve aceitar diferentes perfis e caminhos profissionais. Nenhum cargo, país, moeda ou preferência particular será fixado como objetivo universal do sistema. A escolha de carreira e as decisões de candidatura continuam com a pessoa.

## 4. Foco imediato

**Concluir e validar o fluxo local: perfil → vaga salva → fatos revisados → comparação de elegibilidade com justificativas e evidências.**

Ao final desta etapa, a pessoa deve conseguir responder:

- Esta vaga atende às restrições que configurei?
- Quais informações da descrição sustentam a comparação?
- Quais condições entram em conflito com meu perfil?
- O que ainda preciso confirmar sobre a vaga?

Elegibilidade significa compatibilidade com os critérios efetivamente avaliados pelo sistema. Aderência técnica, autorização legal para trabalhar e probabilidade de contratação exigem outras evidências e não fazem parte dessa conclusão.

## 5. Situação na retomada

Levantamento realizado em 28 de outubro de 2026 a partir do repositório local:

| Parte | Situação identificada |
| --- | --- |
| Infraestrutura local | Aplicação e PostgreSQL com pgvector configurados em Docker, com validações anteriores documentadas. |
| Perfis | Cadastro e edição com histórico de preferências. |
| Vagas | Captura manual do texto original e da origem, com histórico. |
| Fatos da vaga | Estrutura para registrar fatos e seus trechos de evidência, preservando versões. |
| Comparação | Regras de elegibilidade implementadas para parte dos critérios do perfil. |
| Rascunho por IA | Integração opcional com Ollama local; sugestões precisam de revisão humana antes de serem salvas. |
| Interface do fluxo completo | Alterações locais em sete arquivos, ainda não registradas em commit; precisam de revisão e validação antes de considerar a etapa concluída. |
| Funcionamento nesta retomada | Ainda não confirmado: o serviço do Docker estava indisponível na consulta. |

As validações anteriores não comprovam o funcionamento das alterações locais atuais. A qualidade do rascunho no modelo real também precisa de avaliação própria: respostas simuladas em testes não comprovam a interpretação correta de vagas reais.

## 6. Escopo da etapa atual

1. Criar ou selecionar um perfil e configurar suas restrições e preferências.
2. Salvar manualmente uma descrição de vaga, com origem quando conhecida.
3. Consultar a descrição original e suas capturas anteriores.
4. Cadastrar fatos manualmente ou solicitar um rascunho ao Ollama local.
5. Conferir, corrigir ou remover sugestões e salvar os fatos revisados.
6. Comparar um conjunto de fatos com uma versão identificada do perfil.
7. Exibir resultado, motivos, evidências, preferências e pendências de confirmação.

O fluxo manual precisa funcionar mesmo quando a IA estiver indisponível. A comparação é calculada sob consulta; um histórico persistido dos resultados de comparação ainda não está implementado.

## 7. Princípios que devem orientar as decisões

- **Evidência rastreável:** cada fato explícito deve apontar para um trecho da descrição salva.
- **Incerteza visível:** informação ausente, ambígua ou conflitante deve permanecer identificada.
- **Revisão humana:** um rascunho de IA só vira fato salvo após conferência e confirmação.
- **Preferências configuráveis:** alterações de objetivo pessoal devem ser feitas no perfil, sem mudar o código.
- **Critérios separados:** restrições obrigatórias, preferências e aderência técnica devem aparecer separadamente.
- **Alternativas preservadas:** caminhos aceitos pelo perfil, como remoto ou mudança com patrocínio, devem ser avaliados como alternativas.
- **Histórico preservado:** novas capturas, preferências e extrações não devem apagar as versões anteriores.
- **Dados privados protegidos:** perfis reais, documentos pessoais e credenciais devem ficar fora do repositório público.
- **Uso local nesta etapa:** manter o acesso no próprio computador; o identificador do espaço não oferece autenticação.
- **Conclusões proporcionais:** poucas vagas representam a amostra analisada, sem comprovar a demanda de todo o mercado.

## 8. O que fica fora do foco imediato

- Coleta automática de vagas em plataformas como LinkedIn.
- Candidaturas automáticas e contato com recrutadores.
- Recomendação automática de uma carreira ou estimativa de chance de contratação.
- Avaliação de aderência técnica sem histórico documentado de habilidades e experiência.
- Agentes autônomos, RAG e busca por embeddings.
- Publicação para múltiplos usuários, autenticação e serviços pagos ou em nuvem.
- Reformulações amplas de interface ou infraestrutura sem necessidade demonstrada para concluir o fluxo atual.

Esses itens podem ser avaliados depois, com objetivo e critérios próprios. A existência de Agno e pgvector na infraestrutura não torna seu uso uma prioridade por si só.

## 9. Critérios para concluir a etapa atual

- [ ] O fluxo completo funciona na interface, usando dados fictícios de teste.
- [ ] Dois perfis com restrições diferentes produzem resultados coerentes para a mesma vaga, com justificativas.
- [ ] Alterar o perfil permite obter uma nova comparação usando a versão escolhida.
- [ ] Fatos e evidências podem ser conferidos contra a captura exata utilizada.
- [ ] Informação ausente ou conflitante aparece como pendência de confirmação quando impede uma conclusão.
- [ ] Trabalho remoto restrito a um país não é interpretado como remoto mundial.
- [ ] Preferências opcionais não eliminam uma vaga e caminhos alternativos são respeitados.
- [ ] A indisponibilidade do Ollama permite continuar pelo cadastro manual de fatos.
- [ ] Os registros persistem após reiniciar a aplicação e o banco, sem misturar espaços de proprietários diferentes.
- [ ] As verificações pertinentes passam e a documentação corresponde ao comportamento entregue.
- [ ] As alterações são revisadas e o resultado é apresentado a Vinicius para validação de uso.

## 10. Ordem proposta para os próximos passos

| Ordem | Entrega | Condição para avançar |
| --- | --- | --- |
| 1 | Validar este documento de foco. | Vinicius confirma a direção ou solicita ajustes. |
| 2 | Revisar e validar as alterações atuais da interface, corrigindo problemas do fluxo. | Critérios da seção 9 atendidos e resultado apresentado para validação. |
| 3 | Avaliar o rascunho do Ollama em uma pequena amostra de vagas conferidas manualmente. | Registrar erros de interpretação, omissões e fatos sem suporte; definir um nível aceitável antes de considerar o recurso confiável. |
| 4 | Definir a próxima entrega com base no uso do fluxo validado. | Escolher um problema prioritário e seus critérios de aceitação. |

Possíveis evoluções para a ordem 4 incluem análise de habilidades recorrentes na amostra, registro de experiência e habilidades pessoais, avaliação de lacunas e histórico de comparações. A prioridade entre elas permanece aberta para decisão; nenhuma está incluída automaticamente na etapa atual.

## 11. Regra para evitar perda de foco

Antes de incluir uma nova tarefa, responder:

1. Qual problema concreto do usuário ela resolve?
2. Ela é necessária para concluir a etapa atual?
3. Como vamos comprovar que foi entregue corretamente?

Se a tarefa não for necessária agora, registrá-la como possibilidade futura. Mudanças de direção devem atualizar este documento com a decisão, o motivo e o impacto no escopo.

Ao retomar o projeto, consultar este documento, conferir o estado real da aplicação e escolher a próxima tarefa pendente. Uma etapa só deve ser marcada como concluída com evidência de validação.

## 12. Pontos para validação de Vinicius

- O objetivo da seção 3 representa o produto que queremos construir?
- Concluir o fluxo local de comparação é a prioridade imediata correta?
- Os limites da seção 8 preservam o foco desejado para esta etapa?
- Existe algum resultado essencial que deveria entrar nos critérios de conclusão?

Até essa validação, a direção e a sequência propostas neste documento permanecem como rascunho.

## 13. Referências do projeto

- [Visão geral e instalação](README.md)
- [Requisitos do produto](docs/product-requirements.md)
- [Fatos, regras de elegibilidade e rascunho por IA](docs/job-extractions.md)
- [Capturas de vagas](docs/job-captures.md)
- [Perfis e preferências](docs/profile-api.md)
- [Proposta de modelo de dados](docs/data-model-design.md) — contém intenções de evolução que devem ser conferidas contra a implementação atual.

## 14. Registro de decisões

| Data | Registro | Situação |
| --- | --- | --- |
| 28/10/2026 | Criação deste documento com foco proposto na conclusão e validação do fluxo local de comparação. | Aguardando validação de Vinicius. |
