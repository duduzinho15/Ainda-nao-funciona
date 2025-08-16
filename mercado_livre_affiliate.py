#!/usr/bin/env python3
"""
Sistema de Afiliados do Mercado Livre
Implementa geração de links de afiliado para produtos do Mercado Livre
"""
import re
import hashlib
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, quote

logger = logging.getLogger('mercado_livre_affiliate')

class MercadoLivreAffiliate:
    """Sistema de afiliados do Mercado Livre"""
    
    def __init__(self):
        # Configurações do programa de afiliados
        self.affiliate_tag = "garimpeirogeek"
        self.affiliate_tool = "82173227"
        self.base_url = "https://www.mercadolivre.com.br"
        
        # Padrões de URLs do Mercado Livre
        self.url_patterns = {
            'produto': r'https?://(?:www\.)?mercadolivre\.com\.br/(?:produto/)?([^/?]+)',
            'item_id': r'MLB-\d+',
            'categoria': r'https?://(?:www\.)?mercadolivre\.com\.br/([^/?]+)',
            'busca': r'https?://(?:www\.)?mercadolivre\.com\.br/([^/?]+)'
        }
        
        # Mapeamento de categorias para códigos de afiliado
        self.category_codes = {
            'celular-e-smartphone': 'cel',
            'notebooks': 'not',
            'tablets': 'tab',
            'consoles-video-games': 'gam',
            'tv-audio-video': 'tva',
            'informatica': 'inf',
            'eletronicos': 'ele',
            'casa-moveis-decoracao': 'cas',
            'esportes': 'esp',
            'brinquedos-jogos': 'bri'
        }
    
    def generate_affiliate_url(self, original_url: str, product_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Gera link de afiliado para o Mercado Livre
        
        Args:
            original_url: URL original do produto
            product_info: Informações adicionais do produto (opcional)
        
        Returns:
            URL de afiliado gerada
        """
        try:
            if not original_url:
                logger.warning("URL original não fornecida")
                return ""
            
            # Limpa a URL removendo parâmetros desnecessários
            clean_url = self._clean_mercadolivre_url(original_url)
            
            # Extrai informações da URL
            url_info = self._extract_url_info(clean_url)
            
            # Gera link de afiliado baseado no tipo de URL
            if url_info['type'] == 'produto':
                return self._generate_product_affiliate_url(clean_url, url_info, product_info)
            elif url_info['type'] == 'categoria':
                return self._generate_category_affiliate_url(clean_url, url_info)
            elif url_info['type'] == 'busca':
                return self._generate_search_affiliate_url(clean_url, url_info)
            else:
                return self._generate_generic_affiliate_url(clean_url)
                
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado: {e}")
            return original_url
    
    def _clean_mercadolivre_url(self, url: str) -> str:
        """Remove parâmetros desnecessários da URL do Mercado Livre"""
        try:
            # Parse da URL
            parsed = urlparse(url)
            
            # Remove parâmetros de tracking e outros desnecessários
            unwanted_params = [
                'tracking_id', 'wid', 'sid', 'deal_print_id', 'searchVariation',
                'search_layout', 'is_advertising', 'ad_domain', 'ad_position',
                'ad_click_id', 'polycard_client', 'reco_backend', 'reco_client',
                'reco_item_pos', 'reco_backend_type', 'reco_id', 'c_id', 'c_uid'
            ]
            
            # Parse dos parâmetros
            query_params = parse_qs(parsed.query)
            
            # Remove parâmetros indesejados
            for param in unwanted_params:
                if param in query_params:
                    del query_params[param]
            
            # Reconstrói a URL limpa
            clean_query = urlencode(query_params, doseq=True) if query_params else ""
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if clean_query:
                clean_url += f"?{clean_query}"
            
            logger.info(f"URL limpa: {clean_url}")
            return clean_url
            
        except Exception as e:
            logger.error(f"Erro ao limpar URL: {e}")
            return url
    
    def _extract_url_info(self, url: str) -> Dict[str, Any]:
        """Extrai informações da URL do Mercado Livre"""
        url_info = {
            'type': 'generic',
            'item_id': None,
            'category': None,
            'search_query': None,
            'path_parts': []
        }
        
        try:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            url_info['path_parts'] = path_parts
            
            # Verifica se é URL de produto
            if 'produto' in path_parts or any(re.match(r'MLB-\d+', p) for p in path_parts):
                url_info['type'] = 'produto'
                # Extrai ID do item
                for part in path_parts:
                    if re.match(r'MLB-\d+', part):
                        url_info['item_id'] = part
                        break
            
            # Verifica se é URL de categoria
            elif len(path_parts) == 1 and path_parts[0] in self.category_codes:
                url_info['type'] = 'categoria'
                url_info['category'] = path_parts[0]
            
            # Verifica se é URL de busca
            elif 'busca' in path_parts or 'search' in path_parts:
                url_info['type'] = 'busca'
                # Extrai query de busca
                query_params = parse_qs(parsed.query)
                if 'q' in query_params:
                    url_info['search_query'] = query_params['q'][0]
            
            logger.info(f"Tipo de URL identificado: {url_info['type']}")
            return url_info
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações da URL: {e}")
            return url_info
    
    def _generate_product_affiliate_url(self, clean_url: str, url_info: Dict[str, Any], product_info: Optional[Dict[str, Any]]) -> str:
        """Gera link de afiliado para produtos"""
        try:
            # Gera link de afiliado completo
            affiliate_url = self._generate_full_affiliate_url(clean_url)
            
            # Gera link curto se possível
            short_url = self._generate_short_affiliate_url(url_info, product_info)
            
            logger.info(f"Link de afiliado produto gerado: {affiliate_url}")
            if short_url:
                logger.info(f"Link curto gerado: {short_url}")
            
            # Retorna o link completo (mais confiável)
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado para produto: {e}")
            return clean_url
    
    def _generate_category_affiliate_url(self, clean_url: str, url_info: Dict[str, Any]) -> str:
        """Gera link de afiliado para categorias"""
        try:
            category = url_info.get('category')
            if category and category in self.category_codes:
                category_code = self.category_codes[category]
                
                # Gera link de afiliado para categoria
                affiliate_url = self._generate_full_affiliate_url(clean_url)
                
                logger.info(f"Link de afiliado categoria gerado: {affiliate_url}")
                return affiliate_url
            
            return clean_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado para categoria: {e}")
            return clean_url
    
    def _generate_search_affiliate_url(self, clean_url: str, url_info: Dict[str, Any]) -> str:
        """Gera link de afiliado para buscas"""
        try:
            search_query = url_info.get('search_query')
            if search_query:
                # Gera link de afiliado para busca
                affiliate_url = self._generate_full_affiliate_url(clean_url)
                
                logger.info(f"Link de afiliado busca gerado: {affiliate_url}")
                return affiliate_url
            
            return clean_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado para busca: {e}")
            return clean_url
    
    def _generate_generic_affiliate_url(self, clean_url: str) -> str:
        """Gera link de afiliado genérico"""
        try:
            affiliate_url = self._generate_full_affiliate_url(clean_url)
            
            logger.info(f"Link de afiliado genérico gerado: {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado genérico: {e}")
            return clean_url
    
    def _generate_full_affiliate_url(self, clean_url: str) -> str:
        """Gera link de afiliado completo do Mercado Livre"""
        try:
            # Parâmetros de afiliado
            affiliate_params = {
                'matt_word': self.affiliate_tag,
                'matt_tool': self.affiliate_tool,
                'forceInApp': 'true'
            }
            
            # Gera referência única baseada na URL
            ref_hash = self._generate_reference_hash(clean_url)
            affiliate_params['ref'] = ref_hash
            
            # Constrói URL de afiliado
            separator = '&' if '?' in clean_url else '?'
            affiliate_url = f"{clean_url}{separator}{urlencode(affiliate_params)}"
            
            return affiliate_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado completo: {e}")
            return clean_url
    
    def _generate_short_affiliate_url(self, url_info: Dict[str, Any], product_info: Optional[Dict[str, Any]]) -> Optional[str]:
        """Gera link de afiliado curto (simulado)"""
        try:
            # Gera ID curto baseado nas informações do produto
            if url_info.get('item_id'):
                # Para produtos, usa o ID do item
                short_id = self._generate_short_id(url_info['item_id'])
            elif url_info.get('category'):
                # Para categorias, usa código da categoria
                short_id = self._generate_short_id(url_info['category'])
            elif url_info.get('search_query'):
                # Para buscas, usa hash da query
                short_id = self._generate_short_id(url_info['search_query'])
            else:
                # Para URLs genéricas, usa hash da URL
                short_id = self._generate_short_id("generic")
            
            short_url = f"https://mercadolivre.com/sec/{short_id}"
            return short_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar link curto: {e}")
            return None
    
    def _generate_reference_hash(self, url: str) -> str:
        """Gera hash de referência único para o produto"""
        try:
            # Combina URL com timestamp para garantir unicidade
            import time
            timestamp = int(time.time())
            combined = f"{url}_{timestamp}_{self.affiliate_tag}"
            
            # Gera hash SHA-256
            hash_object = hashlib.sha256(combined.encode())
            hash_hex = hash_object.hexdigest()
            
            # Converte para base64-like string (simulado)
            # Na implementação real, isso seria feito pela API do Mercado Livre
            import base64
            hash_bytes = bytes.fromhex(hash_hex[:32])  # Primeiros 16 bytes
            b64_hash = base64.b64encode(hash_bytes).decode('utf-8')
            
            # Remove caracteres especiais e limita tamanho
            clean_hash = re.sub(r'[^A-Za-z0-9]', '', b64_hash)[:50]
            
            return clean_hash
            
        except Exception as e:
            logger.error(f"Erro ao gerar hash de referência: {e}")
            return "default_ref"
    
    def _generate_short_id(self, identifier: str) -> str:
        """Gera ID curto para links encurtados"""
        try:
            # Combina identificador com timestamp
            import time
            timestamp = int(time.time())
            combined = f"{identifier}_{timestamp}"
            
            # Gera hash MD5 (mais curto)
            hash_object = hashlib.md5(combined.encode())
            hash_hex = hash_object.hexdigest()
            
            # Converte para base62 (0-9, A-Z, a-z)
            import string
            base62_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
            
            # Converte hash para base62
            hash_int = int(hash_hex[:8], 16)  # Primeiros 4 bytes
            short_id = ""
            
            while hash_int > 0:
                hash_int, remainder = divmod(hash_int, 62)
                short_id = base62_chars[remainder] + short_id
            
            # Garante que tenha pelo menos 6 caracteres
            while len(short_id) < 6:
                short_id = "0" + short_id
            
            return short_id[:8]  # Limita a 8 caracteres
            
        except Exception as e:
            logger.error(f"Erro ao gerar ID curto: {e}")
            return "1vt6gtj"  # ID padrão
    
    def validate_affiliate_url(self, affiliate_url: str) -> bool:
        """Valida se uma URL de afiliado está correta"""
        try:
            if not affiliate_url:
                return False
            
            # Verifica se contém parâmetros obrigatórios
            required_params = ['matt_word', 'matt_tool', 'ref']
            parsed = urlparse(affiliate_url)
            query_params = parse_qs(parsed.query)
            
            for param in required_params:
                if param not in query_params:
                    logger.warning(f"Parâmetro obrigatório ausente: {param}")
                    return False
            
            # Verifica valores dos parâmetros
            if query_params.get('matt_word', [''])[0] != self.affiliate_tag:
                logger.warning("Tag de afiliado incorreta")
                return False
            
            if query_params.get('matt_tool', [''])[0] != self.affiliate_tool:
                logger.warning("Ferramenta de afiliado incorreta")
                return False
            
            logger.info("URL de afiliado validada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar URL de afiliado: {e}")
            return False
    
    def get_affiliate_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de afiliados"""
        return {
            'affiliate_tag': self.affiliate_tag,
            'affiliate_tool': self.affiliate_tool,
            'url_patterns_supported': len(self.url_patterns),
            'categories_supported': len(self.category_codes),
            'status': '✅ ATIVO',
            'description': 'Sistema de afiliados do Mercado Livre implementado'
        }

def main():
    """Função de teste"""
    print("🔗 TESTANDO SISTEMA DE AFILIADOS DO MERCADO LIVRE")
    print("=" * 60)
    
    # Cria instância
    ml_affiliate = MercadoLivreAffiliate()
    
    # URLs de teste
    test_urls = [
        "https://www.mercadolivre.com.br/case-hd-ssd-externo-usb-30-sata-2535-4tb-com-fonte-knup/up/MLBU2922204299",
        "https://www.mercadolivre.com.br/smartphone-motorola-moto-g35-5g-128gb-12gb-4gb-ram8gb-ram-boost-e-camera-50mp-com-ai-nfc-tela-67-com-superbrilho-grafite-vegan-leather/p/MLB41540844",
        "https://produto.mercadolivre.com.br/MLB-5390754452-fone-de-ouvido-atfly-j10-anc-enc-bluetooth-53-bateria-24h-_JM",
        "https://www.mercadolivre.com.br/celular-e-smartphone",
        "https://www.mercadolivre.com.br/busca?q=notebook+gamer"
    ]
    
    print("📋 URLs de teste:")
    for i, url in enumerate(test_urls, 1):
        print(f"  {i}. {url}")
    
    print("\n🔗 Testando geração de links de afiliado:")
    print("-" * 60)
    
    for i, url in enumerate(test_urls, 1):
        try:
            print(f"\n{i}. URL Original: {url}")
            
            # Gera link de afiliado
            affiliate_url = ml_affiliate.generate_affiliate_url(url)
            
            print(f"   Link Afiliado: {affiliate_url}")
            
            # Valida o link gerado
            is_valid = ml_affiliate.validate_affiliate_url(affiliate_url)
            status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
            print(f"   Status: {status}")
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n📊 Estatísticas do Sistema:")
    print("-" * 60)
    stats = ml_affiliate.get_affiliate_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()
