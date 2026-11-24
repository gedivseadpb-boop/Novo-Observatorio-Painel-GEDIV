# Objetivo do projeto e critérios de encerramento

## Objetivo (definido pela responsável pelo projeto em 24/11/2026)
Um único repositório-mãe (`gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV`), um painel oficial (Painel Unificado "Delicadeza Visual"), uma base canônica (SQLite relacional + acervo por SHA-256), todas as conquistas essenciais preservadas e **alimentação automática diretamente do Diário Oficial da Paraíba** (https://auniao.pb.gov.br/doe e https://auniao.pb.gov.br/servicos/doe), com rigor de evidência, rastreabilidade, controle de configuração e portões de qualidade.

## Critérios de encerramento e situação
Legenda: ✅ comprovado · 🟡 implementado e testado, aguardando ação institucional · ⛔ bloqueado fora do código (ver `docs/BLOQUEIOS.md`).

| Critério | Situação | Evidência |
|---|---|---|
| Repositório-mãe único, limpo e modular | ✅ | `docs/MATRIZ_MIGRACAO.md`, `docs/migracao/MANIFESTO_PROCEDENCIA.json` |
| Instalação limpa | ✅ | `docs/OPERACAO.md` §1; CI do GitHub em Ubuntu e Windows (C-04) |
| Interface aprovada preservada | ✅ | C-05 (idêntica byte a byte), C-06 (acessibilidade) |
| Integridade canônica (versões, duplicidades, republicações) | ✅ | C-07, C-09; testes de versões e eventos |
| Leitura de PDF + OCR em português + classificação GEDIV | ✅ | C-01 e C-02: conjunto-ouro oficial 5/5 |
| Segurança (achados F-01…F-11, A-10) | ✅ | C-07…C-13 |
| Backup cifrado e restauração | ✅ | C-14 |
| Automação agendada (09h/14h, todos os dias) | 🟡 | C-16: agendada e executando; a coleta real depende de B-01 |
| **Coleta oficial real automática** | ⛔ | B-01: a fonte recusa as nuvens disponíveis; exige runner na rede institucional |
| Hospedagem web do painel | 🟡 | B-03: pacote validado no GitHub; falta ativar o Pages (1 clique) |
| Independência dos repositórios antigos | ✅ | Nenhuma referência de código aos repositórios antigos; o build e os testes usam só este repositório |
| Exclusão dos repositórios antigos com backups verificados | 🟡 | C-17 e B-06: backups verificados; a exclusão aguarda aprovação específica |
| Homologação normativa GEDIV | ⛔ | B-02 |
| Piloto de 7 dias e produção | ⛔ | Depende de B-01 e B-08 |

## Fora do alcance desta etapa (registrado, não inventado)
Discos C:\ e D:\ e conversas de outras IAs (B-04, B-05).
