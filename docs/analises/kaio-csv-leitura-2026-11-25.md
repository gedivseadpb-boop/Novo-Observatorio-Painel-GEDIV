# Análise: projeto do Kaio, CSV canônico e leitura dos dados (25/11/2026)

Fontes lidas: conversa do ChatGPT "Brainstorm estratégico colaborativo" (mensagens 37 a 157), repositório `kaiooeduardoo/cursoesafi` (cópia local), base em CSV de 18/11/2026 no Drive (`extrator.py`, `montar_base.py`, `resenhas.csv`, `decisoes.csv`, `eventos_alteracao.csv`, `cobertura_pdfs.csv`, `INDICE_GEDIV_por_edicao_2026.csv`), lidos por cabeçalho e trechos, e o código deste repositório.

## 1. Projeto do Kaio (Observatório DOE Brasil, `cursoesafi`)
- O projeto é um **método de extração**, e não um robô. O PDF é lido no ChatGPT, que segue `CRITERIOS_EXTRACAO.md` v3.0. O resultado é uma planilha de 6 abas, que alguém importa à mão num painel estático (o Excel é lido no próprio navegador).
- Tem três ideias que valem para a GEDIV:
  - **duas passagens**: a passagem A localiza os candidatos em todas as páginas; a passagem B relê só os candidatos e reconcilia as contagens;
  - **"ausência de resultado não é ausência de leitura"**: o projeto registra as páginas examinadas e justifica cada exclusão;
  - **arquivo de dados como contrato**: o painel não depende de servidor.
- Limites:
  - depende do ChatGPT e de importação manual;
  - não coleta nada sozinho;
  - o importador lê só 2 das 6 abas exigidas;
  - o README não concede licença de reúso do código. Por isso, usar apenas os conceitos.
- Já existe aqui: cobertura por edição (edição sem ocorrência é diferente de edição não lida), pendências, vínculo de retificações e exportação para CSV e XLSX com proteção contra fórmulas (`observatorio/painel/exportacao.py`).

## 2. CSV canônico
- **Tamanho:** a base real de jan–nov/2026 cabe em poucos MB (`decisoes.csv` tem 1,3 MB e `resenhas.csv` 0,5 MB). O ChatGPT mediu o mesmo com dados fictícios: 30 mil registros ocupam 12 MB em CSV, 2,2 MB em XLSX e 0,9 MB em CSV compactado.
- **O que o CSV resolve: a persistência.** O histórico sem PDFs, versionado em Git, sobrevive à máquina que coleta, mostra no histórico do Git cada mudança linha a linha e é restaurável.
- **O que o CSV não resolve: a obtenção dos PDFs.** O download continua exigindo uma máquina no Brasil.
- **Dados pessoais:** `decisoes.csv` tem nome e matrícula. Ele **nunca** pode ir para este repositório, que é público. Cabe num repositório **privado** (o `GPT-NOVO-REPOSITORIO` já é privado e pode ser reaproveitado como cofre de dados, sem criar outro). O índice por edição não tem dados pessoais e pode ser público.
- **Recomendação técnica:** manter o SQLite como motor (transações, revisão auditada, versões) e publicar, a cada execução, um **espelho CSV canônico**:
  - ordenação determinística, uma tabela por arquivo, mês a mês;
  - gravado no repositório privado;
  - com um comando de reconstrução (CSV → SQLite) para restaurar.
  - O Excel continua sendo só formato de distribuição.

## 3. Leitura dos dados

| | Extrator de 18/11 (Cowork/ChatGPT) | Motor deste repositório |
|---|---|---|
| Leitura | `pdftotext -raw` + expressões regulares | pdfplumber por colunas + OCR Tesseract `por` quando necessário |
| Classificação | Marcadores (RESENHA, DEREH/GS, listas de exclusão) | Catálogo GEDIV versionado, homologações e regras auditáveis |
| Vínculo com a GEDIV | Muitas vezes "por inferência (sem cabeçalho explícito)" | Exige evidência; sem homologação, o ato fica pendente |
| Conferência | Toda linha marcada `precisa_conferencia = sim` | Conjunto-ouro 5/5; e2e com 11 PDFs oficiais (229 decisões) |
| Cobertura | `cobertura_pdfs.csv` e índice por edição | Tabelas de publicação, arquivo e página, com SHA-256 |

- O extrator de 18/11 foi rápido e cobriu o ano inteiro porque rodou no Brasil. A leitura dele, porém, é menos rigorosa.
- Por decisão da responsável, a aquisição é refeita do zero, sem unir bases antigas. A base de 18/11 serve, no máximo, como **referência de comparação** (quantas resenhas por edição), nunca como fonte.

## 4. Conclusão
1. O gargalo continua sendo **baixar do Brasil**. Kaio, CSV e Excel não mudam isso.
2. A ideia do CSV é boa para **guardar o histórico sem servidor**: espelho canônico num repositório privado, com o SQLite como motor.
3. Do Kaio, incorporar a **disciplina de duas passagens e de cobertura** como regra escrita da GEDIV, adaptada a progressões e tempo de serviço.
