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
            'preco': preco,
            'loja': dominio_loja.capitalize(),
            'fonte': 'Comando',
            'url_fonte': link
        }
        
        # 7. Verificar se a oferta já existe
        if oferta_ja_existe(link):
            logger.info(f"Oferta já existe no banco de dados: {link}")
            await update.message.reply_text("ℹ️ Esta oferta já foi publicada anteriormente.")
            return

        # 8. Formatar a mensagem para o Telegram
        linhas = []
        
        # Título
        linhas.append(f"🔥 *{escape_markdown_v2(titulo)}*\n")
        
        # Preço (formato simples, já que não temos preço original para o comando manual)
        linhas.append(f"💵 *Preço:* {escape_markdown_v2(str(preco))}\n")
        
        # Loja
        linhas.append(f"🏪 *Loja:* {escape_markdown_v2(dominio_loja.capitalize())}")
        
        # Links
        linhas.append(f"\n🛒 [Ver oferta]({link})")
        linhas.append(f"🔗 [Gostou? Compartilhe!](https://t.me/share/url?url={link.replace('&', '%26')})")
        
        # Junta todas as linhas para formar a mensagem final
        mensagem = '\n'.join(linhas)

        # 9. Publicar a oferta
        sucesso = await publicar_oferta(
            mensagem=mensagem,
            url_afiliado=link,  # Será convertido para link de afiliado se disponível
            chat_id=config.TELEGRAM_CHAT_ID,
            context=context
        )
        
        # 10. Se a publicação for bem-sucedida, salvar no banco de dados
        if sucesso:
            if adicionar_oferta(oferta):
                logger.info(f"Oferta adicionada via comando: {titulo}")
                await update.message.reply_text("✅ Oferta publicada com sucesso!")
            else:
                logger.warning(f"Falha ao salvar oferta no banco de dados: {titulo}")
                await update.message.reply_text(
                    "⚠️ Oferta publicada, mas não foi possível salvar no banco de dados."
                )
        else:
            logger.error(f"Falha ao publicar oferta: {titulo}")
            await update.message.reply_text(
                "❌ Falha ao publicar a oferta. Verifique os logs para mais detalhes."
            )
            
    except Exception as e:
        logger.error(f"Erro ao processar comando /oferta: {e}", exc_info=True)
        if update and update.message:
            await update.message.reply_text(
                "❌ Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."
            )

def calcular_desconto(preco_atual: str, preco_original: str) -> Optional[str]:
    """
    Calcula o percentual de desconto entre dois preços.
    
    Args:
        preco_atual: Preço atual como string (ex: 'R$ 1.999,90')
        preco_original: Preço original como string (ex: 'R$ 2.499,90')
        
    Returns:
        str: Percentual de desconto formatado (ex: '20%') ou None se não for possível calcular
    """
    try:
        # Remove caracteres não numéricos, exceto vírgula e ponto
        def parse_price(price_str):
            # Remove R$, espaços e converte vírgula para ponto
            clean = price_str.lower().replace('r$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return float(clean) if clean else 0
        
        atual = parse_price(preco_atual)
        original = parse_price(preco_original)
        
        if atual > 0 and original > 0 and original > atual:
            desconto = ((original - atual) / original) * 100
            return f"{int(round(desconto))}%"
    except Exception as e:
        logger.warning(f"Erro ao calcular desconto: {e}")
    
    return None

async def publicar_oferta_automatica(
    oferta: Dict[str, Any], 
    context: Optional[ContextTypes.DEFAULT_TYPE] = None
) -> bool:
    """
    Publica automaticamente uma oferta no canal do Telegram.
    
    Esta função é usada para publicar ofertas encontradas automaticamente
    por scrapers ou APIs, como a da Amazon.
    
    Args:
        oferta: Dicionário com os dados da oferta a ser publicada
        context: Contexto do bot do Telegram (opcional)
        
    Returns:
        bool: True se a publicação foi bem-sucedida, False caso contrário
    """
    try:
        # Extrai os dados da oferta
        titulo = oferta.get('titulo', 'Oferta Especial')
        preco = oferta.get('preco', 'Preço não disponível')
        preco_original = oferta.get('preco_original')
        url = oferta.get('url_produto', '')
        imagem_url = oferta.get('imagem_url')
        loja = oferta.get('loja', 'Loja')
        menor_preco_historico = oferta.get('menor_preco_historico', False)
        
        # Calcula o desconto se houver preço original
        desconto = None
        if preco_original:
            desconto = calcular_desconto(str(preco), str(preco_original))
        
        # Constrói a mensagem
        linhas = []
        
        # Adiciona destaque para menor preço histórico
        if menor_preco_historico:
            linhas.append("🔥📉 *MENOR PREÇO HISTÓRICO!* 📉🔥\n")
        
        # Título
        linhas.append(f"🔥 *{escape_markdown_v2(titulo)}*\n")
        
        # Preços
        if preco_original and desconto:
            linhas.append(f"💰 *De ~{escape_markdown_v2(str(preco_original))}~ por")
            linhas.append(f"💵 *Preço:* {escape_markdown_v2(str(preco))} (*{desconto} de desconto*)\n")
        else:
            linhas.append(f"💵 *Preço:* {escape_markdown_v2(str(preco))}\n")
        
        # Loja
        linhas.append(f"🏪 *Loja:* {escape_markdown_v2(loja)}")
        
        # Links
        linhas.append(f"\n🛒 [Ver oferta]({url})")
        linhas.append(f"🔗 [Gostou? Compartilhe!](https://t.me/share/url?url={url.replace('&', '%26')})")
        
        # Junta todas as linhas para formar a mensagem final
        mensagem = '\n'.join(linhas)
        
        # Publica a oferta
        sucesso = await publicar_oferta(
            mensagem=mensagem,
            imagem_url=imagem_url,
            url_afiliado=url,
            context=context
        )
        
        if sucesso:
            logger.info(f"Oferta publicada com sucesso: {titulo}")
            
            # Notifica usuários interessados se o sistema estiver disponível
            try:
                from notification_system import notify_users_about_offer
                if context and hasattr(context, 'bot'):
                    notification_results = await notify_users_about_offer(context.bot, oferta)
                    if notification_results['notified_users'] > 0:
                        logger.info(f"📢 {notification_results['successful_notifications']} usuários notificados sobre a oferta")
                    else:
                        logger.info("ℹ️ Nenhum usuário interessado para notificar")
            except ImportError:
                logger.debug("Sistema de notificações não disponível")
            except Exception as e:
                logger.error(f"Erro ao notificar usuários: {e}")
        else:
            logger.error(f"Falha ao publicar oferta: {titulo}")
            
        return sucesso
        
    except Exception as e:
        logger.error(f"Erro em publicar_oferta_automatica: {e}", exc_info=True)
        return False
