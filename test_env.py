"""
Script para testar o carregamento das variáveis de ambiente do arquivo .env
"""
import os
from dotenv import load_dotenv

print("=== TESTE DE CARREGAMENTO DO ARQUIVO .env ===\n")

# Tenta carregar o arquivo .env
env_loaded = load_dotenv()
print(f"Arquivo .env carregado: {'Sim' if env_loaded else 'Não'}")

# Verifica se o arquivo .env existe
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Caminho do arquivo .env: {env_path}")
print(f"Arquivo .env existe: {os.path.exists(env_path)}")

# Tenta ler o arquivo .env diretamente
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("\nConteúdo do arquivo .env:")
    print("-" * 50)
    print(content)
    print("-" * 50)
except Exception as e:
    print(f"\nErro ao ler o arquivo .env: {e}")

# Tenta acessar as variáveis de ambiente
print("\nVariáveis de ambiente carregadas:")
print(f"TELEGRAM_BOT_TOKEN: {'Definido' if os.getenv('TELEGRAM_BOT_TOKEN') else 'Não definido'}")
print(f"TELEGRAM_CHAT_ID: {'Definido' if os.getenv('TELEGRAM_CHAT_ID') else 'Não definido'}")

# Mostra os primeiros e últimos caracteres do token (se existir)
token = os.getenv('TELEGRAM_BOT_TOKEN')
if token:
    print(f"\nToken (parcial): {token[:5]}...{token[-5:] if len(token) > 10 else ''}")

print("\n=== FIM DO TESTE ===")
