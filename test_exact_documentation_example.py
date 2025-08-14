#!/usr/bin/env python3
"""
Teste usando EXATAMENTE o exemplo da documentação da Shopee.
"""

import hashlib
import json
import requests
import time

def test_exact_documentation_example():
    """Testa exatamente o exemplo da documentação da Shopee."""
    
    print("🧪 TESTANDO EXEMPLO EXATO DA DOCUMENTAÇÃO SHOPEE")
    print("=" * 60)
    
    # Exemplo EXATO da documentação
    app_id = "123456"
    secret = "demo"
    timestamp = int(time.time())  # Timestamp atual (não pode ser fixo)
    
    # Payload EXATO da documentação
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
                    error_code = data["errors"][0]["extensions"]["code"]
                    error_msg = data["errors"][0]["extensions"]["message"]
                    print(f"❌ Erro {error_code}: {error_msg}")
                else:
                    print("✅ Sucesso! Resposta válida recebida.")
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 COMPARAÇÃO COM NOSSA IMPLEMENTAÇÃO")
    print("=" * 60)
    
    print("✅ O que funcionou na documentação:")
    print("- AppId: 123456")
    print("- Secret: demo")
    print("- Timestamp: 1577836800")
    print("- Query: brandOffer")
    print("- Assinatura: dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412")
    
    print("\n❌ O que não está funcionando em nossa implementação:")
    print("- Mesmo formato de assinatura")
    print("- Mesmo formato de headers")
    print("- Erro: Invalid Signature")
    
    print("\n💡 Possíveis causas:")
    print("1. Diferença na codificação de caracteres")
    print("2. Diferença no formato do JSON")
    print("3. Diferença nos headers HTTP")
    print("4. Diferença no endpoint")
    print("5. Diferença na versão da API")

if __name__ == "__main__":
    test_exact_documentation_example()

