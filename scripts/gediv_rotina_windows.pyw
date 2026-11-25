"""Lançador da rotina diária para o Agendador de Tarefas do Windows, SEM janela de console.

Executado por pythonw.exe (extensão .pyw): não abre janela preta, então não há o que fechar por engano no meio da
coleta (achado de 25/11/2026: a tarefa foi encerrada com 0xC000013A, interrupção do console). Toda a saída vai para
<dados>/rotina/agendador.log, com início, fim e código de saída; o resumo de cada execução continua em
<dados>/rotina/AAAAMMDD-HHMMSS.json.

Uso (o comando agendar-windows já cria a tarefa assim):
    pythonw.exe C:\\GEDIV\\repo\\scripts\\gediv_rotina_windows.pyw --dados C:\\GEDIV\\dados
"""
import contextlib
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dados = Path(argv[argv.index("--dados") + 1]) if "--dados" in argv else RAIZ / "dados"
    registro = dados / "rotina"
    registro.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(RAIZ))
    os.chdir(RAIZ)
    codigo = 1
    with open(registro / "agendador.log", "a", encoding="utf-8") as log, \
            contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        print(f"=== início {datetime.now().isoformat(timespec='seconds')} (pid {os.getpid()})", flush=True)
        try:
            from observatorio.operacao.__main__ import main as cli
            codigo = int(cli(["rotina-diaria", "--dados", str(dados)]) or 0)
        except SystemExit as e:
            codigo = int(e.code or 0)
        except Exception:                      # o erro fica no registro; o Agendador vê o código 1
            traceback.print_exc()
            codigo = 1
        print(f"=== fim {datetime.now().isoformat(timespec='seconds')} código {codigo}", flush=True)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
