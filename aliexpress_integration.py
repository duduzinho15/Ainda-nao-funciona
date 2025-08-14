"""
Módulo de integração com a API de Afiliados do AliExpress.

Este módulo fornece funções para buscar ofertas de produtos no AliExpress usando a API de Afiliados
e agendar verificações periódicas de ofertas.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from telegram.ext import ContextTypes

# Importa o módulo da API do AliExpress
try:
    from aliexpress_api import AliExpressAPI
    ALIEXPRESS_API_AVAILABLE = True
except ImportError as e:
    logging.warning(f"API do AliExpress não disponível: {e}")
    ALIEXPRESS_API_AVAILABLE = False

from database import adicionar_oferta, oferta_ja_existe_por_url
from telegram_poster import publicar_oferta_automatica

# Configuração de logging
logger = logging.getLogger(__name__)

# Palavras-chave para busca de ofertas no AliExpress
PALAVRAS_CHAVE_ALIEXPRESS = [
    "smartphone",
    "smartwatch",
    "fone de ouvido sem fio",
    "câmera de segurança",
    "smart tv",
    "notebook",
    "tablet",
    "cadeira gamer",
    "teclado mecânico",
    "mouse sem fio"
]

# Configuração da busca de ofertas
CONFIG_BUSCA = {
    'max_itens': 5,           # Número máximo de itens por busca
    'min_desconto': 40,       # Percentual mínimo de desconto
    'preco_max': 500.00,      # Preço máximo em reais
    'avaliacao_minima': 4.0,  # Avaliação mínima do produto
    'vendas_minimas': 50,     # Número mínimo de vendas
}

def formatar_mensagem_oferta(produto: Dict[str, Any]) -> str:
    """Formata os dados do produto para exibição no Telegram.
    
    Args:
        produto: Dicionário com os dados do produto
        
    Returns:
        String formatada com os dados do produto
    """
    # Extrai os dados do produto
    titulo = produto.get('product_title', 'Produto sem título')
    preco_original = float(produto.get('original_price', 0))
    preco_promocional = float(produto.get('sale_price', preco_original))
    desconto = int(produto.get('discount', 0))
    avaliacao = produto.get('evaluate_rate', 'N/A')
    vendas = produto.get('orders', 0)
    url = produto.get('product_detail_url', '#')
    
    # Formata os preços
    preco_original_fmt = f"R$ {preco_original:.2f}".replace('.', ',')
    preco_promocional_fmt = f"R$ {preco_promocional:.2f}".replace('.', ',')
    
    # Monta a mensagem formatada
    mensagem = (
        f"🔥 *{titulo}* 🔥\n\n"
        f"💵 *De:* ~~{preco_original_fmt}~~\n"
        f"💰 *Por:* R$ *{preco_promocional_fmt}*\n"
        f"🤑 *Desconto:* {desconto}%\n"
        f"⭐ *Avaliação:* {avaliacao}/5.0\n"
        f"🛒 *Vendidos:* {vendas}+\n\n"
        f"🔗 [Ver oferta]({url})\n"
        f"#Oferta #AliExpress #Desconto"
    )
    
    return mensagem

async def verificar_ofertas_aliexpress(context: ContextTypes.DEFAULT_TYPE):
    """
    Função para verificar ofertas no AliExpress e publicar no canal do Telegram.
    
    Esta função é chamada periodicamente pelo JobQueue do Telegram.
    
    Args:
        context: Contexto do bot do Telegram
    """
    if not ALIEXPRESS_API_AVAILABLE:
        logger.warning("API do AliExpress não disponível. Ignorando verificação de ofertas.")
        return
    
    try:
        # Inicializa a API do AliExpress
        api = AliExpressAPI()
        
        # Lista para armazenar todas as ofertas encontradas
        todas_as_ofertas = []
        
        # Busca ofertas para cada palavra-chave
        for palavra_chave in PALAVRAS_CHAVE_ALIEXPRESS:
            try:
                logger.info(f"Buscando ofertas para: {palavra_chave}")
                
                # Busca produtos no AliExpress
                resultado = api.search_products(
                    keywords=palavra_chave,
                    page_size=CONFIG_BUSCA['max_itens'],
                    sort='SALE_PRICE_ASC',  # Ordena por preço crescente
                )
                
                # Processa os resultados
                if resultado and 'result' in resultado and 'products' in resultado['result']:
                    produtos = resultado['result']['products'].get('product', [])
                    
                    # Se for um único produto, transforma em lista
                    if isinstance(produtos, dict):
                        produtos = [produtos]
                    
                    # Filtra os produtos de acordo com os critérios
                    for produto in produtos:
                        try:
                            # Calcula o desconto
                            preco_original = float(produto.get('original_price', 0))
                            preco_promocional = float(produto.get('sale_price', preco_original))
                            
                            # Ignora produtos sem desconto ou com preço zero
                            if preco_original <= 0 or preco_promocional <= 0:
                                continue
                                
                            # Calcula o percentual de desconto
                            if preco_original > preco_promocional:
                                desconto = int(((preco_original - preco_promocional) / preco_original) * 100)
                            else:
                                desconto = 0
                            
                            # Aplica os filtros
                            if (desconto >= CONFIG_BUSCA['min_desconto'] and 
                                preco_promocional <= CONFIG_BUSCA['preco_max'] and
                                float(produto.get('evaluate_rate', 0)) >= CONFIG_BUSCA['avaliacao_minima'] and
                                int(produto.get('orders', 0)) >= CONFIG_BUSCA['vendas_minimas']):
                                
                                # Adiciona o desconto ao dicionário do produto
                                produto['discount'] = desconto
                                
                                # Verifica se a oferta já foi publicada (por URL)
                                if not oferta_ja_existe_por_url(produto.get('product_detail_url', '')):
                                    todas_as_ofertas.append(produto)
                                    
                        except (ValueError, KeyError) as e:
                            logger.error(f"Erro ao processar produto: {e}")
                            continue
                
            except Exception as e:
                logger.error(f"Erro ao buscar ofertas para '{palavra_chave}': {e}")
                continue
        
        # Ordena as ofertas por desconto (maior primeiro)
        todas_as_ofertas.sort(key=lambda x: x.get('discount', 0), reverse=True)
        
        # Limita o número de ofertas
        ofertas_selecionadas = todas_as_ofertas[:CONFIG_BUSCA['max_itens']]
        
        # Publica as ofertas no canal
        for oferta in ofertas_selecionadas:
            try:
                # Formata a mensagem
                mensagem = formatar_mensagem_oferta(oferta)
                
                # Prepara os dados da oferta para publicação
                dados_oferta = {
                    'titulo': oferta.get('product_title', 'Oferta do AliExpress'),
                    'preco_original': float(oferta.get('original_price', 0)),
                    'preco': float(oferta.get('sale_price', 0)),
                    'url_produto': oferta.get('product_detail_url', ''),
                    'imagem_url': oferta.get('product_main_image_url', ''),
                    'loja': 'AliExpress',
                    'desconto': oferta.get('discount', 0)
                }
                
                # Publica a oferta
                await publicar_oferta_automatica(
                    oferta=dados_oferta,
                    context=context
                )
                
                # Salva a oferta no banco de dados
                dados_banco = {
                    'url_produto': oferta.get('product_detail_url', ''),
                    'titulo': oferta.get('product_title', ''),
                    'preco': str(float(oferta.get('sale_price', 0))),
                    'loja': 'AliExpress',
                    'fonte': 'AliExpress',
                    'preco_original': float(oferta.get('original_price', 0)),
                    'imagem_url': oferta.get('product_main_image_url', '')
                }
                
                adicionar_oferta(dados_banco)
                
                # Aguarda um pouco entre as publicações para evitar flood
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Erro ao publicar oferta: {e}")
                continue
        
        logger.info(f"Busca de ofertas no AliExpress concluída. {len(ofertas_selecionadas)} ofertas publicadas.")
        
    except Exception as e:
        logger.error(f"Erro ao verificar ofertas do AliExpress: {e}")

def agendar_verificacoes_aliexpress(application):
    """
    Agenda as verificações periódicas de ofertas no AliExpress.
    
    Args:
        application: Instância da aplicação do bot do Telegram
    """
    if not ALIEXPRESS_API_AVAILABLE:
        logger.warning("API do AliExpress não disponível. Verificações não agendadas.")
        return
    
    try:
        # Remove jobs existentes para evitar duplicação
        current_jobs = application.job_queue.get_jobs_by_name('verificar_ofertas_aliexpress')
        for job in current_jobs:
            job.schedule_removal()
        
        # Agenda a verificação a cada 6 horas
        application.job_queue.run_repeating(
            callback=verificar_ofertas_aliexpress,
            interval=timedelta(hours=6),
            first=timedelta(seconds=30),  # Primeira execução em 30 segundos
            name='verificar_ofertas_aliexpress'
        )
        
        logger.info("Verificações periódicas do AliExpress agendadas com sucesso.")
        
    except Exception as e:
        logger.error(f"Erro ao agendar verificações do AliExpress: {e}")
