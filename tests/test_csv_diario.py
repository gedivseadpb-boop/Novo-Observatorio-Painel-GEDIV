"""Exportação CSV diária (D-12): completo interno e público só com conferidos, iniciais e matrícula mascarada.

Todos os dados abaixo são FICTÍCIOS.
"""
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from observatorio.gerencias.gediv import processo as PROC
from observatorio.nucleo.banco import Banco
from observatorio.operacao import csv_diario as X
from observatorio.operacao.__main__ import main as cli

CAB = ("SECRETARIA DE ESTADO DA ADMINISTRAÇÃO RESENHA Nº : {n}/2026\n"
       "DIRETORIA EXECUTIVA DE RECURSOS HUMANOS EXPEDIENTE DO DIA : 08-10-2026\n"
       "GERÊNCIA EXECUTIVA DE CONCESSÃO DE DIREITOS E VANTAGENS\n")
BLOCO = (CAB.format(n=301) + "O Diretor DEFERIU os processos de LICENÇA ESPECIAL:\n"
         "SEC.EST.SAUDE SAD-PSE-2026/90301 9000301 PESSOA FICTICIA DA SILVA TREZENTOS\n"
         "SEC.EST.SAUDE SAD-PSE-2026/90302 9000302 OUTRA PESSOA FICTICIA DOS SANTOS\nPUBLIQUE-SE")


def ler(caminho: Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(caminho.read_text(encoding="utf-8-sig")), delimiter=";"))


class TesteFuncoes(unittest.TestCase):
    def test_iniciais_sem_particulas(self):
        self.assertEqual(X.iniciais("MARIA DA SILVA SOUZA"), "M.S.S.")
        self.assertEqual(X.iniciais(None), "")

    def test_matricula_opcao_b_mostra_so_os_tres_primeiros_digitos(self):
        self.assertEqual(X.mascarar_matricula("123.456-7"), "123.***-*")
        self.assertEqual(X.mascarar_matricula("9000301"), "900****")
        self.assertEqual(X.mascarar_matricula(None), "")


class TesteExportacao(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dados = Path(tmp.name)
        banco = Banco(self.dados / "observatorio.sqlite3")
        try:
            sha = "e" * 64
            banco.con.execute("INSERT INTO arquivo VALUES (?, 10, 'x', 'agora')", (sha,))
            banco.registrar_leitura(sha, "LIDA", "t", [{"numero": 3, "metodo": "TEXTO", "colunas": 2, "texto": BLOCO,
                                                        "palavras": 60, "qualidade": "OK"}], "18900", "2026-10-09", None)
            PROC.classificar_pendentes(banco)
            ids = [r[0] for r in banco.con.execute("SELECT id FROM decisao ORDER BY rowid")]
            self.assertEqual(len(ids), 2)
            banco.con.execute("UPDATE decisao SET validacao = 'CONFERIDO' WHERE id = ?", (ids[0],))
            banco.con.commit()
        finally:
            banco.fechar()

    def test_gera_completo_e_publico_so_com_conferidos(self):
        r = X.exportar(self.dados)
        self.assertEqual((r["situacao"], r["completo"], r["publico"]), ("GERADO", 2, 1))
        completo = ler(self.dados / "exportacao" / "observatorio-completo.csv")
        publico = ler(self.dados / "exportacao" / "observatorio-publico.csv")
        self.assertEqual(list(completo[0]), X.COLUNAS)
        self.assertEqual(list(publico[0]), X.COLUNAS_PUBLICAS)
        self.assertEqual({l["Status_Validacao_GEDIV"] for l in completo}, {"Validado", "Em validação"})
        self.assertEqual([l["Status_Validacao_GEDIV"] for l in publico], ["Validado"])
        self.assertEqual(publico[0]["Data_Publicacao"], "2026-10-09")
        self.assertEqual(len(publico[0]["SHA256_Edicao"]), 64)
        self.assertTrue(publico[0]["Versao_Regras"])

    def test_publico_sem_nome_completo_e_com_matricula_mascarada(self):
        X.exportar(self.dados)
        texto = (self.dados / "exportacao" / "observatorio-publico.csv").read_text(encoding="utf-8-sig")
        self.assertNotIn("FICTICIA", texto)                 # nenhum nome por extenso
        self.assertNotIn("9000301", texto)                  # nenhuma matrícula completa
        self.assertIn("900****", texto)
        linha = ler(self.dados / "exportacao" / "observatorio-publico.csv")[0]
        self.assertEqual(linha["Servidor_Iniciais"], "P.F.S.T.")
        self.assertEqual(linha["Observacoes"], "")

    def test_reexecucao_substitui_sem_acumular(self):
        X.exportar(self.dados)
        X.exportar(self.dados)
        self.assertEqual(len(ler(self.dados / "exportacao" / "observatorio-completo.csv")), 2)
        self.assertEqual(sorted(p.name for p in (self.dados / "exportacao").iterdir()),
                         ["observatorio-completo.csv", "observatorio-publico.csv"])

    def test_camada1_alertas_objetivos_so_no_completo(self):
        r = X.exportar(self.dados)
        self.assertEqual(r["com_alerta"] + r["sem_alerta"], 2)
        completo = ler(self.dados / "exportacao" / "observatorio-completo.csv")
        self.assertIn("Motivo_Alerta", completo[0])
        self.assertNotIn("Motivo_Alerta", ler(self.dados / "exportacao" / "observatorio-publico.csv")[0])

    def test_regras_de_consistencia(self):
        base = {"id": "x", "processo": "SAD-PSE-2026/90301", "matricula": "123.456-7", "servidor": "MARIA SOUZA",
                "resultado": "DEFERIDO", "eixo": "PROGRESSAO", "modalidade": "VERTICAL", "grupo": "AST",
                "subcategoria": None, "metodo": "TEXTO", "conflito": 0, "pendencias": "[]"}
        self.assertEqual(X.alertas(base, set()), [])
        ruim = dict(base, processo="SAD-PSE-2O26/9O301", matricula="12A45", servidor="MAR1A", resultado="NAO_INFORMADO",
                    grupo=None, metodo="OCR", conflito=1)
        motivos = X.alertas(ruim, {"x"})
        for esperado in ("processo fora do padrão", "matrícula fora do padrão", "nome com dígitos (possível erro de OCR)",
                         "resultado não informado", "grupo pendente", "página lida por OCR", "possível duplicidade",
                         "conflito aberto"):
            self.assertIn(esperado, motivos)

    def test_sem_banco_nao_falha(self):
        with tempfile.TemporaryDirectory() as vazio:
            self.assertEqual(X.exportar(vazio)["situacao"], "SEM_BANCO")

    def test_comando_na_cli(self):
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli(["exportar-csv", "--dados", str(self.dados)]), 0)
        self.assertTrue((self.dados / "exportacao" / "observatorio-publico.csv").is_file())


if __name__ == "__main__":
    unittest.main()
