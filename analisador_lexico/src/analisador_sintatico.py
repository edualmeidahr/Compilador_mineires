from __future__ import annotations

from lexer_mineires import TOKEN_IDS


class ErroSintatico(Exception):
    """Exceção usada para indicar erro sintático."""

    pass


class ErroSemantico(Exception):
    """Exceção usada para indicar erro semântico."""

    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.id_para_nome = {valor: chave for chave, valor in TOKEN_IDS.items()}

        # --- NOVOS CONTADORES PARA CÓDIGO INTERMEDIÁRIO ---
        self.cont_temp = 0
        self.cont_label = 0
        # --------------------------------------------------

        # --- CONTADORES E TABELAS SEMÂNTICAS ---
        self.tabela_simbolos = {}       # Dict[str, str]
        self.tipos_temporarios = {}     # Dict[str, str]
        self._tipo_keyword_para_simbolo = {
            TOKEN_IDS["TREM_DI_NUMERU"]: "a",
            TOKEN_IDS["TREM_CUM_VIRGULA"]: "f",
            TOKEN_IDS["TREM_DISCRITA"]: "s",
            TOKEN_IDS["TREM_DISCOLHE"]: "b",
            TOKEN_IDS["TROSSO"]: "c"
        }

        # Otimização: Instanciar os conjuntos de verificação (hashes) no construtor
        # Assim evitamos a recriação a cada chamada de função
        self._tipos_validos = frozenset(
            {
                TOKEN_IDS["TREM_DI_NUMERU"],
                TOKEN_IDS["TREM_CUM_VIRGULA"],
                TOKEN_IDS["TREM_DISCRITA"],
                TOKEN_IDS["TREM_DISCOLHE"],
                TOKEN_IDS["TROSSO"],
            }
        )

        self._io_validos = frozenset(
            {
                TOKEN_IDS["XOVE"],
                TOKEN_IDS["OIA_PROCE_VE"],
            }
        )

        self._inicio_stmt = frozenset(
            {
                TOKEN_IDS["RODA_ESSE_TREM"],
                TOKEN_IDS["ENQUANTO_TIVER_TREM"],
                TOKEN_IDS["UAI_SE"],
                TOKEN_IDS["DEPENDENU"],
                TOKEN_IDS["SIMBORA"],
                TOKEN_IDS["PARA_O_TREM"],
                TOKEN_IDS["TOCA_O_TREM"],
                TOKEN_IDS["TA_BAO"],
                TOKEN_IDS["UAI"],
                TOKEN_IDS["IDENTIFICADOR"],
                TOKEN_IDS["TREM_DI_NUMERU"],
                TOKEN_IDS["TREM_CUM_VIRGULA"],
                TOKEN_IDS["TREM_DISCRITA"],
                TOKEN_IDS["TREM_DISCOLHE"],
                TOKEN_IDS["TROSSO"],
            }
        )

        self._inicio_expr = frozenset(
            {
                TOKEN_IDS["IDENTIFICADOR"],
                TOKEN_IDS["STRING_LITERAL"],
                TOKEN_IDS["TREM_DI_NUMERU_DECIMAL"],
                TOKEN_IDS["TREM_DI_NUMERU_OCTAL"],
                TOKEN_IDS["TREM_DI_NUMERU_HEXA"],
                TOKEN_IDS["TREM_CUM_VIRGULA"],
                TOKEN_IDS["EH_TRUE"],
                TOKEN_IDS["NUM_EH_FALSE"],
                TOKEN_IDS["CHAR_LITERAL"],
                TOKEN_IDS["ABRE_PAREN"],
                TOKEN_IDS["SOMA"],
                TOKEN_IDS["SUBTRACAO"],
                TOKEN_IDS["VAM_MARCA_NOT"],
            }
        )

        self._operadores_rel = frozenset(
            {
                TOKEN_IDS["MEMA_COISA_IGUAL"],
                TOKEN_IDS["NEH_NADA_DIFERENTE"],
                TOKEN_IDS["MENOR"],
                TOKEN_IDS["MENOR_IGUAL"],
                TOKEN_IDS["MAIOR"],
                TOKEN_IDS["MAIOR_IGUAL"],
            }
        )

        self._operadores_add = frozenset(
            {
                TOKEN_IDS["SOMA"],
                TOKEN_IDS["SUBTRACAO"],
            }
        )

        self._operadores_mult = frozenset(
            {
                TOKEN_IDS["VEIZ_MULT"],
                TOKEN_IDS["SOB_DIV"],
                TOKEN_IDS["DIV_INTEIRA"],
                TOKEN_IDS["MOD"],
            }
        )

        self._literais_validos = frozenset(
            {
                TOKEN_IDS["STRING_LITERAL"],
                TOKEN_IDS["IDENTIFICADOR"],
                TOKEN_IDS["TREM_DI_NUMERU_DECIMAL"],
                TOKEN_IDS["TREM_DI_NUMERU_OCTAL"],
                TOKEN_IDS["TREM_DI_NUMERU_HEXA"],
                TOKEN_IDS["TREM_CUM_VIRGULA"],
                TOKEN_IDS["EH_TRUE"],
                TOKEN_IDS["NUM_EH_FALSE"],
                TOKEN_IDS["CHAR_LITERAL"],
            }
        )

    def obter_tipo(self, lugar):
        if not isinstance(lugar, str):
            return None
        if lugar in self.tabela_simbolos:
            return self.tabela_simbolos[lugar]
        if lugar in self.tipos_temporarios:
            return self.tipos_temporarios[lugar]
        # Literais
        if (lugar.startswith('"') and lugar.endswith('"')):
            return "s"
        if (lugar.startswith("'") and lugar.endswith("'")):
            return "c"
        if lugar in ("eh", "num_eh"):
            return "b"
        if "." in lugar:
            return "f"
        # Pode ser int
        if lugar.isdigit() or lugar.startswith("0x") or (lugar.startswith("0") and len(lugar) > 1 and lugar[1].isdigit()):
            return "a"
        return None

    def checar_tipo_binop(self, op, arg1, arg2, temp):
        t1 = self.obter_tipo(arg1)
        t2 = self.obter_tipo(arg2)
        
        if t1 is None or t2 is None:
            raise ErroSemantico(f"Erro semântico: tipo desconhecido para os operandos de '{op}'")
            
        if op in ("or", "and", "xor"):
            if t1 != "b" or t2 != "b":
                raise ErroSemantico(f"Erro semântico: operação lógica '{op}' exige operandos do tipo bool ('b'), mas encontrou '{t1}' e '{t2}'")
            self.tipos_temporarios[temp] = "b"
            
        elif op in ("add", "sub", "veiz", "sob", "/", "%"):
            if t1 not in ("a", "f") or t2 not in ("a", "f"):
                raise ErroSemantico(f"Erro semântico: operação aritmética '{op}' inválida para os tipos '{t1}' e '{t2}'")
            
            if op == "%" or op == "/":
                if t1 != "a" or t2 != "a":
                    raise ErroSemantico(f"Erro semântico: operação '{op}' exige operandos inteiros ('a'), mas encontrou '{t1}' e '{t2}'")
                self.tipos_temporarios[temp] = "a"
            elif op == "sob":
                self.tipos_temporarios[temp] = "f"
            else:
                self.tipos_temporarios[temp] = "f" if (t1 == "f" or t2 == "f") else "a"

    def checar_tipo_unop(self, op, arg, temp):
        t = self.obter_tipo(arg)
        if t is None:
            raise ErroSemantico(f"Erro semântico: tipo desconhecido para o operando de '{op}'")
            
        if op == "not":
            if t != "b":
                raise ErroSemantico(f"Erro semântico: operação lógica 'not' exige operando bool ('b'), mas encontrou '{t}'")
            self.tipos_temporarios[temp] = "b"
        elif op == "uno":
            if t not in ("a", "f"):
                raise ErroSemantico(f"Erro semântico: sinal unário exige operando numérico, mas encontrou '{t}'")
            self.tipos_temporarios[temp] = t

    def checar_tipo_relop(self, op, arg1, arg2, temp):
        t1 = self.obter_tipo(arg1)
        t2 = self.obter_tipo(arg2)
        if t1 is None or t2 is None:
            raise ErroSemantico(f"Erro semântico: tipo desconhecido para os operandos de '{op}'")
            
        if op in ("less", "gret", "leq", "geq"):
            if t1 not in ("a", "f") or t2 not in ("a", "f"):
                raise ErroSemantico(f"Erro semântico: comparação relacional '{op}' exige tipos numéricos, mas encontrou '{t1}' e '{t2}'")
        elif op in ("eq", "dif"):
            if t1 != t2:
                raise ErroSemantico(f"Erro semântico: comparação de igualdade exige tipos iguais, mas encontrou '{t1}' e '{t2}'")
                
        self.tipos_temporarios[temp] = "b"

    # =========================================================
    # Geradores de Código Intermediário
    # =========================================================
    def novo_temp(self):
        """Gera uma nova variável temporária (ex: _t1, _t2)"""
        self.cont_temp += 1
        return f"_t{self.cont_temp}"

    def novo_label(self, prefixo="L"):
        """Gera um novo rótulo de salto (ex: L1, L2)"""
        self.cont_label += 1
        if prefixo == "L":
            return f"L{self.cont_label}"
        return f"{prefixo}_{self.cont_label}"

    # =========================================================
    # Funções básicas de navegação nos tokens
    # =========================================================

    def token_atual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def id_token_atual(self):
        token = self.token_atual()
        if token is None:
            return None
        _, token_id, _, _ = token
        return token_id

    def lexema_atual(self):
        token = self.token_atual()
        if token is None:
            return "EOF"
        lexema, _, _, _ = token
        return lexema

    def linha_coluna_atual(self):
        token = self.token_atual()
        if token is None:
            return (-1, -1)
        _, _, linha, coluna = token
        return (linha, coluna)

    def avanca(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    # =========================================================
    # Consumo de tokens
    # =========================================================

    def consome_id(self, id_esperado):
        id_atual = self.id_token_atual()

        if id_atual == id_esperado:
            self.avanca()
        else:
            linha, coluna = self.linha_coluna_atual()
            lexema = self.lexema_atual()

            nome_esperado = self.id_para_nome.get(id_esperado, str(id_esperado))
            nome_atual = self.id_para_nome.get(
                id_atual, "EOF" if id_atual is None else str(id_atual)
            )

            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava {nome_esperado}, mas encontrou {nome_atual} ('{lexema}')"
            )

    def consome_lexema(self, lexema_esperado):
        lexema_atual = self.lexema_atual()

        if lexema_atual == lexema_esperado:
            self.avanca()
        else:
            linha, coluna = self.linha_coluna_atual()
            id_atual = self.id_token_atual()
            nome_atual = self.id_para_nome.get(
                id_atual, "EOF" if id_atual is None else str(id_atual)
            )

            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava lexema '{lexema_esperado}', mas encontrou "
                f"{nome_atual} ('{lexema_atual}')"
            )



    # =========================================================
    # Ponto de entrada
    # =========================================================

    def parse(self):
        codigo_gerado = self.function_main()
        if self.token_atual() is not None:
            linha, coluna = self.linha_coluna_atual()
            lexema = self.lexema_atual()
            id_atual = self.id_token_atual()
            nome_atual = self.id_para_nome.get(id_atual, str(id_atual))

            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"token inesperado após fim do programa: {nome_atual} ('{lexema}')"
            )
        return codigo_gerado

    # =========================================================
    # Regras principais
    # =========================================================

    def function_main(self):
        """
        <function*> -> 'bora_cumpade' 'main' '(' ')' <bloco>
        """
        codigo_func = []

        self.consome_id(TOKEN_IDS["BORA_CUMPADE"])
        self.consome_id(TOKEN_IDS["MAIN"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])

        codigo_bloco = self.bloco()
        codigo_func.extend(codigo_bloco)

        return codigo_func

    def bloco(self):
        """
        <bloco> -> 'simbora' <stmtList> 'cabo'
        """
        codigo_bloco = []

        self.consome_id(TOKEN_IDS["SIMBORA"])

        codigo_lista = self.stmtList()
        codigo_bloco.extend(codigo_lista)
        self.consome_id(TOKEN_IDS["CABO"])

        return codigo_bloco

    # =========================================================
    # Helpers
    # =========================================================

    def eh_tipo_atual(self):
        return self.id_token_atual() in self._tipos_validos

    def eh_io_atual(self):
        return self.id_token_atual() in self._io_validos

    def inicia_stmt(self):
        """
        Diz se o token atual pode iniciar um comando (<stmt>).
        """
        id_atual = self.id_token_atual()

        if id_atual in self._inicio_stmt:
            return True

        if self.eh_io_atual():
            return True

        return False

    def inicia_expr(self):
        """
        Diz se o token atual pode iniciar uma expressão.
        """
        id_atual = self.id_token_atual()

        return id_atual in self._inicio_expr

    def eh_identificador(self, lugar):
        if not isinstance(lugar, str) or not lugar:
            return False
        # Não pode ser temporário (começa com _t seguido de números)
        if lugar.startswith("_t") and lugar[2:].isdigit():
            return False
        # Não pode ser literal booleano
        if lugar in ("eh", "num_eh"):
            return False
        # Não pode ser literal string/char
        if (lugar.startswith('"') and lugar.endswith('"')) or (
            lugar.startswith("'") and lugar.endswith("'")
        ):
            return False
        # Não pode ser número (decimal, float, hex, octal)
        if lugar[0].isdigit() or (
            lugar.startswith(".") and len(lugar) > 1 and lugar[1].isdigit()
        ):
            return False
        # Não pode ser palavra reservada
        from lexer_mineires import LexerMineres

        if lugar in LexerMineres._KEYWORDS:
            return False
        # Deve começar com letra ou _
        if not (lugar[0].isalpha() or lugar[0] == "_"):
            return False
        return True

    # =========================================================
    # Statements
    # =========================================================

    def stmtList(self):
        """
        <stmtList> -> <stmt> <stmtList> | &
        """

        codigo_total = []
        while self.inicia_stmt():
            codigo_stmt = self.stmt()
            # Se o comando retornar código, adicionamos à nossa lista total
            if codigo_stmt is not None:
                codigo_total.extend(codigo_stmt)

        return codigo_total

    def stmt(self):
        """
        <stmt> -> <forStmt>
               | <ioStmt>
               | <whileStmt>
               | <atrib> 'uai'
               | <ifStmt>
               | <caseStmt>
               | <bloco>
               | 'para_o_trem' 'uai'
               | 'toca_o_trem' 'uai'
               | <declaration>
               | 'ta_bao' <expr> 'uai'
               | 'uai'
        """
        id_atual = self.id_token_atual()

        if id_atual == TOKEN_IDS["SIMBORA"]:
            return self.bloco()

        elif id_atual == TOKEN_IDS["UAI"]:
            self.consome_id(TOKEN_IDS["UAI"])

        elif id_atual == TOKEN_IDS["PARA_O_TREM"]:
            self.consome_id(TOKEN_IDS["PARA_O_TREM"])
            self.consome_id(TOKEN_IDS["UAI"])

        elif id_atual == TOKEN_IDS["TOCA_O_TREM"]:
            self.consome_id(TOKEN_IDS["TOCA_O_TREM"])
            self.consome_id(TOKEN_IDS["UAI"])

        elif id_atual == TOKEN_IDS["TA_BAO"]:
            self.consome_id(TOKEN_IDS["TA_BAO"])
            codigo_expr = self.expr()
            self.consome_id(TOKEN_IDS["UAI"])
            return codigo_expr

        elif self.eh_tipo_atual():
            return self.declaration()  # <-- RETORNA AS QUÁDRUPLAS DAQUI

        elif self.eh_io_atual():
            return self.ioStmt()  # <-- AGORA ELE RETORNA O CÓDIGO DO PRINT E DO SCAN

        elif id_atual == TOKEN_IDS["UAI_SE"]:
            return self.ifStmt()

        elif id_atual == TOKEN_IDS["ENQUANTO_TIVER_TREM"]:
            return self.whileStmt()

        elif id_atual == TOKEN_IDS["RODA_ESSE_TREM"]:
            return self.forStmt()

        elif id_atual == TOKEN_IDS["DEPENDENU"]:
            return self.caseStmt()

        elif id_atual == TOKEN_IDS["IDENTIFICADOR"]:
            codigo_atrib, lugar_ignorado = self.atrib()
            self.consome_id(TOKEN_IDS["UAI"])
            return codigo_atrib

        else:
            linha, coluna = self.linha_coluna_atual()
            nome_atual = self.id_para_nome.get(
                id_atual, "EOF" if id_atual is None else str(id_atual)
            )
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"token '{self.lexema_atual()}' não inicia um comando válido "
                f"({nome_atual})"
            )

    # =========================================================
    # Declarações
    # =========================================================

    def type(self):
        """
        <type> -> 'trem_di_numeru' | 'trem_cum_virgula' |
                  'trem_discrita' | 'trem_discolhe' | 'trosso'
        """
        id_atual = self.id_token_atual()

        if id_atual == TOKEN_IDS["TREM_DI_NUMERU"]:
            self.avanca()
            return "0"
        elif id_atual == TOKEN_IDS["TREM_CUM_VIRGULA"]:
            self.avanca()
            return "0.0"
        elif id_atual == TOKEN_IDS["TREM_DISCRITA"]:
            self.avanca()
            return '""'  # Aspas duplas vazias para string
        elif id_atual == TOKEN_IDS["TREM_DISCOLHE"]:
            self.avanca()
            return "num_eh"  # Falso por padrão
        elif id_atual == TOKEN_IDS["TROSSO"]:
            self.avanca()
            return "''"  # Aspas simples vazias para char
        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava um tipo, mas encontrou '{self.lexema_atual()}'"
            )

    def identList(self, valor_padrao, tipo_simbolo):
        """
        <identList> -> IDENT <restoIdentList>
        Recebe: O valor padrão definido pelo tipo.
        Retorna: A lista de quádruplas já pronta.
        """
        nome_variavel = self.lexema_atual()  # Pega o nome (ex: "k")
        self.consome_id(TOKEN_IDS["IDENTIFICADOR"])

        if nome_variavel in self.tabela_simbolos:
            raise ErroSemantico(f"Erro semântico: re-declaração da variável '{nome_variavel}'")
        self.tabela_simbolos[nome_variavel] = tipo_simbolo

        # Monta a quádrupla dessa variável
        quadrupla_atual = [("att", nome_variavel, valor_padrao, "none")]

        # Pega as quádruplas do resto da lista (se houver mais variáveis depois da vírgula)
        quadruplas_resto = self.restoIdentList(valor_padrao, tipo_simbolo)

        # Junta a quádrupla atual com as que vieram do resto e devolve
        return quadrupla_atual + quadruplas_resto

    def restoIdentList(self, valor_padrao, tipo_simbolo):
        """
        <restoIdentList> -> ',' IDENT <restoIdentList> | &
        Recebe: O valor padrão definido pelo tipo.
        Retorna: Lista de quádruplas ou lista vazia [] se for 'vazio' (&).
        """
        quadruplas = []

        # Se entrar no while, é porque achou uma vírgula
        while self.id_token_atual() == TOKEN_IDS["VIRGULA"]:
            self.consome_id(TOKEN_IDS["VIRGULA"])

            nome_variavel = self.lexema_atual()  # Pega o nome depois da vírgula
            self.consome_id(TOKEN_IDS["IDENTIFICADOR"])

            if nome_variavel in self.tabela_simbolos:
                raise ErroSemantico(f"Erro semântico: re-declaração da variável '{nome_variavel}'")
            self.tabela_simbolos[nome_variavel] = tipo_simbolo

            # Adiciona a quádrupla na lista
            quadruplas.append(("att", nome_variavel, valor_padrao, "none"))

        # Retorna a lista. Se não entrou no while (leu o vazio), retorna [] naturalmente
        return quadruplas

    def declaration(self):
        """
        <declaration> -> <type> <identList> 'uai'
        """
        id_tipo = self.id_token_atual()
        tipo_simbolo = self._tipo_keyword_para_simbolo.get(id_tipo)

        # 1. Pega o valor padrão baseado no tipo
        valor_padrao = self.type()

        # 2. Pede pro identList gerar as quádruplas passando o valor padrão
        codigo = self.identList(valor_padrao, tipo_simbolo)

        self.consome_id(TOKEN_IDS["UAI"])

        # 3. Retorna o código para o bloco/stmtList
        return codigo

    # =========================================================
    # Entrada e saída
    # =========================================================

    def ioStmt(self):
        """
        <ioStmt> -> 'xove' '(' <type> ',' 'IDENT' ')' 'uai'
                  | 'oia_proce_ve' '(' <outList> ')' 'uai'
        """
        lex = self.lexema_atual()

        if self.id_token_atual() == TOKEN_IDS["XOVE"]:
            self.consome_id(TOKEN_IDS["XOVE"])
            self.consome_id(TOKEN_IDS["ABRE_PAREN"])
            self.type()
            self.consome_id(TOKEN_IDS["VIRGULA"])

            nome_variavel = (
                self.lexema_atual()
            )  # Pega a variável que vai receber o valor
            if nome_variavel not in self.tabela_simbolos:
                raise ErroSemantico(f"Erro semântico: variável '{nome_variavel}' não declarada")

            self.consome_id(TOKEN_IDS["IDENTIFICADOR"])
            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
            self.consome_id(TOKEN_IDS["UAI"])

            # Quádrupla de leitura
            return [("call", "read", nome_variavel, "none")]

        elif self.id_token_atual() == TOKEN_IDS["OIA_PROCE_VE"]:
            self.consome_id(TOKEN_IDS["OIA_PROCE_VE"])
            self.consome_id(TOKEN_IDS["ABRE_PAREN"])

            # Pega todas as quádruplas geradas pela lista
            codigo_prints = self.outList()

            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
            self.consome_id(TOKEN_IDS["UAI"])

            return codigo_prints

        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava comando de IO, mas encontrou '{lex}'"
            )

    def outList(self):
        """
        <outList> -> <out> <restoOutList>
        """
        # Pega o primeiro print
        codigo_out = self.out()

        # Pega os prints depois das vírgulas (se houver)
        codigo_resto = self.restoOutList()

        # Junta e sobe tudo
        return codigo_out + codigo_resto

    def out(self):
        """
        <out> -> <fatorZin>
        Retorna: O código gerado para imprimir esse fator.
        """
        # Recebemos as 3 informações
        codigo_fator, valor, eh_variavel = self.fatorZin()

        # Monta a quádrupla exatamente como o professor pediu
        if eh_variavel:
            quad_print = ("call", "print", valor, "none")
        else:
            quad_print = ("call", "print", "none", valor)

        # O código total será o código do fator (se houver) + o print
        codigo_fator.append(quad_print)

        return codigo_fator

    def restoOutList(self):
        """
        <restoOutList> -> ',' <out> <restoOutList> | &
        """
        codigo_total = []
        while self.id_token_atual() == TOKEN_IDS["VIRGULA"]:
            self.consome_id(TOKEN_IDS["VIRGULA"])

            # Pega o código do print do próximo argumento
            codigo_out = self.out()
            codigo_total.extend(codigo_out)

        return codigo_total

    # =========================================================
    # Controle: if / while / for
    # =========================================================

    def ifStmt(self):
        """
        <ifStmt> -> 'uai_se' '(' <expr> ')' <stmt> <elsePart>
        """
        self.consome_id(TOKEN_IDS["UAI_SE"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])

        codigo_if = []

        # 1. Resolve a condição do IF
        codigo_expr, lugar_expr = self.expr()
        codigo_if.extend(codigo_expr)

        tipo_cond = self.obter_tipo(lugar_expr)
        if tipo_cond != "b":
            raise ErroSemantico(
                f"Erro semântico na linha {self.linha_coluna_atual()[0]}: "
                f"a condição do 'uai_se' deve ser do tipo bool ('b'), mas encontrou '{tipo_cond}'"
            )

        # Criamos as placas
        l_falso_if = self.novo_label("l_falso_if")
        l_inicio_if = self.novo_label("l_inicio_if")
        l_outif = self.novo_label("l_outif")

        # 2. Se for mentira (iffalse), pula pro bloco falso
        codigo_if.append(("if", lugar_expr, l_inicio_if, l_falso_if))

        self.consome_id(TOKEN_IDS["FECHA_PAREN"])

        codigo_if.append(("label", l_inicio_if, "none", "none"))

        # 3. Código do bloco VERDADEIRO
        codigo_stmt_verdadeiro = self.stmt()
        if codigo_stmt_verdadeiro:
            codigo_if.extend(codigo_stmt_verdadeiro)

        codigo_if.append(("jump", l_outif, "none", "none"))

        # 4. Pega o código do bloco FALSO (uai_senao) se ele existir
        codigo_else = self.elsePart()

        codigo_if.append(("label", l_falso_if, "none", "none"))

        # 5. Monta o quebra-cabeça
        if codigo_else:  # Se o cara programou um ELSE
            codigo_if.extend(codigo_else)

        codigo_if.append(("label", l_outif, "none", "none"))

        return codigo_if

    def elsePart(self):
        """
        <elsePart> -> 'uai_senao' <stmt> | &
        """

        if self.id_token_atual() == TOKEN_IDS["UAI_SENAO"]:
            self.avanca()
            codigo_stmt = self.stmt()
            return codigo_stmt if codigo_stmt else []
        else:
            return []

    def whileStmt(self):
        """
        <whileStmt> -> 'enquanto_tiver_trem' '(' <expr> ')' <stmt>
        """
        self.consome_id(TOKEN_IDS["ENQUANTO_TIVER_TREM"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])

        # 1. Cria as placas de sinalização usando o gerador que fizemos antes
        l_inicio_while = self.novo_label("l_inicio_while")
        l_fim_while = self.novo_label("l_fim_while")
        l_dentro_while = self.novo_label("l_dentro_while")

        # 2. Marca o começo do laço
        codigo_while = [("label", l_inicio_while, "none", "none")]

        # 3. Lê a condição matemática/lógica
        codigo_expr, lugar_expr = self.expr()
        codigo_while.extend(codigo_expr)

        tipo_cond = self.obter_tipo(lugar_expr)
        if tipo_cond != "b":
            raise ErroSemantico(
                f"Erro semântico na linha {self.linha_coluna_atual()[0]}: "
                f"a condição do 'enquanto_tiver_trem' deve ser do tipo bool ('b'), mas encontrou '{tipo_cond}'"
            )

        # 4. Se a condição for falsa, pula lá pro final do laço (foge do while)
        codigo_while.append(("if", lugar_expr, l_dentro_while, l_fim_while))

        self.consome_id(TOKEN_IDS["FECHA_PAREN"])

        # 5. Coloca a placa de "Dentro do While" aqui
        codigo_while.append(("label", l_dentro_while, "none", "none"))

        # 6. Lê o que tá dentro do laço (o corpo do while)
        codigo_stmt = self.stmt()
        if codigo_stmt:
            codigo_while.extend(codigo_stmt)

        # 7. Acabou o corpo? Volta lá pro topo pra testar de novo!
        codigo_while.append(("jump", l_inicio_while, "none", "none"))

        # 8. Coloca a placa de "Fim" aqui embaixo para quem fugiu do laço saber onde cair
        codigo_while.append(("label", l_fim_while, "none", "none"))

        return codigo_while

    def optExpr(self):
        """
        <optExpr> -> <atrib> | &
        """
        if self.inicia_expr():
            return self.atrib()
        # Se for vazio, não gera código nenhum e não tem variável
        return [], "none"

    def forStmt(self):
        """
        <forStmt> -> 'roda_esse_trem' '(' <optExpr> ';' <optExpr> ';' <optExpr> ')' <stmt>
        """
        self.consome_id(TOKEN_IDS["RODA_ESSE_TREM"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])

        codigo_for = []

        # 1. Lê a INICIALIZAÇÃO
        codigo_init, lugar_init = self.optExpr()
        codigo_for.extend(codigo_init)

        self.consome_id(TOKEN_IDS["PONTO_VIRGULA"])

        # Cria as placas do laço
        l_inicio_for = self.novo_label("l_inicio_for")
        l_fim_for = self.novo_label("l_fim_for")
        l_vdd_for = self.novo_label("l_vdd_for")
        l_soma_for = self.novo_label("l_soma_for")

        # Placa do topo do FOR
        codigo_for.append(("label", l_inicio_for, "none", "none"))

        # 2. Lê a CONDIÇÃO (Ex: i < 10)
        codigo_cond, lugar_cond = self.optExpr()
        codigo_for.extend(codigo_cond)

        if lugar_cond != "none":
            tipo_cond = self.obter_tipo(lugar_cond)
            if tipo_cond != "b":
                raise ErroSemantico(
                    f"Erro semântico na linha {self.linha_coluna_atual()[0]}: "
                    f"a condição do 'roda_esse_trem' deve ser do tipo bool ('b'), mas encontrou '{tipo_cond}'"
                )

        codigo_for.append(("if", lugar_cond, l_vdd_for, l_fim_for))

        self.consome_id(TOKEN_IDS["PONTO_VIRGULA"])

        # 3. Lê o INCREMENTO (Ex: i fica_assim_entao i + 1)
        # ATENÇÃO: Nós lemos, mas NÃO colocamos no código_for ainda!
        codigo_inc, lugar_inc = self.optExpr()

        self.consome_id(TOKEN_IDS["FECHA_PAREN"])

        codigo_for.append(("label", l_vdd_for, "none", "none"))

        # 4. Lê o CORPO DO LAÇO (o <stmt> ou o <bloco>)
        codigo_stmt = self.stmt()
        if codigo_stmt:
            codigo_for.extend(codigo_stmt)

        # Coloca a placa de soma aqui
        codigo_for.append(("label", l_soma_for, "none", "none"))

        # 5. AGORA SIM adicionamos o incremento no final do corpo
        codigo_for.extend(codigo_inc)

        # 6. Volta pro início do laço
        codigo_for.append(("jump", l_inicio_for, "none", l_inicio_for))

        # 7. Placa de saída do laço
        codigo_for.append(("label", l_fim_for, "none", "none"))

        return codigo_for

    # =========================================================
    # Case / switch
    # =========================================================

    def caseStmt(self):
        """
        <caseStmt> -> 'dependenu' '(' 'IDENT' ')' 'simbora' <dosCasos> 'cabo'
        """
        self.consome_id(TOKEN_IDS["DEPENDENU"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        switch_var = self.lexema_atual()
        if switch_var not in self.tabela_simbolos:
            raise ErroSemantico(f"Erro semântico: variável '{switch_var}' não declarada")
        self.consome_id(TOKEN_IDS["IDENTIFICADOR"])
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        self.consome_id(TOKEN_IDS["SIMBORA"])

        l_fim_switch = self.novo_label("l_fim_switch")
        codigo_casos = self.dosCasos(switch_var, l_fim_switch)

        self.consome_id(TOKEN_IDS["CABO"])
        return codigo_casos + [("label", l_fim_switch, "none", "none")]

    def dosCasos(self, switch_var, l_fim_switch):
        """
        <dosCasos> -> <doCaso> <restoDosCasos>
        """
        codigo_caso = self.doCaso(switch_var, l_fim_switch)
        codigo_resto = self.restoDosCasos(switch_var, l_fim_switch)
        return codigo_caso + codigo_resto

    def doCaso(self, switch_var, l_fim_switch):
        """
        <doCaso> -> 'du_casu' <fatorZinMenorAinda> ':' <stmt>
        """
        self.consome_id(TOKEN_IDS["DU_CASU"])
        literal_val = self.fatorZinMenorAinda()
        self.consome_lexema(":")

        l_vdd_case = self.novo_label("l_vdd_case")
        l_next_case = self.novo_label("l_next_case")

        temp = self.novo_temp()
        codigo = [
            ("eq", temp, switch_var, literal_val),
            ("if", temp, l_vdd_case, l_next_case),
            ("label", l_vdd_case, "none", "none"),
        ]

        codigo_stmt = self.stmt()
        if codigo_stmt:
            codigo.extend(codigo_stmt)

        codigo.extend(
            [
                ("jump", l_fim_switch, "none", "none"),
                ("label", l_next_case, "none", "none"),
            ]
        )
        return codigo

    def restoDosCasos(self, switch_var, l_fim_switch):
        """
        <restoDosCasos> -> <doCaso> <restoDosCasos> | 'default' ':' <stmt> | &
        """
        codigo_total = []
        while self.id_token_atual() == TOKEN_IDS["DU_CASU"]:
            codigo_total.extend(self.doCaso(switch_var, l_fim_switch))

        if self.lexema_atual() == "default":
            self.consome_lexema("default")
            self.consome_lexema(":")
            codigo_stmt = self.stmt()
            if codigo_stmt:
                codigo_total.extend(codigo_stmt)

        return codigo_total

    # =========================================================
    # Expressões
    # =========================================================

    def expr(self):
        """
        <expr> -> <atrib>
        """
        return self.atrib()

    def atrib(self):
        """
        <atrib> -> <or> <restoAtrib>
        """
        codigo_esq, lugar_esq = self.orExpr()
        codigo_resto, lugar_final = self.restoAtrib(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoAtrib(self, lugar_esq):
        if self.id_token_atual() == TOKEN_IDS["FICA_ASSIM_ENTAO"]:
            if not self.eh_identificador(lugar_esq):
                linha, coluna = self.linha_coluna_atual()
                raise ErroSintatico(
                    f"Erro sintático na linha {linha}, coluna {coluna}: "
                    f"o lado esquerdo de uma atribuição deve ser um identificador, "
                    f"mas encontrou '{lugar_esq}'"
                )
            if lugar_esq not in self.tabela_simbolos:
                raise ErroSemantico(f"Erro semântico: variável '{lugar_esq}' não declarada")

            self.consome_id(TOKEN_IDS["FICA_ASSIM_ENTAO"])

            codigo_dir, lugar_dir = self.atrib()

            tipo_esq = self.obter_tipo(lugar_esq)
            tipo_dir = self.obter_tipo(lugar_dir)
            if tipo_esq != tipo_dir:
                raise ErroSemantico(
                    f"Erro semântico: tipos incompatíveis na atribuição. "
                    f"Tentando atribuir tipo '{tipo_dir}' para a variável '{lugar_esq}' de tipo '{tipo_esq}'"
                )

            # Quádrupla de atribuição: (att, valor_calculado, none, variavel_destino)
            quad = ("att", lugar_esq, lugar_dir, "none")
            codigo_dir.append(quad)

            return codigo_dir, lugar_esq

        return [], lugar_esq

    def orExpr(self):
        """
        <or> -> <xor> <restoOr>
        """
        codigo_esq, lugar_esq = self.xorExpr()
        codigo_resto, lugar_final = self.restoOr(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoOr(self, lugar_esq):
        codigo_total = []
        lugar_atual = lugar_esq

        while self.id_token_atual() == TOKEN_IDS["QUARQUE_UM_OR"]:
            self.avanca()

            codigo_dir, lugar_dir = self.xorExpr()

            temp = self.novo_temp()
            self.checar_tipo_binop("or", lugar_atual, lugar_dir, temp)
            quad = ("or", temp, lugar_atual, lugar_dir)

            codigo_total.extend(codigo_dir)
            codigo_total.append(quad)
            lugar_atual = temp

        return codigo_total, lugar_atual

    def xorExpr(self):
        """
        <xor> -> <and> <restoXor>
        """
        codigo_esq, lugar_esq = self.andExpr()
        codigo_resto, lugar_final = self.restoXor(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoXor(self, lugar_esq):
        codigo_total = []
        lugar_atual = lugar_esq

        while self.id_token_atual() == TOKEN_IDS["UM_O_OTO_XOR"]:
            self.avanca()

            codigo_dir, lugar_dir = self.andExpr()

            temp = self.novo_temp()
            self.checar_tipo_binop("xor", lugar_atual, lugar_dir, temp)
            quad = ("xor", temp, lugar_atual, lugar_dir)

            codigo_total.extend(codigo_dir)
            codigo_total.append(quad)
            lugar_atual = temp

        return codigo_total, lugar_atual

    def andExpr(self):
        """
        <and> -> <not> <restoAnd>
        """
        codigo_esq, lugar_esq = self.notExpr()
        codigo_resto, lugar_final = self.restoAnd(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoAnd(self, lugar_esq):
        codigo_total = []
        lugar_atual = lugar_esq

        while self.id_token_atual() == TOKEN_IDS["TAMEM_AND"]:
            self.avanca()

            codigo_dir, lugar_dir = self.notExpr()

            temp = self.novo_temp()
            self.checar_tipo_binop("and", lugar_atual, lugar_dir, temp)
            quad = ("and", temp, lugar_atual, lugar_dir)

            codigo_total.extend(codigo_dir)
            codigo_total.append(quad)
            lugar_atual = temp

        return codigo_total, lugar_atual

    def notExpr(self):
        """
        <not> -> 'vam_marca' <not> | <rel>
        """
        if self.id_token_atual() == TOKEN_IDS["VAM_MARCA_NOT"]:
            self.avanca()

            codigo_dir, lugar_dir = self.notExpr()

            temp = self.novo_temp()
            self.checar_tipo_unop("not", lugar_dir, temp)

            quad = ("not", temp, lugar_dir, "none")

            codigo_dir.append(quad)
            return codigo_dir, temp
        else:
            return self.rel()

    def rel(self):
        """
        <rel> -> <add> <restoRel>
        """
        codigo_esq, lugar_esq = self.add()
        codigo_resto, lugar_final = self.restoRel(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoRel(self, lugar_esq):
        """
        <restoRel> -> OPERADOR_RELACIONAL <add> | &
        """
        if self.id_token_atual() in self._operadores_rel:
            op = self.lexema_atual()
            self.avanca()

            codigo_dir, lugar_dir = self.add()

            temp = self.novo_temp()

            if op == "<":
                op = "less"
            elif op == ">":
                op = "gret"
            elif op == "<=" or op == "MENOR_QUE_IGUAL":
                op = "leq"
            elif op == ">=" or op == "MAIOR_QUE_IGUAL":
                op = "geq"
            elif op == "mema_coisa":
                op = "eq"
            elif op == "quase_la":
                op = "dif"

            self.checar_tipo_relop(op, lugar_esq, lugar_dir, temp)
            quad = (op, temp, lugar_esq, lugar_dir)

            codigo_total = codigo_dir
            codigo_total.append(quad)

            return codigo_total, temp

        return [], lugar_esq

    def add(self):
        """
        <add> -> <mult> <restoAdd>
        """
        codigo_esq, lugar_esq = self.mult()
        codigo_resto, lugar_final = self.restoAdd(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoAdd(self, lugar_esq):
        codigo_total = []
        lugar_atual = lugar_esq

        while self.id_token_atual() in self._operadores_add:
            op = self.lexema_atual()  # Pega se é '+' ou '-'
            self.avanca()

            codigo_dir, lugar_dir = self.mult()

            temp = self.novo_temp()  # Cria o _t2
            if op == "+":
                op = "add"
            elif op == "-":
                op = "sub"
            self.checar_tipo_binop(op, lugar_atual, lugar_dir, temp)
            quad = (op, temp, lugar_atual, lugar_dir)

            codigo_total.extend(codigo_dir)
            codigo_total.append(quad)

            lugar_atual = temp

        return codigo_total, lugar_atual

    def mult(self):
        """
        <mult> -> <uno> <restoMult>
        """
        codigo_esq, lugar_esq = self.uno()
        codigo_resto, lugar_final = self.restoMult(lugar_esq)
        return codigo_esq + codigo_resto, lugar_final

    def restoMult(self, lugar_esq):
        codigo_total = []
        lugar_atual = lugar_esq

        while self.id_token_atual() in self._operadores_mult:
            op = self.lexema_atual()  # Pega se é 'veiz', 'sob', etc
            self.avanca()

            codigo_dir, lugar_dir = self.uno()

            temp = self.novo_temp()  # Cria o _t1
            self.checar_tipo_binop(op, lugar_atual, lugar_dir, temp)
            quad = (op, temp, lugar_atual, lugar_dir)

            codigo_total.extend(codigo_dir)
            codigo_total.append(quad)

            # O novo lado esquerdo das próximas contas passa a ser o _t1
            lugar_atual = temp

        return codigo_total, lugar_atual

    def uno(self):
        """
        <uno> -> '+' <uno> | '-' <uno> | <fatorZao>
        """
        id_atual = self.id_token_atual()

        if id_atual == TOKEN_IDS["SOMA"]:
            self.consome_id(TOKEN_IDS["SOMA"])
            codigo, lugar = self.uno()
            temp = self.novo_temp()
            self.checar_tipo_unop("uno", lugar, temp)

            quad = ("uno", "+", temp, lugar)
            codigo.append(quad)
            return codigo, temp

        elif id_atual == TOKEN_IDS["SUBTRACAO"]:
            self.consome_id(TOKEN_IDS["SUBTRACAO"])
            codigo, lugar = self.uno()

            temp = self.novo_temp()
            self.checar_tipo_unop("uno", lugar, temp)

            quad = ("uno", "-", temp, lugar)
            codigo.append(quad)
            return codigo, temp
        else:
            return self.fatorZao()

    def fatorZao(self):
        """
        <fatorZao> -> <fatorZin> | '(' <atrib> ')'
        """
        if self.id_token_atual() == TOKEN_IDS["ABRE_PAREN"]:
            self.consome_id(TOKEN_IDS["ABRE_PAREN"])

            # Resolve tudo que está dentro do parênteses
            codigo, lugar = self.atrib()

            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
            return codigo, lugar
        else:
            codigo, lugar, eh_var = self.fatorZin()
            return codigo, lugar

    def fatorZin(self):
        """
        <fatorZin> -> STR | IDENT | NUMint | NUMfloat | valorBooleano | valorChar
        Retorna: (codigo_gerado, valor_lido, eh_variavel)
        """
        id_atual = self.id_token_atual()
        lexema = self.lexema_atual()

        # Descobrimos se é uma variável ANTES de avançar
        eh_variavel = id_atual == TOKEN_IDS["IDENTIFICADOR"]

        if id_atual in self._literais_validos:
            self.avanca()
            if eh_variavel:
                if lexema not in self.tabela_simbolos:
                    raise ErroSemantico(f"Erro semântico: variável '{lexema}' não declarada")
            else:
                # Conversão de valores: hex/octal para decimal
                if id_atual == TOKEN_IDS["TREM_DI_NUMERU_HEXA"]:
                    lexema = str(int(lexema, 16))
                elif id_atual == TOKEN_IDS["TREM_DI_NUMERU_OCTAL"]:
                    lexema = str(int(lexema, 8))
            # Retorna o código vazio, o lexema e se é variável (True) ou literal (False)
            return ([], lexema, eh_variavel)

        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava literal, identificador ou expressão entre parênteses, "
                f"mas encontrou '{self.lexema_atual()}'"
            )

    def fatorZinMenorAinda(self):
        """
        <fatorZinMenorAinda> -> STR | NUMint | NUMfloat | valorBooleano | valorChar
        """
        id_atual = self.id_token_atual()
        lexema = self.lexema_atual()
        if (
            id_atual in self._literais_validos
            and id_atual != TOKEN_IDS["IDENTIFICADOR"]
        ):
            self.avanca()
            # Conversão de valores: hex/octal para decimal
            if id_atual == TOKEN_IDS["TREM_DI_NUMERU_HEXA"]:
                lexema = str(int(lexema, 16))
            elif id_atual == TOKEN_IDS["TREM_DI_NUMERU_OCTAL"]:
                lexema = str(int(lexema, 8))
            return lexema
        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava literal (número, string, char ou booleano), "
                f"mas encontrou '{self.lexema_atual()}'"
            )
