#!/usr/bin/env python3
"""
Testa diferentes variações para identificar o problema com a API da Shopee.
"""

import requests
import json
import hashlib
import time

def test_variation_1():
    """Testa sem variáveis no payload."""
    print("🧪 VARIAÇÃO 1: Sem variáveis no payload")
    print("=" * 50)
    
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    timestamp = int(time.time())
    
    # Query simples
    query = "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    
    # Payload sem variáveis
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    # Faz a requisição
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Erros: {data['errors']}")
            else:
                print(f"✅ Sucesso!")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_variation_2():
    """Testa com endpoint diferente."""
    print("\n🧪 VARIAÇÃO 2: Endpoint diferente")
    print("=" * 50)
    
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    timestamp = int(time.time())
    
    # Query simples
    query = "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    
    # Payload
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    # Tenta endpoint diferente
    url = "https://open-api.affiliate.shopee.com.br/api/graphql"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Erros: {data['errors']}")
            else:
                print(f"✅ Sucesso!")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_variation_3():
    """Testa com query mais simples."""
    print("\n🧪 VARIAÇÃO 3: Query mais simples")
    print("=" * 50)
    
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    timestamp = int(time.time())
    
    # Query mais simples
    query = "{\n__schema{\n    queryType{\n        name\n    }\n}\n}"
    
    # Payload
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    # Faz a requisição
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Erros: {data['errors']}")
            else:
                print(f"✅ Sucesso!")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_variation_4():
    """Testa com timestamp fixo (como na documentação)."""
    print("\n🧪 VARIAÇÃO 4: Timestamp fixo como na documentação")
    print("=" * 50)
    
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    timestamp = 1577836800  # Timestamp da documentação
    
    # Query da documentação
    query = "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    
    # Payload
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    # Faz a requisição
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Erros: {data['errors']}")
            else:
                print(f"✅ Sucesso!")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🚀 TESTANDO DIFERENTES VARIAÇÕES")
    print("=" * 60)
    
    test_variation_1()
    test_variation_2()
    test_variation_3()
    test_variation_4()
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
