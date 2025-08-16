import logging
import re
from typing import Optional, Dict, Any, List

from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode

import config
from database import adicionar_oferta_manual, adicionar_oferta, oferta_ja_existe, oferta_ja_existe_por_url, extrair_dominio_loja
from utils.images import fetch_bytes, fetch_og_image

# Configuração de logging
logger = logging.getLogger(__name__)

def html_escape(s: str | None) -> str:
    """Escapa caracteres especiais para HTML"""
    if not s: 
        return ""
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def build_buttons(url_principal: str, extras: dict[str,str] | None = None):
    """Constrói botões inline para a oferta"""
    btns = [[InlineKeyboardButton("🛒 Comprar agora", url=url_principal)]]
    if extras:
        for label, url in list(extras.items())[:2]:
            btns[0].append(InlineKeyboardButton(f"🔎 {label}", url=url))
    return InlineKeyboardMarkup(btns)

async def _send_card(bot, chat_id, caption_html, url_btn, maybe_img_url, reply_markup=None):
    """
    Envia cartão de oferta com imagem grande via bytes ou fallback robusto
    
    Args:
        bot: Instância do bot do Telegram
        chat_id: ID do chat para enviar
        caption_html: Legenda formatada em HTML
        url_btn: URL principal para botão (usada para OG image se não tiver imagem)
        maybe_img_url: URL da imagem da oferta (opcional)
        reply_markup: Teclado inline (opcional)
    """
    img_url = maybe_img_url
    image_source = 'none'
    
    # Se não tiver imagem da oferta, tenta extrair OG image da URL
    if not img_url and url_btn:
        img_url = fetch_og_image(url_btn)
        if img_url:
            image_source = 'og:image'
            logger.info(f"Imagem extraída via OG: {img_url[:80]}...")
    
    # Tenta enviar como bytes (mais sólido contra hotlinking)
    if img_url:
        buf = fetch_bytes(img_url)
        try:
            if buf:
                image_source = 'offer' if maybe_img_url else 'og:image'
                logger.info(f"Enviando imagem via bytes (fonte: {image_source})")
                return await bot.send_photo(
                    chat_id=chat_id, photo=buf, caption=caption_html,
                    parse_mode=ParseMode.HTML, reply_markup=reply_markup
                )
            else:
                image_source = 'offer' if maybe_img_url else 'og:image'
                logger.info(f"Enviando imagem via URL (fonte: {image_source})")
                return await bot.send_photo(
                    chat_id=chat_id, photo=img_url, caption=caption_html,
                    parse_mode=ParseMode.HTML, reply_markup=reply_markup
                )
        except Exception as e:
            logger.warning(f"Falha ao enviar imagem ({image_source}): {e}")
            pass

    # Fallback: texto SEM preview
    logger.info("Fallback para texto sem preview")
    return await bot.send_message(
        chat_id=chat_id, text=caption_html, parse_mode=ParseMode.HTML,
        disable_web_page_preview=True, reply_markup=reply_markup
    )

def format_caption_html(oferta: Dict[str, Any]) -> str:
    """Formata a legenda da oferta em HTML"""
    titulo = html_escape(oferta.get("titulo", "Oferta"))
    preco_atual = html_escape(str(oferta.get("preco_atual", "—")))
    preco_original = html_escape(str(oferta.get("preco_original", "")))
    desconto = oferta.get("desconto", 0)
    loja = html_escape(oferta.get("loja", "Loja"))
    origem = html_escape(oferta.get("fonte", "Sistema"))
    
    linhas = [f"🔥 <b>{titulo}</b>"]
    
    # Adiciona características se disponíveis
    if oferta.get("caracteristicas"):
        for c in oferta["caracteristicas"][:4]:
            linhas.append(f"• {html_escape(c)}")
    
    # Adiciona preços
    linhas.append(f"💰 <b>Preço:</b> {preco_atual}")
    
    # Adiciona preço original e desconto se disponíveis
    if preco_original and preco_original != "—" and desconto and desconto > 0:
        linhas.append(f"💸 <b>De:</b> {preco_original}")
        linhas.append(f"🔥 <b>Desconto:</b> {desconto}% OFF")
    
    linhas.append(f"🏷 {loja} | {origem}")
    
    return "\n".join(linhas)

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
        mensagem: Texto formatado da oferta (já em HTML)
        imagem_url: URL da imagem da oferta (opcional)
        url_afiliado: URL de afiliado para o botão (opcional)
        chat_id: ID do chat para publicar (opcional, usa o configurado por padrão)
        context: Contexto do bot (opcional, usado para obter a instância do bot)
        
    Returns:
        bool: True se a publicação foi bem-sucedida, False caso contrário
    """
    # Obtém o bot do contexto
    if context is None or not hasattr(context, 'bot'):
        logger.error("Contexto inválido ou sem instância do bot")
        return False
        
    bot = context.bot
        
    if not chat_id:
        chat_id = config.TELEGRAM_CHAT_ID
    
    try:
        # Cria o teclado inline se houver URL de afiliado
        reply_markup = None
        if url_afiliado:
            reply_markup = build_buttons(url_afiliado)
        
        # Usa o novo sistema de cartão com imagem grande
        await _send_card(
            bot=bot,
            chat_id=chat_id,
            caption_html=mensagem,
            url_btn=url_afiliado,
            maybe_img_url=imagem_url,
            reply_markup=reply_markup
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao publicar oferta: {e}")
        return False

async def comando_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recebe um comando /oferta, formata e envia para o canal,
    restringindo o uso ao administrador.
    
    Formato: /oferta <link> <preço> <título completo>
    Exemplo: /oferta https://www.magazineluiza.com.br/notebook-dell-inspiron-3501/p/123456/te/1234/ 2999,90 Notebook Dell Inspiron 3501 i5 8GB 256GB SSD
    """
    try:
        # 1. Verificar se o comando veio de uma mensagem válida
        if not update or not update.message or not update.effective_user:
            logger.warning("Comando /oferta recebido sem mensagem ou usuário válido")
            return

        # 2. Verificar se o usuário é o administrador
        user = update.effective_user
        if not user or not user.id:
            logger.warning("Usuário não encontrado ou ID inválido em comando_oferta")
            return
            
        if str(user.id) != str(config.ADMIN_USER_ID):
            logger.warning(f"Acesso negado para o usuário {user.id}")
            await update.message.reply_text("❌ Acesso negado. Apenas o administrador pode usar este comando.")
            return

        # 3. Verificar argumentos fornecidos
        if not context.args or len(context.args) < 3:
            logger.warning("Argumentos insuficientes para o comando /oferta")
            await update.message.reply_text(
                "❌ Formato incorreto!\n"
                "Uso: /oferta <link> <preço> <título completo>\n"
                "Exemplo: /oferta https://www.magazineluiza.com.br/notebook... R$2999,90 Notebook Dell Inspiron 3501"
            )
            return

        # 4. Extrair e validar os argumentos
        link = context.args[0].strip()
        preco = context.args[1].strip()
        titulo = " ".join(context.args[2:]).strip()
        
        # Validações básicas
        if not link.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ O link fornecido não é válido. Certifique-se de incluir http:// ou https://")
            return
            
        if not any(char.isdigit() for char in preco):
            await update.message.reply_text("❌ O preço deve conter valores numéricos")
            return

        # 5. Extrair domínio da loja para identificação
        dominio_loja = extrair_dominio_loja(link)
        
        # 6. Preparar dados da oferta para o banco de dados
        oferta = {
            'url_produto': link,
            'titulo': titulo,
            'preco_atual': preco,
            'loja': dominio_loja.capitalize(),
            'fonte': 'Comando',
            'url_fonte': link
        }
        
        # 7. Verificar se a oferta já existe
        if oferta_ja_existe_por_url(link):
            logger.info(f"Oferta já existe no banco de dados: {link}")
            await update.message.reply_text("ℹ️ Esta oferta já foi publicada anteriormente.")
            return

        # 8. Formatar a mensagem para o Telegram (HTML)
        mensagem_html = format_caption_html(oferta)
        
        # 9. Publicar a oferta usando o novo sistema
        sucesso = await publicar_oferta(
            mensagem=mensagem_html,
            url_afiliado=link,  # Por enquanto usa o link original
            context=context
        )
        
        if sucesso:
            # 10. Adicionar ao banco de dados
            adicionar_oferta_manual(link, titulo, preco)
            
            # 11. Confirmar sucesso
            await update.message.reply_text(
                "✅ Oferta publicada com sucesso no canal!\n"
                f"📢 Verifique: https://t.me/garimpeirogeek"
            )
            
            logger.info(f"✅ Oferta publicada via comando: {titulo[:50]}...")
        else:
            await update.message.reply_text("❌ Erro ao publicar a oferta. Tente novamente.")
            logger.error(f"❌ Falha ao publicar oferta via comando: {titulo[:50]}...")
            
    except Exception as e:
        logger.error(f"❌ Erro no comando /oferta: {e}")
        await update.message.reply_text("❌ Erro interno. Tente novamente ou contate o administrador.")

async def publicar_oferta_automatica(
    oferta: Dict[str, Any], 
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: Optional[str] = None
) -> bool:
    """
    Publica uma oferta automaticamente no canal do Telegram.
    
    Args:
        oferta: Dicionário com dados da oferta
        context: Contexto do bot
        chat_id: ID do chat para publicar (opcional)
        
    Returns:
        bool: True se a publicação foi bem-sucedida, False caso contrário
    """
    try:
        # Obtém o bot do contexto
        if context is None or not hasattr(context, 'bot'):
            logger.error("Contexto inválido ou sem instância do bot")
            return False
            
        bot = context.bot
            
        if not chat_id:
            chat_id = config.TELEGRAM_CHAT_ID
        
        # Formata a legenda em HTML
        caption_html = format_caption_html(oferta)
        
        # Obtém URL de afiliado ou URL do produto
        url_afiliado = oferta.get('url_afiliado') or oferta.get('url_produto')
        
        # Obtém URL da imagem
        img_url = oferta.get('imagem_url')
        
        # Cria botões inline
        reply_markup = None
        if url_afiliado:
            reply_markup = build_buttons(url_afiliado)
        
        # Usa o novo sistema de cartão com imagem grande
        await _send_card(
            bot=bot,
            chat_id=chat_id,
            caption_html=caption_html,
            url_btn=url_afiliado,
            maybe_img_url=img_url,
            reply_markup=reply_markup
        )
        
        logger.info(f"✅ Oferta publicada automaticamente: {oferta.get('titulo', 'Sem título')[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao publicar oferta automaticamente: {e}")
        return False
