"""
Script para testar a integração com a API da Amazon.
Execute este script para verificar se a busca de ofertas está funcionando corretamente.
"""
import asyncio
import logging
from amazon_api import buscar_ofertas_amazon

# Configurar logging para ver mensagens detalhadas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def testar_busca():
    """Função principal para testar a busca de ofertas."""
    print("\n=== TESTE DE INTEGRAÇÃO COM A API DA AMAZON ===")
    
    # Lista de palavras-chave para teste
    palavras_chave = ["notebook gamer", "ssd 1tb", "monitor 144hz"]
    
    print(f"\nBuscando ofertas para: {', '.join(palavras_chave)}")
    
    try:
        # Buscar ofertas
        ofertas = await buscar_ofertas_amazon(palavras_chave, max_itens=2)
        
        # Exibir resultados
        if not ofertas:
            print("\nNenhuma oferta encontrada. Verifique suas credenciais e conexão com a internet.")
            return
        
        print(f"\n✅ Encontradas {len(ofertas)} ofertas!")
        
        for i, oferta in enumerate(ofertas, 1):
            print(f"\n--- Oferta {i} ---")
            print(f"Título: {oferta['titulo']}")
            print(f"Preço: {oferta['preco']}")
            if oferta.get('economia'):
                print(f"Economia: R$ {oferta['economia']}")
            print(f"Condição: {oferta['condicao']}")
            print(f"URL: {oferta['url']}")
            if oferta.get('imagem_url'):
                print(f"Imagem: {oferta['imagem_url']}")
    
    except Exception as e:
        print(f"\n❌ Erro durante a busca: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Executar o teste
    asyncio.run(testar_busca())
    
    # Manter o console aberto no Windows
    if os.name == 'nt':
        input("\nPressione Enter para sair...")
