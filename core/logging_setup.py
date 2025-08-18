"""
Configuração de logging para o sistema Garimpeiro Geek.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from .models import LogLevel


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configura o sistema de logging.

    Args:
        level: Nível de logging.
        log_file: Arquivo para salvar logs (opcional).
        max_bytes: Tamanho máximo do arquivo de log.
        backup_count: Número de arquivos de backup.
        console_output: Se deve mostrar logs no console.

    Returns:
        Logger configurado.
    """
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))

    # Limpar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formato dos logs
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.value))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Handler para arquivo
    if log_file:
        try:
            # Garantir que o diretório existe
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Handler com rotação automática
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setLevel(getattr(logging, level.value))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            logging.info(f"Logging configurado para arquivo: {log_file}")

        except Exception as e:
            logging.error(f"Erro ao configurar logging para arquivo: {e}")

    # Configurar loggers específicos
    _setup_specific_loggers(level)

    logging.info(f"Logging configurado com nível: {level.value}")
    return root_logger


def _setup_specific_loggers(level: LogLevel):
    """Configura loggers específicos do sistema."""

    # Logger para scraping
    scraper_logger = logging.getLogger("scraper")
    scraper_logger.setLevel(getattr(logging, level.value))

    # Logger para métricas
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(getattr(logging, level.value))

    # Logger para dashboard
    dashboard_logger = logging.getLogger("dashboard")
    dashboard_logger.setLevel(getattr(logging, level.value))

    # Logger para bot
    bot_logger = logging.getLogger("bot")
    bot_logger.setLevel(getattr(logging, level.value))


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado.

    Args:
        name: Nome do logger.

    Returns:
        Logger configurado.
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: LogLevel):
    """
    Define o nível de logging para um logger específico.

    Args:
        logger_name: Nome do logger.
        level: Novo nível de logging.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.value))


def add_file_handler(
    logger: logging.Logger,
    log_file: Path,
    level: LogLevel = LogLevel.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
):
    """
    Adiciona um handler de arquivo a um logger específico.

    Args:
        logger: Logger para adicionar o handler.
        log_file: Arquivo de log.
        level: Nível de logging.
        max_bytes: Tamanho máximo do arquivo.
        backup_count: Número de backups.
    """
    try:
        # Garantir que o diretório existe
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Handler com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(getattr(logging, level.value))

        # Formato
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.info(f"Handler de arquivo adicionado: {log_file}")

    except Exception as e:
        logger.error(f"Erro ao adicionar handler de arquivo: {e}")


def remove_file_handler(logger: logging.Logger, log_file: Path):
    """
    Remove um handler de arquivo específico de um logger.

    Args:
        logger: Logger para remover o handler.
        log_file: Arquivo de log do handler.
    """
    handlers_to_remove = []

    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            if handler.baseFilename == str(log_file.absolute()):
                handlers_to_remove.append(handler)

    for handler in handlers_to_remove:
        logger.removeHandler(handler)
        logger.info(f"Handler de arquivo removido: {log_file}")


def log_function_call(func_name: str, *args, **kwargs):
    """
    Decorator para logar chamadas de função.

    Args:
        func_name: Nome da função.
        *args: Argumentos posicionais.
        **kwargs: Argumentos nomeados.
    """

    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            logger = get_logger(func_name)
            logger.debug(
                f"Chamando {func_name} com args={func_args}, kwargs={func_kwargs}"
            )

            try:
                result = func(*func_args, **func_kwargs)
                logger.debug(f"{func_name} retornou: {result}")
                return result
            except Exception as e:
                logger.error(f"Erro em {func_name}: {e}")
                raise

        return wrapper

    return decorator


def setup_performance_logging(log_file: Path):
    """
    Configura logging específico para performance.

    Args:
        log_file: Arquivo para logs de performance.
    """
    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.INFO)

    # Handler específico para performance
    perf_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    perf_handler.setLevel(logging.INFO)

    # Formato específico para performance
    perf_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    perf_handler.setFormatter(perf_formatter)

    perf_logger.addHandler(perf_handler)
    perf_logger.info("Logging de performance configurado")


def log_performance(operation: str, duration: float, **kwargs):
    """
    Loga métricas de performance.

    Args:
        operation: Nome da operação.
        duration: Duração em segundos.
        **kwargs: Métricas adicionais.
    """
    perf_logger = logging.getLogger("performance")

    metrics = {
        "operation": operation,
        "duration": duration,
        "duration_ms": round(duration * 1000, 2),
        **kwargs,
    }

    perf_logger.info(f"Performance: {metrics}")


def cleanup_logs(log_dir: Path, max_age_days: int = 30):
    """
    Remove logs antigos.

    Args:
        log_dir: Diretório de logs.
        max_age_days: Idade máxima dos logs em dias.
    """
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0

        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                removed_count += 1

        if removed_count > 0:
            logging.info(f"Removidos {removed_count} logs antigos")

    except Exception as e:
        logging.error(f"Erro ao limpar logs antigos: {e}")
