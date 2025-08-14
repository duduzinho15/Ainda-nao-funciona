#!/usr/bin/env python3
"""
Debug byte por byte da string de assinatura.
"""

import hashlib
import json

def debug_bytes():
    """Debuga byte por byte a string de assinatura."""
    
    print("🔍 DEBUG BYTE POR BYTE")
    print("=" * 50)
    
    # Configurações
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    timestamp = 1755135427
    
    # Query da documentação
    query = "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    
    # Payload
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"App ID: '{app_id}' (tamanho: {len(app_id)})")
    print(f"Secret: '{secret}' (tamanho: {len(secret)})")
    print(f"Timestamp: {timestamp}")
    print(f"Payload JSON: '{payload_json}' (tamanho: {len(payload_json)})")
    print()
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print(f"String base: '{base_string}'")
    print(f"Tamanho total: {len(base_string)}")
    print()
    
    # Debug byte por byte
    print("🔍 DEBUG BYTE POR BYTE:")
    print("Índice | Char | ASCII | Hex")
    print("-" * 30)
    
    for i, char in enumerate(base_string):
        ascii_val = ord(char)
        hex_val = hex(ascii_val)[2:].upper()
        print(f"{i:6d} | '{char}' | {ascii_val:5d} | 0x{hex_val}")
    
    print()
    
    # Verifica se há caracteres especiais
    print("🔍 CARACTERES ESPECIAIS:")
    special_chars = []
    for i, char in enumerate(base_string):
        if not char.isprintable() or ord(char) > 127:
            special_chars.append((i, char, ord(char)))
    
    if special_chars:
        for i, char, ascii_val in special_chars:
            print(f"Índice {i}: '{char}' (ASCII: {ascii_val})")
    else:
        print("Nenhum caractere especial encontrado")
    
    print()
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    print(f"Assinatura SHA256: {signature}")
    
    # Verifica se a string base é igual ao que esperamos
    expected_parts = [
        app_id,
        str(timestamp),
        payload_json,
        secret
    ]
    
    print()
    print("🔍 VERIFICAÇÃO DAS PARTES:")
    for i, part in enumerate(expected_parts):
        print(f"Parte {i}: '{part}' (tamanho: {len(part)})")
    
    # Reconstrói a string para verificar
    reconstructed = "".join(expected_parts)
    print(f"String reconstruída: '{reconstructed}'")
    print(f"Strings são iguais: {base_string == reconstructed}")
    
    if base_string != reconstructed:
        print("❌ DIFERENÇA ENCONTRADA!")
        print(f"Original:  '{base_string}'")
        print(f"Reconstruída: '{reconstructed}'")
        
        # Encontra a primeira diferença
        for i, (orig, recon) in enumerate(zip(base_string, reconstructed)):
            if orig != recon:
                print(f"Primeira diferença no índice {i}:")
                print(f"  Original: '{orig}' (ASCII: {ord(orig)})")
                print(f"  Reconstruída: '{recon}' (ASCII: {ord(recon)})")
                break

if __name__ == "__main__":
    debug_bytes()
