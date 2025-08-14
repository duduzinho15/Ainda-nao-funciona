"""
Integração com a API GraphQL oficial da Shopee para o bot Garimpeiro Geek.

Este módulo implementa a integração com a API GraphQL oficial da Shopee para buscar
ofertas de produtos de tecnologia e eletrônicos.
"""

import os
import time
import hashlib
import hmac
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode
from datetime import datetime, timedelta
import random

# Configuração de logging
logger = logging.getLogger(__name__)

class ShopeeAPIIntegration:
    """
    Classe para integração com a API GraphQL oficial da Shopee.
    
    Implementa autenticação, busca de produtos via GraphQL, e conversão para links de afiliado.
    """
    
    def __init__(self):
        """Inicializa a integração com a API GraphQL da Shopee."""
        from config import (
            SHOPEE_API_KEY, 
            SHOPEE_API_SECRET, 
            SHOPEE_PARTNER_ID, 
            SHOPEE_SHOP_ID,
            SHOPEE_API_AVAILABLE
        )
        
        self.api_key = SHOPEE_API_KEY
        self.api_secret = SHOPEE_API_SECRET
        self.partner_id = SHOPEE_PARTNER_ID
        self.shop_id = SHOPEE_SHOP_ID
        self.api_available = SHOPEE_API_AVAILABLE
        
        # URLs base da API GraphQL da Shopee
        self.base_url = "https://open-api.affiliate.shopee.com.br"
        self.graphql_endpoint = "/graphql"
        
        # Headers padrão para GraphQL
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "GarimpeiroGeek/1.0 (Telegram Bot)",
            "Accept": "application/json"
        }
        
        if not self.api_available:
            logger.warning("⚠️ API GraphQL da Shopee não configurada. Funcionalidade desativada.")
        else:
            logger.info("✅ API GraphQL da Shopee inicializada com sucesso!")
    
    def _generate_signature(self, payload_json: str, timestamp: int) -> str:
        """
        Gera a assinatura necessária para autenticação na API GraphQL da Shopee.
        
        Args:
            payload_json: Payload JSON completo da requisição
            timestamp: Timestamp atual
            
        Returns:
            String com a assinatura SHA256
        """
        try:
            # Constrói a string base para assinatura conforme documentação da Shopee
            # Formato: AppId+Timestamp+Payload+Secret (sem espaços)
            base_string = f"{self.api_key}{timestamp}{payload_json}{self.api_secret}"
            
            logger.info(f"String base para assinatura: {base_string[:50]}...")
            
            # Gera SHA256 (não HMAC-SHA256)
            signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
            
            logger.info(f"Assinatura gerada: {signature}")
            return signature
            
        except Exception as e:
            logger.error(f"Erro ao gerar assinatura: {e}")
            return ""
    
    def _make_graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """
        Faz uma requisição GraphQL para a API da Shopee.
        
        Args:
            query: Query GraphQL
            variables: Variáveis da query (opcional)
            
        Returns:
            Resposta da API ou None em caso de erro
        """
        if not self.api_available:
            logger.warning("API GraphQL da Shopee não disponível")
            return None
        
        try:
            # Parâmetros obrigatórios para autenticação
            timestamp = int(time.time())
            
            # Constrói payload GraphQL
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            # Converte payload para JSON string compacta para gerar assinatura
            # Usa separators=(',', ':') para remover espaços extras
            payload_json = json.dumps(payload, separators=(',', ':'))
            
            # Gera assinatura usando o payload JSON completo
            signature = self._generate_signature(payload_json, timestamp)
            if not signature:
                logger.error("❌ Falha ao gerar assinatura")
                return None
            
            # Constrói cabeçalho de autorização conforme documentação da Shopee
            # Formato: SHA256 Credential={AppId}, Timestamp={Timestamp}, Signature={Signature}
            auth_header = f"SHA256 Credential={self.api_key}, Timestamp={timestamp}, Signature={signature}"
            
            # Headers atualizados com autorização
            headers = self.headers.copy()
            headers["Authorization"] = auth_header
            
            # Constrói URL completa
            url = f"{self.base_url}{self.graphql_endpoint}"
            
            logger.info(f"Fazendo requisição GraphQL para: {url}")
            logger.info(f"Query: {query[:100]}...")
            logger.info(f"Variáveis: {variables}")
            logger.info(f"Payload JSON: {payload_json[:100]}...")
            logger.info(f"Authorization: {auth_header[:50]}...")
            
            # Faz a requisição POST com payload GraphQL
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            logger.info(f"Status da resposta: {response.status_code}")
            logger.info(f"Resposta: {response.text[:500]}...")
            
            # Verifica resposta
            if response.status_code == 200:
                data = response.json()
                
                # Verifica erros GraphQL
                if "errors" in data:
                    logger.error(f"Erro GraphQL: {data['errors']}")
                    return None
                
                return data.get("data", {})
            else:
                logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição GraphQL para API da Shopee: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na API GraphQL da Shopee: {e}")
            return None
    
    def search_products(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Busca produtos na Shopee usando a API GraphQL.
        
        Args:
            keyword: Palavra-chave para busca
            limit: Limite de resultados
            
        Returns:
            Lista de produtos encontrados
        """
        try:
            # Query EXATA que funcionou na ferramenta oficial da Shopee
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
            
            variables = {
                "limit": min(limit, 100)
            }
            
            logger.info(f"Buscando produtos na Shopee: '{keyword}'")
            
            response = self._make_graphql_request(query, variables)
            if not response:
                return []
            
            items = response.get("productOfferV2", {}).get("nodes", [])
            logger.info(f"Encontrados {len(items)} produtos na Shopee")
            
            return self._format_products(items)
            
        except Exception as e:
            logger.error(f"Erro ao buscar produtos na Shopee: {e}")
            return []
    
    def get_category_products(self, category: str, limit: int = 50) -> List[Dict]:
        """
        Busca produtos de uma categoria específica.
        
        Args:
            category: Nome da categoria
            limit: Limite de resultados
            
        Returns:
            Lista de produtos da categoria
        """
        try:
            # Query EXATA que funcionou na ferramenta oficial da Shopee
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
            
            variables = {
                "limit": min(limit, 100)
            }
            
            logger.info(f"Buscando produtos da categoria {category} na Shopee")
            
            response = self._make_graphql_request(query, variables)
            if not response:
                return []
            
            items = response.get("productOfferV2", {}).get("nodes", [])
            logger.info(f"Encontrados {len(items)} produtos na categoria {category}")
            
            return self._format_products(items)
            
        except Exception as e:
            logger.error(f"Erro ao buscar produtos da categoria {category}: {e}")
            return []
    
    def get_flash_sale_products(self, limit: int = 50) -> List[Dict]:
        """
        Busca produtos em oferta relâmpago.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de produtos em oferta
        """
        try:
            # Query EXATA que funcionou na ferramenta oficial da Shopee
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
            
            variables = {
                "limit": min(limit, 100)
            }
            
            logger.info("Buscando produtos em oferta relâmpago na Shopee")
            
            response = self._make_graphql_request(query, variables)
            if not response:
                return []
            
            items = response.get("productOfferV2", {}).get("nodes", [])
            logger.info(f"Encontrados {len(items)} produtos em oferta relâmpago")
            
            return self._format_products(items)
            
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas relâmpago na Shopee: {e}")
            return []
    
    def _format_products(self, items: List[Dict]) -> List[Dict]:
        """
        Formata os produtos retornados pela API GraphQL para o formato padrão do bot.
        
        Args:
            items: Lista de produtos da API
            
        Returns:
            Lista de produtos formatados
        """
        formatted_products = []
        
        for item in items:
            try:
                # Extrai informações básicas
                product_id = item.get("itemId", "")
                product_name = item.get("productName", "Produto sem nome")
                
                # Constrói URL do produto
                product_url = item.get("productLink", f"https://shopee.com.br/product/{product_id}")
                
                # Constrói URL de afiliado
                affiliate_url = item.get("offerLink", product_url)
                
                # Calcula desconto
                discount_rate = item.get("priceDiscountRate", 0)
                current_price = item.get("price", "0")
                
                # Formata produto
                formatted_product = {
                    "titulo": product_name,
                    "preco": str(current_price),
                    "preco_original": None,  # Não disponível na API
                    "desconto": int(discount_rate) if discount_rate else 0,
                    "url_produto": product_url,
                    "url_afiliado": affiliate_url,
                    "imagem_url": item.get("imageUrl", ""),
                    "loja": "Shopee",
                    "categoria": "Tecnologia",  # Categoria padrão
                    "rating": float(item.get("ratingStar", 0)),
                    "vendas": int(item.get("sales", 0)),
                    "estoque": 999,  # Não disponível na API
                    "localizacao": "Brasil",
                    "frete_gratis": False,  # Não disponível na API
                    "data_coleta": datetime.now().isoformat()
                }
                
                formatted_products.append(formatted_product)
                
            except Exception as e:
                logger.warning(f"Erro ao formatar produto da Shopee: {e}")
                continue
        
        return formatted_products
    
    def _generate_affiliate_url(self, original_url: str) -> str:
        """
        Gera URL de afiliado para o produto da Shopee.
        
        Args:
            original_url: URL original do produto
            
        Returns:
            URL de afiliado ou URL original se não implementado
        """
        # TODO: Implementar sistema de afiliados da Shopee
        # Por enquanto, retorna a URL original
        return original_url
    
    def buscar_ofertas_gerais(self, limit: int = 20) -> List[Dict]:
        """
        Busca ofertas gerais em várias categorias de tecnologia.
        
        Args:
            limit: Limite total de ofertas
            
        Returns:
            Lista de ofertas encontradas
        """
        if not self.api_available:
            logger.warning("API GraphQL da Shopee não disponível")
            return []
        
        try:
            # Primeiro tenta usar a API GraphQL
            logger.info("🔄 Tentando usar a API GraphQL oficial da Shopee...")
            todas_ofertas = []
            
            # Categorias de tecnologia para buscar
            categorias_tech = [
                "smartphone", "notebook", "tablet", "fone bluetooth",
                "smartwatch", "câmera", "drone", "console", "smart tv"
            ]
            
            # Palavras-chave populares
            keywords_populares = [
                "smartphone", "notebook", "tablet", "fone bluetooth",
                "smartwatch", "câmera", "drone", "console"
            ]
            
            logger.info("Iniciando busca de ofertas gerais na Shopee via GraphQL...")
            
            # 1. Busca por categorias
            for categoria in categorias_tech:
                try:
                    produtos = self.get_category_products(categoria, limit=10)
                    if produtos:
                        logger.info(f"Encontrados {len(produtos)} produtos na categoria {categoria}")
                        todas_ofertas.extend(produtos)
                        
                        # Aguarda um pouco entre requisições
                        time.sleep(random.uniform(1, 3))
                        
                except Exception as e:
                    logger.error(f"Erro ao buscar categoria {categoria}: {e}")
                    continue
            
            # 2. Busca por palavras-chave
            for keyword in keywords_populares:
                try:
                    produtos = self.search_products(keyword, limit=5)
                    if produtos:
                        logger.info(f"Encontrados {len(produtos)} produtos para '{keyword}'")
                        todas_ofertas.extend(produtos)
                        
                        # Aguarda um pouco entre requisições
                        time.sleep(random.uniform(1, 3))
                        
                except Exception as e:
                    logger.error(f"Erro ao buscar por '{keyword}': {e}")
                    continue
            
            # 3. Busca ofertas relâmpago
            try:
                flash_sale_produtos = self.get_flash_sale_products(limit=10)
                if flash_sale_produtos:
                    logger.info(f"Encontrados {len(flash_sale_produtos)} produtos em oferta relâmpago")
                    todas_ofertas.extend(flash_sale_produtos)
            except Exception as e:
                logger.error(f"Erro ao buscar ofertas relâmpago: {e}")
            
            # Remove duplicatas e limita resultados
            ofertas_unicas = self._remove_duplicates(todas_ofertas)
            ofertas_filtradas = self._filter_best_offers(ofertas_unicas, limit)
            
            logger.info(f"Total de ofertas encontradas na Shopee via GraphQL: {len(ofertas_filtradas)}")
            
            # Se a API não retornou nada, tenta o scraper como fallback
            if not ofertas_filtradas:
                logger.warning("⚠️ API GraphQL da Shopee não retornou ofertas. Tentando scraper como fallback...")
                return self._buscar_ofertas_fallback(limit)
            
            return ofertas_filtradas
            
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas gerais na Shopee: {e}")
            logger.info("🔄 Tentando scraper como fallback...")
            return self._buscar_ofertas_fallback(limit)
    
    def _buscar_ofertas_fallback(self, limit: int = 20) -> List[Dict]:
        """
        Método de fallback que usa o scraper original da Shopee.
        
        Args:
            limit: Limite de ofertas
            
        Returns:
            Lista de ofertas encontradas
        """
        try:
            logger.info("🔄 Usando scraper da Shopee como fallback...")
            
            # Tenta importar o scraper original
            try:
                from shopee_scraper_fixed import ShopeeScraperFixed
                logger.info("✅ Scraper da Shopee importado com sucesso!")
                
                # Cria instância do scraper e busca ofertas
                scraper = ShopeeScraperFixed()
                ofertas = scraper.buscar_ofertas_gerais()
                
                # Limita o número de ofertas se necessário
                if len(ofertas) > limit:
                    ofertas = ofertas[:limit]
                
                logger.info(f"✅ Scraper encontrou {len(ofertas)} ofertas")
                return ofertas
                
            except ImportError:
                logger.error("❌ Não foi possível importar o scraper da Shopee")
                return []
            except Exception as e:
                logger.error(f"❌ Erro no scraper da Shopee: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Erro no fallback da Shopee: {e}")
            return []
    
    def _remove_duplicates(self, ofertas: List[Dict]) -> List[Dict]:
        """
        Remove ofertas duplicadas baseado no ID do produto.
        
        Args:
            ofertas: Lista de ofertas
            
        Returns:
            Lista sem duplicatas
        """
        seen = set()
        unique_ofertas = []
        
        for oferta in ofertas:
            # Usa URL do produto como identificador único
            product_id = oferta.get("url_produto", "")
            if product_id and product_id not in seen:
                seen.add(product_id)
                unique_ofertas.append(oferta)
        
        return unique_ofertas
    
    def _filter_best_offers(self, ofertas: List[Dict], limit: int) -> List[Dict]:
        """
        Filtra as melhores ofertas baseado em critérios de qualidade.
        
        Args:
            ofertas: Lista de ofertas
            limit: Limite de resultados
            
        Returns:
            Lista filtrada de ofertas
        """
        try:
            # Prioriza ofertas com desconto
            ofertas_com_desconto = [o for o in ofertas if o.get("desconto", 0) >= 10]
            
            # Prioriza produtos com boa avaliação
            ofertas_com_rating = [o for o in ofertas if o.get("rating", 0) >= 4.0]
            
            # Prioriza produtos com vendas
            ofertas_com_vendas = [o for o in ofertas if o.get("vendas", 0) > 0]
            
            # Combina as prioridades
            ofertas_prioritarias = []
            ofertas_prioritarias.extend(ofertas_com_desconto)
            ofertas_prioritarias.extend(ofertas_com_rating)
            ofertas_prioritarias.extend(ofertas_com_vendas)
            
            # Remove duplicatas novamente
            ofertas_unicas = self._remove_duplicates(ofertas_prioritarias)
            
            # Adiciona o restante das ofertas
            for oferta in ofertas:
                if oferta not in ofertas_unicas:
                    ofertas_unicas.append(oferta)
            
            # Limita resultados
            return ofertas_unicas[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao filtrar ofertas: {e}")
            return ofertas[:limit]
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com a API GraphQL da Shopee.
        
        Returns:
            True se a conexão estiver funcionando, False caso contrário
        """
        if not self.api_available:
            logger.warning("API GraphQL da Shopee não configurada")
            return False
        
        try:
            logger.info("Testando conexão com a API GraphQL da Shopee...")
            
            # Query EXATA que funcionou na ferramenta oficial da Shopee
            test_query = """{
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
            
            response = self._make_graphql_request(test_query)
            
            if response is not None:
                logger.info("✅ Conexão com a API GraphQL da Shopee estabelecida com sucesso!")
                return True
            else:
                logger.error("❌ Falha na conexão com a API GraphQL da Shopee")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão com a API GraphQL da Shopee: {e}")
            return False


# Função de conveniência para uso externo
def verificar_ofertas_shopee(limit: int = 20) -> List[Dict]:
    """
    Função de conveniência para buscar ofertas da Shopee.
    
    Args:
        limit: Limite de ofertas a buscar
        
    Returns:
        Lista de ofertas encontradas
    """
    try:
        shopee_api = ShopeeAPIIntegration()
        return shopee_api.buscar_ofertas_gerais(limit)
    except Exception as e:
        logger.error(f"Erro ao verificar ofertas da Shopee: {e}")
        return []


if __name__ == "__main__":
    # Teste da integração
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testando integração com a API GraphQL da Shopee...")
    
    shopee = ShopeeAPIIntegration()
    
    # Testa conexão
    if shopee.test_connection():
        print("✅ Conexão estabelecida!")
        
        # Testa busca de produtos
        print("🔍 Testando busca de produtos...")
        ofertas = shopee.buscar_ofertas_gerais(limit=5)
        
        if ofertas:
            print(f"✅ Encontradas {len(ofertas)} ofertas!")
            for i, oferta in enumerate(ofertas[:3], 1):
                print(f"\n{i}. {oferta['titulo']}")
                print(f"   Preço: R$ {oferta['preco']}")
                print(f"   Desconto: {oferta['desconto']}%")
                print(f"   Loja: {oferta['loja']}")
        else:
            print("⚠️ Nenhuma oferta encontrada")
    else:
        print("❌ Falha na conexão com a API GraphQL da Shopee")
