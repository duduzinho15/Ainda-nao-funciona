# shopee_api.py
import requests
import json
import hashlib
import time
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suas credenciais da Shopee
APP_ID = "18330800803"  # Seu AppID real
SECRET_KEY = "ZWOPZOLVZZISXF5J6RIXTHGISP4RZMG6"  # Sua senha (secret) real

# Endpoint oficial da API de afiliados Shopee
API_URL = "https://open-api.affiliate.shopee.com.br/graphql"


def gerar_assinatura(app_id, timestamp, payload, secret):
    """
    Gera a assinatura SHA256 conforme documentação da Shopee
    """
    # Constrói a string base: AppId+Timestamp+Payload+Secret
    base_string = f"{app_id}{timestamp}{payload}{secret}"

    # Gera a assinatura SHA256
    signature = hashlib.sha256(base_string.encode("utf-8")).hexdigest()

    return signature


def criar_headers(payload):
    """
    Cria os headers de autenticação com assinatura
    """
    timestamp = int(time.time())

    # Converte payload para JSON string compacta
    payload_json = json.dumps(payload, separators=(",", ":"))

    # Gera a assinatura
    signature = gerar_assinatura(APP_ID, timestamp, payload_json, SECRET_KEY)

    # Headers com autenticação SHA256
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
        "Accept": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}",
    }

    return headers


def buscar_por_palavra_chave(keyword, limit=5):
    """
    Busca produtos na Shopee por palavra-chave
    """
    try:
        # Query GraphQL para busca por palavra-chave
        query = """{
            productOfferV2(limit: %d, keyword: "%s"){
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
        }""" % (limit, keyword)

        payload = {"query": query}
        headers = criar_headers(payload)

        logger.info(f"Buscando produtos com palavra-chave: {keyword}")
        logger.info(f"Headers: {headers}")

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        logger.info(f"Status da resposta: {response.status_code}")
        logger.info(f"Resposta: {response.text}")

        if response.status_code != 200:
            return {"erro": f"Erro HTTP: {response.status_code}"}

        data = response.json()

        if "errors" in data:
            logger.error(f"Erros da API: {data['errors']}")
            return {"erro": data["errors"]}

        if "data" not in data or "productOfferV2" not in data["data"]:
            return {"erro": "Estrutura de resposta inesperada"}

        produtos = []
        nodes = data["data"]["productOfferV2"]["nodes"]

        for item in nodes:
            # Converte preço de centavos para reais
            preco = float(item.get("price", "0")) / 100 if item.get("price") else 0

            produtos.append(
                {
                    "titulo": item.get("productName", "Produto sem nome"),
                    "preco": f"R$ {preco:.2f}",
                    "preco_original": f"R$ {preco:.2f}",  # Shopee não fornece preço original
                    "imagem": item.get("imageUrl", ""),
                    "link": item.get("offerLink", item.get("productLink", "")),
                    "loja": item.get("shopName", "Shopee"),
                    "avaliacao": item.get("ratingStar", "N/A"),
                    "vendas": item.get("sales", 0),
                    "desconto": item.get("priceDiscountRate", 0),
                    "comissao": item.get("commissionRate", "0"),
                    "item_id": item.get("itemId", ""),
                    "shop_id": item.get("shopId", ""),
                }
            )

        logger.info(f"Encontrados {len(produtos)} produtos")
        return produtos

    except Exception as e:
        logger.error(f"Erro ao buscar por palavra-chave: {e}")
        return {"erro": str(e)}


def buscar_ofertas_gerais(limit=5):
    """
    Busca ofertas gerais na Shopee
    """
    try:
        # Query GraphQL para ofertas gerais (sem filtro específico)
        query = (
            """{
            productOfferV2(limit: %d){
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
            % limit
        )

        payload = {"query": query}
        headers = criar_headers(payload)

        logger.info("Buscando ofertas gerais na Shopee")
        logger.info(f"Headers: {headers}")

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        logger.info(f"Status da resposta: {response.status_code}")
        logger.info(f"Resposta: {response.text}")

        if response.status_code != 200:
            return {"erro": f"Erro HTTP: {response.status_code}"}

        data = response.json()

        if "errors" in data:
            logger.error(f"Erros da API: {data['errors']}")
            return {"erro": data["errors"]}

        if "data" not in data or "productOfferV2" not in data["data"]:
            return {"erro": "Estrutura de resposta inesperada"}

        ofertas = []
        nodes = data["data"]["productOfferV2"]["nodes"]

        for item in nodes:
            # Converte preço de centavos para reais
            preco = float(item.get("price", "0")) / 100 if item.get("price") else 0

            ofertas.append(
                {
                    "titulo": item.get("productName", "Produto sem nome"),
                    "preco": f"R$ {preco:.2f}",
                    "preco_original": f"R$ {preco:.2f}",  # Shopee não fornece preço original
                    "imagem": item.get("imageUrl", ""),
                    "link": item.get("offerLink", item.get("productLink", "")),
                    "loja": item.get("shopName", "Shopee"),
                    "avaliacao": item.get("ratingStar", "N/A"),
                    "vendas": item.get("sales", 0),
                    "desconto": item.get("priceDiscountRate", 0),
                    "comissao": item.get("commissionRate", "0"),
                    "item_id": item.get("itemId", ""),
                    "shop_id": item.get("shopId", ""),
                }
            )

        logger.info(f"Encontradas {len(ofertas)} ofertas gerais")
        return ofertas

    except Exception as e:
        logger.error(f"Erro ao buscar ofertas gerais: {e}")
        return {"erro": str(e)}


def testar_conexao():
    """
    Testa a conexão com a API da Shopee
    """
    try:
        # Query simples para testar conexão
        query = """{
            __schema {
                types {
                    name
                }
            }
        }"""

        payload = {"query": query}
        headers = criar_headers(payload)

        logger.info("Testando conexão com a API da Shopee...")

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        logger.info(f"Status da resposta: {response.status_code}")
        logger.info(f"Resposta: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                logger.error(f"Erros da API: {data['errors']}")
                return False
            else:
                logger.info("✅ Conexão com a API da Shopee estabelecida com sucesso!")
                return True
        else:
            logger.error(f"❌ Erro HTTP: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao testar conexão: {e}")
        return False


if __name__ == "__main__":
    print("🧪 TESTANDO API DA SHOPEE")
    print("=" * 50)

    # Testa conexão primeiro
    print("\n🔌 Testando conexão...")
    if testar_conexao():
        print("✅ Conexão estabelecida!")

        # Testa busca por palavra-chave
        print("\n🔍 Teste de busca por palavra-chave:")
        produtos = buscar_por_palavra_chave("smartphone", limit=3)
        if "erro" not in produtos:
            print(f"✅ Encontrados {len(produtos)} produtos:")
            for i, p in enumerate(produtos, 1):
                print(f"\n{i}. {p['titulo']}")
                print(f"   💰 {p['preco']}")
                print(f"   🏪 {p['loja']}")
                print(f"   ⭐ {p['avaliacao']}")
                print(f"   🛒 {p['vendas']} vendas")
                print(f"   🔗 {p['link'][:50]}...")
        else:
            print(f"❌ Erro: {produtos['erro']}")

        # Testa ofertas gerais
        print("\n🏷️ Teste de ofertas gerais:")
        ofertas = buscar_ofertas_gerais(limit=3)
        if "erro" not in ofertas:
            print(f"✅ Encontradas {len(ofertas)} ofertas:")
            for i, o in enumerate(ofertas, 1):
                print(f"\n{i}. {o['titulo']}")
                print(f"   💰 {o['preco']}")
                print(f"   🏪 {o['loja']}")
                print(f"   ⭐ {o['avaliacao']}")
                print(f"   🛒 {o['vendas']} vendas")
                print(f"   🔗 {o['link'][:50]}...")
        else:
            print(f"❌ Erro: {ofertas['erro']}")
    else:
        print("❌ Falha na conexão com a API da Shopee")
        print("Verifique as credenciais e o status da conta")
