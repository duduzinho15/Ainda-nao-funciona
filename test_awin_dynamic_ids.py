"""
Script de teste para validar a funcionalidade de IDs dinâmicos da Awin

Este script testa a nova função atualizar_ids_lojas_awin que consulta
a API da Awin para obter os IDs dos programas aprovados automaticamente.
"""
import asyncio
import sys
import os

# Adiciona o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_awin_dynamic_ids():
    """Testa a funcionalidade de IDs dinâmicos da Awin"""
    print("🧪 Testando Funcionalidade de IDs Dinâmicos da Awin")
    print("=" * 80)
    
    try:
        # Testa importação do módulo
        print("📦 Testando importação do módulo...")
        from awin_api import atualizar_ids_lojas_awin, LOJAS_AWIN
        print("✅ Módulo importado com sucesso!")
        
        # Mostra estado inicial das lojas
        print("\n🏪 Estado inicial das lojas Awin:")
        for nome, detalhes in LOJAS_AWIN.items():
            status = "✅ ATIVADA" if detalhes['enabled'] else "❌ DESATIVADA"
            awin_id = detalhes['awin_id'] or "NÃO DEFINIDO"
            print(f"   {detalhes['name']}: {status} (ID: {awin_id})")
        
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
        
        # Testa atualização dinâmica dos IDs
        print("\n🔄 Testando atualização dinâmica dos IDs...")
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            await atualizar_ids_lojas_awin(session)
        
        # Mostra estado final das lojas
        print("\n🏪 Estado final das lojas Awin após atualização:")
        lojas_ativadas = 0
        for nome, detalhes in LOJAS_AWIN.items():
            status = "✅ ATIVADA" if detalhes['enabled'] else "❌ DESATIVADA"
            awin_id = detalhes['awin_id'] or "NÃO DEFINIDO"
            print(f"   {detalhes['name']}: {status} (ID: {awin_id})")
            
            if detalhes['enabled']:
                lojas_ativadas += 1
        
        # Estatísticas finais
        print(f"\n📊 RESULTADO DA ATUALIZAÇÃO:")
        print(f"   Total de lojas configuradas: {len(LOJAS_AWIN)}")
        print(f"   Lojas ativadas: {lojas_ativadas}")
        print(f"   Lojas desativadas: {len(LOJAS_AWIN) - lojas_ativadas}")
        
        if lojas_ativadas > 0:
            print(f"\n🎉 SUCESSO! {lojas_ativadas} lojas foram ativadas com IDs válidos!")
            return True
        else:
            print(f"\n⚠️  ATENÇÃO: Nenhuma loja foi ativada. Verifique as credenciais da API.")
            return False
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_awin_integration():
    """Testa a integração completa da Awin com IDs dinâmicos"""
    print("\n🔗 Testando Integração Completa da Awin")
    print("=" * 80)
    
    try:
        from awin_api import buscar_ofertas_awin, LOJAS_AWIN
        
        # Filtra apenas lojas ativadas
        lojas_ativadas = [nome for nome, detalhes in LOJAS_AWIN.items() if detalhes['enabled']]
        
        if not lojas_ativadas:
            print("⚠️  Nenhuma loja Awin está ativada. Execute primeiro o teste de IDs dinâmicos.")
            return False
        
        print(f"🏪 Testando busca de ofertas em {len(lojas_ativadas)} lojas ativadas...")
        
        # Testa busca de ofertas
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
        else:
            print("ℹ️  Nenhuma oferta encontrada (pode ser normal dependendo da disponibilidade)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Teste da Funcionalidade de IDs Dinâmicos da Awin")
    print("=" * 80)
    
    # Testa IDs dinâmicos
    resultado_ids = await test_awin_dynamic_ids()
    
    # Testa integração completa
    resultado_integracao = await test_awin_integration()
    
    # Resultado final
    print("\n" + "=" * 80)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 80)
    print(f"🔧 IDs Dinâmicos: {'✅ PASSOU' if resultado_ids else '❌ FALHOU'}")
    print(f"🔗 Integração Completa: {'✅ PASSOU' if resultado_integracao else '❌ FALHOU'}")
    
    if resultado_ids and resultado_integracao:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A funcionalidade de IDs dinâmicos está funcionando perfeitamente!")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique as configurações e tente novamente.")
        return False

if __name__ == "__main__":
    # Executa os testes
    resultado = asyncio.run(main())
    sys.exit(0 if resultado else 1)
