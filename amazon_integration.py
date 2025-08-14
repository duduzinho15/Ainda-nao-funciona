"""
Módulo de integração com a API de Produtos da Amazon (PA-API v5).

Este módulo fornece funções para buscar ofertas de produtos na Amazon usando a PA-API v5
e agendar verificações periódicas de ofertas. Se a API não estiver disponível, 
utiliza web scraping como fallback.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

from telegram.ext import ContextTypes

# Tenta importar o módulo da Amazon, mas não falha se não estiver disponível
try:
    from amazon_api import buscar_ofertas_amazon, create_api_client
    AMAZON_API_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Amazon PA-API não disponível: {e}. Usando web scraping como fallback.")
    AMAZON_API_AVAILABLE = False

# Importa apenas o necessário para evitar importação circular
from database import adicionar_oferta
from telegram_poster import publicar_oferta_automatica

# Configuração de logging
logger = logging.getLogger(__name__)

# Palavras-chave para busca de ofertas na Amazon
PALAVRAS_CHAVE_AMAZON = [
    "notebook gamer",
    "ssd 1tb",
    "monitor 144hz",
    "smartphone",
    "fone de ouvido bluetooth",
    "smartwatch",
    "tv 4k",
    "echo dot",
    "kindle",
    "cadeira gamer"
]

# Configuração da busca de ofertas
CONFIG_BUSCA = {
    'max_itens': 5,  # Número máximo de itens por busca
    'min_desconto': 30,  # Percentual mínimo de desconto
    'categorias': ['Electronics', 'Computers'],  # Categorias de busca
    'condicao': 'New',  # Condição do produto (New, Used, Refurbished, etc.)
    'vendedor': 'Amazon',  # Filtro por vendedor
}

async def verificar_ofertas_amazon(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Função para verificar ofertas na Amazon e publicar no canal do Telegram.
    
    Esta função é chamada periodicamente pelo JobQueue do Telegram.
    
    Args:
        context: Contexto do bot do Telegram
    """
    logger.info("Iniciando verificação de ofertas na Amazon...")
    
    # Verifica se a API da Amazon está disponível
    if not AMAZON_API_AVAILABLE:
        logger.info("API da Amazon não disponível. Pulando verificação de ofertas.")
        await context.bot.send_message(
            chat_id=context.bot_data.get('chat_id', config.TELEGRAM_CHAT_ID),
            text="⚠️ *Atenção*: A integração com a Amazon está temporariamente indisponível. "
                 "Usando apenas web scraping de outras lojas.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Cria o cliente da API da Amazon
        amazon_client = create_api_client()
        if not amazon_client:
            logger.error("Não foi possível criar o cliente da API da Amazon")
            return
            
        # Busca ofertas para cada palavra-chave
        for palavra_chave in PALAVRAS_CHAVE_AMAZON:
            try:
                logger.info(f"Buscando ofertas para: {palavra_chave}")
                
                # Busca ofertas na Amazon
                ofertas = await buscar_ofertas_amazon(
                    palavras_chave=[palavra_chave],
                    max_itens=CONFIG_BUSCA['max_itens'],
                    min_saving_percent=CONFIG_BUSCA['min_desconto'],
                    search_index=CONFIG_BUSCA['categorias'][0],  # Usa a primeira categoria
                    condition=CONFIG_BUSCA['condicao'],
                    merchant=CONFIG_BUSCA['vendedor']
                )
                
                if not ofertas:
                    logger.info(f"Nenhuma oferta encontrada para: {palavra_chave}")
                    continue
                    
                logger.info(f"Encontradas {len(ofertas)} ofertas para: {palavra_chave}")
                
                # Publica cada oferta encontrada
                for oferta in ofertas:
                    try:
                        # Formata a oferta para o formato esperado
                        oferta_formatada = {
                            'titulo': oferta.get('title', 'Produto sem título'),
                            'preco': oferta.get('price', 'Preço não disponível'),
                            'preco_original': oferta.get('list_price', ''),
                            'url_produto': oferta.get('url', ''),
                            'imagem_url': oferta.get('image_url', ''),
                            'loja': 'Amazon',
                            'fonte': 'Amazon PA-API',
                            'asin': oferta.get('asin', '')
                        }
                        
                        # Publica a oferta
                        await publicar_oferta_automatica(
                            oferta=oferta_formatada,
                            context=context
                        )
                        
                        # Pequena pausa entre publicações para evitar rate limiting
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Erro ao publicar oferta: {e}", exc_info=True)
                        continue
                        
            except Exception as e:
                logger.error(f"Erro ao buscar ofertas para '{palavra_chave}': {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Erro inesperado ao verificar ofertas da Amazon: {e}", exc_info=True)
        
    logger.info("Verificação de ofertas da Amazon concluída")

def agendar_verificacoes_amazon(application) -> None:
    """
    Agenda as verificações periódicas de ofertas na Amazon.
    
    Args:
        application: Instância da aplicação do bot do Telegram
    """
    try:
        # Verifica se a aplicação e o job_queue estão disponíveis
        if not hasattr(application, 'job_queue') or application.job_queue is None:
            logger.warning("Job queue não disponível. Verificando se o updater está disponível...")
            if hasattr(application, 'updater') and hasattr(application.updater, 'job_queue'):
                application.job_queue = application.updater.job_queue
            else:
                logger.error("Não foi possível acessar o job queue. Verifique a inicialização do bot.")
                return
        
        # Remove jobs existentes para evitar duplicação
        if hasattr(application.job_queue, 'jobs'):
            for job in application.job_queue.jobs():
                if hasattr(job, 'name') and job.name == 'verificar_ofertas_amazon':
                    job.schedule_removal()
        
        # Verifica se a API da Amazon está disponível antes de agendar
        if not AMAZON_API_AVAILABLE:
            logger.warning("API da Amazon não disponível. Não foi possível agendar verificações.")
            # Envia mensagem apenas se o bot já estiver em execução
            if hasattr(application, 'bot') and hasattr(application.bot, 'send_message'):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(application.bot.send_message(
                            chat_id=application.bot_data.get('chat_id', config.TELEGRAM_CHAT_ID),
                            text="⚠️ *Atenção*: A integração com a Amazon está desativada. "
                                 "Verifique as credenciais da API para ativar.",
                            parse_mode='Markdown'
                        ))
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem de aviso: {e}")
            return
        
        # Agenda a verificação para rodar a cada 6 horas (21600 segundos)
        # Com um atraso inicial de 10 segundos para dar tempo do bot inicializar
        if hasattr(application.job_queue, 'run_repeating'):
            application.job_queue.run_repeating(
                callback=verificar_ofertas_amazon,
                interval=21600,  # 6 horas
                first=10,  # 10 segundos
                name='verificar_ofertas_amazon'
            )
            logger.info("Verificações periódicas da Amazon agendadas com sucesso")
        else:
            logger.error("Não foi possível agendar as verificações: método run_repeating não disponível")
    except Exception as e:
        logger.error(f"Erro ao agendar verificações da Amazon: {e}", exc_info=True)
