from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Garante import de interpretador ao rodar `python -m unittest` de qualquer cwd
_TESTS_DIR = Path(__file__).resolve().parent
_ANALISADOR_LEXICO = _TESTS_DIR.parent
_SRC = _ANALISADOR_LEXICO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lexer_mineires import LexerMineres
from analisador_sintatico import Parser
from interpretador import Interpretador, ErroExecucao


class TestInterpretador(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def run_source(self, src: str) -> Interpretador:
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        interp = Interpretador(quads, p.tabela_simbolos)
        interp.executar()
        return interp

    def test_basic_math_and_assignment(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a, b, c uai
            trem_cum_virgula d uai
            a fica_assim_entao 10 uai
            b fica_assim_entao 3 uai
            c fica_assim_entao a + b uai  // c = 13
            d fica_assim_entao 10.0 sob 4.0 uai // d = 2.5
            a fica_assim_entao a / b uai  // a = 3 (divisão inteira)
            b fica_assim_entao 10 % 3 uai // b = 1
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["c"], 13)
        self.assertEqual(interp.variaveis["d"], 2.5)
        self.assertEqual(interp.variaveis["a"], 3)
        self.assertEqual(interp.variaveis["b"], 1)

    def test_conditionals_and_jumps(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru x, y uai
            x fica_assim_entao 5 uai
            uai_se (x > 2) simbora
                y fica_assim_entao 1 uai
            cabo
            uai_senao simbora
                y fica_assim_entao 2 uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["y"], 1)

        src2 = """
        bora_cumpade main()
        simbora
            trem_di_numeru x, y uai
            x fica_assim_entao 1 uai
            uai_se (x > 2) simbora
                y fica_assim_entao 1 uai
            cabo
            uai_senao simbora
                y fica_assim_entao 2 uai
            cabo
        cabo
        """
        interp2 = self.run_source(src2)
        self.assertEqual(interp2.variaveis["y"], 2)

    def test_while_loop(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru i, sum uai
            i fica_assim_entao 1 uai
            sum fica_assim_entao 0 uai
            enquanto_tiver_trem (i <= 5) simbora
                sum fica_assim_entao sum + i uai
                i fica_assim_entao i + 1 uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["sum"], 15)
        self.assertEqual(interp.variaveis["i"], 6)

    def test_string_and_char_concatenation(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1, s2 uai
            trosso c1, c2 uai
            c1 fica_assim_entao 'A' uai
            c2 fica_assim_entao 'B' uai
            s1 fica_assim_entao "Ola " + "Mundo" uai
            s2 fica_assim_entao c1 + c2 uai
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["s1"], "Ola Mundo")
        self.assertEqual(interp.variaveis["s2"], "AB")

    def test_division_by_zero_raises(self) -> None:
        srcs = [
            """
            bora_cumpade main()
            simbora
                trem_di_numeru a uai
                a fica_assim_entao 10 / 0 uai
            cabo
            """,
            """
            bora_cumpade main()
            simbora
                trem_di_numeru a uai
                a fica_assim_entao 10 % 0 uai
            cabo
            """,
            """
            bora_cumpade main()
            simbora
                trem_cum_virgula a uai
                a fica_assim_entao 10.0 sob 0.0 uai
            cabo
            """
        ]
        for src in srcs:
            with self.subTest(src=src):
                tokens = self.lx.tokenize(src)
                p = Parser(tokens)
                quads = p.parse()
                interp = Interpretador(quads, p.tabela_simbolos)
                with self.assertRaises(ErroExecucao) as ctx:
                    interp.executar()
                self.assertIn("divisão por zero", str(ctx.exception).lower())

    @patch("builtins.input", side_effect=["42"])
    def test_read_integer_success(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru x uai
            xove(trem_di_numeru, x) uai
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["x"], 42)

    @patch("builtins.input", side_effect=["abc"])
    def test_read_integer_failure(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru x uai
            xove(trem_di_numeru, x) uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        interp = Interpretador(quads, p.tabela_simbolos)
        with self.assertRaises(ErroExecucao) as ctx:
            interp.executar()
        self.assertIn("Erro de leitura: tipo incompatível", str(ctx.exception))

    @patch("builtins.input", side_effect=["3.14"])
    def test_read_float_success(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_cum_virgula y uai
            xove(trem_cum_virgula, y) uai
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["y"], 3.14)

    @patch("builtins.input", side_effect=["not_a_float"])
    def test_read_float_failure(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_cum_virgula y uai
            xove(trem_cum_virgula, y) uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        interp = Interpretador(quads, p.tabela_simbolos)
        with self.assertRaises(ErroExecucao) as ctx:
            interp.executar()
        self.assertIn("Erro de leitura: tipo incompatível", str(ctx.exception))

    @patch("builtins.input", side_effect=["eh"])
    def test_read_bool_success(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_discolhe b uai
            xove(trem_discolhe, b) uai
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["b"], True)

    @patch("builtins.input", side_effect=["maybe"])
    def test_read_bool_failure(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_discolhe b uai
            xove(trem_discolhe, b) uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        interp = Interpretador(quads, p.tabela_simbolos)
        with self.assertRaises(ErroExecucao) as ctx:
            interp.executar()
        self.assertIn("Erro de leitura: tipo incompatível", str(ctx.exception))

    @patch("builtins.input", side_effect=["Z"])
    def test_read_char_success(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trosso c uai
            xove(trosso, c) uai
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["c"], "Z")

    @patch("builtins.input", side_effect=["longer_string"])
    def test_read_char_failure(self, mock_input) -> None:
        src = """
        bora_cumpade main()
        simbora
            trosso c uai
            xove(trosso, c) uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        interp = Interpretador(quads, p.tabela_simbolos)
        with self.assertRaises(ErroExecucao) as ctx:
            interp.executar()
        self.assertIn("Erro de leitura: tipo incompatível", str(ctx.exception))

    def test_print_capture(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            oia_proce_ve("Ola, mundo!") uai
            oia_proce_ve(eh) uai
        cabo
        """
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            self.run_source(src)
        finally:
            sys.stdout = sys.__stdout__
        
        self.assertEqual(captured_output.getvalue(), "Ola, mundo!\neh\n")


    def test_xor_operator(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_discolhe b1, b2, r1, r2, r3, r4 uai
            b1 fica_assim_entao eh uai
            b2 fica_assim_entao num_eh uai
            r1 fica_assim_entao b1 um_o_oto b2 uai // True XOR False -> True
            r2 fica_assim_entao b1 um_o_oto b1 uai // True XOR True -> False
            r3 fica_assim_entao b2 um_o_oto b2 uai // False XOR False -> False
            r4 fica_assim_entao b2 um_o_oto b1 uai // False XOR True -> True
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["r1"], True)
        self.assertEqual(interp.variaveis["r2"], False)
        self.assertEqual(interp.variaveis["r3"], False)
        self.assertEqual(interp.variaveis["r4"], True)

    def test_relational_equality_non_numeric(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1, s2 uai
            trem_discolhe eq1, eq2, dif1, dif2 uai
            s1 fica_assim_entao "Bao" uai
            s2 fica_assim_entao "Bao" uai
            eq1 fica_assim_entao s1 mema_coisa s2 uai // True
            dif1 fica_assim_entao s1 neh_nada s2 uai // False

            s2 fica_assim_entao "Uai" uai
            eq2 fica_assim_entao s1 mema_coisa s2 uai // False
            dif2 fica_assim_entao s1 neh_nada s2 uai // True
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["eq1"], True)
        self.assertEqual(interp.variaveis["dif1"], False)
        self.assertEqual(interp.variaveis["eq2"], False)
        self.assertEqual(interp.variaveis["dif2"], True)

    def test_while_loop_with_break(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru i, sum uai
            i fica_assim_entao 1 uai
            sum fica_assim_entao 0 uai
            enquanto_tiver_trem (i <= 10) simbora
                uai_se (i mema_coisa 5) simbora
                    para_o_trem uai
                cabo
                sum fica_assim_entao sum + i uai
                i fica_assim_entao i + 1 uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["sum"], 10)  # 1 + 2 + 3 + 4 = 10
        self.assertEqual(interp.variaveis["i"], 5)

    def test_while_loop_with_continue(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru i, sum uai
            i fica_assim_entao 0 uai
            sum fica_assim_entao 0 uai
            enquanto_tiver_trem (i < 5) simbora
                i fica_assim_entao i + 1 uai
                uai_se (i mema_coisa 3) simbora
                    toca_o_trem uai
                cabo
                sum fica_assim_entao sum + i uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["sum"], 12)  # 1 + 2 + 4 + 5 = 12

    def test_for_loop_with_break(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru sum uai
            trem_di_numeru i uai
            sum fica_assim_entao 0 uai
            roda_esse_trem (i fica_assim_entao 1; i <= 5; i fica_assim_entao i + 1) simbora
                uai_se (i mema_coisa 3) simbora
                    para_o_trem uai
                cabo
                sum fica_assim_entao sum + i uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["sum"], 3)  # 1 + 2 = 3

    def test_for_loop_with_continue(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru sum uai
            trem_di_numeru i uai
            sum fica_assim_entao 0 uai
            roda_esse_trem (i fica_assim_entao 1; i <= 4; i fica_assim_entao i + 1) simbora
                uai_se (i mema_coisa 2) simbora
                    toca_o_trem uai
                cabo
                sum fica_assim_entao sum + i uai
            cabo
        cabo
        """
        interp = self.run_source(src)
        self.assertEqual(interp.variaveis["sum"], 8)  # 1 + 3 + 4 = 8

    def test_break_outside_loop_raises(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            para_o_trem uai
        cabo
        """
        from analisador_sintatico import ErroSemantico
        with self.assertRaises(ErroSemantico) as ctx:
            tokens = self.lx.tokenize(src)
            Parser(tokens).parse()
        self.assertIn("só pode ser usado dentro de um laço", str(ctx.exception))

    def test_continue_outside_loop_raises(self) -> None:
        src = """
        bora_cumpade main()
        simbora
            toca_o_trem uai
        cabo
        """
        from analisador_sintatico import ErroSemantico
        with self.assertRaises(ErroSemantico) as ctx:
            tokens = self.lx.tokenize(src)
            Parser(tokens).parse()
        self.assertIn("só pode ser usado dentro de um laço", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
