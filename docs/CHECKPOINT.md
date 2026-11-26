# Checkpoint — último estado verificado

**Data:** 25/11/2026 (21h35 BRT / 26/11/2026 00h35 UTC) · **Branch:** `claude/loving-goldberg-j5zhoj` (branch padrão do repositório) · **Release:** [`v1.0.0`](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/releases/tag/v1.0.0) no commit `ea07564`

## Carga completa de 2026 no computador da responsável (`docs/RETOMADA.md` — "Próxima tarefa")
- **Etapa 1 concluída em 25/11/2026 21h35 BRT (26/11/2026 00h35 UTC):** coleta oficial de janeiro a 25/11/2026 diretamente da A União (`auniao.pb.gov.br`), mês a mês, fora dos horários agendados (09h04 e 14h04), gravando somente na pasta privada local `C:\GEDIV\dados` (fora do Git).
  - **Comando:** `1..11 | ForEach-Object { $i = Get-Date -Year 2026 -Month $_ -Day 1; $f = if ($_ -eq 11) { Get-Date } else { $i.AddMonths(1).AddDays(-1) }; python -m observatorio.operacao coletar-intervalo --inicio $i.ToString('yyyy-MM-dd') --fim $f.ToString('yyyy-MM-dd') --dados C:\GEDIV\dados }`
  - **Resultado:** código de saída `0` e `pendencias: false` em todos os 11 meses; `robots.txt` `LIDO` e respeitado (`urls_negadas_por_robots: 0`); 11/11 varreduras mensais sem erro; **228 publicações oficiais no estado `BAIXADA`** (jan: 22, fev: 18, mar: 23, abr: 19, mai: 23, jun: 18, jul: 23, ago: 22, set: 22, out: 23, nov até 25/11: 15), **228 PDFs íntegros no acervo privado** (`639.548.768` bytes, **11.816 páginas** com estrutura e SHA-256 verificados), 0 falhas e 0 quarentenas.
  - **Evidência (sem dados pessoais):** `docs/evidencias/aquisicao-2026-11-25/carga-2026-auniao-etapa1.json`.
  - **Falta nesta tarefa:** Etapa 2 (leitura/OCR e classificação), Etapa 3 (cobertura do ano), Etapa 4 (conta de administradora local digitada pela responsável) e Etapa 5 (abertura do painel local em `http://127.0.0.1:8000/painel/`).

## Estado verificado anterior (25/11/2026, commit da publicação `046595b`)
- Suíte Python: **735 testes, 0 falhas** (7 pulados por dados privados). Interface (jsdom): 5/5. Teste no navegador do pacote oficial (computador e celular): aprovado.
- Conjunto-ouro com PDFs oficiais: 5/5 (evidência de 12/11; não reexecutado depois, sem mudança no código de leitura e classificação).
- **Site oficial no ar: https://paineldoepb.centralgestaopublica.com.br** (HTTPS), publicado em 25/11/2026 pela execução [45683094708](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/actions/runs/45683094708). Estado **"Dados oficiais em validação"**: interface aprovada e 7 abas; indicadores, gráficos e tabelas indisponíveis; 0 registros; nenhum dado fictício. Publicação só por disparo manual autorizado.
- HTTPS obrigatório ativo (Enforce HTTPS marcado pela responsável em 25/11/2026; `http://` passa a `https://`).
- **P0-1 comprovado em 25/11/2026 22h40 UTC** no computador da responsável (Brasil): edição de 25/11 baixada íntegra (52 páginas, SHA-256 `b257d277…`), lida (OCR em 10 páginas), 2 atos GEDIV e 12 decisões pendentes de conferência, reexecução sem duplicidade (`docs/evidencias/aquisicao-2026-11-25/prova-p0-1-pc-responsavel.json`). Fora do Brasil a fonte continua respondendo 403.
- Cobertura oficial independente pela CGE-PB: listagem diária funcionando; os PDFs da CGE exigem senha.
- Backups dos repositórios antigos: 7/7 verificados no Drive (B-06); exclusão aguarda aprovação.

## Próximos passos, em ordem de valor
1. **Concluído (P0-1):** num computador no Brasil, `python -m observatorio.operacao prova-coleta --dados PASTA --saida prova-p0-1.json` (`docs/OPERACAO.md` §9). O relatório sem dados pessoais volta para a auditoria.
2. **P0-2 (provisório ATIVO, D-11):** tarefa do Agendador do Windows sem janela validada em 25/11/2026 20h26 (horário do PC): `rotina-diaria` terminou com código 0 (coleta, reverificação, leitura/classificação e candidato com sucesso; backup cifrado ainda não configurado). **Piloto de 7 dias: 26/11 a 02/12/2026** (14 execuções esperadas). Antes, foram corrigidos dois achados reais: janela de console que encerrava a coleta (0xC000013A) e trava órfã. Agendamento agendamento no computador da responsável (09h04 e 14h04) autorizado em 25/11/2026, **a ser trocado em alguns dias** pelo executor permanente no Brasil: máquina gratuita (Oracle São Paulo) ou da SEAD, com o timer `systemd` de `deploy_autonomo/` (sem runner no repositório público).
3. Piloto de 7 dias com dois disparos diários; registrar cada execução.
4. Decisões normativas da GEDIV (B-02) e reclassificação de uma **cópia** das bases históricas.
5. Aprovação da exclusão dos repositórios antigos (B-06); backups já completos no Drive.
