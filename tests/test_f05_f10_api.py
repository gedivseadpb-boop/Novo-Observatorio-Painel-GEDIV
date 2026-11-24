"""F-05 (confirmações tipadas em POST /api/revisao) e F-10 (token fora do JSON de login). Dados SINTÉTICOS."""
import json
import unittest

import threading

from observatorio.web import contas as K
from observatorio.web.servidor import criar_servidor
from tests import test_painel as TP
from tests import test_admin_contas as AC

SENHA = AC.SENHA


class Base(TP.Base):
    """Mesmo servidor sintético de test_admin_contas, sem herdar (e repetir) os testes daquela classe."""
    def setUp(self):
        super().setUp()
        self.base_padrao()
        K.Contas(self.pasta / "contas.sqlite3").criar("maria.silva", "Maria da Silva", SENHA)
        self.servidor = criar_servidor(self.pasta, None, porta=0, origens_admin=[AC.ORIGEM])
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.addCleanup(self.servidor.server_close)
        self.addCleanup(self.servidor.shutdown)
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"

    pedir = AC.TesteServidorAdmin.pedir
    entrar = AC.TesteServidorAdmin.entrar


class TesteF05ConfirmacaoBooleanaLiteral(Base):
    def _estado(self, ato_id):
        return sorted(tuple(r) for r in self.banco.con.execute(
            "SELECT * FROM decisao WHERE ato_id = ? ORDER BY id", (ato_id,)))

    def _auditorias(self):
        return self.banco.con.execute("SELECT COUNT(*) FROM auditoria WHERE acao = 'CONFERIR'").fetchone()[0]

    def test_valores_nao_booleanos_sao_recusados_sem_alterar_nada(self):
        token = json.loads(self.entrar()[2])["token"]
        ato = self.ato("901/2026")["id"]
        antes, auditorias = self._estado(ato), self._auditorias()
        for invalido in ("false", "true", 1, 0, "sim", [], {}, None):
            with self.subTest(valor=invalido):
                status, _, corpo = self.pedir("/api/revisao", token, {
                    "alvo": "ato", "id": ato, "decisao": "CONFERIR", "justificativa": "conferido no PDF",
                    "confirma_fonte": invalido, "confirma_vinculo": True})
                self.assertEqual(status, 400, corpo)
                self.assertIn(b"booleano", corpo)
        self.assertEqual(self._estado(ato), antes)
        self.assertEqual(self._auditorias(), auditorias)

    def test_booleano_literal_continua_funcionando(self):
        token = json.loads(self.entrar()[2])["token"]
        ato = self.ato("901/2026")["id"]
        status, _, corpo = self.pedir("/api/revisao", token, {
            "alvo": "ato", "id": ato, "decisao": "CONFERIR", "justificativa": "conferido no PDF",
            "confirma_fonte": True, "confirma_vinculo": True})
        self.assertEqual(status, 200, corpo)


class TesteF10TokenForaDoJson(Base):
    def test_login_padrao_devolve_somente_cookie_httponly(self):
        status, cab, corpo = self.pedir("/api/login", corpo={"usuario": "maria.silva", "senha": SENHA})
        self.assertEqual(status, 200)
        self.assertNotIn("token", json.loads(corpo))
        self.assertIn("HttpOnly", cab.get("Set-Cookie", ""))

    def test_modo_cookie_prevalece_sobre_modo_token(self):
        status, _, corpo = self.pedir("/api/login", corpo={"usuario": "maria.silva", "senha": SENHA,
                                                           "modo_cookie": True, "modo_token": True})
        self.assertEqual(status, 200)
        self.assertNotIn("token", json.loads(corpo))

    def test_modo_token_so_com_booleano_literal(self):
        status, _, corpo = self.pedir("/api/login", corpo={"usuario": "maria.silva", "senha": SENHA, "modo_token": "true"})
        self.assertEqual(status, 200)
        self.assertNotIn("token", json.loads(corpo))



if __name__ == "__main__":
    unittest.main()
