"""Prova de coleta real (P0-1) em um único comando, para rodar num computador no Brasil.

    python -m observatorio.operacao prova-coleta --dados C:\\GEDIV\\dados --saida C:\\GEDIV\\prova-p0-1.json

Sequência, cada etapa com evidência:
  1. sonda: descobre a edição mais recente na fonte oficial e baixa o PDF num diretório temporário vazio
     (integridade estrutural, páginas e SHA-256);
  2. coleta do dia dessa edição (ou de --data) para a base privada em --dados (acervo por SHA-256);
  3. leitura (texto e OCR) e classificação GEDIV;
  4. cobertura do dia (COMPLETO, SEM_PUBLICACAO_LISTADA, PENDENTE, QUARENTENA...);
  5. reexecução da mesma coleta: nenhum arquivo ou publicação nova (idempotência).

O relatório (--saida) traz só contagens, situações, URLs oficiais e SHA-256: NENHUM nome, matrícula ou processo.
É esse arquivo que volta para a auditoria. PDFs e banco ficam só em --dados.
Código de saída: 0 = aprovado; 3 = concluído com pendências; 4 = fonte inacessível; 1 = reprovado.
"""
from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

from . import aquisicao, saida

VERSAO_PROVA = "prova-p0-1-2026.11.25"


def _contagens(dados: Path) -> dict:
    banco = dados / "observatorio.sqlite3"
    if not banco.is_file():
        return {"arquivos": 0, "publicacoes": 0}
    import sqlite3
    with closing(sqlite3.connect(banco)) as con:
        return {"arquivos": con.execute("SELECT COUNT(*) FROM arquivo").fetchone()[0],
                "publicacoes": con.execute("SELECT COUNT(*) FROM publicacao").fetchone()[0]}


def _resumo_do_dia(dados: Path, dia: date, fonte: str) -> dict:
    """Agregados do dia, sem dados pessoais."""
    import sqlite3
    banco = dados / "observatorio.sqlite3"
    if not banco.is_file():
        return {}
    with closing(sqlite3.connect(banco)) as con:
        con.row_factory = sqlite3.Row
        pubs = [dict(r) for r in con.execute(
            "SELECT url, tipo, ordem, estado, sha256 FROM publicacao WHERE fonte=? AND data_publicacao=? ORDER BY ordem",
            (fonte, dia.isoformat()))]
        shas = sorted({p["sha256"] for p in pubs if p["sha256"]})
        marca = ",".join("?" * len(shas)) or "''"
        leituras = [dict(r) for r in con.execute(
            f"SELECT sha256, situacao, paginas, paginas_sem_texto, paginas_com_pendencia FROM leitura WHERE sha256 IN ({marca})", shas)]
        metodos = {r[0]: r[1] for r in con.execute(
            f"SELECT metodo, COUNT(*) FROM pagina WHERE sha256 IN ({marca}) GROUP BY metodo", shas)}
        atos = con.execute(f"SELECT COUNT(*) FROM ato WHERE sha256 IN ({marca})", shas).fetchone()[0]
        por_eixo = {(r[0] or "SEM_EIXO"): r[1] for r in con.execute(
            f"SELECT eixo, COUNT(*) FROM ato WHERE sha256 IN ({marca}) GROUP BY eixo", shas)}
        decisoes = {(r[0] or "SEM_RESULTADO"): r[1] for r in con.execute(
            f"SELECT resultado, COUNT(*) FROM decisao WHERE sha256 IN ({marca}) GROUP BY resultado", shas)}
        validacao = {(r[0] or "SEM_VALIDACAO"): r[1] for r in con.execute(
            f"SELECT validacao, COUNT(*) FROM decisao WHERE sha256 IN ({marca}) GROUP BY validacao", shas)}
    return {"publicacoes": [{k: p[k] for k in ("url", "tipo", "ordem", "estado", "sha256")} for p in pubs],
            "leituras": leituras, "paginas_por_metodo": metodos, "atos_gediv": atos, "atos_por_eixo": por_eixo,
            "decisoes_por_resultado": decisoes, "decisoes_por_validacao": validacao}


def executar(dados: str | Path, *, fonte: str = "auniao", data: date | None = None, sonda=None, coletar=None,
             cobertura=None, ler=None) -> dict:
    """Executa a prova. As funções podem ser injetadas nos testes (sem rede)."""
    sonda = sonda or aquisicao.sonda
    coletar = coletar or aquisicao.coletar
    cobertura = cobertura or aquisicao.cobertura
    if ler is None:
        from .rotina import _cli
        ler = lambda pasta: _cli(["executar", "--dados", str(pasta)])  # noqa: E731
    pasta = Path(dados)
    pasta.mkdir(parents=True, exist_ok=True)
    rel = {"versao_prova": VERSAO_PROVA, "inicio_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "ambiente": aquisicao.ambiente(), "fonte": fonte, "etapas": {}, "criterios": {}, "resultado": None}
    E, C = rel["etapas"], rel["criterios"]

    s = sonda(fonte)
    E["sonda"] = {"situacao": s.get("situacao"), "edicao": s.get("edicao"),
                  "listagem": {k: (s.get("listagem") or {}).get(k) for k in ("url", "status", "itens", "erro", "detalhe")}}
    C["download_integro"] = s.get("situacao") == "DOWNLOAD_INTEGRO"
    if not C["download_integro"]:
        rel["resultado"], rel["codigo_de_saida"] = "FONTE_INACESSIVEL", saida.NAO_EXECUTADO
        return _fechar(rel)

    dia = data or date.fromisoformat(s["edicao"]["data"])
    rel["dia"] = dia.isoformat()
    antes = _contagens(pasta)
    c1 = coletar(str(pasta), [fonte], dia, dia, None, False, False)
    depois1 = _contagens(pasta)
    E["coleta"] = {"pendencias": c1.get("pendencias"), "novos": {k: depois1[k] - antes[k] for k in antes},
                   "desempenho": c1.get("desempenho")}

    E["leitura_e_classificacao"] = {"codigo": ler(pasta)}

    m = cobertura(str(pasta), [fonte], dia, dia)
    linha = next((l for l in m.get("dias", []) if l.get("data") == dia.isoformat()), {})
    E["cobertura"] = {k: linha.get(k) for k in ("situacao", "motivo", "listadas", "baixadas", "arquivos_distintos")}

    c2 = coletar(str(pasta), [fonte], dia, dia, None, False, False)
    depois2 = _contagens(pasta)
    E["reexecucao"] = {"pendencias": c2.get("pendencias"), "novos": {k: depois2[k] - depois1[k] for k in depois1}}

    dia_resumo = _resumo_do_dia(pasta, dia, fonte)
    E["dia"] = dia_resumo
    sha_sonda = (s.get("edicao") or {}).get("sha256")
    shas_dia = {p["sha256"] for p in dia_resumo.get("publicacoes", []) if p.get("sha256")}
    from ..nucleo.acervo import Acervo
    acervo = Acervo(pasta / "acervo")
    C["original_no_acervo"] = bool(shas_dia) and all(acervo.conferir(sha) for sha in shas_dia)   # SHA-256 recalculado
    C["mesmo_sha_da_sonda"] = (sha_sonda in shas_dia) if (data is None and sha_sonda) else None
    C["cobertura_completa"] = E["cobertura"].get("situacao") in ("COMPLETO", "SEM_PUBLICACAO_LISTADA")
    C["reexecucao_sem_duplicidade"] = all(v == 0 for v in E["reexecucao"]["novos"].values())
    leituras = dia_resumo.get("leituras", [])
    C["leitura_sem_erro"] = bool(leituras) and all(l["situacao"] != "ERRO" for l in leituras)
    C["leitura_completa"] = bool(leituras) and all(l["situacao"] == "LIDA" for l in leituras)

    obrigatorios = ("download_integro", "original_no_acervo", "cobertura_completa", "reexecucao_sem_duplicidade",
                    "leitura_sem_erro")
    if C["mesmo_sha_da_sonda"] is False or not all(C[k] for k in obrigatorios):
        rel["resultado"], rel["codigo_de_saida"] = "REPROVADO", saida.FALHA
    elif not C["leitura_completa"] or E["coleta"]["pendencias"]:
        rel["resultado"], rel["codigo_de_saida"] = "APROVADO_COM_PENDENCIAS", saida.CONCLUIDO_COM_PENDENCIAS
    else:
        rel["resultado"], rel["codigo_de_saida"] = "APROVADO", saida.SUCESSO
    return _fechar(rel)


def _fechar(rel: dict) -> dict:
    rel["fim_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return rel


def gravar(rel: dict, destino: str | None) -> None:
    texto = json.dumps(rel, ensure_ascii=False, indent=2)
    if destino:
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        Path(destino).write_text(texto + "\n", encoding="utf-8")
    print(texto)
