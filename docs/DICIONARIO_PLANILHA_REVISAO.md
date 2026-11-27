# Dicionário da planilha de revisão (`revisao-pendente.xlsx`)

Explica cada coluna da primeira linha (cabeçalho): de onde vem o dado, como o sistema o extrai do Diário Oficial e o que a revisora faz com ele. Cada linha da planilha é **uma decisão sobre um servidor** dentro de uma resenha.

## Parte 1 — colunas preenchidas pelo sistema (não alterar)

| Coluna | O que significa | Como o sistema obtém | Exemplo (fictício) |
|---|---|---|---|
| **ID_Decisao** | Código único da decisão no banco. É a "chave" da linha | Gerado a partir do PDF (SHA-256), da página e da posição da decisão. Nunca muda | `c161716de29aedf3f4a1` |
| **Impressao_Digital** | Selo de versão da linha. Se a decisão mudar no banco depois que a planilha foi gerada, o selo não confere e a linha é recusada (evita sobrescrever algo mais novo) | Calculado com processo, nome, matrícula, resultado e estado de conferência | `4e1a9b0c2d7f3a11` |
| **Motivo_Alerta** | Por que vale conferir esta linha. Vazio = nenhuma regra disparou (não quer dizer que está certo) | Regras de consistência: processo ou matrícula ausente ou fora do padrão, nome com números, resultado não informado, grupo/modalidade/serviço pendente, página lida por OCR, possível duplicidade, conflito aberto, pendência do classificador | `página lida por OCR; grupo pendente` |
| **Data_Publicacao** | Data da edição do DOE em que a decisão saiu | Data da edição na listagem oficial da A União | `2026-10-09` |
| **ID_Resenha** | Ato que contém a decisão (resenha ou portaria) e seu número | Lido no cabeçalho do ato ("RESENHA Nº 551/2026") | `Resenha 551/2026` |
| **Pagina_PDF** | Página do PDF onde a decisão está | Página em que a linha foi lida | `5` |
| **Link_PDF_Oficial** | Endereço do PDF oficial, já abrindo na página | URL oficial da A União + `#page=` | `https://auniao.pb.gov.br/...pdf#page=5` |
| **Eixo** | Grande área da GEDIV | Classificador, pelo assunto do ato: **Progressão Funcional** ou **Tempo de Serviço/Contribuição** | `Progressão Funcional` |
| **Modalidade_Progressao** | Tipo de progressão (só no eixo Progressão) | Texto do ato: "PROGRESSÃO FUNCIONAL VERTICAL/HORIZONTAL" | `Vertical` |
| **Grupo_Ocupacional** | Grupo do servidor (só no eixo Progressão) | Catálogo de grupos da GEDIV aplicado ao texto do ato. Sem regra homologada, fica "Não informado" | `AST · Apoio Técnico` |
| **Servico_Tempo_Servico** | Tipo de serviço (só no eixo Tempo de Serviço) | Catálogo TS-01 a TS-xx aplicado ao assunto | `TS-04 · Licença para Tratar de Interesses Particulares` |
| **Numero_Processo** | Processo administrativo da decisão | Padrão `ÓRGÃO-PSE/PRC/OFI-ANO/NÚMERO` na linha da tabela | `SAD-PSE-2026/90301` |
| **Servidor** | Nome do servidor, como publicado | Texto da linha da tabela | `PESSOA FICTÍCIA DA SILVA` |
| **Matricula** | Matrícula do servidor | Número na linha da tabela | `123.456-7` |
| **Resultado** | O que foi decidido | Cabeçalho do bloco ("DEFERIU"/"INDEFERIU") ou a própria linha | `Deferido` |

## Parte 2 — colunas preenchidas pela revisora

| Coluna | O que preencher | Obrigatório? |
|---|---|---|
| **Acao** | `Confirmar` (está certo), `Corrigir` (um campo errado) ou `Rejeitar` (não é da GEDIV, ou é lixo de leitura) | Sim, para a linha ser aplicada |
| **Consultei_PDF** | `SIM`, declarando que conferiu no PDF oficial | Sim, para Confirmar e Corrigir |
| **Campo_Corrigido** | Qual campo está errado: `Processo`, `Servidor`, `Matricula` ou `Resultado` | Só em Corrigir |
| **Valor_Corrigido** | O valor certo, como está no PDF | Só em Corrigir |
| **Justificativa** | Motivo, com 5 letras ou mais (ex.: "conferido no PDF") | Recomendado; vazio vira "conferido pela planilha de revisão" |

## O que acontece depois

1. A coleta seguinte (09h04 ou 14h04), ou o comando `aplicar-revisao`, aplica as linhas preenchidas, com o nome da revisora, a data e o motivo na trilha de auditoria.
2. Sai um relatório `revisao-relatorio-*.csv` com cada linha **aplicada** ou **recusada**, e o motivo.
3. A planilha aplicada vai para `revisao/processados/` e uma nova é gerada só com o que continua pendente.

## Observações

- Colunas extras que a revisora criar são ignoradas: não vão para o banco nem para o painel.
- Eixo, modalidade, grupo e serviço **não são corrigidos pela planilha**: dependem das regras da GEDIV (homologação). A correção deles é feita pela tela do painel ou por uma nova versão das regras.
- Republicações (14 resenhas, 119 decisões) não aparecem aqui: o painel conta só a publicação original.
