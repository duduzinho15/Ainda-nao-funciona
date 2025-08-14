"""
Módulo para conversão de URLs para links de afiliado
"""
import re
import logging
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import config

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AffiliateLinkConverter:
    """Conversor de links para afiliados"""
    
    def __init__(self):
        """Inicializa o conversor de links de afiliado"""
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
        
        # Mapeamento de domínios para nomes de lojas
        self.domain_mapping = {
            'magazineluiza.com.br': 'Magazine Luiza',
            'amazon.com.br': 'Amazon',
            'shopee.com.br': 'Shopee',
            'aliexpress.com': 'AliExpress',
            'pt.aliexpress.com': 'AliExpress',
            'kabum.com.br': 'Kabum!',
            'dell.com.br': 'Dell',
            'lenovo.com.br': 'Lenovo',
            'acer.com.br': 'Acer',
            'asus.com.br': 'ASUS',
            'mercadolivre.com.br': 'Mercado Livre',
            'lista.mercadolivre.com.br': 'Mercado Livre'
        }
    
    def detect_store_from_url(self, url: str) -> Optional[str]:
        """
        Detecta a loja a partir da URL
        
        Args:
            url: URL do produto
            
        Returns:
            Nome da loja ou None se não reconhecida
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. se existir
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Procura por correspondência exata
            if domain in self.domain_mapping:
                return self.domain_mapping[domain]
            
            # Procura por correspondência parcial
            for domain_pattern, store_name in self.domain_mapping.items():
                if domain_pattern in domain or domain in domain_pattern:
                    return store_name
            
            logger.warning(f"Loja não reconhecida para o domínio: {domain}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao detectar loja da URL {url}: {e}")
            return None
    
    def _convert_magalu_url(self, url: str) -> str:
        """
        Converte URL do Magazine Luiza para link de afiliado
        
        Args:
            url: URL original do Magazine Luiza
            
        Returns:
            URL de afiliado do Magazine Luiza
        """
        try:
            parsed_url = urlparse(url)
            
            # Constrói a nova URL de afiliado
            affiliate_url = f"{self.affiliate_configs['Magazine Luiza']['base_url']}{parsed_url.path}"
            
            # Adiciona parâmetros de consulta se existirem
            if parsed_url.query:
                affiliate_url += f"?{parsed_url.query}"
            
            # Adiciona fragmento se existir
            if parsed_url.fragment:
                affiliate_url += f"#{parsed_url.fragment}"
            
            logger.info(f"URL do Magazine Luiza convertida: {url} -> {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao converter URL do Magazine Luiza: {e}")
            return url
    
    def _convert_amazon_url(self, url: str) -> str:
        """
        Converte URL da Amazon para link de afiliado
        
        Args:
            url: URL original da Amazon
            
        Returns:
            URL de afiliado da Amazon
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Adiciona ou atualiza o tag de afiliado
            affiliate_tag = self.affiliate_configs['Amazon']['tag']
            query_params['tag'] = [affiliate_tag]
            
            # Reconstrói a URL com os novos parâmetros
            new_query = urlencode(query_params, doseq=True)
            affiliate_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            
            logger.info(f"URL da Amazon convertida: {url} -> {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao converter URL da Amazon: {e}")
            return url
    
    def _convert_shopee_url(self, url: str) -> str:
        """
        Converte URL da Shopee para link de afiliado (por enquanto retorna a original)
        
        Args:
            url: URL original da Shopee
            
        Returns:
            URL original (conversão não implementada ainda)
        """
        logger.info("Conversão de afiliado da Shopee não implementada ainda")
        return url
    
    def _convert_aliexpress_url(self, url: str) -> str:
        """
        Converte URL do AliExpress para link de afiliado (usa API)
        
        Args:
            url: URL original do AliExpress
            
        Returns:
            URL de afiliado do AliExpress
        """
        try:
            # Por enquanto, retorna a URL original
            # A conversão real será feita pela API do AliExpress
            logger.info("Conversão do AliExpress será feita pela API")
            return url
            
        except Exception as e:
            logger.error(f"Erro ao converter URL do AliExpress: {e}")
            return url
    
    def gerar_link_afiliado(self, url_original: str, loja: str = None) -> str:
        """
        Gera link de afiliado para uma URL
        
        Args:
            url_original: URL original do produto
            loja: Nome da loja (opcional, será detectada automaticamente se não fornecida)
            
        Returns:
            URL de afiliado ou URL original se não for possível converter
        """
        try:
            if not url_original:
                logger.warning("URL original não fornecida")
                return ""
            
            # Detecta a loja se não fornecida
            if not loja:
                loja = self.detect_store_from_url(url_original)
                if not loja:
                    logger.warning(f"Loja não reconhecida para a URL: {url_original}")
                    return url_original
            
            # Verifica se a conversão está habilitada para esta loja
            if loja not in self.affiliate_configs:
                logger.warning(f"Configuração de afiliado não encontrada para: {loja}")
                return url_original
            
            config_loja = self.affiliate_configs[loja]
            if not config_loja['enabled']:
                logger.info(f"Conversão de afiliado desabilitada para: {loja}")
                return url_original
            
            # Aplica o método de conversão apropriado
            method = config_loja['method']
            
            if method == 'replace_domain':
                if loja == 'Magazine Luiza':
                    return self._convert_magalu_url(url_original)
            
            elif method == 'add_tag':
                if loja == 'Amazon':
                    return self._convert_amazon_url(url_original)
            
            elif method == 'api':
                if loja == 'AliExpress':
                    return self._convert_aliexpress_url(url_original)
                elif loja in ['Kabum!', 'Dell', 'Lenovo', 'Acer', 'ASUS']:
                    return self._convert_awin_url(url_original, loja)
            
            elif method == 'none':
                logger.info(f"Conversão não implementada para: {loja}")
                return url_original
            
            # Se chegou aqui, não foi possível converter
            logger.warning(f"Método de conversão não implementado para: {loja}")
            return url_original
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado: {e}")
            return url_original
    
    def gerar_links_afiliado_batch(self, urls: list, lojas: list = None) -> Dict[str, str]:
        """
        Gera links de afiliado para uma lista de URLs
        
        Args:
            urls: Lista de URLs para converter
            lojas: Lista de nomes de lojas (opcional)
            
        Returns:
            Dicionário com URLs originais como chaves e URLs de afiliado como valores
        """
        try:
            if not urls:
                logger.warning("Lista de URLs vazia")
                return {}
            
            if lojas and len(urls) != len(lojas):
                logger.warning("Número de URLs e lojas não corresponde")
                return {}
            
            results = {}
            
            for i, url in enumerate(urls):
                loja = lojas[i] if lojas else None
                affiliate_url = self.gerar_link_afiliado(url, loja)
                results[url] = affiliate_url
            
            logger.info(f"Convertidas {len(urls)} URLs para links de afiliado")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao gerar links de afiliado em lote: {e}")
            return {}
    
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
            # Verifica se a API da Awin está configurada
            if not config.AWIN_API_TOKEN or not config.AWIN_PUBLISHER_ID:
                logger.warning("API da Awin não configurada")
                return url_original
            
            # Mapeia nomes de lojas para IDs da Awin
            lojas_awin_ids = {
                'Kabum!': 'kabum',
                'Dell': 'dell',
                'Lenovo': 'lenovo',
                'Acer': 'acer',
                'ASUS': 'asus',
                'Trocafy': 'trocafy',
                'Samsung': 'samsung',
                'Casa Bahia': 'casa_bahia'
            }
            
            # Obtém o ID da loja na Awin
            loja_id = lojas_awin_ids.get(loja)
            if not loja_id:
                logger.warning(f"Loja {loja} não mapeada para Awin")
                return url_original
            
            # Constrói o link de afiliado da Awin
            # Formato: https://www.awin1.com/cread.php?awinmid={publisher_id}&awinaffid={affiliate_id}&clicktracker=url&ued={url_encoded}
            affiliate_url = (
                f"https://www.awin1.com/cread.php?"
                f"awinmid={config.AWIN_PUBLISHER_ID}&"
                f"awinaffid={config.AWIN_PUBLISHER_ID}&"
                f"clicktracker=url&"
                f"ued={url_original}"
            )
            
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
            if loja not in self.affiliate_configs:
                return {
                    'loja': loja,
                    'status': 'nao_configurada',
                    'enabled': False,
                    'method': 'none',
                    'message': 'Loja não configurada'
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
            
            for loja in self.affiliate_configs.keys():
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
            loja = converter.detect_store_from_url(url)
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
