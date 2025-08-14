# Integração com a API da Shopee

## Visão Geral

Este documento descreve a implementação da integração com a API oficial da Shopee para o bot "Garimpeiro Geek". A integração permite buscar ofertas de produtos de tecnologia e eletrônicos diretamente da API oficial da Shopee, garantindo maior confiabilidade e estabilidade na coleta de dados.

## Arquivos Implementados

### 1. `shopee_api_integration.py`
Módulo principal que implementa a integração com a API da Shopee.

**Funcionalidades principais:**
- Autenticação com HMAC-SHA256
- Busca de produtos por palavra-chave
- Busca de produtos por categoria
- Busca de ofertas relâmpago
- Formatação de dados para o padrão do bot
- Sistema de filtros para melhores ofertas

### 2. `config.py` (atualizado)
Adicionadas configurações para a API da Shopee:
- `SHOPEE_API_KEY`: Chave da API
- `SHOPEE_API_SECRET`: Segredo da API
- `SHOPEE_PARTNER_ID`: ID do parceiro
- `SHOPEE_SHOP_ID`: ID da loja (opcional)

### 3. `main.py` (atualizado)
Integrada a busca de ofertas da Shopee na função principal `buscar_e_publicar_ofertas`.

### 4. `test_shopee_api.py`
Script de teste completo para validar todas as funcionalidades da API.

## Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# API da Shopee
SHOPEE_API_KEY=sua_api_key_aqui
SHOPEE_API_SECRET=sua_api_secret_aqui
SHOPEE_PARTNER_ID=seu_partner_id_aqui
SHOPEE_SHOP_ID=seu_shop_id_aqui  # Opcional
```

### 2. Obtenção das Credenciais

Para obter acesso à API da Shopee:

1. Acesse o [Portal de Parceiros da Shopee](https://partner.shopeemobile.com)
2. Faça login ou crie uma conta
3. Solicite acesso à API
4. Obtenha suas credenciais (API Key, Secret, Partner ID)

## Funcionalidades da API

### 1. Busca por Palavra-chave
```python
from shopee_api_integration import ShopeeAPIIntegration

shopee = ShopeeAPIIntegration()
produtos = shopee.search_products("smartphone", limit=10)
```

### 2. Busca por Categoria
```python
# Categorias disponíveis:
# - 11001205: Computadores e Acessórios
# - 11001185: Eletrônicos
# - 11001195: Dispositivos Inteligentes
# - 11001287: Consoles e Acessórios
# - 11001188: Áudio

produtos = shopee.get_category_products(11001205, limit=20)
```

### 3. Ofertas Relâmpago
```python
ofertas = shopee.get_flash_sale_products(limit=15)
```

### 4. Busca Geral
```python
# Busca ofertas em todas as categorias e palavras-chave
todas_ofertas = shopee.buscar_ofertas_gerais(limit=25)
```

## Formato dos Dados

Cada produto retornado pela API segue o seguinte formato:

```python
{
    "titulo": "Nome do Produto",
    "preco": "299.90",
    "preco_original": "399.90",  # Pode ser None
    "desconto": 25,              # Percentual de desconto
    "url_produto": "https://shopee.com.br/product/...",
    "url_afiliado": "https://shopee.com.br/product/...",  # Por enquanto igual à original
    "imagem_url": "https://cf.shopee.com.br/file/...",
    "loja": "Shopee",
    "categoria": "Eletrônicos",
    "rating": 4.5,               # Avaliação de 0 a 5
    "vendas": 150,               # Número de vendas
    "estoque": 50,               # Quantidade em estoque
    "localizacao": "Brasil",
    "frete_gratis": True,        # Se o frete é gratuito
    "data_coleta": "2025-01-15T10:30:00"
}
```

## Sistema de Filtros

A API implementa um sistema inteligente de filtros que prioriza:

1. **Ofertas com desconto** (≥10%)
2. **Produtos bem avaliados** (≥4.0/5)
3. **Produtos com vendas** (histórico de vendas > 0)

## Tratamento de Erros

### 1. Falhas de Conexão
- Timeout de 30 segundos para requisições
- Retry automático com delays aleatórios
- Logs detalhados de erros

### 2. Dados Inválidos
- Validação de campos obrigatórios
- Conversão segura de preços
- Fallback para valores padrão

### 3. Rate Limiting
- Delays aleatórios entre requisições (1-3 segundos)
- Limite de 100 produtos por requisição (máximo da API)

## Testes

### Executar Testes Completos
```bash
python test_shopee_api.py
```

### Testes Disponíveis
1. **Importação**: Verifica se o módulo pode ser importado
2. **Inicialização**: Testa a criação da instância da API
3. **Conexão**: Verifica conectividade com a API
4. **Funcionalidades**: Testa busca por palavra-chave e categoria
5. **Busca Geral**: Valida a busca geral de ofertas
6. **Formato**: Verifica se os dados estão no formato correto
7. **Função de Conveniência**: Testa a função wrapper

## Integração com o Bot

### 1. Busca Automática
A API da Shopee é chamada automaticamente na função `buscar_e_publicar_ofertas` do `main.py`.

### 2. Filtros Aplicados
- Limite de 15 ofertas por busca
- Filtro por desconto (≥10%) ou preço baixo (<R$1000)
- Limite final de 8 ofertas para publicação

### 3. Logs
Todas as operações são registradas com detalhes para monitoramento e debug.

## Monitoramento e Manutenção

### 1. Logs Importantes
- Conexão com a API
- Número de produtos encontrados
- Erros de autenticação ou requisição
- Performance das buscas

### 2. Métricas
- Taxa de sucesso das requisições
- Tempo de resposta da API
- Número de ofertas encontradas por categoria

### 3. Troubleshooting
- Verificar credenciais no arquivo `.env`
- Confirmar conectividade com a internet
- Validar formato das credenciais
- Verificar logs de erro detalhados

## Próximos Passos

### 1. Sistema de Afiliados
- Implementar conversão de URLs para links de afiliado
- Integrar com programa de parceiros da Shopee

### 2. Cache Inteligente
- Implementar cache de produtos para reduzir requisições
- Cache de categorias e palavras-chave populares

### 3. Análise de Tendências
- Coleta de dados históricos de preços
- Identificação de padrões de desconto
- Alertas para melhores oportunidades

## Suporte

Para suporte técnico ou dúvidas sobre a integração:

1. Verifique os logs do sistema
2. Execute os testes com `python test_shopee_api.py`
3. Consulte a documentação da API da Shopee
4. Verifique as configurações no arquivo `.env`

## Changelog

### v1.0.0 (2025-01-15)
- Implementação inicial da API da Shopee
- Integração com o bot principal
- Sistema de filtros inteligentes
- Testes automatizados completos
- Documentação completa
