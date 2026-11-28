# Retomada do trabalho (para Antigravity, Claude, Codex ou outra IA)

Atualizado em 26/11/2026. Leia este arquivo inteiro antes de agir. Depois leia, nesta ordem: `AGENTS.md`, `docs/CHECKPOINT.md`, `docs/DECISOES.md` (D-11) e `docs/BLOQUEIOS.md`.

## ORDEM COMBINADA COM A RESPONSÁVEL (27/11/2026) — leia antes de agir
1. **Primeiro: ajustar a tela.** A responsável vai preencher a planilha-modelo `docs/modelos/dicionario-e-modelo-revisao.xlsx` (dados fictícios, editável) com a organização correta dos eixos, colunas e categorias da GEDIV. A IA analisa a viabilidade, propõe as mudanças nas regras (nova versão, com homologação dela) e na interface, e implementa só com a aprovação dela.
2. **Só depois: retomar o plano e o passo a passo** já registrados: conferência das decisões (planilha de revisão, etapa B pronta), treino por grifos (C), ML de triagem (D), qualidade por campo (E), CSV público com nível de conferência (F), piloto da coleta e executor permanente (D-11).
3. **Até o ajuste da tela:** não iniciar a conferência em massa, porque os eixos podem mudar.

## Quem é a responsável
Profissional de gestão pública, **não desenvolvedora**. Responda em português, com passos numerados e um comando por bloco. Execute você mesmo o trabalho técnico. Não publique, não exclua e não mude permissões sem a autorização dela.

## Onde está cada coisa
- **Repositório oficial:** https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV (branch padrão `claude/loving-goldberg-j5zhoj`). No computador da responsável: `C:\GEDIV\repo`.
- **Dados privados (PDFs, banco, registros):** `C:\GEDIV\dados`. **Nunca** vão para o Git nem para lugar público.
- **Site público:** https://paineldoepb.centralgestaopublica.com.br, no estado "Dados oficiais em validação" (sem dados). Publicar dados reais exige a autorização dela.
- **Python:** `C:\Users\ylena\AppData\Local\Programs\Python\Python312\python.exe`. **Claude Code:** `C:\Users\ylena\.local\bin\claude.exe`. **Git:** instalado (disco D).

## O que já está comprovado (não refazer)
1. **Coleta real a partir do Brasil (P0-1):** edição de 25/11/2026 baixada íntegra, lida e classificada (`docs/evidencias/aquisicao-2026-11-25/prova-p0-1-pc-responsavel.json`).
2. **Coleta automática agendada no PC (provisória, D-11):** tarefas `ObservatorioGEDIV-Coleta-0904` e `-1404` no Agendador do Windows, sem janela; primeira execução com código 0. **Piloto de 7 dias: 26/11 a 02/12/2026.**
3. **Site no domínio próprio, com HTTPS obrigatório**, sem dados fictícios.

## Próxima tarefa: painel completo com dados reais, só no computador (não publicar)
Rode no PowerShell, em `C:\GEDIV\repo`, **fora das 09h04 e 14h04** (horários da coleta agendada), verificando cada etapa:

1. **Carga do ano direto da fonte oficial, mês a mês** (o coletor não baixa de novo o que já tem; pode parar e retomar à vontade):
```
1..11 | ForEach-Object { $i = Get-Date -Year 2026 -Month $_ -Day 1; $f = if ($_ -eq 11) { Get-Date } else { $i.AddMonths(1).AddDays(-1) }; python -m observatorio.operacao coletar-intervalo --inicio $i.ToString('yyyy-MM-dd') --fim $f.ToString('yyyy-MM-dd') --dados C:\GEDIV\dados }
```
2. **Leitura e classificação** (demorado: OCR). Retomável com `--refazer-pendentes`:
```
python -m observatorio.operacao executar --dados C:\GEDIV\dados
```
3. **Cobertura do ano** (relatório sem dados pessoais):
```
python -m observatorio.operacao cobertura --inicio 2026-01-01 --fim 2026-11-26 --dados C:\GEDIV\dados --saida C:\GEDIV\cobertura-2026.json
```
4. **Conta de administradora:** a responsável digita a senha; nunca escolha nem veja a senha dela.
```
python -m observatorio.web.usuarios --dados C:\GEDIV\dados criar ylena --nome "Ylena" --papel admin
```
5. **Abrir o painel** (deixar a janela aberta) e acessar http://127.0.0.1:8000/painel/ → "Acesso da gerência":
```
python -m observatorio.web --dados C:\GEDIV\dados
```

**Como saber se deu certo:** a cobertura mostra os dias COMPLETO ou SEM_PUBLICACAO_LISTADA (os 3 últimos dias ficam BAIXADO_SEM_VARREDURA_COMPLETA, o que é normal: janela de suplementos); o painel abre com os números reais na área da gerência; as decisões aparecem como "em conferência".

## Regras que não podem ser quebradas
- **Não usar os PDFs do Google Drive** (pastas "Coleta automática DOE-PB (robô)" e "Acervo ... 18-11-2026"): a decisão é refazer tudo direto da fonte oficial.
- **Não publicar dados reais no site** nem enviar `C:\GEDIV\dados` ao GitHub. O site só recebe indicadores agregados e conferidos, por promoção auditada, com a autorização dela.
- **Não contornar o bloqueio da fonte** (sem VPN ou proxy): a coleta só funciona a partir do Brasil.
- **Não mudar a interface aprovada** (`observatorio/web/unificado/index.html`).
- **Regras da GEDIV (grupos, equivalências) não são decididas por IA:** só via `observatorio/gerencias/gediv/homologacoes.json`, com o ato de homologação.
- **Não mexer nas tarefas agendadas** sem pedido dela. Robô de Apps Script do Drive: sugerido desativar (`removerAgendamentos`); a decisão é dela.

## Pendências registradas (em ordem)
1. Terminar a "Próxima tarefa" acima e guardar o resumo (sem dados pessoais) em `docs/evidencias/`.
2. Acompanhar o piloto: `Get-Content C:\GEDIV\dados\rotina\agendador.log -Encoding UTF8 | Select-String "=== fim"` (esperado: 14 execuções até 02/12).
3. Trocar o executor provisório (PC) pelo definitivo (máquina gratuita da Oracle em São Paulo ou da SEAD), conforme D-11.
4. Configurar a frase-senha do backup cifrado (`docs/OPERACAO.md` §5).
5. Homologações da GEDIV (B-02) e conferência das decisões na tela de revisão.

## Ao terminar cada etapa
Atualize `docs/CHECKPOINT.md` (data, o que foi feito, evidência) e faça commit sem dados pessoais. Se não puder fazer commit, entregue à responsável o texto pronto para colar aqui na próxima sessão.

## Mudanças no passo a passo (leia isto para atualizar o documento da responsável)
- **26/11/2026 — Planilha CSV diária (D-12):** depois de `git pull`, a rotina das 09h04 e 14h04 também gera `C:\GEDIV\dados\exportacao\observatorio-completo.csv` (interno) e `observatorio-publico.csv` (só conferidos). Gerar na hora: `python -m observatorio.operacao exportar-csv --dados C:\GEDIV\dados`.
- **26/11/2026 — Coluna `Motivo_Alerta` (D-13, etapa A):** a planilha completa traz, em cada linha, o motivo para conferir (processo ou matrícula fora do padrão, página lida por OCR, possível duplicidade, conflito etc.). **Como usar:** no Excel, filtre `Motivo_Alerta` para ver primeiro as linhas com alerta. Linha sem alerta não está garantida; só não disparou nenhuma regra.
- **27/11/2026 — Revisão pela planilha (D-13, etapa B):** a rotina gera `C:\GEDIV\dados\revisao\revisao-pendente.xlsx` (só pendentes, as com alerta primeiro) e, na coleta seguinte, aplica o que a responsável preencheu, com auditoria. **Uma vez:** `python -m observatorio.operacao configurar-revisao --autor ylena --dados C:\GEDIV\dados`. **Como preencher:** Acao (Confirmar, Corrigir ou Rejeitar), Consultei_PDF = SIM, e para Corrigir: Campo_Corrigido e Valor_Corrigido; Justificativa com 5 letras ou mais. **Resultado:** relatório `revisao-relatorio-*.csv` na mesma pasta (aplicadas e recusadas, com o motivo). Para usar pelo Drive, sincronize a pasta `revisao` com o Google Drive para computador e edite o .xlsx sem converter. Inclusão de decisão omitida continua pela tela.
- **Próximas mudanças previstas (ainda não feitas):** treino por grifos (etapa C).
