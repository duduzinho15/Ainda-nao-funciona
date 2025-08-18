# flet_app/ui_tokens.py
from dataclasses import dataclass

@dataclass
class Tokens:
    bg: str
    surface: str
    card: str
    text: str
    text_muted: str
    border: str
    primary: str
    danger: str
    success: str
    warning: str

LIGHT = Tokens(
    bg="#F5F7FA",
    surface="#FFFFFF",
    card="#F3F4F6",
    text="#111827",
    text_muted="#6B7280",
    border="#E5E7EB",
    primary="#0EA5E9",   # azul/teal suave
    danger="#DC2626",
    success="#16A34A",
    warning="#F59E0B",
)

DARK = Tokens(
    bg="#0B0F17",
    surface="#111827",
    card="#0F172A",
    text="#E5E7EB",
    text_muted="#9CA3AF",
    border="#1F2937",
    primary="#22D3EE",   # teal claro (bom contraste no escuro)
    danger="#F87171",
    success="#22C55E",
    warning="#FBBF24",
)

def tokens(mode: str) -> Tokens:
    """mode: 'light' ou 'dark'"""
    return DARK if str(mode).lower().endswith("dark") else LIGHT
