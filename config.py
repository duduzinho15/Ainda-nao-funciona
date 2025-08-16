# config.py
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv()

# Chaves do Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1002853967960")  # Channel ID must be negative
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "1980848673")

# Chaves da Amazon PA-API
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "SUA_ACCESS_KEY_AQUI")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "SUA_SECRET_KEY_AQUI")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "")
AMAZON_REGION = os.getenv("AMAZON_REGION", "us-east-1")

# Configurações do Banco de Dados
DB_NAME = os.getenv("DB_NAME", "ofertas.db")

# Validação das credenciais Amazon
AMAZON_API_AVAILABLE = False
if (AMAZON_ACCESS_KEY and AMAZON_ACCESS_KEY != "SUA_ACCESS_KEY_AQUI" and 
    AMAZON_SECRET_KEY and AMAZON_SECRET_KEY != "SUA_SECRET_KEY_AQUI" and 
    AMAZON_ASSOCIATE_TAG and AMAZON_ASSOCIATE_TAG != "garimpeirogee-20"):
    AMAZON_API_AVAILABLE = True
    print("✅ Amazon PA-API configurada e ativada!")
else:
    print("⚠️  Aviso: Credenciais da Amazon PA-API não configuradas. A funcionalidade da Amazon estará desativada.")
    print("ℹ️  Para ativar, configure as variáveis de ambiente no arquivo .env:")
    print("    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOCIATE_TAG")
    
    # Define valores vazios para desativar a funcionalidade da Amazon
    AMAZON_ACCESS_KEY = ""
    AMAZON_SECRET_KEY = ""
    AMAZON_ASSOCIATE_TAG = ""

# Chaves da API da Shopee
SHOPEE_API_KEY = os.getenv("SHOPEE_API_KEY", "")
SHOPEE_API_SECRET = os.getenv("SHOPEE_API_SECRET", "")
SHOPEE_PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID", "")
SHOPEE_SHOP_ID = os.getenv("SHOPEE_SHOP_ID", "")

# Validação das credenciais Shopee
SHOPEE_API_AVAILABLE = False
if (SHOPEE_API_KEY and SHOPEE_API_KEY != "SUA_SHOPEE_API_KEY_AQUI" and 
    SHOPEE_API_SECRET and SHOPEE_API_SECRET != "SUA_SHOPEE_API_SECRET_AQUI" and 
    SHOPEE_PARTNER_ID and SHOPEE_PARTNER_ID != "SUA_SHOPEE_PARTNER_ID_AQUI"):
    SHOPEE_API_AVAILABLE = True
    print("✅ API da Shopee configurada e ativada!")
else:
    print("⚠️  Aviso: Credenciais da API da Shopee não configuradas. A funcionalidade da Shopee estará desativada.")
    print("ℹ️  Para ativar, configure as variáveis de ambiente no arquivo .env:")
    print("    SHOPEE_API_KEY, SHOPEE_API_SECRET, SHOPEE_PARTNER_ID")
    
    # Define valores vazios para desativar a funcionalidade da Shopee
    SHOPEE_API_KEY = ""
    SHOPEE_API_SECRET = ""
    SHOPEE_PARTNER_ID = ""

# Chaves da API de Afiliados do AliExpress
ALIEXPRESS_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY", "")
ALIEXPRESS_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET", "")
ALIEXPRESS_TRACKING_ID = "telegram"

# Configurações da API da Awin
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN", "")

# Publisher IDs corretos do Eduardo:
AWIN_PUBLISHER_IDS = {
    "default": "2370719",   # COMFY BR, LG BR, Trocafy BR, Kabum BR
    "samsung": "2510157"    # Samsung BR
}
AWIN_PUBLISHER_ID = AWIN_PUBLISHER_IDS["default"]

# Validação das credenciais da Awin
if AWIN_PUBLISHER_ID == "YOUR_PUBLISHER_ID":
    print("⚠️  Aviso: Publisher ID da Awin não configurado. A funcionalidade da Awin estará desativada.")
    print("ℹ️  Para ativar, configure a variável de ambiente no arquivo .env:")
    print("    AWIN_PUBLISHER_ID")
    AWIN_PUBLISHER_ID = ""

# Configurações de Rate Limiting
POST_RATE_DELAY_MS = int(os.getenv("POST_RATE_DELAY_MS", "250"))  # Delay entre posts em massa