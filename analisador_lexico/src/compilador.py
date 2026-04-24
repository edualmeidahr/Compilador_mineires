from lexer_mineires import ErroLexico, LexerMineres
from analisador_sintatico import Parser, ErroSintatico


def main():
    # nome do arquivo de teste
    nome_arquivo = "../input/teste_completo.txt"

    # 1. rodar o lexer
    lexer = LexerMineres()
    try:
        tokens = lexer.tokenize_file(nome_arquivo)
    except ErroLexico as e:
        print("Erro léxico:")
        print(e)
        return

    print("TOKENS GERADOS:")
    for t in tokens:
        print(t)

    print("\n--- ANALISE SINTATICA ---")

    # 2. rodar o parser
    parser = Parser(tokens)

    try:
        parser.parse()
        print("Programa sintaticamente correto!")
    except ErroSintatico as e:
        print("Erro sintático:")
        print(e)


if __name__ == "__main__":
    main()