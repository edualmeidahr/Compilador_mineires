#!/usr/bin/env python3
"""Lê um arquivo fonte Mineirês e imprime (ou salva) os tokens."""

import argparse
import sys
from pathlib import Path

# Permite `import lexer_mineires` ao rodar de qualquer pasta (o Python já coloca
# o diretório do script em sys.path; isso reforça o caso de import indireto).
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lexer_mineires import LexerMineres


def format_tokens(tokens: list) -> str:
    lines = []
    for lexema, token_id, linha, coluna in tokens:
        lines.append(f"({linha:3d},{coluna:3d})  {token_id:4d}  {lexema}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analisador léxico Mineirês: lista tokens (Lexema, Token_ID, Linha, Coluna)."
    )
    parser.add_argument("entrada", type=Path, help="Arquivo fonte (.txt)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="ARQUIVO",
        help="Salva a lista de tokens neste arquivo (UTF-8). Se omitido, só imprime no terminal.",
    )
    args = parser.parse_args()

    path = args.entrada
    if not path.is_file():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)

    lx = LexerMineres()
    tokens = lx.tokenize_file(str(path))

    header = (
        f"Arquivo: {path.resolve()}\n"
        f"Total de tokens: {len(tokens)}\n\n"
    )
    body = format_tokens(tokens)
    text = header + body

    print(text, end="")

    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
        print(f"\nTokens também salvos em: {args.output.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
