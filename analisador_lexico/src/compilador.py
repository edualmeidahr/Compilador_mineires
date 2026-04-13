from lexer_mineires import LexerMineres
from analisador_sintatico import Parser, ErroSintatico


def main():
    # nome do arquivo de teste
    nome_arquivo = "../input/teste3.txt"

    # 1. rodar o lexer
    lexer = LexerMineres()
    tokens = lexer.tokenize_file(nome_arquivo)

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