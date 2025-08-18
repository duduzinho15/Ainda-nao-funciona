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


oferta_teste = {
    "titulo": "🔥 Smartphone Samsung Galaxy A15 128GB - SUPER OFERTA!",
    "preco": "R$ 799,99",
    "preco_original": "R$ 1.199,99",
    "url_produto": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ",
    "url_afiliado": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ?tag=garimpeirogeek-20",
    "imagem_url": "https://picsum.photos/400/300?random=2",
    "loja": "Amazon",
    "fonte": "Teste Final",
}


async def main():
    # Cria contexto simulado com bot válido
    context = ContextoSimulado()

    print("🚀 Iniciando teste de postagem...")
    print(f"📱 Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"💬 Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")

    # Testa publicação
    ok = await publicar_oferta_automatica(oferta_teste, context)
    print(f"✅ Publicado? {ok}")

    # Não fecha o bot para evitar flood control
    print("🎯 Teste concluído! Verifique o canal do Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
