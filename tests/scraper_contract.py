# tests/scraper_contract.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Iterable, Tuple
import re
import os
import json
from datetime import datetime
from pathlib import Path

# Importa a função de hash já criada no projeto
from utils.offer_hash import offer_hash

# Campos mínimos esperados por oferta
REQUIRED_FIELDS = (
    "titulo",
    "preco",            # string formatada ("R$ 1.234,56") – validação flexível
    "url_produto",
    "loja",
    "fonte",            # nome do scraper/fonte
)

OPTIONAL_FIELDS = (
    "preco_original",
    "desconto",
    "imagem_url",
    "url_afiliado",     # será gerado pelo affiliate.py ou validado se já vier
    "categoria",
)

@dataclass
class Offer:
    titulo: str
    preco: str
    url_produto: str
    loja: str
    fonte: str
    preco_original: Optional[str] = None
    desconto: Optional[int] = None
    imagem_url: Optional[str] = None
    url_afiliado: Optional[str] = None
    categoria: Optional[str] = None
    offer_hash: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Offer":
        # Garante chaves mínimas, lança erro amigável do que está faltando
        missing = [k for k in REQUIRED_FIELDS if not d.get(k)]
        if missing:
            raise ValueError(f"Oferta inválida: faltando campos obrigatórios: {missing}. Payload: {d}")

        return Offer(
            titulo=d["titulo"],
            preco=d["preco"],
            url_produto=d["url_produto"],
            loja=d["loja"],
            fonte=d["fonte"],
            preco_original=d.get("preco_original"),
            desconto=d.get("desconto"),
            imagem_url=d.get("imagem_url"),
            url_afiliado=d.get("url_afiliado"),
            categoria=d.get("categoria"),
            offer_hash=d.get("offer_hash"),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "titulo": self.titulo,
            "preco": self.preco,
            "url_produto": self.url_produto,
            "loja": self.loja,
            "fonte": self.fonte,
            "preco_original": self.preco_original,
            "desconto": self.desconto,
            "imagem_url": self.imagem_url,
            "url_afiliado": self.url_afiliado,
            "categoria": self.loja,
            "offer_hash": self.offer_hash,
        }
        return {k: v for k, v in d.items() if v is not None}

def is_price_like(s: str) -> bool:
    # Aceita "R$ 1.234,56" / "R$ 999,00" / "999,00"
    if not isinstance(s, str):
        return False
    s = s.strip()
    return bool(re.match(r"^(R\$)?\s?\d{1,3}(\.\d{3})*,\d{2}$", s))

def ensure_offer_hash(o: Offer) -> Offer:
    if not o.offer_hash:
        o.offer_hash = offer_hash(o.to_dict())
    return o

def validate_offer_structure(o: Offer) -> Tuple[bool, str]:
    if not is_price_like(o.preco):
        return False, f"Preço com formato inesperado: {o.preco!r}"
    if not re.match(r"^https?://", o.url_produto or ""):
        return False, f"url_produto inválida: {o.url_produto!r}"
    if o.imagem_url and not re.match(r"^https?://", o.imagem_url):
        return False, f"imagem_url inválida: {o.imagem_url!r}"
    return True, "OK"

def write_report(items: Iterable[Offer], ok_count: int, fail_count: int, outdir: str = "reports") -> str:
    Path(outdir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(outdir) / f"scraper_report_{ts}"

    # CSV simples
    csv_path = str(base) + ".csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("titulo;loja;fonte;preco;tem_imagem;tem_afiliado;hash\n")
        for o in items:
            f.write(f"{o.titulo};{o.loja};{o.fonte};{o.preco};{bool(o.imagem_url)};{bool(o.url_afiliado)};{o.offer_hash}\n")

    # JSON detalhado
    json_path = str(base) + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([o.to_dict() for o in items], f, ensure_ascii=False, indent=2)

    # resumo TXT
    summary_path = str(base) + "_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"Ofertas OK: {ok_count}\n")
        f.write(f"Ofertas com erro: {fail_count}\n")
        f.write(f"Itens totais: {ok_count + fail_count}\n")

    return csv_path
