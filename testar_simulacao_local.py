import asyncio
import os
import sys
from telegram import Bot
from telegram_poster import publicar_oferta_automatica

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Simula um contexto com bot válido
class ContextoSimulado:
    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN não encontrado no .env")
        self.bot = Bot(token=token)
        self.job = None


# Mock do bot para simulação (não envia nada)
class BotSimulado:
    def __init__(self):
        self.chat_id = None
        self.photo = None
        self.caption = None
        self.markup = None
        self.message_sent = False

    async def send_photo(self, chat_id, photo, caption, parse_mode, reply_markup):
        self.chat_id = chat_id
        self.photo = photo
        self.caption = caption
        self.markup = reply_markup
        self.message_sent = True
        print(f"📸 SIMULAÇÃO: Foto seria enviada para chat {chat_id}")
        print(f"📝 Caption: {caption[:100]}...")
        print(f"🔗 Markup: {reply_markup}")
        return True

    async def send_message(
        self, chat_id, text, parse_mode, disable_web_page_preview, reply_markup
    ):
        self.chat_id = chat_id
        self.caption = text
        self.markup = reply_markup
        self.message_sent = True
        print(f"💬 SIMULAÇÃO: Mensagem seria enviada para chat {chat_id}")
        print(f"📝 Texto: {text[:100]}...")
        print(f"🔗 Markup: {reply_markup}")
        return True


oferta_teste = {
    "titulo": "🔥 Smartphone Samsung Galaxy A15 128GB - SUPER OFERTA!",
    "preco": "R$ 799,99",
    "preco_original": "R$ 1.299,99",
    "url_produto": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ",
    "url_afiliado": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ?tag=garimpeirogeek-20",
    "imagem_url": "https://picsum.photos/400/300?random=3",
    "loja": "Amazon",
    "fonte": "Teste Simulação",
}


async def main():
    print("🚀 INICIANDO TESTE DE SIMULAÇÃO (SEM ENVIAR PARA TELEGRAM)")
    print("=" * 60)

    # Cria contexto simulado com bot MOCK
    context = ContextoSimulado()
    context.bot = BotSimulado()  # Substitui por bot simulado

    print(f"📱 Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"💬 Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
    print(f"🏪 Loja: {oferta_teste['loja']}")
    print(f"📦 Fonte: {oferta_teste['fonte']}")
    print("=" * 60)

    # Testa publicação (simulação)
    print("🔄 Executando simulação de publicação...")
    ok = await publicar_oferta_automatica(oferta_teste, context)

    print("=" * 60)
    print(f"✅ Simulação concluída: {ok}")

    # Valida estrutura da oferta
    print("\n🔍 VALIDAÇÃO DA ESTRUTURA:")
    print(f"  ✅ titulo: {oferta_teste['titulo'][:50]}...")
    print(f"  ✅ preco: {oferta_teste['preco']}")
    print(f"  ✅ preco_original: {oferta_teste['preco_original']}")
    print(f"  ✅ url_produto: {oferta_teste['url_produto'][:50]}...")
    print(f"  ✅ url_afiliado: {oferta_teste['url_afiliado'][:50]}...")
    print(f"  ✅ imagem_url: {oferta_teste['imagem_url']}")
    print(f"  ✅ loja: {oferta_teste['loja']}")
    print(f"  ✅ fonte: {oferta_teste['fonte']}")

    # Verifica se o bot simulado recebeu os dados
    if context.bot.message_sent:
        print("\n🎯 SIMULAÇÃO BEM-SUCEDIDA:")
        print(f"  📸 Chat ID: {context.bot.chat_id}")
        print(f"  📝 Caption/Text: {str(context.bot.caption)[:100]}...")
        print(f"  🔗 Markup: {context.bot.markup}")
    else:
        print("\n❌ SIMULAÇÃO FALHOU: Bot não recebeu dados")

    print("\n🎯 Simulação concluída! Nenhuma mensagem foi enviada para o Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
