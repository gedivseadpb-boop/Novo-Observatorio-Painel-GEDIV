"""F-11: equivalências condicionais de grupo ('TEC. ADM' -> AST, 'STF' -> SFT) só valem com homologação formal.

Sem homologação, o ato fica sem grupo e com pendência para revisão humana, preservando a expressão publicada.
Com homologação, a equivalência ainda exige evidência POSITIVA de cargo compatível (cargos ausentes não bastam).
"""
import json
import tempfile
import unittest
from pathlib import Path

from observatorio.gerencias.gediv import catalogo as C
from observatorio.gerencias.gediv.classificador import classificar

CARGOS_AST = ["TECNICO ADMINISTRATIVO"]


class TesteSemHomologacao(unittest.TestCase):
    def test_registro_versionado_nao_homologa_nada(self):
        self.assertEqual(C._ler_homologacoes(), {})
        self.assertEqual(C.VERSAO_REGRAS, C.VERSAO_REGRAS_BASE)

    def test_tec_adm_com_cargo_compativel_fica_pendente(self):
        codigo, expressao, pendencia = C.avaliar_grupo(C.normalizar("DO GRUPO TEC. ADM."), cargos=CARGOS_AST)
        self.assertIsNone(codigo)
        self.assertEqual(expressao, "TEC. ADM")
        self.assertIn("homologação", pendencia)

    def test_sigla_ast_literal_continua_valendo(self):
        self.assertEqual(C.avaliar_grupo(C.normalizar("GRUPO TEC. ADM E AST"))[0], "AST")
        self.assertIsNone(C.avaliar_grupo(C.normalizar("GRUPO TEC. ADM E MAG"))[0])

    def test_citacao_da_lei_14386_ao_lado_de_tec_adm_nao_basta(self):
        # Preâmbulo das resenhas 524 e 527 de 03/10/2026 (conjunto-ouro): lei citada, grupo 'TEC. ADM.', sem sigla AST.
        preambulo = C.normalizar("COMBINADO COM A LEI Nº 14.386/2026 QUE DEFERIU OS PROCESSOS DE PROGRESSAO FUNCIONAL "
                                 "VERTICAL DO GRUPO TEC. ADM.")
        self.assertEqual(C.avaliar_grupo(preambulo, cargos=CARGOS_AST)[:2], (None, "TEC. ADM"))
        with C.homologacoes_temporarias("TEC. ADM"):
            self.assertEqual(C.avaliar_grupo(preambulo, cargos=CARGOS_AST)[:2], ("AST", "TEC. ADM"))

    def test_stf_com_enquadramento_fiscal_fica_pendente(self):
        codigo, expressao, pendencia = C.avaliar_grupo(
            C.normalizar("DO GRUPO STF AUDITOR FISCAL TRIBUTARIO ESTADUAL"), cargos=["AUDITOR FISCAL TRIBUTARIO"])
        self.assertEqual((codigo, expressao), (None, "STF"))
        self.assertIn("homologação", pendencia)

    def test_ato_real_fica_sem_grupo_e_com_pendencia(self):
        texto = ("RESENHA Nº 524/2026 - DEREH/GS/SEAD O SECRETARIO DE ESTADO DA ADMINISTRACAO DEFERIU os Processos de "
                 "PROGRESSAO FUNCIONAL VERTICAL do Grupo TEC. ADM. Processo Matricula Nome Cargo Classe\n"
                 "SAD-PSE-2026/90001 900001-1 PESSOA FICTICIA TECNICO ADMINISTRATIVO A B\nPUBLIQUE-SE")
        resultado = classificar([(1, texto)], "arquivo-de-teste")
        self.assertEqual(len(resultado.atos), 1)
        ato = resultado.atos[0]
        self.assertIsNone(ato.grupo)
        self.assertEqual(ato.grupo_expressao, "TEC. ADM")


class TesteComHomologacao(unittest.TestCase):
    @C.homologacoes_temporarias("TEC. ADM")
    def test_tec_adm_sem_cargos_nao_e_presumido_ast(self):
        codigo, _, pendencia = C.avaliar_grupo(C.normalizar("DO GRUPO TEC. ADM."))
        self.assertIsNone(codigo)
        self.assertIsNotNone(pendencia)

    @C.homologacoes_temporarias("TEC. ADM")
    def test_tec_adm_com_cargo_compativel_normaliza(self):
        self.assertEqual(C.avaliar_grupo(C.normalizar("DO GRUPO TEC. ADM."), cargos=CARGOS_AST)[:2], ("AST", "TEC. ADM"))

    @C.homologacoes_temporarias("TEC. ADM")
    def test_cargo_misto_ou_desconhecido_fica_pendente(self):
        for cargos in (["TECNICO ADMINISTRATIVO", "ENGENHEIRO CIVIL"], ["ASSISTENTE ADMINISTRATIVO"], ["PROFESSOR"]):
            with self.subTest(cargos=cargos):
                self.assertIsNone(C.avaliar_grupo(C.normalizar("DO GRUPO TEC. ADM."), cargos=cargos)[0])

    def test_homologacao_temporaria_e_restaurada(self):
        with C.homologacoes_temporarias("TEC. ADM", "STF"):
            self.assertTrue(C.equivalencia_homologada("STF"))
        self.assertFalse(C.equivalencia_homologada("STF"))


class TesteRegistroDeHomologacoes(unittest.TestCase):
    def ler(self, conteudo):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "homologacoes.json"
            caminho.write_text(conteudo if isinstance(conteudo, str) else json.dumps(conteudo), encoding="utf-8")
            return C._ler_homologacoes(caminho)

    def test_exige_ato_formal_e_grupo_previsto(self):
        registro = {"equivalencias_homologadas": [
            {"expressao": "TEC. ADM", "grupo": "AST", "ato_de_homologacao": ""},          # sem ato
            {"expressao": "STF", "grupo": "AST", "ato_de_homologacao": "Portaria 1/2027"},  # grupo errado
            {"expressao": "XYZ", "grupo": "AST", "ato_de_homologacao": "Portaria 1/2027"},  # expressão fora da lista
        ]}
        self.assertEqual(self.ler(registro), {})

    def test_homologacao_valida_entra_e_muda_a_versao(self):
        registro = {"equivalencias_homologadas": [
            {"expressao": "TEC. ADM", "grupo": "AST", "ato_de_homologacao": "Portaria GEDIV 1/2027"}]}
        lido = self.ler(registro)
        self.assertEqual(set(lido), {"TEC. ADM"})
        self.assertEqual(C._versao_regras(lido), C.VERSAO_REGRAS_BASE + "+AST")

    def test_arquivo_malformado_falha_fechado(self):
        self.assertEqual(self.ler("{nao e json"), {})
        self.assertEqual(self.ler([1, 2]), {})


if __name__ == "__main__":
    unittest.main()
