# Catálogo de conquistas comprovadas

Cada conquista só entra aqui com **evidência verificável** e com o ambiente em que foi verificada. Legenda de ambiente: **L** = nuvem temporária do Claude Code (Linux); **G** = GitHub Actions; **W** = estação Windows da GEDIV (relato documentado, não reproduzido aqui); **P** = produção (nenhum item até agora).

| # | Conquista | Evidência | Ambiente | Verificada em |
|---|---|---|---|---|
| C-01 | Conjunto-ouro com os 5 PDFs oficiais (SHA-256 conferidos com o manifesto): **5/5** | `GEDIV_PDFS_OURO=<pasta> python -m unittest tests.test_leitura_correcoes.TesteConjuntoOuro`; PDFs baixados da pasta do Drive do projeto, mantidos fora do Git | L | 24/11/2026 |
| C-02 | 02/10/2026: resenhas 488 e 504 recuperadas por OCR `por` (fonte sem mapeamento de caracteres) | Mesma execução de C-01 | L (antes em W) | 24/11/2026 |
| C-03 | Suíte Python: **706 testes, 0 falhas**; 7 pulados (dependem de bancos ou corpus privados); 6 quando os PDFs oficiais são informados | `python -m unittest discover -s tests -t .` | L | 24/11/2026 |
| C-04 | CI em Ubuntu 24.04 e Windows, Python 3.11 e 3.13, com Tesseract `por` no Linux | [Execução 45432987923](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/actions/runs/45432987923) e seguintes | G | 24/11/2026 |
| C-05 | Painel Unificado "Delicadeza Visual" preservado **byte a byte** (`index.html`, SHA-256 `d19296173dcbe3ba5a71915e5a0674b8fc453b5109c3a5ec6c8ba019ccfae809`, 240 cores, 0 cores novas) | Gerado por `scripts/preparar_previa_github_pages.py` e comparado com `gediv-painel-unificado-previa/public/index.html`; repetido no GitHub ([execução 45435101869](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/actions/runs/45435101869)) | L, G | 24/11/2026 |
| C-06 | Acessibilidade em navegador real (Chromium): teclado, foco visível, abas, diálogos, menus; **0 estouro horizontal** em 1440, 768 e 390 px | `node tests/test_acessibilidade_navegador.cjs --static-dir <pacote>`; capturas em `docs/evidencias/painel-2026-11-24/` (7 abas, 0 erros de JavaScript) | L | 24/11/2026 |
| C-07 | F-01: v1 revisada + v2 e v3 com a mesma decisão nova = 4 vigentes (antes 5), estável em replay | `tests/test_f01_versoes_multiplas.py` (reproduzido antes da correção) | L | 24/11/2026 |
| C-08 | F-02: `robots.txt` aplicado a toda URL e a cada redirecionamento; inacessível = proibido (RFC 9309) | `tests/test_f02_robots_por_url.py` (falha com a proteção desligada) | L | 24/11/2026 |
| C-09 | F-03: reverificação delimitada; URL estável com bytes trocados vira nova versão; falha preserva a anterior | `tests/test_f03_reverificacao.py` | L | 24/11/2026 |
| C-10 | F-04: público só com snapshot promovido; revogação = 503 imediato; promoção e revogação auditadas | `tests/test_f04_snapshot_ciclo.py` | L | 24/11/2026 |
| C-11 | F-05 e F-10: confirmações só como booleano literal; token de login fora do JSON por padrão | `tests/test_f05_f10_api.py` | L | 24/11/2026 |
| C-12 | F-11: `TEC. ADM`/`STF` só normalizam com homologação registrada e cargo comprovado | `tests/test_f11_homologacao_grupos.py` | L | 24/11/2026 |
| C-13 | A-10: `/estatico/` legado responde 404 em produção | `tests/test_a10_estatico_producao.py` | L | 24/11/2026 |
| C-14 | Backup cifrado AES-256-GCM com restauração verificada em pasta nova (adulteração, truncamento e frase errada detectados; sessões encerradas) | `tests/test_backup_cifrado.py` | L | 24/11/2026 |
| C-15 | Exclusão de atos normativos pelo cabeçalho (lei, decreto etc.), preservando citações em atos individuais | Testes da branch `feat/exclusao-atos-normativos`, agora integrados; 03/10 com a LC 58 em `fora_escopo` (C-01) | L | 24/11/2026 |
| C-16 | Coleta diária agendada às 09h e 14h (Brasília), com falha visível quando a fonte não é alcançada | `.github/workflows/coleta-diaria.yml`; [execução 45435101354](https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV/actions/runs/45435101354) (vermelha por B-01, como projetado) | G | 24/11/2026 |
| C-17 | Repositórios antigos com backup verificado (`git bundle verify`) e inventário de referências | `docs/migracao/inventario-repositorios-antigos.json`; 6 de 7 no Drive (B-06) | L | 24/11/2026 |
| C-18 | Corpus de PDFs difíceis: 561/566 campos (99,1%) com Tesseract `por` | Relatório da Fase III (`docs/historico/`), corpus esperado privado fora do Git | W | 24/11/2026 (não reproduzido aqui: o esperado privado não está disponível) |
| C-19 | Auditoria de privacidade do conteúdo versionado: 0 CPF, 0 matrícula ou processo reais, 0 segredo nos 232 arquivos de texto; capturas de evidência conferidas por amostragem (5 imagens: dados fictícios ou só agregados) | Varredura por expressões regulares em `git ls-files` (as ocorrências são padrões de detecção e dados fictícios de teste) | L | 24/11/2026 |

**Não comprovado (não declarar como concluído):** coleta oficial automática real (B-01), piloto de 7 dias, publicação do Pages pelo repositório-mãe (B-03), homologação normativa (B-02), produção (B-08).
