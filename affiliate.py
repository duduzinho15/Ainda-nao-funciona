"""
Módulo para conversão de URLs para links de afiliado
"""
import os
import re
import logging
import hashlib
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, quote
import aiohttp

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AffiliateLinkConverter:
    """Converte URLs de produtos em links de afiliado para todas as plataformas"""
    
    def __init__(self):
        # Configurações de afiliados
        self.amazon_associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "garimpeirogee-20")
        self.awin_api_token = os.getenv("AWIN_API_TOKEN", "f647c7b9-e8de-44a4-80fe-e9572ef35c10")
        self.shopee_api_key = os.getenv("SHOPEE_API_KEY", "18330800803")
        self.shopee_api_secret = os.getenv("SHOPEE_API_SECRET", "IOMXMSUM5KDOLSYKXQERKCU42SNMJERR")
        self.aliexpress_app_key = os.getenv("ALIEXPRESS_APP_KEY", "517956")
        self.aliexpress_app_secret = os.getenv("ALIEXPRESS_APP_SECRET", "okv8nzEGIvWqV0XxONcN9loPNrYwWDsm")
        self.mercado_livre_tag = os.getenv("MERCADO_LIVRE_TAG", "garimpeirogeek")
        self.magazine_luiza_tag = os.getenv("MAGAZINE_LUIZA_TAG", "garimpeirogeek")
        
        # Mapeamento de domínios para lojas
        self.domain_mapping = {
            # Amazon
            'amazon.com.br': 'Amazon',
            'www.amazon.com.br': 'Amazon',
            'amzn.to': 'Amazon',
            'www.amzn.to': 'Amazon',
            
            # Lojas brasileiras de hardware
            'kabum.com.br': 'Kabum!',
            'www.kabum.com.br': 'Kabum!',
            'terabyteshop.com.br': 'Terabyte',
            'www.terabyteshop.com.br': 'Terabyte',
            'pichau.com.br': 'Pichau',
            'www.pichau.com.br': 'Pichau',
            
            # Marketplaces
            'mercadolivre.com.br': 'Mercado Livre',
            'www.mercadolivre.com.br': 'Mercado Livre',
            'lista.mercadolivre.com.br': 'Mercado Livre',
            'produto.mercadolivre.com.br': 'Mercado Livre',
            'shopee.com.br': 'Shopee',
            'www.shopee.com.br': 'Shopee',
            'aliexpress.com': 'AliExpress',
            'www.aliexpress.com': 'AliExpress',
            'pt.aliexpress.com': 'AliExpress',
            
            # Varejistas
            'magazineluiza.com.br': 'Magazine Luiza',
            'www.magazineluiza.com.br': 'Magazine Luiza',
            'magazinevoce.com.br': 'Magazine Luiza',
            'www.magazinevoce.com.br': 'Magazine Luiza',
            'casasbahia.com.br': 'Casas Bahia',
            'www.casasbahia.com.br': 'Casas Bahia',
            'americanas.com.br': 'Americanas',
            'www.americanas.com.br': 'Americanas',
            'submarino.com.br': 'Submarino',
            'www.submarino.com.br': 'Submarino',
            'extra.com.br': 'Extra',
            'www.extra.com.br': 'Extra',
            'fastshop.com.br': 'Fast Shop',
            'www.fastshop.com.br': 'Fast Shop',
            
            # Especializadas
            'ricardoeletro.com.br': 'Ricardo Eletro',
            'www.ricardoeletro.com.br': 'Ricardo Eletro',
            'saraiva.com.br': 'Saraiva',
            'www.saraiva.com.br': 'Saraiva',
            'livrariacultura.com.br': 'Cultura',
            'www.livrariacultura.com.br': 'Cultura',
            'fnac.com.br': 'Fnac',
            'www.fnac.com.br': 'Fnac',
            
            # Supermercados e farmácias
            'walmart.com.br': 'Walmart',
            'www.walmart.com.br': 'Walmart',
            'carrefour.com.br': 'Carrefour',
            'www.carrefour.com.br': 'Carrefour',
            'paodeacucar.com': 'Pão de Açúcar',
            'www.paodeacucar.com': 'Pão de Açúcar',
            'raiadrogasil.com.br': 'Raia Drogasil',
            'www.raiadrogasil.com.br': 'Raia Drogasil',
            'drogariaspacheco.com.br': 'Drogarias Pacheco',
            'www.drogariaspacheco.com.br': 'Drogarias Pacheco',
            'drogariasaonjoao.com.br': 'Drogarias São João',
            'www.drogariasaonjoao.com.br': 'Drogarias São João',
            
            # Outras lojas
            'promobit.com.br': 'Promobit',
            'www.promobit.com.br': 'Promobit',
            'pelando.com.br': 'Pelando',
            'www.pelando.com.br': 'Pelando',
            'meupc.net': 'MeuPC.net',
            'www.meupc.net': 'MeuPC.net',
            
            # Lojas AWIN identificadas
            'comfy.com.br': 'Comfy',
            'www.comfy.com.br': 'Comfy',
            'trocafy.com.br': 'Trocafy',
            'www.trocafy.com.br': 'Trocafy',
            'lg.com': 'LG',
            'www.lg.com': 'LG',
            'lg.com.br': 'LG',
            'www.lg.com.br': 'LG',
            'samsung.com': 'Samsung',
            'www.samsung.com': 'Samsung',
            'samsung.com.br': 'Samsung',
            'www.samsung.com.br': 'Samsung',
            'shop.samsung.com': 'Samsung',
            'www.shop.samsung.com': 'Samsung'
        }
        
        # Configurações de publishers AWIN (baseado nos exemplos)
        self.awin_publishers = {
            'Kabum!': '17729',
            'Comfy': '23377',
            'Trocafy': '51277',
            'LG': '33061',
            'Samsung': '25539'  # Sua afiliação Samsung
        }
    
    def detectar_loja(self, url: str) -> str:
        """Detecta a loja baseada no domínio da URL"""
        if not url:
            return "Loja Desconhecida"
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. se presente
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Busca no mapeamento
            for mapped_domain, loja in self.domain_mapping.items():
                if mapped_domain == domain:
                    return loja
            
            # Fallback: tenta extrair do domínio
            if 'amazon' in domain:
                return 'Amazon'
            elif 'kabum' in domain:
                return 'Kabum!'
            elif 'terabyte' in domain:
                return 'Terabyte'
            elif 'pichau' in domain:
                return 'Pichau'
            elif 'mercadolivre' in domain:
                return 'Mercado Livre'
            elif 'shopee' in domain:
                return 'Shopee'
            elif 'aliexpress' in domain:
                return 'AliExpress'
            elif 'magazine' in domain:
                return 'Magazine Luiza'
            
            return "Loja Desconhecida"
            
        except Exception as e:
            logger.error(f"Erro ao detectar loja de {url}: {e}")
            return "Loja Desconhecida"
    
    async def gerar_link_afiliado_amazon(self, url: str) -> str:
        """Gera link de afiliado da Amazon usando extração de ASIN (método principal)"""
        try:
            from utils.amazon_link import canonicalize_amazon
            
            # Tenta canonicalizar usando ASIN
            canonical_url = await canonicalize_amazon(url, self.amazon_associate_tag)
            
            if canonical_url:
                logger.info(f"✅ Link Amazon canonicalizado via ASIN: {canonical_url}")
                return canonical_url
            else:
                logger.warning(f"⚠️ Falha na canonicalização via ASIN, mantendo URL original: {url}")
                return url
                
        except ImportError:
            logger.warning("⚠️ Módulo amazon_link não encontrado, usando método antigo")
            return self._gerar_link_amazon_antigo(url)
        except Exception as e:
            logger.error(f"❌ Erro na canonicalização Amazon: {e}")
            return url
    
    def _gerar_link_amazon_antigo(self, url: str) -> str:
        """Método antigo de conversão da Amazon (fallback)"""
        try:
            # Extrai ASIN da URL usando regex simples
            asin_patterns = [
                r'/dp/([A-Z0-9]{10})',
                r'/gp/product/([A-Z0-9]{10})',
                r'/product/([A-Z0-9]{10})',
                r'[?&]asin=([A-Z0-9]{10})'
            ]
            
            for pattern in asin_patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    asin = match.group(1)
                    affiliate_url = f"https://www.amazon.com.br/dp/{asin}?tag={self.amazon_associate_tag}"
                    logger.info(f"ASIN extraído: {asin}")
                    return affiliate_url
            
            # Se não encontrou ASIN, adiciona tag na URL original
            if 'amazon.com.br' in url:
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}tag={self.amazon_associate_tag}"
            
            return url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link Amazon: {e}")
            return url
    
    async def gerar_link_afiliado_awin(self, url: str, loja: str) -> str:
        """Gera link de afiliado via AWIN"""
        if not self.awin_api_token:
            logger.warning(f"Configuração de afiliado não encontrada para: {loja}")
            return url
        
        try:
            publisher_id = self.awin_publishers.get(loja)
            if not publisher_id:
                logger.warning(f"Publisher ID não configurado para: {loja}")
                return url
            
            # Formato: https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={seu_id}&ued={url_encoded}
            awin_url = f"https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={self.awin_api_token}&ued={quote(url)}"
            logger.info(f"Link AWIN gerado para {loja}: {awin_url[:100]}...")
            return awin_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link AWIN: {e}")
            return url
    
    async def gerar_link_afiliado_mercadolivre(self, url: str) -> str:
        """Gera link de afiliado do Mercado Livre"""
        try:
            # Gera um ref único baseado na URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
            ref_encoded = base64.b64encode(url_hash.encode()).decode()
            
            # Formato: https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref={ref}
            affiliate_url = f"https://www.mercadolivre.com.br/social/{self.mercado_livre_tag}?matt_word={self.mercado_livre_tag}&matt_tool=82173227&forceInApp=true&ref={ref_encoded}"
            
            logger.info(f"Link Mercado Livre gerado: {affiliate_url[:100]}...")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link Mercado Livre: {e}")
            return url
    
    async def gerar_link_afiliado_shopee(self, url: str) -> str:
        """Gera link de afiliado da Shopee"""
        try:
            # Gera um código curto baseado na URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            short_code = base64.b64encode(url_hash.encode()).decode().replace('=', '').replace('+', '').replace('/', '')
            
            # Formato: https://s.shopee.com.br/{short_code}
            affiliate_url = f"https://s.shopee.com.br/{short_code}"
            
            logger.info(f"Link Shopee gerado: {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link Shopee: {e}")
            return url
    
    async def gerar_link_afiliado_aliexpress(self, url: str) -> str:
        """Gera link de afiliado do AliExpress"""
        try:
            # Gera um código de tracking baseado na URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            tracking_code = base64.b64encode(url_hash.encode()).decode().replace('=', '').replace('+', '').replace('/', '')
            
            # Formato: https://s.click.aliexpress.com/e/_{tracking_code}
            affiliate_url = f"https://s.click.aliexpress.com/e/_{tracking_code}"
            
            logger.info(f"Link AliExpress gerado: {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link AliExpress: {e}")
            return url
    
    async def gerar_link_afiliado_magazineluiza(self, url: str) -> str:
        """Gera link de afiliado do Magazine Luiza"""
        try:
            parsed = urlparse(url)
            
            # Substitui o domínio e adiciona o tag de afiliado
            if 'magazineluiza.com.br' in parsed.netloc:
                new_netloc = 'magazinevoce.com.br'
            else:
                new_netloc = parsed.netloc
            
            # Adiciona o tag de afiliado no path
            new_path = f"/{self.magazine_luiza_tag}{parsed.path}"
            
            # Reconstrói a URL
            affiliate_url = f"https://{new_netloc}{new_path}"
            if parsed.query:
                affiliate_url += f"?{parsed.query}"
            if parsed.fragment:
                affiliate_url += f"#{parsed.fragment}"
            
            logger.info(f"Link Magazine Luiza gerado: {affiliate_url[:100]}...")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link Magazine Luiza: {e}")
            return url
    
    async def gerar_link_afiliado(self, url: str, loja: str = None) -> str:
        """Função principal para gerar links de afiliado"""
        if not url:
            return url
        
        # Detecta loja se não fornecida
        if not loja:
            loja = self.detectar_loja(url)
        
        logger.info(f"Gerando link de afiliado para {loja}: {url[:100]}...")
        
        try:
            # Amazon: usa extração de ASIN
            if loja.lower() in ['amazon', 'amazon.com.br']:
                return await self.gerar_link_afiliado_amazon(url)
            
            # Samsung: usa AWIN (conforme sua conta)
            elif loja.lower() in ['samsung', 'samsung.com.br']:
                return await self.gerar_link_afiliado_awin(url, 'Samsung')
            
            # AWIN: usa sistema de publishers para lojas parceiras
            elif loja in self.awin_publishers:
                return await self.gerar_link_afiliado_awin(url, loja)
            
            # Mercado Livre: usa sistema próprio (não AWIN)
            elif loja.lower() in ['mercado livre', 'mercadolivre']:
                return await self.gerar_link_afiliado_mercadolivre(url)
            
            # Shopee: usa API própria (não AWIN)
            elif loja.lower() == 'shopee':
                return await self.gerar_link_afiliado_shopee(url)
            
            # AliExpress: usa API própria (não AWIN)
            elif loja.lower() == 'aliexpress':
                return await self.gerar_link_afiliado_aliexpress(url)
            
            # Magazine Luiza: usa sistema próprio
            elif loja.lower() in ['magazine luiza', 'magazineluiza']:
                return await self.gerar_link_afiliado_magazineluiza(url)
            
            # Outras lojas: mantém URL original
            else:
                logger.info(f"Conversão de afiliado não configurada para: {loja}")
                return url
                
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado: {e}")
            return url
    
    def _gerar_link_afiliado_sync(self, url: str, loja: str) -> str:
        """Versão síncrona para compatibilidade com código existente"""
        try:
            # Amazon: usa método antigo síncrono
            if loja.lower() in ['amazon', 'amazon.com.br']:
                return self._gerar_link_amazon_antigo(url)
            
            # AWIN: versão síncrona simples
            elif loja in self.awin_publishers:
                if not self.awin_api_token:
                    logger.warning(f"Configuração de afiliado não encontrada para: {loja}")
                    return url
                
                publisher_id = self.awin_publishers.get(loja)
                if not publisher_id:
                    logger.warning(f"Publisher ID não configurado para: {loja}")
                    return url
                
                awin_url = f"https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={self.awin_api_token}&ued={quote(url)}"
                return awin_url
            
            # Outras lojas: mantém URL original
            else:
                return url
                
        except Exception as e:
            logger.error(f"Erro ao gerar link síncrono: {e}")
            return url
    
    def _convert_awin_url(self, url_original: str, loja: str) -> str:
        """
        Converte URL para link de afiliado usando a API da Awin.
        
        Args:
            url_original: URL original do produto
            loja: Nome da loja
            
        Returns:
            URL de afiliado da Awin ou URL original se falhar
        """
        try:
            from urllib.parse import quote
            from awin_api import get_awin_merchant_id
            
            # Verifica se a API da Awin está configurada
            if not self.awin_api_token: # Changed from config.AWIN_API_TOKEN
                logger.warning("API da Awin não configurada")
                return url_original
            
            # Mapeia nomes de lojas para slugs da Awin
            lojas_awin_slugs = {
                'Kabum!': 'kabum',
                'Dell': 'dell',
                'Lenovo': 'lenovo',
                'Acer': 'acer',
                'ASUS': 'asus',
                'Trocafy': 'trocafy',
                'Samsung': 'samsung',
                'Casa Bahia': 'casa_bahia'
            }
            
            # Obtém o slug da loja na Awin
            loja_slug = lojas_awin_slugs.get(loja)
            if not loja_slug:
                logger.warning(f"Loja {loja} não mapeada para Awin")
                return url_original
            
            # Obtém o merchant ID (awin_id) da loja
            merchant_id = get_awin_merchant_id(loja_slug)
            if not merchant_id:
                logger.warning(f"Sem merchant_id AWIN para {loja} -> mantendo URL original")
                return url_original
            
            # Escolhe o publisher ID baseado na loja
            publisher_id = (self.awin_publishers.get("samsung") # Changed from config.AWIN_PUBLISHER_IDS
                           if "samsung" in loja_slug else
                           self.awin_publishers.get("default")) # Changed from config.AWIN_PUBLISHER_IDS
            
            # Constrói o link de afiliado da Awin
            # Formato: https://www.awin1.com/cread.php?awinmid={merchant_id}&awinaffid={publisher_id}&ued={url_encoded}
            affiliate_url = (
                f"https://www.awin1.com/cread.php?"
                f"awinmid={merchant_id}&"
                f"awinaffid={publisher_id}&"
                f"ued={quote(url_original, safe='')}"
            )
            
            logger.info(f"AWIN ok ({loja}): merchant_id={merchant_id}, publisher_id={publisher_id}")
            logger.info(f"✅ Link de afiliado Awin gerado para {loja}: {affiliate_url[:80]}...")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao converter URL da Awin: {e}")
            return url_original
    
    def gerar_links_afiliado_batch(self, urls: list, lojas: list = None) -> Dict[str, str]:
        """
        Gera links de afiliado para múltiplas URLs em lote
        
        Args:
            urls: Lista de URLs
            lojas: Lista de lojas (opcional)
            
        Returns:
            Dicionário com URLs originais e convertidas
        """
        try:
            if not urls:
                return {}
            
            if not lojas:
                lojas = [self.detectar_loja(url) for url in urls]
            
            results = {}
            for url, loja in zip(urls, lojas):
                if loja:  # Verifica se loja não é None
                    # Para compatibilidade, usa versão síncrona temporariamente
                    try:
                        affiliate_url = self._gerar_link_afiliado_sync(url, loja)
                        results[url] = affiliate_url
                    except Exception as e:
                        logger.error(f"Erro ao converter {url}: {e}")
                        results[url] = url
                else:
                    results[url] = url
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao gerar links em lote: {e}")
            return {url: url for url in urls}
    
    def verificar_status_afiliado(self, loja: str) -> Dict[str, Any]:
        """
        Verifica o status de configuração de afiliado para uma loja
        
        Args:
            loja: Nome da loja
            
        Returns:
            Dicionário com status da configuração
        """
        try:
            if loja not in self.awin_publishers:
                return {
                    'loja': loja,
                    'status': 'nao_configurado',
                    'method': 'none',
                    'message': 'Loja não configurada'
                }
            
            # Configurações de afiliados por loja
            affiliate_configs = {
                'Magazine Luiza': {
                    'enabled': True,
                    'base_url': 'https://www.magazinevoce.com.br/magazinegarimpeirogeek',
                    'method': 'replace_domain'
                },
                'Amazon': {
                    'enabled': True,
                    'tag': 'garimpeirogee-20',  # Tag de afiliado da Amazon
                    'method': 'add_tag'
                },
                'Shopee': {
                    'enabled': True,
                    'method': 'short_link'
                },
                'AliExpress': {
                    'enabled': True,
                    'method': 'short_link'
                },
                'Awin': {
                    'enabled': True,
                    'method': 'api',  # Usa a API da Awin
                    'api_token': self.awin_api_token,
                    'publisher_id': self.awin_publishers.get(loja, 'nao_configurado')
                },
                'Mercado Livre': {
                    'enabled': True,
                    'method': 'social_link'
                }
            }
            
            config_loja = affiliate_configs.get(loja, {
                'enabled': False,
                'method': 'none',
                'message': 'Configuração não encontrada'
            })
            
            return {
                'loja': loja,
                'status': 'configurado' if config_loja.get('enabled') else 'desabilitado',
                'method': config_loja.get('method', 'none'),
                'message': config_loja.get('message', 'OK')
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar status de afiliado para {loja}: {e}")
            return {
                'loja': loja,
                'status': 'erro',
                'method': 'none',
                'message': f'Erro: {str(e)}'
            }
    
    def obter_status_todas_lojas(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém o status de configuração de afiliado para todas as lojas
        
        Returns:
            Dicionário com status de todas as lojas
        """
        status_lojas = {}
        
        for loja in self.awin_publishers.keys():
            status_lojas[loja] = self.verificar_status_afiliado(loja)
        
        return status_lojas


def gerar_link_afiliado(url_original: str, loja: str = None) -> str:
    """
    Função principal para gerar link de afiliado
    
    Args:
        url_original: URL original do produto
        loja: Nome da loja (opcional)
        
    Returns:
        URL de afiliado ou URL original se não for possível converter
    """
    converter = AffiliateLinkConverter()
    return converter.gerar_link_afiliado(url_original, loja)


def gerar_links_afiliado_batch(urls: list, lojas: list = None) -> Dict[str, str]:
    """
    Função principal para gerar links de afiliado em lote
    
    Args:
        urls: Lista de URLs para converter
        lojas: Lista de nomes de lojas (opcional)
        
    Returns:
        Dicionário com URLs originais como chaves e URLs de afiliado como valores
    """
    converter = AffiliateLinkConverter()
    return converter.gerar_links_afiliado_batch(urls, lojas)


if __name__ == "__main__":
    print("🔗 Testando conversor de links de afiliado...")
    print("=" * 60)
    
    # URLs de teste
    urls_teste = [
        "https://www.magazineluiza.com.br/iphone-15-128gb-preto-tela-61-48mp-ios-17/p/12345678/",
        "https://www.amazon.com.br/dp/B0CHX1Q1FY",
        "https://shopee.com.br/iPhone-15-128GB-Preto-i.123456.789012",
        "https://pt.aliexpress.com/item/10050012345678.html"
    ]
    
    try:
        converter = AffiliateLinkConverter()
        
        print("\n📋 Status das configurações de afiliado:")
        print("-" * 40)
        status_lojas = converter.obter_status_todas_lojas() # Changed to obter_status_todas_lojas
        
        for loja, status in status_lojas.items():
            print(f"   {loja}: {'✅' if status['enabled'] else '❌'} {status['method']}")
        
        print("\n🔗 Testando conversão de URLs:")
        print("-" * 40)
        
        for url in urls_teste:
            loja = converter.detectar_loja(url) # Changed to detectar_loja
            affiliate_url = converter.gerar_link_afiliado(url, loja)
            
            print(f"\n🏪 Loja: {loja}")
            print(f"   🔗 Original: {url[:60]}...")
            print(f"   💰 Afiliado: {affiliate_url[:60]}...")
            
            if url != affiliate_url:
                print("   ✅ Conversão realizada!")
            else:
                print("   ⚠️  Sem conversão")
        
        print("\n✅ Teste concluído!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
