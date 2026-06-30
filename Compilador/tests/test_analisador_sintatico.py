import unittest
import sys
from pathlib import Path

# Configuração de path para rodar direto ou com pytest
_TESTS_DIR = Path(__file__).resolve().parent
_SRC = _TESTS_DIR.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lexer_mineires import LexerMineres
from analisador_sintatico import Parser, ErroSintatico, ErroSemantico

class TestAnalisadorSintaticoSemantico(unittest.TestCase):
    def setUp(self):
        self.lx = LexerMineres()

    def run_parser(self, source_code):
        tokens = self.lx.tokenize(source_code)
        parser = Parser(tokens)
        return parser.parse()

    def test_declaracao_valida(self):
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a, b uai
            a fica_assim_entao 10 uai
        cabo
        """
        # Não deve lançar exceção
        quads = self.run_parser(src)
        self.assertTrue(len(quads) > 0)

    def test_erro_sintatico_parenteses(self):
        src = """
        bora_cumpade main(
        simbora
        cabo
        """
        with self.assertRaises(ErroSintatico):
            self.run_parser(src)

    def test_erro_sintatico_uai_faltando(self):
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a
        cabo
        """
        with self.assertRaises(ErroSintatico):
            self.run_parser(src)

    def test_erro_semantico_variavel_nao_declarada(self):
        src = """
        bora_cumpade main()
        simbora
            b fica_assim_entao 20 uai
        cabo
        """
        with self.assertRaises(ErroSemantico):
            self.run_parser(src)

    def test_erro_semantico_tipos_incompativeis_atribuicao(self):
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a uai
            a fica_assim_entao "String aqui" uai
        cabo
        """
        with self.assertRaises(ErroSemantico):
            self.run_parser(src)

    def test_erro_semantico_tipos_incompativeis_soma(self):
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a uai
            trem_discolhe b uai
            a fica_assim_entao 1 uai
            b fica_assim_entao eh uai
            trem_di_numeru c uai
            c fica_assim_entao a + b uai
        cabo
        """
        with self.assertRaises(ErroSemantico):
            self.run_parser(src)

    def test_erro_semantico_condicao_if_nao_booleana(self):
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a uai
            a fica_assim_entao 1 uai
            uai_se (a)
                a fica_assim_entao 2 uai
        cabo
        """
        with self.assertRaises(ErroSemantico):
            self.run_parser(src)

if __name__ == "__main__":
    unittest.main()
