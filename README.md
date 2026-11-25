# Painel Diário Oficial | GEDIV

Observatório das publicações do **Diário Oficial do Estado da Paraíba** de interesse da Gerência Executiva de Concessão de Direitos e Vantagens (GEDIV/SEAD-PB). Cobre a **Progressão Funcional** (Horizontal e Vertical A–F, por grupo do PCCR) e o **Tempo de Serviço/Contribuição** (TS-01 a TS-07 e Abono de Permanência), além de outras publicações, publicações do dia e histórico.

Este é o **repositório-mãe único** do projeto. Ele substitui `Observat-rio-GEDIV-CLAUDE`, `robo-gediv-V2`, `robo-gediv-gemini`, `robo-gediv-pb`, `gediv-painel-unificado-previa`, `gediv-painel-redesign-preview` e `gediv-conferencia-privada`, todos com backup verificado (`docs/migracao/inventario-repositorios-antigos.json`).

## Como funciona
```
DOE-PB (A União: /doe e /servicos/doe)
  → coleta (robots.txt por URL, SHA-256, versões, reverificação)
  → acervo privado de PDFs por SHA-256
  → leitura por colunas + OCR Tesseract em português
  → classificação GEDIV (regras versionadas e homologações registradas)
  → base canônica SQLite (atos, decisões, eventos, revisão auditada)
  → Painel Unificado "Delicadeza Visual" (Público · Gerência · Administração)
  → snapshot público agregado (promoção e revogação auditadas)
```

## Situação (25/11/2026)
| Parte | Situação |
|---|---|
| Código, testes e documentação | ✅ 735 testes, 0 falhas; CI em Ubuntu e Windows |
| Leitura e classificação com PDFs oficiais | ✅ conjunto-ouro 5/5 |
| Painel Unificado (interface aprovada) | ✅ preservado byte a byte; acessibilidade verificada |
| Achados das auditorias (F-01…F-11, A-10) | ✅ corrigidos, com testes |
| Backup cifrado e restauração | ✅ |
| Coleta automática agendada (09h e 14h, todos os dias) | 🟡 ativa, com cobertura oficial independente pela CGE-PB; o download do conteúdo da A União depende de um executor na rede institucional (B-01) |
| Site oficial | ✅ no ar: https://paineldoepb.centralgestaopublica.com.br, em "Dados oficiais em validação" (sem dados fictícios; dados reais após a coleta, o piloto e a aprovação da GEDIV) |
| Produção com dados reais | ⛔ depende da TI da SEAD (B-08) |

Detalhes: [objetivo e critérios](docs/GOAL.md) · [bloqueios](docs/BLOQUEIOS.md) · [conquistas comprovadas](docs/CATALOGO_CONQUISTAS.md) · [checkpoint](docs/CHECKPOINT.md).

## Começar
```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-dev.txt
sudo apt-get install -y tesseract-ocr tesseract-ocr-por
.venv/bin/python -m unittest discover -s tests -t .
.venv/bin/python scripts/preparar_previa_github_pages.py --banco-local dados-previa-sintetica
.venv/bin/python -m observatorio.operacao promover-snapshot-publico --dados dados-previa-sintetica --gerar --responsavel "Teste" --justificativa "Demonstração local"
.venv/bin/python -m observatorio.web --dados dados-previa-sintetica      # http://127.0.0.1:8000/painel/
```
Operação completa (coleta, contas, snapshot, backup e homologações): [docs/OPERACAO.md](docs/OPERACAO.md).

## Mapa do código
| Pasta | Conteúdo |
|---|---|
| `observatorio/coleta` | descoberta e download do DOE-PB, guarda de acesso, inventário e cobertura |
| `observatorio/leitura` | leitura por colunas, OCR, validação |
| `observatorio/gerencias/gediv` | catálogo, regras e classificação GEDIV, homologações |
| `observatorio/nucleo` | banco canônico, acervo, rede, verificação de PDF |
| `observatorio/revisao` | revisão humana auditada |
| `observatorio/painel` | indicadores, projeções e exportações |
| `observatorio/web` | servidor HTTP, contas e o Painel Unificado (`unificado/`) |
| `observatorio/operacao` | comandos de operação, snapshot, backup, conjunto-ouro |
| `deploy_autonomo` | rotina diária, timer `systemd`, guias de implantação |
| `.github/workflows` | testes, coleta diária, Pages, sonda |
| `docs` | objetivo, decisões, bloqueios, operação, validação e histórico |

## Regras
Nunca versionar PDFs, bancos, backups, senhas, tokens ou dados pessoais. Agentes de IA: leia [AGENTS.md](AGENTS.md).
