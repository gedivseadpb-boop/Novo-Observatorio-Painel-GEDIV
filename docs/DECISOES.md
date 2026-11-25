# Registro de decisões técnicas

Formato curto: contexto → decisão → consequência. Decisões novas entram no topo.

## D-11 · Executor PROVISÓRIO da coleta: computador da responsável, pelo Agendador do Windows (25/11/2026)
- **Contexto:** P0-1 comprovado no computador da responsável, no Brasil (C-26). A fonte só aceita acessos do Brasil e ainda não há máquina permanente.
- **Decisão da responsável (25/11/2026):** autorizada **por enquanto** a opção A. O comando `operacao agendar-windows --dados C:\GEDIV\dados --aplicar` cria as tarefas `ObservatorioGEDIV-Coleta-0904` e `-1404`, que rodam `rotina-diaria` às 09h04 e 14h04. Dados e PDFs ficam só em `C:\GEDIV\dados`, fora do Git. Custo: R$ 0.
- **Provisório:** a responsável informou que **a opção será trocada em alguns dias**. Destino previsto: máquina gratuita da Oracle em São Paulo ou máquina da SEAD, com o timer `systemd` de `deploy_autonomo/` (D-05), sem ligar runner ao repositório público. Na troca: copiar `C:\GEDIV\dados` por backup cifrado, restaurar no novo executor, conferir as métricas e só então apagar as tarefas do Windows.
- **Consequência:** a coleta depende do PC ligado nos horários. Com o PC desligado, a execução seguinte recupera os 3 dias anteriores. O piloto de 7 dias pode começar no PC, mas a operação autônoma só será declarada no executor permanente.

## D-10 · Versão das regras `gediv-2026.11.24-1` (24/11/2026)
- **Contexto:** a Fase III pediu um bump único, cobrindo exclusão de normativos, Abono, OCR `OFI` e o enquadramento `AST`. No repositório antigo, o bump reclassificaria bases históricas.
- **Decisão:** no repositório-mãe a base canônica nasce nova, sem dados históricos. A versão foi elevada uma única vez. Quando houver equivalência homologada, a versão recebe um sufixo automático (ex.: `+AST`).
- **Consequência:** reclassificar as bases históricas privadas com esta versão continua dependendo de autorização normativa e deve ser feito sobre uma **cópia**.

## D-09 · Equivalências condicionais só com homologação registrada (F-11, Q1, Q12)
- **Decisão:** `TEC. ADM`→`AST` e `STF`→`SFT` só valem se constarem de `observatorio/gerencias/gediv/homologacoes.json` com o ato de homologação. Mesmo homologada, `TEC. ADM` exige cargo compatível comprovado. Ao lado de `TEC. ADM`, só a sigla `AST` literal dispensa a homologação; a citação da Lei 14.386/2026 não basta.
- **Consequência:** o conjunto-ouro passa de 4/5 para 5/5; os atos ficam sem grupo e com pendência visível no painel até a decisão da GEDIV.

## D-08 · Snapshot público: candidato → promoção auditada → revogação (F-04)
- **Decisão:** a rotina automática nunca publica. O público recebe 503 sem snapshot promovido. Promoção e revogação exigem responsável e justificativa e ficam na trilha de auditoria.

## D-07 · `robots.txt` por URL e por redirecionamento, conforme a RFC 9309 (F-02)
- **Decisão:** o autorizador fica na camada de rede (`Politica.autorizar`) e vale para coleta, lotes e sonda. Um `robots.txt` inacessível (5xx ou rede) significa acesso não permitido.

## D-06 · Backup cifrado próprio (AES-256-GCM, scrypt) com restauração só em pasta nova
- **Contexto:** o `backup.py` citado no dossiê existia só numa cópia local do computador, sem acesso nesta sessão (B-04).
- **Decisão:** implementar com a biblioteca `cryptography`, em blocos autenticados e com manifesto SHA-256. A frase-senha fica fora do Git, sob custódia institucional.

## D-05 · Executor da coleta: runner próprio na rede institucional; nuvem do GitHub só como sonda
- **Contexto:** B-01 (a fonte recusa nuvens estrangeiras).
- **Decisão:** `coleta-diaria.yml` usa `vars.GEDIV_RUNNER`. Sem esse valor, roda a sonda no executor do GitHub e falha de forma visível. A rotina completa só roda com `GEDIV_DADOS_DIR` persistente e privado. Alternativa equivalente: VM Linux com o timer `systemd`.
- **Rejeitado:** proxies, VPN de terceiros ou contorno de bloqueio (vedado pela política de acesso da fonte).

## D-04 · Migração limpa, sem importar o histórico Git antigo
- **Decisão:** cópia dos arquivos comprovados com manifesto de procedência (blob de origem e SHA-256). O histórico antigo fica nos bundles verificados.
- **Consequência:** o repositório-mãe não herda superfícies históricas ainda não auditadas (A-12/F-09).

## D-03 · Interfaces legadas descartadas; Painel Unificado mantido sem alteração visual
- **Decisão:** `painel-publico`, `painel-v2`, `revisao-2910` e o redesign "Clareza" saem da arquitetura. O Painel Unificado é preservado byte a byte.

## D-02 · Base canônica: SQLite relacional v9 + acervo por SHA-256
- **Fonte:** dossiê técnico de 24/11/2026 §08 e decisão da Fase III. Os checkpoints JSON do V2 foram descartados como persistência.

## D-01 · Repositório-mãe: `gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV`
- **Fonte:** objetivo definido pela responsável pelo projeto em 24/11/2026. Substitui a recomendação anterior de consolidar em `Observat-rio-GEDIV-CLAUDE`.
