from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, NoReturn, Tuple

# Inteiro com sinal 32 bits (constantes numéricas comuns no compilador)
_MAX_INT32 = 0x7FFF_FFFF

Token = Tuple[str, int, int, int]  # (Lexema, Token_ID_INT, Linha, Coluna)


class ErroLexico(Exception):
    """Levantada quando o analisador léxico encontra erro irrecuperável (ex.: número mal formado)."""


def _falha_numero(line: int, col: int, lexema: str, motivo: str) -> NoReturn:
    raise ErroLexico(
        f"Número mal formado: {motivo} (linha {line}, coluna {col}, lexema «{lexema}»)"
    )


TOKEN_IDS: Dict[str, int] = {
    # Palavras-chave / blocos
    "BORA_CUMPADE": 1,
    "SIMBORA": 2,
    "CABO": 3,
    "UAI": 4,

    # Tipos
    "TREM_DI_NUMERU": 5,
    "TREM_DI_NUMERU_DECIMAL": 6,
    "TREM_DI_NUMERU_OCTAL": 7,
    "TREM_DI_NUMERU_HEXA": 8,
    "TREM_CUM_VIRGULA": 9,
    "TREM_DISCRITA": 10,
    "TREM_DISCOLHE": 11,
    "TROSSO": 12,

    # Identificador
    "IDENTIFICADOR": 13,

    # Operadores e símbolos
    "ABRE_PAREN": 14,
    "FECHA_PAREN": 15,
    "VIRGULA": 16,
    "PONTO_VIRGULA": 17,
    "PONTO": 18,
    "DOIS_PONTOS": 19,

    "SOMA": 20,
    "SUBTRACAO": 21,
    "DIV_INTEIRA": 22,
    "MOD": 23,

    "MAIOR": 24,
    "MAIOR_IGUAL": 25,
    "MENOR": 26,
    "MENOR_IGUAL": 27,

    "FICA_ASSIM_ENTAO": 28,
    "MEMA_COISA_IGUAL": 29,
    "NEH_NADA_DIFERENTE": 30,

    "QUARQUE_UM_OR": 31,
    "TAMEM_AND": 32,
    "VAM_MARCA_NOT": 33,
    "UM_O_OTO_XOR": 34,

    # Controle
    "UAI_SE": 35,
    "UAI_SENAO": 36,
    "RODA_ESSE_TREM": 37,
    "ENQUANTO_TIVER_TREM": 38,
    "DEPENDENU": 39,
    "DU_CASU": 40,
    "TA_BAO": 41,
    "PARA_O_TREM": 42,
    "TOCA_O_TREM": 43,
    "EH_TRUE": 44,
    "NUM_EH_FALSE": 45,

    # IO / especiais
    "XOVE": 46,
    "OIA_PROCE_VE": 47,
    "MAIN": 48,
    "DEFAULT": 49,

    # Operadores aritméticos por palavra
    "VEIZ_MULT": 50,
    "SOB_DIV": 51,

    # Literais
    "STRING_LITERAL": 60,
    "CHAR_LITERAL": 61,

    # Erros
    "Números mal formados": 90,
    "Símbolos desconhecidos": 91,
    "String mal formada": 92,
    "String não fechada": 93,
    "Caractere mal formado": 94,
    "ERRO_COMENTARIO_NAO_FECHADO": 95,
}

# O id 9 (TREM_CUM_VIRGULA) designa a palavra "trem_cum_virgula" (tipo) e também literais float.
_TIPO_FLOAT_LEXEMA = "trem_cum_virgula"


def _nomes_variaveis_tipo_trem_cum_virgula(tokens: List[Token]) -> set:
    """
    Nomes declarados com o tipo `trem_cum_virgula` (ponto flutuante).
    Padrão: trem_cum_virgula id (, id)* até fechar a declaração.
    """
    t_ident = TOKEN_IDS["IDENTIFICADOR"]
    t_virg = TOKEN_IDS["VIRGULA"]
    out: set = set()
    i = 0
    n = len(tokens)
    while i < n:
        lex, tid, _a, _b = tokens[i]
        if tid == TOKEN_IDS["TREM_CUM_VIRGULA"] and lex == _TIPO_FLOAT_LEXEMA:
            i += 1
            while i < n:
                lx, tid2, _c, _d = tokens[i]
                if tid2 == t_ident:
                    out.add(lx)
                    i += 1
                    if i < n and tokens[i][0] == "," and tokens[i][1] == t_virg:
                        i += 1
                        continue
                break
        else:
            i += 1
    return out


def _coercao_intdecimal_para_float_apos_fica(
    tokens: List[Token], float_vars: set
) -> List[Token]:
    """
    Após fica_assim_entao, literal decimal inteiro (apenas [0-9]) atribuído
    a variável declarada com trem_cum_virgula vira N.0 (id de literal float 9).
    """
    t_fica = TOKEN_IDS["FICA_ASSIM_ENTAO"]
    t_int = TOKEN_IDS["TREM_DI_NUMERU_DECIMAL"]
    t_fl = TOKEN_IDS["TREM_CUM_VIRGULA"]
    t_ident = TOKEN_IDS["IDENTIFICADOR"]
    out: List[Token] = []
    for j, t in enumerate(tokens):
        lex, tid, ln, c = t
        if (
            tid == t_int
            and lex.isdigit()
            and (len(lex) == 1 or lex[0] != "0" or lex == "0")
            and j >= 2
            and tokens[j - 1][1] == t_fica
            and tokens[j - 2][1] == t_ident
            and tokens[j - 2][0] in float_vars
        ):
            out.append((f"{int(lex)}.0", t_fl, ln, c))
        else:
            out.append(t)
    return out


@dataclass
class _ScanResult:
    lexeme: str
    token_id: str
    line: int
    col: int
    next_index: int


class LexerMineres:
    """
    Analisador Léxico para "Mineirês".

    Requisitos:
    - Processa caractere por caractere em DFA (estados explícitos).
    - Retorna tokens no formato: (Lexema, Token_ID, Linha, Coluna).
    """

    # Palavras reservadas / palavras-chave (inclui operadores lógicos e alguns operadores aritméticos)
    _KEYWORDS: Dict[str, str] = {
    # Controle / estruturas
    "bora_cumpade": "BORA_CUMPADE",
    "main": "MAIN",
    "uai_se": "UAI_SE",
    "uai_senao": "UAI_SENAO",
    "roda_esse_trem": "RODA_ESSE_TREM",
    "enquanto_tiver_trem": "ENQUANTO_TIVER_TREM",
    "dependenu": "DEPENDENU",
    "du_casu": "DU_CASU",
    "default": "DEFAULT",
    "ta_bao": "TA_BAO",
    "para_o_trem": "PARA_O_TREM",
    "toca_o_trem": "TOCA_O_TREM",

    # Entrada / saída
    "xove": "XOVE",
    "oia_proce_ve": "OIA_PROCE_VE",

    # Tipos
    "trem_di_numeru": "TREM_DI_NUMERU",
    "trem_cum_virgula": "TREM_CUM_VIRGULA",
    "trem_discrita": "TREM_DISCRITA",
    "trem_discolhe": "TREM_DISCOLHE",
    "trosso": "TROSSO",

    # Valores lógicos
    "eh": "EH_TRUE",
    "num_eh": "NUM_EH_FALSE",

    # Blocos
    "simbora": "SIMBORA",
    "cabo": "CABO",

    # Terminador
    "uai": "UAI",

    # Operadores por palavra
    "fica_assim_entao": "FICA_ASSIM_ENTAO",
    "mema_coisa": "MEMA_COISA_IGUAL",
    "neh_nada": "NEH_NADA_DIFERENTE",

    # Lógicos
    "quarque_um": "QUARQUE_UM_OR",
    "tamem": "TAMEM_AND",
    "vam_marca": "VAM_MARCA_NOT",
    "um_o_oto": "UM_O_OTO_XOR",

    # Aritméticos por palavra
    "veiz": "VEIZ_MULT",
    "sob": "SOB_DIV",
}

    # Caracteres válidos em identificadores
    _IS_IDENT_START = staticmethod(lambda ch: ch.isalpha() or ch == "_")
    _IS_IDENT_PART = staticmethod(lambda ch: ch.isalnum() or ch == "_")

# Caracteres whitespace a serem ignorados
    _WHITESPACE = {" ", "\t", "\r", "\n"}

    # Separadores típicos (usados para ajudar na recuperação de erros)
    _SEPARATORS = {" ", "\t", "\r", "\n", "(", ")", ",", ";", "{", "}", "[", "]", ":"}

    # Após '\' em string/char literal (um caractere de escape)
    _VALID_ESCAPES = frozenset("ntr0'\"\\")

    def _to_token_id(self, token_name: str) -> int:
        return TOKEN_IDS.get(token_name, -1)
        
    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        line = 1
        col = 1

        while i < len(source):
            ch = source[i]

            # Ignora whitespace (atualiza linha/coluna)
            if ch in self._WHITESPACE:
                i, line, col = self._consume_whitespace(source, i, line, col)
                continue

            # Comentário de linha: // ... até fim de linha (uma / sozinha = divisão)
            if ch == "/" and i + 1 < len(source) and source[i + 1] == "/":
                j = i + 2
                while j < len(source) and source[j] != "\n":
                    j += 1
                consumido = source[i:j]
                i, line, col = self._advance_to(source, j, line, col, consumido)
                continue

            # Strings (aspas duplas) e char (aspas simples), com sequências de escape
            if ch == '"':
                res = self._scan_string_dfa(source, i, line, col)
                tokens.append((res.lexeme, self._to_token_id(res.token_id), res.line, res.col))
                texto_bruto = source[i:res.next_index]
                i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)
                continue

            if ch == "'":
                res = self._scan_char_dfa(source, i, line, col)
                tokens.append((res.lexeme, self._to_token_id(res.token_id), res.line, res.col))
                texto_bruto = source[i:res.next_index]
                i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)
                continue

            # Comentários iniciam com a palavra "causo"
            if self._IS_IDENT_START(ch):
                # Lê o "word" via DFA de identificador; pode virar palavra-chave (inclui causo)
                res = self._scan_identifier_or_keyword_dfa(source, i, line, col)
                if res.token_id == "COMMENT_SKIPPED":
                    # comentário já foi consumido; res.lexeme contém o intervalo consumido
                    texto_bruto = source[i:res.next_index]
                    i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)
                    continue
                tokens.append((res.lexeme, self._to_token_id(res.token_id), res.line, res.col))
                texto_bruto = source[i:res.next_index]
                i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)
                continue

            # Números (inclui float que começa com ponto: .5 → lexema 0.5)
            if ch.isdigit() or (
                ch == "."
                and i + 1 < len(source)
                and source[i + 1].isdigit()
            ):
                if ch == ".":
                    res = self._scan_number_dfa_leading_dot(source, i, line, col)
                else:
                    res = self._scan_number_dfa(source, i, line, col)
                tokens.append((res.lexeme, self._to_token_id(res.token_id), res.line, res.col))
                texto_bruto = source[i:res.next_index]
                i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)
                continue

            # Operadores e símbolos (1-2 caracteres)
            res = self._scan_operator_or_symbol_dfa(source, i, line, col)
            tokens.append((res.lexeme, self._to_token_id(res.token_id), res.line, res.col))
            texto_bruto = source[i:res.next_index]
            i, line, col = self._advance_to(source, res.next_index, line, col, texto_bruto)

        return self._pos_processa_literais_float(tokens)

    def tokenize_file(self, path: str, encoding: str = "utf-8") -> List[Token]:
        with open(path, "r", encoding=encoding) as f:
            return self.tokenize(f.read())

    # -------------------------
    # Utilidades de posição
    # -------------------------
    def _consume_whitespace(
        self, source: str, i: int, line: int, col: int
    ) -> Tuple[int, int, int]:
        while i < len(source) and source[i] in self._WHITESPACE:
            if source[i] == "\n":
                i += 1
                line += 1
                col = 1
            else:
                i += 1
                col += 1
        return i, line, col

    def _pos_processa_literais_float(
        self, tokens: List[Token]
    ) -> List[Token]:
        nomes = _nomes_variaveis_tipo_trem_cum_virgula(tokens)
        if not nomes:
            return tokens
        return _coercao_intdecimal_para_float_apos_fica(tokens, nomes)

    def _advance_to(
        self, source: str, next_index: int, line: int, col: int, consumed_lexeme: str
    ) -> Tuple[int, int, int]:
        """
        Atualiza line/colg conforme consumed_lexeme.
        Assumimos que consumed_lexeme é exatamente source[start:next_index].
        """
        # Atualiza usando o lexema consumido (DFA já calculou o tamanho correto).
        for c in consumed_lexeme:
            if c == "\n":
                line += 1
                col = 1
            else:
                col += 1
        return next_index, line, col

    # -------------------------
    # DFA: Identificador / Palavras-chave / Comentários
    # -------------------------
    def _scan_identifier_or_keyword_dfa(
        self, source: str, i: int, line: int, col: int
    ) -> _ScanResult:
        """
        DFA para [A-Za-z_][A-Za-z0-9_]*.
        Depois faz lookup em _KEYWORDS.

        Comentário:
        - se lexema == "causo", entra em DFA de comentário até "fim_do_causo".
        """

        class S:
            START = 0
            IN_IDENT = 1

        state = S.START
        j = i
        lexeme_chars: List[str] = []

        while j < len(source):
            ch = source[j]

            if state == S.START:
                if self._IS_IDENT_START(ch):
                    state = S.IN_IDENT
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                # se cair aqui, não deveria acontecer pois chamamos só quando _IS_IDENT_START
                break

            if state == S.IN_IDENT:
                if self._IS_IDENT_PART(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                break

        lexeme = "".join(lexeme_chars)

        # DFA extra para comentário: trata "causo ... fim_do_causo"
        if lexeme == "causo":
            res = self._scan_comment_dfa(source, j, line, col, already_consumed=lexeme)
            return res

        token_id = self._KEYWORDS.get(lexeme)
        if token_id is None:
            token_id = "IDENTIFICADOR"
        return _ScanResult(lexeme=lexeme, token_id=token_id, line=line, col=col, next_index=j)

    # -------------------------
    # DFA: Comentários multilinha
    # -------------------------
    def _scan_comment_dfa(
        self,
        source: str,
        j: int,
        line: int,
        col: int,
        already_consumed: str,
    ) -> _ScanResult:
        """
        Consome até encontrar palavra fechadora "fim_do_causo".

        Não emite token (skip).
        Se EOF for atingido antes do fechamento, emite erro.
        """

        closing = "fim_do_causo"
        # KMP (DFA) para procurar a sequência exata "fim_do_causo".
        lps = self._kmp_build_lps(closing)

        k = 0  # quantos caracteres de closing já "batem"
        k_start_line, k_start_col = line, col
        lexeme_chars: List[str] = [already_consumed]

        # Atualiza linha/col conforme already_consumed
        # (aqui já foi consumido pelo chamador, mas ainda não atualizamos linha/col do caller;
        #  usamos o lexeme para avançar no caller depois, então mantemos só para consistência interna).
        # A atualização real de linha/col é feita no caller via _advance_to com consumed_lexeme.

        while j < len(source):
            ch = source[j]
            lexeme_chars.append(ch)

            # Atualiza KMP
            while k > 0 and ch != closing[k]:
                k = lps[k - 1]
            if ch == closing[k]:
                k += 1
            if k == len(closing):
                # fechou: precisa garantir boundary (word boundary simplificado)
                after = source[j + 1] if (j + 1) < len(source) else ""
                before = source[j - len(closing)] if (j - len(closing)) >= 0 else ""
                # Boundary aproximado: antes/depois não sejam [A-Za-z0-9_]
                if (before == "" or not self._IS_IDENT_PART(before)) and (
                    after == "" or not self._IS_IDENT_PART(after)
                ):
                    consumed = "".join(lexeme_chars)
                    return _ScanResult(
                        lexeme=consumed,
                        token_id="COMMENT_SKIPPED",
                        line=k_start_line,
                        col=k_start_col,
                        next_index=j + 1,
                    )
                # Se não era boundary, continua procurando (fallback do KMP)
                k = lps[k - 1]

            j += 1

        # EOF sem fechamento
        consumed = "".join(lexeme_chars)
        return _ScanResult(
            lexeme=consumed,
            token_id="ERRO_COMENTARIO_NAO_FECHADO",
            line=k_start_line,
            col=k_start_col,
            next_index=j,
        )

    def _kmp_build_lps(self, pattern: str) -> List[int]:
        lps = [0] * len(pattern)
        length = 0
        i = 1
        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps

    # -------------------------
    # DFA: Strings delimitadas por aspas duplas (com escape \)
    # -------------------------
    def _scan_string_dfa(self, source: str, i: int, line: int, col: int) -> _ScanResult:
        """
        Aspas duplas "...". Aceita \\, \\n, \\t, \\r, \\0, \\', \\", etc.
        Aspas de fechamento só contam se não forem precedidas por \\ (exceto \\\\).
        """
        if i >= len(source) or source[i] != '"':
            return _ScanResult(
                lexeme=source[i : i + 1] if i < len(source) else "",
                token_id="Símbolos desconhecidos",
                line=line,
                col=col,
                next_index=min(i + 1, len(source)),
            )

        j = i + 1
        lexeme_chars: List[str] = [source[i]]

        while j < len(source):
            ch = source[j]

            if ch == "\\":
                j += 1

                if j >= len(source):
                    lexeme_chars.append("\\")  # Acabou do nada, põe a barra
                    break

                esc = source[j]

                if esc not in self._VALID_ESCAPES:
                    # ESCAPE INVÁLIDO (mantém o seu erro)
                    lexeme_chars.append("\\")
                    lexeme_chars.append(esc)
                    j += 1

                    # Consome até a aspas de fechamento...
                    while j < len(source):
                        c = source[j]

                        if c == "\\":
                            lexeme_chars.append(c)
                            j += 1
                            if j < len(source):
                                lexeme_chars.append(source[j])
                                j += 1
                            continue

                        lexeme_chars.append(c)
                        j += 1

                        if c == '"':
                            break

                    return _ScanResult(
                        lexeme="".join(lexeme_chars),
                        token_id="String mal formada",
                        line=line,
                        col=col,
                        next_index=j,
                    )

                else:
                    # ESCAPE VÁLIDO: Traduz os dois caracteres (\ e n) para 1 só!
                    mapa_escapes = {
                        "n": "\n",
                        "t": "\t",
                        "r": "\r",
                        "0": "\0",
                        "'": "'",
                        '"': '"',
                        "\\": "\\",
                    }
                    lexeme_chars.append(mapa_escapes[esc])
                    j += 1
                    continue

            elif ch == "\n" or ch == "\r":
                lexeme_chars.append(ch)
                j += 1
                return _ScanResult(
                    lexeme="".join(lexeme_chars),
                    token_id="String mal formada",
                    line=line,
                    col=col,
                    next_index=j,
                )

            else:
                lexeme_chars.append(ch)
                j += 1

                if ch == '"':
                    return _ScanResult(
                        lexeme="".join(lexeme_chars),
                        token_id="STRING_LITERAL",
                        line=line,
                        col=col,
                        next_index=j,
                    )

        return _ScanResult(
            lexeme="".join(lexeme_chars),
            token_id="String não fechada",
            line=line,
            col=col,
            next_index=j,
        )

    # -------------------------
    # DFA: Char entre aspas simples 'c' ou '\\n' (um único caractere após decodificar)
    # -------------------------
    def _scan_char_dfa(self, source: str, i: int, line: int, col: int) -> _ScanResult:
        """
        Literal trosso: 'x' ou escapes como '\\n', '\\t', '\\'', '\\\\', etc.
        Deve fechar com aspas simples; conteúdo inválido => Caractere mal formado.
        """
        if i >= len(source) or source[i] != "'":
            return _ScanResult(
                lexeme=source[i : i + 1] if i < len(source) else "",
                token_id="Símbolos desconhecidos",
                line=line,
                col=col,
                next_index=min(i + 1, len(source)),
            )

        j = i + 1
        lexeme_chars: List[str] = [source[i]]

        if j >= len(source):
            return _ScanResult(
                lexeme="".join(lexeme_chars),
                token_id="String não fechada",
                line=line,
                col=col,
                next_index=j,
            )

        if source[j] == "'":
            lexeme_chars.append(source[j])
            j += 1
            return _ScanResult(
                lexeme="".join(lexeme_chars),
                token_id="Caractere mal formado",
                line=line,
                col=col,
                next_index=j,
            )

        elif source[j] == "\\":
            j += 1

            if j >= len(source):
                lexeme_chars.append("\\")
                return _ScanResult(
                    lexeme="".join(lexeme_chars),
                    token_id="String não fechada",
                    line=line,
                    col=col,
                    next_index=j,
                )

            esc = source[j]

            if esc not in self._VALID_ESCAPES:
                lexeme_chars.append("\\")
                lexeme_chars.append(esc)
                j += 1
                return _ScanResult(
                    lexeme="".join(lexeme_chars),
                    token_id="Caractere mal formado",
                    line=line,
                    col=col,
                    next_index=j,
                )

            else:
                mapa_escapes = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "0": "\0",
                    "'": "'",
                    '"': '"',
                    "\\": "\\",
                }
                lexeme_chars.append(mapa_escapes[esc])
                j += 1

        else:
            c = source[j]

            if c in "\n\r":
                lexeme_chars.append(c)
                j += 1
                return _ScanResult(
                    lexeme="".join(lexeme_chars),
                    token_id="Caractere mal formado",
                    line=line,
                    col=col,
                    next_index=j,
                )

            lexeme_chars.append(c)
            j += 1

        if j >= len(source):
            return _ScanResult(
                lexeme="".join(lexeme_chars),
                token_id="String não fechada",
                line=line,
                col=col,
                next_index=j,
            )

        elif source[j] != "'":
            return _ScanResult(
                lexeme="".join(lexeme_chars),
                token_id="Caractere mal formado",
                line=line,
                col=col,
                next_index=j,
            )

        else:
            lexeme_chars.append(source[j])
            j += 1
            return _ScanResult(
                lexeme="".join(lexeme_chars),
                token_id="CHAR_LITERAL",
                line=line,
                col=col,
                next_index=j,
            )

    # -------------------------
    # DFA: Número (hex, octal, decimal, float)
    # -------------------------
    def _scan_number_dfa(self, source: str, i: int, line: int, col: int) -> _ScanResult:
        """
        Regras (conforme enunciado):
        - Hex: 0x [0-9a-fA-F]+
        - Octal: 0 [1-7] [0-7]*
        - Decimal: 0 | [1-9][0-9]*
        - Float: [0-9]+ '.' [0-9]+  (ex: 3.14);  N.  → N.0
        """

        class S:
            START = 0
            AFTER_0 = 1
            AFTER_0_DOT = 2
            HEX_PREFIX_X = 3
            HEX_DIGITS = 4
            OCTAL_FIRST_DIGIT = 5
            OCTAL_DIGITS = 6
            DECIMAL_DIGITS = 7
            DECIMAL_DOT = 8
            FLOAT_FRAC = 9
            ERROR = 10
            FLOAT_PONTO_SEM_FRAC = 11  # "2." ou "0." → 2.0 / 0.0

        def is_hex_digit(ch: str) -> bool:
            return ch.isdigit() or ("a" <= ch.lower() <= "f")

        # OBS - Trocar por hash
        def is_octal_digit(ch: str) -> bool:
            return ch in "01234567"

        def is_dec_digit(ch: str) -> bool:
            return ch.isdigit()

        j = i
        state = S.START
        lexeme_chars: List[str] = []

        # Para erros, faremos consumo “conservador” até delimitador.
        # Mas como precisamos ser determinísticos, o consumo é baseado no conjunto permitido.
        allowed_error_chars = set("0123456789abcdefABCDEFxX._")

        while j < len(source):
            ch = source[j]

            if state == S.START:
                if ch == "0":
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.AFTER_0
                    continue
                elif "1" <= ch <= "9":
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.DECIMAL_DIGITS
                    continue
                # caso improvável
                break

            elif state == S.AFTER_0:
                # 0 pode ser decimal puro, ou iniciar float (0.xxx), hex (0x...), ou octal (0[1-7]...)
                if ch == ".":
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.AFTER_0_DOT
                    continue
                elif ch in ("x", "X"):
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.HEX_PREFIX_X
                    continue
                elif ch.isdigit():
                    # decimal puro (apenas '0') não aceita dígitos adicionais => erro
                    # exceto octal, que só é permitido se o primeiro dígito for [1-7]
                    if "1" <= ch <= "7":
                        lexeme_chars.append(ch)
                        j += 1
                        state = S.OCTAL_DIGITS
                        continue
                    elif ch in "01234567":
                        # já era '0' seguido por '0' => não previsto pela gramática
                        lexeme_chars.append(ch)
                        j += 1
                        state = S.ERROR
                        continue
                    # 8 ou 9 => inválido para octal/decimal com prefixo 0
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.ERROR
                    continue
                # não é dígito/dot/x => fim do número com lexema "0"
                break

            elif state == S.AFTER_0_DOT:
                if is_dec_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.FLOAT_FRAC
                    continue
                elif j >= len(source) or ch in self._SEPARATORS or ch == "/":
                    state = S.FLOAT_PONTO_SEM_FRAC
                    break
                state = S.ERROR
                break

            elif state == S.HEX_PREFIX_X:
                # precisa de pelo menos 1 dígito hex depois do 0x
                if is_hex_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.HEX_DIGITS
                    continue
                # 0x sem dígitos: não consome caractere inválido
                state = S.ERROR
                break

            elif state == S.HEX_DIGITS:
                if is_hex_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                break

            elif state == S.OCTAL_DIGITS:
                # após o primeiro dígito (1-7), aceita [0-7]*
                if is_octal_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                # 8 e 9 não podem fazer parte do octal: número mal formado (lexema inteiro)
                elif ch in "89":
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.ERROR
                    continue
                break

            elif state == S.DECIMAL_DIGITS:
                if is_dec_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                elif ch == ".":
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.DECIMAL_DOT
                    continue
                break

            elif state == S.DECIMAL_DOT:
                if is_dec_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    state = S.FLOAT_FRAC
                    continue
                elif j >= len(source) or ch in self._SEPARATORS or ch == "/":
                    state = S.FLOAT_PONTO_SEM_FRAC
                    break
                state = S.ERROR
                break

            elif state == S.FLOAT_FRAC:
                if is_dec_digit(ch):
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                break

            elif state == S.ERROR:
                # Consome mais caracteres prováveis de número antes de retornar o erro
                if ch in allowed_error_chars:
                    lexeme_chars.append(ch)
                    j += 1
                    continue
                break

        # "12." ou "0." no fim de arquivo (j == len): ainda em DECIMAL_DOT / AFTER_0_DOT
        if state == S.DECIMAL_DOT or state == S.AFTER_0_DOT:
            state = S.FLOAT_PONTO_SEM_FRAC

        lexeme = "".join(lexeme_chars)

        if state == S.HEX_DIGITS:
            return _ScanResult(
                lexeme=lexeme,
                token_id="TREM_DI_NUMERU_HEXA",
                line=line,
                col=col,
                next_index=j
            )

        elif state == S.OCTAL_DIGITS:
            try:
                v = int(lexeme, 8)
            except ValueError:
                _falha_numero(line, col, lexeme, "literal octal inválido")
            if v > _MAX_INT32:
                _falha_numero(
                    line, col, lexeme, "estouro em literal octal (excede 32 bits com sinal)"
                )
            return _ScanResult(
                lexeme=lexeme,
                token_id="TREM_DI_NUMERU_OCTAL",
                line=line,
                col=col,
                next_index=j
            )

        elif state == S.AFTER_0:
            # lexema deve ser "0"
            return _ScanResult(
                lexeme=lexeme,
                token_id="TREM_DI_NUMERU_DECIMAL",
                line=line,
                col=col,
                next_index=j
            )

        elif state == S.DECIMAL_DIGITS:
            return _ScanResult(
                lexeme=lexeme,
                token_id="TREM_DI_NUMERU_DECIMAL",
                line=line,
                col=col,
                next_index=j
            )

        elif state == S.FLOAT_FRAC:
            return _ScanResult(
                lexeme=lexeme,
                token_id="TREM_CUM_VIRGULA",
                line=line,
                col=col,
                next_index=j
            )

        elif state == S.FLOAT_PONTO_SEM_FRAC:
            return _ScanResult(
                lexeme=lexeme + "0",
                token_id="TREM_CUM_VIRGULA",
                line=line,
                col=col,
                next_index=j
            )

        elif state in (S.ERROR, S.HEX_PREFIX_X):
            _falha_numero(line, col, lexeme, "sequência numérica inválida")

        # Caso inesperado
        _falha_numero(line, col, lexeme, "literal numérico inválido")

    def _scan_number_dfa_leading_dot(
        self, source: str, i: int, line: int, col: int
    ) -> _ScanResult:
        """
        Float com zero à esquerda: .5 e .07 → lexemas 0.5 e 0.07.
        Só chamar quando source[i] == '.' e o próximo caractere for dígito.
        """

        if i >= len(source):
            _falha_numero(line, col, "", "esperava '.' no literal")

        elif source[i] != ".":
            _falha_numero(line, col, source[i : i + 1], "esperava '.' no literal")

        j = i + 1
        lexeme_chars: List[str] = ["0", "."]

        if j >= len(source):
            _falha_numero(
                line, col, "0.", "parte fracionária de float exige ao menos um dígito"
            )

        elif not source[j].isdigit():
            _falha_numero(
                line, col, "0.", "parte fracionária de float exige ao menos um dígito"
            )

        while j < len(source) and source[j].isdigit():
            lexeme_chars.append(source[j])
            j += 1

        return _ScanResult(
            lexeme="".join(lexeme_chars),
            token_id="TREM_CUM_VIRGULA",
            line=line,
            col=col,
            next_index=j,
        )

    # -------------------------
    # DFA: Operadores e símbolos (inclui multi-caracter)
    # -------------------------
    def _scan_operator_or_symbol_dfa(
        self, source: str, i: int, line: int, col: int
    ) -> _ScanResult:
        """
        Reconhece operadores/símbolos relevantes:
        - > >=
        - < <=
        - + -
        - % (mod)
        - ( ) ,  (pelo menos para suportar o exemplo do enunciado)
        - '/' divisão inteira (DIV_INTEIRA); divisão real é a palavra 'sob' (SOB_DIV)
        - '=' não existe no spec
        """

        ch = source[i]

        # Relacionais
        if ch == ">":
            if i + 1 < len(source) and source[i + 1] == "=":
                return _ScanResult(
                    lexeme=">=",
                    token_id="MAIOR_IGUAL",
                    line=line,
                    col=col,
                    next_index=i + 2,
                )
            else:
                return _ScanResult(
                    lexeme=">",
                    token_id="MAIOR",
                    line=line,
                    col=col,
                    next_index=i + 1,
                )

        elif ch == "<":
            if i + 1 < len(source) and source[i + 1] == "=":
                return _ScanResult(
                    lexeme="<=",
                    token_id="MENOR_IGUAL",
                    line=line,
                    col=col,
                    next_index=i + 2,
                )
            else:
                return _ScanResult(
                    lexeme="<",
                    token_id="MENOR",
                    line=line,
                    col=col,
                    next_index=i + 1,
                )

        # Aritméticos e símbolos
        elif ch == "+":
            return _ScanResult("+", "SOMA", line=line, col=col, next_index=i + 1)

        elif ch == "-":
            return _ScanResult("-", "SUBTRACAO", line=line, col=col, next_index=i + 1)

        elif ch == "%":
            return _ScanResult("%", "MOD", line=line, col=col, next_index=i + 1)

        elif ch == "/":
            return _ScanResult("/", "DIV_INTEIRA", line=line, col=col, next_index=i + 1)

        # Pontuação (para suportar exemplo)
        elif ch == "(":
            return _ScanResult("(", "ABRE_PAREN", line=line, col=col, next_index=i + 1)

        elif ch == ")":
            return _ScanResult(")", "FECHA_PAREN", line=line, col=col, next_index=i + 1)

        elif ch == ",":
            return _ScanResult(",", "VIRGULA", line=line, col=col, next_index=i + 1)

        elif ch == ";":
            return _ScanResult(";", "PONTO_VIRGULA", line=line, col=col, next_index=i + 1)

        elif ch == ".":
            return _ScanResult(".", "PONTO", line=line, col=col, next_index=i + 1)

        elif ch == ":":
            return _ScanResult(":", "DOIS_PONTOS", line=line, col=col, next_index=i + 1)

        # Se cair aqui, é símbolo desconhecido
        else:
            return _ScanResult(
                lexeme=ch,
                token_id="Símbolos desconhecidos",
                line=line,
                col=col,
                next_index=i + 1,
            )