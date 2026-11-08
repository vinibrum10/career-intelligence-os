# Career Intelligence OS — Documento de foco e direção

**Versão:** 0.2
**Data:** 7 de novembro de 2026
**Status:** fluxo da V1 aceito em homologação. Documento de foco e próximas entregas em revisão.

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

## 5. Situação da V1 em homologação

A homologação usa o commit `3ba6328a779b101db63397499c3a76b587c267a0`. A aplicação e o banco PostgreSQL com pgvector rodam localmente em Docker, em ambiente separado da produção.

| Parte | Situação verificada |
| --- | --- |
| Fluxo manual | Vinicius aceitou o fluxo de perfil configurável, vaga salva, fatos revisados e comparação com justificativas. O teste usou dois perfis fictícios e comprovou a persistência após reiniciar a aplicação e o banco. [CIO-2](https://vinibrum10.atlassian.net/browse/CIO-2) |
| Histórico e comparação | A interface permite consultar a captura original, conferir os trechos e escolher uma versão do perfil, incluindo versões anteriores. |
| Rascunho opcional | Vinicius aceitou o piloto do Ollama Cloud em homologação. Quatro vagas fictícias geraram os 20 fatos esperados com evidência. A adoção com vagas reais depende de avaliar uma amostra rotulada e autorizada. [CIO-3](https://vinibrum10.atlassian.net/browse/CIO-3) |
| Verificações | Os dois checks obrigatórios da main passaram no commit homologado. [Execução da CI](https://github.com/vinibrum10/career-intelligence-os/actions/runs/42432855315) |

## 6. Escopo da etapa atual

1. Criar ou selecionar um perfil e configurar suas restrições e preferências.
2. Salvar manualmente uma descrição de vaga, com origem quando conhecida.
3. Consultar a descrição original e suas capturas anteriores.
4. Cadastrar fatos pelo fluxo manual, que é o padrão de uso da V1. Em homologação, também é possível solicitar um rascunho opcional ao Ollama Cloud.
5. Conferir os fatos contra a descrição salva. Ao usar um rascunho, corrigir ou remover sugestões e confirmar explicitamente antes de salvar.
6. Comparar um conjunto de fatos com uma versão identificada do perfil.
7. Exibir resultado, motivos, evidências, preferências e pendências de confirmação.

O fluxo manual funciona com a IA indisponível. Quando um rascunho é solicitado, o servidor envia ao Ollama Cloud somente o texto da vaga. A comparação é calculada sob consulta; um histórico persistido dos resultados de comparação ainda não está implementado.

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
- Publicação externa, acesso multiusuário, autenticação e novos serviços externos. O Ollama Cloud é o recurso opcional de rascunho já integrado.
- Reformulações amplas de interface ou infraestrutura sem necessidade demonstrada para concluir o fluxo atual.

Esses itens podem ser avaliados depois, com objetivo e critérios próprios. A existência de Agno e pgvector na infraestrutura não torna seu uso uma prioridade por si só.

## 9. Critérios para concluir a etapa atual

- [x] O fluxo completo funciona na interface, usando dados fictícios de teste.
- [x] Dois perfis com restrições diferentes produzem resultados coerentes para a mesma vaga, com justificativas.
- [x] Alterar o perfil permite obter uma nova comparação usando a versão escolhida.
- [x] Fatos e evidências podem ser conferidos contra a captura exata utilizada.
- [x] Informação ausente ou conflitante aparece como pendência de confirmação quando impede uma conclusão.
- [x] Trabalho remoto restrito a um país não é interpretado como remoto mundial.
- [x] Preferências opcionais não eliminam uma vaga e caminhos alternativos são respeitados.
- [x] A indisponibilidade do Ollama permite continuar pelo cadastro manual de fatos.
- [x] Os registros persistem após reiniciar a aplicação e o banco, sem misturar espaços de proprietários diferentes.
- [ ] As verificações pertinentes passam e a documentação corresponde ao comportamento entregue.
- [ ] As alterações são revisadas e o resultado é apresentado a Vinicius para validação de uso.

## 10. Próximos passos da V1

| Entrega | Situação |
| --- | --- |
| Homologar o fluxo manual e a escolha de versões | Aceito por Vinicius no [CIO-2](https://vinibrum10.atlassian.net/browse/CIO-2). |
| Avaliar os rascunhos com dados fictícios | Piloto aceito por Vinicius no [CIO-3](https://vinibrum10.atlassian.net/browse/CIO-3). |
| Alinhar a documentação à entrega | Em revisão no [CIO-6](https://vinibrum10.atlassian.net/browse/CIO-6). |
| Encerrar a V1 | Registrar a decisão de liberação local e escolher ou adiar a próxima entrega no [CIO-4](https://vinibrum10.atlassian.net/browse/CIO-4). |

Possíveis evoluções incluem análise de habilidades recorrentes na amostra, registro de experiência e habilidades pessoais, avaliação de lacunas e histórico de comparações. A prioridade entre elas permanece aberta.

## 11. Regra para evitar perda de foco

Antes de incluir uma nova tarefa, responder:

1. Qual problema concreto do usuário ela resolve?
2. Ela é necessária para concluir a etapa atual?
3. Como vamos comprovar que foi entregue corretamente?

Se a tarefa não for necessária agora, registrá-la como possibilidade futura. Mudanças de direção devem atualizar este documento com a decisão, o motivo e o impacto no escopo.

Ao retomar o projeto, consultar este documento, conferir o estado real da aplicação e escolher a próxima tarefa pendente. Uma etapa só deve ser marcada como concluída com evidência de validação.

## 12. Pontos para validação de Vinicius

- O objetivo da seção 3 representa o produto que queremos construir?
- Os limites da seção 8 preservam o foco desejado para esta etapa?
- Existe algum resultado essencial que deveria entrar nos critérios de conclusão?

A aprovação da direção mais ampla e a escolha de próximas entregas continuam abertas.

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
| 28/10/2026 | Criação deste documento com foco proposto na conclusão e validação do fluxo local de comparação. | Proposta inicial. |
| 07/11/2026 | Aceite do fluxo manual em homologação e do piloto do Ollama Cloud com vagas fictícias. | Fluxo manual validado para a V1. Avaliação com vagas reais pendente antes da adoção da IA. |
