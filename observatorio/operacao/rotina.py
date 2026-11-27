"""Rotina diária multiplataforma (Windows, Linux, macOS): o equivalente em Python de deploy_autonomo/rodar_diario.sh.

Reproduz o que comprovadamente funcionou em 18/11/2026: coleta feita A PARTIR DO BRASIL (computador da responsável ou
rede da SEAD), direto da fonte oficial. Etapas, cada uma com código de saída registrado:

  1. coleta da janela recente (dias_recuo) na A União;
  2. reverificação delimitada das publicações já baixadas (F-03);
  3. leitura (texto + OCR em português) e classificação GEDIV;
  4. candidato a snapshot público (a promoção continua sendo ato humano auditado, F-04);
  5. backup cifrado, quando a frase-senha estiver configurada (GEDIV_BACKUP_CHAVE ou GEDIV_BACKUP_CHAVE_ARQUIVO).

Uma trava de arquivo impede duas execuções simultâneas. O resumo de cada execução fica em <dados>/rotina/AAAAMMDD-HHMMSS.json
(sem dados pessoais). Fonte inacessível (código 4) interrompe só a coleta; as demais etapas seguem com o que já existe.
"""
from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import saida

HORARIOS_PADRAO = ("09:04", "14:04")          # America/Sao_Paulo; minuto 04 evita o pico do minuto zero
NOME_TAREFA = "ObservatorioGEDIV-Coleta"


class RotinaEmAndamento(RuntimeError):
    pass


def _processo_vivo(pid: int) -> bool:
    """True se o processo existe. Em dúvida, considera vivo (não remove trava alheia)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h = kernel32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            codigo = ctypes.c_ulong()
            return bool(kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))) and codigo.value == 259   # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(h)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def _trava_orfa(caminho: Path) -> bool:
    """Órfã: a execução que a criou não existe mais (ex.: janela fechada no meio, achado de 25/11/2026) ou tem > 6 h."""
    try:
        if (datetime.now().timestamp() - caminho.stat().st_mtime) > 6 * 3600:
            return True
        pid = int(caminho.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        return False
    return not _processo_vivo(pid)


def _trava(pasta: Path):
    """Trava simples e portável: criação exclusiva de arquivo. Trava órfã (processo encerrado ou > 6 h) é recuperada."""
    caminho = pasta / ".rotina.lock"
    try:
        if caminho.exists() and _trava_orfa(caminho):
            caminho.unlink()
        fd = os.open(caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        raise RotinaEmAndamento(f"outra execução em andamento ({caminho})") from None
    return caminho


def _cli(argumentos: list[str]) -> int:
    from .__main__ import main
    with redirect_stdout(io.StringIO()):          # a saída detalhada de cada comando não polui o log da rotina
        try:
            return int(main(argumentos) or 0)
        except SystemExit as e:                   # erros de uso do argparse
            return int(e.code or saida.USO_INCORRETO)


def executar(dados: str | Path, *, fontes=("auniao",), dias_recuo: int = 3, reverificar_dias: int = 1,
             limite_reverificacao: int = 6, backup_dir: str | Path | None = None, hoje: date | None = None) -> dict:
    pasta = Path(dados)
    pasta.mkdir(parents=True, exist_ok=True)
    hoje = hoje or date.today()
    trava = _trava(pasta)
    etapas: list[dict] = []
    try:
        def etapa(nome, argumentos):
            codigo = _cli(argumentos)
            etapas.append({"etapa": nome, "codigo": codigo, "situacao": saida.NOMES.get(codigo, str(codigo))})
            return codigo

        fonte_args = [x for f in fontes for x in ("--fonte", f)]
        inicio = (hoje - timedelta(days=dias_recuo)).isoformat()
        rc_coleta = etapa("coleta", ["coletar-intervalo", *fonte_args, "--inicio", inicio, "--fim", hoje.isoformat(),
                                     "--dados", str(pasta)])
        if reverificar_dias > 0 and rc_coleta == saida.SUCESSO:
            etapa("reverificacao", ["coletar-intervalo", "--reverificar", *fonte_args,
                                    "--inicio", (hoje - timedelta(days=reverificar_dias)).isoformat(),
                                    "--fim", hoje.isoformat(), "--limite", str(limite_reverificacao), "--dados", str(pasta)])
        if (pasta / "observatorio.sqlite3").is_file():
            etapa("aplicar_revisao", ["aplicar-revisao", "--dados", str(pasta)])
            etapa("leitura_e_classificacao", ["executar", "--dados", str(pasta)])
            etapa("candidato_snapshot", ["gerar-candidato-snapshot", "--dados", str(pasta)])
            etapa("exportacao_csv", ["exportar-csv", "--dados", str(pasta)])
            etapa("gerar_revisao", ["gerar-revisao", "--dados", str(pasta)])
            if os.environ.get("GEDIV_BACKUP_CHAVE") or os.environ.get("GEDIV_BACKUP_CHAVE_ARQUIVO"):
                etapa("backup_cifrado", ["backup", "--dados", str(pasta), "--saida", str(backup_dir or pasta.parent / "backups")])
            else:
                etapas.append({"etapa": "backup_cifrado", "codigo": None, "situacao": "NAO_CONFIGURADO"})
    finally:
        trava.unlink(missing_ok=True)
    aceitos = (None, saida.SUCESSO, saida.CONCLUIDO_COM_PENDENCIAS)
    falhas_posteriores = [e for e in etapas if e["etapa"] != "coleta" and e["codigo"] not in aceitos]
    if falhas_posteriores:
        codigo = saida.FALHA
    elif rc_coleta not in (saida.SUCESSO, saida.CONCLUIDO_COM_PENDENCIAS):
        codigo = rc_coleta                       # 4 = fonte inacessível/recusada; 1 = falha da coleta
    elif any(e["codigo"] == saida.CONCLUIDO_COM_PENDENCIAS for e in etapas):
        codigo = saida.CONCLUIDO_COM_PENDENCIAS
    else:
        codigo = saida.SUCESSO
    resumo = {"inicio_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dados": str(pasta),
              "janela": {"inicio": inicio, "fim": hoje.isoformat()}, "etapas": etapas, "codigo_de_saida": codigo}
    registro = pasta / "rotina"
    registro.mkdir(exist_ok=True)
    (registro / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumo


def script_windows(dados: str | Path, python: str | None = None, repositorio: str | Path | None = None) -> str:
    """Conteúdo do .cmd chamado pelo Agendador (o /TR do schtasks aceita no máximo 261 caracteres)."""
    python = python or sys.executable
    repositorio = Path(repositorio or Path(__file__).resolve().parents[2])
    return (f'@echo off\r\ncd /d "{repositorio}"\r\n'
            f'"{python}" -m observatorio.operacao rotina-diaria --dados "{dados}" >> "{Path(dados) / "rotina" / "agendador.log"}" 2>&1\r\n')


def acao_oculta_windows(dados: str | Path, python: str | None = None, repositorio: str | Path | None = None) -> str:
    """Ação da tarefa agendada SEM janela de console: pythonw.exe + scripts/gediv_rotina_windows.pyw.

    Achado de 25/11/2026: com o .cmd, a tarefa abre uma janela preta; fechá-la encerra a coleta no meio
    (código 0xC000013A, "Último resultado" -1073741510). Com pythonw não há janela para fechar.
    """
    import ntpath                               # regras de caminho do Windows, também nos testes em Linux
    python = str(python or sys.executable)
    pythonw = (ntpath.join(ntpath.dirname(python), "pythonw.exe")
               if ntpath.basename(python).lower() == "python.exe" else python)
    repositorio = str(repositorio or Path(__file__).resolve().parents[2])
    lancador = ntpath.join(repositorio, "scripts", "gediv_rotina_windows.pyw")
    return f'"{pythonw}" "{lancador}" --dados "{dados}"'


def comandos_agendamento_windows(script: str | Path, horarios=HORARIOS_PADRAO) -> list[list[str]]:
    """Uma tarefa diária por horário, com o usuário atual. Computador desligado no horário: a próxima execução recupera a
    janela, porque a coleta sempre recua alguns dias."""
    acao = str(script) if str(script).startswith('"') else f'"{script}"'    # aceita um caminho ou uma ação já pronta
    return [["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", h, "/TN", f"{NOME_TAREFA}-{h.replace(':', '')}",
             "/TR", acao] for h in horarios]
