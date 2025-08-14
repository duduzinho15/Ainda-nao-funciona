import logging
import re
from typing import Optional, Dict, Any, List

from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode

import config
from database import adicionar_oferta_manual, adicionar_oferta, oferta_ja_existe, extrair_dominio_loja

# Configuração de logging
logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """
    Escapa o texto para o formato MarkdownV2 do Telegram.
    
    Args:
        text: Texto a ser escapado
        
    Returns:
        str: Texto escapado
    """
    if not text:
        return ""
        
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def publicar_oferta(
    mensagem: str, 
    imagem_url: Optional[str] = None, 
    url_afiliado: Optional[str] = None,
    chat_id: Optional[str] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None
) -> bool:
    """
    Publica uma oferta no canal do Telegram.
    
    Args:
        mensagem: Texto formatado da oferta (já em MarkdownV2)
        imagem_url: URL da imagem da oferta (opcional)
        url_afiliado: URL de afiliado para o botão (opcional)
        chat_id: ID do chat para publicar (opcional, usa o configurado por padrão)
        context: Contexto do bot (opcional, usado para obter a instância do bot)
        
    Returns:
        bool: True se a publicação foi bem-sucedida, False caso contrário
    """
    # Obtém o bot do contexto ou da aplicação
    bot = None
    if context is not None and hasattr(context, 'bot'):
        bot = context.bot
    else:
        try:
            from main import application  # Importação local para evitar importação circular
            if application is not None and hasattr(application, 'bot'):
                bot = application.bot
        except Exception as e:
            logger.error(f"Erro ao obter a instância do bot: {e}")
            return False
    
    if bot is None:
        logger.error("Não foi possível acessar a instância do bot")
        return False
        
    if not chat_id:
        chat_id = config.TELEGRAM_CHAT_ID
    
    try:
        # Cria o teclado inline se houver URL de afiliado
        reply_markup = None
        if url_afiliado:
            keyboard = [
                [
                    InlineKeyboardButton("🛒 Ver Oferta", url=url_afiliado),
                    InlineKeyboardButton("📢 Ver Canal", url="https://t.me/garimpeirogeek")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Publica a oferta com ou sem imagem
        if imagem_url:
            # Tenta enviar a foto com legenda
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=imagem_url,
                    caption=mensagem,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup
                )
                return True
            except Exception as e:
                logger.warning(f"Erro ao enviar foto, tentando apenas texto: {e}")
                # Se falhar, tenta enviar apenas o texto
        
        # Se não tiver imagem ou falhar ao enviar a foto, envia apenas o texto
        await bot.send_message(
            chat_id=chat_id,
            text=mensagem,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=not bool(imagem_url),  # Desativa preview se tiver imagem
            reply_markup=reply_markup
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao publicar oferta: {e}", exc_info=True)
        return False

# Resto do código do arquivo original...
