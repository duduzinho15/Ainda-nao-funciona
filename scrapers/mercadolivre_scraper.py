"""
Stub para scraper do Mercado Livre.
Para habilitar, configure as variáveis de ambiente necessárias.

Variáveis de ambiente:
- MERCADOLIVRE_APP_ID: ID da aplicação Mercado Livre
- MERCADOLIVRE_CLIENT_SECRET: Segredo do cliente
- MERCADOLIVRE_ACCESS_TOKEN: Token de acesso
- PROXY_URL: URL do proxy (opcional)

Para implementar:
1. Configurar autenticação com a API do Mercado Livre
2. Implementar função get_ofertas(periodo: str)
3. Definir priority (padrão: 70)
4. Testar coleta de ofertas
"""

# Por padrão, desabilitado até implementação completa
enabled = False
priority = 70

async def get_ofertas(periodo: str):
    """
    Stub para coleta de ofertas do Mercado Livre.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista vazia (stub não implementado)
    """
    # TODO: Implementar coleta real do Mercado Livre
    return []


# Variáveis de ambiente necessárias
REQUIRED_ENV_VARS = [
    "MERCADOLIVRE_APP_ID",
    "MERCADOLIVRE_CLIENT_SECRET",
    "MERCADOLIVRE_ACCESS_TOKEN"
]
