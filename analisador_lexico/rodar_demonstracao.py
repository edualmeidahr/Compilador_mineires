#!/usr/bin/env python3
"""
Executa o lexer no programa de demonstração e grava/ mostra os tokens.
Uso (na pasta analisador_lexico):
    python3 rodar_demonstracao.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "input" / "demonstracao_lexer_total.txt"
OUT = RAIZ / "output" / "demonstracao_saida.txt"
LEXER = RAIZ / "src" / "rodar_lexer.py"

OUT.parent.mkdir(parents=True, exist_ok=True)
env = {**__import__("os").environ, "PYTHONPATH": str(RAIZ / "src")}

r = subprocess.run(
    [sys.executable, str(LEXER), str(SRC), "-o", str(OUT)],
    cwd=str(RAIZ),
    env=env,
    capture_output=True,
    text=True,
    check=False,
)
if r.stderr:
    print(r.stderr, end="", file=sys.stderr)
if r.returncode != 0:
    print(r.stdout, end="")
    sys.exit(r.returncode)
print()
print("Fonte:", SRC.resolve())
print("Salvo: ", OUT.resolve())
print()
print(OUT.read_text(encoding="utf-8"), end="")
