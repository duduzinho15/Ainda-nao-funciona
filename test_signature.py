#!/usr/bin/env python3
"""
Script para testar a geração da assinatura da API da Shopee.
"""

import hashlib
import json

def test_signature():
    """Testa a geração da assinatura da Shopee."""
    
    # Credenciais de teste
    app_id = "18330800803"
    secret = "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4"
    timestamp = 1755134852
    
    # Payload de teste (igual ao que está sendo enviado)
    payload = {
        "query": "\n            query TestConnection {\n                __schema {\n                    queryType {\n                        name\n                    }\n                }\n            }\n        ",
        "variables": {}
    }
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Payload JSON: {payload_json}")
    print()
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print(f"String base para assinatura:")
    print(f"'{base_string}'")
    print()
    
    # Gera assinatura SHA256
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    print(f"Assinatura gerada: {signature}")
    print()
    
    # Verifica se a assinatura tem 64 caracteres (256 bits)
    print(f"Tamanho da assinatura: {len(signature)} caracteres")
    print(f"Assinatura válida: {len(signature) == 64}")
    
    return signature

def test_documentation_example():
    """Testa o exemplo da documentação da Shopee."""
    
    print("\n" + "=" * 60)
    print("🧪 TESTANDO EXEMPLO DA DOCUMENTAÇÃO")
    print("=" * 60)
    
    # Exemplo da documentação
    app_id = "123456"
    secret = "demo"
    timestamp = 1577836800
    
    # Payload do exemplo
    payload = {
        "query": "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    }
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Payload JSON: {payload_json}")
    print()
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print(f"String base para assinatura:")
    print(f"'{base_string}'")
    print()
    
    # Gera assinatura SHA256
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    print(f"Assinatura gerada: {signature}")
    print(f"Assinatura esperada: dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412")
    print(f"Assinaturas coincidem: {signature == 'dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412'}")
    
    return signature

if __name__ == "__main__":
    print("🧪 Testando geração da assinatura da Shopee...")
    print("=" * 50)
    
    # Teste com nossas credenciais
    signature1 = test_signature()
    
    # Teste com exemplo da documentação
    signature2 = test_documentation_example()
    
    print("=" * 50)
    print("✅ Teste concluído!")
