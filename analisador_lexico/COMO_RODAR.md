# Como rodar o analisador léxico (Mineirês)

## Requisito

Python 3 instalado.

## Onde executar

Abra o terminal na pasta **`analisador_lexico`** (a que contém `src/`, `input/` e `output/`).

## Comando básico

Lê um arquivo em `input/` e mostra os tokens no terminal:

```bash
python3 src/rodar_lexer.py input/exemplo_fibonacci.txt
```

## Salvar a saída em arquivo

```bash
python3 src/rodar_lexer.py input/exemplo_fibonacci.txt -o output/tokens_saida.txt
```

A mensagem “Tokens também salvos em: …” aparece no terminal; o conteúdo completo (cabeçalho + lista) vai para o arquivo indicado em `-o` / `--output`.

## Outros exemplos

```bash
python3 src/rodar_lexer.py input/exemplo_completo_mineires.txt -o output/tokens_completo.txt
python3 src/rodar_lexer.py input/exemplo_numericos_mineires.txt -o output/tokens_numericos.txt
```

## Ajuda

```bash
python3 src/rodar_lexer.py -h
```

## Se estiver na pasta “pai” do repositório

Use os caminhos completos até o script e até o `.txt`:

```bash
python3 analisador_lexico/src/rodar_lexer.py analisador_lexico/input/exemplo_fibonacci.txt
```
