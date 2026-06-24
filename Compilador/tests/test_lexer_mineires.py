"""
Testes do lexer (float com 0 à esquerda, octal com estouro, erros numéricos,
comentários //, divisão /) e integração lexer + parser.

Executar a partir da pasta analisador_lexico:

    PYTHONPATH=src python3 -m unittest discover -s tests -v

Ou, com pytest instalado:

    cd analisador_lexico && pytest tests/ -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Garante import de lexer_mineires ao rodar `python -m unittest` de qualquer cwd
_TESTS_DIR = Path(__file__).resolve().parent
_ANALISADOR_LEXICO = _TESTS_DIR.parent
_SRC = _ANALISADOR_LEXICO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lexer_mineires import TOKEN_IDS, ErroLexico, LexerMineres  # noqa: E402

# IDs usados nas asserções (espelham TOKEN_IDS)
ID_FLOAT = TOKEN_IDS["FLOAT_LITERAL"]
ID_DEC = TOKEN_IDS["INT_DECIMAL_LITERAL"]
ID_OCT = TOKEN_IDS["INT_OCTAL_LITERAL"]
ID_HEX = TOKEN_IDS["INT_HEXA_LITERAL"]
ID_DIV = TOKEN_IDS["DIV_INTEIRA"]
ID_PONTO = TOKEN_IDS["PONTO"]
ID_IDENT = TOKEN_IDS["IDENTIFICADOR"]


def _only_ids_and_lexemes(tokens: list[tuple]) -> list[tuple[str, int]]:
    return [(lex, tid) for lex, tid, _ln, _col in tokens]


class TestFloatLeadingZeroLexeme(unittest.TestCase):
    """Literal com ponto à esquerda vira lexema com 0 antes do ponto."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_dot_fraction_becomes_zero_prefix(self) -> None:
        for src, expected_lex in [
            (".5", "0.5"),
            (".01", "0.01"),
            (".0", "0.0"),
        ]:
            with self.subTest(src=src):
                t = self.lx.tokenize(src)
                self.assertEqual(len(t), 1, t)
                self.assertEqual(t[0][0], expected_lex)
                self.assertEqual(t[0][1], ID_FLOAT)

    def test_float_with_integer_part_unchanged(self) -> None:
        t = self.lx.tokenize("3.14")
        self.assertEqual(_only_ids_and_lexemes(t), [("3.14", ID_FLOAT)])

    def test_zero_dot_form(self) -> None:
        t = self.lx.tokenize("0.25")
        self.assertEqual(_only_ids_and_lexemes(t), [("0.25", ID_FLOAT)])

    def test_dot_not_followed_by_digit_is_ponto(self) -> None:
        t = self.lx.tokenize(". x")
        self.assertEqual(t[0][1], ID_PONTO)
        self.assertEqual(t[1][1], ID_IDENT)

    def test_mixed_line(self) -> None:
        t = self.lx.tokenize(".5 + .25")
        self.assertEqual(
            _only_ids_and_lexemes(t),
            [("0.5", ID_FLOAT), ("+", TOKEN_IDS["SOMA"]), ("0.25", ID_FLOAT)],
        )


class TestNumericSignedInt32Bound(unittest.TestCase):
    """Literais válidos; estouro acima de 0x7FFFFFFF → ErroLexico."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_max_int32_octal_ok(self) -> None:
        # 0o17777777777 == 0x7FFFFFFF
        src = "017777777777"
        t = self.lx.tokenize(src)
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0][0], src)
        self.assertEqual(t[0][1], ID_OCT)

    def test_common_small_octal(self) -> None:
        t = self.lx.tokenize("0123")
        self.assertEqual(_only_ids_and_lexemes(t), [("0123", ID_OCT)])

    def test_octal_overflow_raises(self) -> None:
        # 0o20000000000 == 2^31, maior que 0x7FFFFFFF
        with self.assertRaises(ErroLexico) as ctx:
            self.lx.tokenize("020000000000")
        self.assertIn("estouro", str(ctx.exception).lower())

    def test_max_int32_decimal_ok(self) -> None:
        src = "2147483647"
        t = self.lx.tokenize(src)
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0][0], src)
        self.assertEqual(t[0][1], ID_DEC)

    def test_decimal_overflow_raises(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            self.lx.tokenize("2147483648")
        self.assertIn("estouro", str(ctx.exception).lower())

    def test_max_int32_hex_ok(self) -> None:
        src = "0x7FFFFFFF"
        t = self.lx.tokenize(src)
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0][0], src)
        self.assertEqual(t[0][1], ID_HEX)

    def test_hex_overflow_raises(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            self.lx.tokenize("0x80000000")
        self.assertIn("estouro", str(ctx.exception).lower())


class TestMalformedNumberAborts(unittest.TestCase):
    """Número inválido levanta ErroLexico (não emite token 90)."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def _assert_mal_num(self, src: str) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            self.lx.tokenize(src)
        self.assertIn("Número mal formado", str(ctx.exception))

    def test_hex_without_digits(self) -> None:
        self._assert_mal_num("0x")

    def test_zero_followed_by_zero(self) -> None:
        # Gramática: 0 extra após 0 isolado
        self._assert_mal_num("00")

    def test_leading_zero_then_8(self) -> None:
        self._assert_mal_num("08")

    def test_invalid_octal_digit_8_9_fails_as_whole(self) -> None:
        for bad in ("02778", "0128", "018"):
            with self.subTest(bad=bad):
                with self.assertRaises(ErroLexico):
                    self.lx.tokenize(bad)


class TestLineCommentSlashSlash(unittest.TestCase):
    """// até fim de linha é comentário (não gera token)."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_rest_of_line_skipped_including_trailing_code(self) -> None:
        t = self.lx.tokenize("1//2")
        self.assertEqual(_only_ids_and_lexemes(t), [("1", ID_DEC)])

    def test_newline_allows_next_token(self) -> None:
        t = self.lx.tokenize("a// b\n2")
        self.assertEqual(
            _only_ids_and_lexemes(t),
            [("a", ID_IDENT), ("2", ID_DEC)],
        )

    def test_empty_comment(self) -> None:
        t = self.lx.tokenize("x//\n3")
        self.assertEqual(_only_ids_and_lexemes(t), [("x", ID_IDENT), ("3", ID_DEC)])

    def test_only_comment_line_then_identifier(self) -> None:
        t = self.lx.tokenize("// início\ncabo")
        self.assertEqual(_only_ids_and_lexemes(t), [("cabo", TOKEN_IDS["CABO"])])


class TestSingleSlashIsDivision(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_spaced(self) -> None:
        t = self.lx.tokenize("10 / 2")
        self.assertEqual(
            _only_ids_and_lexemes(t),
            [("10", ID_DEC), ("/", ID_DIV), ("2", ID_DEC)],
        )

    def test_no_space(self) -> None:
        t = self.lx.tokenize("10/2")
        self.assertEqual(
            _only_ids_and_lexemes(t),
            [("10", ID_DEC), ("/", ID_DIV), ("2", ID_DEC)],
        )

    def test_not_consumed_by_comment(self) -> None:
        t = self.lx.tokenize("1/ not_slash 2")
        # "/" seguido de espaço, não é "//"
        self.assertIn("/", [x[0] for x in t])


class TestCausoBlockCommentStillWorks(unittest.TestCase):
    """Comentário bloco 'causo'…'fim_do_causo' continua a ser ignorado."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_skip_block(self) -> None:
        t = self.lx.tokenize("cabo causo oi fim_do_causo uai")
        # caus… consome tudo; tokens reais: cabo, uai
        lexs = [x[0] for x in t]
        self.assertIn("cabo", lexs)
        self.assertIn("uai", lexs)


class TestNoMalFormedNumberTokenId(unittest.TestCase):
    """Após alteração, o lexer não deve colocar ID 90 na lista por número ruim."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_invalid_number_raises_not_token_90(self) -> None:
        id_90 = TOKEN_IDS["Números mal formados"]
        for bad in ("0x", "00"):
            with self.subTest(bad=bad):
                with self.assertRaises(ErroLexico):
                    self.lx.tokenize(bad)
                # Não chama o lexer para concluir — só garante que o fluxo é exceção
        # Caso sadio não usa 90
        t = self.lx.tokenize("42")
        self.assertTrue(all(tid != id_90 for _l, tid, _a, _b in t))


class TestIntegrationLexerOnSampleFile(unittest.TestCase):
    def test_teste_completo_lexes_without_error(self) -> None:
        path = _ANALISADOR_LEXICO / "input" / "teste_completo.txt"
        if not path.is_file():
            self.skipTest(f"Arquivo de entrada ausente: {path}")
        lx = LexerMineres()
        tokens = lx.tokenize_file(str(path))
        self.assertGreater(len(tokens), 10)
        # 7.5 e literais conhecidos
        lexs = [t[0] for t in tokens]
        self.assertIn("7.5", lexs)
        # Nada de token de erro 90 vindo de número (pode existir 90? não deve)
        self.assertNotIn(TOKEN_IDS["Números mal formados"], [t[1] for t in tokens])


class TestAllInputTxtFilesLex(unittest.TestCase):
    """Regression: todo .txt em input/ deve lexar sem ErroLexico."""

    def test_each_input_txt(self) -> None:
        inp = _ANALISADOR_LEXICO / "input"
        if not inp.is_dir():
            self.skipTest(f"Pasta input ausente: {inp}")
        paths = sorted(inp.glob("*.txt"))
        self.assertGreater(len(paths), 0, "Nenhum .txt em input/")
        lx = LexerMineres()
        for path in paths:
            with self.subTest(file=path.name):
                tokens = lx.tokenize_file(str(path))
                self.assertGreater(len(tokens), 0, path)


class TestIntegrationLexerParserSampleFile(unittest.TestCase):
    def test_teste_completo_parses(self) -> None:
        from analisador_sintatico import Parser, ErroSintatico  # import tardio

        path = _ANALISADOR_LEXICO / "input" / "teste_completo.txt"
        if not path.is_file():
            self.skipTest(f"Arquivo de entrada ausente: {path}")
        lx = LexerMineres()
        tokens = lx.tokenize_file(str(path))
        try:
            Parser(tokens).parse()
        except ErroSintatico as e:
            self.fail(f"Parser rejeitou teste completo: {e}")


class TestHexAndDecimalSanity(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_hex(self) -> None:
        t = self.lx.tokenize("0xFF")
        self.assertEqual(_only_ids_and_lexemes(t), [("0xFF", ID_HEX)])

    def test_hex_zero(self) -> None:
        t = self.lx.tokenize("0x0")
        self.assertEqual(_only_ids_and_lexemes(t), [("0x0", ID_HEX)])

    def test_decimal(self) -> None:
        t = self.lx.tokenize("100")
        self.assertEqual(_only_ids_and_lexemes(t), [("100", ID_DEC)])


class TestCommentEdgeCases(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_triple_slash_all_comment_after_first_line_comment(self) -> None:
        t = self.lx.tokenize("x///")
        self.assertEqual(_only_ids_and_lexemes(t), [("x", ID_IDENT)])

    def test_slash_slash_at_eof(self) -> None:
        t = self.lx.tokenize("7//")
        self.assertEqual(_only_ids_and_lexemes(t), [("7", ID_DEC)])

    def test_leading_line_comment(self) -> None:
        t = self.lx.tokenize("// ignore\n0")
        self.assertEqual(_only_ids_and_lexemes(t), [("0", ID_DEC)])


class TestFloatTrailingDotZero(unittest.TestCase):
    """12. e 0. passam a ser 12.0 e 0.0 (id float)."""

    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_integer_dot(self) -> None:
        self.assertEqual(
            _only_ids_and_lexemes(self.lx.tokenize("12.")), [("12.0", ID_FLOAT)]
        )

    def test_zero_dot(self) -> None:
        self.assertEqual(_only_ids_and_lexemes(self.lx.tokenize("0.")), [("0.0", ID_FLOAT)])


class TestIntLiteralToFloatVarAfterFica(unittest.TestCase):
    """Literal 2 (decimal) vira 2.0 se o destino for variável declared trem_cum_virgula."""

    def test_two_becomes_2_0(self) -> None:
        src = "trem_cum_virgula f1 uai f1 fica_assim_entao 2 uai"
        t = LexerMineres().tokenize(src)
        self.assertIn(("2.0", ID_FLOAT), _only_ids_and_lexemes(t))

    def test_int_var_stays_integer_token(self) -> None:
        src = "trem_di_numeru a uai a fica_assim_entao 2 uai"
        t = LexerMineres().tokenize(src)
        self.assertIn(("2", ID_DEC), _only_ids_and_lexemes(t))
        self.assertNotIn("2.0", [x[0] for x in t])


class TestFloatMultilineAndStress(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_float_on_second_line(self) -> None:
        t = self.lx.tokenize("\n  .5\n")
        self.assertEqual(t[0][0], "0.5")
        self.assertEqual(t[0][1], ID_FLOAT)
        self.assertEqual(t[0][2], 2)  # linha

    def test_long_dot_fraction(self) -> None:
        t = self.lx.tokenize(".12345")
        self.assertEqual(t[0][0], "0.12345")


class TestSwitchCaseSyntaxAndCodeGen(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_switch_case_variables_not_allowed(self) -> None:
        from analisador_sintatico import Parser, ErroSintatico
        # 'y' is an identifier variable, which shouldn't be allowed inside du_casu
        src = "bora_cumpade main() simbora trem_di_numeru x uai dependenu (x) simbora du_casu y: x fica_assim_entao 1 uai cabo cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSintatico) as ctx:
            p.parse()
        self.assertIn("esperava literal", str(ctx.exception))

    def test_switch_case_code_generation(self) -> None:
        from analisador_sintatico import Parser
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru contador, x uai
            dependenu (contador)
            simbora
                du_casu 2:
                    x fica_assim_entao 1 uai
                default:
                    x fica_assim_entao 0 uai
            cabo
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        
        eq_quads = [q for q in quads if q[0] == "eq"]
        if_quads = [q for q in quads if q[0] == "if"]
        jump_quads = [q for q in quads if q[0] == "jump"]
        
        self.assertEqual(len(eq_quads), 1)
        self.assertEqual(eq_quads[0][2], "contador")
        self.assertEqual(eq_quads[0][3], "2")
        
        self.assertEqual(len(if_quads), 1)
        self.assertEqual(len(jump_quads), 1)
        self.assertTrue(jump_quads[0][1].startswith("l_fim_switch"))


class TestAssignmentLValueValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_valid_assignment_passes(self) -> None:
        from analisador_sintatico import Parser
        src = "bora_cumpade main() simbora trem_di_numeru x uai x fica_assim_entao 10 uai cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        try:
            p.parse()
        except Exception as e:
            self.fail(f"Valid assignment failed to parse: {e}")

    def test_invalid_assignment_literal_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSintatico
        # 5 fica_assim_entao 10 inside parenthesis as an expression
        src = "bora_cumpade main() simbora trem_di_numeru x uai x fica_assim_entao (5 fica_assim_entao 10) uai cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSintatico) as ctx:
            p.parse()
        self.assertIn("o lado esquerdo de uma atribuição deve ser um identificador", str(ctx.exception))

    def test_invalid_assignment_expression_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSintatico
        # (x + 1) fica_assim_entao 5 inside parenthesis as an expression
        src = "bora_cumpade main() simbora trem_di_numeru x uai x fica_assim_entao ((x + 1) fica_assim_entao 5) uai cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSintatico) as ctx:
            p.parse()
        self.assertIn("o lado esquerdo de uma atribuição deve ser um identificador", str(ctx.exception))


class TestSemanticAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        self.lx = LexerMineres()

    def test_re_declaration_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = "bora_cumpade main() simbora trem_di_numeru x, x uai cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("re-declaração", str(ctx.exception))

    def test_prior_declaration_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = "bora_cumpade main() simbora x fica_assim_entao 10 uai cabo"
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("não declarada", str(ctx.exception))

    def test_type_compatibility_assignment_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = 'bora_cumpade main() simbora trem_di_numeru x uai x fica_assim_entao "ola" uai cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("tipos incompatíveis na atribuição", str(ctx.exception))

    def test_invalid_operation_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = 'bora_cumpade main() simbora trem_discrita s uai s fica_assim_entao s - "a" uai cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("operação aritmética", str(ctx.exception))

    def test_invalid_condition_if_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = 'bora_cumpade main() simbora uai_se ("teste") simbora cabo cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("a condição do 'uai_se' deve ser do tipo bool", str(ctx.exception))

    def test_invalid_condition_while_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = 'bora_cumpade main() simbora enquanto_tiver_trem ("teste") simbora cabo cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("a condição do 'enquanto_tiver_trem' deve ser do tipo bool", str(ctx.exception))

    def test_invalid_condition_for_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = 'bora_cumpade main() simbora trem_di_numeru i uai roda_esse_trem (i fica_assim_entao 1; "teste"; i fica_assim_entao i + 1) simbora cabo cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("a condição do 'roda_esse_trem' deve ser do tipo bool", str(ctx.exception))

    def test_literal_hex_octal_conversion_in_quads(self) -> None:
        from analisador_sintatico import Parser
        # Hexa: 0xA -> 10, Octal: 012 -> 10
        src = 'bora_cumpade main() simbora trem_di_numeru x, y uai x fica_assim_entao 0xA uai y fica_assim_entao 012 uai cabo'
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        quads = p.parse()
        # filter for assignment quads
        att_quads = [q for q in quads if q[0] == "att" and q[1] in ("x", "y")]
        self.assertEqual(len(att_quads), 4)
        # Declaration default initializations
        self.assertEqual(att_quads[0], ("att", "x", "0", "none"))
        self.assertEqual(att_quads[1], ("att", "y", "0", "none"))
        # Actual assignments with converted hex/octal
        self.assertEqual(att_quads[2], ("att", "x", "10", "none"))
        self.assertEqual(att_quads[3], ("att", "y", "10", "none"))

    def test_string_and_char_addition_success(self) -> None:
        from analisador_sintatico import Parser
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1, s2, s3 uai
            trosso c1, c2 uai
            s1 fica_assim_entao "ola" uai
            s2 fica_assim_entao s1 + " mundo" uai
            s3 fica_assim_entao s2 + '!' uai
            s1 fica_assim_entao 'A' + s2 uai
            s2 fica_assim_entao 'A' + 'B' uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        try:
            p.parse()
        except Exception as e:
            self.fail(f"String and char addition failed: {e}")

    def test_string_subtraction_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1 uai
            s1 fica_assim_entao s1 - "a" uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("operação aritmética", str(ctx.exception))

    def test_string_multiplication_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1 uai
            s1 fica_assim_entao s1 veiz 3 uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("operação aritmética", str(ctx.exception))


    def test_float_to_int_assignment_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru x uai
            trem_cum_virgula y uai
            y fica_assim_entao 1.5 uai
            x fica_assim_entao y uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("tipos incompatíveis", str(ctx.exception))

    def test_int_to_float_assignment_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru x uai
            trem_cum_virgula y uai
            x fica_assim_entao 1 uai
            y fica_assim_entao x uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("tipos incompatíveis", str(ctx.exception))

    def test_logical_ops_on_int_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_di_numeru a, b uai
            trem_discolhe c uai
            c fica_assim_entao a tamem b uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("operação lógica", str(ctx.exception))

    def test_unary_minus_on_string_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s uai
            s fica_assim_entao -s uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("sinal unário exige operando numérico", str(ctx.exception))

    def test_relational_ops_on_strings_fails(self) -> None:
        from analisador_sintatico import Parser, ErroSemantico
        src = """
        bora_cumpade main()
        simbora
            trem_discrita s1, s2 uai
            trem_discolhe b uai
            b fica_assim_entao s1 < s2 uai
        cabo
        """
        tokens = self.lx.tokenize(src)
        p = Parser(tokens)
        with self.assertRaises(ErroSemantico) as ctx:
            p.parse()
        self.assertIn("comparação relacional", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
