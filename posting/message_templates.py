# posting/message_templates.py
# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Tuple

MAX_CAPTION = 900
ELLIPSIS = "…"


def esc(s: Any) -> str:
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def truncate(text: str, limit: int = MAX_CAPTION) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + ELLIPSIS


def slugify_store(name: str | None) -> str:
    if not name:
        return "default"
    s = name.lower().strip()
    aliases = {
        "mercado livre": "mercadolivre",
        "magazine luiza": "magalu",
        "ml": "mercadolivre",
        "kabum!": "kabum",
        "samsung br": "samsung",
        "lg br": "lg",
        "comfy br": "comfy",
        "trocafy br": "trocafy",
    }
    return aliases.get(s, s)


def fmt_price(offer: Dict[str, Any]) -> str:
    return esc(offer.get("price_formatted") or offer.get("price") or "—")


def bullets(features: List[str] | None, max_items: int = 4) -> List[str]:
    if not features:
        return []
    return [f"• {esc(x)}" for x in features[:max_items] if x]


def render_badges(offer: Dict[str, Any]) -> List[str]:
    types = set(offer.get("types", []))
    out: List[str] = []
    if "historical_low" in types:
        out.append("🥇 <b>MENOR PREÇO HISTÓRICO</b>")
    if "three_month_low" in types:
        out.append("📉 <b>MENOR PREÇO EM 3 MESES</b>")
    if "flash_deal" in types:
        out.append("⏱ <b>OFERTA RELÂMPAGO</b>")
    if offer.get("free_shipping"):
        out.append("🚚 Frete grátis")
    if offer.get("official_store"):
        out.append("🏬 Loja oficial")
    if offer.get("coupon"):
        out.append(f"🎟 Cupom: <code>{esc(offer['coupon'])}</code>")
    if offer.get("cashback"):
        out.append(f"💸 Cashback: {esc(offer['cashback'])}")
    if offer.get("drop_percent"):
        try:
            dp = int(round(float(offer["drop_percent"])))
            out.append(f"⬇️ <b>-{dp}%</b> vs média")
        except Exception:
            pass
    return out


def base_lines(offer: Dict[str, Any], store_icon: str, store_name: str) -> List[str]:
    title = esc(offer.get("title", "Oferta"))
    lines = [f"{store_icon} <b>{title}</b>"]
    lines += bullets(offer.get("features"))
    price_line = f"💰 <b>Preço:</b> {fmt_price(offer)}"
    if offer.get("previous_price"):
        price_line += f"  <s>{esc(offer.get('previous_price'))}</s>"
    lines.append(price_line)
    return lines


def tpl_default(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🔥", esc(offer.get("store", "Loja")))
    lines.append(
        f"🏷 {esc(offer.get('store', 'Loja'))} | {esc(offer.get('origin', 'Garimpeiro Geek'))}"
    )
    return lines


def tpl_amazon(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟧", "Amazon")
    prime = "✔️ Prime" if offer.get("prime") else "—"
    lines.append(f"🚚 Prime: {prime}")
    lines.append(f"🏷 Amazon | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_shopee(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟠", "Shopee")
    if offer.get("shipping_info"):
        lines.append(f"🚚 Frete: {esc(offer['shipping_info'])}")
    if offer.get("coins"):
        lines.append(f"🪙 Moedas: {esc(offer['coins'])}")
    if offer.get("coupon"):
        lines.append(f"🎟 Cupom: <code>{esc(offer['coupon'])}</code>")
    lines.append(f"🏷 Shopee | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_aliexpress(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟥", "AliExpress")
    if offer.get("taxes_info"):
        lines.append(f"🌎 Taxas: {esc(offer['taxes_info'])}")
    if offer.get("shipping_info"):
        lines.append(f"🚚 Envio: {esc(offer['shipping_info'])}")
    if offer.get("coupon"):
        lines.append(f"🎟 Cupom: <code>{esc(offer['coupon'])}</code>")
    lines.append(f"🏷 AliExpress | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_magalu(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🔵", "Magalu")
    if offer.get("parcelamento"):
        lines.append(f"💳 Parcelamento: {esc(offer['parcelamento'])}")
    if offer.get("cashback"):
        lines.append(f"💸 Cashback: {esc(offer['cashback'])}")
    lines.append(f"🏷 Magalu | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_ml(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟡", "Mercado Livre")
    if offer.get("ml_full") is not None:
        lines.append(f"🚚 Full: {'✔️' if offer['ml_full'] else '—'}")
    if offer.get("devolucao_info"):
        lines.append(f"↩️ Devolução: {esc(offer['devolucao_info'])}")
    lines.append(f"🏷 Mercado Livre | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_kabum(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟣", "KaBuM!")
    if offer.get("pix_discount"):
        lines.append(f"🏦 PIX: {esc(offer['pix_discount'])}")
    if offer.get("deal_ends_in"):
        lines.append(f"⏳ Termina em: {esc(offer['deal_ends_in'])}")
    lines.append(f"🏷 KaBuM | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_samsung(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🔵", "Samsung")
    if offer.get("parcelamento"):
        lines.append(f"💳 Parcelamento: {esc(offer['parcelamento'])}")
    if offer.get("garantia"):
        lines.append(f"🛡 Garantia: {esc(offer['garantia'])}")
    lines.append(f"🏷 Samsung | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_lg(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟩", "LG")
    if offer.get("parcelamento"):
        lines.append(f"💳 Parcelamento: {esc(offer['parcelamento'])}")
    if offer.get("garantia"):
        lines.append(f"🛡 Garantia: {esc(offer['garantia'])}")
    lines.append(f"🏷 LG | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_comfy(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟦", "Comfy")
    lines.append(f"🏷 Comfy | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


def tpl_trocafy(offer: Dict[str, Any]) -> List[str]:
    lines = base_lines(offer, "🟪", "Trocafy")
    lines.append(f"🏷 Trocafy | {esc(offer.get('origin', 'Garimpeiro Geek'))}")
    return lines


STORE_TEMPLATES = {
    "amazon": tpl_amazon,
    "shopee": tpl_shopee,
    "aliexpress": tpl_aliexpress,
    "magalu": tpl_magalu,
    "mercadolivre": tpl_ml,
    "kabum": tpl_kabum,
    "samsung": tpl_samsung,
    "lg": tpl_lg,
    "comfy": tpl_comfy,
    "trocafy": tpl_trocafy,
}


def build_buttons(offer: Dict[str, Any]) -> List[Dict[str, str]]:
    buttons: List[Dict[str, str]] = []
    if offer.get("affiliate_url"):
        buttons.append({"text": "🛒 Comprar agora", "url": offer["affiliate_url"]})
    if offer.get("coupon") and offer.get("affiliate_url"):
        buttons.append({"text": "🎟 Cupom", "url": offer["affiliate_url"]})
    if offer.get("compare_url"):
        buttons.append({"text": "🔎 Outras lojas", "url": offer["compare_url"]})
    if offer.get("alt_links"):
        for label, url in list(offer["alt_links"].items()):
            buttons.append({"text": f"🛍 {label}", "url": url})
            if len(buttons) >= 3:
                break
    return buttons[:3]


def render_caption_and_buttons(
    offer: Dict[str, Any],
) -> Tuple[str, List[Dict[str, str]]]:
    store = slugify_store(offer.get("store"))
    tpl = STORE_TEMPLATES.get(store, tpl_default)
    lines: List[str] = []
    badges = render_badges(offer)
    if badges:
        lines += badges
    lines += tpl(offer)
    if "historical_low" in set(offer.get("types", [])):
        lines.append("📊 Preço mais baixo já registrado.")
    elif "three_month_low" in set(offer.get("types", [])):
        lines.append("🗓️ Preço mais baixo dos últimos 3 meses.")
    caption = "\n".join([ln for ln in lines if ln])
    caption = truncate(caption, MAX_CAPTION)
    buttons = build_buttons(offer)
    return caption, buttons
