"""
Configuração de logging do sistema Garimpeiro Geek
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Configura o sistema de logging
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para o arquivo de log
        max_size: Tamanho máximo do arquivo de log em bytes
        backup_count: Número de arquivos de backup
        format_string: Formato das mensagens de log
    
    Returns:
        Logger configurado
    """
    
    # Criar diretório de logs se não existir
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(format_string)
    
    # Configurar handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Configurar handler para arquivo (se especificado)
    handlers = [console_handler]
    
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        handlers.append(file_handler)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Adicionar novos handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    loggers_to_configure = [
        "core",
        "app",
        "scrapers",
        "telegram",
        "database"
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
    
    # Configurar logging de bibliotecas externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    print(f"✅ Sistema de logging configurado (nível: {level})")
    if log_file:
        print(f"📝 Logs sendo salvos em: {log_file}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger específico
    
    Args:
        name: Nome do logger
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

def set_log_level(logger_name: str, level: str):
    """
    Define o nível de logging para um logger específico
    
    Args:
        logger_name: Nome do logger
        level: Nível de logging
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    print(f"⚙️ Nível de logging para '{logger_name}' definido como: {level}")

def add_file_handler(logger_name: str, log_file: str, level: str = "INFO"):
    """
    Adiciona um handler de arquivo para um logger específico
    
    Args:
        logger_name: Nome do logger
        log_file: Caminho para o arquivo de log
        level: Nível de logging
    """
    logger = logging.getLogger(logger_name)
    
    # Criar diretório se não existir
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar handler
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setLevel(getattr(logging, level.upper()))
    
    # Configurar formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Adicionar handler
    logger.addHandler(handler)
    print(f"📝 Handler de arquivo adicionado para '{logger_name}': {log_file}")

def setup_structured_logging():
    """
    Configura logging estruturado para produção
    """
    import json
    from datetime import datetime
    
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry, ensure_ascii=False)
    
    # Aplicar formatter estruturado
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(StructuredFormatter())
    
    print("✅ Logging estruturado configurado")

def log_function_call(func):
    """
    Decorator para logar chamadas de função
    
    Args:
        func: Função a ser decorada
    
    Returns:
        Função decorada
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Chamando função: {func.__name__} com args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Função {func.__name__} executada com sucesso")
            return result
        except Exception as e:
            logger.error(f"Erro na função {func.__name__}: {e}")
            raise
    
    return wrapper
