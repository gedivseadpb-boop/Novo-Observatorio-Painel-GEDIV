"""F-04: candidato -> promoção auditada -> revogação imediata (503) e auditada. Dados SINTÉTICOS."""
import json
import threading
import unittest

from observatorio.operacao import __main__ as cli
from observatorio.operacao import snapshot
from observatorio.painel import indicadores
from observatorio.web import contas as K
from observatorio.web.servidor import criar_servidor
from tests import test_admin_contas as AC
from tests import test_painel as TP


class TesteCicloSnapshot(TP.Base):
    def setUp(self):
        super().setUp()
        self.base_padrao()
        K.Contas(self.pasta / "contas.sqlite3").criar("adm.snap", "Admin Snapshot", AC.SENHA, papel="admin")
        self.servidor = criar_servidor(self.pasta, None, porta=0)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.addCleanup(self.servidor.server_close)
        self.addCleanup(self.servidor.shutdown)
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"

    pedir = AC.TesteServidorAdmin.pedir

    def acoes(self):
        return [r[0] for r in self.banco.con.execute(
            "SELECT acao FROM auditoria WHERE alvo_tipo = 'snapshot_publico' ORDER BY id")]

    def test_sem_promocao_o_publico_recebe_503_e_nada_e_publicado_sozinho(self):
        self.assertEqual(self.pedir("/api/painel")[0], 503)
        self.assertEqual(self.pedir("/api/data")[0], 503)
        self.assertFalse((self.pasta / indicadores.ARQUIVO_SNAPSHOT_PUBLICO).exists())

    def test_candidato_nao_altera_o_publico(self):
        snapshot.gerar_candidato(self.pasta)
        self.assertEqual(self.pedir("/api/painel")[0], 503)

    def test_promocao_exige_ator_e_justificativa(self):
        snapshot.gerar_candidato(self.pasta)
        for resp, just in ((None, "x"), ("Fulano", ""), ("", "")):
            with self.subTest(resp=resp, just=just), self.assertRaises(ValueError):
                snapshot.promover(self.pasta, resp, just)
        self.assertEqual(self.pedir("/api/painel")[0], 503)

    def test_promover_servir_revogar_503_imediato_e_auditado(self):
        snapshot.gerar_candidato(self.pasta)
        r = snapshot.promover(self.pasta, "Gestora GEDIV", "aprovação da divulgação mensal")
        self.assertEqual(r["resultado"], "PROMOVIDO")
        status, _, corpo = self.pedir("/api/painel")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["linhas"], [])          # nenhum dado nominal no público
        self.assertNotIn("PESSOA FICTICIA", corpo.decode())
        self.assertEqual(self.pedir("/api/painel")[0], 200)        # cache aquecido
        r = snapshot.revogar(self.pasta, "Gestora GEDIV", "retirada para correção")
        self.assertEqual(r["resultado"], "REVOGADO")
        self.assertEqual(self.pedir("/api/painel")[0], 503)        # revogação imediata, mesmo com cache aquecido
        self.assertEqual(self.pedir("/api/data")[0], 503)
        self.assertEqual(self.acoes(), ["PROMOVER_SNAPSHOT_PUBLICO", "REVOGAR_SNAPSHOT_PUBLICO"])
        self.assertEqual(len(list(self.pasta.glob("snapshot_publico.revogado-*.json"))), 1)

    def test_arquivo_corrompido_responde_503_sem_reaproveitar_cache(self):
        snapshot.promover(self.pasta, "Gestora GEDIV", "divulgação", gerar_agora=True)
        self.assertEqual(self.pedir("/api/painel")[0], 200)
        (self.pasta / indicadores.ARQUIVO_SNAPSHOT_PUBLICO).write_text("{corrompido", encoding="utf-8")
        self.assertEqual(self.pedir("/api/painel")[0], 503)

    def test_revogacao_pela_api_so_admin_com_justificativa(self):
        snapshot.promover(self.pasta, "Gestora GEDIV", "divulgação", gerar_agora=True)
        self.assertEqual(self.pedir("/api/admin/snapshot-publico/revogar", corpo={"justificativa": "x"})[0], 401)
        _, _, corpo = self.pedir("/api/login", corpo={"usuario": "adm.snap", "senha": AC.SENHA, "modo_token": True})
        token = json.loads(corpo)["token"]
        self.assertEqual(self.pedir("/api/admin/snapshot-publico/revogar", token, {"justificativa": ""})[0], 422)
        self.assertEqual(self.pedir("/api/painel")[0], 200)
        status, _, corpo = self.pedir("/api/admin/snapshot-publico/revogar", token, {"justificativa": "erro detectado"})
        self.assertEqual((status, json.loads(corpo)["resultado"]), (200, "REVOGADO"))
        self.assertEqual(self.pedir("/api/painel")[0], 503)
        self.assertEqual(self.acoes()[-1], "REVOGAR_SNAPSHOT_PUBLICO")

    def test_cli_promove_e_revoga(self):
        self.assertEqual(cli.main(["promover-snapshot-publico", "--dados", str(self.pasta)]), 1)   # sem ator
        self.assertEqual(cli.main(["promover-snapshot-publico", "--dados", str(self.pasta), "--gerar",
                                   "--responsavel", "Gestora", "--justificativa", "divulgação"]), 0)
        self.assertEqual(self.pedir("/api/painel")[0], 200)
        self.assertEqual(cli.main(["revogar-snapshot-publico", "--dados", str(self.pasta),
                                   "--responsavel", "Gestora", "--justificativa", "retirada"]), 0)
        self.assertEqual(self.pedir("/api/painel")[0], 503)


if __name__ == "__main__":
    unittest.main()
