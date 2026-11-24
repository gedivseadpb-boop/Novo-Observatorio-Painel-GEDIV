"""F-03: reverificação delimitada de publicações já baixadas. Rede simulada localmente.

Aceite: novo item, mesma URL alterada (nova versão, original preservado), resposta inalterada (nada duplicado) e falha
na reverificação sem perda da versão anterior. A rotina diária executa a reverificação com janela e limite."""
import unittest
from pathlib import Path

from tests import test_coleta as TC
from tests.apoio import pdf_sintetico

RAIZ = Path(__file__).resolve().parents[1]


class TesteReverificacao(unittest.TestCase):
    INICIO, FIM = TC.TesteColeta.INICIO, TC.TesteColeta.FIM
    setUp, coletar = TC.TesteColeta.setUp, TC.TesteColeta.coletar

    def test_sem_mudanca_nada_e_duplicado(self):
        self.coletar()
        resumo = self.coletar(reverificar=True)
        self.assertEqual(resumo["fontes"]["auniao"]["downloads"], {"IGUAL": 5})
        self.assertEqual(len(self.banco.arquivos()), 5)

    def test_novo_item_e_url_estavel_alterada(self):
        self.coletar()
        rota = self.j + "/diario-oficial-07-01-2026-portal.pdf"
        self.s.rotas[rota] = (200, "application/pdf", pdf_sintetico("07-retificado"))
        resumo = self.coletar(reverificar=True)
        self.assertEqual(resumo["fontes"]["auniao"]["downloads"].get("ALTERADO"), 1)
        versoes = self.banco.versoes(self.banco.publicacao("auniao", self.s.base + rota)["id"])
        self.assertEqual(len(versoes), 2)
        self.assertTrue(all(self.acervo.conferir(v["sha256"]) for v in versoes))   # o original continua no acervo

    def test_falha_na_reverificacao_preserva_a_versao_anterior(self):
        self.coletar()
        rota = self.j + "/diario-oficial-07-01-2026-portal.pdf"
        publicacao = self.banco.publicacao("auniao", self.s.base + rota)
        antes = [v["sha256"] for v in self.banco.versoes(publicacao["id"])]
        self.s.rotas[rota] = (500, "text/plain", b"erro temporario")
        self.coletar(reverificar=True)
        depois = [v["sha256"] for v in self.banco.versoes(publicacao["id"])]
        self.assertEqual(depois, antes)
        self.assertTrue(all(self.acervo.conferir(s) for s in depois))
        self.assertEqual(len(self.banco.arquivos()), 5)
        self.assertEqual(self.banco.publicacao("auniao", self.s.base + rota)["estado"], "BAIXADA")   # não vira lacuna

    def test_rotina_diaria_reverifica_com_janela_e_limite(self):
        rotina = (RAIZ / "deploy_autonomo" / "rodar_diario.sh").read_text(encoding="utf-8")
        self.assertIn("coletar-intervalo --reverificar", rotina)
        self.assertIn('--limite "$REVERIFICAR_LIMITE"', rotina)
        self.assertIn('REVERIFICAR_DIAS="${REVERIFICAR_DIAS:-1}"', rotina)


if __name__ == "__main__":
    unittest.main()
