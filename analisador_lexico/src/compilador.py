from lexer_mineires import ErroLexico, LexerMineres
from analisador_sintatico import Parser, ErroSintatico


def main():
    # nome do arquivo de teste
    nome_arquivo = "../input/teste1.txt"

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
        # Pegamos a lista de quádruplas que o parse() está retornando agora
        codigo_intermediario = parser.parse()
        print("Programa sintaticamente correto!\n")

        print("--- CÓDIGO INTERMEDIÁRIO (QUÁDRUPLAS) ---")

        # 1. Imprimindo uma embaixo da outra no terminal
        for quad in codigo_intermediario:
            # quad[0] é o operador, quad[1] é o arg1, etc...
            # O ljust formata o texto para ficar alinhado como uma tabela bonita
            op = str(quad[0])
            arg1 = str(quad[1])
            arg2 = str(quad[2])
            res = str(quad[3])
            print(f"({op}, {arg1}, {arg2}, {res})")

        # 2. Opcional: Salvando as quádruplas em um arquivo de texto
        caminho_saida = "../output/codigo_intermediario.txt"
        with open(caminho_saida, "w", encoding="utf-8") as f:
            for quad in codigo_intermediario:
                f.write(f"({quad[0]}, {quad[1]}, {quad[2]}, {quad[3]})\n")

        print(f"\nCódigo intermediário salvo com sucesso em: {caminho_saida}")
    except ErroSintatico as e:
        print("Erro sintático:")
        print(e)


if __name__ == "__main__":
    main()
