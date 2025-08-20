"""
Stub para scraper do AliExpress.
Para habilitar, configure as variáveis de ambiente necessárias.

Variáveis de ambiente:
- ALIEXPRESS_APP_KEY: Chave da aplicação AliExpress
- ALIEXPRESS_APP_SECRET: Segredo da aplicação
- ALIEXPRESS_ACCESS_TOKEN: Token de acesso
- PROXY_URL: URL do proxy (opcional)

Para implementar:
1. Configurar autenticação com a API do AliExpress
2. Implementar função get_ofertas(periodo: str)
3. Definir priority (padrão: 60)
4. Testar coleta de ofertas
"""

# Por padrão, desabilitado até implementação completa
enabled = False
priority = 60

async def get_ofertas(periodo: str):
    """
    Stub para coleta de ofertas do AliExpress.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista vazia (stub não implementado)
    """
    # TODO: Implementar coleta real do AliExpress
    return []


# Variáveis de ambiente necessárias
REQUIRED_ENV_VARS = [
    "ALIEXPRESS_APP_KEY",
    "ALIEXPRESS_APP_SECRET",
    "ALIEXPRESS_ACCESS_TOKEN"
]
