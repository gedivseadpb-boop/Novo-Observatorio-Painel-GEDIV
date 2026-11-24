"""PDF que exige senha de usuário (caso real das cópias da CGE-PB, 24/11/2026) é retido com motivo explícito, sem
nenhuma tentativa de contornar a proteção. PDF com restrição de permissões mas senha de usuário vazia continua legível."""
import io
import unittest

from pypdf import PdfWriter

from observatorio.nucleo import pdf


def gerar(senha_usuario: str) -> bytes:
    w = PdfWriter()
    for _ in range(30):                     # acima do tamanho mínimo aceito pelo verificador
        w.add_blank_page(width=200, height=200)
    w.add_metadata({"/Title": "Documento de teste " + "x" * 600})
    w.encrypt(user_password=senha_usuario, owner_password="dono-qualquer", algorithm="AES-128")
    saida = io.BytesIO()
    w.write(saida)
    return saida.getvalue()


class TestePdfProtegido(unittest.TestCase):
    def test_senha_de_usuario_exigida_fica_retido_com_motivo_explicito(self):
        dados = gerar("senha-desconhecida")
        laudo = pdf.verificar(dados, len(dados))
        self.assertFalse(laudo.valido)
        self.assertIn("PDF_PROTEGIDO_POR_SENHA", laudo.motivo or "")

    def test_senha_de_usuario_vazia_continua_legivel(self):
        dados = gerar("")
        laudo = pdf.verificar(dados, len(dados))
        self.assertTrue(laudo.valido, laudo.motivo)
        self.assertEqual(laudo.paginas, 30)


if __name__ == "__main__":
    unittest.main()
