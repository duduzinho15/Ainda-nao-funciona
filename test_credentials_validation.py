#!/usr/bin/env python3
"""
Teste de validação das credenciais da Shopee.
"""

import hashlib
import json
import requests
import time

def test_credential_variations():
    """Testa diferentes variações das credenciais."""
    
    print("🔍 TESTANDO VARIAÇÕES DAS CREDENCIAIS SHOPEE")
    print("=" * 60)
    
    # Credenciais fornecidas
    app_id = "18330800803"
    secret = "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4"
    partner_id = "18330800803"
    shop_id = "18330800803"
    
    # Query simples para teste
    query = "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"
    
    # Teste 1: Usando AppID como credencial
    print("🧪 TESTE 1: AppID como credencial")
    print("-" * 40)
    
    timestamp = int(time.time())
    payload = {"query": query}
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # String base: AppID + Timestamp + Payload + Secret
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Assinatura: {signature}")
    print(f"Header: {auth_header[:80]}...")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    try:
        response = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errors"):
                error_code = data["errors"][0]["extensions"]["code"]
                error_msg = data["errors"][0]["extensions"]["message"]
                print(f"❌ Erro {error_code}: {error_msg}")
            else:
                print("✅ Sucesso!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Teste 2: Usando PartnerID como credencial
    print("🧪 TESTE 2: PartnerID como credencial")
    print("-" * 40)
    
    timestamp = int(time.time())
    payload = {"query": query}
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # String base: PartnerID + Timestamp + Payload + Secret
    base_string = f"{partner_id}{timestamp}{payload_json}{secret}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    auth_header = f"SHA256 Credential={partner_id}, Timestamp={timestamp}, Signature={signature}"
    
    print(f"Partner ID: {partner_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Assinatura: {signature}")
    print(f"Header: {auth_header[:80]}...")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    try:
        response = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errors"):
                error_code = data["errors"][0]["extensions"]["code"]
                error_msg = data["errors"][0]["extensions"]["message"]
                print(f"❌ Erro {error_code}: {error_msg}")
            else:
                print("✅ Sucesso!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Teste 3: Usando ShopID como credencial
    print("🧪 TESTE 3: ShopID como credencial")
    print("-" * 40)
    
    timestamp = int(time.time())
    payload = {"query": query}
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    # String base: ShopID + Timestamp + Payload + Secret
    base_string = f"{shop_id}{timestamp}{payload_json}{secret}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    auth_header = f"SHA256 Credential={shop_id}, Timestamp={timestamp}, Signature={signature}"
    
    print(f"Shop ID: {shop_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Assinatura: {signature}")
    print(f"Header: {auth_header[:80]}...")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    try:
        response = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("errors"):
                error_code = data["errors"][0]["extensions"]["code"]
                error_msg = data["errors"][0]["extensions"]["message"]
                print(f"❌ Erro {error_code}: {error_msg}")
            else:
                print("✅ Sucesso!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Teste 4: Verificar se as credenciais estão ativas
    print("🧪 TESTE 4: Verificar status das credenciais")
    print("-" * 40)
    
    print("📋 Resumo das credenciais:")
    print(f"App ID: {app_id}")
    print(f"Partner ID: {partner_id}")
    print(f"Shop ID: {shop_id}")
    print(f"Secret: {secret}")
    print()
    
    print("💡 Possíveis problemas:")
    print("1. Credenciais podem estar inativas ou expiradas")
    print("2. App pode não ter permissões para a API GraphQL")
    print("3. Pode ser necessário ativar a API no painel da Shopee")
    print("4. As credenciais podem ser para um ambiente diferente (sandbox vs produção)")
    print()
    
    print("🔧 Recomendações:")
    print("1. Verificar no painel da Shopee se a API está ativa")
    print("2. Confirmar se as credenciais são para produção")
    print("3. Verificar se há algum processo de ativação pendente")
    print("4. Contactar o suporte da Shopee para validar as credenciais")

if __name__ == "__main__":
    test_credential_variations()
