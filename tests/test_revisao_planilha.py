"""Revisão pela planilha (D-13, etapa B). Dados FICTÍCIOS."""
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from observatorio.gerencias.gediv import processo as PROC
from observatorio.nucleo.banco import Banco
from observatorio.operacao import revisao_planilha as RP
from tests.test_csv_diario import BLOCO

try:
    import openpyxl
except ImportError:                                  # pragma: no cover
    openpyxl = None


@unittest.skipIf(openpyxl is None, "openpyxl simula a edição feita no Excel/Drive")
class TesteRevisaoPlanilha(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dados = Path(tmp.name)
        banco = Banco(self.dados / "observatorio.sqlite3")
        try:
            sha = "f" * 64
            banco.con.execute("INSERT INTO arquivo VALUES (?, 10, 'x', 'agora')", (sha,))
            banco.registrar_leitura(sha, "LIDA", "t", [{"numero": 3, "metodo": "TEXTO", "colunas": 2, "texto": BLOCO,
                                                        "palavras": 60, "qualidade": "OK"}], "18900", "2026-10-09", None)
            PROC.classificar_pendentes(banco)
        finally:
            banco.fechar()
        RP.configurar(self.dados, "revisora.teste")

    def preencher(self, por_linha: dict[int, dict]):
        """Edita como o Excel faria (openpyxl grava textos compartilhados)."""
        arq = self.dados / "revisao" / RP.ARQUIVO
        wb = openpyxl.load_workbook(arq)
        ws = wb["Revisao"]
        cab = [c.value for c in ws[1]]
        for linha, valores in por_linha.items():
            for campo, valor in valores.items():
                ws.cell(row=linha + 1, column=cab.index(campo) + 1, value=valor)
        wb.save(arq)

    def validacoes(self):
        banco = Banco(self.dados / "observatorio.sqlite3")
        try:
            return {r[0]: (r[1], r[2], r[3]) for r in banco.con.execute("SELECT id, validacao, revisor, processo FROM decisao")}
        finally:
            banco.fechar()

    def relatorio(self, caminho):
        return list(csv.DictReader(io.StringIO(Path(caminho).read_text(encoding="utf-8-sig")), delimiter=";"))

    def test_gera_so_pendentes_com_cabecalho(self):
        r = RP.gerar(self.dados)
        self.assertEqual((r["situacao"], r["linhas"]), ("GERADO", 2))
        linhas = RP.ler_xlsx(self.dados / "revisao" / RP.ARQUIVO)
        self.assertEqual(linhas[0], RP.CABECALHO)

    def test_confirmar_corrigir_e_recusas(self):
        RP.gerar(self.dados)
        ids = [l[0] for l in RP.ler_xlsx(self.dados / "revisao" / RP.ARQUIVO)[1:]]
        self.preencher({1: {"Acao": "Confirmar", "Consultei_PDF": "sim", "Justificativa": "ok no PDF"},
                        2: {"Acao": "Corrigir", "Consultei_PDF": "SIM", "Campo_Corrigido": "Processo",
                            "Valor_Corrigido": "SAD-PSE-2026/90399", "Justificativa": "OCR trocou digito"}})
        r = RP.aplicar(self.dados)
        self.assertEqual((r["situacao"], r["aplicadas"], r["recusadas"]), ("APLICADO", 2, 0))
        v = self.validacoes()
        self.assertEqual(v[ids[0]][:2], ("CONFERIDO", "revisora.teste"))
        self.assertEqual(v[ids[1]][2], "SAD-PSE-2026/90399")
        self.assertFalse((self.dados / "revisao" / RP.ARQUIVO).exists())          # não é aplicada duas vezes
        self.assertEqual(len(list((self.dados / "revisao" / "processados").iterdir())), 1)

    def test_sem_consultei_pdf_e_acao_invalida_sao_recusadas(self):
        RP.gerar(self.dados)
        self.preencher({1: {"Acao": "Confirmar"}, 2: {"Acao": "Talvez", "Consultei_PDF": "SIM"}})
        r = RP.aplicar(self.dados)
        self.assertEqual((r["aplicadas"], r["recusadas"]), (0, 2))
        motivos = {l["Motivo"] for l in self.relatorio(r["relatorio"])}
        self.assertIn("escreva SIM em Consultei_PDF", motivos)
        self.assertTrue(all(v[0] == "PENDENTE" for v in self.validacoes().values()))

    def test_trava_de_versao_recusa_linha_alterada_depois(self):
        RP.gerar(self.dados)
        self.preencher({1: {"Acao": "Rejeitar", "Justificativa": "não é GEDIV"}})
        did = RP.ler_xlsx(self.dados / "revisao" / RP.ARQUIVO)[1][0]
        banco = Banco(self.dados / "observatorio.sqlite3")
        banco.con.execute("UPDATE decisao SET processo = 'MUDOU' WHERE id = ?", (did,))
        banco.con.commit()
        banco.fechar()
        r = RP.aplicar(self.dados)
        self.assertEqual(r["recusadas"], 1)
        self.assertIn("mudou", self.relatorio(r["relatorio"])[0]["Motivo"])

    def test_nao_sobrescreve_planilha_preenchida_e_nao_aplicada(self):
        RP.gerar(self.dados)
        self.preencher({1: {"Acao": "Confirmar"}})
        self.assertEqual(RP.gerar(self.dados)["situacao"], "MANTIDO_COM_PREENCHIMENTO_NAO_APLICADO")

    def test_sem_revisora_configurada_nao_aplica(self):
        (self.dados / "revisao" / "config.json").unlink()
        RP.gerar(self.dados)
        self.preencher({1: {"Acao": "Confirmar", "Consultei_PDF": "SIM"}})
        self.assertEqual(RP.aplicar(self.dados)["situacao"], "REVISORA_NAO_CONFIGURADA")


if __name__ == "__main__":
    unittest.main()
