#!/usr/bin/env python3
"""
Teste do status da conta da Shopee e diferentes abordagens de autenticação.
"""

import hashlib
import json
import requests
import time

def test_account_status():
    """Testa o status da conta da Shopee."""
    
    print("🧪 TESTANDO STATUS DA CONTA SHOPEE")
    print("=" * 60)
    
    # Credenciais reais
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    
    # Timestamp atual
    timestamp = int(time.time())
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret[:10]}...")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Teste 1: Query mais simples possível
    print("🔍 TESTE 1: Query mais simples possível")
    simple_query = """{__schema{types{name}}}"""
    payload_1 = {"query": simple_query}
    payload_json_1 = json.dumps(payload_1, separators=(',', ':'))
    base_string_1 = f"{app_id}{timestamp}{payload_json_1}{secret}"
    signature_1 = hashlib.sha256(base_string_1.encode('utf-8')).hexdigest()
    
    print(f"Query: {simple_query}")
    print(f"Payload: {payload_json_1}")
    print(f"Assinatura: {signature_1}")
    print()
    
    # Teste 2: Query de teste da documentação
    print("🔍 TESTE 2: Query de teste da documentação")
    test_query = """{brandOffer{nodes{commissionRate offerName}}}"""
    payload_2 = {"query": test_query}
    payload_json_2 = json.dumps(payload_2, separators=(',', ':'))
    base_string_2 = f"{app_id}{timestamp}{payload_json_2}{secret}"
    signature_2 = hashlib.sha256(base_string_2.encode('utf-8')).hexdigest()
    
    print(f"Query: {test_query}")
    print(f"Payload: {payload_json_2}")
    print(f"Assinatura: {signature_2}")
    print()
    
    # Teste 3: Sem User-Agent (pode ser bloqueado)
    print("🔍 TESTE 3: Sem User-Agent")
    
    # Teste 4: Com User-Agent diferente
    print("🔍 TESTE 4: User-Agent diferente")
    
    print("=" * 60)
    print("🚀 EXECUTANDO TESTES...")
    print("=" * 60)
    
    # Teste 1: Query simples
    print(f"\n🧪 Teste 1: Query simples")
    headers_1 = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature_1}"
    }
    
    try:
        response_1 = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload_1,
            headers=headers_1,
            timeout=30
        )
        
        print(f"Status: {response_1.status_code}")
        print(f"Resposta: {response_1.text}")
        
        if response_1.status_code == 200:
            try:
                data = response_1.json()
                if data.get("errors"):
                    error_code = data["errors"][0]["extensions"]["code"]
                    error_msg = data["errors"][0]["extensions"]["message"]
                    print(f"❌ Erro {error_code}: {error_msg}")
                    
                    if error_code == 10035:
                        print("🔍 Conta sem acesso à API - verificar status")
                    elif error_code == 10020:
                        print("🔍 Problema de autenticação")
                    else:
                        print("🔍 Outro erro")
                else:
                    print("✅ SUCESSO! Query simples funcionou!")
                    return "simple_query", payload_1, signature_1
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response_1.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 2: Query da documentação
    print(f"\n🧪 Teste 2: Query da documentação")
    headers_2 = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature_2}"
    }
    
    try:
        response_2 = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload_2,
            headers=headers_2,
            timeout=30
        )
        
        print(f"Status: {response_2.status_code}")
        print(f"Resposta: {response_2.text}")
        
        if response_2.status_code == 200:
            try:
                data = response_2.json()
                if data.get("errors"):
                    error_code = data["errors"][0]["extensions"]["code"]
                    error_msg = data["errors"][0]["extensions"]["message"]
                    print(f"❌ Erro {error_code}: {error_msg}")
                    
                    if error_code == 10035:
                        print("🔍 Conta sem acesso à API - verificar status")
                    elif error_code == 10020:
                        print("🔍 Problema de autenticação")
                    else:
                        print("🔍 Outro erro")
                else:
                    print("✅ SUCESSO! Query da documentação funcionou!")
                    return "documentation_query", payload_2, signature_2
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response_2.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 3: Sem User-Agent
    print(f"\n🧪 Teste 3: Sem User-Agent")
    headers_3 = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature_1}"
    }
    
    try:
        response_3 = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            json=payload_1,
            headers=headers_3,
            timeout=30
        )
        
        print(f"Status: {response_3.status_code}")
        print(f"Resposta: {response_3.text}")
        
        if response_3.status_code == 200:
            try:
                data = response_3.json()
                if data.get("errors"):
                    error_code = data["errors"][0]["extensions"]["code"]
                    error_msg = data["errors"][0]["extensions"]["message"]
                    print(f"❌ Erro {error_code}: {error_msg}")
                else:
                    print("✅ SUCESSO! Sem User-Agent funcionou!")
                    return "no_user_agent", payload_1, signature_1
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response_3.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    print("📊 ANÁLISE FINAL")
    print("=" * 60)
    
    print("❌ Nenhum teste funcionou")
    print("💡 Possíveis causas:")
    print("1. Conta da Shopee sem acesso à API")
    print("2. Credenciais inválidas ou expiradas")
    print("3. API em manutenção ou com mudanças")
    print("4. Restrições geográficas")
    print("5. Necessidade de aprovação da conta")
    
    print("\n🔧 Próximos passos:")
    print("1. Verificar status da conta na plataforma Shopee")
    print("2. Entrar em contato com o suporte da Shopee")
    print("3. Verificar se há mudanças na documentação")
    print("4. Testar com conta de desenvolvimento")

if __name__ == "__main__":
    test_account_status()
