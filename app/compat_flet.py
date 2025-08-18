# app/compat_flet.py
from __future__ import annotations
from typing import Any, Callable, Protocol, runtime_checkable

@runtime_checkable
class _SupportsCallFromThread(Protocol):
    """Protocolo para objetos que suportam call_from_thread"""
    def call_from_thread(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any: ...

@runtime_checkable
class _SupportsInvoke(Protocol):
    """Protocolo para objetos que suportam invoke"""
    def invoke(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any: ...

def safe_call_from_thread(page: Any, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Chama call_from_thread de forma segura, com fallback para execução direta"""
    # Tenta usar call_from_thread se disponível
    if hasattr(page, 'call_from_thread') and isinstance(page, _SupportsCallFromThread):
        return page.call_from_thread(fn, *args, **kwargs)
    
    # Fallback para versões mais antigas - executa diretamente
    return fn(*args, **kwargs)

def safe_invoke(page: Any, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Chama invoke de forma segura, com fallback para execução direta"""
    # Tenta usar invoke se disponível
    if hasattr(page, 'invoke') and isinstance(page, _SupportsInvoke):
        return page.invoke(fn, *args, **kwargs)
    
    # Fallback para versões mais antigas - executa diretamente
    return fn(*args, **kwargs)

def safe_page_update(page: Any) -> None:
    """Chama page.update() de forma segura"""
    if hasattr(page, 'update') and callable(getattr(page, 'update')):
        page.update()

def safe_theme_mode_set(page: Any, mode: str) -> None:
    """Define theme_mode de forma segura"""
    if hasattr(page, 'theme_mode'):
        page.theme_mode = mode

def safe_scroll_mode_set(page: Any, mode: str) -> None:
    """Define scroll de forma segura"""
    if hasattr(page, 'scroll'):
        page.scroll = mode
