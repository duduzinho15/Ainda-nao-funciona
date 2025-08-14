#!/usr/bin/env python3
"""
Teste usando EXATAMENTE a mesma query que funcionou na ferramenta oficial da Shopee.
"""

import hashlib
import json
import requests
import time

def test_exact_tool_query():
    """Testa exatamente a mesma query que funcionou na ferramenta oficial da Shopee."""
    
    print("🧪 TESTANDO QUERY EXATA DA FERRAMENTA OFICIAL SHOPEE")
    print("=" * 60)
    
    # Credenciais reais
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    
    # Timestamp atual
    timestamp = int(time.time())
    
    # Query EXATA que funcionou na ferramenta oficial (sem quebras de linha extras)
    query = """{productOfferV2(){nodes{productName itemId commissionRate commission price sales imageUrl shopName productLink offerLink periodStartTime periodEndTime priceMin priceMax productCatIds ratingStar priceDiscountRate shopId shopType sellerCommissionRate shopeeCommissionRate}pageInfo{page limit hasNextPage scrollId}}}"""
    
    # Payload sem variáveis (formato correto)
    payload = {"query": query}
    
    # Converte para JSON string compacta
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret[:10]}...")
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
    print("🔍 COMPARAÇÃO COM FERRAMENTA OFICIAL")
    print("=" * 60)
    
    print("✅ O que estamos testando:")
    print("- Mesmas credenciais")
    print("- Query sem quebras de linha extras")
    print("- Formato compacto")
    print("- Timestamp atual")
    
    print("\n💡 Diferenças testadas:")
    print("1. Query sem quebras de linha extras")
    print("2. Formato mais compacto")
    print("3. Mesma estrutura exata da ferramenta")

if __name__ == "__main__":
    test_exact_tool_query()
