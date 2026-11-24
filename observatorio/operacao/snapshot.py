"""Ciclo de vida do snapshot público (achado F-04): candidato -> promoção auditada -> revogação auditada.

- A rotina automática só GERA um candidato (`snapshot_publico.candidato.json`); nunca publica.
- A consulta pública (`/api/painel`, `/api/data`) só serve o arquivo PROMOVIDO (`snapshot_publico.json`).
- Promover e revogar exigem responsável e justificativa e ficam na trilha de auditoria do banco.
- Revogar retira o arquivo promovido na hora: o servidor responde 503 na requisição seguinte. O conteúdo revogado é
  guardado ao lado, com carimbo de tempo, como evidência.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..nucleo.banco import Banco
from ..painel import indicadores

ARQUIVO_CANDIDATO = "snapshot_publico.candidato.json"


class ErroSnapshot(ValueError):
    pass


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _exigir_ator(responsavel: str | None, justificativa: str | None) -> tuple[str, str]:
    resp, just = (responsavel or "").strip(), (justificativa or "").strip()
    if not resp or not just:
        raise ErroSnapshot("promoção e revogação exigem --responsavel e --justificativa (trilha de auditoria)")
    return resp[:120], just[:1000]


def _banco(pasta: Path) -> Banco:
    caminho = pasta / "observatorio.sqlite3"
    if not caminho.is_file():
        raise FileNotFoundError(str(caminho))
    return Banco(caminho)


def gerar_candidato(pasta_dados: str | Path) -> dict:
    """Gera e valida o candidato a partir do banco; não altera a consulta pública."""
    pasta = Path(pasta_dados)
    banco = _banco(pasta)
    try:
        destino = pasta / ARQUIVO_CANDIDATO
        snap = indicadores.publicar_snapshot_publico(banco, destino)
    finally:
        banco.fechar()
    return {"resultado": "CANDIDATO_GERADO", "arquivo": str(destino), "sha256": _sha256(destino),
            "gerado_em": snap.get("gerado_em")}


def promover(pasta_dados: str | Path, responsavel: str | None, justificativa: str | None, *,
             gerar_agora: bool = False) -> dict:
    """Promove o candidato (ou um snapshot gerado agora) a snapshot público, com auditoria."""
    resp, just = _exigir_ator(responsavel, justificativa)
    pasta = Path(pasta_dados)
    if gerar_agora:
        gerar_candidato(pasta)
    candidato = pasta / ARQUIVO_CANDIDATO
    if not candidato.is_file():
        raise ErroSnapshot("não há candidato: rode gerar-candidato-snapshot (ou use --gerar)")
    snap = indicadores.validar_snapshot_publico(json.loads(candidato.read_text(encoding="utf-8")))
    destino = pasta / indicadores.ARQUIVO_SNAPSHOT_PUBLICO
    anterior = _sha256(destino) if destino.is_file() else None
    banco = _banco(pasta)
    try:
        indicadores.publicar_snapshot_publico(None, destino, snapshot=snap)
        novo = _sha256(destino)
        with banco.con:
            banco.auditar(resp, "PROMOVER_SNAPSHOT_PUBLICO", "snapshot_publico", destino.name,
                          {"sha256": anterior}, {"sha256": novo, "gerado_em": snap.get("gerado_em")}, just)
    finally:
        banco.fechar()
    return {"resultado": "PROMOVIDO", "arquivo": str(destino), "sha256": novo, "sha256_anterior": anterior,
            "gerado_em": snap.get("gerado_em")}


def revogar(pasta_dados: str | Path, responsavel: str | None, justificativa: str | None) -> dict:
    """Retira imediatamente o snapshot público (a consulta pública passa a responder 503), com auditoria."""
    resp, just = _exigir_ator(responsavel, justificativa)
    pasta = Path(pasta_dados)
    destino = pasta / indicadores.ARQUIVO_SNAPSHOT_PUBLICO
    if not destino.is_file():
        return {"resultado": "NADA_A_REVOGAR", "arquivo": str(destino)}
    sha = _sha256(destino)
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    guardado = pasta / f"snapshot_publico.revogado-{carimbo}.json"
    os.replace(destino, guardado)            # atômico: a próxima requisição já não encontra o arquivo promovido
    banco = _banco(pasta)
    try:
        with banco.con:
            banco.auditar(resp, "REVOGAR_SNAPSHOT_PUBLICO", "snapshot_publico", destino.name,
                          {"sha256": sha}, {"guardado_como": guardado.name}, just)
    finally:
        banco.fechar()
    return {"resultado": "REVOGADO", "sha256": sha, "guardado_como": str(guardado)}
