"""Backup cifrado (AES-256-GCM) e restauração verificada em pasta nova. Base de DEMONSTRAÇÃO com PDFs sintéticos."""
import hashlib
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from observatorio.operacao import backup, demonstracao
from observatorio.web.contas import Contas

FRASE = "frase-senha-de-teste-bem-longa-2026"


def contar(caminho, tabela):
    with sqlite3.connect(caminho) as con:
        return con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


class TesteBackupCifrado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.raiz = Path(cls._tmp.name)
        cls.dados = cls.raiz / "dados"
        demonstracao.criar(cls.dados)
        contas = Contas(cls.dados / "contas.sqlite3")
        contas.criar("ger.backup", "Gerente Backup", "SenhaForte#Backup2026", papel="gerencia")
        cls.sessao = contas.entrar("ger.backup", "SenhaForte#Backup2026")
        cls.r = backup.gerar(cls.dados, cls.raiz / "backups", FRASE)
        cls.arquivo = Path(cls.r["arquivo"])

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def destino(self):
        d = Path(tempfile.mkdtemp(dir=self.raiz)) / "restaurado"
        return d

    def test_backup_nao_contem_texto_em_claro(self):
        bruto = self.arquivo.read_bytes()
        self.assertNotIn(b"SQLite format 3", bruto)
        self.assertNotIn(b"%PDF", bruto)
        self.assertNotIn(b"PESSOA", bruto)
        self.assertEqual(hashlib.sha256(bruto).hexdigest(), self.r["sha256"])
        self.assertGreater(self.r["pdfs_registrados"], 0)
        self.assertEqual(self.r["pdfs_ausentes_no_acervo"], 0)

    def test_ida_e_volta_preserva_tudo_e_exige_novo_login(self):
        destino = self.destino()
        r = backup.restaurar(self.arquivo, destino, FRASE)
        self.assertEqual(r["resultado"], "RESTAURADO")
        for tabela in ("arquivo", "publicacao", "ato", "decisao", "auditoria"):
            self.assertEqual(contar(destino / "observatorio.sqlite3", tabela),
                             contar(self.dados / "observatorio.sqlite3", tabela), tabela)
        with sqlite3.connect(destino / "observatorio.sqlite3") as con:
            hashes = [h for (h,) in con.execute("SELECT sha256 FROM arquivo")]
        for sha in hashes:
            pdf = destino / "acervo" / sha[:2] / f"{sha}.pdf"
            self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), sha)
        contas = Contas(destino / "contas.sqlite3")
        self.assertIsNone(contas.sessao(self.sessao["token"]))           # sessão antiga não vale na cópia
        self.assertTrue(contas.entrar("ger.backup", "SenhaForte#Backup2026")["token"])
        self.assertGreaterEqual(r["sessoes_encerradas"], 1)

    def test_frase_senha_errada_falha_sem_gravar(self):
        destino = self.destino()
        with self.assertRaises(backup.ErroBackup):
            backup.restaurar(self.arquivo, destino, "outra-frase-senha-qualquer-2026")
        self.assertFalse(destino.exists())

    def test_adulteracao_e_truncamento_sao_detectados(self):
        bruto = bytearray(self.arquivo.read_bytes())
        adulterado = self.raiz / "adulterado.gedivbak"
        bruto[len(bruto) // 2] ^= 0x01
        adulterado.write_bytes(bytes(bruto))
        truncado = self.raiz / "truncado.gedivbak"
        truncado.write_bytes(self.arquivo.read_bytes()[:-100])
        for caso in (adulterado, truncado):
            with self.subTest(caso=caso.name), self.assertRaises(backup.ErroBackup):
                backup.restaurar(caso, self.destino(), FRASE)

    def test_destino_existente_nunca_e_sobrescrito(self):
        destino = self.destino()
        destino.mkdir(parents=True)
        (destino / "algo.txt").write_text("existente", encoding="utf-8")
        with self.assertRaises(backup.ErroBackup):
            backup.restaurar(self.arquivo, destino, FRASE)
        self.assertEqual((destino / "algo.txt").read_text(encoding="utf-8"), "existente")

    def test_frase_curta_ou_ausente_e_recusada(self):
        with self.assertRaises(backup.ErroBackup):
            backup.gerar(self.dados, self.raiz / "x", "curta")


if __name__ == "__main__":
    unittest.main()
