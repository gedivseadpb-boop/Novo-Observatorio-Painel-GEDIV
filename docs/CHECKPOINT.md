# Checkpoint — último estado verificado

**Data:** 25/11/2026 · **Branch:** `claude/loving-goldberg-j5zhoj` (branch padrão do repositório) · **Release:** [`v1.0.0`](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/releases/tag/v1.0.0) no commit `ea07564`

## Estado verificado (25/11/2026, commit da publicação `046595b`)
- Suíte Python: **735 testes, 0 falhas** (7 pulados por dados privados). Interface (jsdom): 5/5. Teste no navegador do pacote oficial (computador e celular): aprovado.
- Conjunto-ouro com PDFs oficiais: 5/5 (evidência de 12/11; não reexecutado depois, sem mudança no código de leitura e classificação).
- **Site oficial no ar: https://paineldoepb.centralgestaopublica.com.br** (HTTPS), publicado em 25/11/2026 pela execução [45683094708](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/actions/runs/45683094708). Estado **"Dados oficiais em validação"**: interface aprovada e 7 abas; indicadores, gráficos e tabelas indisponíveis; 0 registros; nenhum dado fictício. Publicação só por disparo manual autorizado.
- HTTPS obrigatório ativo (Enforce HTTPS marcado pela responsável em 25/11/2026; `http://` passa a `https://`).
- **P0-1 comprovado em 25/11/2026 22h40 UTC** no computador da responsável (Brasil): edição de 25/11 baixada íntegra (52 páginas, SHA-256 `b257d277…`), lida (OCR em 10 páginas), 2 atos GEDIV e 12 decisões pendentes de conferência, reexecução sem duplicidade (`docs/evidencias/aquisicao-2026-11-25/prova-p0-1-pc-responsavel.json`). Fora do Brasil a fonte continua respondendo 403.
- Cobertura oficial independente pela CGE-PB: listagem diária funcionando; os PDFs da CGE exigem senha.
- Backups dos repositórios antigos: 7/7 verificados no Drive (B-06); exclusão aguarda aprovação.

## Próximos passos, em ordem de valor
1. **Concluído (P0-1):** num computador no Brasil, `python -m observatorio.operacao prova-coleta --dados PASTA --saida prova-p0-1.json` (`docs/OPERACAO.md` §9). O relatório sem dados pessoais volta para a auditoria.
2. **P0-2 (provisório em andamento, D-11):** agendamento no computador da responsável (09h04 e 14h04) autorizado em 25/11/2026, **a ser trocado em alguns dias** pelo executor permanente no Brasil: máquina gratuita (Oracle São Paulo) ou da SEAD, com o timer `systemd` de `deploy_autonomo/` (sem runner no repositório público).
3. Piloto de 7 dias com dois disparos diários; registrar cada execução.
4. Decisões normativas da GEDIV (B-02) e reclassificação de uma **cópia** das bases históricas.
5. Aprovação da exclusão dos repositórios antigos (B-06); backups já completos no Drive.
