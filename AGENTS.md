# Instruções para agentes de IA (Claude, Codex, Gemini, ChatGPT e outros)

Este é o **repositório-mãe único** do Observatório GEDIV. Antes de alterar qualquer coisa, leia nesta ordem:
`docs/CHECKPOINT.md` (último estado verificado) → `docs/GOAL.md` → `docs/BLOQUEIOS.md` → `docs/DECISOES.md` → `docs/MATRIZ_MIGRACAO.md`.

## A responsável pelo projeto
Profissional de gestão pública, **não desenvolvedora**. Responda em português do Brasil, em linguagem clara. Execute você mesmo o trabalho técnico; peça a ela só o que exige a conta, a autorização ou uma decisão de negócio, com passos numerados e exatos.

## Regras invioláveis
1. **Nunca versionar** PDFs, bancos `.sqlite3`, backups, `.env`, frases-senha, tokens ou dados pessoais (`.gitignore` já bloqueia os formatos). PDFs oficiais de teste ficam fora do Git (`GEDIV_PDFS_OURO`).
2. **Não declarar sucesso sem evidência.** Testes pulados, workflows vermelhos ou dados sintéticos não comprovam coleta real. Diferencie local, GitHub Actions e produção.
3. **Não contornar** bloqueios de acesso da fonte oficial (sem proxies, VPN de terceiros ou troca de identidade). Respeite o `robots.txt` (RFC 9309).
4. **Não alterar a interface aprovada** (`observatorio/web/unificado/`) sem pedido explícito. O `index.html` gerado deve manter o SHA-256 registrado em `docs/CATALOGO_CONQUISTAS.md` (C-05) e a paleta de 240 cores.
5. **Regras normativas da GEDIV não são decididas por IA.** Equivalências só entram via `observatorio/gerencias/gediv/homologacoes.json`, com o ato de homologação.
6. Sem merge, deploy, exclusão de repositório ou mudança de permissões sem autorização expressa da responsável.
7. Toda mudança de regra que altere a classificação muda `VERSAO_REGRAS` (ver D-10) e exige teste.

## Portões de qualidade (antes de cada commit)
```bash
python -m unittest discover -s tests -t .                 # 0 falhas
npm test                                                   # interface (jsdom)
GEDIV_PDFS_OURO=/pasta/pdfs python -m unittest tests.test_leitura_correcoes.TesteConjuntoOuro   # 5/5, quando houver os PDFs
```
Ao mexer na interface, rode também `node tests/test_acessibilidade_navegador.cjs --static-dir <pacote>`.

## Continuidade
Ao terminar uma etapa, atualize `docs/CHECKPOINT.md` (data, commit, testes, o que falta) e o catálogo de conquistas. Retome sempre do último estado verificado, nunca de memória.
