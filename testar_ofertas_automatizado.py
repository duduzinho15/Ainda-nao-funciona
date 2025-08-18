#!/usr/bin/env python3
"""
Teste Automatizado de Ofertas - Garimpeiro Geek
Testa publicação com e sem imagem para validar fallbacks
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from telegram import Bot
from telegram_poster import publicar_oferta_automatica

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging detalhado
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Mock do bot para simulação (não envia nada)
class BotSimulado:
    def __init__(self):
        self.chat_id = None
        self.photo = None
        self.caption = None
        self.markup = None
        self.message_sent = False
        self.message_type = None

    async def send_photo(self, chat_id, photo, caption, parse_mode, reply_markup):
        self.chat_id = chat_id
        self.photo = photo
        self.caption = caption
        self.markup = reply_markup
        self.message_sent = True
        self.message_type = "photo"

        # Log detalhado da imagem
        image_source = "bytes" if hasattr(photo, "read") else "url"
        logger.info(
            f"📸 SIMULAÇÃO: Foto enviada (source={image_source}) para chat {chat_id}"
        )
        logger.info(f"📝 Caption: {caption[:100]}...")
        logger.info(f"🔗 Markup: {reply_markup}")
        return True

    async def send_message(
        self, chat_id, text, parse_mode, disable_web_page_preview, reply_markup
    ):
        self.chat_id = chat_id
        self.caption = text
        self.markup = reply_markup
        self.message_sent = True
        self.message_type = "text"

        logger.info(f"💬 SIMULAÇÃO: Mensagem de texto enviada para chat {chat_id}")
        logger.info(f"📝 Texto: {text[:100]}...")
        logger.info(f"🔗 Markup: {reply_markup}")
        return True


# Simula um contexto com bot válido
class ContextoSimulado:
    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN não encontrado no .env")
        self.bot = Bot(token=token)
        self.job = None


# Ofertas de teste
ofertas_teste = [
    {
        "titulo": "🔥 Smartphone Samsung Galaxy A15 128GB - COM IMAGEM",
        "preco": "R$ 799,99",
        "preco_original": "R$ 1.299,99",
        "url_produto": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ",
        "url_afiliado": "https://www.amazon.com.br/Samsung-Galaxy-A15-128GB-Preto/dp/B0CQZ6K9YQ?tag=garimpeirogeek-20",
        "imagem_url": "https://picsum.photos/400/300?random=1",
        "loja": "Amazon",
        "fonte": "Teste Automatizado - Com Imagem",
    },
    {
        "titulo": "💻 Notebook Dell Inspiron 15 - SEM IMAGEM",
        "preco": "R$ 2.499,99",
        "preco_original": "R$ 3.299,99",
        "url_produto": "https://www.amazon.com.br/Notebook-Dell-Inspiron-15-3000/dp/B08N5WRWNW",
        "url_afiliado": "https://www.amazon.com.br/Notebook-Dell-Inspiron-15-3000/dp/B08N5WRWNW?tag=garimpeirogeek-20",
        "imagem_url": "",  # Sem imagem para testar fallback
        "loja": "Amazon",
        "fonte": "Teste Automatizado - Sem Imagem",
    },
]


async def testar_estrutura_oferta(oferta: dict, index: int):
    """Testa se a estrutura da oferta está correta"""
    logger.info(f"🔍 TESTE {index + 1}: Validando estrutura da oferta")

    # Chaves obrigatórias
    chaves_obrigatorias = [
        "titulo",
        "preco",
        "url_produto",
        "url_afiliado",
        "loja",
        "fonte",
    ]
    chaves_opcionais = ["preco_original", "imagem_url"]

    # Valida chaves obrigatórias
    for chave in chaves_obrigatorias:
        if chave not in oferta:
            logger.error(f"❌ Chave obrigatória '{chave}' não encontrada")
            return False
        if not oferta[chave]:
            logger.error(f"❌ Chave '{chave}' está vazia")
            return False

    # Valida chaves opcionais
    for chave in chaves_opcionais:
        if chave in oferta:
            logger.info(f"✅ Chave opcional '{chave}': {oferta[chave]}")

    # Valida URLs
    if not oferta["url_produto"].startswith("http"):
        logger.error(f"❌ URL do produto inválida: {oferta['url_produto']}")
        return False

    if not oferta["url_afiliado"].startswith("http"):
        logger.error(f"❌ URL de afiliado inválida: {oferta['url_afiliado']}")
        return False

    logger.info(f"✅ Estrutura da oferta {index + 1} válida")
    return True


async def testar_publicacao_oferta(oferta: dict, context, index: int):
    """Testa a publicação de uma oferta específica"""
    logger.info(f"🚀 TESTE {index + 1}: Publicando oferta '{oferta['titulo'][:50]}...'")

    # Substitui bot real por bot simulado
    bot_original = context.bot
    context.bot = BotSimulado()

    try:
        # Testa publicação
        ok = await publicar_oferta_automatica(oferta, context)

        if ok and context.bot.message_sent:
            logger.info(f"✅ Oferta {index + 1} publicada com sucesso")
            logger.info(f"📊 Tipo de mensagem: {context.bot.message_type}")
            logger.info(f"💬 Chat ID: {context.bot.chat_id}")

            # Log detalhado do caption
            caption = context.bot.caption or ""
            logger.info(f"📝 Caption (primeiros 150 chars): {caption[:150]}...")

            # Log do markup
            markup = context.bot.markup
            if markup:
                logger.info(f"🔗 Botões: {len(markup.inline_keyboard)} botão(ões)")
                for i, row in enumerate(markup.inline_keyboard):
                    for j, button in enumerate(row):
                        logger.info(
                            f"  Botão {i + 1}.{j + 1}: {button.text} -> {button.url[:50]}..."
                        )

            return True
        else:
            logger.error(f"❌ Falha na publicação da oferta {index + 1}")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao publicar oferta {index + 1}: {e}")
        return False
    finally:
        # Restaura bot original
        context.bot = bot_original


async def main():
    """Função principal do teste automatizado"""
    print("🚀 TESTE AUTOMATIZADO DE OFERTAS - GARIMPEIRO GEEK")
    print("=" * 70)

    # Cria contexto simulado
    context = ContextoSimulado()

    print(f"📱 Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"💬 Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
    print(f"🕐 Início: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)

    resultados = []

    # Testa cada oferta
    for i, oferta in enumerate(ofertas_teste):
        print(f"\n📋 TESTE {i + 1}: {oferta['titulo'][:50]}...")
        print("-" * 50)

        # Valida estrutura
        estrutura_ok = await testar_estrutura_oferta(oferta, i)
        if not estrutura_ok:
            logger.error(f"❌ Estrutura da oferta {i + 1} inválida")
            resultados.append(False)
            continue

        # Testa publicação
        publicacao_ok = await testar_publicacao_oferta(oferta, context, i)
        resultados.append(publicacao_ok)

        # Aguarda entre testes
        if i < len(ofertas_teste) - 1:
            await asyncio.sleep(1)

    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)

    for i, resultado in enumerate(resultados):
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        titulo = ofertas_teste[i]["titulo"][:40]
        print(f"Teste {i + 1}: {status} - {titulo}...")

    total_passou = sum(resultados)
    total_testes = len(resultados)

    print(f"\n🎯 RESULTADO FINAL: {total_passou}/{total_testes} testes passaram")

    if total_passou == total_testes:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando perfeitamente.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")

    print(f"🕐 Fim: {datetime.now().strftime('%H:%M:%S')}")
    print(
        "\n🎯 Teste automatizado concluído! Nenhuma mensagem foi enviada para o Telegram."
    )


if __name__ == "__main__":
    asyncio.run(main())
