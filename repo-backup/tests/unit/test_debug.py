#!/usr/bin/env python3
"""
Teste simples para debugar o problema do cupom
"""

import os
import sys
from decimal import Decimal

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.models import Offer
from src.telegram_bot.message_builder import MessageBuilder


def test_coupon_debug():
    """Teste simples para debugar o problema do cupom"""
    print("🔍 Testando debug do cupom...")

    # Criar instância do MessageBuilder
    builder = MessageBuilder()

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

    print(f"✅ Oferta criada com cupom: {test_offer.coupon_code}")

    # Testar formatação do cupom
    coupon_info = builder._format_coupon_info(test_offer)
    print(f"✅ Cupom formatado: {repr(coupon_info)}")

    # Gerar mensagem com template aprimorado
    message = builder._apply_enhanced_template(test_offer, "TEST")
    print(f"✅ Mensagem gerada com {len(message)} caracteres")

    # Verificar se o cupom está na mensagem
    cupom_encontrado = "🎫 CUPOM:" in message
    print(f"✅ Cupom encontrado na mensagem: {cupom_encontrado}")

    # Verificar se o código do cupom está na mensagem
    codigo_encontrado = "TEST123" in message
    print(f"✅ Código do cupom encontrado: {codigo_encontrado}")

    # Mostrar parte da mensagem onde deveria estar o cupom
    if "🎫" in message:
        start_idx = message.find("🎫")
        end_idx = start_idx + 100
        cupom_section = message[start_idx:end_idx]
        print(f"✅ Seção do cupom: {repr(cupom_section)}")
    else:
        print("❌ Emoji do cupom não encontrado na mensagem")

    # Verificar se há algum problema de codificação
    print(f"✅ Mensagem contém 'CUPOM': {'CUPOM' in message}")
    print(f"✅ Mensagem contém 'TEST123': {'TEST123' in message}")

    return True


if __name__ == "__main__":
    try:
        test_coupon_debug()
        print("\n🔍 Debug concluído!")
    except Exception as e:
        print(f"\n❌ Erro durante o debug: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
