#!/usr/bin/env python3
"""Script para verificar o arquivo geek_auto_poster.py"""

def check_file():
    try:
        with open('geek_auto_poster.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Total de linhas: {len(lines)}")
        print(f"Linha 273: {repr(lines[272])}")
        print(f"Linha 274: {repr(lines[273])}")
        print(f"Linha 275: {repr(lines[274])}")
        
        # Verifica se há caracteres especiais
        for i, line in enumerate(lines[270:280], 270):
            if any(ord(c) > 127 for c in line):
                print(f"Linha {i} tem caracteres especiais: {[ord(c) for c in line if ord(c) > 127]}")
        
        print("Verificação concluída!")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_file()
