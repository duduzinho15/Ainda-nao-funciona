#!/usr/bin/env python3
"""
Script de Instalação do Garimpeiro Geek
Instala todas as dependências e configura o ambiente
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Executa um comando e retorna sucesso/falha"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} concluído com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}: {e}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário")
        print(f"Versão atual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def install_dependencies():
    """Instala as dependências do projeto"""
    print("\n📦 Instalando dependências...")
    
    # Atualizar pip
    if not run_command("python -m pip install --upgrade pip", "Atualizando pip"):
        return False
    
    # Instalar dependências principais
    if not run_command("pip install -r requirements.txt", "Instalando dependências principais"):
        return False
    
    # Instalar playwright browsers
    if not run_command("playwright install", "Instalando navegadores Playwright"):
        print("⚠️ Playwright pode ser instalado manualmente depois")
    
    return True

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    
    directories = [
        ".data",
        ".data/config",
        ".data/logs",
        "exports",
        "backups",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def setup_environment():
    """Configura o ambiente de desenvolvimento"""
    print("\n⚙️ Configurando ambiente...")
    
    # Criar arquivo .env se não existir
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path("env_example.txt")
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Converter para formato .env
            env_content = content.replace("# ", "").replace("=seu_token_aqui", "=")
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            print("✅ Arquivo .env criado a partir do template")
        else:
            print("⚠️ Template .env não encontrado")
    
    # Verificar se há arquivo .env
    if env_file.exists():
        print("✅ Arquivo .env configurado")
    else:
        print("⚠️ Configure manualmente o arquivo .env")

def run_tests():
    """Executa os testes automatizados"""
    print("\n🧪 Executando testes...")
    
    if not run_command("python -m pytest tests/ -v", "Executando testes"):
        print("⚠️ Alguns testes falharam, mas a instalação pode continuar")
        return False
    
    return True

def main():
    """Função principal de instalação"""
    print("🚀 Instalador do Garimpeiro Geek")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Criar diretórios
    create_directories()
    
    # Instalar dependências
    if not install_dependencies():
        print("❌ Falha na instalação das dependências")
        sys.exit(1)
    
    # Configurar ambiente
    setup_environment()
    
    # Executar testes
    run_tests()
    
    print("\n🎉 Instalação concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Configure suas chaves de API no arquivo .env")
    print("2. Execute 'python app/dashboard.py' para testar o dashboard")
    print("3. Configure o bot Telegram se desejar")
    print("4. Execute os scrapers para coletar ofertas")
    
    print("\n🔗 Links úteis:")
    print("- Documentação: README.md")
    print("- Configuração GitHub: SETUP_GITHUB.md")
    print("- Exemplo de configuração: env_example.txt")

if __name__ == "__main__":
    main()

