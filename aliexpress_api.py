"""
Módulo para integração com a API de Afiliados do AliExpress.

Documentação da API: https://developers.aliexpress.com/en/doc.htm?docId=108975&docType=1
"""
import hashlib
import hmac
import json
import logging
import os
import re
import time
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests

# Tenta importar do config.py, mas usa variáveis de ambiente como fallback
try:
    from config import (
        ALIEXPRESS_APP_KEY,
        ALIEXPRESS_APP_SECRET,
        ALIEXPRESS_TRACKING_ID
    )
except (ImportError, AttributeError):
    # Se não conseguir importar do config.py, usa variáveis de ambiente
    ALIEXPRESS_APP_KEY = os.getenv('ALIEXPRESS_APP_KEY')
    ALIEXPRESS_APP_SECRET = os.getenv('ALIEXPRESS_APP_SECRET')
    ALIEXPRESS_TRACKING_ID = os.getenv('ALIEXPRESS_TRACKING_ID')

# Configuração de logging
logger = logging.getLogger('garimpeiro_bot.ali_api')

class AliExpressAPIError(Exception):
    """Exceção para erros na API do AliExpress."""
    pass

class AliExpressAPI:
    """Classe para interagir com a API de Afiliados do AliExpress."""
    
    # URL base da API do AliExpress Affiliate
    # Documentação: https://developers.aliexpress.com/en/doc.htm?docId=118192&docType=1
    BASE_URL = "https://api-sg.aliexpress.com/sync"  # Endpoint de produção
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Versão da API
    API_VERSION = "2.0"
    
    # Formato de resposta
    RESPONSE_FORMAT = "json"
    
    # Método de assinatura
    SIGN_METHOD = "md5"
    
    # Tipos de link de promoção
    PROMOTION_LINK_TYPES = {
        'universal': '0',       # Universal Link
        'deep': '1',            # Deep Link
        'universal_coupon': '2' # Universal Link with coupon
    }
    
    def __init__(self, app_key: str = None, app_secret: str = None, tracking_id: str = None):
        """Inicializa a API do AliExpress com as credenciais fornecidas.
        
        Args:
            app_key: Chave do aplicativo (AppKey)
            app_secret: Segredo do aplicativo (App Secret)
            tracking_id: ID de rastreamento (Tracking ID)
            
        Raises:
            ValueError: Se alguma credencial estiver faltando
        """
        self.app_key = app_key or ALIEXPRESS_APP_KEY
        self.app_secret = app_secret or ALIEXPRESS_APP_SECRET
        self.tracking_id = tracking_id or ALIEXPRESS_TRACKING_ID
        
        # Verifica se todas as credenciais foram fornecidas
        missing_creds = []
        if not self.app_key:
            missing_creds.append('app_key')
        if not self.app_secret:
            missing_creds.append('app_secret')
        if not self.tracking_id:
            missing_creds.append('tracking_id')
            
        if missing_creds:
            raise ValueError(
                f"Credenciais ausentes: {', '.join(missing_creds)}. "
                "Por favor, forneça as credenciais diretamente ou defina as variáveis de ambiente: "
                "ALIEXPRESS_APP_KEY, ALIEXPRESS_APP_SECRET, ALIEXPRESS_TRACKING_ID"
            )
            
        logger.info("API do AliExpress inicializada com sucesso")
    
    def _generate_signature(self, params: Dict[str, str]) -> str:
        """Gera a assinatura para autenticação na API.
        
        A assinatura é gerada usando o método MD5, conforme documentação da API.
        
        Args:
            params: Dicionário com os parâmetros da requisição
            
        Returns:
            String com a assinatura gerada em maiúsculas
        """
        # Ordena os parâmetros por chave
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # Concatena os parâmetros no formato chave+valor
        string_to_sign = self.app_secret
        for key, value in sorted_params:
            if value is not None:
                string_to_sign += f"{key}{value}"
        string_to_sign += self.app_secret
        
        logger.debug(f"String para assinatura: {string_to_sign}")
        logger.debug(f"App Secret: {self.app_secret}")
        logger.debug(f"App Key: {self.app_key}")
        logger.debug(f"Tracking ID: {self.tracking_id}")
        
        # Calcula o MD5 (método padrão da API do AliExpress)
        signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest().upper()
        logger.debug(f"Assinatura gerada: {signature}")
        
        return signature
    
    def _make_request(self, method: str, params: Dict[str, str]) -> Dict:
        """Faz uma requisição para a API do AliExpress.
        
        Args:
            method: Nome do método da API a ser chamado
            params: Dicionário com os parâmetros da requisição
            
        Returns:
            Dicionário com a resposta da API
            
        Raises:
            AliExpressAPIError: Em caso de erro na requisição
        """
        # Adiciona parâmetros padrão
        timestamp = datetime.now().strftime(self.TIMESTAMP_FORMAT)
        
        # Parâmetros base obrigatórios para a API
        base_params = {
            'app_key': self.app_key,
            'method': method,
            'timestamp': timestamp,
            'format': self.RESPONSE_FORMAT,
            'v': self.API_VERSION,
            'sign_method': self.SIGN_METHOD,
            'partner_id': 'garimpeiro_geek',
        }
        
        logger.debug(f"Método: {method}")
        logger.debug(f"Parâmetros base: {base_params}")
        logger.debug(f"Parâmetros do método: {params}")
        
        # Adiciona parâmetros específicos do método
        all_params = {**base_params, **params}
        
        # Remove parâmetros vazios
        all_params = {k: v for k, v in all_params.items() if v is not None}
        
        # Gera a assinatura
        signature = self._generate_signature(all_params)
        all_params['sign'] = signature
        
        logger.debug(f"Método: {method}")
        logger.debug(f"Parâmetros base: {base_params}")
        logger.debug(f"Parâmetros do método: {params}")
        logger.debug(f"Parâmetros finais: {all_params}")
        logger.debug(f"Assinatura gerada: {signature}")
        
        try:
            # URL completa para depuração
            full_url = f"{self.BASE_URL}?" + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in all_params.items()])
            logger.debug(f"URL da requisição: {full_url}")
            
            # Faz a requisição (POST é o método recomendado pela documentação)
            logger.info(f"Enviando requisição para: {method}")
            logger.debug(f"Parâmetros: {all_params}")
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
            }
            
            start_time = time.time()
            response = requests.post(
                self.BASE_URL, 
                data=all_params, 
                headers=headers, 
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            logger.debug(f"Resposta recebida em {elapsed_time:.2f}s")
            logger.debug(f"Status code: {response.status_code}")
            logger.debug(f"Cabeçalhos da resposta: {response.headers}")
            
            # Verifica o status da resposta
            response.raise_for_status()
            
            # Tenta decodificar o JSON da resposta
            try:
                result = response.json()
                logger.debug(f"Resposta JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON da resposta: {e}")
                logger.error(f"Conteúdo da resposta: {response.text[:1000]}...")
                raise AliExpressAPIError(f"Resposta inválida da API: {str(e)}")
            
            # Verifica se há erros na resposta
            if 'error_response' in result:
                error = result['error_response']
                error_msg = f"Erro na API do AliExpress: {error.get('msg', 'Erro desconhecido')} (Código: {error.get('code', 'N/A')})"
                logger.error(error_msg)
                logger.debug(f"Resposta completa de erro: {json.dumps(error, indent=2, ensure_ascii=False)}")
                raise AliExpressAPIError(error_msg)
                
            # Retorna o primeiro resultado disponível (removendo o wrapper da resposta)
            if not result:
                raise AliExpressAPIError("Resposta vazia da API")
                
            # Verifica se há resultados válidos
            result_key = next(iter(result.keys())) if isinstance(result, dict) else None
            if not result_key or not result[result_key]:
                raise AliExpressAPIError(f"Resposta inválida da API: {result}")
                
            return result[result_key]
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro na requisição para a API do AliExpress: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AliExpressAPIError(error_msg) from e
    
    def get_product_info(self, product_id: str, country: str = 'BR', language: str = 'pt') -> Dict:
        """Obtém informações detalhadas de um produto pelo ID.
        
        Args:
            product_id: ID do produto no AliExpress
            country: Código do país (padrão: 'BR')
            language: Idioma (padrão: 'pt')
            
        Returns:
            Dicionário com as informações do produto
            
        Raises:
            AliExpressAPIError: Se ocorrer um erro na requisição
        """
        params = {
            'product_ids': product_id,
            'target_currency': 'BRL',
            'target_language': language.upper(),
            'tracking_id': self.tracking_id,
            'country': country.upper(),
            'promotion_link_type': self.PROMOTION_LINK_TYPES['universal']  # Adiciona o tipo de link de promoção
        }
        
        return self._make_request('aliexpress.affiliate.productdetail.get', params)
    
    def get_promotion_links(self, urls: List[str], country: str = 'BR', link_type: str = 'universal') -> List[Dict]:
        """Gera links de afiliado para uma lista de URLs de produtos.
        
        Args:
            urls: Lista de URLs de produtos do AliExpress
            country: Código do país (padrão: 'BR')
            link_type: Tipo de link de promoção ('universal', 'deep', 'universal_coupon')
            
        Returns:
            Lista de dicionários com os links de afiliado gerados
            
        Raises:
            ValueError: Se o tipo de link não for válido
            AliExpressAPIError: Se ocorrer um erro na requisição
        """
        if not urls:
            return []
            
        # Valida o tipo de link
        if link_type not in self.PROMOTION_LINK_TYPES:
            raise ValueError(f"Tipo de link inválido. Use um dos seguintes: {', '.join(self.PROMOTION_LINK_TYPES.keys())}")
            
        # Converte a lista de URLs em uma string separada por vírgulas
        source_values = ','.join(urls)
        
        params = {
            'source_values': source_values,
            'tracking_id': self.tracking_id,
            'country': country.upper(),
            'promotion_link_type': self.PROMOTION_LINK_TYPES[link_type],
            'target_currency': 'BRL',
            'target_language': 'PT'  # Idioma fixo para português
        }
        
        # O método correto para gerar links de afiliado
        result = self._make_request('aliexpress.affiliate.link.generate', params)
        return result.get('promotion_links', {}).get('promotion_link', [])
    
    def search_products(
        self,
        keywords: str,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: str = 'SALE_PRICE_DESC',
        page_no: int = 1,
        page_size: int = 20,
        country: str = 'BR',
        language: str = 'pt',
        link_type: str = 'universal'
    ) -> Dict:
        """Busca produtos no AliExpress com base em palavras-chave.
        
        Args:
            keywords: Palavras-chave para busca
            category_id: ID da categoria para filtrar (opcional)
            min_price: Preço mínimo (opcional)
            max_price: Preço máximo (opcional)
            sort: Critério de ordenação (padrão: 'SALE_PRICE_DESC')
            page_no: Número da página (padrão: 1)
            page_size: Itens por página (padrão: 20, máximo: 50)
            country: Código do país (padrão: 'BR')
            language: Idioma (padrão: 'pt')
            
        Returns:
            Dicionário com os resultados da busca
        """
        params = {
            'keywords': keywords,
            'sort': sort,
            'page_no': str(page_no),
            'page_size': str(min(page_size, 50)),  # Limita a 50 itens por página
            'target_currency': 'BRL',
            'target_language': language.upper(),
            'ship_to_country': country.upper(),
            'tracking_id': self.tracking_id,
            'promotion_link_type': self.PROMOTION_LINK_TYPES.get(link_type, '0')  # Tipo de link de promoção
        }
        
        # Adiciona parâmetros opcionais
        if category_id:
            params['category_ids'] = category_id
        if min_price is not None:
            params['min_sale_price'] = str(min_price)
        if max_price is not None:
            params['max_sale_price'] = str(max_price)
        
        return self._make_request('aliexpress.affiliate.product.query', params)


def extract_product_id(url: str) -> Optional[str]:
    """Extrai o ID do produto de uma URL do AliExpress.
    
    Args:
        url: URL do produto no AliExpress
        
    Returns:
        ID do produto ou None se não encontrado
        
    Exemplos:
        >>> extract_product_id('https://pt.aliexpress.com/item/10050012345678.html')
        '10050012345678'
        >>> extract_product_id('https://pt.aliexpress.com/i/10050012345678.html')
        '10050012345678'
        >>> extract_product_id('https://www.aliexpress.com/item/10050012345678.html')
        '10050012345678'
        >>> extract_product_id('https://www.aliexpress.com/item//10050012345678.html')
        '10050012345678'
    """
    """Extrai o ID do produto de uma URL do AliExpress.
    
    Args:
        url: URL do produto no AliExpress
        
    Returns:
        ID do produto ou None se não encontrado
    """
    if not url or 'aliexpress.com' not in url:
        return None
    
    # Tenta extrair o ID da URL
    patterns = [
        r'/item/(\d+)\.html',
        r'/i/(\d+)\.html',
        r'/(\d+)\.html',
        r'productId=(\d+)',
        r'/(\d+)_\d+\.html'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def format_product_info(product_data: Dict) -> Dict:
    """Formata os dados do produto para um formato padronizado.
    
    Args:
        product_data: Dicionário com os dados brutos do produto
        
    Returns:
        Dicionário com os dados formatados
    """
    if not product_data or 'result' not in product_data:
        return {}
    
    result = product_data['result']
    
    # Extrai informações básicas
    product = {
        'title': result.get('product_title', ''),
        'product_id': result.get('product_id', ''),
        'url': result.get('product_detail_url', ''),
        'image_url': result.get('product_main_image_url', ''),
        'price': result.get('target_sale_price', ''),
        'original_price': result.get('target_original_price', ''),
        'currency': result.get('target_currency', 'BRL'),
        'discount': result.get('discount', ''),
        'rating': result.get('evaluate_rate', ''),
        'orders': result.get('lastest_volume', 0),
        'store_name': result.get('shop_name', ''),
        'store_url': result.get('shop_url', ''),
        'available': result.get('inventory', 0) > 0,
        'category': result.get('category_name', ''),
        'category_id': result.get('category_id', ''),
        'shipping_info': {
            'free_shipping': result.get('free_shipping', False),
            'ship_from': result.get('ship_from', ''),
            'delivery_days': result.get('delivery_days', '')
        },
        'promotion_info': {
            'promotion_volume': result.get('promotion_volume', 0),
            'promotion_price': result.get('promotion_price', ''),
            'promotion_percentage': result.get('promotion_percentage', 0)
        }
    }
    
    return product
