"""Apoio de testes (F-04): a consulta pública só serve snapshot PROMOVIDO explicitamente.

`criar_servidor_promovido` executa a promoção explícita (o mesmo passo que o operador faz com
`python -m observatorio.operacao publicar-snapshot-publico`) antes de subir o servidor de teste.
"""
from pathlib import Path

from observatorio.nucleo.banco import Banco
from observatorio.painel import indicadores
from observatorio.web.servidor import criar_servidor


def promover_snapshot(pasta) -> None:
    pasta = Path(pasta)
    banco_arq = pasta / "observatorio.sqlite3"
    if not banco_arq.is_file():
        return
    with Banco(banco_arq) as banco:
        indicadores.publicar_snapshot_publico(banco, pasta / indicadores.ARQUIVO_SNAPSHOT_PUBLICO)


def criar_servidor_promovido(pasta, *args, **kwargs):
    promover_snapshot(pasta)
    return criar_servidor(pasta, *args, **kwargs)
