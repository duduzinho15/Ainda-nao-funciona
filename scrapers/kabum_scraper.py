"""
Stub para scraper da Kabum.
Para habilitar, configure as variáveis de ambiente necessárias.

Variáveis de ambiente:
- KABUM_API_KEY: Chave da API da Kabum
- KABUM_PARTNER_ID: ID do parceiro afiliado
- PROXY_URL: URL do proxy (opcional)

Para implementar:
1. Configurar autenticação com a API da Kabum
2. Implementar função get_ofertas(periodo: str)
3. Definir priority (padrão: 50)
4. Testar coleta de ofertas
"""

# Por padrão, desabilitado até implementação completa
enabled = False
priority = 50

async def get_ofertas(periodo: str):
    """
    Stub para coleta de ofertas da Kabum.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista vazia (stub não implementado)
    """
    # TODO: Implementar coleta real da Kabum
    return []


# Variáveis de ambiente necessárias
REQUIRED_ENV_VARS = [
    "KABUM_API_KEY",
    "KABUM_PARTNER_ID"
]
