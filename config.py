# config.py
import os
from typing import List
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv()

# Configurações do Bot Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")

# Configurações de Rate Limiting
POST_RATE_DELAY_MS = int(os.getenv("POST_RATE_DELAY_MS", "250"))

# Configurações do Banco de Dados
DB_NAME = os.getenv("DB_NAME", "ofertas.db")

# ===== FLAGS DE CONTROLE PARA SCRAPERS =====
ENABLE_PROMOBIT = os.getenv("ENABLE_PROMOBIT", "1") == "1"
ENABLE_PELANDO = os.getenv("ENABLE_PELANDO", "1") == "1"
ENABLE_SHOPEE = os.getenv("ENABLE_SHOPEE", "0") == "1"  # Desabilitado por padrão
ENABLE_AMAZON = os.getenv("ENABLE_AMAZON", "0") == "1"  # Desabilitado por padrão
ENABLE_ALIEXPRESS = os.getenv("ENABLE_ALIEXPRESS", "0") == "1"  # Desabilitado por padrão
ENABLE_MEPUC = os.getenv("ENABLE_MEPUC", "0") == "1"  # Desabilitado por padrão

# Configurações da Amazon PA-API
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "")
AMAZON_REGION = os.getenv("AMAZON_REGION", "us-east-1")

# Configurações da API da Shopee
SHOPEE_API_KEY = os.getenv("SHOPEE_API_KEY", "")
SHOPEE_API_SECRET = os.getenv("SHOPEE_API_SECRET", "")

# Configurações da API da AliExpress
ALIEXPRESS_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY", "")
ALIEXPRESS_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET", "")

# Configurações da AWIN
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN", "")

# Publisher IDs corretos do Eduardo:
AWIN_PUBLISHER_IDS = {
    "default": "2370719",   # COMFY BR, LG BR, Trocafy BR, Kabum BR
    "samsung": "2510157"    # Samsung BR
}
AWIN_PUBLISHER_ID = AWIN_PUBLISHER_IDS["default"]

# Configurações de Métricas
METRICS_ENABLED = os.getenv("METRICS", "0") == "1"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9308"))

# ===== VALIDAÇÕES DE CONFIGURAÇÃO =====
def validate_config() -> List[str]:
    """Valida se as configurações essenciais estão presentes"""
    errors: List[str] = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN não configurado")
    
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID não configurado")
    
    if ENABLE_AMAZON and not AMAZON_ASSOCIATE_TAG:
        errors.append("AMAZON_ASSOCIATE_TAG necessário para Amazon")
    
    if ENABLE_SHOPEE and not SHOPEE_API_KEY:
        errors.append("SHOPEE_API_KEY necessário para Shopee")
    
    if ENABLE_ALIEXPRESS and not ALIEXPRESS_APP_KEY:
        errors.append("ALIEXPRESS_APP_KEY necessário para AliExpress")
    
    return errors

# ===== IMPRESSÃO DE STATUS =====
def print_config_status() -> None:
    """Imprime o status das configurações"""
    print("🔧 CONFIGURAÇÕES DO SISTEMA GARIMPEIRO GEEK")
    print("=" * 50)
    
    # Status dos scrapers
    print(f"📊 Scrapers:")
    print(f"  Promobit: {'✅ ATIVO' if ENABLE_PROMOBIT else '❌ DESABILITADO'}")
    print(f"  Pelando: {'✅ ATIVO' if ENABLE_PELANDO else '❌ DESABILITADO'}")
    print(f"  Shopee: {'✅ ATIVO' if ENABLE_SHOPEE else '❌ DESABILITADO'}")
    print(f"  Amazon: {'✅ ATIVO' if ENABLE_AMAZON else '❌ DESABILITADO'}")
    print(f"  AliExpress: {'✅ ATIVO' if ENABLE_ALIEXPRESS else '❌ DESABILITADO'}")
    print(f"  MeuPC.net: {'✅ ATIVO' if ENABLE_MEPUC else '❌ DESABILITADO'}")
    
    # Status das APIs
    print(f"\n🔑 APIs:")
    if ENABLE_AMAZON:
        print("✅ Amazon PA-API configurada e ativada!")
    if ENABLE_SHOPEE:
        print("✅ API da Shopee configurada e ativada!")
    if ENABLE_ALIEXPRESS:
        print("✅ API da AliExpress configurada e ativada!")
    
    # Status das métricas
    print(f"\n📈 Métricas:")
    print(f"  Prometheus: {'✅ ATIVO' if METRICS_ENABLED else '❌ DESABILITADO'}")
    if METRICS_ENABLED:
        print(f"  Porta: {METRICS_PORT}")
    
    # Validações
    errors: List[str] = validate_config()
    if errors:
        print(f"\n⚠️ AVISOS:")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"\n✅ Configuração válida!")
    
    print("=" * 50)

# Executa validação se o arquivo for executado diretamente
if __name__ == "__main__":
    print_config_status()