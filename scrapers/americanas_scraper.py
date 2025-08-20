"""
Stub para scraper da Americanas.
Para habilitar, configure as variáveis de ambiente necessárias.

⚠️ AVISO: Scraping da Americanas pode ser bloqueado rapidamente.
Recomenda-se usar proxy e rotação de User-Agents.

Variáveis de ambiente:
- PROXY_URL: URL do proxy (altamente recomendado)
- PROXY_USER: Usuário do proxy (se necessário)
- PROXY_PASS: Senha do proxy (se necessário)
- GG_ALLOW_SCRAPING: Deve ser "1" para habilitar

Para implementar:
1. Implementar função get_ofertas(periodo: str)
2. Adicionar rate limiting adequado (máximo 1 req/seg)
3. Implementar rotação de User-Agents
4. Adicionar retry com backoff exponencial
5. Testar com proxy para evitar bloqueios
"""

import os
import asyncio
import logging
from typing import List, Dict, Any


# Configurações
name = "americanas_scraper"
priority = 80  # Prioridade baixa devido ao risco de bloqueio
rate_limit = 0.5  # 0.5 requests por segundo (muito conservador)
retry_count = 5  # Mais tentativas devido ao risco
retry_delay = 3.0  # Delay maior entre tentativas

# URLs base (para referência futura)
BASE_URL = "https://www.americanas.com.br"
DOMAIN = "www.americanas.com.br"

# Páginas de ofertas (para implementação futura)
OFFER_PAGES = [
    "/ofertas",
    "/ofertas/mais-vendidos",
    "/ofertas/lancamentos",
    "/ofertas/black-friday",
    "/ofertas/cyber-monday"
]

# Categorias populares (para implementação futura)
CATEGORIES = [
    "/eletronicos",
    "/informatica",
    "/games",
    "/casa",
    "/moda",
    "/beleza"
]


def enabled() -> bool:
    """Verifica se o scraper está habilitado."""
    # Verificar se scraping é permitido
    if os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME"):
        return False  # Modo CI
    
    # Verificar se há proxy configurado (recomendado)
    has_proxy = bool(os.getenv("PROXY_URL"))
    
    if not has_proxy:
        logging.getLogger(f"scraper.{name}").warning(
            "⚠️ Americanas scraper sem proxy - risco alto de bloqueio"
        )
    
    return os.getenv("GG_ALLOW_SCRAPING") == "1"


async def get_ofertas(periodo: str) -> List[Dict[str, Any]]:
    """
    Stub para coleta de ofertas da Americanas.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista vazia (stub não implementado)
    """
    logger = logging.getLogger(f"scraper.{name}")
    
    if not enabled():
        logger.info("⚠️ Scraper desabilitado (modo CI ou GG_ALLOW_SCRAPING != 1)")
        return []
    
    logger.info("⚠️ Stub da Americanas - implementação não disponível")
    logger.info("📝 Para implementar:")
    logger.info("  1. Adicionar dependências: aiohttp, beautifulsoup4")
    logger.info("  2. Implementar scraping de páginas de ofertas")
    logger.info("  3. Adicionar rate limiting rigoroso")
    logger.info("  4. Implementar rotação de User-Agents")
    logger.info("  5. Adicionar suporte a proxy")
    
    # Retornar lista vazia (stub)
    return []


# Variáveis de ambiente necessárias
REQUIRED_ENV_VARS = [
    "PROXY_URL"  # Altamente recomendado
]

# Configurações de risco
RISK_LEVEL = "ALTO"
BLOCK_PROBABILITY = "ALTA"
RECOMMENDED_PROXY = True
RATE_LIMIT_STRICT = True


# Teste local (se executado diretamente)
if __name__ == "__main__":
    async def test():
        print("🧪 Testando stub da Americanas...")
        
        if not enabled():
            print("⚠️ Scraper desabilitado")
            return
        
        print("📋 Informações do stub:")
        print(f"  - Nome: {name}")
        print(f"  - Prioridade: {priority}")
        print(f"  - Rate Limit: {rate_limit} req/seg")
        print(f"  - Nível de Risco: {RISK_LEVEL}")
        print(f"  - Proxy Recomendado: {RECOMMENDED_PROXY}")
        print(f"  - Rate Limit Rigoroso: {RATE_LIMIT_STRICT}")
        
        ofertas = await get_ofertas("7d")
        print(f"✅ Stub retornou {len(ofertas)} ofertas")
    
    asyncio.run(test())
