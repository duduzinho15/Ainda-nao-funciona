"""
Módulo para conversão de URLs para links de afiliado
"""
import os
import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import config

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AffiliateLinkConverter:
    """Converte URLs de produtos em links de afiliado"""
    
    def __init__(self):
        # Configurações de afiliados
        self.amazon_associate_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "garimpeirogee-20")
        self.awin_api_token = os.getenv("AWIN_API_TOKEN", "")
        
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
            'shopee.com.br': 'Shopee',
            'www.shopee.com.br': 'Shopee',
            'aliexpress.com': 'AliExpress',
            'www.aliexpress.com': 'AliExpress',
            
            # Varejistas
            'magazineluiza.com.br': 'Magazine Luiza',
            'www.magazineluiza.com.br': 'Magazine Luiza',
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
            'www.meupc.net': 'MeuPC.net'
        }
        
        # Configurações de publishers AWIN
        self.awin_publishers = {
            'Kabum!': 'seu_publisher_id_kabum',
            'Terabyte': 'seu_publisher_id_terabyte',
            'Pichau': 'seu_publisher_id_pichau',
            'Mercado Livre': 'seu_publisher_id_mercadolivre',
            'Shopee': 'seu_publisher_id_shopee',
            'AliExpress': 'seu_publisher_id_aliexpress'
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
            
            # Formato: https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={seu_id}&clickref=&p={url_encoded}
            awin_url = f"https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={self.awin_api_token}&clickref=&p={url}"
            logger.info(f"Link AWIN gerado para {loja}: {awin_url[:100]}...")
            return awin_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link AWIN: {e}")
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
            
            # AWIN: usa sistema de publishers
            elif loja in self.awin_publishers:
                return await self.gerar_link_afiliado_awin(url, loja)
            
            # Shopee: desabilitado por enquanto
            elif loja.lower() == 'shopee':
                logger.info("Conversão de afiliado desabilitada para: Shopee")
                return url
            
            # AliExpress: desabilitado por enquanto
            elif loja.lower() == 'aliexpress':
                logger.info("Conversão de afiliado desabilitada para: AliExpress")
                return url
            
            # Outras lojas: mantém URL original
            else:
                logger.info(f"Conversão de afiliado não configurada para: {loja}")
                return url
                
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado: {e}")
            return url
    
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
                
                awin_url = f"https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={self.awin_api_token}&clickref=&p={url}"
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
            if not config.AWIN_API_TOKEN:
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
            publisher_id = (config.AWIN_PUBLISHER_IDS["samsung"]
                           if "samsung" in loja_slug else
                           config.AWIN_PUBLISHER_IDS["default"])
            
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
    
    def verificar_status_afiliado(self, loja: str) -> Dict:
        """
        Verifica o status da configuração de afiliado para uma loja
        
        Args:
            loja: Nome da loja
            
        Returns:
            Dicionário com informações de status
        """
        try:
            if loja not in self.awin_publishers: # Changed to awin_publishers
                return {
                    'loja': loja,
                    'status': 'nao_configurada',
                    'enabled': False,
                    'method': 'none',
                    'message': 'Loja não configurada'
                }
            
            # Configurações de afiliados por loja
            self.affiliate_configs = {
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
                    'enabled': False,  # Por enquanto desabilitado
                    'method': 'none'
                },
                'AliExpress': {
                    'enabled': True,
                    'method': 'api'  # Usa a API do AliExpress
                },
                'Awin': {
                    'enabled': True,
                    'method': 'api',  # Usa a API da Awin
                    'api_token': config.AWIN_API_TOKEN,
                    'publisher_id': config.AWIN_PUBLISHER_ID
                },
                'Mercado Livre': {
                    'enabled': True,
                    'method': 'none',  # Por enquanto sem conversão específica
                    'message': 'Links diretos do Mercado Livre'
                }
            }

            config_loja = self.affiliate_configs[loja]
            
            return {
                'loja': loja,
                'status': 'configurada',
                'enabled': config_loja['enabled'],
                'method': config_loja['method'],
                'message': 'Configuração válida' if config_loja['enabled'] else 'Desabilitada'
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar status de afiliado para {loja}: {e}")
            return {
                'loja': loja,
                'status': 'erro',
                'enabled': False,
                'method': 'none',
                'message': f'Erro: {str(e)}'
            }
    
    def listar_lojas_configuradas(self) -> Dict[str, Dict]:
        """
        Lista todas as lojas configuradas para afiliados
        
        Returns:
            Dicionário com configurações de todas as lojas
        """
        try:
            status_lojas = {}
            
            for loja in self.awin_publishers.keys(): # Changed to awin_publishers
                status_lojas[loja] = self.verificar_status_afiliado(loja)
            
            return status_lojas
            
        except Exception as e:
            logger.error(f"Erro ao listar lojas configuradas: {e}")
            return {}


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
        status_lojas = converter.listar_lojas_configuradas()
        
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
