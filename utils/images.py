# utils/images.py
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from .cache import cached

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

async def fetch_bytes(url: str, timeout: int = 12) -> BytesIO | None:
    """
    Baixa imagem com requests (UA de navegador), retorna BytesIO.
    Cacheado com TTL de 1 hora para evitar requisições repetidas.
    """
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, stream=True)
        r.raise_for_status()
        buf = BytesIO(r.content)
        buf.seek(0)
        return buf
    except Exception:
        return None

async def fetch_og_image(page_url: str, timeout: int = 10) -> str | None:
    """
    Pega og:image de uma página caso não haja imagem explícita.
    Cacheado com TTL de 30 minutos para evitar requisições repetidas.
    """
    try:
        r = requests.get(page_url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tag = (soup.find("meta", property="og:image")
               or soup.find("meta", attrs={"name": "og:image"}))
        return tag.get("content") if tag and tag.get("content") else None
    except Exception:
        return None
