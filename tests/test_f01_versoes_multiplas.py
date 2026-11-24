"""F-01: três ou mais versões do mesmo ato não podem duplicar uma decisão acrescentada em versão intermediária.

Cenário do contraditório independente: v1 com 3 decisões (revisada), v2 e v3 com as mesmas 4 decisões.
Esperado: 4 decisões vigentes (antes da correção: 5), estável em replay e reprocessamento.
"""
import unittest

from tests import test_leitura_banco_revisao as L
from tests import test_painel as TP
from tests import textos_doe as T


class TesteTresVersoes(L.Base):
    def versao(self, marca, texto, data="2026-10-09"):
        sha = TP.carregar(self.banco, marca, data, texto)
        self.classificar()
        return sha

    def vigentes(self):
        return self.banco.con.execute(
            "SELECT COUNT(*) FROM decisao d JOIN ato a ON a.id = d.ato_id "
            "WHERE a.natureza = 'ORIGINAL' AND d.vigente = 1").fetchone()[0]

    def test_v1_revisada_v2_e_v3_com_o_mesmo_acrescimo(self):
        self.versao("a", T.HORIZONTAL_GAJ)
        self.conferir_tudo()                                   # a v1 recebe revisão humana: vira a representação principal
        self.versao("b", L.HORIZONTAL_COM_EXTRA)
        self.versao("c", L.HORIZONTAL_COM_EXTRA)
        self.assertEqual(self.vigentes(), 4)                   # antes da correção: 5
        nova = self.decisoes(processo="SAD-PSE-2026/90010")
        self.assertEqual(sorted(d["vigente"] for d in nova), [0, 1])   # a cópia aponta para a representação vigente
        copia = [d for d in nova if d["vigente"] == 0][0]
        vigente = [d for d in nova if d["vigente"] == 1][0]
        self.assertEqual(copia["representada_por"], vigente["id"])
        self.conferir_tudo()
        self.assertEqual(self.indicador(), 4)

    def test_replay_e_reprocessamento_mantem_a_cardinalidade(self):
        self.versao("a", T.HORIZONTAL_GAJ)
        self.conferir_tudo()
        self.versao("b", L.HORIZONTAL_COM_EXTRA)
        self.versao("c", L.HORIZONTAL_COM_EXTRA)
        for _ in range(3):
            self.classificar(refazer=True)
            self.assertEqual(self.vigentes(), 4)
        self.versao("d", L.HORIZONTAL_COM_EXTRA)               # quarta versão idêntica
        self.assertEqual(self.vigentes(), 4)

    def test_acrescimo_revisado_na_v2_continua_vigente_apos_a_v3(self):
        self.versao("a", T.HORIZONTAL_GAJ)
        self.conferir_tudo()
        self.versao("b", L.HORIZONTAL_COM_EXTRA)
        self.conferir_tudo()                                   # a gerência confere o acréscimo na v2
        self.versao("c", L.HORIZONTAL_COM_EXTRA)
        self.assertEqual(self.vigentes(), 4)
        nova = self.decisoes(processo="SAD-PSE-2026/90010")
        vigentes = [d for d in nova if d["vigente"] == 1]
        self.assertEqual([d["validacao"] for d in vigentes], ["CONFERIDO"])   # a revisão humana não se perde
        self.assertEqual(self.indicador(), 4)

    def test_sem_revisao_a_versao_mais_nova_e_a_principal(self):
        self.versao("a", T.HORIZONTAL_GAJ)
        self.versao("b", L.HORIZONTAL_COM_EXTRA)
        self.versao("c", L.HORIZONTAL_COM_EXTRA)
        self.assertEqual(self.vigentes(), 4)


if __name__ == "__main__":
    unittest.main()
