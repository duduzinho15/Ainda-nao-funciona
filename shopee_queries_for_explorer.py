"""
Queries GraphQL para usar no Explorer da API Shopee
https://open-api.affiliate.shopee.com.br/explorer

COMO USAR:
1. Acesse: https://open-api.affiliate.shopee.com.br/explorer
2. Cole a query desejada no campo de query
3. Configure as variáveis se necessário
4. Clique em "Play" para executar
"""

# ============================================================
# QUERY 1: TESTE DE CONEXÃO BÁSICA
# ============================================================
QUERY_TEST_CONNECTION = """
{
  __schema {
    types {
      name
    }
  }
}
"""

# ============================================================
# QUERY 2: BUSCAR OFERTAS DE PRODUTOS
# ============================================================
QUERY_PRODUCT_OFFERS = """
query ProductOfferQuery($limit: Int) {
  productOfferV2(limit: $limit) {
    nodes {
      productName
      itemId
      commissionRate
      commission
      price
      sales
      imageUrl
      shopName
      shopId
      ratingStar
      productLink
      priceMin
      priceMax
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
"""

# Variáveis para a query de ofertas
VARIABLES_PRODUCT_OFFERS = {"limit": 10}

# ============================================================
# QUERY 3: BUSCAR PRODUTOS POR PALAVRA-CHAVE
# ============================================================
QUERY_SEARCH_PRODUCTS = """
query SearchProducts($keyword: String!, $limit: Int) {
  productOfferV2(keyword: $keyword, limit: $limit) {
    nodes {
      productName
      itemId
      commissionRate
      price
      imageUrl
      shopName
      productLink
    }
    pageInfo {
      hasNextPage
    }
  }
}
"""

# Variáveis para a query de busca
VARIABLES_SEARCH_PRODUCTS = {"keyword": "notebook", "limit": 5}

# ============================================================
# QUERY 4: EXPLORAR SCHEMA COMPLETO
# ============================================================
QUERY_FULL_SCHEMA = """
{
  __schema {
    queryType {
      name
      fields {
        name
        description
        type {
          name
          kind
        }
        args {
          name
          description
          type {
            name
            kind
          }
        }
      }
    }
    types {
      name
      description
      kind
      fields {
        name
        description
        type {
          name
          kind
        }
      }
    }
  }
}
"""

# ============================================================
# QUERY 5: DETALHES DO PRODUTO ESPECÍFICO
# ============================================================
QUERY_PRODUCT_DETAILS = """
query ProductDetails($itemId: String!) {
  productOfferV2(itemId: $itemId) {
    nodes {
      productName
      itemId
      commissionRate
      commission
      price
      sales
      imageUrl
      shopName
      shopId
      ratingStar
      productLink
      priceMin
      priceMax
      description
      specifications
      reviews {
        rating
        comment
        userName
        date
      }
    }
  }
}
"""

# Variáveis para detalhes do produto
VARIABLES_PRODUCT_DETAILS = {
    "itemId": "123456789"  # Substitua pelo ID real do produto
}

# ============================================================
# QUERY 6: BUSCAR PRODUTOS POR CATEGORIA
# ============================================================
QUERY_CATEGORY_PRODUCTS = """
query CategoryProducts($category: String!, $limit: Int) {
  productOfferV2(category: $category, limit: $limit) {
    nodes {
      productName
      itemId
      commissionRate
      price
      imageUrl
      shopName
      productLink
      priceMin
      priceMax
    }
    pageInfo {
      hasNextPage
    }
  }
}
"""

# Variáveis para busca por categoria
VARIABLES_CATEGORY_PRODUCTS = {"category": "electronics", "limit": 20}

# ============================================================
# QUERY 7: PRODUTOS EM PROMOÇÃO
# ============================================================
QUERY_PROMOTION_PRODUCTS = """
query PromotionProducts($limit: Int) {
  productOfferV2(limit: $limit, promotion: true) {
    nodes {
      productName
      itemId
      commissionRate
      price
      originalPrice
      discountPercentage
      imageUrl
      shopName
      productLink
      promotionEndDate
    }
    pageInfo {
      hasNextPage
    }
  }
}
"""

# Variáveis para produtos em promoção
VARIABLES_PROMOTION_PRODUCTS = {"limit": 15}

# ============================================================
# INSTRUÇÕES DE USO NO EXPLORER
# ============================================================
INSTRUCTIONS = """
🔧 COMO USAR NO EXPLORER DA SHOPEE:

1. 📱 Acesse: https://open-api.affiliate.shopee.com.br/explorer

2. 🔑 Configure suas credenciais:
   - AppId: 18330800803
   - Secret: BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4

3. 📝 Cole a query desejada no campo "Query"

4. ⚙️ Configure as variáveis no campo "Variables" (se necessário)

5. ▶️ Clique em "Play" para executar

6. 📊 Visualize os resultados no painel direito

💡 DICAS:
- Comece com QUERY_TEST_CONNECTION para verificar a conexão
- Use QUERY_FULL_SCHEMA para explorar todos os campos disponíveis
- Ajuste os valores das variáveis conforme necessário
- Copie e cole as queries diretamente no explorer
"""


# ============================================================
# EXEMPLO DE USO RÁPIDO
# ============================================================
def print_queries_for_explorer():
    """Imprime todas as queries formatadas para uso no explorer"""

    print("=" * 80)
    print("🚀 QUERIES GRAPHQL PARA O EXPLORER DA SHOPEE")
    print("=" * 80)
    print()

    print("1️⃣ QUERY DE TESTE (Cole no explorer):")
    print("-" * 50)
    print(QUERY_TEST_CONNECTION)
    print()

    print("2️⃣ QUERY DE OFERTAS (Cole no explorer):")
    print("-" * 50)
    print(QUERY_PRODUCT_OFFERS)
    print()

    print("3️⃣ VARIÁVEIS PARA OFERTAS (Cole no campo Variables):")
    print("-" * 50)
    print(json.dumps(VARIABLES_PRODUCT_OFFERS, indent=2))
    print()

    print("4️⃣ QUERY DE BUSCA (Cole no explorer):")
    print("-" * 50)
    print(QUERY_SEARCH_PRODUCTS)
    print()

    print("5️⃣ VARIÁVEIS PARA BUSCA (Cole no campo Variables):")
    print("-" * 50)
    print(json.dumps(VARIABLES_SEARCH_PRODUCTS, indent=2))
    print()

    print("=" * 80)
    print("📱 ACESSE: https://open-api.affiliate.shopee.com.br/explorer")
    print("=" * 80)


if __name__ == "__main__":
    import json

    print_queries_for_explorer()
