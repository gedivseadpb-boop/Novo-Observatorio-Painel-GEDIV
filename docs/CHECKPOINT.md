# Checkpoint — último estado verificado

**Data:** 24/11/2026 · **Branch:** `claude/loving-goldberg-j5zhoj` (branch padrão do repositório) · **Release:** [`v1.0.0`](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/releases/tag/v1.0.0) no commit `ea07564`

## Estado verificado
- Suíte Python: 706 testes, 0 falhas (7 pulados por dados privados; 6 com os PDFs oficiais informados).
- Testes de interface (jsdom): 5/5. Acessibilidade em Chromium: 9 verificações, 0 estouro em 1440/768/390 px.
- Conjunto-ouro com PDFs oficiais: **5/5**.
- CI do GitHub: Ubuntu 24.04 e Windows; Python 3.11 e 3.13 — verde no commit da release.
- Instalação limpa a partir do GitHub (clone novo + ambiente novo): 706 testes aprovados; painel e API servindo.
- Coleta diária agendada (09h/14h Brasília): executa, mas a fonte oficial não é alcançada a partir da nuvem do GitHub (B-01).
- Pages: pacote validado; ativação pendente (B-03).
- Backups dos repositórios antigos: 7/7 verificados e 7/7 no Drive, em pasta restrita (B-06); a exclusão aguarda aprovação.

## Próximos passos, em ordem de valor
1. **Destravar a coleta real (B-01):** runner próprio `gediv-br` na rede da SEAD + variáveis `GEDIV_RUNNER` e `GEDIV_DADOS_DIR` (`docs/OPERACAO.md` §2.1). Depois, rodar "Coleta diária do DOE-PB" manualmente e registrar a evidência no catálogo.
2. Ativar o GitHub Pages (B-03).
3. Piloto de 7 dias com dois disparos diários; registrar cada execução.
4. Decisões normativas da GEDIV (B-02) e reclassificação de uma **cópia** das bases históricas.
5. Aprovação da exclusão dos repositórios antigos (B-06); backups já completos no Drive.
