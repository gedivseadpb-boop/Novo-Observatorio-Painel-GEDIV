"""A-10: em modo produção a interface legada /estatico/ responde 404; o painel oficial /painel/ continua servido."""
import os
import threading
import unittest
import urllib.error
import urllib.request

from observatorio.web.servidor import POLITICA_PRODUCAO, criar_servidor
from tests import test_painel as TP


class TesteEstaticoEmProducao(TP.Base):
    def setUp(self):
        super().setUp()
        self.base_padrao()
        anteriores = {k: os.environ.get(k) for k in POLITICA_PRODUCAO}
        os.environ.update(POLITICA_PRODUCAO)

        def restaurar():
            for k, v in anteriores.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.addCleanup(restaurar)
        self.servidor = criar_servidor(self.pasta, None, porta=0, modo_producao=True)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.addCleanup(self.servidor.server_close)
        self.addCleanup(self.servidor.shutdown)
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"

    def status(self, caminho):
        try:
            with urllib.request.urlopen(self.url + caminho, timeout=10) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def test_legado_404_e_painel_oficial_200(self):
        for rota in ("/estatico", "/estatico/", "/estatico/index.html", "/estatico/app.js", "/estatico/estilo.css"):
            with self.subTest(rota=rota):
                self.assertEqual(self.status(rota), 404)
        self.assertEqual(self.status("/painel/"), 200)


if __name__ == "__main__":
    unittest.main()
