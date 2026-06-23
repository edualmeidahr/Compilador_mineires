# Como Executar o Compilador Mineirês

Este repositório contém o pipeline completo para compilação do Mineirês (Léxico, Sintático, Semântico e Geração de Código Intermediário).

## Requisitos

- Python 3 instalado.

## Onde Executar

Abra o seu terminal na pasta **`analisador_lexico`** (a pasta que contém os subdiretórios `src/`, `input/`, etc.).

---

## 1. Compilador Completo (Recomendado)

O arquivo `rodar_compilador.py` na raiz executa a análise léxica, sintática, semântica e gera o código intermediário (quádruplas).

### Comando Básico (exibindo no terminal)
```bash
python3 rodar_compilador.py input/teste_completo.txt
```

### Salvar as Quádruplas em um Arquivo
Use a flag `-o` ou `--output` para gravar a lista de quádruplas:
```bash
python3 rodar_compilador.py input/teste_completo.txt -o output/codigo_intermediario.txt
```

---

## 2. Somente Análise Léxica (Opcional)

Se você desejar listar apenas a tabela de tokens gerados pelo analisador léxico:

### Comando Básico
```bash
python3 src/rodar_lexer.py input/exemplo_fibonacci.txt
```

### Salvar os Tokens em um Arquivo
```bash
python3 src/rodar_lexer.py input/exemplo_fibonacci.txt -o output/tokens_saida.txt
```

---

## 3. Rodando os Testes Unitários e de Integração

Você pode rodar toda a suíte de testes automáticos (50 testes cobrindo análise sintática, semântica, erros léxicos e mais) com o comando:
```bash
python3 -m unittest discover -s tests -v
```
