from __future__ import annotations
import sys

class ErroExecucao(Exception):
    """Exceção usada para indicar erro em tempo de execução."""
    pass

class Interpretador:
    def __init__(self, quadruplas, tabela_simbolos):
        self.quadruplas = quadruplas
        self.tabela_simbolos = tabela_simbolos # Dict[str, str] (nome -> tipo, e.g. "contador" -> "a")
        self.variaveis = {} # Dict[str, any] (armazena os valores das variáveis e temporários)
        self.labels = {} # Dict[str, int] (mapeia o nome do label para o índice da quádrupla)
        self.ip = 0 # Ponteiro de instrução

    def mapear_labels(self):
        for i, quad in enumerate(self.quadruplas):
            op = quad[0]
            if op == "label":
                label_name = quad[1]
                self.labels[label_name] = i

    def avaliar(self, lugar):
        if not isinstance(lugar, str):
            return lugar
        if lugar == "none":
            return None
        
        # Se for uma variável ou temporário já existente:
        if lugar in self.variaveis:
            return self.variaveis[lugar]
        
        # Se for literal boolean:
        if lugar == "eh":
            return True
        if lugar == "num_eh":
            return False
            
        # Se for literal string (com aspas duplas):
        if lugar.startswith('"') and lugar.endswith('"'):
            return lugar[1:-1]
            
        # Se for literal char (com aspas simples):
        if lugar.startswith("'") and lugar.endswith("'"):
            return lugar[1:-1]
            
        # Se for float (contém ponto):
        if "." in lugar:
            try:
                return float(lugar)
            except ValueError:
                pass
                
        # Se for inteiro (decimal, hexa ou octal):
        try:
            if lugar.startswith("0x") or lugar.startswith("0X"):
                return int(lugar, 16)
            elif lugar.startswith("0") and len(lugar) > 1 and lugar[1].isdigit():
                return int(lugar, 8)
            else:
                return int(lugar)
        except ValueError:
            pass
            
        # Se for um identificador mas não está na tabela de símbolos nem nas variáveis,
        # ou se for temporário, levantamos erro de variável não definida.
        raise ErroExecucao(f"Erro de execução: variável ou temporário '{lugar}' não foi inicializado/declarado.")

    def executar_passo(self):
        if self.ip >= len(self.quadruplas):
            return False # Fim da execução
            
        quad = self.quadruplas[self.ip]
        op = quad[0]
        
        if op == "label":
            self.ip += 1
            
        elif op == "jump":
            target = quad[1]
            if target not in self.labels:
                raise ErroExecucao(f"Erro de execução: label '{target}' não encontrado.")
            self.ip = self.labels[target]
            
        elif op == "if":
            cond_var = quad[1]
            label_true = quad[2]
            label_false = quad[3]
            
            cond_val = self.avaliar(cond_var)
            if not isinstance(cond_val, bool):
                raise ErroExecucao(f"Erro de execução: a condição do IF deve ser booleana, mas obteve '{cond_val}'.")
                
            target = label_true if cond_val else label_false
            if target not in self.labels:
                raise ErroExecucao(f"Erro de execução: label '{target}' não encontrado.")
            self.ip = self.labels[target]
            
        elif op == "att":
            dest = quad[1]
            src = quad[2]
            
            val = self.avaliar(src)
            self.variaveis[dest] = val
            self.ip += 1
            
        elif op == "uno":
            # (uno, sinal, dest, src)
            sinal = quad[1]
            dest = quad[2]
            src = quad[3]
            
            val = self.avaliar(src)
            if not isinstance(val, (int, float)):
                raise ErroExecucao(f"Erro de execução: sinal unário '{sinal}' exige operando numérico, mas obteve '{val}'.")
                
            if sinal == "-":
                self.variaveis[dest] = -val
            else:
                self.variaveis[dest] = val
            self.ip += 1
            
        elif op in ("add", "sub", "veiz", "sob", "/", "%"):
            dest = quad[1]
            arg1 = quad[2]
            arg2 = quad[3]
            
            val1 = self.avaliar(arg1)
            val2 = self.avaliar(arg2)
            
            if op == "add":
                if isinstance(val1, str) or isinstance(val2, str):
                    self.variaveis[dest] = str(val1) + str(val2)
                else:
                    self.variaveis[dest] = val1 + val2
            elif op == "sub":
                self.variaveis[dest] = val1 - val2
            elif op == "veiz":
                self.variaveis[dest] = val1 * val2
            elif op == "sob":
                if val2 == 0 or val2 == 0.0:
                    raise ErroExecucao("Erro de execução: divisão por zero.")
                self.variaveis[dest] = val1 / val2
            elif op == "/":
                if val2 == 0:
                    raise ErroExecucao("Erro de execução: divisão por zero.")
                self.variaveis[dest] = val1 // val2
            elif op == "%":
                if val2 == 0:
                    raise ErroExecucao("Erro de execução: divisão por zero.")
                self.variaveis[dest] = val1 % val2
                
            self.ip += 1
            
        elif op in ("or", "and", "xor", "not"):
            dest = quad[1]
            arg1 = quad[2]
            arg2 = quad[3] # no caso do "not", arg2 é "none"
            
            val1 = self.avaliar(arg1)
            
            if op == "not":
                self.variaveis[dest] = not val1
            else:
                val2 = self.avaliar(arg2)
                if op == "or":
                    self.variaveis[dest] = val1 or val2
                elif op == "and":
                    self.variaveis[dest] = val1 and val2
                elif op == "xor":
                    self.variaveis[dest] = val1 != val2
                    
            self.ip += 1
            
        elif op in ("less", "gret", "leq", "geq", "eq", "dif"):
            dest = quad[1]
            arg1 = quad[2]
            arg2 = quad[3]
            
            val1 = self.avaliar(arg1)
            val2 = self.avaliar(arg2)
            
            if op == "less":
                self.variaveis[dest] = val1 < val2
            elif op == "gret":
                self.variaveis[dest] = val1 > val2
            elif op == "leq":
                self.variaveis[dest] = val1 <= val2
            elif op == "geq":
                self.variaveis[dest] = val1 >= val2
            elif op == "eq":
                self.variaveis[dest] = val1 == val2
            elif op == "dif":
                self.variaveis[dest] = val1 != val2
                
            self.ip += 1
            
        elif op == "call":
            func = quad[1]
            arg1 = quad[2]
            arg2 = quad[3]
            
            if func == "print":
                if arg1 == "none":
                    val_to_print = self.avaliar(arg2)
                else:
                    val_to_print = self.avaliar(arg1)
                
                # Exibe o valor
                if val_to_print is True:
                    print("eh")
                elif val_to_print is False:
                    print("num_eh")
                else:
                    print(val_to_print)
                
            elif func == "read":
                # arg1 é a variável de destino
                tipo_dest = self.tabela_simbolos.get(arg1)
                if tipo_dest is None:
                    raise ErroExecucao(f"Erro de execução: tipo da variável '{arg1}' não encontrado na tabela de símbolos.")
                
                try:
                    valor_lido_str = input().strip().lstrip("\ufeff")
                except EOFError:
                    valor_lido_str = ""
                
                # Conversão e validação com erro de leitura amigável
                if tipo_dest == "a":
                    try:
                        self.variaveis[arg1] = int(valor_lido_str)
                    except ValueError:
                        raise ErroExecucao(f"Erro de leitura: tipo incompatível. Esperava inteiro ('trem_di_numeru'), mas obteve '{valor_lido_str}'.")
                elif tipo_dest == "f":
                    try:
                        self.variaveis[arg1] = float(valor_lido_str)
                    except ValueError:
                        raise ErroExecucao(f"Erro de leitura: tipo incompatível. Esperava ponto flutuante ('trem_cum_virgula'), mas obteve '{valor_lido_str}'.")
                elif tipo_dest == "s":
                    self.variaveis[arg1] = valor_lido_str
                elif tipo_dest == "b":
                    if valor_lido_str == "eh":
                        self.variaveis[arg1] = True
                    elif valor_lido_str == "num_eh":
                        self.variaveis[arg1] = False
                    else:
                        raise ErroExecucao(f"Erro de leitura: tipo incompatível. Esperava booleano ('trem_discolhe' - 'eh' ou 'num_eh'), mas obteve '{valor_lido_str}'.")
                elif tipo_dest == "c":
                    if len(valor_lido_str) != 1:
                        raise ErroExecucao(f"Erro de leitura: tipo incompatível. Esperava caractere único ('trosso'), mas obteve '{valor_lido_str}'.")
                    self.variaveis[arg1] = valor_lido_str
                    
            self.ip += 1
            
        else:
            raise ErroExecucao(f"Erro de execução: comando intermediário desconhecido '{op}'.")
            
        return True

    def executar(self):
        self.mapear_labels()
        while self.executar_passo():
            pass
