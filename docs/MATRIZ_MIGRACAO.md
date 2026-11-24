# Matriz de migração para o repositório-mãe

Princípio: **transferir conquistas comprovadas, não desorganização**. Cada componente tem origem, evidência, decisão e destino. A procedência arquivo a arquivo (commit de origem, blob Git e SHA-256) está em `docs/migracao/MANIFESTO_PROCEDENCIA.json`.

Base migrada: `Observat-rio-GEDIV-CLAUDE` `main` `d9be033` + PR #22 (`7b36d1d`, OCR `OF1`→`OFI`) + `feat/exclusao-atos-normativos` (`92103b7`). As duas branches foram integradas sem conflito.

| Componente | Origem | Evidência que sustenta | Decisão | Destino |
|---|---|---|---|---|
| Descoberta do DOE (índice recente, acervo mensal, paginação, suplemento/extra) | Claude `coleta/fontes.py` | Testes de rede simulada; dossiê 24/11 §06 | **MANTER** | `observatorio/coleta/` |
| Transporte, guarda de acesso, suspensão auditada | Claude `coleta/coletor.py`, `nucleo/rede.py` | Testes; F-02 e F-03 abertos nas auditorias | **ADAPTAR**: F-02 (robots por URL e por redirecionamento) e F-03 (reverificação delimitada) corrigidos | mesmo módulo |
| Leitura por colunas + OCR Tesseract `por` seletivo | Claude `leitura/` + PR #22 | Conjunto-ouro oficial **5/5** neste repositório (24/11/2026, Linux, Tesseract 5.3.4) | **MANTER** | `observatorio/leitura/` |
| Classificação GEDIV (Vertical A–F, Horizontal, TS-01..07, Abono) | Claude `gerencias/gediv` | 706 testes; conjunto-ouro | **ADAPTAR**: F-11 (homologação explícita de `TEC. ADM`/`STF`), exclusão de normativos integrada | `observatorio/gerencias/gediv/` |
| Banco relacional SQLite v9 + acervo SHA-256 | Claude `nucleo/banco.py` | Testes de integridade, migrações, versões | **ADAPTAR**: F-01 (uma decisão vigente por cadeia de versões) | `observatorio/nucleo/` |
| Revisão auditada | Claude `revisao/servico.py` | Testes de trilha e conflitos | **MANTER** | `observatorio/revisao/` |
| Painel Unificado "Delicadeza Visual" (7 abas, filtros, gráficos, calendário, exportações, 240 cores) | Claude `web/unificado` | `index.html` gerado aqui é **idêntico byte a byte** à prévia publicada (SHA-256 `d19296173dcbe3ba…`); a11y em Chromium com 9 verificações e 0 estouro em 1440/768/390 px | **MANTER sem alterações visuais** | `observatorio/web/unificado/` |
| API por perfil (Público, Gerência, Administração) | Claude `web/servidor.py`, `contas.py` | Testes HTTP | **ADAPTAR**: F-04, F-05, F-10, A-10 | `observatorio/web/` |
| Snapshot público | Claude `painel/indicadores.py` | Testes de privacidade (k ≥ 5) | **ADAPTAR**: candidato → promoção auditada → revogação 503 (F-04) | `observatorio/operacao/snapshot.py` |
| Rotina diária + timer `systemd` 09h/14h | Claude `deploy_autonomo/` | Testes de agenda e feriados | **ADAPTAR**: candidato em vez de publicação; reverificação; backup cifrado | `deploy_autonomo/` |
| Backup e restauração | V2 (princípio de conjunto cifrado) + Claude (cópia SQLite) | `tests/test_backup_cifrado.py` | **DESENVOLVER**: AES-256-GCM em blocos, manifesto, restauração só em pasta nova | `observatorio/operacao/backup.py` |
| Automação na nuvem | — | Execuções do GitHub Actions | **DESENVOLVER**: `coleta-diaria.yml` (runner configurável), `pages.yml` | `.github/workflows/` |
| Prévia pública estática | `gediv-painel-unificado-previa` | Gerada do código deste repositório | **SUBSTITUÍDA** por `pages.yml` (mesmo conteúdo, sem repositório separado) | GitHub Pages do repositório-mãe |
| Interfaces legadas `painel-publico/`, `painel-v2/`, `revisao-2910/` e testes exclusivos delas | Claude | Superadas pelo Painel Unificado | **DESCARTAR** (preservadas no bundle e no repositório antigo) | — |
| Gerador estático legado `painel/publicacao.py` | Claude | F-08: recusa o esquema v9 | **DESCARTAR** | — |
| Checkpoints JSON como banco | V2 `estado_sqlite.py` | Sem integridade relacional | **DESCARTAR** como persistência | — |
| Reconferência/OCR regional do V2 | V2 `ocr_regional.py`, `reconferencia.py`; patch do Drive de 24/11 | O leitor atual já recupera 488/504 e fecha 5/5 sem ele | **NÃO MIGRADO** (Pareto: ganho não demonstrado) | — |
| Gateway Gemini, `robo-gediv-pb` | Gemini / PB | Experimentos dependentes de outro backend | **NÃO MIGRADO** (referência histórica) | — |
| Redesign "Clareza" (`gediv-painel-redesign-preview`) | Preview | Interface alternativa, não escolhida | **NÃO MIGRADO** (preservado no bundle) | — |
| Questões normativas, conjunto-ouro, corpus | Claude `docs/homologacao`, `docs/validacao` | Manifestos com SHA-256 | **MANTER** + Q12 nova | `docs/` |
| Documentação histórica das etapas 01–30 | Claude `docs/` | Rastreabilidade | **MANTER** como histórico | `docs/historico/` |
