import os
import sys
import subprocess

# Ajuste conforme seu ambiente
PYTHON_BIN = "python"
COMPILADOR_SCRIPT = "rodar_compilador.py"
TESTES_DIR = "TESTES"

# Mapeia prefixo de arquivo para a expectativa de saída:
# 0lexer02 -> Erro léxico
# 1gramar02 -> Erro sintático
# 2semantics02, 03, 04, 05 -> Erro semântico
# 3interpreter02 -> Erro execução
# O resto -> Sucesso

def run_tests():
    test_files = [f for f in os.listdir(TESTES_DIR) if f.endswith(".uai")]
    test_files.sort()
    
    passed = 0
    failed = 0

    print("========================================")
    print(" INICIANDO BATERIA DE TESTES - MINEIRÊS ")
    print("========================================")
    
    # Limpa o arquivo de log se existir
    if os.path.exists("erros_gerados.log"):
        os.remove("erros_gerados.log")
    
    for f in test_files:
        filepath = os.path.join(TESTES_DIR, f)
        print(f"Testando: {f} ... ", end="")
        
        # Define expectativa
        expect_error = False
        if "0lexer02" in f or "1gramar02" in f or "2semantics02" in f or "2semantics03" in f or "2semantics04" in f or "2semantics05" in f or "3interpreter02" in f:
            expect_error = True

        result = subprocess.run([PYTHON_BIN, COMPILADOR_SCRIPT, filepath], capture_output=True, text=True)
        
        has_error = result.returncode != 0 or "Erro" in result.stderr or "Erro" in result.stdout
        
        if expect_error == has_error:
            print("OK!")
            passed += 1
        else:
            print("FALHOU!")
            failed += 1
            print("--- EXPECTATIVA ---")
            print(f"Esperava Erro: {expect_error}")
            print("--- OUTPUT ---")
            print(result.stdout)
            print(result.stderr)
            print("-------------------")
            
        # Vamos salvar os logs detalhados das falhas ESPERADAS também num arquivo
        # para que o agente (eu) possa ler e validar as mensagens de erro.
        if expect_error:
            with open("erros_gerados.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"=== {f} ===\n")
                if result.stderr: log_file.write(result.stderr)
                if result.stdout: log_file.write(result.stdout)
                log_file.write("\n")
            
    print("========================================")
    print(f" RESULTADO FINAL: {passed} Passaram / {failed} Falharam")
    print("========================================")

if __name__ == "__main__":
    # Verifica qual comando python está disponível
    if subprocess.run(["py", "--version"], capture_output=True).returncode == 0:
        PYTHON_BIN = "py"
    elif subprocess.run(["python3", "--version"], capture_output=True).returncode == 0:
        PYTHON_BIN = "python3"
        
    run_tests()
