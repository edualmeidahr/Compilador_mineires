from __future__ import annotations

from lexer_mineires import TOKEN_IDS


class ErroSintatico(Exception):
    """Exceção usada para indicar erro sintático."""
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.id_para_nome = {valor: chave for chave, valor in TOKEN_IDS.items()}
        
        # Otimização: Instanciar os conjuntos de verificação (hashes) no construtor
        # Assim evitamos a recriação a cada chamada de função
        self._tipos_validos = frozenset({
            TOKEN_IDS["TREM_DI_NUMERU"],
            TOKEN_IDS["TREM_CUM_VIRGULA"],
            TOKEN_IDS["TREM_DISCRITA"],
            TOKEN_IDS["TREM_DISCOLHE"],
            TOKEN_IDS["TROSSO"],
        })
        
        self._io_validos = frozenset({
            TOKEN_IDS["XOVE"],
            TOKEN_IDS["OIA_PROCE_VE"],
        })
        
        self._inicio_stmt = frozenset({
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
        })
        
        self._inicio_expr = frozenset({
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
        })

        self._operadores_rel = frozenset({
            TOKEN_IDS["MEMA_COISA_IGUAL"],
            TOKEN_IDS["NEH_NADA_DIFERENTE"],
            TOKEN_IDS["MENOR"],
            TOKEN_IDS["MENOR_IGUAL"],
            TOKEN_IDS["MAIOR"],
            TOKEN_IDS["MAIOR_IGUAL"],
        })

        self._operadores_add = frozenset({
            TOKEN_IDS["SOMA"],
            TOKEN_IDS["SUBTRACAO"],
        })

        self._operadores_mult = frozenset({
            TOKEN_IDS["VEIZ_MULT"],
            TOKEN_IDS["SOB_DIV"],
            TOKEN_IDS["DIV_INTEIRA"],
            TOKEN_IDS["MOD"],
        })

        self._literais_validos = frozenset({
            TOKEN_IDS["STRING_LITERAL"],
            TOKEN_IDS["IDENTIFICADOR"],
            TOKEN_IDS["TREM_DI_NUMERU_DECIMAL"],
            TOKEN_IDS["TREM_DI_NUMERU_OCTAL"],
            TOKEN_IDS["TREM_DI_NUMERU_HEXA"],
            TOKEN_IDS["TREM_CUM_VIRGULA"],
            TOKEN_IDS["EH_TRUE"],
            TOKEN_IDS["NUM_EH_FALSE"],
            TOKEN_IDS["CHAR_LITERAL"],
        })

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

    def consome_um_dos_lexemas(self, *lexemas_esperados):
        atual = self.lexema_atual()
        if atual in lexemas_esperados:
            self.avanca()
        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava um destes lexemas {lexemas_esperados}, "
                f"mas encontrou '{atual}'"
            )

    # =========================================================
    # Ponto de entrada
    # =========================================================

    def parse(self):
        self.function_main()

        if self.token_atual() is not None:
            linha, coluna = self.linha_coluna_atual()
            lexema = self.lexema_atual()
            id_atual = self.id_token_atual()
            nome_atual = self.id_para_nome.get(id_atual, str(id_atual))

            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"token inesperado após fim do programa: {nome_atual} ('{lexema}')"
            )

    # =========================================================
    # Regras principais
    # =========================================================

    def function_main(self):
        """
        <function*> -> 'bora_cumpade' 'main' '(' ')' <bloco>
        """
        self.consome_id(TOKEN_IDS["BORA_CUMPADE"])
        self.consome_id(TOKEN_IDS["MAIN"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        self.bloco()

    def bloco(self):
        """
        <bloco> -> 'simbora' <stmtList> 'cabo'
        """
        self.consome_id(TOKEN_IDS["SIMBORA"])
        self.stmtList()
        self.consome_id(TOKEN_IDS["CABO"])

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

    # =========================================================
    # Statements
    # =========================================================

    def stmtList(self):
        """
        <stmtList> -> <stmt> <stmtList> | &
        """
        while self.inicia_stmt():
            self.stmt()

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
            self.bloco()

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
            self.expr()
            self.consome_id(TOKEN_IDS["UAI"])

        elif self.eh_tipo_atual():
            self.declaration()

        elif self.eh_io_atual():
            self.ioStmt()

        elif id_atual == TOKEN_IDS["UAI_SE"]:
            self.ifStmt()

        elif id_atual == TOKEN_IDS["ENQUANTO_TIVER_TREM"]:
            self.whileStmt()

        elif id_atual == TOKEN_IDS["RODA_ESSE_TREM"]:
            self.forStmt()

        elif id_atual == TOKEN_IDS["DEPENDENU"]:
            self.caseStmt()

        elif id_atual == TOKEN_IDS["IDENTIFICADOR"]:
            self.atrib()
            self.consome_id(TOKEN_IDS["UAI"])

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
        if self.eh_tipo_atual():
            self.avanca()
        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava um tipo, mas encontrou '{self.lexema_atual()}'"
            )

    def identList(self):
        """
        <identList> -> IDENT <restoIdentList>
        """
        self.consome_id(TOKEN_IDS["IDENTIFICADOR"])
        self.restoIdentList()

    def restoIdentList(self):
        """
        <restoIdentList> -> ',' IDENT <restoIdentList> | &
        """
        while self.id_token_atual() == TOKEN_IDS["VIRGULA"]:
            self.consome_id(TOKEN_IDS["VIRGULA"])
            self.consome_id(TOKEN_IDS["IDENTIFICADOR"])

    def declaration(self):
        """
        <declaration> -> <type> <identList> 'uai'
        """
        self.type()
        self.identList()
        self.consome_id(TOKEN_IDS["UAI"])

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
            self.consome_id(TOKEN_IDS["IDENTIFICADOR"])
            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
            self.consome_id(TOKEN_IDS["UAI"])

        elif self.id_token_atual() == TOKEN_IDS["OIA_PROCE_VE"]:
            self.consome_id(TOKEN_IDS["OIA_PROCE_VE"])
            self.consome_id(TOKEN_IDS["ABRE_PAREN"])
            self.outList()
            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
            self.consome_id(TOKEN_IDS["UAI"])

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
        self.out()
        self.restoOutList()

    def out(self):
        """
        <out> -> <fatorZin>
        """
        self.fatorZin()

    def restoOutList(self):
        """
        <restoOutList> -> ',' <out> <restoOutList> | &
        """
        while self.id_token_atual() == TOKEN_IDS["VIRGULA"]:
            self.consome_id(TOKEN_IDS["VIRGULA"])
            self.out()

    # =========================================================
    # Controle: if / while / for
    # =========================================================

    def ifStmt(self):
        """
        <ifStmt> -> 'uai_se' '(' <expr> ')' <stmt> <elsePart>
        """
        self.consome_id(TOKEN_IDS["UAI_SE"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        self.expr()
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        self.stmt()
        self.elsePart()

    def elsePart(self):
        """
        <elsePart> -> 'uai_senao' <stmt> | &
        """
        id_atual = self.id_token_atual()
        lex = self.lexema_atual()

        if self.id_token_atual() == TOKEN_IDS["UAI_SENAO"]:
            self.avanca()
            self.stmt()

    def whileStmt(self):
        """
        <whileStmt> -> 'enquanto_tiver_trem' '(' <expr> ')' <stmt>
        """
        self.consome_id(TOKEN_IDS["ENQUANTO_TIVER_TREM"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        self.expr()
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        self.stmt()

    def optExpr(self):
        """
        <optExpr> -> <atrib> | &
        """
        if self.inicia_expr():
            self.atrib()

    def forStmt(self):
        """
        <forStmt> -> 'roda_esse_trem' '(' <optExpr> ';' <optExpr> ';' <optExpr> ')' <stmt>
        """
        self.consome_id(TOKEN_IDS["RODA_ESSE_TREM"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])

        self.optExpr()
        self.consome_id(TOKEN_IDS["PONTO_VIRGULA"])

        self.optExpr()
        self.consome_id(TOKEN_IDS["PONTO_VIRGULA"])

        self.optExpr()
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])

        self.stmt()

    # =========================================================
    # Case / switch
    # =========================================================

    def caseStmt(self):
        """
        <caseStmt> -> 'dependenu' '(' 'IDENT' ')' 'simbora' <dosCasos> 'cabo'
        """
        self.consome_id(TOKEN_IDS["DEPENDENU"])
        self.consome_id(TOKEN_IDS["ABRE_PAREN"])
        self.consome_id(TOKEN_IDS["IDENTIFICADOR"])
        self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        self.consome_id(TOKEN_IDS["SIMBORA"])
        self.dosCasos()
        self.consome_id(TOKEN_IDS["CABO"])

    def dosCasos(self):
        """
        <dosCasos> -> <doCaso> <restoDosCasos>
        """
        self.doCaso()
        self.restoDosCasos()

    def doCaso(self):
        """
        <doCaso> -> 'du_casu' <fatorZin> ':' <stmt>
        """
        self.consome_id(TOKEN_IDS["DU_CASU"])
        self.fatorZin()
        self.consome_lexema(":")
        self.stmt()

    def restoDosCasos(self):
        """
        <restoDosCasos> -> <doCaso><restoDosCasos> | 'default' ':' <stmt> | &
        """
        while self.id_token_atual() == TOKEN_IDS["DU_CASU"]:
            self.doCaso()

        if self.lexema_atual() == "default":
            self.consome_lexema("default")
            self.consome_lexema(":")
            self.stmt()

    # =========================================================
    # Expressões
    # =========================================================

    def expr(self):
        """
        <expr> -> <atrib>
        """
        self.atrib()

    def atrib(self):
        """
        <atrib> -> <or> <restoAtrib>
        """
        self.orExpr()
        self.restoAtrib()

    def restoAtrib(self):
        """
        <restoAtrib> -> 'fica_assim_entao' <atrib> | &
        """
        if self.id_token_atual() == TOKEN_IDS["FICA_ASSIM_ENTAO"]:
            self.consome_id(TOKEN_IDS["FICA_ASSIM_ENTAO"])
            self.atrib()

    def orExpr(self):
        """
        <or> -> <xor> <restoOr>
        """
        self.xorExpr()
        self.restoOr()

    def restoOr(self):
        while self.id_token_atual() == TOKEN_IDS["QUARQUE_UM_OR"]:
            self.consome_id(TOKEN_IDS["QUARQUE_UM_OR"])
            self.xorExpr()

    def xorExpr(self):
        """
        <xor> -> <and> <restoXor>
        """
        self.andExpr()
        self.restoXor()

    def restoXor(self):
        while self.id_token_atual() == TOKEN_IDS["UM_O_OTO_XOR"]:
            self.consome_id(TOKEN_IDS["UM_O_OTO_XOR"])
            self.andExpr()

    def andExpr(self):
        """
        <and> -> <not> <restoAnd>
        """
        self.notExpr()
        self.restoAnd()

    def restoAnd(self):
        while self.id_token_atual() == TOKEN_IDS["TAMEM_AND"]:
            self.consome_id(TOKEN_IDS["TAMEM_AND"])
            self.notExpr()

    def notExpr(self):
        """
        <not> -> 'vam_marca' <not> | <rel>
        """
        if self.id_token_atual() == TOKEN_IDS["VAM_MARCA_NOT"]:
            self.consome_id(TOKEN_IDS["VAM_MARCA_NOT"])
            self.notExpr()
        else:
            self.rel()

    def rel(self):
        """
        <rel> -> <add> <restoRel>
        """
        self.add()
        self.restoRel()

    def restoRel(self):
        if self.id_token_atual() in self._operadores_rel:
            self.avanca()
            self.add()

    def add(self):
        """
        <add> -> <mult> <restoAdd>
        """
        self.mult()
        self.restoAdd()

    def restoAdd(self):
        while self.id_token_atual() in self._operadores_add:
            self.avanca()
            self.mult()

    def mult(self):
        """
        <mult> -> <uno> <restoMult>
        """
        self.uno()
        self.restoMult()

    def restoMult(self):
        while self.id_token_atual() in self._operadores_mult:
            self.avanca()
            self.uno()

    def uno(self):
        """
        <uno> -> '+' <uno> | '-' <uno> | <fatorZao>
        """
        id_atual = self.id_token_atual()

        if id_atual == TOKEN_IDS["SOMA"]:
            self.consome_id(TOKEN_IDS["SOMA"])
            self.uno()
        elif id_atual == TOKEN_IDS["SUBTRACAO"]:
            self.consome_id(TOKEN_IDS["SUBTRACAO"])
            self.uno()
        else:
            self.fatorZao()

    def fatorZao(self):
        """
        <fatorZao> -> <fatorZin> | '(' <atrib> ')'
        """
        if self.id_token_atual() == TOKEN_IDS["ABRE_PAREN"]:
            self.consome_id(TOKEN_IDS["ABRE_PAREN"])
            self.atrib()
            self.consome_id(TOKEN_IDS["FECHA_PAREN"])
        else:
            self.fatorZin()

    def fatorZin(self):
        """
        <fatorZin> -> STR | IDENT | NUMint | NUMfloat | valorBooleano | valorChar
        """
        id_atual = self.id_token_atual()

        if id_atual in self._literais_validos:
            self.avanca()
        else:
            linha, coluna = self.linha_coluna_atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}, coluna {coluna}: "
                f"esperava literal, identificador ou expressão entre parênteses, "
                f"mas encontrou '{self.lexema_atual()}'"
            )