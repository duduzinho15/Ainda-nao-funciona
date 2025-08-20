"""
Módulo para buscar ofertas do AliExpress usando a API de Afiliados.

Este módulo fornece funções para buscar ofertas de produtos no AliExpress
usando a API de Afiliados e formatar os resultados em um formato padronizado.
"""

import logging
import time
from typing import Dict, List, Optional, Any

# Importa a classe AliExpressAPI do módulo existente
from aliexpress_api import AliExpressAPI, extract_product_id, format_product_info

# Configuração de logging
logger = logging.getLogger("garimpeiro_bot.ali_scraper")


def buscar_ofertas_aliexpress(
    palavras_chave: List[str], limite: int = 10
) -> List[Dict]:
    """
    Busca ofertas no AliExpress com base em palavras-chave.

    Args:
        palavras_chave: Lista de palavras-chave para busca
        limite: Número máximo de ofertas a retornar (padrão: 10)

    Returns:
        Lista de dicionários contendo as ofertas encontradas, no formato:
        {
            'id_produto': str,       # ID único do produto
            'loja': str,             # Nome da loja ('AliExpress')
            'titulo': str,           # Título do produto
            'preco': str,            # Preço formatado como string
            'url_produto': str,      # URL original do produto
            'url_imagem': str,       # URL da imagem do produto
            'preco_original': str    # Preço original (se houver desconto)
        }
    """
    if not palavras_chave:
        logger.warning("Nenhuma palavra-chave fornecida para busca no AliExpress")
        return []

    try:
        # Inicializa a API do AliExpress
        api = AliExpressAPI()
        logger.info(
            f"Buscando ofertas no AliExpress para as palavras-chave: {', '.join(palavras_chave)}"
        )

        # Lista para armazenar todas as ofertas encontradas
        todas_ofertas = []

        # Para cada palavra-chave, busca produtos
        for palavra_chave in palavras_chave:
            try:
                # Busca produtos no AliExpress
                resultados = api.search_products(
                    keywords=palavra_chave,
                    page_size=min(limite, 50),  # Máximo de 50 itens por página
                    country="BR",
                    language="pt",
                    sort="SALE_PRICE_DESC",  # Ordena por preço com desconto (maior desconto primeiro)
                )

                # Processa os resultados
                if (
                    resultados
                    and "products" in resultados
                    and "product" in resultados["products"]
                ):
                    for produto in resultados["products"]["product"][:limite]:
                        # Formata os dados do produto
                        oferta = {
                            "id_produto": produto.get("product_id", ""),
                            "loja": "AliExpress",
                            "titulo": produto.get("product_title", "").strip(),
                            "preco": produto.get("target_sale_price", ""),
                            "url_produto": produto.get("product_detail_url", ""),
                            "url_imagem": produto.get("product_main_image_url", ""),
                            "preco_original": produto.get("target_original_price", ""),
                        }

                        # Adiciona à lista de ofertas
                        todas_ofertas.append(oferta)

                        # Verifica se já atingiu o limite de ofertas
                        if len(todas_ofertas) >= limite:
                            break

                # Se já atingiu o limite de ofertas, interrompe a busca
                if len(todas_ofertas) >= limite:
                    break

            except Exception as e:
                logger.error(
                    f"Erro ao buscar produtos para a palavra-chave '{palavra_chave}': {str(e)}",
                    exc_info=True,
                )
                continue

        # Limita o número de ofertas retornadas
        return todas_ofertas[:limite]

    except Exception as e:
        logger.error(f"Erro ao buscar ofertas no AliExpress: {str(e)}", exc_info=True)
        return []


def buscar_info_produto(url_produto: str) -> Optional[Dict]:
    """
    Obtém informações detalhadas de um produto específico do AliExpress.

    Args:
        url_produto: URL do produto no AliExpress

    Returns:
        Dicionário com as informações do produto ou None em caso de erro
    """
    if not url_produto or "aliexpress.com" not in url_produto:
        logger.error("URL do produto inválida")
        return None

    try:
        # Extrai o ID do produto da URL
        product_id = extract_product_id(url_produto)
        if not product_id:
            logger.error(
                f"Não foi possível extrair o ID do produto da URL: {url_produto}"
            )
            return None

        # Inicializa a API do AliExpress
        api = AliExpressAPI()

        # Obtém informações detalhadas do produto
        produto = api.get_product_info(product_id, country="BR", language="pt")

        if not produto or "result" not in produto:
            logger.error("Resposta inválida da API do AliExpress")
            return None

        # Formata as informações do produto
        produto_formatado = format_product_info(produto)

        # Retorna no formato padronizado
        return {
            "id_produto": product_id,
            "loja": "AliExpress",
            "titulo": produto_formatado.get("title", ""),
            "preco": produto_formatado.get("price", ""),
            "url_produto": produto_formatado.get("url", url_produto),
            "url_imagem": produto_formatado.get("image_url", ""),
            "preco_original": produto_formatado.get("original_price", ""),
        }

    except Exception as e:
        logger.error(f"Erro ao buscar informações do produto: {str(e)}", exc_info=True)
        return None


# ===== FUNÇÃO COMPATIBILIDADE COM SCRAPER REGISTRY =====

async def get_ofertas(periodo: str = "24h") -> List[Dict[str, Any]]:
    """
    Função de compatibilidade com o scraper registry.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    try:
        # Palavras-chave padrão para ofertas
        palavras_chave = ["smartphone", "fone bluetooth", "smartwatch", "camera"]
        ofertas = buscar_ofertas_aliexpress(palavras_chave=palavras_chave, limite=20)
        
        # Adicionar metadados de compatibilidade
        for oferta in ofertas:
            oferta['fonte'] = 'aliexpress_scraper'
            oferta['periodo'] = periodo
            oferta['timestamp'] = time.time()
        
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 70  # Prioridade alta (API oficial)
rate_limit = 2.0  # 2 requisições por segundo
description = "API oficial do AliExpress - Busca ofertas usando API de Afiliados"

if __name__ == "__main__":
    # Configura o logging para exibir mensagens no console
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Testa a busca de ofertas por palavras-chave
    print("Testando busca de ofertas no AliExpress...")
    ofertas = buscar_ofertas_aliexpress(
        palavras_chave=["smartphone", "fone bluetooth"], limite=2
    )

    if ofertas:
        print(f"\nEncontradas {len(ofertas)} ofertas no AliExpress:")
        for i, oferta in enumerate(ofertas, 1):
            print(f"\n--- Oferta {i} ---")
            print(f"Título: {oferta['titulo']}")
            print(f"Preço: R$ {oferta['preco']}")
            print(f"Preço Original: R$ {oferta.get('preco_original', 'N/A')}")
            print(f"URL: {oferta['url_produto']}")
            print(f"Imagem: {oferta['url_imagem']}")
    else:
        print("Nenhuma oferta encontrada no AliExpress.")

    # Testa a busca de informações de um produto específico
    if ofertas:
        print("\nTestando busca de informações de um produto específico...")
        url_teste = ofertas[0]["url_produto"]
        print(f"Buscando informações para: {url_teste}")

        info_produto = buscar_info_produto(url_teste)
        if info_produto:
            print("\nInformações do produto:")
            print(f"Título: {info_produto['titulo']}")
            print(f"Preço: R$ {info_produto['preco']}")
            print(f"Preço Original: R$ {info_produto.get('preco_original', 'N/A')}")
            print(f"URL: {info_produto['url_produto']}")
            print(f"Imagem: {info_produto['url_imagem']}")
        else:
            print("Não foi possível obter as informações do produto.")
