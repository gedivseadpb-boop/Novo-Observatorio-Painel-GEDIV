# Manual de operação

Linguagem direta, para quem opera o Observatório. Comandos em Linux; o mesmo vale no Windows com `python` no lugar de `.venv/bin/python`.

## 1. Instalação limpa

```bash
git clone https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV.git
cd Novo-Observatorio-Painel-GEDIV
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
sudo apt-get install -y tesseract-ocr tesseract-ocr-por
.venv/bin/python -m unittest discover -s tests -t .
```

Resultado esperado: todos os testes aprovados; os pulados dependem apenas de dados privados.

## 2. Coleta automática do Diário Oficial

### 2.1 Opção A: runner próprio do GitHub na rede da SEAD (recomendada; resolve o bloqueio B-01)
1. Num computador ou VM Linux da SEAD **que abra https://auniao.pb.gov.br/doe no navegador**, siga GitHub > repositório > Settings > Actions > Runners > **New self-hosted runner** e cadastre-o com o rótulo `gediv-br`.
2. Nesse host, crie uma pasta privada e persistente para os dados (ex.: `/var/lib/gediv/dados`, dono = usuário do runner, permissão 700) e instale `tesseract-ocr-por` e Python 3.11+.
3. No GitHub: Settings > Secrets and variables > Actions > **Variables**:
   - `GEDIV_RUNNER` = `gediv-br`
   - `GEDIV_DADOS_DIR` = `/var/lib/gediv/dados`
4. Em Actions > "Coleta diária do DOE-PB" > **Run workflow**. Verde = coleta real feita; o resumo mostra edição, SHA-256 e páginas.

### 2.2 Opção B: VM Linux com timer `systemd` (independente do GitHub)
Siga `deploy_autonomo/GUIA_IMPLANTACAO_AUTONOMA.md`. O timer roda às 09h e 14h (America/Sao_Paulo), todos os dias.

### 2.3 Teste de rede no host (antes de tudo)
```bash
.venv/bin/python -m observatorio.operacao sonda --fonte auniao --saida sonda.json
```
Código 0 = download íntegro (com SHA-256 e páginas). Código 4 = fonte inacessível; o campo `detalhe` mostra a causa (ex.: conexão recusada, tempo esgotado).

## 3. Painel
- Local: `.venv/bin/python -m observatorio.web --dados /var/lib/gediv/dados` e abrir `http://127.0.0.1:8000/painel/`.
- Contas: `.venv/bin/python -m observatorio.web.usuarios --dados DADOS criar LOGIN --nome "Nome" --papel gerencia|admin`.
- GitHub Pages (site público): o workflow "Painel no GitHub Pages" gera o **pacote oficial** (`scripts/preparar_pacote_oficial_pages.py`). Enquanto não houver dados oficiais aprovados, o pacote mostra **"Dados oficiais em validação"**: navegação e 7 abas preservadas; indicadores, gráficos e tabelas indisponíveis (nunca zero); nenhum registro. A validação recusa dados fictícios, pessoais, PDFs, bancos, backups e credenciais. A demonstração sintética (`scripts/preparar_previa_github_pages.py`) fica só para testes e homologação local.
- **Publicação somente manual**: Actions > "Painel no GitHub Pages" > Run workflow > marcar **publicar**. Um push só gera e valida o pacote (artefato `pacote-oficial-*`), sem publicar; não há agendamento. Teste do pacote no navegador: `python scripts/preparar_pacote_oficial_pages.py --saida /tmp/site` e `GEDIV_CHROMIUM=/caminho/chrome node tests/test_pagina_oficial_navegador.cjs --static-dir /tmp/site`.
- Domínio próprio `paineldoepb.centralgestaopublica.com.br`: no Registro.br, zona do domínio `centralgestaopublica.com.br`, **um** registro `CNAME`, nome `paineldoepb`, valor `gedivseadpb-boop.github.io`. No disparo manual com **publicar**, o workflow consulta o DNS: se o CNAME apontar para o GitHub, o arquivo `CNAME` entra no pacote e o HTTPS é solicitado; senão, publica só no endereço `github.io`. Reversão: apagar o registro (o disparo seguinte volta ao `github.io`) ou disparar de novo a partir de um commit anterior.

## 4. Divulgação pública (snapshot)
```bash
.venv/bin/python -m observatorio.operacao gerar-candidato-snapshot --dados DADOS
.venv/bin/python -m observatorio.operacao promover-snapshot-publico --dados DADOS --responsavel "Nome" --justificativa "Aprovação ..."
.venv/bin/python -m observatorio.operacao revogar-snapshot-publico --dados DADOS --responsavel "Nome" --justificativa "Motivo"
```
A revogação vale na hora: a consulta pública passa a responder 503. Tudo fica na trilha de auditoria.

## 5. Backup cifrado e restauração
1. Gere uma frase-senha forte (mínimo 16 caracteres) e guarde-a **fora do servidor** (cofre institucional). Sem ela, o backup é irrecuperável.
2. No host: `/etc/gediv/backup.chave` com a frase, permissão 600, e `GEDIV_BACKUP_CHAVE_ARQUIVO=/etc/gediv/backup.chave` no serviço. A rotina diária passa a gerar `backups/cifrado/gediv-*.gedivbak`.
3. Copie os `.gedivbak` para um destino externo autorizado (eles já estão cifrados).
4. Restaurar (sempre em pasta nova):
```bash
GEDIV_BACKUP_CHAVE_ARQUIVO=/etc/gediv/backup.chave .venv/bin/python -m observatorio.operacao restaurar --arquivo X.gedivbak --destino /var/lib/gediv/restaurado-AAAAMMDD
```

## 6. Homologação de equivalências pela GEDIV
Quando a GEDIV decidir a Q1 (`TEC. ADM` = `AST`) ou a equivalência `STF` = `SFT`, inclua em `observatorio/gerencias/gediv/homologacoes.json`:
```json
{"expressao": "TEC. ADM", "grupo": "AST", "ato_de_homologacao": "Portaria GEDIV nº X/2027, de DD/MM/2027"}
```
A versão das regras muda sozinha e o painel passa a marcar as classificações antigas como desatualizadas até a reclassificação.

## 7. Conjunto-ouro com os PDFs oficiais (regressão real)
Os PDFs oficiais ficam **fora do Git**. Com a pasta local deles:
```bash
GEDIV_PDFS_OURO=/caminho/pdfs .venv/bin/python -m unittest tests.test_leitura_correcoes.TesteConjuntoOuro -v
```

## 8. Nova versão (release)
Crie `docs/releases/vN.N.N.md` com as notas e envie para a branch padrão. O workflow "Release" roda a suíte completa e, se tudo passar, cria a tag e a release no GitHub, com o pacote sintético do painel e o `.sha256` anexados. Versões já publicadas são ignoradas.

## 9. Coleta automática no computador da responsável (Windows) — o caminho que já funcionou em 18/11
A A União só aceita acessos do Brasil ou da rede interna. Em 18/11/2026 a coleta completa funcionou a partir do computador da responsável. Para automatizar isso:
```bat
git clone https://github.com/gedivseadpb-boop/Novo-Observatorio-Painel-GEDIV.git C:\GEDIV\repo
cd C:\GEDIV\repo
python -m pip install -r requirements.txt
python -m observatorio.operacao rotina-diaria --dados C:\GEDIV\dados
python -m observatorio.operacao agendar-windows --dados C:\GEDIV\dados --aplicar
```
- `rotina-diaria` faz coleta, reverificação, leitura/OCR, classificação, candidato do painel e backup (se configurado), com registro em `C:\GEDIV\dados\rotina\`.
- `agendar-windows --aplicar` cria duas tarefas diárias (09:04 e 14:04) no Agendador de Tarefas. Sem `--aplicar`, só mostra o que faria.
- Requisitos: Python 3.11+ e Tesseract com português (`por`). Os PDFs e o banco ficam só em `C:\GEDIV\dados`, fora do Git.
- Com o computador desligado no horário, a execução seguinte recupera a janela (a coleta recua 3 dias).

### 9.1 P0-1: provar a coleta real em um único comando
No computador no Brasil (pasta do repositório clonado, com as dependências instaladas):
```bat
python -m observatorio.operacao prova-coleta --dados C:\GEDIV\dados --saida C:\GEDIV\prova-p0-1.json
```
O comando roda a sonda, a coleta do dia da edição mais recente, a leitura e a classificação, a cobertura do dia e a reexecução (que não pode trazer arquivo novo). Código 0 = APROVADO; 3 = aprovado com pendências (ex.: páginas sem OCR); 4 = fonte inacessível; 1 = reprovado. O arquivo `prova-p0-1.json` não tem nomes, matrículas nem processos: é ele que volta para a auditoria. PDFs e banco ficam só em `C:\GEDIV\dados`.
