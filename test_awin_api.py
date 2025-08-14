"""
Teste da integração com a API da Awin.

Este script testa todas as funcionalidades da integração com a Awin:
- Conexão com a API
- Busca de programas parceiros
- Busca de ofertas
- Conversão de dados
"""
import asyncio
import sys
import os

# Adiciona o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_awin_integration():
    """Testa a integração completa com a Awin."""
    print("🧪 Testando Integração com a API da Awin")
    print("=" * 60)
    
    try:
        # Testa importação do módulo
        print("📦 Testando importação do módulo...")
        from awin_api import (
            obter_programas_parceiros,
            buscar_ofertas_awin,
            testar_api_awin
        )
        print("✅ Módulo importado com sucesso!")
        
        # Testa configuração
        print("\n⚙️  Testando configuração...")
        import config
        if config.AWIN_API_TOKEN and config.AWIN_API_TOKEN != "YOUR_TOKEN":
            print(f"✅ Token da Awin configurado: {config.AWIN_API_TOKEN[:10]}...")
        else:
            print("❌ Token da Awin não configurado")
            return False
        
        if config.AWIN_PUBLISHER_ID and config.AWIN_PUBLISHER_ID != "YOUR_PUBLISHER_ID":
            print(f"✅ Publisher ID configurado: {config.AWIN_PUBLISHER_ID}")
        else:
            print("❌ Publisher ID não configurado")
            return False
        
        # Testa função de teste integrada
        print("\n🔍 Testando função de teste integrada...")
        resultado_teste = await testar_api_awin()
        if resultado_teste:
            print("✅ Teste integrado executado com sucesso!")
        else:
            print("❌ Teste integrado falhou")
            return False
        
        # Testa busca de programas parceiros
        print("\n🏢 Testando busca de programas parceiros...")
        programas = await obter_programas_parceiros()
        if programas and 'data' in programas:
            num_programas = len(programas['data'])
            print(f"✅ {num_programas} programas parceiros encontrados!")
            
            # Lista os primeiros programas
            for i, programa in enumerate(programas['data'][:5], 1):
                nome = programa.get('name', 'Sem nome')
                programa_id = programa.get('id', 'Sem ID')
                print(f"   {i}. {nome} (ID: {programa_id})")
        else:
            print("❌ Nenhum programa parceiro encontrado")
            return False
        
        # Testa busca de ofertas
        print("\n📦 Testando busca de ofertas...")
        ofertas = await buscar_ofertas_awin(max_ofertas=5, min_desconto=10)
        if ofertas:
            print(f"✅ {len(ofertas)} ofertas encontradas!")
            
            # Mostra detalhes das primeiras ofertas
            for i, oferta in enumerate(ofertas[:3], 1):
                print(f"\n   📦 Oferta {i}:")
                print(f"      Título: {oferta['titulo'][:50]}...")
                print(f"      Loja: {oferta['loja']}")
                print(f"      Preço: {oferta['preco']}")
                print(f"      Desconto: {oferta['desconto']}%")
                print(f"      Categoria: {oferta['categoria']}")
        else:
            print("❌ Nenhuma oferta encontrada")
            return False
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_affiliate_conversion():
    """Testa a conversão de links de afiliado."""
    print("\n🔗 Testando Conversão de Links de Afiliado")
    print("=" * 60)
    
    try:
        from affiliate import AffiliateLinkConverter
        
        converter = AffiliateLinkConverter()
        
        # URLs de teste para lojas da Awin
        urls_teste = [
            "https://www.kabum.com.br/produto/123456",
            "https://www.dell.com.br/p/notebook-latitude-123",
            "https://www.lenovo.com.br/notebook/thinkpad-456",
            "https://www.acer.com.br/notebook/aspire-789"
        ]
        
        print("🔍 Testando detecção de lojas...")
        for url in urls_teste:
            loja = converter.detect_store_from_url(url)
            print(f"   {url[:40]}... → {loja}")
        
        print("\n💰 Testando conversão de links...")
        for url in urls_teste:
            loja = converter.detect_store_from_url(url)
            affiliate_url = converter.gerar_link_afiliado(url, loja)
            
            print(f"\n   🏪 {loja}:")
            print(f"      Original: {url[:50]}...")
            print(f"      Afiliado: {affiliate_url[:50]}...")
            
            if url != affiliate_url:
                print("      ✅ Conversão realizada!")
            else:
                print("      ⚠️  Sem conversão (esperado para Awin)")
        
        print("\n✅ Teste de conversão concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de conversão: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Função principal de teste."""
    print("🚀 Iniciando Testes da Integração Awin")
    print("=" * 60)
    
    # Testa integração principal
    resultado_integracao = await test_awin_integration()
    
    # Testa conversão de links
    resultado_conversao = await test_affiliate_conversion()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    print(f"🔌 Integração Awin: {'✅ PASSOU' if resultado_integracao else '❌ FALHOU'}")
    print(f"🔗 Conversão de Links: {'✅ PASSOU' if resultado_conversao else '❌ FALHOU'}")
    
    if resultado_integracao and resultado_conversao:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A integração com a Awin está funcionando corretamente!")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique as configurações e tente novamente.")
        return False

if __name__ == "__main__":
    # Executa os testes
    resultado = asyncio.run(main())
    sys.exit(0 if resultado else 1)
