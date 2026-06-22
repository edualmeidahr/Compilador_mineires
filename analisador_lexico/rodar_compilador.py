#!/usr/bin/env python3
"""Lê um arquivo fonte Mineirês e executa o compilador completo (Lexer + Parser + Analisador Semântico + Código Intermediário)."""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório 'src' ao sys.path para permitir a importação direta dos módulos
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lexer_mineires import ErroLexico, LexerMineres
from analisador_sintatico import Parser, ErroSintatico, ErroSemantico
from interpretador import Interpretador, ErroExecucao


def format_quadruples(quadruples: list) -> str:
    lines = []
    for op, arg1, arg2, res in quadruples:
        lines.append(f"({op}, {arg1}, {arg2}, {res})")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compilador Mineirês: executa análise léxica, sintática, semântica e gera código intermediário."
    )
    parser.add_argument("entrada", type=Path, help="Arquivo fonte Mineirês (.txt)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="ARQUIVO",
        help="Salva as quádruplas do código intermediário neste arquivo (UTF-8). Se omitido, só imprime no terminal.",
    )
    args = parser.parse_args()

    path = args.entrada
    if not path.is_file():
        print(f"Erro: Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    # 1. Análise Léxica (Lexer)
    lexer = LexerMineres()
    try:
        tokens = lexer.tokenize_file(str(path))
    except ErroLexico as e:
        print(f"Erro léxico:\n{e}", file=sys.stderr)
        sys.exit(2)

    # 2. Análise Sintática, Semântica e Geração de Código (Parser)
    compilador = Parser(tokens)
    try:
        quadruplas = compilador.parse()
    except ErroSintatico as e:
        print(f"Erro sintático:\n{e}", file=sys.stderr)
        sys.exit(3)
    except ErroSemantico as e:
        print(f"Erro semântico:\n{e}", file=sys.stderr)
        sys.exit(4)

    # Sucesso! Exibe as quádruplas geradas
    print("Compilação concluída com sucesso! Programa correto.\n", file=sys.stderr)
    print("--- CÓDIGO INTERMEDIÁRIO (QUÁDRUPLAS) ---", file=sys.stderr)
    
    text = format_quadruples(quadruplas)
    print(text)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"\nCódigo intermediário também salvo em: {args.output.resolve()}", file=sys.stderr)

    # 3. Execução (Interpretador)
    print("\n--- INICIANDO EXECUÇÃO (MÁQUINA VIRTUAL) ---\n", file=sys.stderr)
    interpretador = Interpretador(quadruplas, compilador.tabela_simbolos)
    try:
        interpretador.executar()
    except ErroExecucao as e:
        print(f"\nErro em tempo de execução:\n{e}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
