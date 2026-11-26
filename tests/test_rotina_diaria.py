"""Rotina diária multiplataforma (equivalente Python do rodar_diario.sh) e agendamento no Windows. Sem rede externa."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from observatorio.operacao import rotina, saida


class TesteRotina(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dados = Path(self._tmp.name) / "dados"
        self.chamadas = []

    def simular(self, codigos, criar_banco=True):
        def falso(argumentos):
            self.chamadas.append(argumentos)
            if criar_banco:
                (self.dados / "observatorio.sqlite3").touch()
            return codigos.get(argumentos[0] + ("+rever" if "--reverificar" in argumentos else ""), 0)
        return mock.patch.object(rotina, "_cli", side_effect=falso)

    def test_sequencia_completa_janela_e_registro(self):
        with self.simular({}):
            r = rotina.executar(self.dados, hoje=date(2026, 11, 25))
        self.assertEqual([e["etapa"] for e in r["etapas"]],
                         ["coleta", "reverificacao", "leitura_e_classificacao", "candidato_snapshot", "exportacao_csv", "backup_cifrado"])
        self.assertEqual(r["janela"], {"inicio": "2026-11-22", "fim": "2026-11-25"})
        self.assertIn("--fonte", self.chamadas[0])
        self.assertEqual(r["codigo_de_saida"], saida.SUCESSO)
        self.assertEqual(len(list((self.dados / "rotina").glob("*.json"))), 1)
        self.assertFalse((self.dados / ".rotina.lock").exists())

    def test_fonte_recusada_nao_reverifica_mas_processa_o_que_ja_existe(self):
        with self.simular({"coletar-intervalo": saida.NAO_EXECUTADO}):
            r = rotina.executar(self.dados, hoje=date(2026, 11, 25))
        etapas = [e["etapa"] for e in r["etapas"]]
        self.assertNotIn("reverificacao", etapas)
        self.assertIn("leitura_e_classificacao", etapas)
        self.assertEqual(r["codigo_de_saida"], saida.NAO_EXECUTADO)

    def test_falha_posterior_vira_falha_geral(self):
        with self.simular({"executar": saida.FALHA}):
            r = rotina.executar(self.dados, hoje=date(2026, 11, 25))
        self.assertEqual(r["codigo_de_saida"], saida.FALHA)

    def test_trava_impede_execucao_simultanea(self):
        self.dados.mkdir(parents=True)
        (self.dados / ".rotina.lock").write_text(str(__import__("os").getpid()))   # execução viva
        with self.simular({}), self.assertRaises(rotina.RotinaEmAndamento):
            rotina.executar(self.dados, hoje=date(2026, 11, 25))

    def test_backup_so_com_frase_configurada(self):
        with self.simular({}), mock.patch.dict("os.environ", {"GEDIV_BACKUP_CHAVE": "frase-senha-de-teste-longa-2026"}):
            rotina.executar(self.dados, hoje=date(2026, 11, 25))
        self.assertTrue(any(c[0] == "backup" for c in self.chamadas))


class TesteTravaOrfa(unittest.TestCase):
    """Achado de 25/11/2026: a execução encerrada à força deixou .rotina.lock e a seguinte saiu EM_ANDAMENTO."""

    def test_trava_de_processo_encerrado_e_recuperada(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".rotina.lock").write_text("999999999", encoding="utf-8")   # PID inexistente
            trava = rotina._trava(Path(t))
            self.assertEqual(trava.read_text(encoding="utf-8"), str(__import__("os").getpid()))
            trava.unlink()

    def test_trava_de_processo_vivo_e_respeitada(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".rotina.lock").write_text(str(__import__("os").getpid()), encoding="utf-8")
            with self.assertRaises(rotina.RotinaEmAndamento):
                rotina._trava(Path(t))


class TesteAgendamentoWindows(unittest.TestCase):
    def test_tarefas_diarias_e_script_curto(self):
        script = r"C:\GEDIV\dados\gediv-rotina.cmd"
        cmds = rotina.comandos_agendamento_windows(script)
        self.assertEqual([c[c.index("/ST") + 1] for c in cmds], ["09:04", "14:04"])
        for c in cmds:
            self.assertEqual(c[:5], ["schtasks", "/Create", "/F", "/SC", "DAILY"])
            self.assertLessEqual(len(c[c.index("/TR") + 1]), 261)      # limite do Agendador do Windows
        conteudo = rotina.script_windows(r"C:\GEDIV\dados", python=r"C:\Python313\python.exe", repositorio=r"C:\GEDIV\repo")
        self.assertIn("rotina-diaria", conteudo)
        self.assertIn("\r\n", conteudo)

    def test_tarefa_sem_janela_de_console(self):
        """Achado de 25/11/2026: fechar a janela do .cmd encerrava a coleta (0xC000013A). A tarefa usa pythonw + .pyw."""
        acao = rotina.acao_oculta_windows(r"C:\GEDIV\dados", python=r"C:\Py\python.exe", repositorio=r"C:\GEDIV\repo")
        self.assertIn("pythonw.exe", acao)
        self.assertIn("gediv_rotina_windows.pyw", acao)
        self.assertIn('--dados "C:\\GEDIV\\dados"'.replace("\\\\", "\\"), acao)
        for c in rotina.comandos_agendamento_windows(acao):
            tr = c[c.index("/TR") + 1]
            self.assertEqual(tr, acao)
            self.assertLessEqual(len(tr), 261)
        self.assertTrue((Path(rotina.__file__).resolve().parents[2] / "scripts" / "gediv_rotina_windows.pyw").is_file())

    def test_lancador_grava_registro_e_codigo(self):
        import importlib.util
        caminho = Path(rotina.__file__).resolve().parents[2] / "scripts" / "gediv_rotina_windows.pyw"
        from importlib.machinery import SourceFileLoader
        mod = SourceFileLoader("gediv_rotina_windows", str(caminho)).load_module()
        with tempfile.TemporaryDirectory() as t, mock.patch("observatorio.operacao.__main__.main", return_value=4) as cli:
            self.assertEqual(mod.main(["--dados", t]), 4)
            log = (Path(t) / "rotina" / "agendador.log").read_text(encoding="utf-8")
        cli.assert_called_once()
        self.assertIn("=== início", log)
        self.assertIn("código 4", log)

    def test_cli_simulacao_e_aplicar_recusado_fora_do_windows(self):
        from observatorio.operacao.__main__ import main
        with tempfile.TemporaryDirectory() as t, mock.patch("sys.stdout") as out:
            self.assertEqual(main(["agendar-windows", "--dados", t]), 0)
            if __import__("os").name != "nt":
                self.assertEqual(main(["agendar-windows", "--dados", t, "--aplicar"]), saida.USO_INCORRETO)


if __name__ == "__main__":
    unittest.main()
