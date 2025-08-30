#!/usr/bin/env python3
"""
Teste completo do MessageBuilder com funcionalidades avançadas
Valida todas as funcionalidades de emojis, formatação e templates
"""

import os
import sys
from decimal import Decimal

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.models import Offer
from src.telegram_bot.message_builder import MessageBuilder


def test_enhanced_message_builder():
    """Testa todas as funcionalidades avançadas do MessageBuilder"""
    print("🧪 Testando MessageBuilder com funcionalidades avançadas...")

    # Criar instância do MessageBuilder
    builder = MessageBuilder()

    # Teste 1: Validação da estrutura básica
    print("\n1️⃣ Testando estrutura básica...")
    assert hasattr(builder, "emojis"), "Emojis não encontrados"
    assert hasattr(builder, "quality_badges"), "Quality badges não encontrados"
    assert hasattr(builder, "category_emojis"), "Category emojis não encontrados"
    assert hasattr(builder, "shipping_emojis"), "Shipping emojis não encontrados"
    assert hasattr(builder, "payment_emojis"), "Payment emojis não encontrados"
    print("✅ Estrutura básica validada")

    # Teste 2: Validação de emojis por categoria
    print("\n2️⃣ Testando emojis por categoria...")
    assert "tech" in builder.emojis, "Categoria tech não encontrada"
    assert "gaming" in builder.emojis, "Categoria gaming não encontrada"
    assert "discount" in builder.emojis, "Categoria discount não encontrada"
    assert "quality" in builder.emojis, "Categoria quality não encontrada"
    assert "urgency" in builder.emojis, "Categoria urgency não encontrada"
    assert "category" in builder.emojis, "Categoria category não encontrada"
    assert "shipping" in builder.emojis, "Categoria shipping não encontrada"
    assert "payment" in builder.emojis, "Categoria payment não encontrada"
    assert "time" in builder.emojis, "Categoria time não encontrada"
    assert "status" in builder.emojis, "Categoria status não encontrada"
    print("✅ Emojis por categoria validados")

    # Teste 3: Validação de badges de qualidade
    print("\n3️⃣ Testando badges de qualidade...")
    assert (
        "best_price_90d" in builder.quality_badges
    ), "Badge best_price_90d não encontrado"
    assert "flash_sale" in builder.quality_badges, "Badge flash_sale não encontrado"
    assert (
        "free_shipping" in builder.quality_badges
    ), "Badge free_shipping não encontrado"
    assert (
        "trusted_store" in builder.quality_badges
    ), "Badge trusted_store não encontrado"
    assert "limited_time" in builder.quality_badges, "Badge limited_time não encontrado"
    print("✅ Badges de qualidade validados")

    # Teste 4: Validação de emojis específicos por categoria
    print("\n4️⃣ Testando emojis específicos por categoria...")
    assert "smartphone" in builder.category_emojis, "Emoji smartphone não encontrado"
    assert "laptop" in builder.category_emojis, "Emoji laptop não encontrado"
    assert "gaming" in builder.category_emojis, "Emoji gaming não encontrado"
    assert "audio" in builder.category_emojis, "Emoji audio não encontrado"
    print("✅ Emojis específicos por categoria validados")

    # Teste 5: Validação de métodos auxiliares
    print("\n5️⃣ Testando métodos auxiliares...")
    assert hasattr(
        builder, "_get_category_emoji"
    ), "Método _get_category_emoji não encontrado"
    assert hasattr(
        builder, "_get_shipping_emoji"
    ), "Método _get_shipping_emoji não encontrado"
    assert hasattr(
        builder, "_get_payment_emoji"
    ), "Método _get_payment_emoji não encontrado"
    assert hasattr(
        builder, "_format_price_with_emoji"
    ), "Método _format_price_with_emoji não encontrado"
    assert hasattr(
        builder, "_format_discount_with_emoji"
    ), "Método _format_discount_with_emoji não encontrado"
    assert hasattr(
        builder, "_format_time_badge"
    ), "Método _format_time_badge não encontrado"
    assert hasattr(
        builder, "_format_store_trust_badge"
    ), "Método _format_store_trust_badge não encontrado"
    assert hasattr(
        builder, "_format_shipping_info"
    ), "Método _format_shipping_info não encontrado"
    assert hasattr(
        builder, "_format_payment_options"
    ), "Método _format_payment_options não encontrado"
    print("✅ Métodos auxiliares validados")

    # Teste 6: Validação de formatação de preços
    print("\n6️⃣ Testando formatação de preços...")
    price_emoji = builder._format_price_with_emoji(Decimal("29.99"))
    assert "💸" in price_emoji, "Emoji de preço baixo não encontrado"

    price_emoji = builder._format_price_with_emoji(Decimal("299.99"))
    assert "💎" in price_emoji, "Emoji de preço médio não encontrado"

    price_emoji = builder._format_price_with_emoji(Decimal("1299.99"))
    assert "👑" in price_emoji, "Emoji de preço alto não encontrado"

    price_emoji = builder._format_price_with_emoji(Decimal("2999.99"))
    assert "👑" in price_emoji, "Emoji de preço premium não encontrado"
    print("✅ Formatação de preços validada")

    # Teste 7: Validação de formatação de desconto
    print("\n7️⃣ Testando formatação de desconto...")
    discount_text = builder._format_discount_with_emoji(55.0)
    assert (
        "🔥" in discount_text and "IMPRESSIONANTE" in discount_text
    ), "Desconto alto não formatado corretamente"

    discount_text = builder._format_discount_with_emoji(35.0)
    assert (
        "⚡" in discount_text and "EXCELENTE" in discount_text
    ), "Desconto médio não formatado corretamente"

    discount_text = builder._format_discount_with_emoji(15.0)
    assert (
        "💰" in discount_text and "DESCONTO" in discount_text
    ), "Desconto baixo não formatado corretamente"
    print("✅ Formatação de desconto validada")

    # Teste 8: Validação de emojis por categoria de produto
    print("\n8️⃣ Testando emojis por categoria de produto...")
    category_emoji = builder._get_category_emoji("smartphone")
    assert category_emoji == "📱", f"Emoji smartphone incorreto: {category_emoji}"

    category_emoji = builder._get_category_emoji("laptop gaming")
    assert category_emoji == "💻", f"Emoji laptop incorreto: {category_emoji}"

    category_emoji = builder._get_category_emoji("headphones")
    assert category_emoji == "🎧", f"Emoji headphones incorreto: {category_emoji}"

    category_emoji = builder._get_category_emoji("placa de vídeo")
    assert category_emoji == "🎨", f"Emoji placa de vídeo incorreto: {category_emoji}"
    print("✅ Emojis por categoria de produto validados")

    # Teste 9: Validação de emojis de frete
    print("\n9️⃣ Testando emojis de frete...")
    shipping_emoji = builder._get_shipping_emoji("grátis")
    assert shipping_emoji == "🚚", f"Emoji frete grátis incorreto: {shipping_emoji}"

    shipping_emoji = builder._get_shipping_emoji("rápido")
    assert shipping_emoji == "⚡", f"Emoji frete rápido incorreto: {shipping_emoji}"

    shipping_emoji = builder._get_shipping_emoji("mesmo dia")
    assert (
        shipping_emoji == "🚀"
    ), f"Emoji entrega mesmo dia incorreto: {shipping_emoji}"
    print("✅ Emojis de frete validados")

    # Teste 10: Validação de emojis de pagamento
    print("\n🔟 Testando emojis de pagamento...")
    payment_emoji = builder._get_payment_emoji("pix")
    assert payment_emoji == "📱", f"Emoji PIX incorreto: {payment_emoji}"

    payment_emoji = builder._get_payment_emoji("cartão")
    assert payment_emoji == "💳", f"Emoji cartão incorreto: {payment_emoji}"

    payment_emoji = builder._get_payment_emoji("boleto")
    assert payment_emoji == "📄", f"Emoji boleto incorreto: {payment_emoji}"
    print("✅ Emojis de pagamento validados")

    # Teste 11: Validação de template aprimorado
    print("\n1️⃣1️⃣ Testando template aprimorado...")

    # Criar oferta de teste simples
    test_offer = Offer(
        title="Test Product",
        price=Decimal("100"),
        url="https://example.com/test",
        store="Test Store",
        original_price=Decimal("200"),
        coupon_code="TEST123",
        coupon_discount=15.0,
        coupon_valid_until="2024-12-31",
    )

    # Gerar mensagem com template aprimorado
    message = builder._apply_enhanced_template(test_offer, "TEST")

    # Validar elementos essenciais da mensagem
    assert "OFERTA TEST" in message, "Título da oferta não encontrado"
    assert "CUPOM:" in message, "Informações de cupom não encontradas"
    assert "TEST123" in message, "Código do cupom não encontrado"

    print("✅ Template aprimorado validado")

    # Teste 12: Validação de mensagens específicas por plataforma
    print("\n1️⃣2️⃣ Testando mensagens específicas por plataforma...")

    # Teste Awin
    awin_message = builder._build_awin_template(test_offer)
    assert "OFERTA ESPECIAL" in awin_message, "Template Awin não formatado corretamente"

    # Teste Amazon
    amazon_message = builder._build_amazon_template(test_offer)
    assert (
        "OFERTA AMAZON" in amazon_message
    ), "Template Amazon não formatado corretamente"

    # Teste Mercado Livre
    ml_message = builder._build_mercadolivre_template(test_offer)
    assert (
        "OFERTA MERCADO LIVRE" in ml_message
    ), "Template Mercado Livre não formatado corretamente"

    # Teste Shopee
    shopee_message = builder._build_shopee_template(test_offer)
    assert (
        "OFERTA SHOPEE" in shopee_message
    ), "Template Shopee não formatado corretamente"

    # Teste Magazine Luiza
    magalu_message = builder._build_magazineluiza_template(test_offer)
    assert (
        "OFERTA MAGAZINE LUIZA" in magalu_message
    ), "Template Magazine Luiza não formatado corretamente"

    # Teste AliExpress
    aliexpress_message = builder._build_aliexpress_template(test_offer)
    assert (
        "OFERTA ALIEXPRESS" in aliexpress_message
    ), "Template AliExpress não formatado corretamente"

    # Teste Default
    default_message = builder._build_default_template(test_offer)
    assert (
        "OFERTA ESPECIAL" in default_message
    ), "Template Default não formatado corretamente"

    print("✅ Mensagens específicas por plataforma validadas")

    # Teste 13: Validação de mensagens especiais
    print("\n1️⃣3️⃣ Testando mensagens especiais...")

    # Teste mensagem de boas-vindas
    welcome_message = builder.build_welcome_message()
    assert (
        "Bem-vindo ao Garimpeiro Geek!" in welcome_message
    ), "Mensagem de boas-vindas não formatada corretamente"

    # Teste mensagem de ajuda
    help_message = builder.build_help_message({"/start": "Iniciar", "/help": "Ajuda"})
    assert (
        "Comandos do Garimpeiro Geek:" in help_message
    ), "Mensagem de ajuda não formatada corretamente"

    # Teste mensagem de status
    status_message = builder.build_status_message()
    assert (
        "Status do Sistema" in status_message
    ), "Mensagem de status não formatada corretamente"

    # Teste mensagem de estatísticas
    stats_message = builder.build_stats_message()
    assert (
        "Estatísticas do Sistema" in stats_message
    ), "Mensagem de estatísticas não formatada corretamente"

    print("✅ Mensagens especiais validadas")

    print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
    print(
        "✅ MessageBuilder com funcionalidades avançadas está funcionando perfeitamente!"
    )

    return True


if __name__ == "__main__":
    try:
        test_enhanced_message_builder()
        print("\n🚀 MessageBuilder está pronto para produção!")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
