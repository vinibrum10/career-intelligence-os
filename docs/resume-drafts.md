# Currículo em português com IA

Entrega do CIO-10. O uso exige uma versão que inclua esta funcionalidade e a configuração do Ollama Cloud no servidor. As evidências de integração, homologação, liberação e aceite de uso são registradas no [cartão do projeto](https://vinibrum10.atlassian.net/browse/CIO-10).

## Uso

Abra uma entrevista profissional salva e clique em **Criar currículo com IA**. O link identifica o espaço e o registro exato: confira a data para escolher o perfil corrigido mais recente, quando houver.

Na página do currículo, confira os fatos e marque a autorização de envio ao **Ollama Cloud**. **Gerar rascunho em português** produz um resumo e uma seção por tema confirmado. A tela apresenta o texto editável e as fontes de cada trecho. Temas sem fatos aparecem como pendências. Nenhuma informação ausente é preenchida automaticamente pelo sistema.

Preencha o nome, os contatos desejados e os complementos de datas, formação ou idiomas. Esses campos são locais e não são enviados ao modelo. Confira o texto contra as fontes e marque a confirmação de revisão. Uma alteração posterior exige nova confirmação. **Baixar texto** gera um `.txt`. **Baixar versão para impressão** gera um HTML independente; abra-o no navegador e use **Imprimir → Salvar como PDF** para obter um PDF.

O rascunho fica apenas na página aberta: atualizar ou sair perde a edição ainda não baixada. Os arquivos baixados são a forma de guardar o currículo nesta entrega. O perfil de origem e seus registros anteriores permanecem intactos. Não há salvamento automático nem tabela nova de currículos.

## Fluxo de dados autorizado

Em 13/11/2026, Vinicius autorizou o uso de Ollama Cloud com os fatos profissionais confirmados. Essa é uma nova finalidade de uso do provedor, além do rascunho de vagas existente.

`POST /career/owners/{owner_id}/interviews/{interview_id}/resume-draft` exige corpo `{"consent": true}`. O servidor carrega a entrevista no espaço correspondente e envia ao cliente Cloud apenas `{"facts": {...}}`. Respostas originais, temas excluídos, preferências de busca, identificadores do espaço e da entrevista e metadados do documento ficam fora da solicitação. O texto de um fato confirmado pode conter informações pessoais inseridas pelo usuário; por isso os fatos completos são mostrados antes da autorização.

O cliente já existente usa somente `OLLAMA_API_KEY`, host `https://ollama.com`, modelo `gemma4:31b`, sem redirecionamentos ou fallback de credenciais. A chave fica somente no servidor. Não há novas dependências nem outro serviço. Cada tentativa do usuário faz uma solicitação, sem repetição automática.

## Fontes, limites e revisão

O servidor aceita JSON com resumo e seções. Exige fontes existentes e não repetidas, exatamente uma seção por tema confirmado e referências ao próprio tema em cada seção. Números escritos com algarismos devem aparecer nas fontes citadas; períodos de experiência ou outras métricas não são calculados automaticamente. O tamanho de entrada é limitado a 12.000 caracteres de fatos e o de resposta a 60.000 caracteres.

Essas verificações não comprovam a precisão semântica ou a fidelidade de cada frase. O modelo ainda pode exagerar uma responsabilidade, interpretar mal um fato ou escrever uma afirmação inadequada. A revisão humana contra as fontes é obrigatória. A confirmação é invalidada quando o documento muda.

Conteúdo de perfil e de modelo entra na tela como texto. A exportação HTML escapa os campos, não inclui scripts ou recursos externos e aplica uma política que bloqueia conteúdo ativo. O documento exportado contém o texto revisado, sem incluir os identificadores internos ou a lista de fontes.

## Validação e operação

Os testes simulam a IA: consentimento, isolamento entre espaços, envio exclusivo dos fatos confirmados, preservação do perfil, formato, fontes, números e erros controlados. Testes JavaScript cobrem a revisão e a exportação. Avaliações reais do modelo usam dados fictícios apropriados, fora da suíte de aprovação e sem registros de produção.

Em 13/11/2026, foram avaliados dois perfis fictícios pelo cliente real do aplicativo com `gemma4:31b`: um com os quatro temas confirmados e outro apenas com experiência. Ambos passaram pelas verificações de formato, fontes e números. Na conferência da redação contra a amostra, não foram acrescentados datas, formação, empregadores ou métricas ausentes. Essa amostra pequena não substitui a revisão de cada currículo gerado. A primeira tentativa havia retornado HTTP 402; após Vinicius liberar créditos da conta, a avaliação foi repetida com sucesso.

Não há migração nova. A configuração do ambiente deve fornecer `OLLAMA_API_KEY`; sem ela o servidor retorna uma orientação controlada e preserva o perfil. A liberação segue o mesmo fluxo de revisão, integração, CI, homologação e produção do projeto.

Currículo em inglês, adaptação a uma vaga, DOCX, envio de candidaturas e persistência de currículos no banco ficam fora desta entrega.
