#!/usr/bin/env python3
"""
Teste de diferentes codificações de caracteres para identificar o problema da assinatura.
"""

import hashlib
import json
import requests
import time

def test_encoding_variations():
    """Testa diferentes codificações de caracteres."""
    
    print("🧪 TESTANDO DIFERENTES CODIFICAÇÕES DE CARACTERES")
    print("=" * 60)
    
    # Credenciais reais
    app_id = "18330800803"
    secret = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"
    
    # Timestamp atual
    timestamp = int(time.time())
    
    # Query compacta
    query = """{productOfferV2(){nodes{productName itemId commissionRate commission price sales imageUrl shopName productLink offerLink periodStartTime periodEndTime priceMin priceMax productCatIds ratingStar priceDiscountRate shopId shopType sellerCommissionRate shopeeCommissionRate}pageInfo{page limit hasNextPage scrollId}}}"""
    
    # Payload
    payload = {"query": query}
    
    print(f"App ID: {app_id}")
    print(f"Secret: {secret[:10]}...")
    print(f"Query: {query[:100]}...")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Teste 1: JSON padrão com separators
    print("🔍 TESTE 1: JSON padrão com separators")
    payload_json_1 = json.dumps(payload, separators=(',', ':'))
    base_string_1 = f"{app_id}{timestamp}{payload_json_1}{secret}"
    signature_1 = hashlib.sha256(base_string_1.encode('utf-8')).hexdigest()
    print(f"Payload JSON: {payload_json_1[:100]}...")
    print(f"Assinatura: {signature_1}")
    print()
    
    # Teste 2: JSON sem separators (com espaços)
    print("🔍 TESTE 2: JSON sem separators (com espaços)")
    payload_json_2 = json.dumps(payload)
    base_string_2 = f"{app_id}{timestamp}{payload_json_2}{secret}"
    signature_2 = hashlib.sha256(base_string_2.encode('utf-8')).hexdigest()
    print(f"Payload JSON: {payload_json_2[:100]}...")
    print(f"Assinatura: {signature_2}")
    print()
    
    # Teste 3: JSON com ensure_ascii=False
    print("🔍 TESTE 3: JSON com ensure_ascii=False")
    payload_json_3 = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    base_string_3 = f"{app_id}{timestamp}{payload_json_3}{secret}"
    signature_3 = hashlib.sha256(base_string_3.encode('utf-8')).hexdigest()
    print(f"Payload JSON: {payload_json_3[:100]}...")
    print(f"Assinatura: {signature_3}")
    print()
    
    # Teste 4: JSON com sort_keys=True
    print("🔍 TESTE 4: JSON com sort_keys=True")
    payload_json_4 = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    base_string_4 = f"{app_id}{timestamp}{payload_json_4}{secret}"
    signature_4 = hashlib.sha256(base_string_4.encode('utf-8')).hexdigest()
    print(f"Payload JSON: {payload_json_4[:100]}...")
    print(f"Assinatura: {signature_4}")
    print()
    
    # Teste 5: String literal exata (como na ferramenta)
    print("🔍 TESTE 5: String literal exata (como na ferramenta)")
    payload_json_5 = '{"query":"{productOfferV2(){nodes{productName itemId commissionRate commission price sales imageUrl shopName productLink offerLink periodStartTime periodEndTime priceMin priceMax productCatIds ratingStar priceDiscountRate shopId shopType sellerCommissionRate shopeeCommissionRate}pageInfo{page limit hasNextPage scrollId}}}"}'
    base_string_5 = f"{app_id}{timestamp}{payload_json_5}{secret}"
    signature_5 = hashlib.sha256(base_string_5.encode('utf-8')).hexdigest()
    print(f"Payload JSON: {payload_json_5[:100]}...")
    print(f"Assinatura: {signature_5}")
    print()
    
    print("=" * 60)
    print("🚀 TESTANDO TODAS AS VARIAÇÕES...")
    print("=" * 60)
    
    # Testa todas as variações
    variations = [
        ("JSON padrão com separators", payload_json_1, signature_1),
        ("JSON sem separators", payload_json_2, signature_2),
        ("JSON ensure_ascii=False", payload_json_3, signature_3),
        ("JSON sort_keys=True", payload_json_4, signature_4),
        ("String literal exata", payload_json_5, signature_5)
    ]
    
    for name, payload_json, signature in variations:
        print(f"\n🧪 Testando: {name}")
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
            "Accept": "application/json",
            "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
        }
        
        # URL da API
        url = "https://open-api.affiliate.shopee.com.br/graphql"
        
        try:
            response = requests.post(
                url,
                json=json.loads(payload_json),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("errors"):
                        error_code = data["errors"][0]["extensions"]["code"]
                        error_msg = data["errors"][0]["extensions"]["message"]
                        print(f"❌ Erro {error_code}: {error_msg}")
                        
                        if error_code == 10020 and "Invalid Signature" in error_msg:
                            print("🔍 Assinatura inválida")
                        elif error_code == 10020 and "Request Expired" in error_msg:
                            print("🔍 Timestamp expirado")
                        else:
                            print("🔍 Outro erro")
                    else:
                        print("✅ SUCESSO! Resposta válida recebida!")
                        return name, payload_json, signature
                        
                except json.JSONDecodeError:
                    print("⚠️ Resposta não é JSON válido")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    print("❌ Nenhuma variação funcionou")
    print("💡 O problema pode estar em outro aspecto:")
    print("1. Formato específico esperado pela API")
    print("2. Headers HTTP específicos")
    print("3. Endpoint diferente")
    print("4. Versão da API")
    print("5. Status da conta")

if __name__ == "__main__":
    test_encoding_variations()
