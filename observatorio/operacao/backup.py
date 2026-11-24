"""Backup cifrado e restauração verificada da base canônica (SQLite + contas + acervo de PDFs).

Formato `.gedivbak` (versão 1):
    cabeçalho JSON (uma linha): formato, versão, sal do scrypt, parâmetros, tamanho do bloco
    blocos: [4 bytes tamanho][12 bytes nonce][texto cifrado AES-256-GCM + etiqueta]
    O dado associado (AAD) de cada bloco liga o bloco ao cabeçalho, à sua posição e à marca de último bloco:
    reordenar, truncar, trocar ou adulterar qualquer bloco faz a restauração FALHAR (nada é gravado pela metade).

Conteúdo (um tar dentro da cifra):
    observatorio.sqlite3, contas.sqlite3 (cópias consistentes pela API de backup do SQLite),
    acervo/xx/<sha256>.pdf (somente os arquivos registrados no banco) e MANIFESTO.json (SHA-256 de cada item).

A chave vem de uma FRASE-SENHA fora do Git (variável GEDIV_BACKUP_CHAVE ou arquivo indicado em
GEDIV_BACKUP_CHAVE_ARQUIVO), derivada por scrypt. Perder a frase-senha torna o backup irrecuperável: a custódia é
institucional (docs/OPERACAO.md).

Restauração: só em diretório NOVO; confere o SHA-256 de cada item contra o manifesto, roda PRAGMA integrity_check,
confere os PDFs pelo próprio hash e encerra todas as sessões (as contas restauradas precisam de novo login).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import secrets
import shutil
import sqlite3
import struct
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FORMATO = "GEDIVBAK"
VERSAO = 1
BLOCO = 8 * 1024 * 1024
SCRYPT = {"n": 2 ** 15, "r": 8, "p": 1}
MIN_FRASE = 16


class ErroBackup(Exception):
    pass


def _aesgcm(chave: bytes):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as erro:                     # dependência declarada em requirements.txt
        raise ErroBackup("biblioteca 'cryptography' ausente: python -m pip install -r requirements.txt") from erro
    return AESGCM(chave)


def frase_senha(explicita: str | None = None) -> str:
    frase = explicita or os.environ.get("GEDIV_BACKUP_CHAVE")
    arquivo = os.environ.get("GEDIV_BACKUP_CHAVE_ARQUIVO")
    if not frase and arquivo:
        frase = Path(arquivo).read_text(encoding="utf-8").strip()
    if not frase or len(frase) < MIN_FRASE:
        raise ErroBackup(f"frase-senha do backup ausente ou curta (mínimo {MIN_FRASE} caracteres): "
                         "defina GEDIV_BACKUP_CHAVE ou GEDIV_BACKUP_CHAVE_ARQUIVO")
    return frase


def _derivar(frase: str, sal: bytes, p=SCRYPT) -> bytes:
    return hashlib.scrypt(frase.encode("utf-8"), salt=sal, n=p["n"], r=p["r"], p=p["p"], dklen=32, maxmem=2 ** 27)


def _sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for parte in iter(lambda: f.read(1 << 20), b""):
            h.update(parte)
    return h.hexdigest()


def _copiar_sqlite(origem: Path, destino: Path) -> None:
    with sqlite3.connect(origem.resolve().as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(destino) as dst:
        src.backup(dst)
    with sqlite3.connect(destino) as chk:
        if chk.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ErroBackup(f"cópia de {origem.name} reprovada no integrity_check")


def _montar_tar(dados: Path, pasta_tmp: Path) -> tuple[Path, dict]:
    banco = dados / "observatorio.sqlite3"
    if not banco.is_file():
        raise ErroBackup(f"banco ausente: {banco}")
    itens: dict[str, str] = {}
    preparados = pasta_tmp / "conteudo"
    preparados.mkdir()
    _copiar_sqlite(banco, preparados / "observatorio.sqlite3")
    itens["observatorio.sqlite3"] = _sha256_arquivo(preparados / "observatorio.sqlite3")
    if (dados / "contas.sqlite3").is_file():
        _copiar_sqlite(dados / "contas.sqlite3", preparados / "contas.sqlite3")
        itens["contas.sqlite3"] = _sha256_arquivo(preparados / "contas.sqlite3")
    with sqlite3.connect(preparados / "observatorio.sqlite3") as con:
        hashes = [r[0] for r in con.execute("SELECT sha256 FROM arquivo ORDER BY sha256")]
    ausentes = []
    tar_caminho = pasta_tmp / "conteudo.tar"
    with tarfile.open(tar_caminho, "w") as tar:
        for nome in ("observatorio.sqlite3", "contas.sqlite3"):
            if nome in itens:
                tar.add(preparados / nome, arcname=nome)
        for sha in hashes:
            relativo = f"acervo/{sha[:2]}/{sha}.pdf"
            caminho = dados / relativo
            if not caminho.is_file():
                ausentes.append(sha)
                continue
            if _sha256_arquivo(caminho) != sha:
                raise ErroBackup(f"PDF do acervo não confere com o próprio hash: {sha}")
            tar.add(caminho, arcname=relativo)
            itens[relativo] = sha
        manifesto = {"formato": FORMATO, "versao": VERSAO, "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "itens": itens, "pdfs_registrados": len(hashes), "pdfs_ausentes_no_acervo": ausentes}
        bruto = json.dumps(manifesto, ensure_ascii=False, indent=1).encode("utf-8")
        info = tarfile.TarInfo("MANIFESTO.json")
        info.size = len(bruto)
        tar.addfile(info, io.BytesIO(bruto))
    return tar_caminho, manifesto


def gerar(dados_dir: str | Path, saida_dir: str | Path, frase: str | None = None) -> dict:
    """Gera <saida>/gediv-AAAAMMDDTHHMMSSZ.gedivbak (cifrado) e o .sha256 ao lado."""
    dados, saida = Path(dados_dir), Path(saida_dir)
    chave_frase = frase_senha(frase)
    saida.mkdir(parents=True, exist_ok=True)
    sal = secrets.token_bytes(16)
    cabecalho = {"formato": FORMATO, "versao": VERSAO, "kdf": "scrypt", "sal": sal.hex(), **SCRYPT, "bloco": BLOCO}
    linha = (json.dumps(cabecalho, sort_keys=True) + "\n").encode("ascii")
    aes = _aesgcm(_derivar(chave_frase, sal))
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = saida / f"gediv-{carimbo}.gedivbak"
    tmp_destino = destino.with_suffix(".gedivbak.tmp")
    with tempfile.TemporaryDirectory(prefix="gediv-backup-") as tmp:
        tar_caminho, manifesto = _montar_tar(dados, Path(tmp))
        tamanho = tar_caminho.stat().st_size
        with open(tar_caminho, "rb") as origem, open(tmp_destino, "wb") as f:
            f.write(linha)
            indice, lidos = 0, 0
            while True:
                bloco = origem.read(BLOCO)
                lidos += len(bloco)
                ultimo = lidos >= tamanho
                aad = linha + struct.pack(">Q?", indice, ultimo)
                nonce = secrets.token_bytes(12)
                cifrado = aes.encrypt(nonce, bloco, aad)
                f.write(struct.pack(">I", len(cifrado)) + nonce + cifrado)
                indice += 1
                if ultimo:
                    break
            f.flush()
            os.fsync(f.fileno())
    os.replace(tmp_destino, destino)
    sha = _sha256_arquivo(destino)
    destino.with_suffix(".gedivbak.sha256").write_text(f"{sha}  {destino.name}\n", encoding="utf-8")
    return {"resultado": "BACKUP_GERADO", "arquivo": str(destino), "sha256": sha, "itens": len(manifesto["itens"]),
            "pdfs_registrados": manifesto["pdfs_registrados"], "pdfs_ausentes_no_acervo": len(manifesto["pdfs_ausentes_no_acervo"])}


def _decifrar(arquivo: Path, frase: str, destino_tar: Path) -> None:
    with open(arquivo, "rb") as f:
        linha = f.readline()
        try:
            cab = json.loads(linha)
        except ValueError:
            raise ErroBackup("cabeçalho do backup ilegível") from None
        if cab.get("formato") != FORMATO or cab.get("versao") != VERSAO:
            raise ErroBackup("formato de backup desconhecido")
        aes = _aesgcm(_derivar(frase, bytes.fromhex(cab["sal"]), cab))
        indice, terminou = 0, False
        with open(destino_tar, "wb") as saida:
            while True:
                tamanho = f.read(4)
                if not tamanho:
                    break
                if terminou:
                    raise ErroBackup("dados após o último bloco: arquivo adulterado")
                (n,) = struct.unpack(">I", tamanho)
                nonce, cifrado = f.read(12), f.read(n)
                if len(nonce) != 12 or len(cifrado) != n:
                    raise ErroBackup("backup truncado")
                for ultimo in (False, True):
                    try:
                        claro = aes.decrypt(nonce, cifrado, linha + struct.pack(">Q?", indice, ultimo))
                        terminou = ultimo
                        break
                    except Exception:
                        claro = None
                if claro is None:
                    raise ErroBackup("falha de autenticação: frase-senha errada ou backup adulterado")
                saida.write(claro)
                indice += 1
        if not terminou:
            raise ErroBackup("backup truncado: último bloco ausente")


def restaurar(arquivo: str | Path, destino_dir: str | Path, frase: str | None = None) -> dict:
    """Restaura num diretório NOVO e verifica tudo antes de declarar sucesso."""
    arquivo, destino = Path(arquivo), Path(destino_dir)
    if destino.exists() and any(destino.iterdir()):
        raise ErroBackup(f"destino já existe e não está vazio: {destino} (a restauração nunca sobrescreve)")
    chave_frase = frase_senha(frase)
    with tempfile.TemporaryDirectory(prefix="gediv-restauro-") as tmp:
        tar_caminho = Path(tmp) / "conteudo.tar"
        _decifrar(arquivo, chave_frase, tar_caminho)
        extraido = Path(tmp) / "extraido"
        with tarfile.open(tar_caminho) as tar:
            for membro in tar.getmembers():
                if not membro.isfile() or membro.name.startswith(("/", "..")) or ".." in Path(membro.name).parts:
                    raise ErroBackup(f"item inesperado no backup: {membro.name}")
            tar.extractall(extraido, filter="data")
        manifesto = json.loads((extraido / "MANIFESTO.json").read_text(encoding="utf-8"))
        for relativo, sha in manifesto["itens"].items():
            caminho = extraido / relativo
            if not caminho.is_file() or _sha256_arquivo(caminho) != sha:
                raise ErroBackup(f"item não confere com o manifesto: {relativo}")
        for nome in ("observatorio.sqlite3", "contas.sqlite3"):
            if (extraido / nome).is_file():
                with sqlite3.connect(extraido / nome) as con:
                    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ErroBackup(f"{nome} reprovado no integrity_check")
        sessoes_encerradas = 0
        if (extraido / "contas.sqlite3").is_file():
            with sqlite3.connect(extraido / "contas.sqlite3") as con:
                sessoes_encerradas = con.execute("DELETE FROM sessao").rowcount
        with sqlite3.connect(extraido / "observatorio.sqlite3") as con:
            contagens = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                         for t in ("arquivo", "publicacao", "ato", "decisao", "auditoria")}
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.exists():
            _mover_conteudo(extraido, destino)
        else:
            shutil.move(str(extraido), str(destino))      # pode cruzar sistemas de arquivos (tmp -> volume de dados)
    (destino / "MANIFESTO.json").unlink(missing_ok=True)
    return {"resultado": "RESTAURADO", "destino": str(destino), "itens_conferidos": len(manifesto["itens"]),
            "contagens": contagens, "sessoes_encerradas": sessoes_encerradas, "gerado_em": manifesto["gerado_em"]}


def _mover_conteudo(origem: Path, destino: Path) -> None:
    for item in origem.iterdir():
        shutil.move(str(item), str(destino / item.name))
