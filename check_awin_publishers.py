#!/usr/bin/env python3
"""
Script para verificar e configurar publishers AWIN adicionais
Verifica quais lojas precisam de Publisher ID e ajuda na configuração
"""

import asyncio
import aiohttp
import logging
from affiliate import AffiliateLinkConverter

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verificar_publishers_awin():
    """Verifica o status dos publishers AWIN e identifica os que precisam de configuração"""
    
    print("🔍 VERIFICANDO STATUS DOS PUBLISHERS AWIN")
    print("=" * 60)
    
    converter = AffiliateLinkConverter()
    
    # Lista de lojas que precisam de Publisher ID
    lojas_para_configurar = [
        'Terabyte',
        'Pichau', 
        'Mercado Livre',
        'Shopee',
        'AliExpress'
    ]
    
    print("\n📋 LOJAS QUE PRECISAM DE PUBLISHER ID:")
    print("-" * 50)
    
    for loja in lojas_para_configurar:
        if loja in converter.awin_publishers:
            publisher_id = converter.awin_publishers[loja]
            if publisher_id.startswith('seu_publisher_id'):
                print(f"⚠️ {loja}: Publisher ID não configurado")
                print(f"   Status: {publisher_id}")
                print(f"   Ação: Obter Publisher ID da AWIN")
            else:
                print(f"✅ {loja}: Publisher ID configurado")
                print(f"   ID: {publisher_id}")
        else:
            print(f"❌ {loja}: Não encontrada na lista de publishers")
    
    print("\n🔧 COMO OBTER PUBLISHER IDS:")
    print("-" * 50)
    print("1️⃣ Acesse: https://www.awin.com/br/account")
    print("2️⃣ Faça login na sua conta")
    print("3️⃣ Vá em 'Programs' > 'My Programs'")
    print("4️⃣ Para cada loja, clique e copie o 'Publisher ID'")
    print("5️⃣ Atualize o arquivo affiliate.py com os IDs reais")
    
    print("\n📝 EXEMPLO DE CONFIGURAÇÃO:")
    print("-" * 50)
    print("self.awin_publishers = {")
    print("    'Kabum!': '17729',")
    print("    'Comfy': '23377',")
    print("    'Trocafy': '51277',")
    print("    'LG': '33061',")
    print("    'Terabyte': 'SEU_PUBLISHER_ID_TERABYTE',")
    print("    'Pichau': 'SEU_PUBLISHER_ID_PICHAU',")
    print("    'Mercado Livre': 'SEU_PUBLISHER_ID_MERCADOLIVRE',")
    print("    'Shopee': 'SEU_PUBLISHER_ID_SHOPEE',")
    print("    'AliExpress': 'SEU_PUBLISHER_ID_ALIEXPRESS'")
    print("}")
    
    return lojas_para_configurar

async def testar_integracao_awin():
    """Testa a integração com a API da AWIN"""
    
    print("\n🔗 TESTANDO INTEGRAÇÃO COM API DA AWIN")
    print("=" * 60)
    
    try:
        converter = AffiliateLinkConverter()
        
        # URLs de teste para lojas AWIN
        test_urls = {
            'Kabum!': 'https://www.kabum.com.br/produto/123456',
            'Comfy': 'https://www.comfy.com.br/produto/123456',
            'Trocafy': 'https://www.trocafy.com.br/produto/123456',
            'LG': 'https://www.lg.com.br/produto/123456'
        }
        
        print("📋 Testando geração de links AWIN:")
        print("-" * 40)
        
        for loja, url in test_urls.items():
            try:
                affiliate_url = await converter.gerar_link_afiliado_awin(url, loja)
                
                if affiliate_url != url:
                    print(f"✅ {loja}: Link AWIN gerado com sucesso!")
                    print(f"   Original: {url}")
                    print(f"   AWIN: {affiliate_url[:80]}...")
                else:
                    print(f"⚠️ {loja}: Falha na geração do link AWIN")
                    
            except Exception as e:
                print(f"❌ {loja}: Erro - {e}")
                
    except Exception as e:
        print(f"❌ Erro geral na integração AWIN: {e}")

async def main():
    """Função principal"""
    try:
        # Verifica publishers
        await verificar_publishers_awin()
        
        # Testa integração
        await testar_integracao_awin()
        
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("=" * 60)
        print("1️⃣ Configure os Publisher IDs das lojas pendentes")
        print("2️⃣ Execute novamente este script para validar")
        print("3️⃣ Teste a integração com o orquestrador")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")

if __name__ == "__main__":
    asyncio.run(main())
