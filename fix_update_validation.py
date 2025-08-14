#!/usr/bin/env python3
"""
Script para corrigir todas as validações de update no arquivo main.py
Substitui as verificações problemáticas por chamadas para a função is_valid_update
"""

import re

def fix_update_validations():
    # Lê o arquivo
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar as verificações problemáticas
    pattern = r'if not update\.effective_user or not update\.message:\s*\n\s*await update\.message\.reply_text\("❌ Erro: dados do usuário não encontrados\."\)\s*\n\s*return'
    
    # Substitui por chamada para is_valid_update
    replacement = '''if not is_valid_update(update):
        logger.warning("Update inválido em {function_name}")
        return'''
    
    # Encontra todas as ocorrências
    matches = re.finditer(pattern, content)
    
    # Lista para armazenar as posições das substituições
    replacements = []
    
    for match in matches:
        # Tenta determinar o nome da função
        start_pos = match.start()
        # Procura para trás para encontrar o nome da função
        before_match = content[:start_pos]
        function_match = re.search(r'async def (\w+)\(', before_match)
        function_name = function_match.group(1) if function_match else "função_desconhecida"
        
        # Cria a substituição personalizada
        custom_replacement = replacement.format(function_name=function_name)
        replacements.append((match.start(), match.end(), custom_replacement))
    
    # Aplica as substituições em ordem reversa para não afetar as posições
    for start, end, replacement_text in reversed(replacements):
        content = content[:start] + replacement_text + content[end:]
    
    # Escreve o arquivo corrigido
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Corrigidas {len(replacements)} validações de update")
    
    # Lista as funções corrigidas
    for start, end, replacement_text in replacements:
        before_match = content[:start]
        function_match = re.search(r'async def (\w+)\(', before_match)
        if function_match:
            print(f"  - {function_match.group(1)}")

if __name__ == "__main__":
    fix_update_validations()
