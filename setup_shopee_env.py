#!/usr/bin/env python3
"""
Script para configurar as variáveis de ambiente da API da Shopee.
Execute este script para testar a API com as credenciais fornecidas.
"""

import os
import sys


def setup_shopee_env():
    """Configura as variáveis de ambiente da Shopee para teste."""

    # Credenciais da Shopee fornecidas pelo usuário
    shopee_credentials = {
        "SHOPEE_API_KEY": "18330800803",
        "SHOPEE_API_SECRET": "BZDT6KRMD7AIHNWZS7443MS7R3K2CHC4",
        "SHOPEE_PARTNER_ID": "18330800803",
        "SHOPEE_SHOP_ID": "18330800803",
    }

    print("🔧 Configurando variáveis de ambiente da Shopee...")

    # Define as variáveis de ambiente
    for key, value in shopee_credentials.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")

    print("\n🚀 Variáveis de ambiente configuradas!")
    print("💡 Agora você pode executar: python test_shopee_api.py")

    return True


if __name__ == "__main__":
    try:
        setup_shopee_env()
        print("\n✅ Configuração concluída com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro na configuração: {e}")
        sys.exit(1)
