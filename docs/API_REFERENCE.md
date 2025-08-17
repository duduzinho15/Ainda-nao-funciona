# 📚 Referência da API - Sistema Garimpeiro Geek

## 🏗️ **Visão Geral**

O Sistema Garimpeiro Geek é uma plataforma completa para busca automática de ofertas e postagem no Telegram. Esta documentação descreve todas as APIs e funcionalidades disponíveis.

---

## 🔗 **Sistema de Afiliados**

### **Classe: AffiliateLinkConverter**

Converte URLs de produtos em links de afiliado para todas as plataformas suportadas.

#### **Métodos Principais**

##### `detectar_loja(url: str) -> str`
Detecta automaticamente a loja baseada no domínio da URL.

**Parâmetros:**
- `url` (str): URL do produto

**Retorna:**
- `str`: Nome da loja detectada

**Exemplo:**
```python
converter = AffiliateLinkConverter()
loja = converter.detectar_loja("https://www.amazon.com.br/dp/B0CHX1Q1FY")
# Retorna: "Amazon"
```

##### `async gerar_link_afiliado(url: str, loja: Optional[str] = None) -> str`
Gera link de afiliado para a URL fornecida.

**Parâmetros:**
- `url` (str): URL original do produto
- `loja` (Optional[str]): Nome da loja (se não fornecido, será detectado automaticamente)

**Retorna:**
- `str`: URL de afiliado

**Exemplo:**
```python
converter = AffiliateLinkConverter()
affiliate_url = await converter.gerar_link_afiliado("https://www.amazon.com.br/dp/B0CHX1Q1FY")
```

##### `gerar_links_afiliado_batch(urls: List[str], lojas: Optional[List[str]] = None) -> Dict[str, str]`
Gera links de afiliado para múltiplas URLs em lote.

**Parâmetros:**
- `urls` (List[str]): Lista de URLs para converter
- `lojas` (Optional[List[str]]): Lista de nomes de lojas

**Retorna:**
- `Dict[str, str]`: Dicionário com URLs originais como chaves e URLs de afiliado como valores

**Exemplo:**
```python
urls = [
    "https://www.amazon.com.br/dp/B0CHX1Q1FY",
    "https://shopee.com.br/iPhone-15-128GB-Preto-i.123456.789012"
]
result = converter.gerar_links_afiliado_batch(urls)
```

#### **Lojas Suportadas**

| Loja | Método | Status |
|------|--------|--------|
| Amazon | ASIN + Tag | ✅ Ativo |
| Shopee | Short Link | ✅ Ativo |
| AliExpress | Tracking Code | ✅ Ativo |
| Mercado Livre | Social Link | ✅ Ativo |
| Magazine Luiza | Domain Replace | ✅ Ativo |
| Kabum! | AWIN API | ✅ Ativo |
| Samsung | AWIN API | ✅ Ativo |
| LG | AWIN API | ✅ Ativo |

---

## ⚙️ **Sistema de Configuração**

### **Módulo: config.py**

Gerencia todas as configurações do sistema via variáveis de ambiente.

#### **Variáveis de Ambiente**

##### **Telegram Bot**
```bash
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
ADMIN_USER_ID=seu_user_id_aqui
```

##### **Rate Limiting**
```bash
POST_RATE_DELAY_MS=250
```

##### **Banco de Dados**
```bash
DB_NAME=ofertas.db
```

##### **Scrapers**
```bash
ENABLE_PROMOBIT=1
ENABLE_PELANDO=1
ENABLE_SHOPEE=0
ENABLE_AMAZON=0
ENABLE_ALIEXPRESS=0
ENABLE_MEPUC=0
```

##### **Amazon PA-API**
```bash
AMAZON_ACCESS_KEY=sua_access_key_aqui
AMAZON_SECRET_KEY=sua_secret_key_aqui
AMAZON_ASSOCIATE_TAG=garimpeirogee-20
AMAZON_REGION=us-east-1
```

##### **Shopee API**
```bash
SHOPEE_API_KEY=sua_api_key_aqui
SHOPEE_API_SECRET=sua_api_secret_aqui
```

##### **AliExpress API**
```bash
ALIEXPRESS_APP_KEY=sua_app_key_aqui
ALIEXPRESS_APP_SECRET=sua_app_secret_aqui
```

##### **AWIN API**
```bash
AWIN_API_TOKEN=seu_token_awin_aqui
```

#### **Funções de Validação**

##### `validate_config() -> List[str]`
Valida se as configurações essenciais estão presentes.

**Retorna:**
- `List[str]`: Lista de erros encontrados (vazia se tudo estiver correto)

**Exemplo:**
```python
from config import validate_config

errors = validate_config()
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Configuração válida!")
```

##### `print_config_status()`
Imprime o status atual de todas as configurações.

---

## 🕷️ **Sistema de Scrapers**

### **Promobit Scraper**

#### **Classe: PromobitScraper**

Scraper principal para o site Promobit com tratamento de erros e anti-bloqueio.

#### **Métodos Principais**

##### `async buscar_ofertas_gerais() -> List[Dict]`
Busca ofertas gerais de todas as categorias configuradas.

**Retorna:**
- `List[Dict]`: Lista de ofertas encontradas

**Exemplo:**
```python
scraper = PromobitScraper()
ofertas = await scraper.buscar_ofertas_gerais()
```

##### `async buscar_ofertas_categoria(categoria: str) -> List[Dict]`
Busca ofertas de uma categoria específica.

**Parâmetros:**
- `categoria` (str): Nome da categoria (ex: "smartphone", "notebook")

**Retorna:**
- `List[Dict]`: Lista de ofertas da categoria

---

## 🗄️ **Sistema de Banco de Dados**

### **Módulo: database.py**

Gerencia o banco de dados SQLite para armazenar ofertas e configurações.

#### **Funções Principais**

##### `init_database()`
Inicializa o banco de dados com as tabelas necessárias.

##### `save_offer(offer_data: Dict) -> bool`
Salva uma oferta no banco de dados.

**Parâmetros:**
- `offer_data` (Dict): Dados da oferta

**Retorna:**
- `bool`: True se salvo com sucesso, False caso contrário

##### `get_recent_offers(limit: int = 50) -> List[Dict]`
Recupera ofertas recentes do banco de dados.

**Parâmetros:**
- `limit` (int): Número máximo de ofertas a retornar

**Retorna:**
- `List[Dict]`: Lista de ofertas recentes

---

## 📱 **Sistema de Postagem no Telegram**

### **Módulo: telegram_poster.py**

Gerencia a postagem automática de ofertas no Telegram.

#### **Classe: TelegramPoster**

##### `async post_offer(offer: Dict) -> bool`
Posta uma oferta no canal do Telegram.

**Parâmetros:**
- `offer` (Dict): Dados da oferta a ser postada

**Retorna:**
- `bool`: True se postado com sucesso, False caso contrário

##### `async post_offers_batch(offers: List[Dict]) -> Dict[str, bool]`
Posta múltiplas ofertas em lote.

**Parâmetros:**
- `offers` (List[Dict]): Lista de ofertas para postar

**Retorna:**
- `Dict[str, bool]`: Dicionário com status de cada postagem

---

## 🔄 **Sistema de Orquestração**

### **Módulo: orchestrator.py**

Coordena todos os sistemas para funcionamento automático.

#### **Classe: ScraperOrchestrator**

##### `async run_full_cycle() -> Dict[str, Any]`
Executa um ciclo completo de scraping e postagem.

**Retorna:**
- `Dict[str, Any]`: Relatório do ciclo executado

##### `async run_scraper(scraper_name: str) -> List[Dict]`
Executa um scraper específico.

**Parâmetros:**
- `scraper_name` (str): Nome do scraper a executar

**Retorna:**
- `List[Dict]`: Ofertas encontradas pelo scraper

---

## 🧪 **Sistema de Testes**

### **Execução de Testes**

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Executar testes específicos
python -m pytest tests/test_affiliate_system.py -v

# Executar com cobertura
python -m pytest tests/ --cov=. --cov-report=html
```

### **Estrutura de Testes**

```
tests/
├── test_affiliate_system.py      # Testes do sistema de afiliados
├── test_config_system.py         # Testes do sistema de configuração
└── conftest.py                   # Configurações compartilhadas
```

---

## 🚀 **Deploy e Produção**

### **Requisitos do Sistema**

- Python 3.11+
- Dependências listadas em `requirements.txt`
- Arquivo `.env` configurado com credenciais
- Acesso à internet para scraping
- Token do bot do Telegram válido

### **Configuração de Produção**

1. **Clone o repositório:**
```bash
git clone https://github.com/duduzinho15/Ainda-nao-funciona.git
cd Ainda-nao-funciona
```

2. **Configure o ambiente:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**
```bash
cp env_template.txt .env
# Edite .env com suas credenciais reais
```

4. **Execute o sistema:**
```bash
python main.py
```

---

## 📊 **Monitoramento e Métricas**

### **Métricas Disponíveis**

- **Prometheus**: Porta 9308 (configurável via `METRICS_PORT`)
- **Logs**: Arquivos de log em `logs/`
- **Status**: Função `print_config_status()` para verificação manual

---

## 🔒 **Segurança**

### **Boas Práticas**

- ✅ **NUNCA** commite o arquivo `.env` no Git
- ✅ Use variáveis de ambiente para credenciais
- ✅ Mantenha o `env_template.txt` atualizado
- ✅ Execute testes antes de cada deploy
- ✅ Monitore logs para atividades suspeitas

### **Verificações de Segurança**

O CI/CD inclui verificações automáticas:
- **Bandit**: Análise de segurança do código
- **Safety**: Verificação de dependências vulneráveis
- **Detect-secrets**: Busca por segredos hardcoded

---

## 📞 **Suporte**

Para dúvidas ou problemas:

1. **Verifique os logs** em `logs/`
2. **Execute os testes** para validar funcionalidades
3. **Consulte esta documentação**
4. **Abra uma issue** no GitHub

---

## 📝 **Changelog**

### **v1.0.0** (Atual)
- ✅ Sistema de afiliados completo
- ✅ Scrapers consolidados e otimizados
- ✅ Configuração via variáveis de ambiente
- ✅ Sistema de testes implementado
- ✅ CI/CD com GitHub Actions
- ✅ Documentação completa
- ✅ Estrutura limpa e profissional

---

**🎯 Sistema Garimpeiro Geek - Transformando busca de ofertas em automação inteligente!**
