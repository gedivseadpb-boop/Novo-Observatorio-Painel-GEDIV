"""P0-1 em um comando (operacao prova-coleta), contra um servidor HTTP local com PDFs sintéticos (sem internet)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from observatorio.coleta import coletor
from observatorio.coleta.fontes import AUniao
from observatorio.nucleo import banco as B
from observatorio.nucleo.acervo import Acervo
from observatorio.operacao import aquisicao, prova
from tests.apoio import FonteLocal, Servidor, pdf_sintetico
from tests.test_aquisicao import FIXTURE, NOV, OUT, rota_pdf

HOJE = date(2026, 11, 14)


class TesteProvaColeta(unittest.TestCase):
    def setUp(self):
        self.s = Servidor()
        self.addCleanup(self.s.encerrar)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dados = Path(tmp.name) / "dados"
        self.fonte = FonteLocal(AUniao(), self.s)
        html = FIXTURE.read_text(encoding="utf-8").replace("https://auniao.pb.gov.br", "").encode()
        for rota in ("/doe/edicoes-recentes", NOV, OUT):
            self.s.rotas[rota] = (200, "text/html", html)
        for dia in (4, 5, 6, 7, 10, 11, 13, 14):
            self.s.rotas[rota_pdf(dia)] = (200, "application/pdf", pdf_sintetico(f"nov-{dia}", paginas=2))
        self.s.rotas[rota_pdf(12, sufixo="-1")] = (200, "application/pdf", pdf_sintetico("nov-12-1", paginas=2))
        for dia in (28, 29, 31):
            self.s.rotas[rota_pdf(dia, OUT)] = (200, "application/pdf", pdf_sintetico(f"out-{dia}", paginas=2))
        self.leituras = 0

    def _sonda(self, _sigla):
        return aquisicao.sonda(fonte=self.fonte, politica=self.s.politica())

    def _coletar(self, dados, _siglas, inicio, fim, *_resto):
        banco = B.Banco(Path(dados) / "observatorio.sqlite3")
        try:
            resumo = coletor.coletar_intervalo([self.fonte], banco, Acervo(Path(dados) / "acervo"), inicio, fim,
                                               politica=self.s.politica(), hoje=HOJE)
        finally:
            banco.fechar()
        resumo["pendencias"] = coletor.houve_pendencia(resumo)
        return resumo

    def _ler(self, pasta):
        self.leituras += 1
        from observatorio.operacao.rotina import _cli
        return _cli(["executar", "--dados", str(pasta)])

    def executar(self, **extra):
        return prova.executar(self.dados, sonda=self._sonda, coletar=self._coletar, ler=self._ler, **extra)

    def test_aprova_download_integridade_cobertura_e_reexecucao(self):
        rel = self.executar()
        self.assertEqual(rel["etapas"]["sonda"]["situacao"], "DOWNLOAD_INTEGRO")
        self.assertEqual(rel["dia"], "2026-11-14")
        c = rel["criterios"]
        self.assertTrue(c["download_integro"] and c["original_no_acervo"] and c["mesmo_sha_da_sonda"])
        self.assertTrue(c["cobertura_completa"], rel["etapas"]["cobertura"])
        self.assertTrue(c["reexecucao_sem_duplicidade"])
        self.assertEqual(rel["etapas"]["coleta"]["novos"], {"arquivos": 1, "publicacoes": rel["etapas"]["coleta"]["novos"]["publicacoes"]})
        self.assertEqual(rel["etapas"]["reexecucao"]["novos"], {"arquivos": 0, "publicacoes": 0})
        self.assertEqual(rel["etapas"]["cobertura"]["situacao"], "COMPLETO")
        self.assertIn(rel["resultado"], ("APROVADO", "APROVADO_COM_PENDENCIAS"))
        self.assertIn(rel["codigo_de_saida"], (0, 3))
        self.assertEqual(self.leituras, 1)

    def test_relatorio_sem_dados_pessoais(self):
        texto = json.dumps(self.executar(), ensure_ascii=False)
        for proibido in ('"servidor"', '"matricula"', '"processo"', '"nome"', '"trecho"', '"texto"'):
            self.assertNotIn(proibido, texto)

    def test_fonte_bloqueada_nao_coleta_e_devolve_4(self):
        self.s.rotas["/doe/edicoes-recentes"] = (403, "text/html", "Acesso permitido somente a partir do Brasil".encode())
        rel = self.executar()
        self.assertEqual((rel["resultado"], rel["codigo_de_saida"]), ("FONTE_INACESSIVEL", 4))
        self.assertEqual(rel["etapas"]["sonda"]["situacao"], "LISTAGEM_INACESSIVEL")
        self.assertNotIn("coleta", rel["etapas"])
        self.assertFalse((self.dados / "observatorio.sqlite3").exists())

    def test_dia_explicito_sem_comparacao_com_a_sonda(self):
        rel = self.executar(data=date(2026, 11, 7))
        self.assertEqual(rel["dia"], "2026-11-07")
        self.assertIsNone(rel["criterios"]["mesmo_sha_da_sonda"])
        self.assertTrue(rel["criterios"]["reexecucao_sem_duplicidade"])

    def test_comando_registrado_na_cli(self):
        from observatorio.operacao import __main__ as cli
        self.assertIn("prova-coleta", cli.__doc__)


if __name__ == "__main__":
    unittest.main()
