"""Revisão pela planilha (D-13, etapa B): a responsável confere no Excel ou no Drive, e o sistema aplica com auditoria.

    python -m observatorio.operacao configurar-revisao --autor ylena --dados C:\\GEDIV\\dados
    python -m observatorio.operacao gerar-revisao --dados C:\\GEDIV\\dados
    python -m observatorio.operacao aplicar-revisao --dados C:\\GEDIV\\dados

Fluxo (pasta <dados>/revisao, que pode ser sincronizada com a pasta privada do Drive pelo Google Drive para computador):
  1. gerar-revisao escreve revisao-pendente.xlsx: só decisões PENDENTES, as com alerta primeiro.
  2. A responsável preenche Acao (Confirmar, Corrigir, Rejeitar), Consultei_PDF (SIM), e, para Corrigir,
     Campo_Corrigido e Valor_Corrigido, mais a Justificativa. Salva o arquivo como .xlsx (sem converter).
  3. aplicar-revisao lê o arquivo e aplica pelo mesmo serviço da tela de revisão (observatorio.revisao.servico),
     com o nome da revisora na trilha de auditoria. Cada linha traz uma impressão digital: se a decisão mudou
     no banco depois que a planilha foi gerada, a linha é RECUSADA (trava de versão). Linhas inválidas também.
  4. O arquivo aplicado vai para revisao/processados/ (não é aplicado duas vezes) e sai o relatório
     revisao-relatorio-AAAAMMDD-HHMMSS.csv (aplicadas e recusadas, com o motivo).
A rotina diária faz 3 e depois 1. Inclusão de decisão omitida continua pela tela (exige o trecho literal do PDF).
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from ..nucleo.banco import Banco
from ..painel.exportacao import csv as _csv, xlsx as _xlsx
from ..revisao import servico as S
from . import csv_diario as X

ARQUIVO = "revisao-pendente.xlsx"
CAMPOS_FIXOS = ["ID_Decisao", "Impressao_Digital", "Motivo_Alerta", "Data_Publicacao", "ID_Resenha", "Pagina_PDF",
                "Link_PDF_Oficial", "Eixo", "Modalidade_Progressao", "Grupo_Ocupacional", "Servico_Tempo_Servico",
                "Numero_Processo", "Servidor", "Matricula", "Resultado"]
CAMPOS_EDITAVEIS = ["Acao", "Consultei_PDF", "Campo_Corrigido", "Valor_Corrigido", "Justificativa"]
CABECALHO = CAMPOS_FIXOS + CAMPOS_EDITAVEIS
ACOES = {"CONFIRMAR": S.CONFERIR, "CORRIGIR": S.CONFERIR, "REJEITAR": S.REJEITAR}
# Campo da planilha -> campo corrigível do serviço de revisão.
CORRIGIVEIS = {"PROCESSO": "processo", "NUMERO_PROCESSO": "processo", "SERVIDOR": "servidor", "NOME": "servidor",
               "MATRICULA": "matricula", "RESULTADO": "resultado", "LOTACAO": "lotacao", "CARGO": "cargo"}
_RESULTADOS = {"DEFERIDO": "DEFERIDO", "INDEFERIDO": "INDEFERIDO", "NAO INFORMADO": "NAO_INFORMADO", "NAO_INFORMADO": "NAO_INFORMADO"}


def _sem_acento(texto: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(texto or "")) if unicodedata.category(c) != "Mn").upper().strip()


def impressao(r: dict) -> str:
    """Impressão digital da decisão: muda se qualquer campo revisável ou a validação mudar no banco."""
    base = "|".join(str(r.get(c) or "") for c in ("id", "processo", "servidor", "matricula", "resultado", "validacao"))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _pasta(dados) -> Path:
    p = Path(dados) / "revisao"
    p.mkdir(parents=True, exist_ok=True)
    return p


def configurar(dados, autor: str) -> dict:
    autor = (autor or "").strip()
    if not autor:
        raise ValueError("informe --autor (o usuário da revisora, como na conta do painel)")
    (_pasta(dados) / "config.json").write_text(json.dumps({"autor": autor}, ensure_ascii=False), encoding="utf-8")
    return {"situacao": "CONFIGURADO", "autor": autor}


def _autor(dados) -> str | None:
    cfg = _pasta(dados) / "config.json"
    if not cfg.is_file():
        return None
    return (json.loads(cfg.read_text(encoding="utf-8")).get("autor") or "").strip() or None


def gerar(dados) -> dict:
    banco = Path(dados) / "observatorio.sqlite3"
    if not banco.is_file():
        return {"situacao": "SEM_BANCO", "linhas": 0}
    linhas = X._linhas(banco)
    dup = X._duplicadas(linhas)
    pendentes = [r for r in linhas if r["validacao"] == "PENDENTE" and r["natureza"] == "ORIGINAL"]
    pendentes.sort(key=lambda r: (not X.alertas(r, dup), r["data_publicacao"] or "", r["numero"] or 0))
    tabela = [CABECALHO]
    for r in pendentes:
        v = dict(zip(X.COLUNAS, X._valores(r, False, dup)))
        tabela.append([r["id"], impressao(r), v["Motivo_Alerta"], v["Data_Publicacao"], v["ID_Resenha"], v["Pagina_PDF"],
                       v["Link_PDF_Oficial"], v["Eixo"], v["Modalidade_Progressao"], v["Grupo_Ocupacional"],
                       v["Servico_Tempo_Servico"], v["Numero_Processo"], v["Servidor"], v["Matricula"], v["Resultado"],
                       "", "", "", "", ""])
    instrucoes = [["Como preencher"],
                  ["1. Abra o link do PDF oficial e compare com a linha."],
                  ["2. Acao: Confirmar (está certo), Corrigir (um campo errado) ou Rejeitar (não é da GEDIV ou é lixo)."],
                  ["3. Consultei_PDF: escreva SIM. Sem isso a linha é recusada."],
                  ["4. Para Corrigir: Campo_Corrigido (Processo, Servidor, Matricula ou Resultado) e Valor_Corrigido."],
                  ["5. Justificativa: pelo menos 5 letras (ex.: conferido no PDF). Se ficar vazia, entra \"conferido pela planilha de revisão\"."],
                  ["6. Salve como .xlsx, sem converter para Planilhas Google. A próxima coleta (09h04 ou 14h04) aplica."],
                  ["Não altere as colunas ID_Decisao e Impressao_Digital."]]
    destino = _pasta(dados) / ARQUIVO
    if destino.exists() and _tem_preenchimento(destino):
        return {"situacao": "MANTIDO_COM_PREENCHIMENTO_NAO_APLICADO", "arquivo": str(destino), "linhas": len(pendentes)}
    temporario = destino.with_suffix(".tmp")
    temporario.write_bytes(_xlsx({"Revisao": tabela, "Instrucoes": instrucoes}))
    temporario.replace(destino)
    return {"situacao": "GERADO", "arquivo": str(destino), "linhas": len(pendentes)}


# --- leitura de .xlsx (biblioteca padrão; aceita o que o Excel e o Drive gravam) ---------------------------------
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _indice(ref: str) -> int:
    letras = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letras:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def ler_xlsx(caminho: Path) -> list[list[str]]:
    """Primeira aba, como lista de linhas de texto."""
    with zipfile.ZipFile(caminho) as z:
        compartilhadas = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                compartilhadas.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        livro = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        primeira = livro.find("m:sheets/m:sheet", _NS)
        rid = primeira.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        alvo = next(r.get("Target") for r in rels if r.get("Id") == rid)
        alvo = alvo.lstrip("/")
        folha = ET.fromstring(z.read(alvo if alvo.startswith("xl/") else "xl/" + alvo))
    linhas = []
    for row in folha.iter(f"{{{_NS['m']}}}row"):
        valores: dict[int, str] = {}
        for i, c in enumerate(row.findall("m:c", _NS)):
            col = _indice(c.get("r")) if c.get("r") else i
            tipo = c.get("t")
            if tipo == "inlineStr":
                texto = "".join(t.text or "" for t in c.iter(f"{{{_NS['m']}}}t"))
            else:
                v = c.find("m:v", _NS)
                texto = "" if v is None else (v.text or "")
                if tipo == "s" and texto:
                    texto = compartilhadas[int(texto)]
                elif texto.endswith(".0") and tipo is None:
                    texto = texto[:-2]
            valores[col] = texto
        linhas.append([valores.get(i, "") for i in range(max(valores) + 1)] if valores else [])
    return linhas


def _registros(caminho: Path) -> list[dict]:
    linhas = ler_xlsx(caminho)
    if not linhas:
        return []
    cab = [h.strip() for h in linhas[0]]
    return [dict(zip(cab, l + [""] * (len(cab) - len(l)))) for l in linhas[1:]]


def _tem_preenchimento(caminho: Path) -> bool:
    try:
        return any((r.get("Acao") or "").strip() for r in _registros(caminho))
    except Exception:                          # arquivo aberto/corrompido: não sobrescrever
        return True


def aplicar(dados, arquivo: str | Path | None = None, autor: str | None = None) -> dict:
    pasta = _pasta(dados)
    caminho = Path(arquivo) if arquivo else pasta / ARQUIVO
    if not caminho.is_file():
        return {"situacao": "SEM_PLANILHA", "aplicadas": 0, "recusadas": 0}
    autor = (autor or _autor(dados) or "").strip()
    if not autor:
        return {"situacao": "REVISORA_NAO_CONFIGURADA", "aplicadas": 0, "recusadas": 0}
    try:
        registros = [r for r in _registros(caminho) if (r.get("Acao") or "").strip()]
    except Exception as e:
        return {"situacao": "PLANILHA_ILEGIVEL", "erro": type(e).__name__, "aplicadas": 0, "recusadas": 0}
    if not registros:
        return {"situacao": "NADA_PREENCHIDO", "aplicadas": 0, "recusadas": 0}
    banco = Banco(Path(dados) / "observatorio.sqlite3")
    relatorio = [["ID_Decisao", "Acao", "Resultado", "Motivo"]]
    aplicadas = recusadas = 0
    try:
        for r in registros:
            did, acao = (r.get("ID_Decisao") or "").strip(), _sem_acento(r.get("Acao"))
            try:
                if acao not in ACOES:
                    raise S.Recusada("Acao deve ser Confirmar, Corrigir ou Rejeitar")
                atual = banco.con.execute("SELECT id, processo, servidor, matricula, resultado, validacao FROM decisao WHERE id = ?",
                                          (did,)).fetchone()
                if atual is None:
                    raise S.Recusada("ID_Decisao não encontrado")
                if impressao(dict(atual)) != (r.get("Impressao_Digital") or "").strip():
                    raise S.Recusada("a decisão mudou depois que a planilha foi gerada; revise na planilha nova")
                justificativa = (r.get("Justificativa") or "").strip() or "conferido pela planilha de revisão"
                confirma = _sem_acento(r.get("Consultei_PDF")) in ("SIM", "S", "X")
                correcoes = None
                if acao == "CORRIGIR":
                    campo = CORRIGIVEIS.get(_sem_acento(r.get("Campo_Corrigido")).replace(" ", "_"))
                    valor = (r.get("Valor_Corrigido") or "").strip()
                    if not campo or not valor:
                        raise S.Recusada("para Corrigir informe Campo_Corrigido (Processo, Servidor, Matricula ou Resultado) e Valor_Corrigido")
                    if campo == "resultado":
                        valor = _RESULTADOS.get(_sem_acento(valor))
                        if not valor:
                            raise S.Recusada("Resultado deve ser Deferido, Indeferido ou Não informado")
                    correcoes = {campo: valor}
                if ACOES[acao] == S.CONFERIR and not confirma:
                    raise S.Recusada("escreva SIM em Consultei_PDF")
                S.revisar_decisoes(banco, [did], ACOES[acao], autor, justificativa, confirma_fonte=confirma,
                                   confirma_vinculo=confirma, correcoes=correcoes)
                aplicadas += 1
                relatorio.append([did, r.get("Acao"), "APLICADA", ""])
            except S.Recusada as e:
                recusadas += 1
                relatorio.append([did, r.get("Acao"), "RECUSADA", str(e)])
    finally:
        banco.fechar()
    momento = datetime.now().strftime("%Y%m%d-%H%M%S")
    (pasta / f"revisao-relatorio-{momento}.csv").write_bytes(_csv(relatorio))
    processados = pasta / "processados"
    processados.mkdir(exist_ok=True)
    caminho.replace(processados / f"revisao-aplicada-{momento}.xlsx")
    return {"situacao": "APLICADO", "aplicadas": aplicadas, "recusadas": recusadas,
            "relatorio": str(pasta / f"revisao-relatorio-{momento}.csv")}
