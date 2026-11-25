"""Página 403 de bloqueio geográfico da fonte (texto real da A União em 25/11/2026) vira recusa com motivo explícito,
sem nova tentativa e sem qualquer contorno. Servidor local; nenhuma requisição externa."""
import unittest

from observatorio.nucleo import rede
from tests.apoio import Servidor

PAGINA = ("<!doctype html><html lang='pt-BR'><head><title>403 · Acesso Negado</title></head><body><main>"
          "<div class='code'>403</div><h1>Acesso Negado</h1><p class='msg'>Acesso permitido somente a partir do "
          "Brasil ou da rede interna</p></main></body></html>").encode("utf-8")


class TesteGeobloqueio(unittest.TestCase):
    def setUp(self):
        self.s = Servidor()
        self.addCleanup(self.s.encerrar)

    def test_403_geografico_e_recusa_com_motivo_e_sem_repeticao(self):
        self.s.rotas["/doe"] = (403, "text/html; charset=utf-8", PAGINA)
        with self.assertRaises(rede.ErroRede) as erro:
            rede.obter(self.s.base + "/doe", self.s.politica())
        self.assertEqual(erro.exception.categoria, "HTTP_403")
        self.assertTrue(erro.exception.recusa)                      # a guarda suspende a fonte, sem insistir
        self.assertIn("GEOBLOQUEIO", str(erro.exception))
        self.assertEqual(self.s.acessos["/doe"], 1)                  # uma única requisição

    def test_403_comum_nao_e_rotulado_como_geobloqueio(self):
        self.s.rotas["/x"] = (403, "text/html", b"<h1>Forbidden</h1>")
        with self.assertRaises(rede.ErroRede) as erro:
            rede.obter(self.s.base + "/x", self.s.politica())
        self.assertNotIn("GEOBLOQUEIO", str(erro.exception))


if __name__ == "__main__":
    unittest.main()
