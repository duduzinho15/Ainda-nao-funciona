#!/usr/bin/env python3
"""
Script para debugar exatamente o que está sendo enviado para a API da Shopee.
"""

import requests
import json
import hashlib
import time

def debug_shopee_request():
    """Debuga a requisição para a API da Shopee."""
    
    # Configurações
    app_id = "18330800803"
    secret = "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4"
    base_url = "https://open-api.affiliate.shopee.com.br"
    graphql_endpoint = "/graphql"
    
    # Query de teste
    query = """
    query TestConnection {
        __schema {
            queryType {
                name
            }
        }
    }
    """
    
    # Timestamp atual
    timestamp = int(time.time())
    
    # Constrói payload
    payload = {
        "query": query,
        "variables": {}
    }
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print("🔍 DEBUG DA REQUISIÇÃO SHOPEE")
    print("=" * 50)
    print(f"App ID: {app_id}")
    print(f"Secret: {secret}")
    print(f"Timestamp: {timestamp}")
    print(f"Query: {query.strip()}")
    print()
    
    print("📦 PAYLOAD:")
    print(f"Payload dict: {payload}")
    print(f"Payload JSON: {payload_json}")
    print()
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print("🔐 ASSINATURA:")
    print(f"String base: {base_string}")
    print(f"Tamanho da string base: {len(base_string)}")
    print()
    
    # Gera assinatura
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    print(f"Assinatura SHA256: {signature}")
    print(f"Tamanho da assinatura: {len(signature)}")
    print()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    print("📋 HEADERS:")
    print(f"Authorization: {auth_header}")
    print()
    
    # Headers completos
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": auth_header
    }
    
    print("🌐 REQUISIÇÃO:")
    url = f"{base_url}{graphql_endpoint}"
    print(f"URL: {url}")
    print(f"Method: POST")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Body: {payload_json}")
    print()
    
    # Faz a requisição
    try:
        print("🚀 ENVIANDO REQUISIÇÃO...")
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📥 RESPOSTA:")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "errors" in data:
                    print(f"❌ Erros GraphQL: {data['errors']}")
                else:
                    print(f"✅ Sucesso! Dados: {data}")
            except:
                print(f"⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    debug_shopee_request()
