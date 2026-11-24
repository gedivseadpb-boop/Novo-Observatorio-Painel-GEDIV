"""F-02: o robots.txt vale para TODA URL requisitada (listagem, PDF, redirecionamento e sonda), não só para a primeira
listagem mensal. Rede simulada localmente; nenhuma requisição externa."""
import unittest

from observatorio.nucleo import rede
from tests import test_coleta as TC


class TesteRobotsPorUrl(unittest.TestCase):
    """Mesmo cenário de rede local de tests/test_coleta.py, sem herdar (e repetir) os testes daquela classe."""
    INICIO, FIM = TC.TesteColeta.INICIO, TC.TesteColeta.FIM
    setUp, coletar = TC.TesteColeta.setUp, TC.TesteColeta.coletar

    def test_listagem_permitida_mas_pdf_proibido_nao_e_baixado(self):
        # Regra específica contrária ao PDF, com a listagem mensal permitida (o caso do contraditório independente).
        self.s.rotas["/robots.txt"] = (200, "text/plain",
                                      b"User-agent: *\nDisallow: /servicos/doe/2026/janeiro/diario-oficial-08-01-2026-portal.pdf\n")
        resumo = self.coletar()
        parte = resumo["fontes"]["auniao"]
        self.assertEqual(parte["robots"], "LIDO")
        self.assertEqual(self.s.acessos.get(self.j + "/diario-oficial-08-01-2026-portal.pdf", 0), 0)   # nunca requisitado
        self.assertEqual(parte["downloads"].get("NOVO"), 4)
        self.assertGreaterEqual(parte["urls_negadas_por_robots"], 1)
        self.assertTrue(rede.ErroRede("ROBOTS_RESTRINGE").categoria.startswith("ROBOTS"))

    def test_redirecionamento_para_caminho_proibido_e_barrado_antes_do_salto(self):
        pdf = self.j + "/diario-oficial-07-01-2026-portal.pdf"
        destino = "/proibido/diario.pdf"
        self.s.rotas[pdf] = (302, "text/html", destino.encode())        # o servidor de teste envia o corpo como Location
        self.s.rotas[destino] = (200, "application/pdf", b"%PDF-1.4 nao deveria ser lido")
        self.s.rotas["/robots.txt"] = (200, "text/plain", b"User-agent: *\nDisallow: /proibido/\n")
        self.coletar()
        self.assertEqual(self.s.acessos.get(pdf), 1)                   # o primeiro salto (permitido) aconteceu
        self.assertEqual(self.s.acessos.get(destino, 0), 0)            # o destino proibido nunca foi requisitado

    def test_robots_inacessivel_5xx_nao_permite_acesso(self):
        self.s.rotas["/robots.txt"] = (503, "text/plain", b"indisponivel")
        resumo = self.coletar()
        pdfs = [k for k in self.s.acessos if k.endswith(".pdf")]
        self.assertEqual(pdfs, [])                                   # RFC 9309: inacessível = proibido
        self.assertTrue(resumo["fontes"]["auniao"]["robots"] in ("INACESSIVEL",))


class TesteAutorizadorIsolado(unittest.TestCase):
    def test_situacoes(self):
        politica = rede.Politica(servidores=frozenset({"x.gov.br"}))
        a = rede.AutorizadorRobots(politica)
        regras = __import__("urllib.robotparser").robotparser.RobotFileParser()
        regras.parse(["User-agent: *", "Disallow: /privado/"])
        a.situacoes["https://x.gov.br"] = ("LIDO", regras)
        a("https://x.gov.br/publico/a.pdf")
        with self.assertRaises(rede.ErroRede) as e:
            a("https://x.gov.br/privado/a.pdf")
        self.assertEqual(e.exception.categoria, "ROBOTS_RESTRINGE")
        a.situacoes["https://y.gov.br"] = ("RECUSADO", None)
        with self.assertRaises(rede.ErroRede) as e:
            a("https://y.gov.br/qualquer")
        self.assertEqual(e.exception.categoria, "ROBOTS_RECUSADO")
        a.situacoes["https://z.gov.br"] = ("AUSENTE", None)
        a("https://z.gov.br/qualquer")                               # 404: sem restrições declaradas
        self.assertFalse(rede.ErroRede("ROBOTS_INACESSIVEL").recusa)  # não suspende a fonte (transitório)



if __name__ == "__main__":
    unittest.main()
