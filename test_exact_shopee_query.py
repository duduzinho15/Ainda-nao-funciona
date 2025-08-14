#!/usr/bin/env python3
"""
Teste usando exatamente a mesma query que funcionou na ferramenta da Shopee.
"""

import hashlib
import json
import requests
import time

def test_exact_shopee_query():
    """Testa exatamente a mesma query que funcionou na ferramenta da Shopee."""
    
    print("🧪 TESTANDO QUERY EXATA DA FERRAMENTA SHOPEE")
    print("=" * 60)
    
    # Credenciais exatas que funcionaram na ferramenta
    app_id = "18330800803"
    secret = "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4"
    
    # Query EXATA que funcionou na ferramenta da Shopee
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
    
    # Payload exato
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret}")
    print(f"Query: {query[:100]}...")
    print(f"Payload JSON: {payload_json[:100]}...")
    print()
    
    # Timestamp atual
    timestamp = int(time.time())
    
    # Constrói string base para assinatura (exatamente como na documentação)
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
    
    print("🚀 Enviando requisição com query exata da ferramenta...")
    
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
    print("🔍 COMPARAÇÃO COM FERRAMENTA DA SHOPEE")
    print("=" * 60)
    
    print("✅ O que funcionou na ferramenta:")
    print("- AppId: 18330800803")
    print("- Secret: BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4")
    print("- Query: productOfferV2")
    print("- Resposta: 20 produtos retornados")
    
    print("\n❌ O que não está funcionando em nossa implementação:")
    print("- Mesmas credenciais")
    print("- Mesma query")
    print("- Mesmo formato de assinatura")
    print("- Erro: Invalid Signature")
    
    print("\n💡 Possíveis causas:")
    print("1. Diferença na geração da assinatura")
    print("2. Diferença no formato do payload")
    print("3. Diferença nos headers")
    print("4. Diferença no timestamp")
    print("5. Diferença na codificação dos caracteres")

if __name__ == "__main__":
    test_exact_shopee_query()
