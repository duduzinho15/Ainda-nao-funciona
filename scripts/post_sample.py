#!/usr/bin/env python3
"""
Script de teste para publicar ofertas de exemplo num chat de teste
"""

import asyncio
import logging
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN
from utils.images import fetch_bytes, fetch_og_image

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chat de teste (deve ser configurado no .env)
TELEGRAM_TEST_CHAT_ID = os.getenv(
    "TELEGRAM_TEST_CHAT_ID", "-1002853967960"
)  # Usa o chat principal se não configurado


async def testar_cartao_com_imagem_explicita():
    """Teste 1: Oferta com imagem explícita"""
    print("🧪 TESTE 1: Oferta com imagem explícita")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Oferta de exemplo com imagem
    oferta = {
        "titulo": "Smartphone Samsung Galaxy S25 Ultra 512GB - Teste com Imagem",
        "preco_atual": "R$ 6.002,10",
        "preco_original": "R$ 11.999,00",
        "desconto": 50,
        "loja": "Samsung",
        "fonte": "Teste",
        "imagem_url": "https://i.promobit.com.br/300/185433158517552035186780100066.png",
        "url_produto": "https://www.samsung.com/br/smartphones/galaxy-s25-ultra/",
    }

    caption_html = f"""🔥 <b>{oferta["titulo"]}</b>

💰 <b>Preço:</b> {oferta["preco_atual"]}
💸 <b>De:</b> {oferta["preco_original"]}
🔥 <b>Desconto:</b> {oferta["desconto"]}% OFF

🏷 {oferta["loja"]} | {oferta["fonte"]}"""

    try:
        # Tenta enviar como bytes primeiro
        img_url = oferta["imagem_url"]
        buf = fetch_bytes(img_url)

        if buf:
            await bot.send_photo(
                chat_id=TELEGRAM_TEST_CHAT_ID,
                photo=buf,
                caption=caption_html,
                parse_mode=ParseMode.HTML,
            )
            print("✅ Imagem enviada via bytes")
        else:
            await bot.send_photo(
                chat_id=TELEGRAM_TEST_CHAT_ID,
                photo=img_url,
                caption=caption_html,
                parse_mode=ParseMode.HTML,
            )
            print("✅ Imagem enviada via URL")

    except Exception as e:
        print(f"❌ Erro no teste 1: {e}")


async def testar_cartao_sem_imagem_mas_com_og():
    """Teste 2: Oferta sem imagem mas com OG válido"""
    print("\n🧪 TESTE 2: Oferta sem imagem mas com OG válido")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Oferta de exemplo sem imagem (será extraída via OG)
    oferta = {
        "titulo": "Notebook Dell Inspiron 15 - Teste com OG Image",
        "preco_atual": "R$ 3.499,00",
        "preco_original": "R$ 4.999,00",
        "desconto": 30,
        "loja": "Dell",
        "fonte": "Teste",
        "url_produto": "https://www.dell.com/pt/p/inspiron-15-3511-laptop/pd",
    }

    caption_html = f"""🔥 <b>{oferta["titulo"]}</b>

💰 <b>Preço:</b> {oferta["preco_atual"]}
💸 <b>De:</b> {oferta["preco_original"]}
🔥 <b>Desconto:</b> {oferta["desconto"]}% OFF

🏷 {oferta["loja"]} | {oferta["fonte"]}"""

    try:
        # Tenta extrair OG image
        og_image = fetch_og_image(oferta["url_produto"])

        if og_image:
            print(f"✅ OG image encontrada: {og_image[:80]}...")

            # Tenta enviar como bytes
            buf = fetch_bytes(og_image)
            if buf:
                await bot.send_photo(
                    chat_id=TELEGRAM_TEST_CHAT_ID,
                    photo=buf,
                    caption=caption_html,
                    parse_mode=ParseMode.HTML,
                )
                print("✅ OG image enviada via bytes")
            else:
                await bot.send_photo(
                    chat_id=TELEGRAM_TEST_CHAT_ID,
                    photo=og_image,
                    caption=caption_html,
                    parse_mode=ParseMode.HTML,
                )
                print("✅ OG image enviada via URL")
        else:
            print("⚠️ OG image não encontrada, caindo para texto")
            await bot.send_message(
                chat_id=TELEGRAM_TEST_CHAT_ID,
                text=caption_html,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            print("✅ Mensagem enviada sem preview")

    except Exception as e:
        print(f"❌ Erro no teste 2: {e}")


async def testar_cartao_sem_imagem_sem_og():
    """Teste 3: Oferta sem imagem e sem OG (cai em texto sem preview)"""
    print("\n🧪 TESTE 3: Oferta sem imagem e sem OG")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Oferta de exemplo sem imagem e sem OG
    oferta = {
        "titulo": "Produto Genérico - Teste sem Imagem/OG",
        "preco_atual": "R$ 99,90",
        "loja": "Loja Teste",
        "fonte": "Teste",
        "url_produto": "https://exemplo.com/produto-teste",
    }

    caption_html = f"""🔥 <b>{oferta["titulo"]}</b>

💰 <b>Preço:</b> {oferta["preco_atual"]}

🏷 {oferta["loja"]} | {oferta["fonte"]}"""

    try:
        # Envia como mensagem de texto sem preview
        await bot.send_message(
            chat_id=TELEGRAM_TEST_CHAT_ID,
            text=caption_html,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        print("✅ Mensagem enviada sem preview")

    except Exception as e:
        print(f"❌ Erro no teste 3: {e}")


async def main():
    """Função principal para executar todos os testes"""
    print("🚀 INICIANDO TESTES DE POSTAGEM DE OFERTAS")
    print("=" * 60)
    print(f"📱 Chat de teste: {TELEGRAM_TEST_CHAT_ID}")
    print(f"🤖 Bot: @{TELEGRAM_BOT_TOKEN.split(':')[0]}")
    print("=" * 60)

    try:
        # Executa os 3 testes
        await testar_cartao_com_imagem_explicita()
        await asyncio.sleep(2)  # Aguarda entre testes

        await testar_cartao_sem_imagem_mas_com_og()
        await asyncio.sleep(2)  # Aguarda entre testes

        await testar_cartao_sem_imagem_sem_og()

        print("\n🎉 TODOS OS TESTES CONCLUÍDOS!")
        print("✅ Verifique o chat de teste para ver os resultados")

    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
