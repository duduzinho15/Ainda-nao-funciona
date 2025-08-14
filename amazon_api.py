"""
Módulo para integração com a API de Produtos da Amazon (PA-API v5).

Este módulo fornece funções para buscar ofertas de produtos na Amazon usando a PA-API v5.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Union

# Configuração básica do logger antes de qualquer outra coisa
def setup_logging():
    """
    Configura o sistema de logging para o módulo.
    
    Returns:
        logging.Logger: Instância do logger configurado
    """
    # Configuração básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    
    # Cria um logger específico para este módulo
    logger = logging.getLogger('amazon_paapi')
    
    # Configura o nível de log para bibliotecas de terceiros
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    
    # Tenta configurar o log para arquivo
    try:
        # Cria diretório de logs se não existir
        os.makedirs('logs', exist_ok=True)
        
        # Cria um handler para arquivo com nível DEBUG
        log_file = os.path.join('logs', f'amazon_api_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Define o formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Adiciona o handler de arquivo ao logger
        logger.addHandler(file_handler)
        logger.debug(f"Logging para arquivo configurado em: {log_file}")
        
    except Exception as e:
        logger.warning(f"Não foi possível configurar logging para arquivo: {e}")
    
    return logger

# Configura o logger
logger = setup_logging()

# Tenta importar a biblioteca oficial da Amazon para PA-API v5
PAAPI_AVAILABLE = False
try:
    from paapi5_python_sdk.api.default_api import DefaultApi
    from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
    from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
    from paapi5_python_sdk.models.partner_type import PartnerType
    from paapi5_python_sdk.models.condition import Condition
    from paapi5_python_sdk.models.delivery_flag import DeliveryFlag
    from paapi5_python_sdk.models.merchant import Merchant
    from paapi5_python_sdk.models.get_items_resource import GetItemsResource
    from paapi5_python_sdk.models.get_items_request import GetItemsRequest
    from paapi5_python_sdk.models.availability import Availability
    from paapi5_python_sdk.models.browse_node_ancestor import BrowseNodeAncestor
    from paapi5_python_sdk.models.browse_node_ancestor_list import BrowseNodeAncestorList
    from paapi5_python_sdk.models.browse_node import BrowseNode
    from paapi5_python_sdk.models.browse_node_list import BrowseNodeList
    from paapi5_python_sdk.models.item_info import ItemInfo
    from paapi5_python_sdk.models.images import Images
    from paapi5_python_sdk.models.image_type import ImageType
    from paapi5_python_sdk.models.image import Image
    from paapi5_python_sdk.models.item import Item
    from paapi5_python_sdk.models.offer_listing import OfferListing
    from paapi5_python_sdk.models.offer_price import OfferPrice
    from paapi5_python_sdk.models.offers import Offers
    from paapi5_python_sdk.models.offers_list import OffersList
    from paapi5_python_sdk.models.prime_information import PrimeInformation
    from paapi5_python_sdk.models.website_sales_rank import WebsiteSalesRank
    from paapi5_python_sdk.rest import ApiException
    from paapi5_python_sdk import Configuration
    
    PAAPI_AVAILABLE = True
    logger.info("Biblioteca python-amazon-paapi importada com sucesso")
    
except ImportError as e:
    logger.error(f"Erro ao importar biblioteca PA-API: {e}")
    logger.error("Instale com: pip install python-amazon-paapi")
    logger.error("A funcionalidade de busca automática da Amazon estará desativada.")
    PAAPI_AVAILABLE = False
    
    # Cria classes vazias para evitar erros de importação
    class DefaultApi:
        pass
    class SearchItemsRequest:
        pass
    class SearchItemsResource:
        pass
    class PartnerType:
        pass
    class Condition:
        pass
    class DeliveryFlag:
        pass
    class Merchant:
        pass
    class GetItemsResource:
        pass
    class GetItemsRequest:
        pass
    class Availability:
        pass
    class BrowseNodeAncestor:
        pass
    class BrowseNodeAncestorList:
        pass
    class BrowseNode:
        pass
    class BrowseNodeList:
        pass
    class ItemInfo:
        pass
    class Images:
        pass
    class ImageType:
        pass
    class Image:
        pass
    class Item:
        pass
    class OfferListing:
        pass
    class OfferPrice:
        pass
    class Offers:
        pass
    class OffersList:
        pass
    class PrimeInformation:
        pass
    class WebsiteSalesRank:
        pass
    class ApiException(Exception):
        pass
    class Configuration:
        pass

# Importa a configuração do projeto
try:
    import config
    from dotenv import load_dotenv
    
    # Carrega variáveis de ambiente do arquivo .env se existir
    load_dotenv()
    
    # Mapeamento de variáveis de ambiente para atributos de configuração
    ENV_VAR_MAPPING = {
        'AMAZON_ACCESS_KEY': 'AMAZON_ACCESS_KEY',
        'AMAZON_SECRET_KEY': 'AMAZON_SECRET_KEY',
        'AMAZON_ASSOCIATE_TAG': 'AMAZON_ASSOCIATE_TAG',
        'TELEGRAM_BOT_TOKEN': 'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID': 'TELEGRAM_CHAT_ID',
        'ADMIN_USER_ID': 'ADMIN_USER_ID'
    }
    
    # Atualiza o config com as variáveis de ambiente, se disponíveis
    for env_var, config_attr in ENV_VAR_MAPPING.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            setattr(config, config_attr, env_value)
    
    # Verifica se as credenciais necessárias estão configuradas
    REQUIRED_CREDENTIALS = [
        'AMAZON_ACCESS_KEY',
        'AMAZON_SECRET_KEY',
        'AMAZON_ASSOCIATE_TAG'
    ]
    
    missing_creds = [cred for cred in REQUIRED_CREDENTIALS if not getattr(config, cred, None)]
    
    if missing_creds:
        if PAAPI_AVAILABLE:
            logger.warning(f"Credenciais da Amazon não configuradas: {', '.join(missing_creds)}")
            logger.warning("A funcionalidade de busca automática da Amazon estará desativada.")
    else:
        logger.info("Todas as credenciais necessárias da Amazon foram configuradas.")
        
except ImportError as e:
    logger.error(f"Erro ao importar o módulo de configuração: {e}")
    logger.error("Certifique-se de que o arquivo config.py existe no diretório raiz.")
    
    # Se não conseguir importar o dotenv, tenta instalar
    if "No module named 'dotenv'" in str(e):
        logger.info("Instalando python-dotenv...")
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
            logger.info("python-dotenv instalado com sucesso. Reinicie o aplicativo.")
        except Exception as install_error:
            logger.error(f"Falha ao instalar python-dotenv: {install_error}")
    
    # Se não conseguir importar o config, cria um módulo vazio
    if "No module named 'config'" in str(e):
        logger.warning("Criando módulo config.py vazio...")
        try:
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write("""# Configurações do Bot Garimpeiro Geek
# Renomeie este arquivo para config.py e preencha as credenciais

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = ''  # Token do seu bot do Telegram
TELEGRAM_CHAT_ID = ''    # ID do chat/canal onde as ofertas serão publicadas
ADMIN_USER_ID = ''       # ID do usuário administrador (pode ser o mesmo do chat)

# Configurações da Amazon PA-API
AMAZON_ACCESS_KEY = ''   # Sua chave de acesso da Amazon PA-API
AMAZON_SECRET_KEY = ''   # Sua chave secreta da Amazon PA-API
AMAZON_ASSOCIATE_TAG = '' # Sua tag de afiliado da Amazon
""")
            logger.info("Arquivo config.py criado. Por favor, preencha as credenciais necessárias.")
        except Exception as file_error:
            logger.error(f"Erro ao criar o arquivo config.py: {file_error}")
    
    # Cria um módulo config vazio para evitar erros de importação
    class Config:
        pass
    
    config = Config()
    for cred in REQUIRED_CREDENTIALS:
        setattr(config, cred, None)

# Configura o logger
logger = setup_logging()

# Verifica se as credenciais da Amazon estão configuradas
if not all([config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY, config.AMAZON_ASSOCIATE_TAG]):
    logger.warning("Credenciais da Amazon PA-API não configuradas. A funcionalidade da Amazon estará desativada.")
    PAAPI_AVAILABLE = False

# Configuração da API Amazon PA-API v5
class AmazonPAAPI:
    """
    Cliente para a API de Publicidade de Produtos da Amazon (PA-API v5).
    
    Esta classe fornece métodos para buscar ofertas de produtos na Amazon usando a PA-API v5.
    Ela lida com autenticação, formatação de requisições e processamento de respostas.
    """
    
    # Constantes
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos
    
    def __init__(self, access_key=None, secret_key=None, associate_tag=None):
        """
        Inicializa o cliente da API com as credenciais fornecidas ou do config.py.
        
        Args:
            access_key (str, optional): Chave de acesso da Amazon PA-API. Se não fornecida, usa config.AMAZON_ACCESS_KEY.
            secret_key (str, optional): Chave secreta da Amazon PA-API. Se não fornecida, usa config.AMAZON_SECRET_KEY.
            associate_tag (str, optional): Tag de afiliado da Amazon. Se não fornecida, usa config.AMAZON_ASSOCIATE_TAG.
            
        Raises:
            ImportError: Se a biblioteca python-amazon-paapi não estiver disponível.
            ValueError: Se as credenciais necessárias não estiverem configuradas.
        """
        if not PAAPI_AVAILABLE:
            raise ImportError("A biblioteca python-amazon-paapi não está disponível. "
                            "Instale com: pip install python-amazon-paapi")
        
        # Usa as credenciais fornecidas ou as do config.py
        self.access_key = access_key or getattr(config, 'AMAZON_ACCESS_KEY', None)
        self.secret_key = secret_key or getattr(config, 'AMAZON_SECRET_KEY', None)
        self.associate_tag = associate_tag or getattr(config, 'AMAZON_ASSOCIATE_TAG', None)
        
        # Verifica se todas as credenciais necessárias estão presentes
        missing_creds = []
        if not self.access_key:
            missing_creds.append('AMAZON_ACCESS_KEY')
        if not self.secret_key:
            missing_creds.append('AMAZON_SECRET_KEY')
        if not self.associate_tag:
            missing_creds.append('AMAZON_ASSOCIATE_TAG')
            
        if missing_creds:
            raise ValueError(
                f"Credenciais da Amazon PA-API ausentes: {', '.join(missing_creds)}. "
                "Configure-as no arquivo .env ou passe como parâmetros."
            )
        
        # Configuração do cliente
        self.host = 'webservices.amazon.com.br'  # Endpoint para o Brasil
        self.region = 'us-west-2'  # Região para assinatura de requisições
        self.marketplace = 'www.amazon.com.br'  # Marketplace brasileiro
        
        # Configuração da API
        self.configuration = self._get_api_configuration()
        self.api_client = DefaultApi(api_client=None, configuration=self.configuration)
        
        # Configura o logger
        self.logger = logging.getLogger('amazon_paapi')
        self.logger.info("Cliente Amazon PA-API inicializado com sucesso")
        self.logger.debug(f"Associate Tag: {self.associate_tag}")
        self.logger.debug(f"Host: {self.host}, Região: {self.region}")
    
    def _get_api_configuration(self) -> Configuration:
        """
        Configura e retorna o objeto de configuração da API.
        
        Returns:
            Configuration: Objeto de configuração da API Amazon PA-API.
            
        Raises:
            ValueError: Se a configuração não puder ser criada com as credenciais fornecidas.
        """
        try:
            self.logger.debug("Configurando cliente da API Amazon PA-API...")
            
            # Cria e configura o objeto de configuração
            configuration = Configuration()
            configuration.access_key = self.access_key
            configuration.secret_key = self.secret_key
            configuration.host = f"{self.host}"  # O endpoint completo é definido na operação
            configuration.region = self.region
            
            # Configurações adicionais
            configuration.debug = False  # Ativar apenas para depuração (expõe credenciais no log)
            
            self.logger.debug("Configuração da API criada com sucesso")
            return configuration
            
        except Exception as e:
            error_msg = f"Erro ao configurar a API da Amazon: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    def search_items(
        self, 
        keywords: Union[str, List[str]], 
        item_count: int = 10, 
        min_saving_percent: int = 30,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search_index: str = 'All',
        condition: str = 'New',
        merchant: str = 'Amazon',
        delivery_flags: Optional[List[str]] = None,
        sort_by: str = 'Relevance',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Busca itens na Amazon com base em palavras-chave.
        
        Args:
            keywords: Palavra-chave ou lista de palavras-chave para busca.
            item_count: Número máximo de itens a retornar (1-10).
            min_saving_percent: Porcentagem mínima de desconto para filtrar (0-100).
            min_price: Preço mínimo dos itens (opcional).
            max_price: Preço máximo dos itens (opcional).
            search_index: Categoria de busca (ex: 'All', 'Electronics', 'Computers').
            condition: Condição do produto ('New', 'Used', 'Refurbished', 'All').
            merchant: Filtro por vendedor (ex: 'Amazon', 'All').
            delivery_flags: Filtros de entrega (ex: ['PrimeEligible', 'FreeShipping']).
            sort_by: Critério de ordenação ('Relevance', 'Price:HighToLow', 'Price:LowToHigh', 'AvgCustomerReviews').
            **kwargs: Parâmetros adicionais para a API.
            
        Returns:
            Lista de dicionários com informações dos produtos encontrados, cada um contendo:
            - asin: ID único do produto na Amazon
            - title: Título do produto
            - price: Preço atual (string formatada)
            - list_price: Preço de listagem (string formatada)
            - discount_percent: Percentual de desconto
            - url: URL do produto
            - image_url: URL da imagem principal
            - is_prime: Se o produto é elegível para Prime
            - merchant: Nome do vendedor
            - features: Lista de características do produto
            - category: Categoria principal do produto
            - ratings_count: Número de avaliações
            - rating: Média de avaliações (0-5)
            
        Raises:
            ValueError: Se os parâmetros de entrada forem inválidos.
            ApiException: Se ocorrer um erro na chamada à API.
        """
        if not PAAPI_AVAILABLE:
            self.logger.error("A biblioteca PA-API não está disponível")
            return []
            
        try:
            # Validação dos parâmetros
            if not keywords:
                raise ValueError("Pelo menos uma palavra-chave deve ser fornecida")
                
            if not isinstance(keywords, list):
                keywords = [keywords]
                
            if not (1 <= item_count <= 10):
                raise ValueError("item_count deve estar entre 1 e 10")
                
            if not (0 <= min_saving_percent <= 100):
                raise ValueError("min_saving_percent deve estar entre 0 e 100")
                
            # Configura os recursos que serão retornados
            resources = [
                SearchItemsResource.ITEMINFO_TITLE,
                SearchItemsResource.ITEMINFO_FEATURES,
                SearchItemsResource.ITEMINFO_PRODUCTINFO,
                SearchItemsResource.ITEMINFO_CLASSIFICATIONS,
                SearchItemsResource.OFFERS_LISTINGS_PRICE,
                SearchItemsResource.OFFERS_LISTINGS_SAVINGBASIS,
                SearchItemsResource.OFFERS_LISTINGS_CONDITION,
                SearchItemsResource.OFFERS_LISTINGS_ISBUYBOXWINNER,
                SearchItemsResource.OFFERS_LISTINGS_DELIVERYINFO_ISPRIMEELIGIBLE,
                SearchItemsResource.OFFERS_LISTINGS_MERCHANTINFO,
                SearchItemsResource.IMAGES_PRIMARY_LARGE,
                SearchItemsResource.IMAGES_VARIANTS,
                SearchItemsResource.BROWSE_NODE_INFO_BROWSE_NODES,
                SearchItemsResource.CUSTOMER_REVIEWS_COUNT,
                SearchItemsResource.CUSTOMER_REVIEWS_STAR_RATING,
            ]
            
            # Cria a requisição de busca
            self.logger.info(f"Preparando busca para: {', '.join(keywords)}")
            
            search_request = SearchItemsRequest(
                partner_tag=self.associate_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                item_count=item_count,
                min_saving_percent=min_saving_percent,
                search_index=search_index,
                resources=resources,
                sort_by=sort_by,
                **kwargs
            )
            
            # Adiciona filtros adicionais se fornecidos
            if min_price is not None:
                search_request.min_price = min_price * 100  # Converte para centavos
                
            if max_price is not None:
                search_request.max_price = max_price * 100  # Converte para centavos
                
            if condition.lower() != 'all':
                search_request.condition = Condition(condition)
                
            if merchant.lower() != 'all':
                search_request.merchant = Merchant(merchant)
                
            if delivery_flags:
                search_request.delivery_flags = [DeliveryFlag(flag) for flag in delivery_flags]
            
            # Executa a busca com retry em caso de falha
            for attempt in range(self.MAX_RETRIES):
                try:
                    self.logger.debug(f"Executando busca (tentativa {attempt + 1}/{self.MAX_RETRIES})")
                    response = self.api_client.search_items(search_request)
                    break
                except ApiException as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise  # Re-lança a exceção na última tentativa
                    wait_time = self.RETRY_DELAY * (attempt + 1)
                    self.logger.warning(
                        f"Erro na busca (tentativa {attempt + 1}): {e}. "
                        f"Aguardando {wait_time}s antes de tentar novamente..."
                    )
                    time.sleep(wait_time)
            
            # Processa a resposta
            self.logger.info(f"Busca concluída. Status: {response.search_result}")
            
            if response.errors:
                for error in response.errors:
                    self.logger.error(f"Erro na resposta da API: {error.code} - {error.message}")
                return []
                
            if not response.search_result or not response.search_result.items:
                self.logger.info("Nenhum item encontrado para os critérios de busca")
                return []
                
            # Processa os itens encontrados
            return self._process_search_response(response.search_result.items)
            
        except ValueError as ve:
            self.logger.error(f"Erro de validação nos parâmetros: {str(ve)}")
            raise
            
        except ApiException as e:
            error_msg = f"Erro na API da Amazon (Status {e.status}): {e.reason}"
            self.logger.error(error_msg)
            
            if e.body:
                try:
                    error_data = json.loads(e.body)
                    self.logger.error(f"Detalhes do erro: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except Exception as json_err:
                    self.logger.error(f"Resposta de erro (não-JSON): {e.body}")
            
        except ValueError as ve:
            self.logger.error(f"Erro de validação nos parâmetros: {str(ve)}")
            raise
                
        except ApiException as e:
            error_msg = f"Erro na API da Amazon (Status {e.status}): {e.reason}"
            self.logger.error(error_msg)
                
            if e.body:
                try:
                    error_data = json.loads(e.body)
                    self.logger.error(f"Detalhes do erro: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except Exception as json_err:
                    self.logger.error(f"Resposta de erro (não-JSON): {e.body}")
                
            raise ApiException(f"{error_msg}. Consulte os logs para mais detalhes.") from e
                
        except Exception as e:
            error_msg = f"Erro inesperado ao buscar itens: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise Exception(f"{error_msg}. Consulte os logs para mais detalhes.") from e
                
    def _extract_title(self, item: Any) -> str:
        """Extrai o título do produto."""
        try:
            if hasattr(item, 'item_info') and hasattr(item.item_info, 'title') and hasattr(item.item_info.title, 'display_value'):
                return item.item_info.title.display_value
            return "Produto sem título"
        except Exception as e:
            self.logger.warning(f"Erro ao extrair título: {str(e)}")
            return "Produto sem título"
    
    def _extract_price_info(self, item: Any) -> Dict[str, Any]:
        """Extrai informações de preço e desconto do produto."""
        price_info = {
            'price': None,
            'list_price': None,
            'discount_percent': 0,
            'discount_amount': None,
            'currency': 'BRL'
        }
        
        try:
            # Verifica se há ofertas disponíveis
            if hasattr(item, 'offers') and hasattr(item.offers, 'listings') and item.offers.listings:
                listing = item.offers.listings[0]
                    
                # Preço atual
                if hasattr(listing, 'price') and hasattr(listing.price, 'amount') and listing.price.amount is not None:
                    price_info['price'] = float(listing.price.amount)
                    
                # Preço original (de lista)
                if hasattr(listing, 'saving_basis') and hasattr(listing.saving_basis, 'amount') and listing.saving_basis.amount is not None:
                    price_info['list_price'] = float(listing.saving_basis.amount)
                    
                # Calcula desconto se ambos os preços estiverem disponíveis
                if price_info['price'] and price_info['list_price'] and price_info['list_price'] > 0:
                    discount = ((price_info['list_price'] - price_info['price']) / price_info['list_price']) * 100
                    price_info['discount_percent'] = round(discount, 1)
                    price_info['discount_amount'] = price_info['list_price'] - price_info['price']
                    
                # Moeda
                if hasattr(listing.price, 'currency'):
                    price_info['currency'] = listing.price.currency
                
            # Formata os preços como strings
            if price_info['price'] is not None:
                price_info['price_str'] = f"R$ {price_info['price']:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
                
            if price_info['list_price'] is not None:
                price_info['list_price_str'] = f"R$ {price_info['list_price']:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
                
            if price_info['discount_amount'] is not None:
                price_info['discount_amount_str'] = f"R$ {price_info['discount_amount']:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
                
        except Exception as e:
            self.logger.warning(f"Erro ao extrair informações de preço: {str(e)}")
            
        return price_info
    
    def _extract_image_url(self, item: Any) -> Optional[str]:
        """Extrai a URL da imagem principal do produto."""
        try:
            if hasattr(item, 'images') and hasattr(item.images, 'primary') and hasattr(item.images.primary, 'large') and hasattr(item.images.primary.large, 'url'):
                return item.images.primary.large.url
            return None
        except Exception as e:
            self.logger.warning(f"Erro ao extrair URL da imagem: {str(e)}")
            return None
    
    def _extract_seller_info(self, item: Any) -> Dict[str, Any]:
        """Extrai informações do vendedor e entrega."""
        seller_info = {
            'merchant': 'Vendedor não especificado',
            'is_amazon': False,
            'is_prime_eligible': False,
            'is_fulfilled_by_amazon': False
        }
        
        try:
            if hasattr(item, 'offers') and hasattr(item.offers, 'listings') and item.offers.listings:
                listing = item.offers.listings[0]
                    
                # Nome do vendedor
                if hasattr(listing, 'merchant_info') and hasattr(listing.merchant_info, 'name'):
                    seller_info['merchant'] = listing.merchant_info.name
                    seller_info['is_amazon'] = 'amazon' in seller_info['merchant'].lower()
                
                # Informações de entrega
                if hasattr(listing, 'delivery_info') and hasattr(listing.delivery_info, 'is_prime_eligible'):
                    seller_info['is_prime_eligible'] = bool(listing.delivery_info.is_prime_eligible)
                
                # Se é vendido e entregue pela Amazon
                if hasattr(listing, 'fulfillment') and hasattr(listing.fulfillment, 'fulfillment_channel'):
                    seller_info['is_fulfilled_by_amazon'] = (listing.fulfillment.fulfillment_channel.lower() == 'amazon')
                
        except Exception as e:
            self.logger.warning(f"Erro ao extrair informações do vendedor: {str(e)}")
            
        return seller_info
    
    def _extract_rating_info(self, item: Any) -> Dict[str, Any]:
        """Extrai informações de avaliação do produto."""
        rating_info = {
            'rating': None,
            'ratings_count': 0
        }
        
        try:
            if hasattr(item, 'customer_reviews'):
                # Avaliação média em estrelas
                if hasattr(item.customer_reviews, 'star_rating') and item.customer_reviews.star_rating is not None:
                    rating_info['rating'] = float(item.customer_reviews.star_rating)
                
                # Contagem de avaliações
                if hasattr(item.customer_reviews, 'count') and item.customer_reviews.count is not None:
                    rating_info['ratings_count'] = int(item.customer_reviews.count)
                
        except Exception as e:
            self.logger.warning(f"Erro ao extrair informações de avaliação: {str(e)}")
            
        return rating_info
    
    def _extract_category(self, item: Any) -> str:
        """Extrai a categoria principal do produto."""
        try:
            if hasattr(item, 'browse_node_info') and hasattr(item.browse_node_info, 'browse_nodes') and item.browse_node_info.browse_nodes:
                # Pega o primeiro nó de categoria
                browse_node = item.browse_node_info.browse_nodes[0]
                if hasattr(browse_node, 'display_name') and hasattr(browse_node.display_name, 'value'):
                    return browse_node.display_name.value
            return "Sem categoria"
        except Exception as e:
            self.logger.warning(f"Erro ao extrair categoria: {str(e)}")
            return "Sem categoria"
    
    def _extract_features(self, item: Any) -> List[str]:
        """Extrai as características do produto."""
        try:
            if hasattr(item, 'item_info') and hasattr(item.item_info, 'features') and hasattr(item.item_info.features, 'display_values'):
                return list(item.item_info.features.display_values)
            return []
        except Exception as e:
            self.logger.warning(f"Erro ao extrair características: {str(e)}")
            return []
    
    def _process_search_response(self, items: List[Any]) -> List[Dict[str, Any]]:
        """
        Processa a resposta da API da Amazon e extrai as informações relevantes dos produtos.
        
        Args:
            items: Lista de itens retornados pela API da Amazon.
                
        Returns:
            Lista de dicionários contendo as informações processadas de cada produto.
                
        Cada dicionário contém as seguintes chaves:
            - asin: ID único do produto na Amazon
            - title: Título do produto
            - price: Preço atual formatado como string (ex: "R$ 1.234,56")
            - list_price: Preço de listagem formatado como string (pode ser None)
            - discount_percent: Percentual de desconto (pode ser None)
            - discount_amount: Valor do desconto formatado (pode ser None)
            - url: URL do produto com o código de afiliado
            - image_url: URL da imagem principal do produto
            - is_prime: Booleano indicando se o produto é elegível para Prime
            - merchant: Nome do vendedor
            - features: Lista de características do produto
            - category: Categoria principal do produto
            - ratings_count: Número de avaliações (pode ser None)
            - rating: Média de avaliações (0-5, pode ser None)
        """
        if not items:
            self.logger.debug("Nenhum item para processar na resposta da API")
            return []
                
        self.logger.info(f"Processando {len(items)} itens da resposta da API...")
        processed_items = []
            
        for item in items:
            try:
                # Extrai informações básicas do item
                asin = getattr(item, 'asin', '')
                if not asin:
                    self.logger.warning("Item sem ASIN, pulando...")
                    continue
                        
                self.logger.debug(f"Processando item ASIN: {asin}")
                    
                # URL do produto com código de afiliado
                url = f"https://www.amazon.com.br/dp/{asin}?tag={self.associate_tag}"
                    
                # Extrai o título
                title = self._extract_title(item)
                    
                # Extrai informações de preço e desconto
                price_info = self._extract_price_info(item)
                    
                # Extrai a URL da imagem
                image_url = self._extract_image_url(item)
                    
                # Extrai informações do vendedor e entrega
                seller_info = self._extract_seller_info(item)
                    
                # Extrai informações de avaliação
                rating_info = self._extract_rating_info(item)
                    
                # Extrai a categoria principal
                category = self._extract_category(item)
                    
                # Extrai características do produto
                features = self._extract_features(item)
                    
                # Cria o dicionário com todas as informações do produto
                product = {
                    'asin': asin,
                    'title': title,
                    'url': url,
                    'image_url': image_url,
                    'features': features,
                    'category': category,
                    **price_info,
                    **seller_info,
                    **rating_info
                }
                    
                processed_items.append(product)
                self.logger.debug(f"Item processado com sucesso: {title[:50]}...")
                    
            except Exception as e:
                self.logger.error(f"Erro ao processar item ASIN {getattr(item, 'asin', 'desconhecido')}: {str(e)}", 
                                exc_info=True)
                continue
                    
        self.logger.info(f"Processamento concluído. {len(processed_items)} itens processados com sucesso.")
        return processed_items

def create_api_client():
    """
    Cria e retorna uma instância do cliente da API da Amazon.
    
    Returns:
        Instância de AmazonPAAPI ou None se não for possível criar
    """
    if not PAAPI_AVAILABLE:
        logger.warning("PA-API não está disponível. Verifique as dependências.")
        return None
        
    if not all([config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY, config.AMAZON_ASSOCIATE_TAG]):
        logger.warning("Credenciais da Amazon não configuradas corretamente.")
        return None
        
    try:
        return AmazonPAAPI()
    except Exception as e:
        logger.error(f"Erro ao criar cliente da API da Amazon: {str(e)}")
        return None

async def buscar_ofertas_amazon(palavras_chave: List[str], max_itens: int = 5) -> List[Dict[str, Any]]:
    """
    Busca ofertas na Amazon com base nas palavras-chave fornecidas.
    
    Args:
        palavras_chave: Lista de termos de busca
        max_itens: Número máximo de itens a retornar por busca (máx 10)
        
    Returns:
        Lista de dicionários contendo informações dos produtos encontrados
    """
    if not palavras_chave:
        logger.warning("Nenhuma palavra-chave fornecida para busca na Amazon.")
        return []
    
    # Limita o número de itens ao máximo permitido
    max_itens = min(max(1, max_itens), 10)
    
    try:
        # Cria o cliente da API
        api_client = create_api_client()
        if not api_client:
            logger.error("Não foi possível criar o cliente da API da Amazon.")
            return []
        
        # Executa a busca
        logger.info(f"Buscando até {max_itens} ofertas na Amazon para: {', '.join(palavras_chave)}")
        
        # Executa a busca de forma síncrona com run_in_executor
        loop = asyncio.get_running_loop()
        resultados = await loop.run_in_executor(
            None,
            lambda: api_client.search_items(
                keywords=palavras_chave,
                item_count=max_itens,
                min_saving_percent=30,
                search_index='All'
            )
        )
        
        logger.info(f"Encontrados {len(resultados)} ofertas na Amazon.")
        return resultados
        
    except Exception as e:
        logger.error(f"Erro ao buscar ofertas na Amazon: {str(e)}", exc_info=True)
        return []

async def testar_busca():
    """
    Função para testar a busca na API da Amazon.
    
    Esta função testa a busca de ofertas na Amazon usando a PA-API v5.
    Ela realiza uma busca assíncrona por produtos com base em palavras-chave
    e exibe os resultados formatados.
    """
    if not PAAPI_AVAILABLE:
        print("Erro: A biblioteca python-amazon-paapi não está instalada.")
        print("Instale com: pip install python-amazon-paapi")
        return
        
    if not all([config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY, config.AMAZON_ASSOCIATE_TAG]):
        print("Erro: Credenciais da Amazon não configuradas corretamente.")
        print("Verifique as configurações em config.py")
        return
    
    print("\n=== TESTE DA API DA AMAZON ===")
    print(f"Usando a conta associada a: {config.AMAZON_ASSOCIATE_TAG}")
    
    try:
        # Testa a busca por palavras-chave
        palavras_chave = ["ssd 1tb", "notebook gamer", "monitor 144hz"]
        
        print(f"\nBuscando ofertas para: {', '.join(palavras_chave)}")
        
        # Executa a busca assíncrona
        ofertas = await buscar_ofertas_amazon(palavras_chave, max_itens=3)
        
        if not ofertas:
            print("Nenhuma oferta encontrada.")
            print(f"- AMAZON_ASSOCIATE_TAG (atual: {config.AMAZON_ASSOCIATE_TAG if hasattr(config, 'AMAZON_ASSOCIATE_TAG') else 'Não configurado'})")
            return
            
        print(f"\n=== {len(ofertas)} OFERTAS ENCONTRADAS ===\n")
        
        # Exibe os resultados
        for i, oferta in enumerate(ofertas, 1):
            print(f"=== OFERTA {i} ===")
            print(f"Título: {oferta.get('title', 'Sem título')}")
            print(f"Preço: R$ {oferta.get('price', 'N/A'):.2f}")
            
            if oferta.get('list_price'):
                print(f"Preço original: R$ {oferta['list_price']:.2f}")
                print(f"Desconto: {oferta.get('discount_percent', 0)}%")
            
            print(f"Vendido por: {oferta.get('seller', 'Vendedor não especificado')}")
            print(f"URL: {oferta.get('url', 'URL não disponível')}")
            
            if oferta.get('image_url'):
                print(f"Imagem: {oferta['image_url']}")
                
            print()
            
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    # Executa o teste assíncrono
    try:
        asyncio.run(testar_busca())
    except KeyboardInterrupt:
        print("\n❌ Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a execução do teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔍 Análise de resultados concluída.")
        print("1. Verifique se as credenciais da Amazon estão corretas no arquivo config.py")
        print("2. Verifique se a região configurada está correta (atualmente: us-west-2)")
        print("3. Verifique se o Amazon Associate Tag está ativo e configurado corretamente")
        print("4. Consulte a documentação da API para códigos de erro específicos")
        print("5. Verifique os logs para informações detalhadas sobre o erro")
