#!/usr/bin/env python3
"""
Teste exato da documentação da Shopee para verificar a implementação.
"""

import hashlib
import json
import requests
import time

def test_exact_documentation():
    """Testa exatamente o exemplo da documentação da Shopee."""
    
    print("🧪 TESTANDO EXEMPLO EXATO DA DOCUMENTAÇÃO SHOPEE")
    print("=" * 60)
    
    # Exemplo exato da documentação
    app_id = "123456"
    secret = "demo"
    timestamp = 1577836800
    
    # Payload exato da documentação
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
    
    # Constrói string base para assinatura (exatamente como na documentação)
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print(f"String base para assinatura:")
    print(f"'{base_string}'")
    print()
    
    # Gera assinatura SHA256
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    print(f"Assinatura gerada: {signature}")
    print(f"Assinatura esperada: dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412")
    print(f"Assinaturas coincidem: {signature == 'dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412'}")
    print()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    print(f"Authorization Header: {auth_header}")
    print()
    
    # Headers completos
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    # URL da API
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    print("🚀 Enviando requisição de teste...")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 Resposta:")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("errors"):
                    print(f"❌ Erro GraphQL: {data.get('errors')}")
                else:
                    print("✅ Sucesso! Resposta válida recebida.")
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    
    # Agora testa com nossas credenciais reais
    print("🧪 TESTANDO COM NOSSAS CREDENCIAIS REAIS")
    print("=" * 60)
    
    app_id_real = "18330800803"
    secret_real = "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4"
    timestamp_real = int(time.time())
    
    # Usa o mesmo payload da documentação
    payload_real = {
        "query": "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    }
    
    payload_json_real = json.dumps(payload_real, separators=(',', ':'))
    
    print(f"App ID: {app_id_real}")
    print(f"Secret: {secret_real}")
    print(f"Timestamp: {timestamp_real}")
    print(f"Payload JSON: {payload_json_real}")
    print()
    
    # Constrói string base para assinatura
    base_string_real = f"{app_id_real}{timestamp_real}{payload_json_real}{secret_real}"
    
    print(f"String base para assinatura:")
    print(f"'{base_string_real[:100]}...'")
    print()
    
    # Gera assinatura SHA256
    signature_real = hashlib.sha256(base_string_real.encode('utf-8')).hexdigest()
    
    print(f"Assinatura gerada: {signature_real}")
    print()
    
    # Constrói cabeçalho de autorização
    auth_header_real = f"SHA256 Credential={app_id_real}, Timestamp={timestamp_real}, Signature={signature_real}"
    
    print(f"Authorization Header: {auth_header_real[:100]}...")
    print()
    
    # Headers completos
    headers_real = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header_real
    }
    
    print("🚀 Enviando requisição com nossas credenciais...")
    
    try:
        response_real = requests.post(
            url,
            json=payload_real,
            headers=headers_real,
            timeout=30
        )
        
        print(f"📥 Resposta:")
        print(f"Status: {response_real.status_code}")
        print(f"Body: {response_real.text}")
        
        if response_real.status_code == 200:
            try:
                data_real = response_real.json()
                if data_real.get("errors"):
                    print(f"❌ Erro GraphQL: {data_real.get('errors')}")
                else:
                    print("✅ Sucesso! Resposta válida recebida.")
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response_real.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_exact_documentation()
