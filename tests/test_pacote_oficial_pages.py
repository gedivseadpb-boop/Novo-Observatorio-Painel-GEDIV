"""Pacote oficial do GitHub Pages: estado 'Dados oficiais em validação', sem dados fictícios nem privados.

Executar: python -m unittest tests.test_pacote_oficial_pages -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import preparar_pacote_oficial_pages as P  # noqa: E402


class TestePacoteOficialVazio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="gediv-oficial-"))
        cls.pacote = P.construir_pacote_oficial(cls.tmp / "site", gerado_em="2026-11-25T00:00:00+00:00")
        cls.html = (cls.pacote / "index.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _copia(self) -> Path:
        destino = Path(tempfile.mkdtemp(prefix="gediv-oficial-copia-")) / "site"
        shutil.copytree(self.pacote, destino)
        self.addCleanup(shutil.rmtree, destino.parent, True)
        return destino

    def _recusa(self, pasta: Path, trecho: str):
        with self.assertRaises(AssertionError) as ctx:
            P.validar_pacote_oficial(pasta, permitir_cname=True)
        self.assertIn(trecho, str(ctx.exception))

    # --- o que o pacote contém -------------------------------------------------------------------
    def test_arquivos_exatos_e_estado_vazio(self):
        arquivos = sorted(p.name for p in self.pacote.iterdir())
        self.assertEqual(arquivos, sorted(P.PERMITIDOS))
        estado = json.loads((self.pacote / P.ESTADO_ARQUIVO).read_text(encoding="utf-8"))
        self.assertEqual(estado["estado"], "EM_VALIDACAO")
        self.assertIs(estado["dados_publicados"], False)
        self.assertIs(estado["cobertura_validada"], False)
        self.assertEqual(estado["registros"], 0)

    def test_aviso_navegacao_e_sem_registros(self):
        self.assertNotIn('id="avisoValidacao"', self.html)          # faixa azul removida (28/11/2026)
        self.assertIn('<body class="estado-validacao">', self.html)
        for vista in ("geral", "vertical", "horizontal", "tempo", "outras", "hoje", "historico"):
            self.assertIn(f'data-view="{vista}"', self.html)
        boot = P._bootstrap(self.html)
        self.assertEqual((boot["rows"], boot["events"], boot["otherPublications"]), ([], [], []))
        self.assertNotIn("dados-sinteticos-publicos.json", self.html)

    def test_indicadores_graficos_e_tabelas_indisponiveis_nunca_zero(self):
        # Os valores ficam ocultos e substituídos por "Indisponível" (zero só com cobertura validada).
        for regra in ("#kpis .kpi .val", "#reportRoot .card>:not(.card-heading)", ".svc-count", "#receivedSummaryBar",
                      "content:\"Indisponível\"", "content:\"Indisponível · dados oficiais em validação\""):
            self.assertIn(regra, self.html)

    def test_interface_aprovada_intacta_e_paleta(self):
        origem = P.HTML_ORIGEM.read_text(encoding="utf-8")
        self.assertNotIn("estado-validacao", origem, "o arquivo aprovado não pode ser alterado; a adaptação é só no pacote")
        cores = {c.lower() for c in json.loads(P.PALETA_JSON.read_text(encoding="utf-8"))["cores_hex"]}
        import re
        self.assertFalse({c.lower() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", self.html)} - cores)

    def test_previa_sintetica_c05_continua_identica(self):
        # A prévia sintética (C-05) não muda: a faixa de demonstração e a interface aprovada seguem as mesmas.
        import preparar_previa_github_pages as previa
        html_previa = previa.adaptar_html_estatico(P.HTML_ORIGEM.read_text(encoding="utf-8"))
        self.assertIn('id="avisoDemonstracao"', html_previa)
        self.assertNotIn("estado-validacao", html_previa)

    # --- o que a validação recusa ----------------------------------------------------------------
    def test_recusa_carga_ficticia(self):
        for injecao, motivo in (("SERVIDOR FICTICIO ALFA", "fictício"), ("SAD-PSE-2099/00001", "2099"),
                                ("950.123-4", "950."), ("./dados-sinteticos-publicos.json", "sintéticos"),
                                ('id="avisoDemonstracao"', "demonstração")):
            with self.subTest(injecao=injecao):
                pasta = self._copia()
                alvo = pasta / "index.html"
                alvo.write_text(alvo.read_text(encoding="utf-8").replace("</body>", f"<p>{injecao}</p></body>", 1),
                                encoding="utf-8", newline="\n")
                self._recusa(pasta, motivo)

    def test_recusa_registros_no_bootstrap_e_no_estado(self):
        pasta = self._copia()
        alvo = pasta / "index.html"
        alvo.write_text(alvo.read_text(encoding="utf-8").replace('window.GEDIV_BOOTSTRAP={"rows":[]',
                                                                  'window.GEDIV_BOOTSTRAP={"rows":[{"id":"x"}]', 1),
                        encoding="utf-8", newline="\n")
        self._recusa(pasta, "registros em rows")

        pasta = self._copia()
        estado = json.loads((pasta / P.ESTADO_ARQUIVO).read_text(encoding="utf-8"))
        estado["registros"] = 3
        (pasta / P.ESTADO_ARQUIVO).write_text(json.dumps(estado), encoding="utf-8")
        self._recusa(pasta, "0 registros")

    def test_recusa_dados_pessoais_e_credenciais(self):
        for injecao, motivo in (("123.456.789-09", "CPF"), ("SAD-PSE-2026/02811", "processo"), ("174571-9", "matrícula"),
                                ("ghp_" + "a" * 36, "token"), ("C:\\Users\\ylena\\dados", "Windows"),
                                ("observatorio.sqlite3", "banco")):
            with self.subTest(injecao=injecao):
                pasta = self._copia()
                alvo = pasta / P.ESTADO_ARQUIVO
                estado = json.loads(alvo.read_text(encoding="utf-8"))
                estado["mensagem"] += " " + injecao
                alvo.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
                self._recusa(pasta, motivo)

    def test_recusa_arquivos_privados_ou_extras(self):
        for nome in ("diario-oficial-24-11-2026.pdf", "observatorio.sqlite3", "backup.gedivbak", ".env",
                     "decisoes.csv", "dados-sinteticos-publicos.json"):
            with self.subTest(nome=nome):
                pasta = self._copia()
                (pasta / nome).write_bytes(b"x")
                self._recusa(pasta, "Arquivos fora da lista")

    def test_cname_aceito_so_quando_valido(self):
        pasta = self._copia()
        (pasta / "CNAME").write_text("paineldoepb.centralgestaopublica.com.br\n", encoding="utf-8")
        P.validar_pacote_oficial(pasta, permitir_cname=True)
        with self.assertRaises(AssertionError):
            P.validar_pacote_oficial(pasta, permitir_cname=False)
        (pasta / "CNAME").write_text("https://exemplo.com/caminho\n", encoding="utf-8")
        self._recusa(pasta, "CNAME inválido")


class TesteWorkflowPages(unittest.TestCase):
    """O workflow do Pages publica só o pacote oficial, e só com disparo manual explícito."""

    def setUp(self):
        self.yml = (RAIZ / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

    def test_usa_pacote_oficial_e_nao_a_previa_sintetica(self):
        self.assertIn("scripts/preparar_pacote_oficial_pages.py", self.yml)
        self.assertNotIn("preparar_previa_github_pages.py --saida", self.yml)

    def test_sem_publicacao_automatica(self):
        import re
        self.assertNotRegex(self.yml, r"(?m)^\s*schedule:", "agendamento publicaria sem autorização")
        self.assertIn("workflow_dispatch:", self.yml)
        for passo in ("Publicar o pacote validado", "Solicitar o build do Pages"):
            bloco = self.yml[self.yml.index(passo):]
            self.assertRegex(bloco[:400], r"if: .*github\.event_name == 'workflow_dispatch'.*inputs\.publicar",
                             f"o passo '{passo}' precisa exigir disparo manual com publicar=true")
        self.assertTrue(re.search(r"publicar:\s*\n\s*description:", self.yml))


if __name__ == "__main__":
    unittest.main()
