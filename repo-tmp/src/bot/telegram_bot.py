"""
Bot do Telegram para postagem automática de ofertas - Garimpeiro Geek

Funcionalidades:
- Postagem automática de ofertas validadas
- Integração com PostingManager
- Sistema de agendamento
- Moderação de conteúdo
- Métricas de performance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.core.config import TELEGRAM_ADMIN_IDS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from src.core.enhanced_metrics import log_bot_event, log_offer_posted
from src.core.models import Offer
from src.posting.posting_manager import PostingManager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class GarimpeiroGeekBot:
    """Bot principal do Garimpeiro Geek para postagem de ofertas"""

    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.posting_manager = PostingManager()
        self.scheduled_posts: List[Dict[str, Any]] = []
        self.post_queue: List[Offer] = []

        # Configurar handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Configura os handlers do bot"""
        # Comandos administrativos
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))

        # Comandos de moderação
        self.application.add_handler(CommandHandler("post", self.post_offer_command))
        self.application.add_handler(
            CommandHandler("schedule", self.schedule_post_command)
        )
        self.application.add_handler(CommandHandler("queue", self.show_queue_command))
        self.application.add_handler(
            CommandHandler("approve", self.approve_offer_command)
        )
        self.application.add_handler(
            CommandHandler("reject", self.reject_offer_command)
        )

        # Callbacks para botões inline
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Handler para mensagens de texto (para processar links)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_message)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text(
                "🚫 Acesso negado. Este bot é apenas para administradores."
            )
            return

        welcome_text = f"""
🤖 **Garimpeiro Geek Bot - Sistema de Ofertas**

**Comandos disponíveis:**
📝 `/post` - Postar oferta imediatamente
⏰ `/schedule` - Agendar post para depois
📋 `/queue` - Ver fila de ofertas
✅ `/approve` - Aprovar oferta pendente
❌ `/reject` - Rejeitar oferta
📊 `/status` - Status do sistema

**Status:** ✅ Sistema operacional
**Ofertas na fila:** {len(self.post_queue)} ofertas
        """

        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
        log_bot_event("bot_start", str(user_id), "Bot iniciado")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
📚 **Ajuda - Garimpeiro Geek Bot**

**Como usar:**
1. **Envie um link** de oferta para processar
2. **Use /post** para publicar imediatamente
3. **Use /schedule** para agendar publicação
4. **Modere conteúdo** com /approve ou /reject

**Formatos aceitos:**
- ✅ Links de afiliados válidos
- ✅ Shortlinks das plataformas
- ✅ URLs com tracking correto

**Plataformas suportadas:**
- 🛒 Amazon, Shopee, Mercado Livre
- 🏪 Magazine Luiza, AliExpress
- 🔗 Awin, Rakuten

**Para suporte:** @garimpeirogeek_support
        """

        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status - Mostra status do sistema"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        # Estatísticas do sistema
        total_offers = len(self.post_queue)
        scheduled_posts = len(self.scheduled_posts)

        # Métricas dos validadores
        from src.affiliate.magazineluiza import get_metrics as magalu_metrics
        from src.affiliate.mercadolivre import get_metrics as ml_metrics
        from src.affiliate.shopee import get_metrics as shopee_metrics

        shopee_stats = shopee_metrics()
        ml_stats = ml_metrics()
        magalu_stats = magalu_metrics()

        status_text = f"""
📊 **Status do Sistema - Garimpeiro Geek**

**🔄 Sistema:**
- Status: ✅ Operacional
- Ofertas na fila: {total_offers}
- Posts agendados: {scheduled_posts}
- Última verificação: {datetime.now().strftime('%H:%M:%S')}

**📈 Métricas dos Validadores:**
- **Shopee**: {shopee_stats['category_blocked']} categorias bloqueadas
- **ML**: {ml_stats['product_blocked']} produtos bloqueados
- **Magalu**: {magalu_stats['domain_blocked']} domínios bloqueados

**🔧 Plataformas Ativas:**
- ✅ Amazon, Shopee, Mercado Livre
- ✅ Magazine Luiza, AliExpress, Awin
- ✅ Rakuten

**📱 Canal:** @garimpeirogeek_ofertas
        """

        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

    async def post_offer_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Comando /post - Posta oferta imediatamente"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        if not self.post_queue:
            await update.message.reply_text("📭 Nenhuma oferta na fila para postar.")
            return

        # Pegar a primeira oferta da fila
        offer = self.post_queue.pop(0)

        # Postar no canal
        success = await self._post_to_channel(offer)

        if success:
            await update.message.reply_text(
                f"✅ Oferta postada com sucesso!\n"
                f"📱 Plataforma: {offer.platform}\n"
                f"🔗 Link: {offer.affiliate_url[:50]}..."
            )
            log_offer_posted(
                offer.platform, "manual_post", "Oferta postada manualmente"
            )
        else:
            await update.message.reply_text("❌ Erro ao postar oferta. Verifique logs.")

    async def schedule_post_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Comando /schedule - Agenda post para depois"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        if not self.post_queue:
            await update.message.reply_text("📭 Nenhuma oferta na fila para agendar.")
            return

        # Interface para agendamento
        keyboard = [
            [
                InlineKeyboardButton("⏰ 1 hora", callback_data="schedule_1h"),
                InlineKeyboardButton("⏰ 3 horas", callback_data="schedule_3h"),
                InlineKeyboardButton("⏰ 6 horas", callback_data="schedule_6h"),
            ],
            [
                InlineKeyboardButton(
                    "🌅 Amanhã 9h", callback_data="schedule_tomorrow_9"
                ),
                InlineKeyboardButton(
                    "🌅 Amanhã 18h", callback_data="schedule_tomorrow_18"
                ),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="schedule_cancel")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⏰ **Agendar Post**\n\n"
            "Escolha quando deseja publicar a próxima oferta da fila:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def show_queue_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Comando /queue - Mostra fila de ofertas"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        if not self.post_queue:
            await update.message.reply_text("📭 Fila de ofertas vazia.")
            return

        queue_text = "📋 **Fila de Ofertas**\n\n"

        for i, offer in enumerate(
            self.post_queue[:10], 1
        ):  # Mostrar apenas as 10 primeiras
            platform_emoji = self._get_platform_emoji(offer.platform)
            queue_text += f"{i}. {platform_emoji} **{offer.platform}**\n"
            queue_text += f"   🔗 {offer.affiliate_url[:60]}...\n"
            queue_text += f"   📝 {offer.description[:50]}...\n\n"

        if len(self.post_queue) > 10:
            queue_text += f"... e mais {len(self.post_queue) - 10} ofertas"

        await update.message.reply_text(queue_text, parse_mode=ParseMode.MARKDOWN)

    async def approve_offer_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Comando /approve - Aprova oferta pendente"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        # Implementar lógica de aprovação
        await update.message.reply_text("✅ Sistema de aprovação em desenvolvimento.")

    async def reject_offer_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Comando /reject - Rejeita oferta pendente"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Acesso negado.")
            return

        # Implementar lógica de rejeição
        await update.message.reply_text("❌ Sistema de rejeição em desenvolvimento.")

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto (links de ofertas)"""
        user_id = update.effective_user.id

        if user_id not in TELEGRAM_ADMIN_IDS:
            await update.message.reply_text(
                "🚫 Apenas administradores podem enviar ofertas."
            )
            return

        message_text = update.message.text

        if not message_text.startswith(("http://", "https://")):
            await update.message.reply_text(
                "🔗 Por favor, envie um link de oferta válido."
            )
            return

        # Processar link
        await self._process_offer_link(update, message_text)

    async def _process_offer_link(self, update: Update, url: str):
        """Processa link de oferta enviado"""
        try:
            # Detectar plataforma
            platform = self._detect_platform(url)

            if not platform:
                await update.message.reply_text(
                    "❌ **Plataforma não suportada**\n\n"
                    "Plataformas aceitas:\n"
                    "🛒 Amazon, Shopee, Mercado Livre\n"
                    "🏪 Magazine Luiza, AliExpress\n"
                    "🔗 Awin, Rakuten"
                )
                return

            # Criar oferta
            offer = Offer(
                platform=platform,
                affiliate_url=url,
                description="Oferta enviada via bot",
                price=None,
                created_at=datetime.now(),
            )

            # Validar com PostingManager
            validation_result = self.posting_manager.validate_affiliate_url(
                url, platform
            )

            if not validation_result.is_valid:
                await update.message.reply_text(
                    f"❌ **Link inválido**\n\n"
                    f"**Erro:** {validation_result.blocked_reason}\n"
                    f"**Plataforma:** {platform}\n\n"
                    f"Verifique se o link está correto e tente novamente."
                )
                return

            # Adicionar à fila
            self.post_queue.append(offer)

            # Confirmar recebimento
            platform_emoji = self._get_platform_emoji(platform)
            await update.message.reply_text(
                f"✅ **Oferta recebida e validada!**\n\n"
                f"{platform_emoji} **Plataforma:** {platform}\n"
                f"🔗 **Link:** {url[:60]}...\n"
                f"📋 **Status:** Na fila para publicação\n"
                f"📊 **Posição:** #{len(self.post_queue)}\n\n"
                f"Use `/post` para publicar imediatamente ou `/schedule` para agendar."
            )

            log_bot_event(
                "offer_received", platform, f"Oferta {platform} recebida e validada"
            )

        except Exception as e:
            logger.error(f"Erro ao processar link: {e}")
            await update.message.reply_text(
                "❌ **Erro interno**\n\n"
                "Ocorreu um erro ao processar o link. Tente novamente ou contate o suporte."
            )

    async def _post_to_channel(self, offer: Offer) -> bool:
        """Posta oferta no canal do Telegram"""
        try:
            platform_emoji = self._get_platform_emoji(offer.platform)

            # Formatar mensagem da oferta
            post_text = f"""
🔥 **OFERTA IMPERDÍVEL!** 🔥

{platform_emoji} **{offer.platform.upper()}**

🔗 **Link:** {offer.affiliate_url}

📝 **Descrição:** {offer.description or 'Oferta especial selecionada pelo Garimpeiro Geek!'}

⏰ **Válida até:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

💡 **Dica:** Clique no link para aproveitar!

---
🤖 *Postado automaticamente pelo @garimpeirogeek_bot*
            """.strip()

            # Botões inline
            keyboard = [
                [
                    InlineKeyboardButton("🛒 Ver Oferta", url=offer.affiliate_url),
                    InlineKeyboardButton(
                        "📱 Canal", url="https://t.me/garimpeirogeek_ofertas"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⭐️ Avaliar", callback_data=f"rate_{offer.platform}"
                    ),
                    InlineKeyboardButton(
                        "📤 Compartilhar", callback_data="share_offer"
                    ),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Enviar para o canal
            await self.application.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=post_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            log_offer_posted(offer.platform, "channel_post", "Oferta postada no canal")
            return True

        except Exception as e:
            logger.error(f"Erro ao postar no canal: {e}")
            return False

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks dos botões inline"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith("schedule_"):
            await self._handle_schedule_callback(query, data)
        elif data.startswith("rate_"):
            await self._handle_rate_callback(query, data)
        elif data == "share_offer":
            await self._handle_share_callback(query)
        elif data == "schedule_cancel":
            await query.edit_message_text("❌ Agendamento cancelado.")

    async def _handle_schedule_callback(self, query, data: str):
        """Processa callback de agendamento"""
        if not self.post_queue:
            await query.edit_message_text("📭 Nenhuma oferta na fila para agendar.")
            return

        offer = self.post_queue.pop(0)

        # Calcular horário baseado na seleção
        if data == "schedule_1h":
            schedule_time = datetime.now() + timedelta(hours=1)
            time_text = "1 hora"
        elif data == "schedule_3h":
            schedule_time = datetime.now() + timedelta(hours=3)
            time_text = "3 horas"
        elif data == "schedule_6h":
            schedule_time = datetime.now() + timedelta(hours=6)
            time_text = "6 horas"
        elif data == "schedule_tomorrow_9":
            tomorrow = datetime.now() + timedelta(days=1)
            schedule_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            time_text = "amanhã às 9h"
        elif data == "schedule_tomorrow_18":
            tomorrow = datetime.now() + timedelta(days=1)
            schedule_time = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
            time_text = "amanhã às 18h"
        else:
            await query.edit_message_text("❌ Horário inválido.")
            return

        # Agendar post
        self.scheduled_posts.append(
            {
                "offer": offer,
                "schedule_time": schedule_time,
                "user_id": query.from_user.id,
            }
        )

        await query.edit_message_text(
            f"⏰ **Post Agendado!**\n\n"
            f"📱 **Plataforma:** {offer.platform}\n"
            f"🔗 **Link:** {offer.affiliate_url[:50]}...\n"
            f"⏰ **Horário:** {time_text}\n"
            f"📅 **Data:** {schedule_time.strftime('%d/%m/%Y %H:%M')}\n\n"
            f"✅ A oferta será publicada automaticamente!"
        )

        log_bot_event(
            "post_scheduled", offer.platform, f"Post agendado para {time_text}"
        )

    async def _handle_rate_callback(self, query, data: str):
        """Processa callback de avaliação"""
        platform = data.split("_")[1]
        await query.edit_message_text(
            f"⭐️ Obrigado pela avaliação da oferta {platform}!"
        )

    async def _handle_share_callback(self, query):
        """Processa callback de compartilhamento"""
        await query.edit_message_text("📤 Oferta compartilhada! Obrigado!")

    def _detect_platform(self, url: str) -> Optional[str]:
        """Detecta a plataforma baseado na URL"""
        url_lower = url.lower()

        if "amazon.com.br" in url_lower:
            return "amazon"
        elif "shopee.com.br" in url_lower or "s.shopee.com.br" in url_lower:
            return "shopee"
        elif "mercadolivre.com.br" in url_lower or "mercadolivre.com/sec" in url_lower:
            return "mercadolivre"
        elif "magazinevoce.com.br" in url_lower or "magazineluiza.com.br" in url_lower:
            return "magalu"
        elif "aliexpress.com" in url_lower or "s.click.aliexpress.com" in url_lower:
            return "aliexpress"
        elif "awin1.com" in url_lower or "tidd.ly" in url_lower:
            return "awin"
        elif "rakuten.com" in url_lower or "linksynergy.com" in url_lower:
            return "rakuten"

        return None

    def _get_platform_emoji(self, platform: str) -> str:
        """Retorna emoji para a plataforma"""
        emojis = {
            "amazon": "🛒",
            "shopee": "🛍️",
            "mercadolivre": "📱",
            "magalu": "🏪",
            "aliexpress": "🌏",
            "awin": "🔗",
            "rakuten": "🎯",
        }
        return emojis.get(platform, "🛒")

    async def start_polling(self):
        """Inicia o bot"""
        logger.info("🤖 Iniciando Garimpeiro Geek Bot...")

        # Iniciar polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("✅ Bot iniciado com sucesso!")

        # Iniciar loop de posts agendados
        asyncio.create_task(self._scheduled_posts_loop())

    async def _scheduled_posts_loop(self):
        """Loop para processar posts agendados"""
        while True:
            try:
                current_time = datetime.now()

                # Verificar posts agendados
                posts_to_execute = [
                    post
                    for post in self.scheduled_posts
                    if post["schedule_time"] <= current_time
                ]

                for post in posts_to_execute:
                    # Executar post
                    success = await self._post_to_channel(post["offer"])

                    if success:
                        # Remover da lista de agendados
                        self.scheduled_posts.remove(post)
                        logger.info(
                            f"✅ Post agendado executado: {post['offer'].platform}"
                        )
                    else:
                        logger.error(
                            f"❌ Erro ao executar post agendado: {post['offer'].platform}"
                        )

                # Aguardar 1 minuto antes da próxima verificação
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Erro no loop de posts agendados: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        """Para o bot"""
        logger.info("🛑 Parando Garimpeiro Geek Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("✅ Bot parado com sucesso!")


# Função principal para executar o bot
async def main():
    """Função principal"""
    bot = GarimpeiroGeekBot()

    try:
        await bot.start_polling()

        # Manter o bot rodando
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Recebido sinal de parada...")
        await bot.stop()
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
