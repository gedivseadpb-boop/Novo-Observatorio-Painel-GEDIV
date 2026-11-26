"""Exportação CSV diária a partir do banco canônico (decisão da responsável em 26/11/2026, D-12).

    python -m observatorio.operacao exportar-csv --dados C:\\GEDIV\\dados

Gera, em <dados>/exportacao/ (pasta PRIVADA, fora do Git):
  - observatorio-completo.csv: todas as decisões vigentes da GEDIV, com nome e matrícula completos.
    Uso INTERNO da gerência. Nunca vai para o Git nem para o site.
  - observatorio-publico.csv: SÓ decisões CONFERIDAS por revisão humana, publicação original, com o nome
    reduzido às iniciais e a matrícula mascarada (só os 3 primeiros dígitos, opção B da responsável).
    Fica pronto no computador; ir para o site exige a autorização dela (promoção auditada, D-08).

O CSV é um produto DERIVADO do banco: o SQLite continua sendo a base verdadeira. Layout inspirado na
planilha-modelo "Base de Dados - Observatório DOE (SEAD · GEDIV)", aba Publicacoes_DOE, com colunas
de rastreabilidade acrescentadas (ID da decisão, página, SHA-256 da edição e versão das regras).
Separador ";", UTF-8 com BOM (abre direto no Excel) e proteção contra injeção de fórmulas.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from ..gerencias.gediv import catalogo as C
from ..painel.exportacao import csv as _csv

COLUNAS = ["ID_Decisao", "ID_Resenha", "Data_Publicacao", "Edicao_DOE", "Pagina_PDF", "Link_PDF_Oficial", "Eixo",
           "Modalidade_Progressao", "Grupo_Ocupacional", "Servico_Tempo_Servico", "Numero_Processo", "Servidor",
           "Servidor_Iniciais", "Matricula", "Resultado", "Natureza", "Status_Validacao_GEDIV", "Observacoes",
           "SHA256_Edicao", "Versao_Regras"]
# A versão pública não tem o nome completo.
COLUNAS_PUBLICAS = [c for c in COLUNAS if c != "Servidor"]

STATUS = {"CONFERIDO": "Validado", "PENDENTE": "Em validação", "REJEITADO": "Excluído do catálogo"}
_PARTICULAS = {"DA", "DE", "DO", "DAS", "DOS", "E", "D"}


def iniciais(nome: str | None) -> str:
    """'MARIA DA SILVA SOUZA' -> 'M.S.S.' (sem partículas)."""
    partes = [p for p in re.split(r"[\s.]+", (nome or "").upper()) if p and p not in _PARTICULAS]
    return "".join(p[0] + "." for p in partes if p[0].isalpha())


def mascarar_matricula(matricula: str | None, visiveis: int = 3) -> str:
    """Mantém só os primeiros dígitos (opção B): '123.456-7' -> '123.***-*'; '1234567' -> '123****'."""
    if not matricula:
        return ""
    saida, vistos = [], 0
    for ch in str(matricula):
        if ch.isdigit():
            saida.append(ch if vistos < visiveis else "*")
            vistos += 1
        elif ch.isalpha():
            saida.append("*")
        else:
            saida.append(ch)
    return "".join(saida)


def _linhas(banco: Path) -> list[dict]:
    with closing(sqlite3.connect(f"file:{banco.as_posix()}?mode=ro", uri=True)) as con:
        con.row_factory = sqlite3.Row
        return [dict(r) for r in con.execute(
            "SELECT d.id, d.pagina, d.processo, d.servidor, d.matricula, d.resultado, d.validacao, d.sha256, "
            "a.numero, a.sufixo, a.tipo, a.data_publicacao, a.eixo, a.modalidade, a.grupo, a.subcategoria, "
            "a.natureza, a.pendencias, l.numero_edicao, c.versao_regras, "
            "(SELECT MIN(p.url) FROM publicacao p WHERE p.sha256 = d.sha256) AS url "
            "FROM decisao d JOIN ato a ON a.id = d.ato_id JOIN leitura l ON l.sha256 = d.sha256 "
            "LEFT JOIN classificacao c ON c.sha256 = d.sha256 AND c.gerencia = a.gerencia "
            "WHERE a.gerencia = 'GEDIV' AND d.vigente = 1 "
            "ORDER BY a.data_publicacao, a.numero, d.pagina, d.rowid")]


def _valores(r: dict, publica: bool) -> list:
    grupos = {g.codigo: g.nome for g in C.GRUPOS}
    subs = {s.codigo: s.nome for s in C.SUBCATEGORIAS}
    pend = json.loads(r["pendencias"] or "[]")
    linha = {
        "ID_Decisao": r["id"], "ID_Resenha": f"{r['tipo'].title()} {r['numero']}{r['sufixo'] or ''}",
        "Data_Publicacao": r["data_publicacao"], "Edicao_DOE": r["numero_edicao"] or "", "Pagina_PDF": r["pagina"],
        "Link_PDF_Oficial": (f"{r['url']}#page={r['pagina']}" if r["url"] else ""),
        "Eixo": C.EIXOS.get(r["eixo"], r["eixo"] or ""), "Modalidade_Progressao": C.MODALIDADES.get(r["modalidade"], ""),
        "Grupo_Ocupacional": grupos.get(r["grupo"], "Não informado" if r["eixo"] == C.PROGRESSAO else ""),
        "Servico_Tempo_Servico": subs.get(r["subcategoria"], ""), "Numero_Processo": r["processo"] or "",
        "Servidor": r["servidor"] or "", "Servidor_Iniciais": iniciais(r["servidor"]),
        "Matricula": mascarar_matricula(r["matricula"]) if publica else (r["matricula"] or ""),
        "Resultado": C.RESULTADOS.get(r["resultado"], r["resultado"]), "Natureza": (r["natureza"] or "").title(),
        "Status_Validacao_GEDIV": STATUS.get(r["validacao"], r["validacao"]),
        # Pendências do classificador ajudam a gerência; na versão pública só entram registros conferidos.
        "Observacoes": "" if publica else "; ".join(pend),
        "SHA256_Edicao": r["sha256"], "Versao_Regras": r["versao_regras"] or "",
    }
    return [linha[c] for c in (COLUNAS_PUBLICAS if publica else COLUNAS)]


def exportar(dados: str | Path) -> dict:
    pasta = Path(dados)
    banco = pasta / "observatorio.sqlite3"
    if not banco.is_file():
        return {"situacao": "SEM_BANCO", "completo": 0, "publico": 0}
    linhas = _linhas(banco)
    publicas = [r for r in linhas if r["validacao"] == "CONFERIDO" and r["natureza"] == C.ORIGINAL]
    destino = pasta / "exportacao"
    destino.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in (("observatorio-completo.csv", [COLUNAS] + [_valores(r, False) for r in linhas]),
                           ("observatorio-publico.csv", [COLUNAS_PUBLICAS] + [_valores(r, True) for r in publicas])):
        temporario = destino / (nome + ".tmp")
        temporario.write_bytes(_csv(conteudo))
        temporario.replace(destino / nome)          # troca atômica: quem abre o arquivo nunca vê meio CSV
    return {"situacao": "GERADO", "pasta": str(destino), "completo": len(linhas), "publico": len(publicas)}
