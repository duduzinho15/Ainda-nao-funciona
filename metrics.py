# metrics.py
from prometheus_client import Counter, Gauge, start_http_server
import os

STARTED = False
POSTS_OK = Counter("gg_posts_ok_total", "Posts bem-sucedidos")
POSTS_FAIL = Counter("gg_posts_fail_total", "Posts com falha")
OFFERS_COLLECTED = Gauge("gg_offers_collected", "Ofertas coletadas na execução")
OFFERS_APPROVED = Gauge("gg_offers_approved", "Ofertas aprovadas na execução")
OFFERS_DUPLICATED = Counter("gg_offers_duplicated_total", "Ofertas duplicadas detectadas")
SCRAPER_ERRORS = Counter("gg_scraper_errors_total", "Erros de scrapers", ["scraper_name"])
SCRAPER_SUCCESS = Counter("gg_scraper_success_total", "Sucessos de scrapers", ["scraper_name"])

def maybe_start_server():
    global STARTED
    if not STARTED and os.getenv("METRICS", "0") == "1":
        port = int(os.getenv("METRICS_PORT", "9308"))
        start_http_server(port)
        print(f"📊 Métricas Prometheus iniciadas na porta {port}")
        STARTED = True
