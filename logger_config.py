"""
Configuração centralizada do sistema de logging para o Garimpeiro Geek
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys

class GarimpeiroLogger:
    """Sistema de logging centralizado para o Garimpeiro Geek"""
    
    def __init__(self, name: str = "garimpeiro_geek"):
        self.name = name
        self.logger = None
        self.setup_logger()
    
    def setup_logger(self):
        """Configura o sistema de logging"""
        # Cria o logger principal
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers
        if self.logger.handlers:
            return
        
        # Cria diretório de logs se não existir
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Formato das mensagens de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para arquivo principal (todas as mensagens)
        main_handler = RotatingFileHandler(
            os.path.join(log_dir, "garimpeiro.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(formatter)
        
        # Handler para arquivo de erros (apenas erros e críticos)
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, "garimpeiro_errors.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Handler para arquivo de scraping (apenas mensagens relacionadas ao scraping)
        scraping_handler = RotatingFileHandler(
            os.path.join(log_dir, "garimpeiro_scraping.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        scraping_handler.setLevel(logging.INFO)
        scraping_handler.setFormatter(formatter)
        
        # Filtro para mensagens de scraping
        class ScrapingFilter(logging.Filter):
            def filter(self, record):
                return any(keyword in record.getMessage().lower() for keyword in [
                    'scraping', 'scraper', 'coleta', 'oferta', 'produto', 'magalu', 
                    'amazon', 'shopee', 'promobit', 'aliexpress', 'publicação', 'telegram'
                ])
        
        scraping_handler.addFilter(ScrapingFilter())
        
        # Handler para console (apenas INFO e acima)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Adiciona todos os handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(scraping_handler)
        self.logger.addHandler(console_handler)
        
        # Log inicial
        self.logger.info("🚀 Sistema de logging inicializado com sucesso")
        self.logger.info(f"📁 Diretório de logs: {os.path.abspath(log_dir)}")
    
    def get_logger(self, name: str = None):
        """Retorna um logger específico"""
        if name:
            return logging.getLogger(f"{self.name}.{name}")
        return self.logger
    
    def log_scraping_start(self, store_name: str, urls_count: int):
        """Registra o início do scraping de uma loja"""
        self.logger.info(f"🔍 [SCRAPING] Iniciando coleta em {store_name} - {urls_count} URLs para processar")
    
    def log_scraping_progress(self, store_name: str, current_url: int, total_urls: int, products_found: int):
        """Registra o progresso do scraping"""
        self.logger.info(f"📊 [SCRAPING] {store_name}: URL {current_url}/{total_urls} - {products_found} produtos encontrados")
    
    def log_scraping_complete(self, store_name: str, total_products: int, duration: float):
        """Registra a conclusão do scraping"""
        self.logger.info(f"✅ [SCRAPING] {store_name}: Concluído - {total_products} produtos em {duration:.2f}s")
    
    def log_product_found(self, store_name: str, product_title: str, price: str, discount: str = None):
        """Registra um produto encontrado"""
        discount_info = f" - {discount}% OFF" if discount else ""
        self.logger.info(f"🛍️ [PRODUTO] {store_name}: {product_title[:50]}... - R$ {price}{discount_info}")
    
    def log_duplicate_product(self, product_title: str, store_name: str):
        """Registra produto duplicado"""
        self.logger.info(f"🔄 [DUPLICATA] Produto já existe: {product_title[:50]}... ({store_name})")
    
    def log_new_product(self, product_title: str, store_name: str):
        """Registra novo produto"""
        self.logger.info(f"🆕 [NOVO] Produto encontrado: {product_title[:50]}... ({store_name})")
    
    def log_affiliate_conversion(self, original_url: str, affiliate_url: str):
        """Registra conversão de link de afiliado"""
        self.logger.info(f"🔗 [AFILIADO] Link convertido: {original_url[:50]}... -> {affiliate_url[:50]}...")
    
    def log_telegram_publication(self, product_title: str, success: bool, error: str = None):
        """Registra publicação no Telegram"""
        if success:
            self.logger.info(f"📱 [TELEGRAM] Oferta publicada com sucesso: {product_title[:50]}...")
        else:
            self.logger.error(f"❌ [TELEGRAM] Falha ao publicar: {product_title[:50]}... - Erro: {error}")
    
    def log_database_operation(self, operation: str, product_title: str, success: bool, error: str = None):
        """Registra operações no banco de dados"""
        if success:
            self.logger.info(f"💾 [BANCO] {operation}: {product_title[:50]}...")
        else:
            self.logger.error(f"❌ [BANCO] {operation} falhou: {product_title[:50]}... - Erro: {error}")
    
    def log_automation_cycle(self, cycle_number: int, total_products: int, new_products: int, published: int):
        """Registra o resumo de um ciclo de automação"""
        self.logger.info(f"🔄 [CICLO {cycle_number}] Resumo: {total_products} produtos processados, {new_products} novos, {published} publicados")
    
    def log_error(self, context: str, error: Exception, details: str = None):
        """Registra erros com contexto"""
        error_msg = f"❌ [ERRO] {context}: {str(error)}"
        if details:
            error_msg += f" - Detalhes: {details}"
        self.logger.error(error_msg, exc_info=True)
    
    def log_warning(self, context: str, message: str):
        """Registra avisos"""
        self.logger.warning(f"⚠️ [AVISO] {context}: {message}")
    
    def log_info(self, context: str, message: str):
        """Registra informações gerais"""
        self.logger.info(f"ℹ️ [INFO] {context}: {message}")
    
    def log_debug(self, context: str, message: str):
        """Registra informações de debug"""
        self.logger.debug(f"🔍 [DEBUG] {context}: {message}")

# Instância global do logger
garimpeiro_logger = GarimpeiroLogger()

def get_logger(name: str = None):
    """Função helper para obter um logger"""
    return garimpeiro_logger.get_logger(name)

def log_scraping_start(store_name: str, urls_count: int):
    """Helper para registrar início do scraping"""
    garimpeiro_logger.log_scraping_start(store_name, urls_count)

def log_scraping_complete(store_name: str, total_products: int, duration: float):
    """Helper para registrar conclusão do scraping"""
    garimpeiro_logger.log_scraping_complete(store_name, total_products, duration)

def log_product_found(store_name: str, product_title: str, price: str, discount: str = None):
    """Helper para registrar produto encontrado"""
    garimpeiro_logger.log_product_found(store_name, product_title, price, discount)

def log_new_product(product_title: str, store_name: str):
    """Helper para registrar novo produto"""
    garimpeiro_logger.log_new_product(product_title, store_name)

def log_duplicate_product(product_title: str, store_name: str):
    """Helper para registrar produto duplicado"""
    garimpeiro_logger.log_duplicate_product(product_title, store_name)

def log_telegram_publication(product_title: str, success: bool, error: str = None):
    """Helper para registrar publicação no Telegram"""
    garimpeiro_logger.log_telegram_publication(product_title, success, error)

def log_automation_cycle(cycle_number: int, total_products: int, new_products: int, published: int):
    """Helper para registrar ciclo de automação"""
    garimpeiro_logger.log_automation_cycle(cycle_number, total_products, new_products, published)

def log_error(context: str, error: Exception, details: str = None):
    """Helper para registrar erros"""
    garimpeiro_logger.log_error(context, error, details)

def log_info(context: str, message: str):
    """Helper para registrar informações"""
    garimpeiro_logger.log_info(context, message)

def log_warning(context: str, message: str):
    """Helper para registrar avisos"""
    garimpeiro_logger.log_warning(context, message)

