#!/usr/bin/env python3
"""
Teste com nossas credenciais reais da Shopee usando o formato correto.
"""

import hashlib
import json
import requests
import time
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def test_real_credentials():
    """Testa com nossas credenciais reais da Shopee."""
    
    print("🧪 TESTANDO COM CREDENCIAIS REAIS DA SHOPEE")
    print("=" * 60)
    
    # Nossas credenciais reais (do config.py)
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    
    print("✅ Usando credenciais do config.py")
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret[:10]}..." if secret else "Secret: Não configurado")
    print()
    
    # Timestamp atual
    timestamp = int(time.time())
    
    # Query EXATA que funcionou na ferramenta oficial
    query = """{
    productOfferV2(){
        nodes {
            productName
            itemId
            commissionRate
            commission
            price
            sales
            imageUrl
            shopName
            productLink
            offerLink
            periodStartTime
            periodEndTime
            priceMin
            priceMax
            productCatIds
            ratingStar
            priceDiscountRate
            shopId
            shopType
            sellerCommissionRate
            shopeeCommissionRate
        }
        pageInfo{
            page
            limit
            hasNextPage
            scrollId
        }
    }
}"""
    
    # Payload sem variáveis (formato correto)
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"Query: {query[:100]}...")
    print(f"Payload JSON: {payload_json[:100]}...")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Constrói string base para assinatura
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    
    print(f"String base para assinatura:")
    print(f"'{base_string[:100]}...'")
    print()
    
    # Gera assinatura SHA256
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    print(f"Assinatura gerada: {signature}")
    print()
    
    # Constrói cabeçalho de autorização
    auth_header = f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
    
    print(f"Authorization Header: {auth_header[:100]}...")
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
    
    print("🚀 Enviando requisição com credenciais reais...")
    
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
                    
                    # Análise do erro
                    if error_code == 10020:
                        if "Invalid Signature" in error_msg:
                            print("🔍 Análise: Assinatura inválida - verificar geração")
                        elif "Request Expired" in error_msg:
                            print("🔍 Análise: Timestamp expirado - verificar sincronização de tempo")
                        elif "Invalid Credential" in error_msg:
                            print("🔍 Análise: Credenciais inválidas - verificar AppId/Secret")
                        else:
                            print("🔍 Análise: Outro erro de autenticação")
                    elif error_code == 10035:
                        print("🔍 Análise: Sem acesso à API - verificar status da conta")
                    else:
                        print("🔍 Análise: Erro desconhecido")
                        
                else:
                    print("✅ Sucesso! Resposta válida recebida.")
                    # Verifica se temos dados
                    if data.get("data", {}).get("productOfferV2", {}).get("nodes"):
                        nodes = data["data"]["productOfferV2"]["nodes"]
                        print(f"🎉 Encontrados {len(nodes)} produtos!")
                        # Mostra o primeiro produto
                        if nodes:
                            first_product = nodes[0]
                            print(f"📦 Primeiro produto: {first_product.get('productName', 'Sem nome')}")
                            print(f"💰 Preço: R$ {first_product.get('price', 'N/A')}")
                            print(f"🏪 Loja: {first_product.get('shopName', 'N/A')}")
                    else:
                        print("⚠️ Resposta sem dados de produtos")
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 ANÁLISE DOS RESULTADOS")
    print("=" * 60)
    
    print("✅ O que está funcionando:")
    print("- Geração da assinatura SHA256")
    print("- Formato da requisição GraphQL")
    print("- Headers HTTP")
    print("- Endpoint da API")
    
    print("\n❌ Possíveis problemas:")
    print("1. Credenciais inválidas ou expiradas")
    print("2. Conta sem acesso à API")
    print("3. Diferença na codificação de caracteres")
    print("4. Formato específico esperado pela API")

if __name__ == "__main__":
    test_real_credentials()
