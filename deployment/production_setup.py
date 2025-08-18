"""
Configuração de Produção para o Sistema de Recomendações
Gerencia credenciais, variáveis de ambiente e configurações de produção
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionConfig:
    """Gerencia configurações de produção de forma segura"""
    
    def __init__(self, config_path: str = "config_producao.env"):
        self.config_path = config_path
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Configurações padrão de produção
        self.default_config = {
            # Telegram Bot
            'TELEGRAM_BOT_TOKEN': '',
            'TELEGRAM_CHANNEL_ID': '',
            'TELEGRAM_ADMIN_ID': '',
            
            # APIs de Afiliados
            'AMAZON_ASSOCIATE_TAG': '',
            'AWIN_API_TOKEN': '',
            'SHOPEE_API_KEY': '',
            'SHOPEE_API_SECRET': '',
            'ALIEXPRESS_APP_KEY': '',
            'ALIEXPRESS_APP_SECRET': '',
            'MERCADO_LIVRE_TAG': '',
            'MAGAZINE_LUIZA_TAG': '',
            
            # Banco de Dados
            'DATABASE_URL': 'sqlite:///production.db',
            'DATABASE_BACKUP_PATH': './backups/',
            'DATABASE_BACKUP_RETENTION_DAYS': 30,
            
            # Servidor
            'HOST': '0.0.0.0',
            'PORT': 8080,
            'DEBUG': False,
            'SECRET_KEY': '',
            
            # Monitoramento
            'HEALTH_CHECK_INTERVAL': 300,  # 5 minutos
            'ALERT_EMAIL': '',
            'ALERT_SMS_NUMBER': '',
            'SLACK_WEBHOOK_URL': '',
            
            # Rate Limiting
            'MAX_REQUESTS_PER_MINUTE': 60,
            'MAX_REQUESTS_PER_HOUR': 1000,
    
    # Logs
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': './logs/production.log',
            'LOG_MAX_SIZE': 10485760,  # 10MB
            'LOG_BACKUP_COUNT': 5
        }
    
    def _get_or_create_key(self) -> bytes:
        """Obtém ou cria chave de criptografia"""
        key_file = Path('.production_key')
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Cria nova chave
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("🔑 Nova chave de criptografia criada")
            return key
    
    def encrypt_value(self, value: str) -> str:
        """Criptografa um valor sensível"""
        if not value:
            return ''
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Descriptografa um valor criptografado"""
        if not encrypted_value:
            return ''
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Erro ao descriptografar valor: {e}")
            return ''
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configurações de produção"""
        config = self.default_config.copy()
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                logger.info(f"✅ Configuração carregada de {self.config_path}")
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
        
        # Carrega variáveis de ambiente (prioridade)
        for key in config:
            env_value = os.getenv(key)
            if env_value:
                config[key] = env_value
        
        return config
    
    def save_config(self, config: Dict[str, Any], encrypt_sensitive: bool = True):
        """Salva configurações de produção"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("# Configuração de Produção - Sistema de Recomendações\n")
                f.write("# Arquivo gerado automaticamente - NÃO EDITAR MANUALMENTE\n\n")
                
                for key, value in config.items():
                    if encrypt_sensitive and self._is_sensitive_key(key):
                        encrypted_value = self.encrypt_value(str(value))
                        f.write(f"{key}={encrypted_value}\n")
            else:
                        f.write(f"{key}={value}\n")
            
            logger.info(f"✅ Configuração salva em {self.config_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Identifica chaves que contêm informações sensíveis"""
        sensitive_patterns = [
            'TOKEN', 'KEY', 'SECRET', 'PASSWORD', 'API', 'TAG'
        ]
        return any(pattern in key.upper() for pattern in sensitive_patterns)
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configurações e retorna erros encontrados"""
        errors = []
        warnings = []
        
        # Validações obrigatórias
        required_keys = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHANNEL_ID',
            'DATABASE_URL'
        ]
        
        for key in required_keys:
            if not config.get(key):
                errors.append(f"Chave obrigatória ausente: {key}")
        
        # Validações de formato
        if config.get('PORT'):
            try:
                port = int(config['PORT'])
                if not (1 <= port <= 65535):
                    errors.append(f"Porta inválida: {port}")
            except ValueError:
                errors.append(f"Porta deve ser um número: {config['PORT']}")
        
        # Avisos
        if not config.get('SECRET_KEY'):
            warnings.append("SECRET_KEY não configurada - usando valor padrão")
            config['SECRET_KEY'] = Fernet.generate_key().decode()
        
        if not config.get('ALERT_EMAIL') and not config.get('SLACK_WEBHOOK_URL'):
            warnings.append("Sistema de alertas não configurado")
        
        return {
            'config': config,
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
    
    def setup_production_environment(self):
        """Configura ambiente de produção completo"""
        logger.info("🚀 Configurando ambiente de produção...")
        
        # Carrega configuração atual
        config = self.load_config()
        
        # Valida configuração
        validation = self.validate_config(config)
        
        if not validation['is_valid']:
            logger.error("❌ Configuração inválida:")
            for error in validation['errors']:
                logger.error(f"   - {error}")
            return False
    
        # Exibe avisos
        for warning in validation['warnings']:
            logger.warning(f"⚠️  {warning}")
        
        # Salva configuração validada
        self.save_config(validation['config'])
        
        # Cria diretórios necessários
        self._create_directories()
        
        # Configura logging
        self._setup_logging(validation['config'])
        
        logger.info("✅ Ambiente de produção configurado com sucesso!")
            return True
            
    def _create_directories(self):
        """Cria diretórios necessários para produção"""
        directories = [
            './logs',
            './backups',
            './storage/data',
            './storage/temp',
            './migrations'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Diretório criado: {directory}")
    
    def _setup_logging(self, config: Dict[str, Any]):
        """Configura sistema de logging para produção"""
        log_level = getattr(logging, config.get('LOG_LEVEL', 'INFO').upper())
        log_file = config.get('LOG_FILE', './logs/production.log')
        
        # Configura logging para arquivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Formato de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Adiciona handler ao logger raiz
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().setLevel(log_level)
        
        logger.info(f"📝 Logging configurado para: {log_file}")


def main():
    """Função principal para configuração de produção"""
    print("🚀 Configurador de Ambiente de Produção")
    print("=" * 50)
    
    config_manager = ProductionConfig()
    
    if config_manager.setup_production_environment():
        print("\n✅ Configuração concluída com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Configure as credenciais no arquivo config_producao.env")
        print("2. Execute o sistema com: python main.py")
        print("3. Monitore os logs em ./logs/production.log")
    else:
        print("\n❌ Falha na configuração. Verifique os erros acima.")


if __name__ == "__main__":
    main()
