# utils/images.py
from io import BytesIO
import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def fetch_bytes(url: str, timeout: int = 12) -> BytesIO | None:
    """Download da imagem para bytes para evitar hotlinking"""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, stream=True)
        r.raise_for_status()
        buf = BytesIO(r.content)
        buf.seek(0)
        return buf
    except Exception:
        return None

def fetch_og_image(page_url: str, timeout: int = 10) -> str | None:
    """Extrai og:image de uma página web"""
    try:
        r = requests.get(page_url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tag = (soup.find("meta", property="og:image")
               or soup.find("meta", attrs={"name": "og:image"}))
        return tag.get("content") if tag and tag.get("content") else None
    except Exception:
        return None
